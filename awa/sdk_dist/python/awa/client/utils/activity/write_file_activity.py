from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.client import constants


async def write_file_activity(file_path: str | Path, content: str) -> None:
    """Write content to a file.

    Args:
        file_path: The path where the file should be written. Can be a string or Path object.
        content: The string content to write to the file.

    """
    await workflow.execute_activity(
        constants.ACTIVITY_WRITE_FILE,
        args=[str(file_path), content],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
