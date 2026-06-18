from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.sdk import constants


async def is_directory_activity(dir_path: str | Path) -> bool:
    """Check if a path is a directory.

    Args:
        dir_path: The directory path to check.

    Returns:
        True if the path is a directory, False otherwise.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_IS_DIRECTORY,
        arg=str(dir_path),
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
