"""Wrapper for fix Python SDK imports activity."""

from datetime import timedelta

from temporalio import workflow

from awa.sdk import constants as sdk_constants
from awa.workflows.generate_sdk import constants as generate_sdk_constants


async def fix_python_sdk_imports_activity(sdk_path: str) -> None:
    """Fix import statements in copied Python SDK files.

    This is a wrapper function that executes the actual activity
    through Temporal's workflow execution context.

    Args:
        sdk_path: Path to the Python SDK directory

    """
    await workflow.execute_activity(
        generate_sdk_constants.ACTIVITY_FIX_PYTHON_SDK_IMPORTS,
        args=[sdk_path],
        task_queue=sdk_constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=sdk_constants.FILE_IO_TIMEOUT_SECONDS),
    )
