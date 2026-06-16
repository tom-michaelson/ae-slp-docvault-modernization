from temporalio import activity
from temporalio.client import Client

from awa.core.utils.temporal_utils import TemporalUtils
from awa.sdk import constants as sdk_constants


class GetParentWorkflowTaskQueueActivity:
    def __init__(self, temporal_client: Client) -> None:
        """Initialize the GetParentWorkflowTaskQueueActivity with a Temporal client.

        Args:
            temporal_client: The Temporal client instance used for workflow operations.

        """
        self._temporal_client = temporal_client

    @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
    async def get_parent_workflow_task_queue_activity(self) -> str:
        """Get the task queue of the top-most parent workflow of a workflow.

        Args:
            workflow_info: The workflow info.

        Returns:
            The task queue of the top-most parent workflow of the workflow.

        """
        return await TemporalUtils.get_parent_workflow_task_queue_for_activity(
            self._temporal_client,
            activity.info(),
        )
