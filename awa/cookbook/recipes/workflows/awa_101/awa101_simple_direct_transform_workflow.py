from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from cookbook.recipes import constants
from cookbook.recipes.decorators import recipe_exposed
from sdk_dist.python.awa.client.models import WorkflowPaths


@recipe_exposed("Summarizes a code file")
@workflow.defn(name="awa-101-simple-direct-transform")
class Awa101SimpleDirectTransformWorkflow:
    @workflow.run
    async def run(self) -> str:
        workflow.logger.info("Hello from AWA 101!")

        # region get_workflow_paths
        # Get workflow paths
        workflow_dir = Path(__file__).parent
        workflow_info = workflow.info()
        workflow_paths = WorkflowPaths(
            input=str(Path(workflow_dir) / "input"),
            output=str(Path(workflow_dir) / "output" / workflow_info.workflow_type / workflow_info.workflow_id),
            baml_src=str(Path(workflow_dir) / "baml_src"),
        )
        # endregion get_workflow_paths

        # region read_code_file
        # Read code file
        code_file_path = Path(workflow_paths.input) / "hello-world-csharp" / "HelloWorld" / "Program.cs"
        code_file_content = await workflow.execute_activity(
            constants.AWA_ACTIVITY_READ_FILE,
            args=[str(code_file_path), None],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
        )
        request_data = {
            "code_file": code_file_content,
            "code_file_name": str(code_file_path),
        }
        # endregion read_code_file

        # Get BAML content
        baml_content = await workflow.execute_activity(
            constants.AWA_ACTIVITY_READ_FILE,
            args=[str(Path(workflow_paths.baml_src) / "summarize_code.baml"), None],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
        )

        # region execute_baml_transform
        # Execute transform via BAML
        transform_result = await workflow.execute_child_workflow(
            workflow=constants.AWA_WORKFLOW_TRANSFORM,
            arg={
                "baml_function_name": "SummarizeCode",
                "baml_content": baml_content,
                "request": request_data,
                "timeout_seconds": constants.BAML_TIMEOUT_SECONDS,
            },
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            execution_timeout=timedelta(seconds=constants.BAML_TIMEOUT_SECONDS * 2),
        )

        # endregion execute_baml_transform

        # region write_summary_file
        # Write summary file
        partial_code_file_path = Path(code_file_path).relative_to(Path(workflow_paths.input))
        output_file = Path(workflow_paths.output) / "code_summary" / partial_code_file_path.with_suffix(".md")
        await workflow.execute_activity(
            constants.AWA_ACTIVITY_WRITE_FILE,
            args=[str(output_file), transform_result],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
        )

        # Return result
        return transform_result
        # endregion write_summary_file
