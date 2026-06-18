"""Activity to fix Python SDK imports after copying files."""

import re
from pathlib import Path

from temporalio import activity

from awa.workflows.generate_sdk import constants


@activity.defn(name=constants.ACTIVITY_FIX_PYTHON_SDK_IMPORTS)
async def fix_python_sdk_imports_activity_impl(sdk_path: str) -> None:
    """Fix import statements in copied Python SDK files.

    Replaces all occurrences of 'from awa.sdk' with 'from awa.client'
    and 'import awa.sdk' with 'import awa.client' in all Python files
    within the SDK directory.

    Args:
        sdk_path: Path to the Python SDK directory

    """
    sdk_dir = Path(sdk_path)

    if not sdk_dir.exists():
        raise FileNotFoundError(f"SDK directory does not exist: {sdk_path}")

    # Pattern to match import statements
    patterns = [
        (r"from awa\.sdk", "from awa.client"),
        (r"import awa\.sdk", "import awa.client"),
    ]

    # Find all Python files in the SDK directory
    python_files = list(sdk_dir.rglob("*.py"))

    activity.logger.info(f"Fixing imports in {len(python_files)} Python files in {sdk_path}")

    # Process files synchronously since we're already in an activity
    _process_files_sync(python_files, patterns)

    activity.logger.info("Completed fixing Python SDK imports")


def _process_files_sync(python_files: list[Path], patterns: list[tuple[str, str]]) -> None:
    """Process files synchronously in executor.

    Args:
        python_files: List of Python file paths to process
        patterns: List of (pattern, replacement) tuples

    """
    for file_path in python_files:
        try:
            # Read the file content
            content = file_path.read_text(encoding="utf-8")

            # Track if any changes were made
            original_content = content

            # Apply all replacements
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            # Write back only if changes were made
            if content != original_content:
                file_path.write_text(content, encoding="utf-8")
                activity.logger.debug(f"Fixed imports in {file_path}")

        except (OSError, UnicodeDecodeError) as e:
            activity.logger.warning(f"Failed to process {file_path}: {e}")
