"""Sample workflow demonstrating isolated agent execution in ANALYZE mode."""

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

from .models.workflow_input import SampleIsolatedAgentAnalyzeWorkflowInput


@recipe_exposed("Executes agents in isolated directories (ANALYZE mode)")
@workflow.defn(name="sample-isolated-agent-analyze")
class SampleIsolatedAgentAnalyzeWorkflow:
    """Sample workflow demonstrating isolated agent execution in ANALYZE mode.

    This workflow shows how to use the IsolatedAgentChildWorkflow to execute
    agents in isolated temporary directories for security analysis without
    making changes to the original directory.
    """

    def __init__(self) -> None:
        """Initialize the workflow."""
        self.workflow_paths: WorkflowPaths | None = None

    @workflow.run
    async def run(self, input_data: SampleIsolatedAgentAnalyzeWorkflowInput) -> TaskResponseModel:
        """Execute a sample isolated agent in ANALYZE mode.

        Args:
            input_data: Input containing directory path and output directory

        Returns:
            TaskResponseModel with the agent execution result

        """
        workflow.logger.info(f"Starting sample isolated agent ANALYZE workflow for {input_data.directory_path}")

        # Initialize workflow paths
        self.workflow_paths = awa_general.get_workflow_paths(
            Path(__file__).parent,
            workflow.info(),
        )

        # Configure agent for ANALYZE mode using AWA SDK models and enums
        agent_config = AgentConfiguration(
            mode=AgentModeEnum.ANALYZE,
            provider=AgentProviderEnum.CLAUDE,
            prompt=(
                "Perform a comprehensive security vulnerability analysis of this codebase. "
                "Examine all code files for common security issues such as: "
                "- SQL injection vulnerabilities "
                "- Cross-site scripting (XSS) vulnerabilities "
                "- Insecure authentication or authorization "
                "- Hardcoded secrets or credentials "
                "- Insecure file handling "
                "- Command injection vulnerabilities "
                "- Unsafe deserialization "
                "- Missing input validation "
                "- Insecure dependencies "
                "- Configuration security issues "
                "\n\n"
                f"Generate a detailed security analysis report in markdown format and save it to "
                f"the {input_data.output_directory} directory as 'security_analysis_report.md'. "
                "The report should include: "
                "1. Executive Summary "
                "2. Methodology "
                "3. Findings (categorized by severity: Critical, High, Medium, Low) "
                "4. Detailed vulnerability descriptions with code references "
                "5. Remediation recommendations "
                "6. Conclusion "
                "\n\n"
                "Do not modify any source code files - only analyze them and produce the report."
            ),
            initialize=False,
            working_directory=input_data.directory_path,
        )

        # Create isolated agent parameters using AWA SDK model
        isolated_params = IsolatedAgentParams(
            source_directory=input_data.directory_path,
            agent_config=agent_config,
            agent_execution_timeout_minutes=20,
            output_directory=input_data.output_directory,
        )

        # Execute the isolated agent using AWA SDK utility
        result: TaskResponseModel = await awa_workflow.isolated_agent(
            params=isolated_params,
            workflow_id=f"isolated_agent_{workflow.info().workflow_id}",
        )

        workflow.logger.info(f"Sample isolated agent ANALYZE workflow completed: {result.status}")
        return result
