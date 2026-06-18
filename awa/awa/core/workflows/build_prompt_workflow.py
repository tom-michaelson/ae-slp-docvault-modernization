import asyncio
from datetime import timedelta

from temporalio import workflow

from awa.core import constants
from awa.sdk import constants as sdk_constants
from awa.sdk.models.build_prompt_params import BuildPromptParams


@workflow.defn(name=sdk_constants.WORKFLOW_BUILD_PROMPT)
class BuildPromptWorkflow:
    @workflow.run
    async def run(self, workflow_input: BuildPromptParams) -> str:
        """Build a prompt from a template and variables.

        Args:
            workflow_input: The input parameters for the build prompt workflow.

        Returns:
            The resolved template.

        """
        if not workflow_input.template and not workflow_input.template_input:
            raise ValueError("Either template or template_input must be provided")

        template: str | None = workflow_input.template
        if not template:
            template = await workflow.execute_local_activity(
                activity=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY,
                arg=workflow_input.template_input,
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

        variables = workflow_input.variables or {}
        if workflow_input.inputs:
            # Read files in parallel and populate request with file contents
            file_read_tasks = []
            file_keys = []

            for input_item in workflow_input.inputs:
                task = workflow.execute_local_activity(
                    activity=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY,
                    arg=input_item,
                    start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
                )
                file_read_tasks.append(task)
                file_keys.append(input_item.name)

            # Execute all file reads in parallel
            file_contents = await asyncio.gather(*file_read_tasks)

            # Merge file contents into the request dict
            for key, content in zip(file_keys, file_contents, strict=False):
                if key in variables:
                    raise ValueError(f"Key {key} already exists in variables")
                variables[key] = content

        resolved_template = await workflow.execute_local_activity(
            sdk_constants.ACTIVITY_RESOLVE_TEMPLATE,
            args=[template, variables],
            start_to_close_timeout=timedelta(
                seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS,
            ),
        )

        if workflow_input.output_path:
            await workflow.execute_local_activity(
                sdk_constants.ACTIVITY_WRITE_FILE,
                args=[workflow_input.output_path, resolved_template],
                start_to_close_timeout=timedelta(
                    seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS,
                ),
            )

        return resolved_template
