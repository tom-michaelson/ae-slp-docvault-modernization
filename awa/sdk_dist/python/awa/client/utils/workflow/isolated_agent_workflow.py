from temporalio import workflow

from awa.client import constants
from awa.client.models.agent_modes.isolated_agent_models import IsolatedAgentParams
from awa.client.models.agent_modes.task_response_model import TaskResponseModel


async def isolated_agent_workflow(
    params: IsolatedAgentParams,
    workflow_id: str | None = None,
) -> TaskResponseModel:
    """Execute an agent in an isolated environment.

    This workflow implements complete separation of concerns:
    1. Environment setup is fully encapsulated in setup activities
    2. Agent execution is completely unaware of environment context
    3. Cleanup and output handling are managed by dedicated activities

    For ACT mode: Uses git worktree for isolated execution and merges changes back
    For ANALYZE mode: Uses temporary directory copy for isolated execution and copies outputs back

    Args:
        params: Parameters containing source directory, agent config, and options including:
            - source_directory: Source directory path (can be Git repo or regular directory)
            - source_branch: Source branch name (only used for Git repositories in ACT mode)
            - agent_config: Agent configuration for execution
            - agent_execution_timeout_minutes: Timeout in minutes for agent execution (default: 10)
            - output_directory: Directory name for agent outputs in analyze mode (default: "awa-agent-output")
        workflow_id: Optional custom workflow ID. If not provided, will be auto-generated.

    Returns:
        TaskResponseModel: The result of the agent execution with status and details.

    """
    return TaskResponseModel.model_validate(
        await workflow.execute_child_workflow(
            workflow=constants.WORKFLOW_ISOLATED_AGENT,
            arg=params,
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            id=workflow_id or f"isolated-agent-{workflow.info().workflow_id}",
        ),
    )
