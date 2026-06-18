from datetime import timedelta

from temporalio import workflow

from awa.core import constants
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


@workflow.defn(name=sdk_constants.WORKFLOW_EXECUTE_AGENT)
class ExecuteAgentWorkflow:
    """Workflow for executing AI agents with configurable prompts and settings.

    This workflow provides a high-level interface for agent execution, supporting
    both direct prompt execution and dynamic prompt building from templates.
    It handles agent configuration, prompt preparation, and result processing.
    """

    def __init__(self) -> None:
        """Initialize the workflow."""
        self._parent_session_id: str | None = None

    @workflow.run
    async def run(self, agent_config: AgentConfiguration) -> TaskResponseModel:
        # Set default session IDs if stream_enabled is True
        if agent_config.stream_enabled:
            workflow_info = workflow.info()

            # Set parent_session_id to parent workflow ID if not provided
            if not agent_config.parent_session_id:
                agent_config.parent_session_id = workflow_info.parent.workflow_id if workflow_info.parent else None

            # Set stream_session_id to current workflow ID if not provided
            if not agent_config.stream_session_id:
                agent_config.stream_session_id = workflow_info.workflow_id

        # Store parent_session_id for query access
        self._parent_session_id = agent_config.parent_session_id
        if agent_config.prompt and agent_config.build_prompt_params:
            raise ValueError("prompt and build_prompt_params cannot both be set")

        if agent_config.build_prompt_params:
            agent_config.prompt = await workflow.execute_child_workflow(
                workflow=sdk_constants.WORKFLOW_BUILD_PROMPT,
                arg=agent_config.build_prompt_params,
            )

        # Use streaming activity if stream_session_id is provided
        activity_name = (
            sdk_constants.ACTIVITY_EXECUTE_AGENT_STREAMING
            if agent_config.stream_session_id
            else sdk_constants.ACTIVITY_EXECUTE_AGENT
        )

        agent_result: TaskResponseModel = TaskResponseModel.model_validate(
            await workflow.execute_activity(
                activity=activity_name,
                args=[agent_config],
                start_to_close_timeout=timedelta(
                    seconds=agent_config.timeout_seconds or constants.DEFAULT_AGENT_ACTIVITY_TIMEOUT_SECONDS,
                ),
            ),
        )

        return agent_result

    @workflow.query
    def get_parent_session_id(self) -> str | None:
        """Query to get the parent session ID for this agent workflow.

        Returns:
            Parent session ID or None if this workflow is not part of a streaming session

        """
        return self._parent_session_id
