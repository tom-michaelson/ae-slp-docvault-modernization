import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from temporalio import workflow

from cookbook.recipes.constants import AWA_WORKFLOW_LEGACY_TO_REACT
from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import (
    AgentConfiguration,
    BuildPromptParams,
    InputParams,
    JiraIssueRequest,
    McpServer,
    TransformParams,
)

from .models.workflow_input import LegacyToReactWorkflowInput

if TYPE_CHECKING:
    from sdk_dist.python.awa.client.models import WorkflowPaths

# TODO RH: Bug: we need to handle cross-file type references in BAML. Currently we only ship the single file.


@recipe_exposed("Converts legacy COBOL code to modern React applications")
@workflow.defn(name=AWA_WORKFLOW_LEGACY_TO_REACT)
class LegacyToReactWorkflow:
    """Workflow to convert legacy COBOL code to modern React applications."""

    def __init__(self) -> None:
        """Initialize the workflow."""
        self.workflow_paths: WorkflowPaths | None = None
        self.jira_issue_id: str = ""
        self.jira_issue_url: str = ""

    @workflow.run
    async def run(self, workflow_input: LegacyToReactWorkflowInput | None = None) -> str:
        """Execute the workflow to convert COBOL to React."""
        workflow.logger.info("Starting Legacy to React conversion workflow")

        if not workflow_input:
            workflow_input = LegacyToReactWorkflowInput(
                cobol_file_path="legacy_code.cbl",
                react_app_path="react-baseline-app",
                jira_project_key="TSKSTRM",
                jira_instance_url="https://slalom.atlassian.net",
            )

        # Initialize workflow paths
        self.workflow_paths = awa_general.get_workflow_paths(
            Path(__file__).parent,
            workflow.info(),
        )

        # Step 1: Read COBOL file
        cobol_content = await awa_activity.read_file(
            str(Path(self.workflow_paths.input) / workflow_input.cobol_file_path),
        )

        # Step 2: Extract requirements from COBOL
        transform_params = TransformParams(
            baml_function_name="ExtractCobolRequirements",
            request={"cobol_code": cobol_content},
            output_path=str(Path(self.workflow_paths.output) / "requirements.json"),
        )
        requirements: dict[str, Any] = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "extract_cobol_requirements.baml"),
        )

        # Step 3: Create user story
        transform_params = TransformParams(
            baml_function_name="CreateUserStory",
            request={"requirements": requirements},
            output_path=str(Path(self.workflow_paths.output) / "user_story.json"),
        )
        user_story: dict[str, Any] = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "create_user_story.baml"),
        )

        # Step 4: Save to JIRA
        jira_request = JiraIssueRequest(
            project_id=workflow_input.jira_project_key,
            issue_type="Story",
            summary=user_story.get("title", "UNKNOWN"),
            description=user_story.get("description", "UNKNOWN"),
        )
        self.jira_issue_id = await awa_activity.upsert_jira_issue(jira_request)
        self.jira_issue_url = f"{workflow_input.jira_instance_url}/browse/{self.jira_issue_id}"

        # Step 5: Create implementation plan
        transform_params = TransformParams(
            baml_function_name="CreateImplementationPlan",
            request={
                "user_story": user_story,
                "requirements": requirements,
            },
            output_path=str(Path(self.workflow_paths.output) / "implementation_plan.json"),
        )
        implementation_plan: dict[str, Any] = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "create_implementation_plan.baml"),
        )

        # Step 6: Copy baseline React app
        react_source_path = str(Path(self.workflow_paths.input) / workflow_input.react_app_path)
        await awa_activity.copy_directory(
            source_path=react_source_path,
            destination_path=str(Path(self.workflow_paths.output) / "react-app"),
            ignore_file_path=str(Path(react_source_path) / ".gitignore"),
        )

        # Step 8: Implement React component using BAML function
        target_react_file_path = str(Path(self.workflow_paths.output) / "react-app" / "src" / "App.tsx")
        transform_params = TransformParams(
            baml_function_name="ImplementReactComponent",
            request={
                "implementation_plan": json.dumps(implementation_plan, indent=2),
                "user_story": json.dumps(user_story, indent=2),
                "requirements": json.dumps(requirements, indent=2),
            },
            inputs=[
                InputParams(
                    name="existing_app_tsx",
                    path=target_react_file_path,
                ),
            ],
            output_path=target_react_file_path,
        )
        updated_react_file: str = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "implement_react_component.baml"),
        )

        # Step 9: Build and run verification using Playwright MCP
        react_app_path = str(Path(self.workflow_paths.output) / "react-app")
        mcp_json = await awa_activity.read_file(str(Path(self.workflow_paths.agent_prompts) / "mcp.json"))

        # Create proper AgentConfiguration model
        agent_config = AgentConfiguration(
            provider="claude",
            mode="act",
            build_prompt_params=BuildPromptParams(
                template_input={
                    "path": str(Path(self.workflow_paths.agent_prompts) / "build_verification.jinja"),
                },
                variables={"react_app_path": react_app_path},
            ),
            initialize=False,
            working_directory=react_app_path,
            mcp=McpServer(mcp_json=mcp_json),
        )

        _ = await awa_workflow.execute_agent(
            name="ReactBuildVerification",
            agent_config=agent_config,
            timeout_seconds=600,
        )

        # Step 10: Code review - only review changed files
        # Get list of changed files by comparing with baseline
        transform_params = TransformParams(
            baml_function_name="PerformCodeReview",
            request={
                "react_code": updated_react_file,
                "requirements": json.dumps(requirements, indent=2),
                "user_story": json.dumps(user_story, indent=2),
            },
            output_path=str(Path(self.workflow_paths.output) / "code_review_report.md"),
        )
        code_review_report = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "perform_code_review.baml"),
        )

        # Step 11: Write unit tests using BAML function
        transform_params = TransformParams(
            baml_function_name="WriteUnitTests",
            request={
                "react_code": updated_react_file,
                "acceptance_criteria": json.dumps(user_story.get("acceptance_criteria", []), indent=2),
            },
            output_path=str(Path(self.workflow_paths.output) / "react-app" / "src" / "App.test.tsx"),
        )
        _ = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "write_unit_tests.baml"),
        )

        # Step 12: Generate summary report
        transform_params = TransformParams(
            baml_function_name="GenerateSummaryReport",
            request={
                "cobol_file": workflow_input.cobol_file_path,
                "requirements": json.dumps(requirements, indent=2),
                "user_story": json.dumps(user_story, indent=2),
                "jira_url": self.jira_issue_url,
                "code_review": json.dumps(code_review_report, indent=2),
            },
            output_path=str(Path(self.workflow_paths.output) / "summary-report.md"),
        )
        summary_report = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=str(Path(self.workflow_paths.baml_src) / "generate_summary_report.baml"),
        )

        workflow.set_current_details(summary_report)

        return f"Workflow completed successfully. JIRA issue: {self.jira_issue_url}"
