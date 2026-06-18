from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.client import constants


async def list_all_directories_recursive_activity(source_dir: str | Path) -> list[str]:
    """Recursively list all directories under the source directory.

    This function uses the FileSystemUtils to recursively find all directories
    under the given source directory path. It returns a sorted list of full
    directory paths.

    Args:
        source_dir: The root directory to search from. Can be a string or Path object.

    Returns:
        list[str]: A list of directory paths as strings.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_LIST_ALL_DIRECTORIES_RECURSIVE,
        arg=str(source_dir),
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS * 10),
    )
