"""Client for managing workflow lifecycle operations in Temporal."""

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from temporalio.client import Client

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import WorkflowRun, WorkflowRunStatus
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.temporal_utils import map_temporal_status

if TYPE_CHECKING:
    from awa.core.engine.hitl_task_client import HITLTaskClient


class WorkflowManagementClient:
    """Client for managing workflow lifecycle operations.

    This client handles workflow management operations including:
    - Listing workflow runs
    - Terminating workflows
    - Getting workflow status and links
    """

    def __init__(self, client: Client, hitl_client: "HITLTaskClient | None" = None) -> None:
        """Initialize the Workflow Management client.

        Args:
            client: The Temporal client instance
            hitl_client: Optional HITL client for fetching task information

        """
        self.client = client
        self.hitl_client = hitl_client
        self.logger = get_logger(LoggerComponent.CLIENT)

    async def list_workflow_runs(self) -> list[WorkflowRun]:
        """List all workflow runs (running and completed).

        Returns:
            List of WorkflowRun objects with pending task counts for running workflows

        """
        runs = []
        async for workflow in self.client.list_workflows():
            # Skip child workflows
            if workflow.parent_id is not None:
                continue

            start_time = workflow.execution_time
            end_time = workflow.close_time
            duration = end_time - start_time if end_time else datetime.now(UTC) - start_time

            # Get the workflow status
            workflow_status = map_temporal_status(workflow.status)
            # Count pending tasks for running workflows
            pending_tasks_count = 0
            if workflow_status == WorkflowRunStatus.RUNNING and self.hitl_client:
                try:
                    # Get pending tasks for this workflow
                    pending_tasks = await self.hitl_client.list_pending_tasks_for_workflow(workflow.run_id)
                    pending_tasks_count = len(pending_tasks)
                except Exception as e:  # noqa: BLE001
                    self.logger.warning(f"Failed to get pending tasks for workflow {workflow.run_id}: {e}")
                    # Continue with count of 0 if we can't get the tasks

            runs.append(
                WorkflowRun(
                    type=workflow.workflow_type,
                    id=workflow.run_id,
                    workflow_id=workflow.id,
                    status=workflow_status,
                    started=workflow.execution_time,
                    duration=str(self._round_seconds(duration)),
                    monitor=await self.get_workflow_ui_link(
                        workflow_id=workflow.id,
                        run_id=workflow.run_id,
                    ),
                    pending_tasks_count=pending_tasks_count,
                ),
            )

        return runs

    async def get_workflow_run(self, run_id: str) -> WorkflowRun | None:
        """Get a specific workflow run by run ID.

        Args:
            run_id: The workflow run ID

        Returns:
            WorkflowRun object if found, None otherwise

        """
        async for workflow in self.client.list_workflows():
            # Skip child workflows
            if workflow.parent_id is not None:
                continue

            if workflow.run_id == run_id:
                start_time = workflow.execution_time
                end_time = workflow.close_time
                duration = end_time - start_time if end_time else datetime.now(UTC) - start_time

                workflow_status = map_temporal_status(workflow.status)

                # Count pending tasks for running workflows
                pending_tasks_count = 0
                if workflow_status == WorkflowRunStatus.RUNNING and self.hitl_client:
                    try:
                        # Get pending tasks for this workflow
                        pending_tasks = await self.hitl_client.list_pending_tasks_for_workflow(workflow.run_id)
                        pending_tasks_count = len(pending_tasks)
                    except Exception as e:  # noqa: BLE001
                        self.logger.warning(f"Failed to get pending tasks for workflow {workflow.run_id}: {e}")
                        # Continue with count of 0 if we can't get the tasks

                return WorkflowRun(
                    type=workflow.workflow_type,
                    id=workflow.run_id,
                    workflow_id=workflow.id,
                    status=workflow_status,
                    started=workflow.execution_time,
                    duration=str(self._round_seconds(duration)),
                    monitor=await self.get_workflow_ui_link(
                        workflow_id=workflow.id,
                        run_id=workflow.run_id,
                    ),
                    pending_tasks_count=pending_tasks_count,
                )

        return None

    async def terminate_all_workflows(self) -> None:
        """Terminate all running workflows."""
        self.logger.info("Terminating workflows...")
        found_one = False

        async for workflow in self.client.list_workflows('ExecutionStatus = "Running"'):
            workflow_handle = self.client.get_workflow_handle(workflow.id)
            if workflow.status in (1, 0):  # RUNNING or UNSPECIFIED
                found_one = True
                self.logger.info(f"Terminating workflow {workflow.id} (status={workflow.status})...")
                await workflow_handle.terminate()

        if found_one:
            self.logger.info("Terminated workflows.")
        else:
            self.logger.info("No workflows to terminate.")

    async def get_workflow_ui_link(self, workflow_id: str, run_id: str) -> str:
        """Get the Temporal UI link for a workflow.

        Args:
            workflow_id: The workflow ID
            run_id: The run ID

        Returns:
            URL to the Temporal UI for this workflow

        """
        env_config = EnvConfig.get_env_config()
        host = env_config.temporal_ui_host
        port = env_config.temporal_ui_port

        return f"http://{host}:{port}/namespaces/{self.client.namespace}/workflows/{workflow_id}/{run_id}"

    def sort_workflows_by_status(
        self,
        workflows: list[WorkflowRun],
        status: WorkflowRunStatus,
    ) -> list[WorkflowRun]:
        """Sort workflows by status and start date.

        Args:
            workflows: List of workflow runs
            status: Status to prioritize

        Returns:
            Sorted list of workflow runs

        """
        return sorted(
            workflows,
            key=lambda x: (x.status != status, -x.started.timestamp()),
        )

    def _round_seconds(self, obj: timedelta) -> timedelta:
        """Round a timedelta to the nearest second.

        Args:
            obj: Timedelta to round

        Returns:
            Rounded timedelta

        """
        total_seconds = obj.total_seconds()
        rounded_seconds = round(total_seconds)
        return timedelta(seconds=rounded_seconds)
