from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.client import constants
from awa.client.models.folder_info import FolderInfo


async def get_directory_info_activity(directory_path: str | Path) -> FolderInfo:
    """Get information about a single directory including its immediate files and subdirectories.

    This function examines a single directory and returns information about its
    immediate contents without recursing into subdirectories. It provides lists
    of file names and subdirectory names found directly in the specified directory.

    Args:
        directory_path: The path to the directory to analyze. Can be a string or Path object.

    Returns:
        FolderInfo: A FolderInfo object containing:
            - path: The directory path
            - files: List of file names (not full paths)
            - subdirectories: List of subdirectory names (not full paths)

    """
    raw_result = await workflow.execute_activity(
        constants.ACTIVITY_GET_DIRECTORY_INFO,
        arg=str(directory_path),
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
    return FolderInfo(**raw_result)
