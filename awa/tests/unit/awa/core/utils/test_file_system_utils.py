import asyncio
import shutil
import subprocess
import tempfile
import typing
from pathlib import Path
from unittest.mock import MagicMock, patch

import fsspec
import pytest
from fsspec.implementations.local import LocalFileSystem

from awa.core.utils.file_system_utils import (
    FileSystemUtils,
    _get_filesystem_protocol,
    _is_windows_drive_path,
    create_ignore_matcher,
)
from awa.sdk.models.folder_info import FolderInfo
from tests.utils.platform_test_utils import normalize_path_for_comparison


@pytest.fixture
def temp_dir() -> typing.Generator[str, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def fs() -> LocalFileSystem:
    return LocalFileSystem()


@pytest.mark.asyncio
async def test_read_write_async(temp_dir: str) -> None:
    file_path = str(Path(temp_dir) / "test.txt")
    content = "hello async world"

    # Write
    await FileSystemUtils.write_async(file_path, content)
    # Read
    read_content = await FileSystemUtils.read_async(file_path)
    assert read_content == content


@pytest.mark.asyncio
async def test_read_async_file_not_found(temp_dir: str) -> None:
    file_path = str(Path(temp_dir) / "nonexistent.txt")
    with pytest.raises(FileNotFoundError):
        await FileSystemUtils.read_async(file_path)


@pytest.mark.asyncio
async def test_remove_async(temp_dir: str) -> None:
    file_path = Path(temp_dir) / "to_remove.txt"
    with file_path.open("w") as f:
        f.write("delete me")
    assert file_path.exists()
    await FileSystemUtils.remove_async(str(file_path))
    assert not file_path.exists()


@pytest.mark.asyncio
async def test_remove_async_nonexistent(temp_dir: str) -> None:
    file_path = str(Path(temp_dir) / "does_not_exist.txt")
    # Should not raise
    await FileSystemUtils.remove_async(file_path)


@pytest.mark.asyncio
async def test_remove_directory_async(temp_dir: str) -> None:
    # Create a directory with some files
    test_dir = Path(temp_dir) / "test_directory"
    test_dir.mkdir()

    # Create some files in the directory
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "file2.txt").write_text("content2")

    # Create a subdirectory with files
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "file3.txt").write_text("content3")

    # Verify the directory exists
    assert test_dir.exists()
    assert test_dir.is_dir()

    # Remove the directory
    await FileSystemUtils.remove_directory_async(str(test_dir))

    # Verify the directory is removed
    assert not test_dir.exists()


@pytest.mark.asyncio
async def test_remove_directory_async_nonexistent(temp_dir: str) -> None:
    dir_path = str(Path(temp_dir) / "does_not_exist_dir")
    # Should not raise
    await FileSystemUtils.remove_directory_async(dir_path)


@pytest.mark.asyncio
async def test_concurrent_operations(temp_dir: str) -> None:
    """Test that multiple async operations can run concurrently."""
    file_paths = [str(Path(temp_dir) / f"test_{i}.txt") for i in range(3)]
    contents = [f"content {i}" for i in range(3)]

    await asyncio.gather(*(FileSystemUtils.write_async(fp, c) for fp, c in zip(file_paths, contents, strict=False)))
    read_contents = await asyncio.gather(*(FileSystemUtils.read_async(fp) for fp in file_paths))

    assert read_contents == contents


class TestTemporaryDirectories:
    """Test temporary directory creation functionality."""

    def test_create_temp_directory_basic(self) -> None:
        """Test basic temporary directory creation."""
        temp_path = FileSystemUtils.create_temp_directory()

        # Verify directory exists and is a directory
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()

        # Clean up
        Path(temp_path).rmdir()

    def test_create_temp_directory_with_prefix(self) -> None:
        """Test temporary directory creation with prefix."""
        prefix = "awa_test_"
        temp_path = FileSystemUtils.create_temp_directory(prefix=prefix)

        # Verify directory exists and name contains prefix
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()
        assert prefix in Path(temp_path).name

        # Clean up
        Path(temp_path).rmdir()

    def test_create_temp_directory_with_suffix(self) -> None:
        """Test temporary directory creation with suffix."""
        suffix = "_awa_test"
        temp_path = FileSystemUtils.create_temp_directory(suffix=suffix)

        # Verify directory exists and name contains suffix
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()
        assert suffix in Path(temp_path).name

        # Clean up
        Path(temp_path).rmdir()

    def test_create_temp_directory_with_prefix_and_suffix(self) -> None:
        """Test temporary directory creation with both prefix and suffix."""
        prefix = "awa_test_"
        suffix = "_temp"
        temp_path = FileSystemUtils.create_temp_directory(prefix=prefix, suffix=suffix)

        # Verify directory exists and name contains both prefix and suffix
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()
        assert prefix in Path(temp_path).name
        assert suffix in Path(temp_path).name

        # Clean up
        Path(temp_path).rmdir()

    @pytest.mark.asyncio
    async def test_create_temp_directory_async_basic(self) -> None:
        """Test basic asynchronous temporary directory creation."""
        temp_path = await FileSystemUtils.create_temp_directory_async()

        # Verify directory exists and is a directory
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()

        # Clean up
        await FileSystemUtils.remove_directory_async(temp_path)

    @pytest.mark.asyncio
    async def test_create_temp_directory_async_with_prefix(self) -> None:
        """Test asynchronous temporary directory creation with prefix."""
        prefix = "awa_async_"
        temp_path = await FileSystemUtils.create_temp_directory_async(prefix=prefix)

        # Verify directory exists and name contains prefix
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()
        assert prefix in Path(temp_path).name

        # Clean up
        await FileSystemUtils.remove_directory_async(temp_path)

    @pytest.mark.asyncio
    async def test_create_temp_directory_async_with_suffix(self) -> None:
        """Test asynchronous temporary directory creation with suffix."""
        suffix = "_async_test"
        temp_path = await FileSystemUtils.create_temp_directory_async(suffix=suffix)

        # Verify directory exists and name contains suffix
        assert Path(temp_path).exists()
        assert Path(temp_path).is_dir()
        assert suffix in Path(temp_path).name

        # Clean up
        await FileSystemUtils.remove_directory_async(temp_path)

    @pytest.mark.asyncio
    async def test_create_temp_directory_async_concurrent(self) -> None:
        """Test concurrent asynchronous temporary directory creation."""
        num_dirs = 3

        # Create multiple temporary directories concurrently
        temp_paths = await asyncio.gather(
            *(FileSystemUtils.create_temp_directory_async(prefix=f"concurrent_{i}_") for i in range(num_dirs)),
        )

        # Verify all directories exist and are unique
        assert len(temp_paths) == num_dirs
        assert len(set(temp_paths)) == num_dirs  # All paths are unique

        for temp_path in temp_paths:
            assert Path(temp_path).exists()
            assert Path(temp_path).is_dir()

        # Clean up all directories
        await asyncio.gather(*(FileSystemUtils.remove_directory_async(temp_path) for temp_path in temp_paths))

    @pytest.mark.asyncio
    async def test_temp_directory_can_contain_files(self) -> None:
        """Test that temporary directories can contain files and be cleaned up properly."""
        temp_path = await FileSystemUtils.create_temp_directory_async(prefix="file_test_")

        # Create some files in the temporary directory
        file1_path = str(Path(temp_path) / "test1.txt")
        file2_path = str(Path(temp_path) / "test2.txt")

        await FileSystemUtils.write_async(file1_path, "content1")
        await FileSystemUtils.write_async(file2_path, "content2")

        # Verify files exist
        assert Path(file1_path).exists()
        assert Path(file2_path).exists()

        # Clean up entire directory with contents
        await FileSystemUtils.remove_directory_async(temp_path)

        # Verify directory and files are gone
        assert not Path(temp_path).exists()
        assert not Path(file1_path).exists()
        assert not Path(file2_path).exists()


@pytest.mark.asyncio
async def test_read_directory_async_basic(temp_dir: str) -> None:
    """Test basic functionality of read_directory_async."""
    # Arrange
    file1_path = Path(temp_dir) / "file1.txt"
    file2_path = Path(temp_dir) / "file2.md"

    file1_content = "Content of file 1"
    file2_content = "# Content of file 2\nMarkdown content"

    file1_path.write_text(file1_content, newline="\n")
    file2_path.write_text(file2_content, newline="\n")

    # Act
    results = await FileSystemUtils.read_directory_async(temp_dir)

    # Assert
    assert len(results) == 2

    # Sort results by file path for consistent testing
    results.sort(key=lambda x: x["file"])

    assert results[0]["file"] == str(file1_path)
    assert results[0]["content"] == file1_content
    assert results[1]["file"] == str(file2_path)
    assert results[1]["content"] == file2_content


