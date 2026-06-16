"""Activity to get the top-level workflow ID for logging purposes."""

from temporalio import activity
from temporalio.client import Client

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.temporal_utils import TemporalUtils
from awa.sdk.constants import ACTIVITY_GET_TOP_LEVEL_WORKFLOW_INFO


class GetTopLevelWorkflowIdActivity:
    """Activity to retrieve the top-level workflow ID in a workflow hierarchy."""

    def __init__(self, temporal_client: Client) -> None:
        """Initialize the activity with a Temporal client.

        Args:
            temporal_client: The Temporal client instance used for workflow operations.

        """
        self._temporal_client = temporal_client
        self.logger = get_logger(LoggerComponent.ACTIVITY)

    @activity.defn(name=ACTIVITY_GET_TOP_LEVEL_WORKFLOW_INFO)
    async def get_top_level_workflow_id_activity(self) -> str:
        """Get the top-level workflow ID by traversing the parent hierarchy.

        As a side effect, this also sets the top-level workflow type in the context.

        Returns:
            The ID of the top-most parent workflow.

        """
        # Import here to avoid circular imports
        from awa.core.logger.workflow_context import set_top_level_workflow_type

        top_level_workflow_info = await TemporalUtils.get_top_level_workflow_info_from_activity(self._temporal_client)

        # Set the workflow type in context as a side effect
        set_top_level_workflow_type(top_level_workflow_info.workflow_type)
        return top_level_workflow_info.workflow_id
