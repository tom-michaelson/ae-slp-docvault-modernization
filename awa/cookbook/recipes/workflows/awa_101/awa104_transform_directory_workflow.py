import asyncio
from pathlib import Path

from temporalio import workflow

from cookbook.recipes.decorators import recipe_exposed
from cookbook.recipes.workflows.awa_101.awa103_transform_chain_workflow import Awa103TransformChainWorkflow
from cookbook.recipes.workflows.awa_101.models.code_understanding_workflow_input import CodeUnderstandingWorkflowInput
from sdk_dist.python.awa.client import awa_activity, awa_general
from sdk_dist.python.awa.client.models import WorkflowPaths


@recipe_exposed("Summarizes and then extracts technical requirements from a set of code files")
@workflow.defn(name="awa-104-transform-directory")
class Awa104TransformDirectoryWorkflow:
    @workflow.run
    async def run(self, workflow_paths: WorkflowPaths | None = None) -> str:
        workflow_paths = workflow_paths or awa_general.get_workflow_paths(
            Path(__file__).parent,
            workflow.info(),
        )

        # region iterate_files
        # Iterate directory, then execute AWA-103 workflow for each file
        files = await awa_activity.list_directory(
            str(Path(workflow_paths.input) / "hello-world-csharp"),
            Path(workflow_paths.input) / "file_filters.gitignore",
        )
        # endregion iterate_files

        # region execute_child_workflow
        # Execute AWA-103 workflow for each file to get code summaries and technical requirements
        tasks = [
            workflow.execute_child_workflow(
                workflow=Awa103TransformChainWorkflow.run,
                arg=CodeUnderstandingWorkflowInput(code_file_path=str(file), workflow_paths=workflow_paths),
            )
            for file in files
        ]

        _ = await asyncio.gather(*tasks)
        # endregion execute_child_workflow

        # Return result
        return f"Done. Processed {len(files)!s} files."
