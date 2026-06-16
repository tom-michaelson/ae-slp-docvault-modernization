"""Activities for applying diffs to files."""

from temporalio import activity

from awa.core.models.apply_diff_result import ApplyDiffResult
from awa.core.utils.diff_utilities import DiffError, process_patch
from awa.core.utils.file_system_utils import FileSystemUtils
from awa.sdk import constants as sdk_constants


@activity.defn(name=sdk_constants.ACTIVITY_APPLY_DIFF)
async def apply_diff_activity(diff_text: str) -> ApplyDiffResult:
    """Apply a diff to files.

    This activity applies a diff in a custom format to files. The diff format is
    parsed by the diff_utilities module.

    Args:
        diff_text: A diff in a custom format that can be parsed by the diff_utilities module.

    Returns:
        True if the diff was applied successfully, False otherwise.

    """
    try:
        await process_patch(
            diff_text,
            open_file,
            write_file,
            remove_file,
        )
    except (DiffError, FileNotFoundError, OSError) as e:
        activity.logger.exception("Error applying diff")
        return ApplyDiffResult(success=False, message=str(e))
    else:
        return ApplyDiffResult(success=True)


async def open_file(path: str) -> str:
    """Open a file and return its content."""
    return await FileSystemUtils.read_async(path)


async def write_file(path: str, content: str) -> None:
    """Write content to a file."""
    await FileSystemUtils.write_async(path, content)


async def remove_file(path: str) -> None:
    """Remove a file."""
    await FileSystemUtils.remove_async(path)
