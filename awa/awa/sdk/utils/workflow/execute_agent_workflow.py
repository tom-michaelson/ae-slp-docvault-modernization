from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


async def execute_agent_workflow(
    agent_config: AgentConfiguration,
    timeout_seconds: int | None = None,
    name: str | None = None,
) -> TaskResponseModel:
    """Execute an agent with the specified configuration.

    Args:
        agent_config: The configuration for the agent to execute.
        timeout_seconds: Optional timeout in seconds for agent execution.
            If not provided, uses agent_config.timeout_seconds or default.
        name: Optional name for the agent execution, used in workflow ID generation.

    Returns:
        TaskResponseModel: The result of the agent execution.

    """
    if not agent_config.timeout_seconds:
        agent_config.timeout_seconds = timeout_seconds or constants.AGENT_TIMEOUT_SECONDS
    return TaskResponseModel.model_validate(
        await workflow.execute_child_workflow(
            workflow=constants.WORKFLOW_EXECUTE_AGENT,
            args=[agent_config],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            id=f"{name}-{workflow.info().workflow_id}" if name else None,
        ),
    )
