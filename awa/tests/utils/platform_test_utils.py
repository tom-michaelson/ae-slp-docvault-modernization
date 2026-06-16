"""Cross-platform test utilities for consistent testing across Windows and Unix systems."""

import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

from awa.core.utils.platform_utils import PlatformUtils


def normalize_path_for_comparison(path: str | Path) -> str:
    """Normalize path for cross-platform test comparison.

    Converts all paths to use forward slashes for consistent
    comparison across Windows and Unix systems.

    Args:
        path: Path to normalize (string or Path object)

    Returns:
        Normalized path string with forward slashes

    """
    return str(Path(path).as_posix())


@contextmanager
def mock_platform_detection(is_windows: bool = False) -> Generator[None, None, None]:
    """Context manager for mocking platform detection in tests.

    Args:
        is_windows: Whether to mock as Windows platform

    Yields:
        None - Context manager for use in test cases

    """
    platform_name = "win32" if is_windows else "linux"
    with (
        patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=is_windows),
        patch("sys.platform", platform_name),
    ):
        yield


@contextmanager
def mock_home_directory(temp_dir: str | None = None) -> Generator[str, None, None]:
    """Context manager for mocking home directory in tests.

    Ensures tests have a reliable home directory that works
    across different environments and platforms.

    Args:
        temp_dir: Optional temporary directory to use as home.
                 If None, creates a new temporary directory.

    Yields:
        str - Path to the temporary home directory

    """
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp()

    home_path = Path(temp_dir)

    with patch("pathlib.Path.home", return_value=home_path):
        yield str(home_path)


def get_platform_specific_subprocess_kwargs(
    base_kwargs: dict[str, Any],
    is_shell_mode: bool = False,
    is_detach_mode: bool = False,
) -> dict[str, Any]:
    """Get platform-specific subprocess keyword arguments for test assertions.

    Based on CommandUtils implementation:
    - Windows non-detach: adds creationflags=512 (CREATE_NEW_PROCESS_GROUP) for both shell and exec
    - Windows detach: adds creationflags=512 (CREATE_NEW_PROCESS_GROUP) for both shell and exec
    - Unix non-detach exec: adds start_new_session=True
    - Unix non-detach shell: no extra flags
    - Unix detach: adds start_new_session=True for both shell and exec

    Args:
        base_kwargs: Base keyword arguments for subprocess calls
        is_shell_mode: Whether this is for shell mode (vs exec mode)
        is_detach_mode: Whether this is for detach mode (vs non-detach)

    Returns:
        Platform-specific keyword arguments

    """
    kwargs = base_kwargs.copy()

    if PlatformUtils.is_windows():
        # Windows always uses creationflags for process group management
        kwargs["creationflags"] = 512  # subprocess.CREATE_NEW_PROCESS_GROUP
    # Unix behavior
    elif is_detach_mode:
        # Detach mode: always use start_new_session=True
        kwargs["start_new_session"] = True
    elif not is_shell_mode:
        # Non-detach exec mode: use start_new_session=True
        kwargs["start_new_session"] = True
        # Non-detach shell mode: no extra flags needed

    return kwargs


def normalize_line_endings(text: str, target_ending: str = "\n") -> str:
    """Normalize line endings in text for cross-platform testing.

    Converts Windows CRLF and legacy Mac CR to Unix LF
    or specified target ending.

    Args:
        text: Text with potentially mixed line endings
        target_ending: Target line ending (default: Unix)

    Returns:
        Text with normalized line endings

    """
    # First normalize all to \n, then convert to target
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")

    if target_ending != "\n":
        normalized = normalized.replace("\n", target_ending)

    return normalized


def create_temp_file_with_content(content: str, suffix: str = ".txt") -> str:
    """Create a temporary file with specified content and consistent line endings.

    Ensures file is created with appropriate line endings for the platform
    to avoid test failures due to line ending differences.

    Args:
        content: Content to write to the file
        suffix: File suffix/extension

    Returns:
        Path to the created temporary file

    """
    # Normalize content to platform-specific line endings
    platform_content = content
    if PlatformUtils.is_windows():
        platform_content = normalize_line_endings(content, "\r\n")

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, newline="") as temp_file:
        temp_file.write(platform_content)
        return temp_file.name
