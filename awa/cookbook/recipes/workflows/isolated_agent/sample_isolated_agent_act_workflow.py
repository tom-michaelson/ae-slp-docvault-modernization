"""Sample workflow demonstrating isolated agent execution in ACT mode."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed

with workflow.unsafe.imports_passed_through():
    from sdk_dist.python.awa.client import awa_general, awa_workflow
    from sdk_dist.python.awa.client.models import (
        AgentConfiguration,
        AgentModeEnum,
        AgentProviderEnum,
        IsolatedAgentParams,
        TaskResponseModel,
        WorkflowPaths,
    )

from .models.workflow_input import SampleIsolatedAgentActWorkflowInput


@recipe_exposed("Executes agents in isolated git worktrees (ACT mode)")
@workflow.defn(name="sample-isolated-agent-act")
class SampleIsolatedAgentActWorkflow:
    """Sample workflow demonstrating isolated agent execution in ACT mode.

    This workflow shows how to use the IsolatedAgentChildWorkflow to execute
    agents in isolated git worktrees for making changes to code repositories.
    """

    def __init__(self) -> None:
        """Initialize the workflow."""
        self.workflow_paths: WorkflowPaths | None = None

    @workflow.run
    async def run(self, input_data: SampleIsolatedAgentActWorkflowInput) -> TaskResponseModel:
        """Execute a sample isolated agent in ACT mode.

        Args:
            input_data: Input containing repo path and branch

        Returns:
            TaskResponseModel with the agent execution result

        """
        workflow.logger.info(f"Starting sample isolated agent ACT workflow for {input_data.repo_path}")

        # Initialize workflow paths
        self.workflow_paths = awa_general.get_workflow_paths(
            Path(__file__).parent,
            workflow.info(),
        )

        # Configure agent for ACT mode using AWA SDK models and enums
        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ACT,
            provider=AgentProviderEnum.CLAUDE,
            prompt=(
                "Add comprehensive logging to any Python files that are missing it. "
                "Use the logging library and use a logging BasicConfig"
            ),
            initialize=False,
            working_directory=input_data.repo_path,
        )

        # Create isolated agent parameters using AWA SDK model
        isolated_params = IsolatedAgentParams(
            source_directory=input_data.repo_path,
            source_branch=input_data.branch,
            agent_config=agent_config,
            agent_execution_timeout_minutes=15,
        )

        # Execute the isolated agent using AWA SDK utility
        result: TaskResponseModel = await awa_workflow.isolated_agent(
            params=isolated_params,
            workflow_id=f"isolated_agent_{workflow.info().workflow_id}",
        )

        workflow.logger.info(f"Sample isolated agent ACT workflow completed: {result.status}")
        return result
