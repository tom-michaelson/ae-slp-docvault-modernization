import json
from datetime import timedelta
from typing import Any

from pydantic import BaseModel
from temporalio import workflow

from awa.sdk import constants as sdk_constants
from awa.sdk.models.transform_params import TransformParams


class FileBasedTransformInput(BaseModel):
    input_path: str
    output_path: str


@workflow.defn(name=sdk_constants.WORKFLOW_TRANSFORM_FILE)
class TransformFileWorkflow:
    @workflow.run
    async def run(self, workflow_input: FileBasedTransformInput) -> str:
        """Read a request from a file, transform the data, and write the result.

        This workflow reads a JSON request from a file specified in the input,
        uses the transform_activity to process it, and writes the final poem
        to an output file.

        Args:
            workflow_input: An object containing the input and output file paths.

        Returns:
            A string indicating the successful completion and the output path.

        """
        # Read the request from the input file
        request_json = await workflow.execute_activity(
            sdk_constants.ACTIVITY_READ_FILE,
            workflow_input.input_path,
            start_to_close_timeout=timedelta(seconds=5),
        )
        request_data = json.loads(request_json)

        # Prepare parameters for the transform activity
        params = TransformParams(
            baml_function_name="WritePoem",
            request=request_data,
        )

        # Execute the transformation
        raw_response: dict[str, Any] = await workflow.execute_activity(
            sdk_constants.ACTIVITY_TRANSFORM,
            params,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Write the poem to the output file
        await workflow.execute_activity(
            sdk_constants.ACTIVITY_WRITE_FILE,
            args=[workflow_input.output_path, raw_response.get("poem", "")],
            start_to_close_timeout=timedelta(seconds=5),
        )

        return f"Poem successfully written to {workflow_input.output_path}"
