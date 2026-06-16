"""Workflow for applying diffs to a single file based on natural language requests."""

from datetime import timedelta
from typing import Any

from pydantic import BaseModel
from temporalio import workflow

from awa.core import constants
from awa.core.models.apply_diff_result import ApplyDiffResult
from awa.sdk import constants as sdk_constants
from awa.sdk.models.transform_params import TransformParams


class SingleFileDiffInput(BaseModel):
    """Input for the SingleFileDiffWorkflow."""

    file_path: str
    natural_language_request: str
    fallback_to_full_apply: bool = False


class DiffGenerationInput(BaseModel):
    file_path: str
    file_content: str
    natural_language_request: str


class SingleFileDiffOutput(BaseModel):
    """Output for the SingleFileDiffWorkflow."""

    success: bool
    file_path: str
    message: str


@workflow.defn(name=sdk_constants.WORKFLOW_APPLY_SINGLE_FILE_DIFF)
class ApplySingleFileDiffWorkflow:
    """Workflow for applying diffs to a single file based on natural language requests.

    This workflow reads the content of a file, generates a diff based on a natural language
    request, and applies the diff to the file. It uses three activities:
    - read_file: Reads the content of the file.
    - generate_file_diff: Generates a diff based on the file content and natural language request.
    - apply_diff: Applies the diff to the file.
    """

    max_attempts_before_falling_back_to_full_rewrite = 2

    @workflow.run
    async def run(self, workflow_input: SingleFileDiffInput) -> SingleFileDiffOutput:
        """Run the single file diff workflow.

        Args:
            workflow_input: An object containing the file path and natural language request.

        Returns:
            An object containing the success status, file path, and a message.

        """
        workflow.logger.info("Starting SingleFileDiffWorkflow")
        workflow.logger.info(f"Workflow ID: {workflow.info().workflow_id}")
        workflow.logger.info(f"Task queue: {workflow.info().task_queue}")
        workflow.logger.info(f"Run ID: {workflow.info().run_id}")
        workflow.logger.info(f"File path: {workflow_input.file_path}")
        workflow.logger.info(f"Natural language request: {workflow_input.natural_language_request}")

        # Read the file content
        if workflow_input.file_path != "":
            file_content = await workflow.execute_activity(
                sdk_constants.ACTIVITY_READ_FILE,
                workflow_input.file_path,
                start_to_close_timeout=timedelta(seconds=5),
            )
        else:
            file_content = ""

        # Prepare parameters for the transform activity
        request_data = DiffGenerationInput(
            file_path=workflow_input.file_path,
            file_content=file_content,
            natural_language_request=workflow_input.natural_language_request,
        )

        result: ApplyDiffResult | None = None
        diff_text: str | None = None
        attempt = 0
        while (not result or not result.success) and attempt < self.max_attempts_before_falling_back_to_full_rewrite:
            attempt += 1

            function_name = "GenerateFileDiffRetry" if diff_text else "GenerateFileDiff"
            request = request_data.model_dump()
            if diff_text:
                request["invalid_diff"] = diff_text
            diff_text_result = await workflow.execute_activity(
                sdk_constants.ACTIVITY_TRANSFORM,
                TransformParams(
                    baml_function_name=function_name,
                    request=request,
                ),
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS),
            )

            diff_text = diff_text_result["diff_string"]

            # Apply the diff
            result_raw: dict[str, Any] = await workflow.execute_activity(
                sdk_constants.ACTIVITY_APPLY_DIFF,
                diff_text,
                start_to_close_timeout=timedelta(seconds=10),
            )

            result = ApplyDiffResult.model_validate(result_raw)

            if not result.success:
                workflow.logger.warning(
                    f"Failed to apply diff for {workflow_input.file_path} (attempt {attempt}): {result.message}",
                )

        if result.success:
            return SingleFileDiffOutput(
                success=True,
                file_path=workflow_input.file_path,
                message=f"Successfully applied changes to {workflow_input.file_path}",
            )

        if workflow_input.fallback_to_full_apply:
            # TODO RH: Prompt to get complete new file content
            workflow.logger.warning(f"Falling back to rewriting full file for {workflow_input.file_path}")
            new_file_content_result = await workflow.execute_activity(
                activity=sdk_constants.ACTIVITY_TRANSFORM,
                arg=TransformParams(
                    baml_function_name="RewriteFile",
                    request=request,
                ),
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_BAML_ACTIVITY_TIMEOUT_SECONDS),
            )
            new_file_content = new_file_content_result["complete_new_file_content"]
            await workflow.execute_activity(
                activity=sdk_constants.ACTIVITY_WRITE_FILE,
                args=[workflow_input.file_path, new_file_content],
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )
            return SingleFileDiffOutput(
                success=True,
                file_path=workflow_input.file_path,
                message=f"Successfully applied change, but had to fallback to rewriting full file. "
                f"Failed to apply changes after {attempt} attempts to {workflow_input.file_path}. ",
            )

        return SingleFileDiffOutput(
            success=False,
            file_path=workflow_input.file_path,
            message=f"Failed to apply changes after {attempt} attempts to {workflow_input.file_path}: {result.message}",
        )
