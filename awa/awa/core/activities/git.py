"""Git-related Temporal activities for AWA core."""

import shutil
import subprocess
import tempfile
from pathlib import Path

from temporalio import activity

from awa.sdk import constants as sdk_constants


class GitOperationError(Exception):
    """Exception raised when Git operations fail."""


@activity.defn(name=sdk_constants.ACTIVITY_GIT_CLONE)
async def git_clone_repository_activity(
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

    Raises:
        Exception: If git clone fails or repository is inaccessible

    """
    activity.logger.info(f"Cloning repository from {git_url}")

    # If no destination provided, create a temporary directory
    if destination_path is None:
        temp_dir = tempfile.mkdtemp(prefix="awa_git_clone_")
        destination_path = temp_dir
        activity.logger.info(f"Created temporary directory: {destination_path}")

    destination_path = Path(destination_path)

    # Ensure the destination directory exists and is empty
    if destination_path.exists():
        if any(destination_path.iterdir()):
            # If directory exists and is not empty, create a subdirectory
            repo_name = git_url.rstrip("/").split("/")[-1].replace(".git", "")
            destination_path = destination_path / repo_name
            destination_path.mkdir(parents=True, exist_ok=True)
    else:
        destination_path.mkdir(parents=True, exist_ok=True)

    try:
        # Build git clone command
        clone_cmd = ["git", "clone"]

        # Add branch option if specified
        if branch:
            clone_cmd.extend(["-b", branch])

        # Add the URL and destination
        clone_cmd.extend([git_url, str(destination_path)])

        # Execute git clone
        activity.logger.info(f"Executing: {' '.join(clone_cmd)}")
        result = subprocess.run(  # noqa: ASYNC221, S603
            clone_cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        if result.stderr:
            activity.logger.info(f"Git clone stderr: {result.stderr}")

        activity.logger.info(f"Successfully cloned repository to {destination_path}")

        # Return the path to the cloned repository
        return str(destination_path)

    except subprocess.CalledProcessError as e:
        activity.logger.error(f"Git clone failed: {e.stderr}")
        # Clean up if we created a temp directory
        if "temp_dir" in locals() and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
        raise GitOperationError(f"Failed to clone repository: {e.stderr}") from e
    except Exception as e:
        activity.logger.error(f"Unexpected error during git clone: {e!s}")
        # Clean up if we created a temp directory
        if "temp_dir" in locals() and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)
        raise
