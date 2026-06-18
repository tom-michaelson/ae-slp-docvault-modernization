from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.sdk import constants


async def copy_directory_activity(
    source_path: str | Path,
    destination_path: str | Path,
    ignore_file_path: str | Path | None = None,
) -> list[str]:
    """Copy a directory and its contents to a destination.

    Args:
        source_path: The path to the source directory to copy. Can be a string or Path object.
        destination_path: The path where the directory should be copied. Can be a string or Path object.
        ignore_file_path: Optional path to an ignore file (like .gitignore) to exclude files.
            Can be a string or Path object. Defaults to None.

    Returns:
        list[str]: A list of the files that were copied.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_COPY_DIRECTORY,
        args=[str(source_path), str(destination_path), str(ignore_file_path) if ignore_file_path else None],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS * 20),
    )
