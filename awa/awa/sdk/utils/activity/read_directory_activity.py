from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.sdk import constants
from awa.sdk.models.read_directory_result import ReadDirectoryResult


async def read_directory_activity(
    source_path: str | Path,
    ignore_file_path: str | Path | None = None,
) -> list[ReadDirectoryResult]:
    """Read a directory and return detailed information about its contents.

    Args:
        source_path: The path to the directory to read. Can be a string or Path object.
        ignore_file_path: Optional path to an ignore file (like .gitignore) to exclude files.
            Can be a string or Path object. Defaults to None.

    Returns:
        list[ReadDirectoryResult]: A list of ReadDirectoryResult objects containing
            detailed information about each file and directory.

    """
    raw_results = await workflow.execute_activity(
        constants.ACTIVITY_READ_DIRECTORY,
        args=[str(source_path), str(ignore_file_path) if ignore_file_path else None],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS * 10),
    )
    return [ReadDirectoryResult(**result) for result in raw_results]
