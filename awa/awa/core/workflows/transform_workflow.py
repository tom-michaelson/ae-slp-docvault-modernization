import asyncio
import base64
import json
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from temporalio import exceptions, workflow

from awa.core import constants
from awa.sdk import constants as sdk_constants
from awa.sdk.models.baml_image_input_params import BamlImageInputParams
from awa.sdk.models.transform_params import TransformParams

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from awa.sdk.models.input_params import InputParams


def _extract_json_path(data: Any, json_path: str) -> Any | None:  # noqa: ANN401
    """Extract data using a simple JSON path query.

    Supports basic JSON path syntax like:
    - $.field_name - extract field from root object
    - $['field_name'] - extract field from root object (bracket notation)

    Args:
        data: The data to extract from
        json_path: The JSON path query string

    Returns:
        The extracted value or None if not found

    """
    try:
        if not json_path.startswith("$"):
            return None

        # Remove the initial $
        path = json_path[1:]

        # Handle dot notation: $.field_name
        if path.startswith("."):
            field_name = path[1:]  # Remove the dot
            if isinstance(data, dict) and field_name in data:
                return data[field_name]

        # Handle bracket notation: $['field_name']
        elif path.startswith("['") and path.endswith("']"):
            field_name = path[2:-2]  # Remove ['...']
            if isinstance(data, dict) and field_name in data:
                return data[field_name]

        return None
    except (TypeError, KeyError, IndexError):
        return None


@workflow.defn(name=sdk_constants.WORKFLOW_TRANSFORM)
class TransformWorkflow:
    @workflow.run
    async def run(self, workflow_input: TransformParams) -> Any:  # noqa: ANN401, PLR0915
        """Execute a transform activity.

        Note: Currently this just executes the transform activity. However, in the future,
        having a workflow here will allow us to provide more functionality by default (e.g. response streaming).

        Args:
            workflow_input: The input parameters for the transform activity.

        Returns:
            The raw response from the transform activity.

        """
        if workflow_input.inputs:
            # Read files in parallel and populate request with file contents
            file_read_tasks = []
            file_keys: list[InputParams] = []

            for input_item in workflow_input.inputs:
                task: Coroutine[Any, Any, Any]
                if input_item.image_mime_type:
                    task = workflow.execute_local_activity(
                        activity=sdk_constants.ACTIVITY_READ_FILE_BYTES,
                        args=[input_item.path, input_item.default],
                        start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
                    )
                else:
                    task = workflow.execute_local_activity(
                        activity=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY,
                        args=[input_item],
                        start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
                    )
                file_read_tasks.append(task)
                file_keys.append(input_item)

            # Execute all file reads in parallel
            file_contents = await asyncio.gather(*file_read_tasks)

            # Ensure request is a dict, initialize if None
            if workflow_input.request is None:
                workflow_input.request = {}

            # Merge file contents into the request dict if it's a dict
            if isinstance(workflow_input.request, dict):
                for input_item, content in zip(file_keys, file_contents, strict=False):
                    if input_item.name in workflow_input.request:
                        raise exceptions.ApplicationError(
                            f"Key {input_item.name} already exists in request",
                        )

                    if input_item.image_mime_type and isinstance(content, bytes):
                        if not workflow_input.images:
                            workflow_input.images = []
                        workflow_input.images.append(
                            BamlImageInputParams(
                                name=input_item.name,
                                mime_type=input_item.image_mime_type,
                                base64_str=base64.b64encode(content).decode("utf-8"),
                            ),
                        )
                    else:
                        workflow_input.request[input_item.name] = content
            else:
                # If request is not a dict, we can't merge file contents into it
                workflow.logger.warning(
                    f"Cannot merge file contents into non-dict request type: {type(workflow_input.request)}",
                )

        # Determine the BAML content source
        baml_content_to_use = workflow_input.baml_content

        # If baml_content_dir is provided, read and compile all BAML files
        if workflow_input.baml_content_dir is not None:
            if workflow_input.baml_content is not None:
                raise exceptions.ApplicationError(
                    "Cannot specify both 'baml_content' and 'baml_content_dir'. "
                    "Please provide only one source for BAML definitions.",
                )

            # Use existing read_directory_activity to get all files
            directory_contents = await workflow.execute_local_activity(
                activity=sdk_constants.ACTIVITY_READ_DIRECTORY,
                args=[workflow_input.baml_content_dir],
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            # Filter for .baml files and combine them
            baml_files = [item for item in directory_contents if item["file"].endswith(".baml")]

            if not baml_files:
                raise exceptions.ApplicationError(
                    f"No BAML files found in directory: {workflow_input.baml_content_dir}",
                )

            # Sort for consistent ordering
            baml_files.sort(key=lambda x: x["file"])

            # Combine all BAML file contents with source markers
            combined_content = []
            for item in baml_files:
                # Add separator comment to identify source files
                combined_content.append(f"// ===== Source: {item['file']} =====\n")
                combined_content.append(item["content"])
                combined_content.append("\n\n")

            baml_content_to_use = "".join(combined_content)

        # Generate BAML client if baml_content is provided (either directly or from directory)
        if baml_content_to_use is not None:
            workflow_task_queue = await workflow.execute_local_activity(
                activity=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE,
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            baml_src_dir = await workflow.execute_local_activity(
                activity=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT,
                args=[workflow_input.baml_function_name, baml_content_to_use, workflow_task_queue],
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            # Set the generated BAML source directory in the workflow input
            workflow_input.baml_src_dir = baml_src_dir

        transform_response = await workflow.execute_activity(
            activity=sdk_constants.ACTIVITY_TRANSFORM,
            args=[workflow_input],
            start_to_close_timeout=timedelta(
                seconds=workflow_input.timeout_seconds or constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS,
            ),
        )

        if workflow_input.output_path:
            # Determine what data to write to the output file
            output_data = transform_response

            # Apply JSON path extraction if specified
            if workflow_input.output_json_path:
                extracted_data = _extract_json_path(transform_response, workflow_input.output_json_path)
                if extracted_data is not None:
                    output_data = extracted_data
                else:
                    workflow.logger.warning(
                        f"JSON path '{workflow_input.output_json_path}' found no matches in response",
                    )
                    # Don't write anything if JSON path extraction fails
                    output_data = None

            # Convert output data to string for file writing
            if output_data is not None:
                if isinstance(output_data, dict):
                    output_data_str = json.dumps(output_data, indent=4)
                elif not isinstance(output_data, str):
                    output_data_str = str(output_data)
                else:
                    output_data_str = output_data

                await workflow.execute_local_activity(
                    activity=sdk_constants.ACTIVITY_WRITE_FILE,
                    args=[workflow_input.output_path, output_data_str],
                    start_to_close_timeout=timedelta(
                        seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS,
                    ),
                )

        return transform_response
