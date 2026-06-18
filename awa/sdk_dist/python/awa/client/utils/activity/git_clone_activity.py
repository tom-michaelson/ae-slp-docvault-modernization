from datetime import timedelta
from pathlib import Path

from temporalio import workflow

from awa.client import constants


async def git_clone_activity(
    git_url: str,
    destination_path: str | Path | None = None,
    branch: str | None = None,
) -> str:
    """Clone a Git repository to a destination path.

    Args:
        git_url: The Git repository URL to clone
        destination_path: Optional destination path. If not provided, uses a temp directory
        branch: Optional branch to checkout

    Returns:
        The path to the cloned repository

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_GIT_CLONE,
        args=[git_url, str(destination_path) if destination_path else None, branch],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.GIT_TIMEOUT_SECONDS),
    )
