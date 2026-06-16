from pathlib import Path
from typing import TYPE_CHECKING

from temporalio import workflow

from cookbook.recipes.decorators import recipe_exposed
from cookbook.recipes.workflows.awa_101.awa102_advanced_direct_transform_workflow import (
    Awa102AdvancedDirectTransformWorkflow,
)
from cookbook.recipes.workflows.awa_101.models.code_understanding_workflow_input import CodeUnderstandingWorkflowInput
from sdk_dist.python.awa.client import awa_activity, awa_general, awa_workflow
from sdk_dist.python.awa.client.models import TransformParams

if TYPE_CHECKING:
    from cookbook.recipes.workflows.awa_101.models.code_summary_result import CodeSummaryResult


@recipe_exposed("Summarizes and then extracts technical requirements from a code file")
@workflow.defn(name="awa-103-transform-chain")
class Awa103TransformChainWorkflow:
    @workflow.run
    async def run(self, workflow_input: CodeUnderstandingWorkflowInput | None = None) -> str:
        workflow_paths = (
            workflow_input.workflow_paths
            if workflow_input and workflow_input.workflow_paths
            else awa_general.get_workflow_paths(Path(__file__).parent, workflow.info())
        )

        # region code_summary
        # Execute AWA-102 workflow to get code summary
        code_summary_result: CodeSummaryResult = await workflow.execute_child_workflow(
            workflow=Awa102AdvancedDirectTransformWorkflow.run,
            arg=workflow_input or CodeUnderstandingWorkflowInput(workflow_paths=workflow_paths),
        )
        # endregion code_summary

        # region technical_requirements
        # Execute transform via BAML
        transform_params = TransformParams(
            baml_function_name="ExtractTechnicalRequirements",
            request={
                "code_file": code_summary_result.code_file_content,
                "code_file_name": str(code_summary_result.code_file_path),
                "the_code_summary": code_summary_result.code_summary,
            },
        )

        technical_requirements = await awa_workflow.execute_baml_transform(
            transform_params=transform_params,
            baml_path=Path(workflow_paths.baml_src) / "extract_technical_requirements.baml",
        )
        # endregion technical_requirements

        # Write technical requirements file
        partial_code_file_path = Path(code_summary_result.code_file_path).relative_to(Path(workflow_paths.input))
        output_path = Path(workflow_paths.output) / "technical_requirements" / partial_code_file_path.with_suffix(".md")
        await awa_activity.write_file(output_path, technical_requirements)

        return technical_requirements
