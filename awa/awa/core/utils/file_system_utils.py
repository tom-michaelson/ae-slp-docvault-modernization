import asyncio
import fnmatch
import subprocess
import tempfile
import uuid
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import IO, cast

import fsspec
from fsspec.implementations.local import AbstractFileSystem

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.sdk.models.folder_info import FolderInfo

logger = get_logger(LoggerComponent.ACTIVITY)

try:
    from gitignore_parser import parse_gitignore_str
except ImportError:
    parse_gitignore_str = None

# Constants for Windows path detection
WINDOWS_DRIVE_PATH_MIN_LENGTH = 2
WINDOWS_DRIVE_COLON_POSITION = 1

# Common binary file extensions that should not be decoded as UTF-8
BINARY_FILE_EXTENSIONS = {
    ".ico",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".svg",
    ".webp",  # Images
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",  # Archives/Documents
    ".exe",
    ".dll",
    ".so",
    ".dylib",  # Executables
    ".bin",
    ".dat",
    ".db",
    ".sqlite",  # Binary data
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",  # Fonts
    ".mp3",
    ".mp4",
    ".avi",
    ".mov",
    ".wav",  # Media
}


def create_ignore_matcher(ignore_content: str) -> Callable[[str], bool]:
    """Create a function that checks if a file path should be ignored.

    This function parses .gitignore style patterns and returns a callable
    that can be used to check if a given file path should be ignored.

    Args:
        ignore_content: String content of the ignore file with patterns

    Returns:
        A function that takes a file path and returns True if it should be ignored

    """
    # Parse all patterns in order, preserving negation info
    patterns = []

    for line_content in ignore_content.splitlines():
        stripped_line = line_content.strip()
        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith("#"):
            continue

        if stripped_line.startswith("!"):
            # Negation pattern - remove the ! prefix
            patterns.append((stripped_line[1:], True))  # (pattern, is_negation)
        else:
            # Positive pattern
            patterns.append((stripped_line, False))  # (pattern, is_negation)

    def should_ignore(file_path: str) -> bool:
        """Check if file_path should be ignored based on patterns.

        Args:
            file_path: The path to check against ignore patterns

        Returns:
            True if the file should be ignored, False otherwise

        """
        # Convert to forward slashes for consistency
        norm_path = Path(file_path).as_posix()
        filename = Path(file_path).name

        # Start with not ignored
        ignored = False

        # Process patterns in order (later patterns override earlier ones)
        for pattern, is_negation in patterns:
            if _matches_pattern(pattern, norm_path, filename):
                ignored = not is_negation  # If negation, then don't ignore; otherwise ignore

        return ignored

    def _matches_pattern(pattern: str, norm_path: str, filename: str) -> bool:
        """Check if a single pattern matches the given path."""
        # Direct match with filename
        if pattern == filename:
            return True

        # Handle directory patterns: if path starts with the pattern, it should be ignored
        # This handles cases like .venv matching .venv/bin/python
        if norm_path.startswith(f"{pattern}/") or norm_path == pattern:
            return True

        # Handle */pattern (matches files in any directory)
        if pattern.startswith("*/"):
            suffix = pattern[2:]
            if fnmatch.fnmatch(norm_path, f"*/{suffix}") or fnmatch.fnmatch(filename, suffix):
                return True

        # Handle **/ patterns (match any depth)
        if "**/" in pattern and pattern.startswith("**/"):
            # For **/*.cs, we want to match any .cs file at any depth
            suffix = pattern[3:]  # Remove **/
            # Match if any part of the path matches the suffix pattern
            if fnmatch.fnmatch(filename, suffix):
                return True
            # Also check the full path
            if fnmatch.fnmatch(norm_path, f"*/{suffix}"):
                return True

        # Handle directory patterns (ending with /)
        if pattern.endswith("/"):
            # For directory patterns, check if the path contains this directory
            dir_pattern = pattern[:-1]  # Remove trailing /
            path_parts = norm_path.split("/")
            if dir_pattern in path_parts:
                return True

                # General pattern matching
        return fnmatch.fnmatch(norm_path, pattern) or fnmatch.fnmatch(filename, pattern)

    return should_ignore


