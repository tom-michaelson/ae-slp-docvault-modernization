from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.client import constants


async def delete_directory_activity(dir_path: str | Path) -> None:
    """Delete a directory and all its contents.

    Args:
        dir_path: The directory path to delete.

    """
    await workflow.execute_activity(
        constants.ACTIVITY_DELETE_DIRECTORY,
        args=[str(dir_path)],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS * 10),
    )