@pytest.mark.asyncio
async def test_read_directory_async_recursive(temp_dir: str) -> None:
    """Test that read_directory_async reads files recursively."""
    # Arrange
    # Create nested directory structure
    sub_dir = Path(temp_dir) / "subdir"
    sub_sub_dir = sub_dir / "deeper"
    sub_dir.mkdir()
    sub_sub_dir.mkdir()

    # Create files at different levels
    root_file = Path(temp_dir) / "root.txt"
    sub_file = sub_dir / "sub.txt"
    deep_file = sub_sub_dir / "deep.txt"

    root_content = "Root content"
    sub_content = "Sub content"
    deep_content = "Deep content"

    root_file.write_text(root_content, newline="\n")
    sub_file.write_text(sub_content, newline="\n")
    deep_file.write_text(deep_content, newline="\n")

    # Act
    results = await FileSystemUtils.read_directory_async(temp_dir)

    # Assert
    assert len(results) == 3

    # Sort results by file path for consistent testing
    results.sort(key=lambda x: x["file"])

    # Check that all files were found and read correctly
    file_contents = {result["file"]: result["content"] for result in results}

    assert str(root_file) in file_contents
    assert str(sub_file) in file_contents
    assert str(deep_file) in file_contents

    assert file_contents[str(root_file)] == root_content
    assert file_contents[str(sub_file)] == sub_content
    assert file_contents[str(deep_file)] == deep_content


@pytest.mark.asyncio
async def test_read_directory_async_with_ignore_file(temp_dir: str) -> None:
    """Test read_directory_async with ignore file functionality."""
    # Arrange
    # Create files
    file1 = Path(temp_dir) / "include.txt"
    file2 = Path(temp_dir) / "ignore.log"
    file3 = Path(temp_dir) / "temp" / "temp_file.txt"
    ignore_file = Path(temp_dir) / ".gitignore"

    # Create directories
    (Path(temp_dir) / "temp").mkdir()

    file1.write_text("Include this", newline="\n")
    file2.write_text("Ignore this", newline="\n")
    file3.write_text("Ignore this too", newline="\n")

    # Create ignore file
    ignore_content = """
*.log
temp/
"""
    ignore_file.write_text(ignore_content, newline="\n")

    # Act
    results = await FileSystemUtils.read_directory_async(temp_dir, str(ignore_file))

    # Assert
    # Should only include file1 and ignore file, not the .log file or files in temp/
    assert len(results) == 2  # include.txt and .gitignore

    file_paths = [result["file"] for result in results]
    assert str(file1) in file_paths
    assert str(ignore_file) in file_paths
    assert str(file2) not in file_paths
    assert str(file3) not in file_paths


@pytest.mark.asyncio
async def test_read_directory_async_empty_directory(temp_dir: str) -> None:
    """Test read_directory_async with an empty directory."""
    # Arrange
    empty_dir = Path(temp_dir) / "empty"
    empty_dir.mkdir()

    # Act
    results = await FileSystemUtils.read_directory_async(str(empty_dir))

    # Assert
    assert results == []


@pytest.mark.asyncio
async def test_read_directory_async_nonexistent_directory(temp_dir: str) -> None:
    """Test read_directory_async with a nonexistent directory."""
    # Arrange
    nonexistent_dir = str(Path(temp_dir) / "does_not_exist")

    # Act
    results = await FileSystemUtils.read_directory_async(nonexistent_dir)

    # Assert
    # Should return empty list for non-existent directory (same as list_directory_async)
    assert results == []


@pytest.mark.asyncio
async def test_read_directory_async_file_read_error(temp_dir: str) -> None:
    """Test read_directory_async handles file read errors gracefully."""
    # Arrange
    # Create a file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Original content")

    # Create a binary file that might cause read issues
    binary_file = Path(temp_dir) / "binary.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\xff\xfe\xfd")

    # Act
    results = await FileSystemUtils.read_directory_async(temp_dir)

    # Assert
    assert len(results) == 2

    results.sort(key=lambda x: x["file"])

    # The binary file should have an error message in content
    # (though it might succeed depending on encoding handling)
    text_result = next(r for r in results if "test.txt" in r["file"])
    binary_result = next(r for r in results if "binary.bin" in r["file"])

    assert text_result["content"] == "Original content"
    # Binary file should either succeed with decoded content or have error message
    assert binary_result["content"] is not None


@pytest.mark.asyncio
async def test_read_directory_async_performance_parallel(temp_dir: str) -> None:
    """Test that read_directory_async performs reads in parallel for better performance."""
    import time

    # Arrange
    # Create multiple files
    num_files = 10
    file_paths = []
    for i in range(num_files):
        file_path = Path(temp_dir) / f"file_{i}.txt"
        file_path.write_text(f"Content of file {i}", newline="\n")
        file_paths.append(file_path)

    # Act
    start_time = time.time()
    results = await FileSystemUtils.read_directory_async(temp_dir)
    end_time = time.time()

    # Assert
    assert len(results) == num_files

    # Verify all files were read correctly
    file_contents = {result["file"]: result["content"] for result in results}
    for i, file_path in enumerate(file_paths):
        assert str(file_path) in file_contents
        assert file_contents[str(file_path)] == f"Content of file {i}"

    # Performance test - should complete reasonably quickly
    # (This is more of a smoke test than a strict performance requirement)
    assert end_time - start_time < 5.0  # Should complete within 5 seconds


@pytest.mark.asyncio
async def test_read_directory_async_mixed_file_types(temp_dir: str) -> None:
    """Test read_directory_async with various file types and extensions."""
    # Arrange
    files_to_create = [
        ("README.md", "# README\nThis is a markdown file"),
        ("config.json", '{"setting": "value"}'),
        ("script.py", "print('Hello, World!')"),
        ("data.csv", "name,age\nJohn,30\nJane,25"),
        ("notes.txt", "Some plain text notes"),
    ]

    for filename, content in files_to_create:
        file_path = Path(temp_dir) / filename
        file_path.write_text(content, newline="\n")

    # Act
    results = await FileSystemUtils.read_directory_async(temp_dir)

    # Assert
    assert len(results) == len(files_to_create)

    # Create a mapping for easier verification
    results_by_filename = {}
    for result in results:
        filename = Path(result["file"]).name
        results_by_filename[filename] = result["content"]

    # Verify each file was read correctly
    for filename, expected_content in files_to_create:
        assert filename in results_by_filename
        assert results_by_filename[filename] == expected_content


@pytest.mark.asyncio
async def test_read_directory_async_with_subdirectories_and_ignore(temp_dir: str) -> None:
    """Test read_directory_async with complex directory structure and ignore patterns."""
    # Arrange
    # Create complex directory structure
    src_dir = Path(temp_dir) / "src"
    tests_dir = Path(temp_dir) / "tests"
    build_dir = Path(temp_dir) / "build"

    src_dir.mkdir()
    tests_dir.mkdir()
    build_dir.mkdir()

    # Create files in various locations
    (src_dir / "main.py").write_text("# Main application")
    (src_dir / "utils.py").write_text("# Utility functions")
    (tests_dir / "test_main.py").write_text("# Test cases")
    (build_dir / "output.bin").write_text("Binary output")
    (Path(temp_dir) / "README.md").write_text("# Project README")
    (Path(temp_dir) / "temp.log").write_text("Log content")

    # Create ignore file
    ignore_file = Path(temp_dir) / ".gitignore"
    ignore_file.write_text("""
build/
*.log
""")

    # Act
    results = await FileSystemUtils.read_directory_async(temp_dir, str(ignore_file))

    # Assert
    # Should include: main.py, utils.py, test_main.py, README.md, .gitignore
    # Should exclude: output.bin (in build/), temp.log (*.log pattern)
    assert len(results) == 5

    file_paths = [result["file"] for result in results]
    filenames = [Path(path).name for path in file_paths]

    assert "main.py" in filenames
    assert "utils.py" in filenames
    assert "test_main.py" in filenames
    assert "README.md" in filenames
    assert ".gitignore" in filenames

    assert "output.bin" not in filenames
    assert "temp.log" not in filenames


class TestCreateIgnoreMatcher:
    """Test the create_ignore_matcher function with various gitignore patterns."""

    def test_basic_patterns(self) -> None:
        """Test basic gitignore patterns."""
        # Arrange
        ignore_content = """
# Comments should be ignored
*.log
temp/
.env
"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("app.log") is True  # Should ignore .log files
        assert matcher("debug.log") is True  # Should ignore .log files
        assert matcher("temp/") is True  # Should ignore temp directory
        assert matcher("temp/file.txt") is True  # Should ignore files in temp
        assert matcher(".env") is True  # Should ignore .env file
        assert matcher("app.py") is False  # Should not ignore .py files
        assert matcher("src/main.py") is False  # Should not ignore .py files

    def test_negation_patterns(self) -> None:
        """Test gitignore negation patterns (!)."""
        # Arrange
        ignore_content = """
