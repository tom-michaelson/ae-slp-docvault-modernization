from pathlib import Path

from temporalio import workflow

from cookbook.recipes.decorators import recipe_exposed
from cookbook.recipes.workflows.awa_101.models.code_summary_result import CodeSummaryResult
from cookbook.recipes.workflows.awa_101.models.code_understanding_workflow_input import CodeUnderstandingWorkflowInput
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import TransformParams


@recipe_exposed("Summarizes a code file")
# region input
@workflow.defn(name="awa-102-advanced-direct-transform")
class Awa102AdvancedDirectTransformWorkflow:
    @workflow.run
    async def run(
        self,
        workflow_input: CodeUnderstandingWorkflowInput | None = None,
    ) -> CodeSummaryResult:
        workflow_paths = (
            workflow_input.workflow_paths
            if workflow_input and workflow_input.workflow_paths
            else awa_general.get_workflow_paths(Path(__file__).parent, workflow.info())
        )
        # endregion input

        # Read code file
        code_file_path = (
            workflow_input.code_file_path
            if workflow_input and workflow_input.code_file_path
            else Path(workflow_paths.input) / "hello-world-csharp" / "HelloWorld" / "Program.cs"
        )
        code_file_content = await awa_activity.read_file(Path(workflow_paths.input) / code_file_path)

        # Read additional instructions file (if present)
        # region read_additional_instructions
        additional_instructions = await awa_activity.read_file(
            file_path=Path(workflow_paths.input) / "additional_instructions.md",
            default="",
        )
        # endregion read_additional_instructions

        # Execute transform via BAML
        transform_params = TransformParams(
            baml_function_name="SummarizeCodeWithAdditionalInstructions",
            request={
                "code_file": code_file_content,
                "code_file_name": str(code_file_path),
                "additional_instructions": additional_instructions,
            },
        )

        code_summary = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=Path(workflow_paths.baml_src) / "summarize_code_with_additional_instructions.baml",
        )

        # Write summary file
        partial_code_file_path = Path(code_file_path).relative_to(Path(workflow_paths.input))
        output_file = Path(workflow_paths.output) / "code_summary" / partial_code_file_path.with_suffix(".md")

        await awa_activity.write_file(
            file_path=output_file,
            content=code_summary,
        )

        # region structured_result
        return CodeSummaryResult(
            code_file_path=str(code_file_path),
            code_file_content=code_file_content,
            code_summary=code_summary,
        )

        # endregion structured_result
