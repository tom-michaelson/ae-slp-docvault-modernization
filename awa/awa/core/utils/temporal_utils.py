import json
from datetime import UTC, datetime, timedelta

from loguru import logger
from pydantic import BaseModel
from temporalio import activity
from temporalio.activity import Info as ActivityInfo
from temporalio.api.enums.v1 import WorkflowExecutionStatus
from temporalio.client import Client
from temporalio.workflow import Info as WorkflowInfo

from awa.core import constants
from awa.core.models.api import WorkflowRunStatus
from awa.core.utils.cache_utils import CacheUtils
from awa.core.utils.command_utils import CommandUtils


class TopLevelWorkflowInfo(BaseModel):
    """Information about the top-level workflow in a hierarchy."""

    workflow_id: str
    workflow_type: str


class TemporalUtils:
    @staticmethod
    async def get_top_level_workflow_info_from_activity(
        temporal_client: Client,
    ) -> TopLevelWorkflowInfo:
        """Get the top-level workflow information by traversing the parent hierarchy.

        This method traverses up the workflow parent hierarchy to find the top-most
        parent workflow and returns its ID and type.

        Args:
            temporal_client: The Temporal client instance used for workflow operations.
            starting_workflow_id: The workflow ID to start traversing from.

        Returns:
            TopLevelWorkflowInfo containing the ID and type of the top-level workflow.

        """
        current_workflow_id = activity.info().workflow_id
        top_level_workflow_id = current_workflow_id
        top_level_workflow_type = "UnknownWorkflow"

        logger.debug(f"Starting workflow hierarchy traversal from ID: {current_workflow_id}")

        # Traverse up the parent hierarchy
        while current_workflow_id:
            try:
                workflow_handle = temporal_client.get_workflow_handle(current_workflow_id)
                workflow_description = await workflow_handle.describe()

                # Capture the workflow type at each level (the last one will be the top-level)
                if hasattr(workflow_description, "workflow_type") and workflow_description.workflow_type:
                    top_level_workflow_type = workflow_description.workflow_type
                    logger.debug(f"Found workflow type: {top_level_workflow_type}")

                if workflow_description.parent_id:
                    # Has a parent, continue traversing
                    current_workflow_id = workflow_description.parent_id
                    top_level_workflow_id = current_workflow_id
                else:
                    # No parent, this is the top-level workflow
                    break
            except Exception:  # noqa: BLE001
                logger.exception(f"Error getting workflow description for {current_workflow_id}")
                break

        logger.info(f"Top-level workflow - ID: {top_level_workflow_id}, Type: {top_level_workflow_type}")
        return TopLevelWorkflowInfo(
            workflow_id=top_level_workflow_id,
            workflow_type=top_level_workflow_type,
        )

    @staticmethod
    def generate_workflow_id() -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # noqa: DTZ005
        timestamp_hash = CacheUtils.hash(value=timestamp, short=True)
        return f"{timestamp}_{timestamp_hash}"

    @staticmethod
    async def get_parent_workflow_task_queue_for_activity(temporal_client: Client, activity_info: ActivityInfo) -> str:
        """Get the task queue of the top-most parent workflow of an activity.

        Args:
            temporal_client: The Temporal client.
            activity_info: The activity info.

        Returns:
            The task queue of the top-most parent workflow of the activity.

        """
        workflow_task_queue = activity_info.task_queue
        parent_workflow_id = activity_info.workflow_id
        while parent_workflow_id:
            workflow_description = await temporal_client.get_workflow_handle(parent_workflow_id).describe()
            workflow_task_queue = workflow_description.task_queue
            parent_workflow_id = workflow_description.parent_id
        return workflow_task_queue

    @staticmethod
    async def get_parent_workflow_task_queue_for_workflow(temporal_client: Client, workflow_info: WorkflowInfo) -> str:
        """Get the task queue of the top-most parent workflow of a workflow.

        Args:
            temporal_client: The Temporal client.
            workflow_info: The workflow info.

        Returns:
            The task queue of the top-most parent workflow of the workflow.

        """
        workflow_task_queue = workflow_info.task_queue
        parent_workflow_id = workflow_info.workflow_id
        while parent_workflow_id:
            workflow_description = await temporal_client.get_workflow_handle(parent_workflow_id).describe()
            workflow_task_queue = workflow_description.task_queue
            parent_workflow_id = workflow_description.parent_id
        return workflow_task_queue


async def _get_active_worker_pollers(task_queue: str, startup_mode: bool = False) -> list[str]:
    """Get active worker pollers from the task queue.

    Args:
        task_queue: The task queue to check for active pollers
        startup_mode: If True, use extended timeout for startup phase. If False, use runtime timeout.

    Returns:
        list[str]: List of unique poller identities that are actively polling

    """
    try:
        command = f"temporal task-queue describe --task-queue {task_queue} --output json"
        status, result = await CommandUtils.run_command_async(command)

        if not status:
            logger.warning(f"Failed to get task queue status: {result}")
            return []

        try:
            task_queue_data = json.loads(result)
            pollers = task_queue_data.get("pollers", []) or []
            if not pollers:
                return []

            # Filter pollers based on startup vs runtime timeout thresholds (AWA-133 Phase 2.1)
            active_pollers = []
            current_time = datetime.now(tz=UTC)

            if startup_mode:
                threshold_seconds = constants.WORKER_POLL_STARTUP_TIMEOUT_SECONDS
                timeout_context = "startup"
            else:
                threshold_seconds = constants.WORKER_POLL_RUNTIME_TIMEOUT_SECONDS
                timeout_context = "runtime"

            threshold = timedelta(seconds=threshold_seconds)
            logger.debug(
                f"Using {timeout_context} timeout threshold: {threshold_seconds} seconds for task queue '{task_queue}'",
            )

            for poller in pollers:
                last_access_time_str = poller.get("lastAccessTime")
                try:
                    # Parse ISO format timestamp - handle both 'Z' suffix and timezone offset
                    if last_access_time_str.endswith("Z"):
                        # Remove Z and parse as UTC
                        last_access_time = datetime.fromisoformat(last_access_time_str[:-1]).replace(tzinfo=UTC)
                    else:
                        # Parse with timezone info
                        last_access_time = datetime.fromisoformat(last_access_time_str)

                    if current_time - last_access_time <= threshold:
                        identity = poller.get("identity", "")
                        if identity and identity not in active_pollers:
                            active_pollers.append(identity)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Failed to parse last access time '{last_access_time_str}': {e}")
                    continue

            logger.debug(
                f"Found {len(active_pollers)} active pollers using {timeout_context} timeout for "
                f"task queue '{task_queue}'",
            )
            return active_pollers

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse task queue JSON response: {e}")
            return []

    except Exception as e:  # noqa: BLE001
        logger.warning(f"Error checking for active worker pollers: {e}")
        return []


def map_temporal_status(status: int) -> WorkflowRunStatus:
    mapping = {
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CANCELED: WorkflowRunStatus.CANCELED,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_COMPLETED: WorkflowRunStatus.COMPLETED,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CONTINUED_AS_NEW: WorkflowRunStatus.CONTINUED_AS_NEW,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_FAILED: WorkflowRunStatus.FAILED,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_RUNNING: WorkflowRunStatus.RUNNING,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TERMINATED: WorkflowRunStatus.TERMINATED,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TIMED_OUT: WorkflowRunStatus.TIMED_OUT,
        WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_UNSPECIFIED: WorkflowRunStatus.UNSPECIFIED,
    }
    return mapping.get(status, WorkflowRunStatus.UNKNOWN)