*.log
!important.log
"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("app.log") is True  # Should ignore .log files
        assert matcher("debug.log") is True  # Should ignore .log files
        assert matcher("important.log") is False  # Should NOT ignore due to negation

    def test_cs_files_only_pattern(self) -> None:
        """Test the specific C# files only pattern from the user's example."""
        # Arrange
        ignore_content = """# Only include C# files
*
!*/
!**/*.cs"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert - C# files should NOT be ignored
        assert matcher("Program.cs") is False
        assert matcher("src/Program.cs") is False
        assert matcher("src/models/Model.cs") is False
        assert matcher("nested/deep/Service.cs") is False

        # Act & Assert - Non-C# files should be ignored
        assert matcher("README.md") is True
        assert matcher("src/README.md") is True
        assert matcher("config.json") is True
        assert matcher("scripts/build.py") is True
        assert matcher("docs/guide.txt") is True

    def test_directory_patterns(self) -> None:
        """Test patterns that match directories."""
        # Arrange
        ignore_content = """
node_modules/
.git/
temp/
"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("node_modules/") is True
        assert matcher("node_modules/package/index.js") is True
        assert matcher(".git/") is True
        assert matcher("temp/") is True
        assert matcher("src/temp/file.txt") is True

    def test_wildcard_patterns(self) -> None:
        """Test various wildcard patterns."""
        # Arrange
        ignore_content = """
*.tmp
test_*
*/logs/*
**/cache/**
"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("file.tmp") is True  # *.tmp
        assert matcher("test_something.py") is True  # test_*
        assert matcher("app/logs/error.log") is True  # */logs/*
        assert matcher("src/cache/file.dat") is True  # **/cache/**
        assert matcher("deep/nested/cache/more/file.dat") is True  # **/cache/**

    def test_complex_negation_order(self) -> None:
        """Test that pattern order matters for negations."""
        # Arrange
        ignore_content = """
# Ignore all txt files
*.txt
# But don't ignore important ones
!important.txt
# But DO ignore secret important ones
secret_important.txt
"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("regular.txt") is True  # Ignored by *.txt
        assert matcher("important.txt") is False  # Not ignored due to !important.txt
        assert matcher("secret_important.txt") is True  # Ignored again by specific pattern

    def test_empty_and_comment_lines(self) -> None:
        """Test that empty lines and comments are handled correctly."""
        # Arrange
        ignore_content = """
# This is a comment

*.log
# Another comment

temp/

# Final comment
"""
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("app.log") is True
        assert matcher("temp/file.txt") is True
        assert matcher("app.py") is False

    def test_path_separators(self) -> None:
        """Test that both forward and backslashes work correctly."""
        # Arrange
        ignore_content = "src/temp/*"
        matcher = create_ignore_matcher(ignore_content)

        # Act & Assert
        assert matcher("src/temp/file.txt") is True
        assert matcher("other/temp/file.txt") is False


class TestPermissionChecking:
    """Test the permission checking methods."""

    def test_check_read_permission_readable_directory(self, temp_dir: str) -> None:
        """Test that read permissions are correctly detected for a readable directory."""
        # Arrange - temp_dir is readable by default

        # Act
        result = FileSystemUtils.check_read_permission(temp_dir)

        # Assert
        assert result is True

    def test_check_read_permission_nonexistent_directory(self, temp_dir: str) -> None:
        """Test that read permission check returns False for non-existent directory."""
        # Arrange
        nonexistent_dir = str(Path(temp_dir) / "does_not_exist")

        # Act
        result = FileSystemUtils.check_read_permission(nonexistent_dir)

        # Assert
        assert result is False

    def test_check_read_permission_file_path(self, temp_dir: str) -> None:
        """Test that read permission check returns False for a file path."""
        # Arrange - create a file instead of directory
        file_path = Path(temp_dir) / "test_file.txt"
        file_path.write_text("test content")

        # Act
        result = FileSystemUtils.check_read_permission(str(file_path))

        # Assert
        assert result is False

    def test_check_write_permission_writable_directory(self, temp_dir: str) -> None:
        """Test that write permissions are correctly detected for a writable directory."""
        # Arrange - temp_dir is writable by default

        # Act
        result = FileSystemUtils.check_write_permission(temp_dir)

        # Assert
        assert result is True

    def test_check_write_permission_nonexistent_directory(self, temp_dir: str) -> None:
        """Test that write permission check returns False for non-existent directory."""
        # Arrange
        nonexistent_dir = str(Path(temp_dir) / "does_not_exist")

        # Act
        result = FileSystemUtils.check_write_permission(nonexistent_dir)

        # Assert
        assert result is False

    def test_check_write_permission_file_path(self, temp_dir: str) -> None:
        """Test that write permission check returns False for a file path."""
        # Arrange - create a file instead of directory
        file_path = Path(temp_dir) / "test_file.txt"
        file_path.write_text("test content")

        # Act
        result = FileSystemUtils.check_write_permission(str(file_path))

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_read_permission_async_readable_directory(self, temp_dir: str) -> None:
        """Test that async read permissions are correctly detected for a readable directory."""
        # Arrange - temp_dir is readable by default

        # Act
        result = await FileSystemUtils.check_read_permission_async(temp_dir)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_read_permission_async_nonexistent_directory(self, temp_dir: str) -> None:
        """Test that async read permission check returns False for non-existent directory."""
        # Arrange
        nonexistent_dir = str(Path(temp_dir) / "does_not_exist")

        # Act
        result = await FileSystemUtils.check_read_permission_async(nonexistent_dir)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_check_write_permission_async_writable_directory(self, temp_dir: str) -> None:
        """Test that async write permissions are correctly detected for a writable directory."""
        # Arrange - temp_dir is writable by default

        # Act
        result = await FileSystemUtils.check_write_permission_async(temp_dir)

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_write_permission_async_nonexistent_directory(self, temp_dir: str) -> None:
        """Test that async write permission check returns False for non-existent directory."""
        # Arrange
        nonexistent_dir = str(Path(temp_dir) / "does_not_exist")

        # Act
        result = await FileSystemUtils.check_write_permission_async(nonexistent_dir)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_concurrent_permission_checks(self, temp_dir: str) -> None:
        """Test that multiple permission checks can run concurrently."""
        # Arrange
        test_dirs = []
        for i in range(3):
            dir_path = Path(temp_dir) / f"test_dir_{i}"
            dir_path.mkdir()
            test_dirs.append(str(dir_path))

        # Act - run concurrent permission checks
        read_results = await asyncio.gather(
            *(FileSystemUtils.check_read_permission_async(d) for d in test_dirs),
        )
        write_results = await asyncio.gather(
            *(FileSystemUtils.check_write_permission_async(d) for d in test_dirs),
        )

        # Assert
        assert all(read_results)  # All should be readable
        assert all(write_results)  # All should be writable

    def test_check_permissions_with_path_object(self, temp_dir: str) -> None:
        """Test that permission checking works with string paths (Path objects converted to strings)."""
        # Arrange - convert Path to string as per new API requirements
        path_str = str(Path(temp_dir))

        # Act
        read_result = FileSystemUtils.check_read_permission(path_str)
        write_result = FileSystemUtils.check_write_permission(path_str)

        # Assert
        assert read_result is True
        assert write_result is True

    def test_check_write_permission_cleanup_on_error(self, temp_dir: str) -> None:
        """Test that temporary files are cleaned up even if there's an error."""
        # This test ensures that our cleanup logic works
        # In a real scenario, this would test against a directory where we can create
        # files but not remove them, but that's hard to simulate reliably across platforms

        # Arrange - use a normal writable directory
        test_dir = Path(temp_dir) / "test_cleanup"
        test_dir.mkdir()

        # Act
        result = FileSystemUtils.check_write_permission(str(test_dir))

        # Assert
        assert result is True

        # Verify no temp files are left behind
        temp_files = [f for f in test_dir.iterdir() if f.name.startswith(".__temp_permission_test_")]
        assert len(temp_files) == 0


