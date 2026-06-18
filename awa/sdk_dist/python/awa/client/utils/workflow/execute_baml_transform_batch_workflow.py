from pathlib import Path
from typing import Any

from temporalio import workflow

from awa.client import constants
from awa.client.models.transform_params import TransformParams
from awa.client.utils.activity.read_file_activity import read_file_activity


async def execute_baml_transform_batch_workflow(
    baml_requests_by_key: dict[str, TransformParams],
    baml_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute multiple BAML transformations in batch using a specified function.

    Args:
        baml_requests_by_key: Dictionary mapping keys to BAML transform params.
            Each key will have its corresponding request processed.
        baml_path: Optional path to the BAML file (will be read and added as content to the tranform params).

    Returns:
        dict[str, Any]: Dictionary mapping the same keys to their transformation results.

    """
    if not baml_requests_by_key or len(baml_requests_by_key) == 0:
        return {}

    if baml_path:
        baml_content = await read_file_activity(str(baml_path))
        for transform_params in baml_requests_by_key.values():
            transform_params.baml_content = baml_content

    baml_function_name = next(iter(baml_requests_by_key.values())).baml_function_name
    return await workflow.execute_child_workflow(
        workflow=constants.WORKFLOW_TRANSFORM_BATCH,
        arg={"params_by_key": baml_requests_by_key, "timeout_seconds": constants.BAML_TIMEOUT_SECONDS},
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        id=f"TransformBatch-{workflow.uuid4()}",
        static_summary=f"TransformBatch-{baml_function_name} ({len(baml_requests_by_key)})",
        static_details="\n".join(baml_requests_by_key.keys()),
    )
