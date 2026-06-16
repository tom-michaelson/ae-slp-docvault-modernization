from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.client import constants


async def read_file_activity(file_path: str | Path, default: str | None = None) -> str:
    """Read the contents of a file as a string.

    Args:
        file_path: The path to the file to read. Can be a string or Path object.
        default: The default value to return if the file cannot be read. Defaults to None.

    Returns:
        str: The contents of the file as a string, or the default value if specified.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_READ_FILE,
        args=[str(file_path), default],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