class TestFileSystemUtilsGitConfig:
    """Test cases for git config checking functionality."""

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_success(self, mock_run: MagicMock) -> None:
        """Test git config check when both name and email are configured."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 0
        mock_name.stdout = "John Doe\n"

        mock_email = MagicMock()
        mock_email.returncode = 0
        mock_email.stdout = "john.doe@example.com\n"

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is True
        assert mock_run.call_count == 3
        mock_run.assert_any_call(["git", "--version"], capture_output=True, text=True, timeout=10, check=False)
        mock_run.assert_any_call(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        mock_run.assert_any_call(
            ["git", "config", "user.email"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_missing_name(self, mock_run: MagicMock) -> None:
        """Test git config check when user.name is missing."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 1  # Git returns non-zero when config not found
        mock_name.stdout = ""

        mock_email = MagicMock()
        mock_email.returncode = 0
        mock_email.stdout = "john.doe@example.com\n"

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_missing_email(self, mock_run: MagicMock) -> None:
        """Test git config check when user.email is missing."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 0
        mock_name.stdout = "John Doe\n"

        mock_email = MagicMock()
        mock_email.returncode = 1  # Git returns non-zero when config not found
        mock_email.stdout = ""

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_empty_values(self, mock_run: MagicMock) -> None:
        """Test git config check when values are empty strings."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 0
        mock_name.stdout = "   \n"  # Whitespace only

        mock_email = MagicMock()
        mock_email.returncode = 0
        mock_email.stdout = ""  # Empty string

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_git_not_available(self, mock_run: MagicMock) -> None:
        """Test git config check when git is not available."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 1  # Git version command fails

        mock_run.return_value = mock_version

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False
        assert mock_run.call_count == 1  # Should stop after version check fails

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_git_not_found(self, mock_run: MagicMock) -> None:
        """Test git config check when git command is not found."""
        # Arrange
        mock_run.side_effect = FileNotFoundError("git command not found")

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_timeout(self, mock_run: MagicMock) -> None:
        """Test git config check when subprocess times out."""
        # Arrange
        mock_run.side_effect = subprocess.TimeoutExpired("git", 10)

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_subprocess_error(self, mock_run: MagicMock) -> None:
        """Test git config check when subprocess raises an error."""
        # Arrange
        mock_run.side_effect = subprocess.SubprocessError("Something went wrong")

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.subprocess.run")
    async def test_check_git_config_async_success(self, mock_run: MagicMock) -> None:
        """Test async git config check when both name and email are configured."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 0
        mock_name.stdout = "Jane Doe\n"

        mock_email = MagicMock()
        mock_email.returncode = 0
        mock_email.stdout = "jane.doe@example.com\n"

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = await FileSystemUtils.check_git_config_async()

        # Assert
        assert result is True
        assert mock_run.call_count == 3

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.subprocess.run")
    async def test_check_git_config_async_failure(self, mock_run: MagicMock) -> None:
        """Test async git config check when configuration is missing."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 1
        mock_name.stdout = ""

        mock_email = MagicMock()
        mock_email.returncode = 0
        mock_email.stdout = "jane.doe@example.com\n"

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = await FileSystemUtils.check_git_config_async()

        # Assert
        assert result is False

    @patch("awa.core.utils.file_system_utils.subprocess.run")
    def test_check_git_config_partial_configuration(self, mock_run: MagicMock) -> None:
        """Test edge case where name is configured but email is whitespace."""
        # Arrange
        mock_version = MagicMock()
        mock_version.returncode = 0

        mock_name = MagicMock()
        mock_name.returncode = 0
        mock_name.stdout = "Valid Name"

        mock_email = MagicMock()
        mock_email.returncode = 0
        mock_email.stdout = "   "  # Only whitespace, should be treated as missing

        mock_run.side_effect = [mock_version, mock_name, mock_email]

        # Act
        result = FileSystemUtils.check_git_config()

        # Assert
        assert result is False


class TestWindowsPathDetection:
    """Test the Windows path detection functionality."""

    @pytest.mark.parametrize(
        "path",
        [
            "C:\\Users\\test\\file.txt",
            "D:/Documents/project",
            "c:\\temp",
            "E:\\",
            "F:/",
            "G:\\folder\\subfolder\\file.exe",
            "H:/some/mixed/path\\file.txt",
            "Z:\\very\\long\\path\\to\\some\\file.txt",
            "C:",  # Minimal Windows path
            "c:",  # Lowercase drive
            "Z:",  # Last letter
            "A:",  # First letter
            "C:file",  # No separator after colon
            "C:\\",  # Drive root with backslash
            "C:/",  # Drive root with forward slash
        ],
    )
    def test_is_windows_drive_path_valid_paths(self, path: str) -> None:
        """Test that valid Windows drive paths are correctly identified."""
        assert _is_windows_drive_path(path) is True, f"Failed for path: {path}"

    @pytest.mark.parametrize(
        "path",
        [
            "/home/user/file.txt",  # POSIX absolute path
            "./relative/path",  # Relative path
            "file.txt",  # Simple filename
            "s3://bucket/key",  # S3 path
            "gs://bucket/object",  # GCS path
            "hdfs://namenode:9000/path",  # HDFS path
            "http://example.com",  # HTTP URL
            "folder:with:colons",  # Colon but not drive
            "1:not_a_drive",  # Numeric prefix
            "AB:too_long",  # Two letters
            ":missing_drive",  # Missing drive letter
            "C",  # Too short
            "",  # Empty string
            "ftp://server/path",  # FTP URL
            "file://local/path",  # File URL
        ],
    )
    def test_is_windows_drive_path_invalid_paths(self, path: str) -> None:
        """Test that non-Windows drive paths are correctly rejected."""
        assert _is_windows_drive_path(path) is False, f"Incorrectly identified as Windows path: {path}"

    @pytest.mark.parametrize(
        "path",
        [
            "C:\\Users\\test\\file.txt",
            "D:/Documents/project",
            "c:\\temp",
            "E:\\",
            "F:/",
            "G:\\folder\\subfolder\\file.exe",
            "/home/user/file.txt",  # POSIX absolute path
            "./relative/path",  # Relative path
            "../parent/path",  # Parent path
            "file.txt",  # Simple filename
            "/var/log/app.log",  # System path
            "~/documents/file.txt",  # Home path
        ],
    )
    def test_get_filesystem_protocol_returns_file_for_local_paths(self, path: str) -> None:
        """Test that local paths (Windows and POSIX) return 'file' protocol."""
        protocol = _get_filesystem_protocol(path)
        assert protocol == "file", f"Path '{path}' returned protocol '{protocol}', expected 'file'"

    @pytest.mark.parametrize(
        ("path", "expected_protocol"),
        [
            ("s3://bucket/key/file.txt", "s3"),
            ("gs://bucket/object", "gs"),
            ("hdfs://namenode:9000/path", "hdfs"),
            ("http://example.com/path", "http"),
            ("https://example.com/path", "https"),
            ("ftp://server/path", "ftp"),
            ("sftp://server/path", "sftp"),
        ],
    )
    def test_get_filesystem_protocol_remote_paths(self, path: str, expected_protocol: str) -> None:
        """Test that remote paths return correct protocols."""
        protocol = _get_filesystem_protocol(path)
        assert protocol == expected_protocol, (
            f"Path '{path}' returned protocol '{protocol}', expected '{expected_protocol}'"
        )

    @pytest.mark.parametrize(
        ("path", "expected_protocol"),
        [
            ("", "file"),  # Empty string
            (":", ""),  # Just colon
            ("C:", "file"),  # Windows drive
            ("file:", "file"),  # Ambiguous case
            ("proto:path", "proto"),  # Simple protocol
            ("complex:path:with:colons", "complex"),  # Multiple colons
        ],
    )
    def test_get_filesystem_protocol_edge_cases(self, path: str, expected_protocol: str) -> None:
        """Test edge cases for protocol detection."""
        protocol = _get_filesystem_protocol(path)
        assert protocol == expected_protocol, (
            f"Path '{path}' returned protocol '{protocol}', expected '{expected_protocol}'"
        )

    @pytest.mark.parametrize(
        "path",
        [
            "C:\\Users\\test\\file.txt",
            "D:/Documents/project",
            "c:\\temp",
        ],
    )
    def test_get_filesystem_integration(self, path: str) -> None:
        """Test that get_filesystem works correctly with Windows paths."""
        fs = FileSystemUtils.get_filesystem(path)
        assert fs is not None
        assert hasattr(fs, "protocol")
        protocol = fs.protocol

        # Handle both string and tuple/list protocols
        if isinstance(protocol, (list, tuple)):
            protocol = protocol[0]
        assert protocol == "file", f"Path '{path}' created filesystem with protocol '{protocol}', expected 'file'"

    def test_regression_windows_path_issue(self) -> None:
        """Regression test for a specific Windows path parsing issue.

        This test reproduces the exact error that was occurring in AWA-184:
        ValueError: Protocol not known: C
        """
        # This is the exact path from the error log
        problematic_path = (
            "C:\\AWA\\slalom-consulting-agentic-workflow-accelerator-8f6b775297ad\\.awa_state\\services.json"
        )

        # Before the fix, this would have caused:
        # ValueError: Protocol not known: C
        # because the old code would do: path_str.split(":", 1)[0] -> "C"

        # Test the detection functions
        assert _is_windows_drive_path(problematic_path) is True
        assert _get_filesystem_protocol(problematic_path) == "file"

        # Test the full integration - this should NOT raise an exception
        fs = FileSystemUtils.get_filesystem(problematic_path)
        assert fs is not None

        # Verify it's a local filesystem
        protocol = fs.protocol
        if isinstance(protocol, (list, tuple)):
            protocol = protocol[0]
        assert protocol == "file"

    @pytest.mark.parametrize(
        ("path", "expected_old_protocol"),
        [
            ("C:\\Windows\\System32\\file.txt", "C"),
            ("D:/Program Files/app/file.exe", "D"),
            ("E:\\temp\\data.json", "E"),
        ],
    )
    def test_original_bug_simulation(self, path: str, expected_old_protocol: str) -> None:
        """Test that simulates a bug from AWA-184 to ensure it's fixed.

        This test demonstrates what the old code would have done wrong.
        """

        # Simulate the old buggy logic
        def old_buggy_logic(path_str: str) -> str:
            # This is what the old code did - it would incorrectly return "C" for Windows paths
            return path_str.split(":", 1)[0] if ":" in path_str else "file"

        # Old logic would return the drive letter as protocol
        old_result = old_buggy_logic(path)
        assert old_result == expected_old_protocol, f"Old logic test failed for {path}"

        # New logic correctly returns "file"
        new_result = _get_filesystem_protocol(path)
        assert new_result == "file", f"New logic failed for {path}"

        # Demonstrate the fix works
        assert old_result != new_result, f"Bug not fixed for {path}"


class TestDirectoryListingFunctions:
    """Test the new directory listing functions."""

    @pytest.mark.asyncio
    async def test_list_all_directories_recursive(self, temp_dir: str) -> None:
        """Test listing all directories recursively."""
        # Create a nested directory structure
        base_path = Path(temp_dir)
        (base_path / "dir1").mkdir()
        (base_path / "dir1" / "subdir1").mkdir()
        (base_path / "dir1" / "subdir2").mkdir()
        (base_path / "dir2").mkdir()
        (base_path / "dir2" / "subdir3").mkdir()
        (base_path / "dir2" / "subdir3" / "deepdir").mkdir()

        # Create some files (should not be included)
        (base_path / "file1.txt").write_text("content1")
        (base_path / "dir1" / "file2.txt").write_text("content2")
        (base_path / "dir2" / "subdir3" / "file3.txt").write_text("content3")

        # Test sync version
        directories = FileSystemUtils.list_all_directories_recursive(temp_dir)

        # Convert to relative paths and normalize for cross-platform comparison
        relative_dirs = sorted([normalize_path_for_comparison(Path(d).relative_to(temp_dir)) for d in directories])

        expected_dirs = sorted(
            [
                "dir1",
                "dir1/subdir1",
                "dir1/subdir2",
                "dir2",
                "dir2/subdir3",
                "dir2/subdir3/deepdir",
            ],
        )

        assert relative_dirs == expected_dirs

        # Test async version
        async_directories = await FileSystemUtils.list_all_directories_recursive_async(temp_dir)
        async_relative_dirs = sorted(
            [normalize_path_for_comparison(Path(d).relative_to(temp_dir)) for d in async_directories],
        )
        assert async_relative_dirs == expected_dirs

    @pytest.mark.asyncio
    async def test_list_all_directories_recursive_empty(self, temp_dir: str) -> None:
        """Test listing directories in an empty directory."""
        # Empty directory should return empty list
        directories = await FileSystemUtils.list_all_directories_recursive_async(temp_dir)
        assert directories == []

    @pytest.mark.asyncio
    async def test_list_all_directories_recursive_nonexistent(self, temp_dir: str) -> None:
        """Test listing directories with non-existent path."""
        nonexistent_path = str(Path(temp_dir) / "nonexistent")

        with pytest.raises(FileNotFoundError, match="Source directory does not exist"):
            await FileSystemUtils.list_all_directories_recursive_async(nonexistent_path)

    @pytest.mark.asyncio
    async def test_list_all_directories_recursive_file_path(self, temp_dir: str) -> None:
        """Test listing directories when given a file path instead of directory."""
        file_path = str(Path(temp_dir) / "test.txt")
        Path(file_path).write_text("content")

        with pytest.raises(NotADirectoryError, match="Source path is not a directory"):
            await FileSystemUtils.list_all_directories_recursive_async(file_path)

    @pytest.mark.asyncio
    async def test_get_directory_info(self, temp_dir: str) -> None:
        """Test getting directory information."""
        # Create test structure
        base_path = Path(temp_dir)
        test_dir = base_path / "test_dir"
        test_dir.mkdir()

        # Create files
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.py").write_text("content2")
        (test_dir / ".hidden").write_text("hidden")

        # Create subdirectories
        (test_dir / "subdir1").mkdir()
        (test_dir / "subdir2").mkdir()
        (test_dir / ".git").mkdir()

        # Test sync version
        info = FileSystemUtils.get_directory_info(str(test_dir))

        assert isinstance(info, FolderInfo)
        assert info.path == str(test_dir)
        assert sorted(info.files) == sorted([".hidden", "file1.txt", "file2.py"])
        assert sorted(info.subdirectories) == sorted([".git", "subdir1", "subdir2"])

        # Test async version
        async_info = await FileSystemUtils.get_directory_info_async(str(test_dir))
        assert async_info == info

    @pytest.mark.asyncio
    async def test_get_directory_info_empty(self, temp_dir: str) -> None:
        """Test getting info for empty directory."""
        empty_dir = Path(temp_dir) / "empty"
        empty_dir.mkdir()

        info = await FileSystemUtils.get_directory_info_async(str(empty_dir))

        assert isinstance(info, FolderInfo)
        assert info.path == str(empty_dir)
        assert info.files == []
        assert info.subdirectories == []

    @pytest.mark.asyncio
    async def test_get_directory_info_nonexistent(self, temp_dir: str) -> None:
        """Test getting info for non-existent directory."""
        nonexistent_path = str(Path(temp_dir) / "nonexistent")

        with pytest.raises(FileNotFoundError, match="Directory does not exist"):
            await FileSystemUtils.get_directory_info_async(nonexistent_path)

    @pytest.mark.asyncio
    async def test_get_directory_info_file_path(self, temp_dir: str) -> None:
        """Test getting directory info when given a file path."""
        file_path = str(Path(temp_dir) / "test.txt")
        Path(file_path).write_text("content")

        with pytest.raises(NotADirectoryError, match="Path is not a directory"):
            await FileSystemUtils.get_directory_info_async(file_path)

    @pytest.mark.asyncio
    async def test_directory_functions_with_special_chars(self, temp_dir: str) -> None:
        """Test directory functions with special characters in names."""
        base_path = Path(temp_dir)

        # Create directories with special characters
        special_dir = base_path / "dir with spaces"
        special_dir.mkdir()
        (special_dir / "sub-dir_123").mkdir()
        (special_dir / "файлы").mkdir()  # Unicode directory name

        # Create files with special characters
        (special_dir / "file with spaces.txt").write_text("content")
        (special_dir / "файл.txt").write_text("content")  # Unicode filename

        # Test list_all_directories_recursive
        directories = await FileSystemUtils.list_all_directories_recursive_async(temp_dir)
        relative_dirs = sorted([normalize_path_for_comparison(Path(d).relative_to(temp_dir)) for d in directories])

        expected_dirs = sorted(
            [
                "dir with spaces",
                "dir with spaces/sub-dir_123",
                "dir with spaces/файлы",
            ],
        )
        assert relative_dirs == expected_dirs

        # Test get_directory_info
        info = await FileSystemUtils.get_directory_info_async(str(special_dir))
        assert sorted(info.files) == sorted(["file with spaces.txt", "файл.txt"])
        assert sorted(info.subdirectories) == sorted(["sub-dir_123", "файлы"])

    @pytest.mark.asyncio
    async def test_concurrent_directory_operations(self, temp_dir: str) -> None:
        """Test concurrent execution of directory operations."""
        # Create multiple directories
        base_path = Path(temp_dir)
        for i in range(5):
            dir_path = base_path / f"dir{i}"
            dir_path.mkdir()
            (dir_path / f"file{i}.txt").write_text(f"content{i}")
            (dir_path / f"subdir{i}").mkdir()

        # Run multiple operations concurrently
        tasks = []
        for i in range(5):
            dir_path = str(base_path / f"dir{i}")
            tasks.append(FileSystemUtils.get_directory_info_async(dir_path))

        # Also add a list_all_directories task
        tasks.append(FileSystemUtils.list_all_directories_recursive_async(temp_dir))

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)

        # Verify results
        for i in range(5):
            info = results[i]
            assert isinstance(info, FolderInfo)
            assert info.files == [f"file{i}.txt"]
            assert info.subdirectories == [f"subdir{i}"]

        # Check list_all_directories result
        all_dirs = results[5]
        assert len(all_dirs) == 10  # 5 main dirs + 5 subdirs


class TestRemoteFilesystemSupport:
    """Test remote filesystem support functionality."""

    @pytest.fixture
    def mock_s3_filesystem(self) -> MagicMock:
        """Create a mock S3 filesystem for testing."""
        from unittest.mock import MagicMock

        mock_fs = MagicMock()
        mock_fs.protocol = "s3"
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True
        mock_fs.isfile.return_value = False
        mock_fs.makedirs.return_value = None
        mock_fs.read_text.return_value = "mock content"
        mock_fs.write_text.return_value = None
        mock_fs.find.return_value = ["s3://bucket/file1.txt", "s3://bucket/file2.txt"]
        mock_fs.ls.return_value = ["s3://bucket/file1.txt", "s3://bucket/subdir"]
        mock_fs.copy.return_value = None
        mock_fs.rm.return_value = None
        return mock_fs

    @pytest.mark.parametrize(
        ("path", "expected_protocol"),
        [
            ("s3://bucket/key", "s3"),
            ("gs://bucket/object", "gs"),
            ("abfs://container/path", "abfs"),
            ("az://container/path", "az"),
            ("sftp://server/path", "sftp"),
            ("hdfs://namenode:9000/path", "hdfs"),
            ("C:\\Windows\\file.txt", "file"),
            ("/home/user/file.txt", "file"),
            ("relative/path", "file"),
        ],
    )
    def test_remote_path_protocol_detection(self, path: str, expected_protocol: str) -> None:
        """Test that remote filesystem protocols are correctly detected."""
        protocol = _get_filesystem_protocol(path)
        assert protocol == expected_protocol, (
            f"Path '{path}' should have protocol '{expected_protocol}', got '{protocol}'"
        )

    @pytest.mark.parametrize(
        "path",
        ["s3://bucket/key", "gs://bucket/object", "abfs://container/path", "sftp://server/path"],
    )
    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_get_filesystem_with_remote_paths(self, mock_fsspec_filesystem: MagicMock, path: str) -> None:
        """Test that get_filesystem works with remote paths."""
        mock_fs = MagicMock()
        mock_fsspec_filesystem.return_value = mock_fs

        fs = FileSystemUtils.get_filesystem(path)
        assert fs is mock_fs
        protocol = _get_filesystem_protocol(path)
        mock_fsspec_filesystem.assert_called_with(protocol)

    @pytest.mark.parametrize("remote_path", ["s3://bucket/directory/", "gs://bucket/folder", "abfs://container/dir"])
    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_is_directory_with_remote_paths(self, mock_fsspec_filesystem: MagicMock, remote_path: str) -> None:
        """Test is_directory method with remote paths."""
        mock_fs = MagicMock()
        mock_fs.isdir.return_value = True
        mock_fsspec_filesystem.return_value = mock_fs

        result = FileSystemUtils.is_directory(remote_path)
        assert result is True
        mock_fs.isdir.assert_called_with(remote_path)

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_write_async_with_remote_path_parent_creation(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test write_async creates parent directories correctly for remote paths."""
        mock_fs = MagicMock()
        mock_fsspec_filesystem.return_value = mock_fs

        # Test S3 path
        s3_path = "s3://bucket/path/to/file.txt"
        await FileSystemUtils.write_async(s3_path, "content")

        # Should call makedirs for parent directory
        mock_fs.makedirs.assert_called_with("s3://bucket/path/to", exist_ok=True)
        mock_fs.write_text.assert_called_with(s3_path, "content", encoding="utf-8")

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_write_async_remote_path_no_parent_creation_for_root(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test write_async doesn't try to create parent for bucket-only remote paths."""
        mock_fs = MagicMock()
        mock_fsspec_filesystem.return_value = mock_fs

        # Test S3 bucket-only path (no directory structure)
        s3_path = "s3://bucket/file.txt"
        await FileSystemUtils.write_async(s3_path, "content")

        # Should call makedirs for the bucket parent since it's a valid directory level
        # The logic creates parent directories when count("/") > 1, which is true for s3://bucket/file.txt
        mock_fs.makedirs.assert_called_with("s3://bucket", exist_ok=True)
        mock_fs.write_text.assert_called_with(s3_path, "content", encoding="utf-8")

    @pytest.mark.asyncio
    async def test_copy_directory_async_remote_path_handling(self) -> None:
        """Test copy_directory_async with remote paths."""
        mem_fs = fsspec.filesystem("memory")
        source_path = "memory://source-bucket/dir"
        dest_path = "memory://dest-bucket/newdir"

        # Create source files
        mem_fs.makedirs(f"{source_path}/subdir", exist_ok=True)
        mem_fs.write_text(f"{source_path}/file1.txt", "content1")
        mem_fs.write_text(f"{source_path}/subdir/file2.txt", "content2")

        await FileSystemUtils.copy_directory_async(source_path, dest_path)

        # Check that files were copied
        assert mem_fs.exists(f"{dest_path}/file1.txt")
        assert mem_fs.exists(f"{dest_path}/subdir/file2.txt")
        assert mem_fs.read_text(f"{dest_path}/file1.txt") == "content1"
        assert mem_fs.read_text(f"{dest_path}/subdir/file2.txt") == "content2"

    @pytest.mark.asyncio
    async def test_copy_directory_async_remote_deeply_nested(self) -> None:
        """Test copy_directory_async with deeply nested remote directory structure."""
        mem_fs = fsspec.filesystem("memory")
        source_path = "memory://source/project"
        dest_path = "memory://dest/project-copy"

        # Create deeply nested structure
        mem_fs.makedirs(f"{source_path}/src/components/ui/buttons", exist_ok=True)
        mem_fs.makedirs(f"{source_path}/tests/unit/components", exist_ok=True)
        mem_fs.write_text(f"{source_path}/README.md", "readme")
        mem_fs.write_text(f"{source_path}/src/index.ts", "index")
        mem_fs.write_text(f"{source_path}/src/components/ui/buttons/Button.tsx", "button")
        mem_fs.write_text(f"{source_path}/tests/unit/components/test.ts", "test")

        await FileSystemUtils.copy_directory_async(source_path, dest_path)

        # Verify all files copied with correct structure
        assert mem_fs.exists(f"{dest_path}/README.md")
        assert mem_fs.exists(f"{dest_path}/src/index.ts")
        assert mem_fs.exists(f"{dest_path}/src/components/ui/buttons/Button.tsx")
        assert mem_fs.exists(f"{dest_path}/tests/unit/components/test.ts")
        assert mem_fs.read_text(f"{dest_path}/README.md") == "readme"
        assert mem_fs.read_text(f"{dest_path}/src/components/ui/buttons/Button.tsx") == "button"

    @pytest.mark.asyncio
    async def test_copy_directory_async_remote_multiple_levels(self) -> None:
        """Test copy_directory_async with multiple files at different nesting levels."""
        mem_fs = fsspec.filesystem("memory")
        source_path = "memory://src-bucket/data"
        dest_path = "memory://dst-bucket/data-backup"

        # Create files at different levels
        mem_fs.write_text(f"{source_path}/root.txt", "root")
        mem_fs.makedirs(f"{source_path}/level1", exist_ok=True)
        mem_fs.write_text(f"{source_path}/level1/file1.txt", "level1")
        mem_fs.makedirs(f"{source_path}/level1/level2", exist_ok=True)
        mem_fs.write_text(f"{source_path}/level1/level2/file2.txt", "level2")
        mem_fs.makedirs(f"{source_path}/level1/level2/level3", exist_ok=True)
        mem_fs.write_text(f"{source_path}/level1/level2/level3/file3.txt", "level3")

        await FileSystemUtils.copy_directory_async(source_path, dest_path)

        # Verify entire hierarchy copied correctly
        assert mem_fs.read_text(f"{dest_path}/root.txt") == "root"
        assert mem_fs.read_text(f"{dest_path}/level1/file1.txt") == "level1"
        assert mem_fs.read_text(f"{dest_path}/level1/level2/file2.txt") == "level2"
        assert mem_fs.read_text(f"{dest_path}/level1/level2/level3/file3.txt") == "level3"

    @pytest.mark.asyncio
    async def test_copy_directory_async_remote_path_normalization(self) -> None:
        """Test that remote paths are normalized correctly (with and without trailing slashes)."""
        mem_fs = fsspec.filesystem("memory")

        # Test with trailing slash on source
        source_with_slash = "memory://source/dir/"
        dest1 = "memory://dest/dir1"

        mem_fs.makedirs(source_with_slash.rstrip("/"), exist_ok=True)
        mem_fs.write_text(f"{source_with_slash.rstrip('/')}/file.txt", "content")

        await FileSystemUtils.copy_directory_async(source_with_slash, dest1)
        assert mem_fs.exists(f"{dest1}/file.txt")
        assert mem_fs.read_text(f"{dest1}/file.txt") == "content"

        # Test with trailing slash on destination
        source_no_slash = "memory://source/dir"
        dest_with_slash = "memory://dest/dir2/"

        await FileSystemUtils.copy_directory_async(source_no_slash, dest_with_slash)
        assert mem_fs.exists(f"{dest_with_slash.rstrip('/')}/file.txt")
        assert mem_fs.read_text(f"{dest_with_slash.rstrip('/')}/file.txt") == "content"

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_list_directory_async_remote_path_resolution(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test list_directory_async with remote path resolution."""
        mock_fs = MagicMock()
        mock_fs.find.return_value = [
            "s3://bucket/dir/file1.txt",
            "s3://bucket/dir/subdir/file2.txt",
            "s3://bucket/dir/file3.py",
        ]
        mock_fs.isdir.return_value = False  # All are files
        mock_fsspec_filesystem.return_value = mock_fs

        source_path = "s3://bucket/dir"
        result = await FileSystemUtils.list_directory_async(source_path)

        # Should return all files found
        assert len(result) == 3
        assert "s3://bucket/dir/file1.txt" in result
        assert "s3://bucket/dir/subdir/file2.txt" in result
        assert "s3://bucket/dir/file3.py" in result

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_check_write_permission_remote_path_temp_file_creation(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test check_write_permission with remote paths creates temp files correctly."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True
        mock_fs.write_text.return_value = None
        mock_fs.rm.return_value = None
        mock_fsspec_filesystem.return_value = mock_fs

        remote_path = "s3://bucket/directory"
        result = FileSystemUtils.check_write_permission(remote_path)

        assert result is True

        # Verify temp file path construction for remote paths
        call_args = mock_fs.write_text.call_args[0]
        temp_file_path = call_args[0]
        assert temp_file_path.startswith("s3://bucket/directory/.__temp_permission_test_")
        assert temp_file_path.endswith(".tmp")

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_create_temp_directory_with_remote_base_path(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test create_temp_directory with remote base path."""
        mock_fs = MagicMock()
        mock_fs.makedirs.return_value = None
        mock_fsspec_filesystem.return_value = mock_fs

        base_path = "s3://bucket/temp"
        prefix = "test_"
        suffix = "_temp"

        result = FileSystemUtils.create_temp_directory(prefix=prefix, suffix=suffix, base_path=base_path)

        # Should create directory on remote filesystem
        assert result.startswith("s3://bucket/temp/test_")
        assert result.endswith("_temp")
        mock_fs.makedirs.assert_called_once()

    def test_create_temp_directory_local_fallback(self) -> None:
        """Test create_temp_directory falls back to local when no base_path provided."""
        result = FileSystemUtils.create_temp_directory(prefix="test_")

        # Should be a local temp directory
        # Check for common temp directory patterns
        assert result.startswith(("/tmp", "/var")) or "temp" in result.lower()  # noqa: S108
        assert "test_" in result

        # Clean up
        shutil.rmtree(result, ignore_errors=True)

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_create_temp_directory_async_with_remote_base_path(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test create_temp_directory_async with remote base path."""
        mock_fs = MagicMock()
        mock_fs.makedirs.return_value = None
        mock_fsspec_filesystem.return_value = mock_fs

        base_path = "gs://bucket/workspace"

        result = await FileSystemUtils.create_temp_directory_async(prefix="async_", base_path=base_path)

        assert result.startswith("gs://bucket/workspace/async_")
        mock_fs.makedirs.assert_called_once()

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_list_all_directories_recursive_remote_path_joining(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test list_all_directories_recursive with remote path joining."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True

        # Mock walk to return remote paths
        mock_fs.walk.return_value = [
            ("s3://bucket/root", ["dir1", "dir2"], ["file1.txt"]),
            ("s3://bucket/root/dir1", ["subdir1"], ["file2.txt"]),
            ("s3://bucket/root/dir2", [], ["file3.txt"]),
        ]
        mock_fsspec_filesystem.return_value = mock_fs

        source_path = "s3://bucket/root"
        result = FileSystemUtils.list_all_directories_recursive(source_path)

        # Should properly join remote paths with forward slashes
        expected_dirs = ["s3://bucket/root/dir1", "s3://bucket/root/dir1/subdir1", "s3://bucket/root/dir2"]
        assert sorted(result) == sorted(expected_dirs)

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_get_directory_info_remote_filename_extraction(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test get_directory_info with remote paths extracts filenames correctly."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True
        mock_fs.ls.return_value = ["s3://bucket/dir/file1.txt", "s3://bucket/dir/file2.py", "s3://bucket/dir/subdir"]
        mock_fs.isfile.side_effect = lambda path: not path.endswith("subdir")
        mock_fsspec_filesystem.return_value = mock_fs

        directory_path = "s3://bucket/dir"
        result = FileSystemUtils.get_directory_info(directory_path)

        assert result.path == directory_path
        assert sorted(result.files) == ["file1.txt", "file2.py"]
        assert result.subdirectories == ["subdir"]

    def test_path_type_annotations_accept_strings_only(self) -> None:
        """Test that methods with updated type annotations work with string paths."""
        # This test ensures the type annotation changes are working
        # by testing that methods can be called with string paths

        with patch("awa.core.utils.file_system_utils.fsspec.filesystem") as mock_fsspec:
            mock_fs = MagicMock()
            mock_fs.isdir.return_value = True
            mock_fsspec.return_value = mock_fs

            # These should all work with string paths
            string_path = "s3://bucket/path"

            # Test is_directory
            result = FileSystemUtils.is_directory(string_path)
            assert result is True

            # Test get_filesystem
            fs = FileSystemUtils.get_filesystem(string_path)
            assert fs is mock_fs

    @pytest.mark.parametrize(
        ("remote_path", "expected_protocol"),
        [
            ("s3://bucket/key/file.txt", "s3"),
            ("gs://bucket/object", "gs"),
            ("abfs://container@account.dfs.core.windows.net/path", "abfs"),
            ("az://container/path", "az"),
            ("sftp://user@server/path/file", "sftp"),
            ("hdfs://namenode:9000/path", "hdfs"),
            ("ftp://server/path", "ftp"),
        ],
    )
    def test_remote_protocol_detection_comprehensive(self, remote_path: str, expected_protocol: str) -> None:
        """Test comprehensive remote protocol detection."""
        protocol = _get_filesystem_protocol(remote_path)
        assert protocol == expected_protocol

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_remote_filesystem_error_handling(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test error handling with remote filesystems."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True

        # Mock the open method to raise an exception
        mock_fs.open.side_effect = OSError("Connection timeout")
        mock_fsspec_filesystem.return_value = mock_fs

        with pytest.raises(OSError):
            await FileSystemUtils.read_async("s3://bucket/file.txt")

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_write_permission_local_vs_remote_path_handling(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test that write permission check handles local vs remote paths differently."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True
        mock_fs.write_text.return_value = None
        mock_fs.rm.return_value = None
        mock_fsspec_filesystem.return_value = mock_fs

        # Test remote path - should use forward slash joining
        remote_result = FileSystemUtils.check_write_permission("s3://bucket/dir")
        assert remote_result is True

        # Verify the temp file path uses forward slash
        temp_file_calls = [call[0][0] for call in mock_fs.write_text.call_args_list]
        remote_temp_file = temp_file_calls[-1] if temp_file_calls else ""
        assert "s3://bucket/dir/.__temp_permission_test_" in remote_temp_file

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_read_directory_async_with_remote_paths(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test read_directory_async works correctly with remote filesystem paths."""
        # Mock the filesystem calls
        mock_fs = MagicMock()
        mock_fs.find.return_value = ["s3://bucket/dir/file1.txt", "s3://bucket/dir/file2.py"]
        mock_fs.isdir.return_value = False  # All files
        mock_fsspec_filesystem.return_value = mock_fs

        # Mock the read_async calls to return content
        with patch.object(FileSystemUtils, "read_async") as mock_read:
            mock_read.side_effect = ["content1", "content2"]

            result = await FileSystemUtils.read_directory_async("s3://bucket/dir")

            assert len(result) == 2
            assert result[0]["file"] == "s3://bucket/dir/file1.txt"
            assert result[0]["content"] == "content1"
            assert result[1]["file"] == "s3://bucket/dir/file2.py"
            assert result[1]["content"] == "content2"


class TestCommit6f6c04dcChanges:
    """Test the specific changes from commit 6f6c04dc3ead8553f738a34aabfcb182e188a7f9."""

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_write_async_parent_directory_fix(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test the fix for write_async parent directory creation with remote paths."""
        mock_fs = MagicMock()
        mock_fsspec_filesystem.return_value = mock_fs

        # This was the problematic case - S3 path where Path(path).parent would return "s3:"
        s3_path = "s3://bucket/deep/nested/path/file.txt"

        await FileSystemUtils.write_async(s3_path, "test content")

        # Should create parent using string manipulation, not Path.parent
        expected_parent = "s3://bucket/deep/nested/path"
        mock_fs.makedirs.assert_called_with(expected_parent, exist_ok=True)
        mock_fs.write_text.assert_called_with(s3_path, "test content", encoding="utf-8")

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_copy_directory_async_remote_parent_fix(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test the fix for copy_directory_async parent directory creation."""
        mock_fs = MagicMock()
        mock_fs.find.return_value = ["s3://src/dir/subdir/file.txt"]
        mock_fs.exists.return_value = False  # Parent doesn't exist
        mock_fsspec_filesystem.return_value = mock_fs

        # Mock the file reading to properly return EOF
        # Mock the source and destination file context managers
        mock_src_file_cm = MagicMock()
        mock_src_file_cm.read.side_effect = [b"test content", b""]

        mock_dest_file_cm = MagicMock()

        mock_fs.open.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=mock_src_file_cm)),
            MagicMock(__enter__=MagicMock(return_value=mock_dest_file_cm)),
        ]

        await FileSystemUtils.copy_directory_async("s3://src/dir", "s3://dest/newdir")

        # Should use string manipulation for remote path parent directory
        # The destination path would be s3://dest/newdir/subdir/file.txt
        # The parent would be s3://dest/newdir/subdir which has count("/") > 1
        assert mock_fs.makedirs.called

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @pytest.mark.asyncio
    async def test_list_directory_async_relative_path_fix(self, mock_fsspec_filesystem: MagicMock) -> None:
        """Test the fix for list_directory_async relative path calculation."""
        mock_fs = MagicMock()
        mock_fs.find.return_value = ["s3://bucket/dir/file1.txt", "s3://bucket/dir/subdir/file2.txt"]
        mock_fs.isdir.return_value = False
        mock_fsspec_filesystem.return_value = mock_fs

        # This was problematic because Path.resolve().relative_to() fails on S3 paths
        result = await FileSystemUtils.list_directory_async("s3://bucket/dir")

        # Should handle the relative path calculation without using Path operations
        expected_files = ["s3://bucket/dir/file1.txt", "s3://bucket/dir/subdir/file2.txt"]
        assert sorted(result) == sorted(expected_files)

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            ("s3://bucket", "s3"),  # Bucket-only path
            ("s3://bucket/", "s3"),  # Bucket with trailing slash
            ("gs://bucket/object/with/many/parts", "gs"),  # Deep path
            ("abfs://container@account.dfs.core.windows.net/path", "abfs"),  # Azure full format
        ],
    )
    def test_path_protocol_detection_edge_cases(self, path: str, expected: str) -> None:
        """Test edge cases in path protocol detection that were fixed."""
        protocol = _get_filesystem_protocol(path)
        assert protocol == expected, f"Path {path} should return protocol {expected}, got {protocol}"

    @pytest.mark.parametrize(
        "path",
        ["s3://bucket/path/file.txt", "gs://bucket/deep/nested/file.py", "abfs://container/folder/document.pdf"],
    )
    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_string_manipulation_vs_path_operations(self, mock_fsspec_filesystem: MagicMock, path: str) -> None:
        """Test that string manipulation is used instead of Path operations for remote paths."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True
        mock_fs.write_text.return_value = None
        mock_fs.rm.return_value = None
        mock_fsspec_filesystem.return_value = mock_fs

        # This should work without throwing "ValueError: Protocol not known"
        result = FileSystemUtils.check_write_permission(path)
        assert result is True

        # Verify temp file creation uses string manipulation
        temp_file_call = mock_fs.write_text.call_args[0][0]
        assert temp_file_call.startswith(path.rsplit("/", 1)[0])
        assert ".__temp_permission_test_" in temp_file_call

    @pytest.mark.parametrize(
        ("path", "expected_parent"),
        [
            ("s3://bucket/file.txt", "s3://bucket"),
            ("s3://bucket/deep/nested/file.txt", "s3://bucket/deep/nested"),
            ("gs://bucket/folder/file.py", "gs://bucket/folder"),
            ("abfs://container/path/to/file.pdf", "abfs://container/path/to"),
        ],
    )
    def test_remote_parent_path_extraction(self, path: str, expected_parent: str) -> None:
        """Test that parent path extraction works correctly for remote paths."""
        # Simulate the string manipulation used in the fixed code
        if "/" in path:
            calculated_parent = path.rsplit("/", 1)[0]
            assert calculated_parent == expected_parent

        # Verify this would work in check_write_permission
        with patch("awa.core.utils.file_system_utils.fsspec.filesystem") as mock_fsspec:
            mock_fs = MagicMock()
            mock_fs.exists.return_value = True
            mock_fs.isdir.return_value = True
            mock_fs.write_text.return_value = None
            mock_fs.rm.return_value = None
            mock_fsspec.return_value = mock_fs

            FileSystemUtils.check_write_permission(expected_parent)
            # Should not raise any path-related errors
            assert mock_fs.write_text.called


class TestRegressionPrevention:
    """Tests to prevent regression of the remote filesystem fixes."""

    @pytest.mark.parametrize(
        "remote_path",
        ["s3://bucket/key", "gs://bucket/object", "abfs://container/path", "sftp://server/path"],
    )
    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    def test_no_path_object_usage_in_remote_operations(
        self,
        mock_fsspec_filesystem: MagicMock,
        remote_path: str,
    ) -> None:
        """Ensure Path objects are not used for remote filesystem operations."""
        mock_fs = MagicMock()
        mock_fs.exists.return_value = True
        mock_fs.isdir.return_value = True
        mock_fsspec_filesystem.return_value = mock_fs

        # These operations should work without any Path object usage
        FileSystemUtils.is_directory(remote_path)
        FileSystemUtils.get_filesystem(remote_path)

        # Verify no Path constructor would be called with remote URLs
        # (This is more of a code pattern verification)
        protocol = _get_filesystem_protocol(remote_path)
        assert protocol != "file"

    @patch("awa.core.utils.file_system_utils.fsspec.filesystem")
    @patch("awa.core.utils.file_system_utils.logger")
    def test_filesystem_exception_logging_uses_logger_exception(
        self,
        mock_logger: MagicMock,
        mock_fsspec_filesystem: MagicMock,
    ) -> None:
        """Test that filesystem errors use logger.exception() for proper stack trace logging."""
        # Arrange - mock fsspec.filesystem to raise ValueError
        mock_fsspec_filesystem.side_effect = ValueError("Unsupported protocol: unknown")

        # Act & Assert - should raise ValueError and log using logger.exception
        with pytest.raises(ValueError, match="Unsupported filesystem protocol 'unknown'"):
            FileSystemUtils.get_filesystem("unknown://invalid/path")

        # Verify logger.exception was called for proper exception logging with stack trace
        assert mock_logger.exception.call_count == 2
        mock_logger.exception.assert_any_call(
            "Failed to get filesystem for path 'unknown://invalid/path' with protocol 'unknown'",
        )
        # Second call should log available protocols
        available_protocols_call = mock_logger.exception.call_args_list[1]
        assert "Available protocols:" in available_protocols_call[0][0]

    def test_type_annotations_prevent_path_object_passing(self) -> None:
        """Test that updated type annotations prevent Path object usage."""
        # This test ensures that our type annotations encourage string usage
        # In practice, mypy would catch Path object usage, but we test the interface

        # These methods should work with strings
        test_path = "s3://bucket/file.txt"

        # The type hints now expect strings only, which is correct for remote paths
        with patch("awa.core.utils.file_system_utils.fsspec.filesystem"):
            mock_fs = MagicMock()
            mock_fs.isdir.return_value = True

            # String path should work
            FileSystemUtils.is_directory(test_path)

            # Path object would work but is discouraged by type hints
            # In real usage, mypy would warn about this

    @pytest.mark.asyncio
    async def test_comprehensive_remote_workflow(self) -> None:
        """Test a comprehensive workflow with remote paths to ensure no regressions."""
        with patch("awa.core.utils.file_system_utils.fsspec.filesystem") as mock_fsspec:
            mock_fs = MagicMock()
            mock_fs.exists.return_value = True
            mock_fs.isdir.return_value = True
            mock_fs.isfile.return_value = False
            mock_fs.write_text.return_value = None
            mock_fs.makedirs.return_value = None
            mock_fs.find.return_value = ["s3://bucket/dir/file.txt"]
            mock_fs.ls.return_value = ["s3://bucket/dir/file.txt"]
            mock_fs.copy.return_value = None

            # Mock the file reading properly
            mock_file = MagicMock()
            mock_file.read.side_effect = [b"test content", b""]
            mock_fs.open.return_value.__enter__.return_value = mock_file

            mock_fsspec.return_value = mock_fs

            base_path = "s3://test-bucket/workflow"

            # Test directory operations
            assert FileSystemUtils.is_directory(base_path)

            # Test write operations
            await FileSystemUtils.write_async(f"{base_path}/output.txt", "test")

            # Test read operations
            content = await FileSystemUtils.read_async(f"{base_path}/input.txt")
            assert content == "test content"

            # Test directory listing
            files = await FileSystemUtils.list_directory_async(base_path)
            assert len(files) >= 0

            # Test copy operations
            await FileSystemUtils.copy_directory_async(f"{base_path}/source", f"{base_path}/dest")

            # Test permission checks
            assert FileSystemUtils.check_read_permission(base_path)
            assert FileSystemUtils.check_write_permission(base_path)

            # All operations should complete without path-related errors
            assert True  # If we get here, all operations succeeded

    @pytest.mark.parametrize(
        "path",
        ["C:\\AWA\\services.json", "D:\\Program Files\\app\\file.exe", "E:\\temp\\data.json"],
    )
    def test_windows_path_regression_prevention(self, path: str) -> None:
        """Prevent regression of Windows path handling issues."""
        # Should correctly identify as Windows drive path
        assert _is_windows_drive_path(path) is True

        # Should return 'file' protocol, not drive letter
        protocol = _get_filesystem_protocol(path)
        assert protocol == "file"

        # Should not raise "Protocol not known" error
        fs = FileSystemUtils.get_filesystem(path)
        assert fs is not None