def _is_windows_drive_path(path_str: str) -> bool:
    r"""Check if a path string represents a Windows drive path.

    Windows drive paths have the format X:\ or X:/ where X is a letter.
    This function checks for this pattern to distinguish Windows paths
    from remote filesystem protocols.

    Args:
        path_str: The path string to check

    Returns:
        True if this is a Windows drive path, False otherwise

    """
    return (
        len(path_str) >= WINDOWS_DRIVE_PATH_MIN_LENGTH
        and path_str[WINDOWS_DRIVE_COLON_POSITION] == ":"
        and path_str[0].isalpha()
    )


def _get_filesystem_protocol(path_str: str) -> str:
    r"""Extract the filesystem protocol from a path string.

    This function correctly handles Windows drive paths (C:\, D:/, etc.)
    and remote filesystem protocols (s3://, gs://, etc.).

    Args:
        path_str: The path string to extract protocol from

    Returns:
        The filesystem protocol (e.g., 'file', 's3', 'gs')

    """
    # Check if this is a Windows drive path
    if _is_windows_drive_path(path_str):
        return "file"

    # For other paths, check for protocol separator
    if ":" in path_str:
        return path_str.split(":", 1)[0]

    # Default to local file protocol
    return "file"


class FileSystemUtils:
    @staticmethod
    def _calculate_relative_path(
        src_full_path: str,
        source_path: str,
        source_protocol: str,
    ) -> str:
        """Calculate relative path from source to found file.

        Args:
            src_full_path: The full path of the file found by fsspec
            source_path: The source directory path
            source_protocol: The filesystem protocol of the source

        Returns:
            The relative path from source to the file

        """
        source_path_str = str(source_path).replace("\\", "/")
        src_full_path_str = src_full_path.replace("\\", "/")

        if source_protocol != "file":
            # For remote paths, fsspec.find() returns paths without protocol prefix
            # Normalize both paths by stripping protocol for comparison
            source_normalized = source_path_str.split("://", 1)[1] if "://" in source_path_str else source_path_str
            if not source_normalized.startswith("/"):
                source_normalized = "/" + source_normalized

            src_normalized = src_full_path_str if src_full_path_str.startswith("/") else "/" + src_full_path_str

            if src_normalized.startswith(source_normalized):
                return src_normalized[len(source_normalized) :].lstrip("/")
            # Fallback: extract just the filename
            return src_full_path_str.split("/")[-1] if "/" in src_full_path_str else src_full_path_str

        if src_full_path_str.startswith(source_path_str):
            return src_full_path_str[len(source_path_str) :].lstrip("/")
        # For local paths, use Path.relative_to
        return Path(src_full_path).relative_to(str(source_path)).as_posix()

    @staticmethod
    def _build_destination_path(
        destination_path: str,
        relative_path: str,
        dest_protocol: str,
    ) -> str:
        """Build full destination path from base and relative path.

        Args:
            destination_path: The base destination directory path
            relative_path: The relative path to append
            dest_protocol: The filesystem protocol of the destination

        Returns:
            The full destination path

        """
        if dest_protocol != "file":
            # For remote paths, use string concatenation
            return f"{str(destination_path).rstrip('/')}/{relative_path}"
        # For local paths, use Path for proper path handling
        return str(Path(destination_path) / relative_path).replace("\\", "/")

    @staticmethod
    def _ensure_destination_parent(
        dest_full_path: str,
        dest_fs: AbstractFileSystem,
        dest_protocol: str,
    ) -> None:
        """Ensure the parent directory of destination file exists.

        Args:
            dest_full_path: The full destination file path
            dest_fs: The destination filesystem
            dest_protocol: The filesystem protocol of the destination

        """
        if dest_protocol != "file" and "/" in dest_full_path:
            # For remote paths, use string manipulation
            dest_parent = dest_full_path.rsplit("/", 1)[0]
            # Only create parent if it's not just the protocol/bucket
            if dest_parent.count("/") > 1 and not dest_fs.exists(dest_parent):
                dest_fs.makedirs(dest_parent, exist_ok=True)
        else:
            # For local paths, use Path
            dest_parent = str(Path(dest_full_path).parent).replace("\\", "/")
            if dest_parent and dest_parent != "." and not dest_fs.exists(dest_parent):
                dest_fs.makedirs(dest_parent, exist_ok=True)

    @staticmethod
    def is_directory(path: str) -> bool:
        path_str = str(path)
        fs = FileSystemUtils.get_filesystem(path_str)
        return fs.isdir(path_str)

    @staticmethod
    def read(fs: AbstractFileSystem, path: str) -> str:
        path_str = str(path)
        content = fs.read_text(path_str)
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return str(content)

    @staticmethod
    def write(fs: AbstractFileSystem, path: str, content: str) -> None:
        path_str = str(path)
        fs.write_text(path_str, content)

    @staticmethod
    async def read_async(path: str, default: str | None = None) -> str:
        file_bytes = await FileSystemUtils.read_bytes_async(path, default)
        if isinstance(file_bytes, bytes):
            # Check if this is a known binary file extension
            file_ext = Path(path).suffix.lower()
            if file_ext in BINARY_FILE_EXTENSIONS:
                return f"[Binary file: {Path(path).name}]"

            # Try UTF-8 decoding with fallback for unexpected binary content
            try:
                return file_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return f"[Binary or non-UTF-8 file: {Path(path).name}]"
        return str(file_bytes)

    @staticmethod
    async def read_bytes_async(path: str, default: bytes | None = None) -> bytes:
        loop = asyncio.get_running_loop()

        def _read() -> str:
            fs = FileSystemUtils.get_filesystem(path)
            if not fs.exists(path):
                if default is None:
                    raise FileNotFoundError(f"File not found: {path}")
                return default

            with fs.open(path, "rb") as f:
                content: bytes = f.read()
                return content

        return await loop.run_in_executor(None, _read)

    @staticmethod
    async def write_async(path: str, content: str) -> None:
        loop = asyncio.get_running_loop()

        def _write() -> None:
            fs = FileSystemUtils.get_filesystem(path)

            # For remote filesystems, use fsspec's path handling
            protocol = _get_filesystem_protocol(path)
            if protocol != "file":
                # For remote paths, extract parent using string manipulation
                if "/" in path:
                    parent_path = path.rsplit("/", 1)[0]
                    # Only create parent if it's not just the protocol/bucket
                    if parent_path.count("/") > 1 or (protocol == "file" and parent_path):
                        fs.makedirs(parent_path, exist_ok=True)
            else:
                # For local filesystem, use Path
                dir_path = Path(path).parent
                if dir_path and str(dir_path) != ".":
                    fs.makedirs(str(dir_path), exist_ok=True)

            fs.write_text(path, content, encoding="utf-8")

        await loop.run_in_executor(None, _write)

    @staticmethod
    async def remove_async(path: str) -> None:
        loop = asyncio.get_running_loop()

        def _remove() -> None:
            try:
                fs = FileSystemUtils.get_filesystem(path)
                fs.rm(path)
            except FileNotFoundError:
                pass

        await loop.run_in_executor(None, _remove)

    @staticmethod
    async def remove_directory_async(path: str) -> None:
        """Recursively remove a directory and all its contents.

        Args:
            path: The path to the directory to remove.

        """
        loop = asyncio.get_running_loop()

        def _remove_directory() -> None:
            fs = FileSystemUtils.get_filesystem(path)
            # Only attempt removal if the path exists
            if fs.exists(path):
                # Use recursive=True to remove directory and all contents
                fs.rm(path, recursive=True)

        await loop.run_in_executor(None, _remove_directory)

    @staticmethod
    async def copy_file_async(source_path: str | Path, destination_path: str | Path) -> None:
        """Copy a file from source to destination.

        This function uses `fsspec` to copy a file. It determines the
        filesystem (e.g., local, S3, GCS) from the protocol prefix of the
        source path. The copy operation is performed within this single
        filesystem. Cross-filesystem copies are not supported by this method.

        Args:
            source_path: The path or URI of the source file. Must include a
                         protocol prefix (e.g., 's3://') for remote filesystems.
            destination_path: The path or URI for the destination, which must be
                              on the same filesystem as the source.

        """
        loop = asyncio.get_running_loop()

        source_str = str(source_path)
        dest_str = str(destination_path)

        def _copy_file() -> None:
            source_fs = FileSystemUtils.get_filesystem(source_str)
            dest_fs = FileSystemUtils.get_filesystem(dest_str)

            # Check if source file exists
            if not source_fs.exists(source_str):
                raise FileNotFoundError(f"Source file not found: {source_str}")

            # Check if source is actually a file
            if source_fs.isdir(source_str):
                raise IsADirectoryError(f"Source is a directory, not a file: {source_str}")

            # Ensure destination directory exists
            dest_parent = Path(dest_str).parent
            if dest_parent and not dest_fs.exists(str(dest_parent)):
                dest_fs.makedirs(str(dest_parent), exist_ok=True)

            # Copy the file
            source_fs.copy(source_str, dest_str)

        await loop.run_in_executor(None, _copy_file)

    @staticmethod
    async def copy_directory_async(
        source_path: str,
        destination_path: str,
        ignore_file_path: str | None = None,
    ) -> list[str]:
        """Recursively copies a directory from a source to a destination.

        This function uses `fsspec` to copy a directory. It determines the
        filesystem (e.g., local, S3, GCS) from the protocol prefix of the
        source path. The copy operation is performed within this single
        filesystem. Cross-filesystem copies are not supported by this method.

        If an ignore file is provided, it will be parsed using .gitignore patterns.
        Files matching these patterns will not be copied.

        Args:
            source_path: The path or URI of the source directory. Must include a
                         protocol prefix (e.g., 's3://') for remote filesystems.
            destination_path: The path or URI for the destination, which must be
                              on the same filesystem as the source.
            ignore_file_path: Optional path to a file containing .gitignore-style
                              patterns for files to ignore during the copy.

        Returns:
            A list of full paths to files that were copied to the destination.

        """
        loop = asyncio.get_running_loop()

        def _copy_directory() -> None:
            if ignore_file_path and parse_gitignore_str is None:
                warnings.warn(
                    "gitignore-parser is not installed, but ignore_file_path was provided. "
                    "The ignore file will not be used.",
                    stacklevel=2,
                )
                # For tests where parse_gitignore_str is None, don't use custom matcher

            source_fs = FileSystemUtils.get_filesystem(str(source_path))
            dest_fs = FileSystemUtils.get_filesystem(str(destination_path))

            matcher = None
            # Only use custom matcher if parse_gitignore_str is not None (for tests)
            if ignore_file_path and parse_gitignore_str is not None:
                ignore_fs = FileSystemUtils.get_filesystem(str(ignore_file_path))
                with ignore_fs.open(str(ignore_file_path), "r", encoding="utf-8") as f:
                    ignore_content = f.read()
                    if isinstance(ignore_content, bytes):
                        ignore_content = ignore_content.decode("utf-8")
                # Create a custom matcher function
                matcher = create_ignore_matcher(ignore_content)

            source_protocol = _get_filesystem_protocol(str(source_path))
            dest_protocol = _get_filesystem_protocol(str(destination_path))

            for src_full_path in source_fs.find(str(source_path)):
                # Calculate relative path from source to found file
                relative_path = FileSystemUtils._calculate_relative_path(
                    src_full_path,
                    str(source_path),
                    source_protocol,
                )

                if matcher and matcher(relative_path):
                    continue

                # Build full destination path
                dest_full_path = FileSystemUtils._build_destination_path(
                    str(destination_path),
                    relative_path,
                    dest_protocol,
                )

                # Ensure destination parent directory exists
                FileSystemUtils._ensure_destination_parent(dest_full_path, dest_fs, dest_protocol)

                # Use open() instead of copy() to avoid glob expansion issues
                # with special characters like brackets in paths
                with source_fs.open(src_full_path, "rb") as src_file, dest_fs.open(dest_full_path, "wb") as dest_file:
                    # Copy in chunks for memory efficiency
                    while True:
                        chunk = src_file.read(8 * 1024 * 1024)  # 8MB chunks
                        if not chunk:
                            break
                        dest_file.write(chunk)

        await loop.run_in_executor(None, _copy_directory)
        return await FileSystemUtils.list_directory_async(destination_path, ignore_file_path=ignore_file_path)

    @staticmethod
    async def list_directory_async(
        source_path: str,
        ignore_file_path: str | None = None,
    ) -> list[str]:
        """List all files in a directory, optionally ignoring based on .gitignore.

        This function recursively finds all files in the given source path.
        If an ignore file is provided, it filters the file list based on
        .gitignore-style patterns. It returns a flat list of full file paths.

        The returned paths are suitable for use with other file activities like
        `read_file` or `write_file`.

        Args:
            source_path: The path or URI of the source directory.
            ignore_file_path: Optional path to a file with .gitignore patterns.

        Returns:
            A list of full paths to files in the directory.

        """
        loop = asyncio.get_running_loop()

        source_path_str = str(source_path)
        ignore_file_path_str = str(ignore_file_path) if ignore_file_path else None

        def _list_directory() -> list[str]:
            if ignore_file_path_str and parse_gitignore_str is None:
                warnings.warn(
                    "gitignore-parser is not installed, but ignore_file_path was provided. "
                    "The ignore file will not be used.",
                    stacklevel=2,
                )

            source_protocol = _get_filesystem_protocol(source_path_str)
            source_fs = fsspec.filesystem(source_protocol)

            matcher = None
            # Only use custom matcher if parse_gitignore_str is not None (for tests)
            if ignore_file_path_str and parse_gitignore_str is not None:
                ignore_protocol = _get_filesystem_protocol(ignore_file_path_str)
                ignore_fs = fsspec.filesystem(ignore_protocol)
                with ignore_fs.open(ignore_file_path_str, "r", encoding="utf-8") as f:
                    ignore_content = cast("IO[str]", f).read()
                # Create a custom matcher function
                matcher = create_ignore_matcher(ignore_content)

            file_paths = []

            # Handle path resolution based on filesystem type
            if source_protocol == "file":
                # For local filesystem, use Path.resolve()
                abs_source_path = Path(source_path_str).resolve()
            else:
                # For remote filesystems, use the path as-is
                abs_source_path = source_path_str.rstrip("/")

            for path in source_fs.find(source_path_str):
                if source_fs.isdir(path):
                    continue

                # Calculate relative path based on filesystem type
                if source_protocol == "file":
                    # For local filesystem, use Path operations
                    relative_path = Path(path).resolve().relative_to(abs_source_path).as_posix()
                # For remote filesystems, use string manipulation
                elif path.startswith(abs_source_path):
                    relative_path = path[len(abs_source_path) :].lstrip("/")
                else:
                    # Fallback: extract filename
                    relative_path = path.split("/")[-1] if "/" in path else path

                if matcher and matcher(relative_path):
                    continue

                # Handle path normalization based on filesystem type
                if hasattr(source_fs, "protocol") and source_fs.protocol == "memory":
                    # For memory filesystem, preserve forward slashes
                    file_paths.append(path)
                elif source_protocol == "file":
                    # For local file systems, normalize to OS-specific separators
                    normalized_path = str(Path(path))
                    file_paths.append(normalized_path)
                else:
                    # For remote filesystems, keep paths as-is
                    file_paths.append(path)

            return file_paths

        return await loop.run_in_executor(None, _list_directory)

    @staticmethod
    async def read_directory_async(
        source_path: str,
        ignore_file_path: str | None = None,
    ) -> list[dict[str, str]]:
        """Read all files in a directory recursively, optionally ignoring based on .gitignore.

        This function recursively finds and reads all files in the given source path.
        If an ignore file is provided, it filters the file list based on
        .gitignore-style patterns. It returns a list of dictionaries containing
        file paths and their content.

        File reads are performed in parallel for optimal performance.

        Args:
            source_path: The path or URI of the source directory.
            ignore_file_path: Optional path to a file with .gitignore patterns.

        Returns:
            A list of dictionaries with 'file' and 'content' keys for each file.

        """
        # First get the list of files to read
        file_paths = await FileSystemUtils.list_directory_async(source_path, ignore_file_path)

        # Create async tasks to read all files in parallel
        async def read_single_file(file_path: str) -> dict[str, str]:
            try:
                content = await FileSystemUtils.read_async(file_path)
                return {"file": file_path, "content": content}
            except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError):
                return {"file": file_path, "content": "Error reading file"}

        # Execute all reads in parallel
        if not file_paths:
            return []

        results = await asyncio.gather(*[read_single_file(path) for path in file_paths])
        return results

    @staticmethod
    def get_filesystem(path: str) -> AbstractFileSystem:
        path_str = str(path)
        protocol = _get_filesystem_protocol(path_str)
        try:
            return fsspec.filesystem(protocol)
        except ValueError as e:
            logger.exception(f"Failed to get filesystem for path '{path_str}' with protocol '{protocol}'")
            logger.exception(f"Available protocols: {sorted(fsspec.available_protocols())}")
            protocols = sorted(fsspec.available_protocols())
            raise ValueError(
                f"Unsupported filesystem protocol '{protocol}' for path '{path_str}'. Available protocols: {protocols}",
            ) from e

    @staticmethod
    def check_read_permission(path: str) -> bool:
        """Check if the directory has read permissions.

        Args:
            path: The directory path to check

        Returns:
            True if the directory can be read, False otherwise

        """
        try:
            fs = FileSystemUtils.get_filesystem(path)

            # Check if path exists and is a directory
            if not fs.exists(path):
                return False

            if not fs.isdir(path):
                return False

            # Try to list directory contents to test read permission
            fs.listdir(path)
            return True
        except (OSError, PermissionError):
            return False

    @staticmethod
    async def check_read_permission_async(path: str) -> bool:
        """Check if the directory has read permissions asynchronously.

        Args:
            path: The directory path to check

        Returns:
            True if the directory can be read, False otherwise

        """
        loop = asyncio.get_running_loop()

        def _check_read_permission() -> bool:
            return FileSystemUtils.check_read_permission(path)

        return await loop.run_in_executor(None, _check_read_permission)

    @staticmethod
    def check_write_permission(path: str) -> bool:
        """Check if the directory has write permissions.

        Args:
            path: The directory path to check

        Returns:
            True if the directory can be written to, False otherwise

        """
        try:
            fs = FileSystemUtils.get_filesystem(path)

            # Check if path exists and is a directory
            if not fs.exists(path):
                return False

            if not fs.isdir(path):
                return False

            # Try to create a temporary file to test write permission
            # Handle path joining based on filesystem type
            protocol = _get_filesystem_protocol(path)
            if protocol != "file":
                # For remote paths, ensure proper path joining
                path_clean = path.rstrip("/")
                temp_file = f"{path_clean}/.__temp_permission_test_{uuid.uuid4().hex}.tmp"
            else:
                # For local paths, use Path for proper OS-specific handling
                temp_file = str(Path(path) / f".__temp_permission_test_{uuid.uuid4().hex}.tmp")

            try:
                # Try to write a temporary file
                fs.write_text(temp_file, "test", encoding="utf-8")
                # Clean up the temporary file
                fs.rm(temp_file)
                return True
            except (OSError, PermissionError):
                # Clean up if file was created but couldn't be removed
                try:
                    if fs.exists(temp_file):
                        fs.rm(temp_file)
                except Exception as e:  # noqa: BLE001
                    # Log cleanup failure but don't propagate the exception
                    logger = get_logger(__name__)
                    logger.debug("Failed to clean up temporary file %s: %s", temp_file, e)
                return False
        except (OSError, PermissionError):
            return False

    @staticmethod
    async def check_write_permission_async(path: str) -> bool:
        """Check if the directory has write permissions asynchronously.

        Args:
            path: The directory path to check

        Returns:
            True if the directory can be written to, False otherwise

        """
        loop = asyncio.get_running_loop()

        def _check_write_permission() -> bool:
            return FileSystemUtils.check_write_permission(path)

        return await loop.run_in_executor(None, _check_write_permission)

    @staticmethod
    def check_git_config() -> bool:
        """Check if git user configuration is available.

        This method checks if both user.name and user.email are configured
        in git, which are required for making commits. It checks both global
        and local git configuration.

        Returns:
            True if both user.name and user.email are configured, False otherwise

        """
        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "--version"],  # noqa: S607 TODO: AWA-139: harden this by specifiyng exact path to git
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode != 0:
                return False

            # Check for user.name
            name_result = subprocess.run(
                ["git", "config", "user.name"],  # noqa: S607 TODO: AWA-139: harden this by specifiyng exact path to git
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            # Check for user.email
            email_result = subprocess.run(
                ["git", "config", "user.email"],  # noqa: S607 TODO: AWA-139: harden this by specifiyng exact path to git
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )

            # Both commands should succeed and return non-empty values
            has_name = name_result.returncode == 0 and bool(name_result.stdout.strip())
            has_email = email_result.returncode == 0 and bool(email_result.stdout.strip())

            return has_name and has_email

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError):
            # Git not found, timeout, or other subprocess error
            return False

    @staticmethod
    async def check_git_config_async() -> bool:
        """Check if git user configuration is available asynchronously.

        This method checks if both user.name and user.email are configured
        in git, which are required for making commits. It checks both global
        and local git configuration.

        Returns:
            True if both user.name and user.email are configured, False otherwise

        """
        loop = asyncio.get_running_loop()

        def _check_git_config() -> bool:
            return FileSystemUtils.check_git_config()

        return await loop.run_in_executor(None, _check_git_config)

    @staticmethod
    def create_temp_directory(
        prefix: str | None = None,
        suffix: str | None = None,
        base_path: str | None = None,
    ) -> str:
        """Create a temporary directory.

        Args:
            prefix: Optional prefix for the temporary directory name
            suffix: Optional suffix for the temporary directory name
            base_path: Optional base path for the temporary directory. If provided and is a remote path,
                      creates the temp directory on the remote filesystem. Otherwise uses local tempfile.

        Returns:
            The path to the created temporary directory as a string

        """
        if base_path:
            protocol = _get_filesystem_protocol(base_path)
            if protocol != "file":
                # For remote filesystems, create a unique directory
                fs = FileSystemUtils.get_filesystem(base_path)
                temp_name = f"{prefix or 'tmp'}{uuid.uuid4().hex}{suffix or ''}"
                temp_path = f"{base_path}{temp_name}" if base_path.endswith("/") else f"{base_path}/{temp_name}"
                fs.makedirs(temp_path, exist_ok=True)
                return temp_path

        # For local filesystem or no base_path specified
        return tempfile.mkdtemp(prefix=prefix, suffix=suffix)

    @staticmethod
    async def create_temp_directory_async(
        prefix: str | None = None,
        suffix: str | None = None,
        base_path: str | None = None,
    ) -> str:
        """Create a temporary directory asynchronously.

        Args:
            prefix: Optional prefix for the temporary directory name
            suffix: Optional suffix for the temporary directory name
            base_path: Optional base path for the temporary directory. If provided and is a remote path,
                      creates the temp directory on the remote filesystem. Otherwise uses local tempfile.

        Returns:
            The path to the created temporary directory as a string

        """
        loop = asyncio.get_running_loop()

        def _create_temp_directory() -> str:
            return FileSystemUtils.create_temp_directory(
                prefix=prefix,
                suffix=suffix,
                base_path=base_path,
            )

        return await loop.run_in_executor(None, _create_temp_directory)

    @staticmethod
    def list_all_directories_recursive(source_dir: str) -> list[str]:
        """Recursively list all directories under the source directory.

        Args:
            source_dir: The root directory to search from

        Returns:
            A list of directory paths as strings

        """

        def _validate_directory(fs: AbstractFileSystem, path: str) -> None:
            """Validate that the path exists and is a directory."""
            if not fs.exists(path):
                raise FileNotFoundError(f"Source directory does not exist: {path}")
            if not fs.isdir(path):
                raise NotADirectoryError(f"Source path is not a directory: {path}")

        try:
            fs = FileSystemUtils.get_filesystem(source_dir)
            _validate_directory(fs, source_dir)

            # Recursively find all directories
            all_directories = []
            for root, dirs, _ in fs.walk(source_dir):
                for directory in dirs:
                    # Handle path joining based on filesystem type
                    protocol = _get_filesystem_protocol(source_dir)
                    if protocol != "file":
                        # For remote filesystems, use forward slash
                        dir_path = f"{root}/{directory}" if root else directory
                    else:
                        # For local filesystem, use the filesystem's separator
                        dir_path = fs.sep.join([root, directory])
                    all_directories.append(dir_path)

            return sorted(all_directories)  # Sort for consistent output
        except Exception:
            logger.exception(f"Error listing directories recursively from {source_dir}")
            raise

    @staticmethod
    async def list_all_directories_recursive_async(source_dir: str) -> list[str]:
        """Recursively list all directories under the source directory asynchronously.

        Args:
            source_dir: The root directory to search from

        Returns:
            A list of directory paths as strings

        """
        loop = asyncio.get_running_loop()

        def _list_all_directories_recursive() -> list[str]:
            return FileSystemUtils.list_all_directories_recursive(source_dir)

        return await loop.run_in_executor(None, _list_all_directories_recursive)

    @staticmethod
    def get_directory_info(directory_path: str) -> FolderInfo:
        """Get information about a single directory including its immediate files and subdirectories.

        Does not recurse into subdirectories.

        Args:
            directory_path: The path to the directory to analyze

        Returns:
            A DirectoryInfo object containing:
                - path: The directory path
                - files: List of file names (not full paths)
                - subdirectories: List of subdirectory names (not full paths)

        """

        def _validate_directory(fs: AbstractFileSystem, path: str) -> None:
            """Validate that the path exists and is a directory."""
            if not fs.exists(path):
                raise FileNotFoundError(f"Directory does not exist: {path}")
            if not fs.isdir(path):
                raise NotADirectoryError(f"Path is not a directory: {path}")

        try:
            fs = FileSystemUtils.get_filesystem(directory_path)
            _validate_directory(fs, directory_path)

            # Get immediate files and subdirectories
            files = []
            subdirectories = []

            for item in fs.ls(directory_path, detail=False):
                # Extract just the name from the full path
                # Handle different path formats based on filesystem type
                protocol = _get_filesystem_protocol(directory_path)
                item_name = item.split("/")[-1] if protocol != "file" else Path(item).name

                if fs.isfile(item):
                    files.append(item_name)
                elif fs.isdir(item):
                    subdirectories.append(item_name)

            return FolderInfo(
                path=directory_path,
                files=sorted(files),
                subdirectories=sorted(subdirectories),
            )
        except Exception:
            logger.exception(f"Error getting directory info for {directory_path}")
            raise

    @staticmethod
    async def get_directory_info_async(directory_path: str) -> FolderInfo:
        """Get information about a single directory asynchronously.

        Does not recurse into subdirectories.

        Args:
            directory_path: The path to the directory to analyze

        Returns:
            A DirectoryInfo object containing:
                - path: The directory path
                - files: List of file names (not full paths)
                - subdirectories: List of subdirectory names (not full paths)

        """
        loop = asyncio.get_running_loop()

        def _get_directory_info() -> FolderInfo:
            return FileSystemUtils.get_directory_info(directory_path)

        return await loop.run_in_executor(None, _get_directory_info)
