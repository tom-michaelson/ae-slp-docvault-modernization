from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.sdk import constants


async def list_directory_activity(dir_path: str | Path, ignore_file_path: str | Path | None = None) -> list[str]:
    """List the contents of a directory.

    Args:
        dir_path: The path to the directory to list. Can be a string or Path object.
        ignore_file_path: Optional path to an ignore file (like .gitignore) to exclude files.
            Can be a string or Path object. Defaults to None.

    Returns:
        list[str]: A list of file and directory names in the specified directory.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_LIST_DIRECTORY,
        args=[str(dir_path), str(ignore_file_path) if ignore_file_path else None],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
