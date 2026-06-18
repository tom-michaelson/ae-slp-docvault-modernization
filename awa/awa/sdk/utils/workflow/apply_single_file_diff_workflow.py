from temporalio import workflow

from awa.sdk import constants


async def apply_single_file_diff_workflow(file_path: str, prompt: str) -> None:
    """Apply a diff to a single file based on a natural language prompt.

    Args:
        file_path: The path to the file to modify.
        prompt: The natural language request describing the changes to make.

    """
    await workflow.execute_child_workflow(
        workflow=constants.WORKFLOW_APPLY_SINGLE_FILE_DIFF,
        arg={
            "file_path": file_path,
            "natural_language_request": prompt,
        },
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
    )
