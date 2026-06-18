from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.sdk import constants


async def copy_file_activity(source_path: str | Path, destination_path: str | Path) -> None:
    """Copy a file from source to destination.

    Args:
        source_path: The source file path.
        destination_path: The destination file path.

    """
    await workflow.execute_activity(
        constants.ACTIVITY_COPY_FILE,
        args=[str(source_path), str(destination_path)],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
