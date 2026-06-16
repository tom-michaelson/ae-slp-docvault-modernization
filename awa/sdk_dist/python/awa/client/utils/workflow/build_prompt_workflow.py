from pathlib import Path
from typing import Any

from temporalio import workflow

from awa.client import constants
from awa.client.models.input_params import InputParams


async def build_prompt_workflow(
    template_input: InputParams,
    variables: dict[str, Any] | None = None,
    inputs: list[InputParams] | None = None,
    output_path: str | Path | None = None,
) -> str:
    """Build a prompt using a template and variables.

    Args:
        template_input: InputParams containing template configuration and content.
        variables: Optional dictionary of variables to use in template resolution.
            Defaults to None.
        inputs: Optional list of InputParams for the prompt building process.
            Defaults to None.
        output_path: Optional path where the built prompt should be saved.
            Can be a string or Path object. Defaults to None.

    Returns:
        str: The built prompt string.

    """
    return await workflow.execute_child_workflow(
        workflow=constants.WORKFLOW_BUILD_PROMPT,
        arg={
            "template_input": template_input,
            "variables": variables,
            "inputs": inputs,
            "output_path": str(output_path) if output_path else None,
        },
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
    )
