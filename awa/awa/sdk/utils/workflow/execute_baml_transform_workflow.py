from pathlib import Path
from typing import Any

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.transform_params import TransformParams
from awa.sdk.utils.activity.read_file_activity import read_file_activity


async def execute_baml_transform_workflow(
    transform_params: TransformParams,
    baml_path: str | Path | None = None,
    additional_workflow_id_part: str | None = None,
) -> Any:  # noqa: ANN401
    """Execute a BAML transformation using a specified function.

    Args:
        transform_params: Parameters for the BAML transformation.
        baml_path: Optional path to the BAML file (will be read and added as content to the tranform params).
        additional_workflow_id_part: Optional additional part to include in the workflow ID.
            Defaults to None.

    Returns:
        Any: The result of the BAML transformation.

    """
    if baml_path:
        baml_content = await read_file_activity(str(baml_path))
        transform_params.baml_content = baml_content
    additional_workflow_id_part = f"-{additional_workflow_id_part}" if additional_workflow_id_part else ""
    transform_result = await workflow.execute_child_workflow(
        workflow=constants.WORKFLOW_TRANSFORM,
        arg=transform_params,
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        id=f"Transform-{workflow.uuid4()}",
        static_summary=f"Transform-{transform_params.baml_function_name}{additional_workflow_id_part}",
        static_details=transform_params.model_dump_json(indent=2),
    )
    return transform_result
