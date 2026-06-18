from pathlib import Path
from unittest.mock import patch

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.file_io import (
    copy_directory_activity,
    copy_file_activity,
    get_directory_info,
    is_directory_activity,
    list_all_directories_recursive,
    list_directory_activity,
    read_directory_activity,
    read_file_activity,
    read_file_bytes_activity,
    read_file_or_directory_activity,
    remove_directory_activity,
    write_file_activity,
)
from awa.sdk.models.folder_info import FolderInfo
from awa.sdk.models.input_params import InputParams
from tests.utils.platform_test_utils import normalize_line_endings, normalize_path_for_comparison


class TestFileIOActivities:
    @pytest.mark.asyncio
    async def test_write_and_read_file_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that writing and then reading a file works correctly."""
        # Arrange
        file_path = tmp_path / "test_file.txt"
        content = "hello world"

        # Act
        await activity_env.run(write_file_activity, str(file_path), content)
        result = await activity_env.run(read_file_activity, str(file_path))

        # Assert
        assert result == content
        assert file_path.exists()

    @pytest.mark.asyncio
    async def test_write_file_overwrites_content(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that the write_file activity overwrites existing content."""
        # Arrange
        file_path = tmp_path / "overwrite_test.txt"
        initial_content = "initial content"
        new_content = "new content"

        file_path.write_text(initial_content)

        # Act
        await activity_env.run(write_file_activity, str(file_path), new_content)
        result = await activity_env.run(read_file_activity, str(file_path))

        # Assert
        assert result == new_content

    @pytest.mark.asyncio
    async def test_copy_directory_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that a directory is copied correctly."""
        # Arrange
        source_path = tmp_path / "source_dir"
        dest_path = tmp_path / "dest_dir"
        file1_content = b"file 1"
        file2_content = b"file 2"

        source_path.mkdir()
        (source_path / "file1.txt").write_bytes(file1_content)
        (source_path / "subdir").mkdir()
        (source_path / "subdir" / "file2.txt").write_bytes(file2_content)

        # Act
        result = await activity_env.run(copy_directory_activity, str(source_path), str(dest_path))

        # Assert
        assert (dest_path / "file1.txt").exists()
        assert (dest_path / "subdir" / "file2.txt").exists()
        assert (dest_path / "file1.txt").read_bytes() == file1_content
        assert (dest_path / "subdir" / "file2.txt").read_bytes() == file2_content

        # Verify the returned list contains the copied files
        expected_files = {
            str(dest_path / "file1.txt"),
            str(dest_path / "subdir" / "file2.txt"),
        }
        assert isinstance(result, list)
        assert set(result) == expected_files

    @pytest.mark.asyncio
    async def test_copy_directory_with_ignore_file(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that a directory is copied correctly while ignoring specified files."""
        # Arrange
        source_path = tmp_path / "source_dir_ignore"
        dest_path = tmp_path / "dest_dir_ignore"
        ignore_file_path = tmp_path / "ignore.txt"
        file1_content = b"file 1"
        ignored_file_content = b"ignored file"
        ignored_dir_file_content = b"another ignored file"

        source_path.mkdir()
        (source_path / "file1.txt").write_bytes(file1_content)
        (source_path / "ignored_file.txt").write_bytes(ignored_file_content)
        (source_path / "ignored_dir").mkdir()
        (source_path / "ignored_dir" / "another_ignored_file.txt").write_bytes(ignored_dir_file_content)
        ignore_file_path.write_bytes(b"ignored_file.txt\nignored_dir/\n")

        # Act
        result = await activity_env.run(
            copy_directory_activity,
            str(source_path),
            str(dest_path),
            str(ignore_file_path),
        )

        # Assert
        assert (dest_path / "file1.txt").exists()
        assert not (dest_path / "ignored_file.txt").exists()
        assert not (dest_path / "ignored_dir").exists()
        assert (dest_path / "file1.txt").read_bytes() == file1_content

        # Verify the returned list contains only the copied files (not ignored files)
        assert isinstance(result, list)
        assert result == [str(dest_path / "file1.txt")]

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.parse_gitignore_str", None)
    async def test_copy_directory_no_parser(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that copy proceeds without ignoring files if gitignore-parser is not installed."""
        # Arrange
        source_path = tmp_path / "source_dir_no_parser"
        dest_path = tmp_path / "dest_dir_no_parser"
        ignore_file_path = tmp_path / "ignore.txt"
        file1_content = b"file 1"

        source_path.mkdir()
        (source_path / "file1.txt").write_bytes(file1_content)
        ignore_file_path.write_bytes(b"file1.txt")

        # Act & Assert
        with pytest.warns(
            UserWarning,
            match="gitignore-parser is not installed",
        ):
            result = await activity_env.run(
                copy_directory_activity,
                str(source_path),
                str(dest_path),
                str(ignore_file_path),
            )

        assert (dest_path / "file1.txt").exists()

        # Verify the returned list contains the copied files (ignore file should be ignored in warning case)
        assert isinstance(result, list)
        assert result == [str(dest_path / "file1.txt")]

    @pytest.mark.asyncio
    async def test_list_directory_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that a directory is listed correctly."""
        # Arrange
        source_path = tmp_path / "source_dir"
        file1_content = b"file 1"
        file2_content = b"file 2"
        file3_content = b"file 3"

        source_path.mkdir()
        (source_path / "file1.txt").write_bytes(file1_content)
        (source_path / "file2.txt").write_bytes(file2_content)
        (source_path / "subdir").mkdir()
        (source_path / "subdir" / "file3.txt").write_bytes(file3_content)

        # Act
        result = await activity_env.run(list_directory_activity, str(source_path))

        # Assert
        expected_files = {
            str(source_path / "file1.txt"),
            str(source_path / "file2.txt"),
            str(source_path / "subdir" / "file3.txt"),
        }
        assert set(result) == expected_files

    @pytest.mark.asyncio
    async def test_list_directory_with_ignore_file(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that a directory is listed correctly while ignoring specified files."""
        # Arrange
        source_path = tmp_path / "source_dir_ignore"
        ignore_file_path = tmp_path / "ignore.txt"
        file1_content = b"file 1"
        ignored_file_content = b"ignored file"
        ignored_dir_file_content = b"another ignored file"

        source_path.mkdir()
        (source_path / "file1.txt").write_bytes(file1_content)
        (source_path / "ignored_file.txt").write_bytes(ignored_file_content)
        (source_path / "ignored_dir").mkdir()
        (source_path / "ignored_dir" / "another_ignored_file.txt").write_bytes(ignored_dir_file_content)
        ignore_file_path.write_bytes(b"ignored_file.txt\nignored_dir/\n")

        # Act
        result = await activity_env.run(
            list_directory_activity,
            str(source_path),
            str(ignore_file_path),
        )

        # Assert
        assert result == [str(source_path / "file1.txt")]

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.parse_gitignore_str", None)
    async def test_list_directory_no_parser(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that list proceeds without ignoring files if gitignore-parser is not installed."""
        # Arrange
        source_path = tmp_path / "source_dir_no_parser"
        ignore_file_path = tmp_path / "ignore.txt"
        file1_content = b"file 1"
        file2_content = b"file 2"

        source_path.mkdir()
        (source_path / "file1.txt").write_bytes(file1_content)
        (source_path / "file2.txt").write_bytes(file2_content)
        ignore_file_path.write_bytes(b"file1.txt")

        # Act & Assert
        with pytest.warns(
            UserWarning,
            match="gitignore-parser is not installed",
        ):
            result = await activity_env.run(
                list_directory_activity,
                str(source_path),
                str(ignore_file_path),
            )

        expected_files = {
            str(source_path / "file1.txt"),
            str(source_path / "file2.txt"),
        }
        assert set(result) == expected_files


class TestReadFileOrDirectoryActivity:
    """Test cases for read_file_or_directory_activity function."""

    @pytest.mark.asyncio
    async def test_read_single_file_basic(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a single file with basic parameters."""
        # Arrange
        file_path = tmp_path / "single_file.txt"
        file_content = "Hello, World!"
        file_path.write_text(file_content)

        input_params = InputParams(
            path=str(file_path),
            name="test_file",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert result == file_content

    @pytest.mark.asyncio
    async def test_read_single_file_with_default_when_exists(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a single file with default value when file exists (should ignore default)."""
        # Arrange
        file_path = tmp_path / "existing_file.txt"
        file_content = "Actual content"
        default_content = "Default content"
        file_path.write_text(file_content)

        input_params = InputParams(
            path=str(file_path),
            name="test_file",
            default=default_content,
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert result == file_content

    @pytest.mark.asyncio
    async def test_read_single_file_with_default_when_not_exists(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a single file with default value when file doesn't exist."""
        # Arrange
        file_path = tmp_path / "nonexistent_file.txt"
        default_content = "Default content"

        input_params = InputParams(
            path=str(file_path),
            name="test_file",
            default=default_content,
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert result == default_content

    @pytest.mark.asyncio
    async def test_read_directory_basic_default_template(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with default join string and template."""
        # Arrange
        dir_path = tmp_path / "test_dir"
        dir_path.mkdir()
        file1_content = "Content of file 1"
        file2_content = "Content of file 2"

        (dir_path / "file1.txt").write_text(file1_content)
        (dir_path / "file2.txt").write_text(file2_content)

        input_params = InputParams(
            path=str(dir_path),
            name="test_directory",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert - normalize paths for cross-platform comparison
        expected_file1 = f'<file name="{normalize_path_for_comparison(dir_path)}/file1.txt">\n{file1_content}\n</file>'
        expected_file2 = f'<file name="{normalize_path_for_comparison(dir_path)}/file2.txt">\n{file2_content}\n</file>'
        normalized_result = normalize_path_for_comparison(result)

        # The result should contain both files joined with newline
        assert expected_file1 in normalized_result
        assert expected_file2 in normalized_result
        # Check that files are joined with default join string ("\n")
        assert "\n" in result
        # Verify both file contents are present
        assert file1_content in result
        assert file2_content in result

    @pytest.mark.asyncio
    async def test_read_directory_custom_join_string(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with custom join string."""
        # Arrange
        dir_path = tmp_path / "test_dir_custom_join"
        dir_path.mkdir()
        file1_content = "Content 1"
        file2_content = "Content 2"

        (dir_path / "file1.txt").write_text(file1_content)
        (dir_path / "file2.txt").write_text(file2_content)

        input_params = InputParams(
            path=str(dir_path),
            name="test_directory",
            directory_join_str="---SEPARATOR---",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert "---SEPARATOR---" in result
        # Should contain both files with custom separator
        parts = result.split("---SEPARATOR---")
        assert len(parts) == 2
        assert file1_content in result
        assert file2_content in result

    @pytest.mark.asyncio
    async def test_read_directory_custom_template_string(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with custom template string."""
        # Arrange
        dir_path = tmp_path / "test_dir_custom_template"
        dir_path.mkdir()
        file1_content = "Template test content"

        (dir_path / "file1.txt").write_text(file1_content)

        input_params = InputParams(
            path=str(dir_path),
            name="test_directory",
            directory_join_template_str="FILE: {file} | CONTENT: {content}",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert - normalize paths for cross-platform comparison
        expected_result = f"FILE: {normalize_path_for_comparison(dir_path)}/file1.txt | CONTENT: {file1_content}"
        normalized_result = normalize_path_for_comparison(result)
        assert normalized_result == expected_result

    @pytest.mark.asyncio
    async def test_read_directory_custom_join_and_template(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with both custom join string and template."""
        # Arrange
        dir_path = tmp_path / "test_dir_custom_both"
        dir_path.mkdir()
        file1_content = "Content A"
        file2_content = "Content B"

        (dir_path / "file1.txt").write_text(file1_content)
        (dir_path / "file2.txt").write_text(file2_content)

        input_params = InputParams(
            path=str(dir_path),
            name="test_directory",
            directory_join_str=" || ",
            directory_join_template_str="[{file}]: {content}",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert - normalize paths for cross-platform comparison
        expected_file1 = f"[{normalize_path_for_comparison(dir_path)}/file1.txt]: {file1_content}"
        expected_file2 = f"[{normalize_path_for_comparison(dir_path)}/file2.txt]: {file2_content}"
        normalized_result = normalize_path_for_comparison(result)

        assert " || " in result
        assert expected_file1 in normalized_result
        assert expected_file2 in normalized_result

    @pytest.mark.asyncio
    async def test_read_directory_with_ignore_file(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with ignore file patterns."""
        # Arrange
        dir_path = tmp_path / "test_dir_ignore"
        dir_path.mkdir()
        ignore_file_path = tmp_path / "test_ignore.txt"
        file1_content = "Keep this file"
        file2_content = "Ignore this file"

        (dir_path / "keep.txt").write_text(file1_content)
        (dir_path / "ignore.txt").write_text(file2_content)
        ignore_file_path.write_text("ignore.txt")

        input_params = InputParams(
            path=str(dir_path),
            name="test_directory",
            ignore_file_path=str(ignore_file_path),
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert file1_content in result
        assert file2_content not in result
        assert "keep.txt" in result
        assert "ignore.txt" not in result

    @pytest.mark.asyncio
    async def test_read_directory_nested_structure(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with nested folder structure."""
        # Arrange
        dir_path = tmp_path / "test_dir_nested"
        dir_path.mkdir()
        file1_content = "Root file"
        file2_content = "Nested file"
        file3_content = "Deep nested file"

        (dir_path / "root.txt").write_text(file1_content)
        (dir_path / "subdir").mkdir(parents=True)
        (dir_path / "subdir" / "nested.txt").write_text(file2_content)
        (dir_path / "subdir" / "deep").mkdir(parents=True)
        (dir_path / "subdir" / "deep" / "deep.txt").write_text(file3_content)

        input_params = InputParams(
            path=str(dir_path),
            name="test_directory",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert file1_content in result
        assert file2_content in result
        assert file3_content in result
        assert "root.txt" in result
        assert "nested.txt" in result
        assert "deep.txt" in result

    @pytest.mark.asyncio
    async def test_read_empty_directory(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading an empty directory."""
        # Arrange
        dir_path = tmp_path / "empty_dir"
        dir_path.mkdir()

        input_params = InputParams(
            path=str(dir_path),
            name="empty_directory",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert result == ""

    @pytest.mark.asyncio
    async def test_read_directory_single_file(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading a directory with only one file."""
        # Arrange
        dir_path = tmp_path / "single_file_dir"
        dir_path.mkdir()
        file_content = "Only file content"

        (dir_path / "only.txt").write_text(file_content)

        input_params = InputParams(
            path=str(dir_path),
            name="single_file_directory",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert - normalize paths for cross-platform comparison
        expected_result = f'<file name="{normalize_path_for_comparison(dir_path)}/only.txt">\n{file_content}\n</file>'
        normalized_result = normalize_path_for_comparison(result)
        assert normalized_result == expected_result

    @pytest.mark.asyncio
    async def test_input_params_all_fields(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test that all InputParams fields are handled correctly."""
        # Arrange
        file_path = tmp_path / "test_all_fields.txt"
        file_content = "Test content"
        file_path.write_text(file_content)

        input_params = InputParams(
            path=str(file_path),
            name="comprehensive_test",
            ignore_file_path="/some/ignore/file",  # Should be ignored for files
            default="Should be ignored",  # Should be ignored when file exists
            directory_join_str="Should be ignored",  # Should be ignored for files
            directory_join_template_str="Should be ignored",  # Should be ignored for files
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert
        assert result == file_content

    @pytest.mark.asyncio
    async def test_directory_with_special_characters_in_content(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading directory with files containing special characters."""
        # Arrange
        dir_path = tmp_path / "special_chars_dir"
        dir_path.mkdir()
        file1_content = "Content with\nnewlines\nand\ttabs"
        file2_content = "Content with 'quotes' and \"double quotes\""

        (dir_path / "file1.txt").write_text(file1_content)
        (dir_path / "file2.txt").write_text(file2_content)

        input_params = InputParams(
            path=str(dir_path),
            name="special_chars_directory",
        )

        # Act
        result = await activity_env.run(read_file_or_directory_activity, input_params)

        # Assert - normalize line endings for cross-platform comparison
        normalized_result = normalize_line_endings(result)
        normalized_file1_content = normalize_line_endings(file1_content)
        normalized_file2_content = normalize_line_endings(file2_content)

        assert normalized_file1_content in normalized_result
        assert normalized_file2_content in normalized_result
        assert "newlines" in result
        assert "tabs" in result
        assert "'quotes'" in result
        assert '"double quotes"' in result


class TestDirectoryListingActivities:
    """Test the new directory listing activities."""

    @pytest.mark.asyncio
    async def test_list_all_directories_recursive_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test listing all directories recursively."""
        # Arrange
        base_dir = tmp_path / "test_recursive"
        base_dir.mkdir()

        # Create nested directory structure
        (base_dir / "dir1").mkdir()
        (base_dir / "dir1" / "subdir1").mkdir()
        (base_dir / "dir1" / "subdir2").mkdir()
        (base_dir / "dir2").mkdir()
        (base_dir / "dir2" / "subdir3").mkdir()
        (base_dir / "dir2" / "subdir3" / "deepdir").mkdir()

        # Create some files (should not be included)
        (base_dir / "file1.txt").write_text("content1")
        (base_dir / "dir1" / "file2.txt").write_text("content2")

        # Act
        result = await activity_env.run(list_all_directories_recursive, str(base_dir))

        # Assert
        assert len(result) == 6  # All subdirectories
        # Convert to relative paths for easier assertion
        relative_dirs = sorted([str(Path(d).relative_to(base_dir)) for d in result])
        expected_dirs = sorted(
            [
                "dir1",
                str(Path("dir1") / "subdir1"),
                str(Path("dir1") / "subdir2"),
                "dir2",
                str(Path("dir2") / "subdir3"),
                str(Path("dir2") / "subdir3" / "deepdir"),
            ],
        )
        assert relative_dirs == expected_dirs

    @pytest.mark.asyncio
    async def test_list_all_directories_recursive_empty_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test listing directories in an empty directory."""
        # Arrange
        empty_dir = tmp_path / "empty_dir"
        empty_dir.mkdir()

        # Act
        result = await activity_env.run(list_all_directories_recursive, str(empty_dir))

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_get_directory_info_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test getting directory information."""
        # Arrange
        test_dir = tmp_path / "info_test_dir"
        test_dir.mkdir()

        # Create files
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.py").write_text("content2")
        (test_dir / ".hidden").write_text("hidden")

        # Create subdirectories
        (test_dir / "subdir1").mkdir()
        (test_dir / "subdir2").mkdir()
        (test_dir / ".git").mkdir()

        # Act
        result = await activity_env.run(get_directory_info, str(test_dir))

        # Assert
        assert isinstance(result, FolderInfo)
        assert result.path == str(test_dir)
        assert sorted(result.files) == sorted([".hidden", "file1.txt", "file2.py"])
        assert sorted(result.subdirectories) == sorted([".git", "subdir1", "subdir2"])

    @pytest.mark.asyncio
    async def test_get_directory_info_empty_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test getting info for an empty directory."""
        # Arrange
        empty_dir = tmp_path / "empty_info_dir"
        empty_dir.mkdir()

        # Act
        result = await activity_env.run(get_directory_info, str(empty_dir))

        # Assert
        assert isinstance(result, FolderInfo)
        assert result.path == str(empty_dir)
        assert result.files == []
        assert result.subdirectories == []

    @pytest.mark.asyncio
    async def test_directory_activities_with_special_chars(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test directory activities with special characters in names."""
        # Arrange
        base_dir = tmp_path / "special_chars_test"
        base_dir.mkdir()
        special_dir = base_dir / "dir with spaces"
        special_dir.mkdir()
        (special_dir / "sub-dir_123").mkdir()

        # Create files with special characters
        (special_dir / "file with spaces.txt").write_text("content")
        (special_dir / "file_123.txt").write_text("content")

        # Act - test list_all_directories_recursive
        all_dirs = await activity_env.run(list_all_directories_recursive, str(base_dir))

        # Assert
        relative_dirs = sorted([str(Path(d).relative_to(base_dir)) for d in all_dirs])
        assert "dir with spaces" in relative_dirs
        assert str(Path("dir with spaces") / "sub-dir_123") in relative_dirs

        # Act - test get_directory_info
        info = await activity_env.run(get_directory_info, str(special_dir))

        # Assert
        assert sorted(info.files) == sorted(["file with spaces.txt", "file_123.txt"])
        assert info.subdirectories == ["sub-dir_123"]


class TestNewFileIOActivities:
    """Test cases for the new file I/O activities."""

    @pytest.mark.asyncio
    async def test_is_directory_activity_true(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test is_directory_activity returns True for directories."""
        # Arrange
        dir_path = tmp_path / "test_directory"
        dir_path.mkdir()

        # Act
        result = await activity_env.run(is_directory_activity, str(dir_path))

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_is_directory_activity_false_for_file(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test is_directory_activity returns False for files."""
        # Arrange
        file_path = tmp_path / "test_file.txt"
        file_path.write_bytes(b"content")

        # Act
        result = await activity_env.run(is_directory_activity, str(file_path))

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_is_directory_activity_false_for_nonexistent(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        """Test is_directory_activity returns False for nonexistent paths."""
        # Arrange
        nonexistent_path = "/nonexistent_path"

        # Act
        result = await activity_env.run(is_directory_activity, nonexistent_path)

        # Assert
        assert result is False

    @pytest.mark.asyncio
    async def test_read_file_bytes_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading file as bytes."""
        # Arrange
        file_path = tmp_path / "binary_file.bin"
        binary_content = b"\x00\x01\x02\x03\xff"
        file_path.write_bytes(binary_content)

        # Act
        result = await activity_env.run(read_file_bytes_activity, str(file_path))

        # Assert
        assert result == binary_content

    @pytest.mark.asyncio
    async def test_read_file_bytes_activity_with_default(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        """Test reading file as bytes with default value when file doesn't exist."""
        # Arrange
        nonexistent_path = "/nonexistent.bin"
        default_content = b"default content"

        # Act
        result = await activity_env.run(read_file_bytes_activity, nonexistent_path, default_content)

        # Assert
        assert result == default_content

    @pytest.mark.asyncio
    async def test_read_file_bytes_activity_no_default(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        """Test reading nonexistent file as bytes without default raises FileNotFoundError."""
        # Arrange
        nonexistent_path = "/nonexistent.bin"

        # Act & Assert
        with pytest.raises(FileNotFoundError, match="File not found"):
            await activity_env.run(read_file_bytes_activity, nonexistent_path)

    @pytest.mark.asyncio
    async def test_read_directory_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading directory and returning structured data."""
        # Arrange
        dir_path = tmp_path / "test_read_dir"
        dir_path.mkdir()
        file1_content = "content 1"
        file2_content = "content 2"

        (dir_path / "file1.txt").write_text(file1_content)
        (dir_path / "subdir").mkdir()
        (dir_path / "subdir" / "file2.txt").write_text(file2_content)

        # Act
        results = await activity_env.run(read_directory_activity, str(dir_path))

        # Assert
        assert isinstance(results, list)
        assert len(results) == 2

        # Sort results by file path for consistent assertion
        results = sorted(results, key=lambda x: x["file"])

        # Normalize paths for cross-platform comparison
        expected_file1_path = f"{normalize_path_for_comparison(dir_path)}/file1.txt"
        expected_file2_path = f"{normalize_path_for_comparison(dir_path)}/subdir/file2.txt"
        actual_file1_path = normalize_path_for_comparison(results[0]["file"])
        actual_file2_path = normalize_path_for_comparison(results[1]["file"])

        assert actual_file1_path == expected_file1_path
        assert results[0]["content"] == file1_content
        assert actual_file2_path == expected_file2_path
        assert results[1]["content"] == file2_content

    @pytest.mark.asyncio
    async def test_read_directory_activity_empty(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test reading empty directory returns empty list."""
        # Arrange
        dir_path = tmp_path / "empty_read_dir"
        dir_path.mkdir()

        # Act
        result = await activity_env.run(read_directory_activity, str(dir_path))

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_remove_directory_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test removing directory recursively."""
        # Arrange
        dir_path = tmp_path / "remove_test_dir"
        dir_path.mkdir()
        (dir_path / "file1.txt").write_bytes(b"content1")
        (dir_path / "subdir").mkdir()
        (dir_path / "subdir" / "file2.txt").write_bytes(b"content2")

        # Verify directory exists before removal
        assert dir_path.exists()
        assert (dir_path / "file1.txt").exists()
        assert (dir_path / "subdir" / "file2.txt").exists()

        # Act
        await activity_env.run(remove_directory_activity, str(dir_path))

        # Assert
        assert not dir_path.exists()
        assert not (dir_path / "file1.txt").exists()
        assert not (dir_path / "subdir" / "file2.txt").exists()

    @pytest.mark.asyncio
    async def test_remove_directory_activity_nonexistent(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        """Test removing nonexistent directory doesn't raise error."""
        # Arrange
        nonexistent_path = "/nonexistent_dir"

        # Act & Assert (should not raise)
        await activity_env.run(remove_directory_activity, nonexistent_path)

    @pytest.mark.asyncio
    async def test_copy_file_activity(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test copying individual file."""
        # Arrange
        source_path = tmp_path / "source_file.txt"
        dest_path = tmp_path / "dest_file.txt"
        file_content = "file content to copy"

        source_path.write_text(file_content)

        # Act
        await activity_env.run(copy_file_activity, str(source_path), str(dest_path))

        # Assert
        assert dest_path.exists()
        assert dest_path.read_text() == file_content
        # Verify source still exists
        assert source_path.exists()

    @pytest.mark.asyncio
    async def test_copy_file_activity_overwrite(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test copying file overwrites destination."""
        # Arrange
        source_path = tmp_path / "source_overwrite.txt"
        dest_path = tmp_path / "dest_overwrite.txt"
        source_content = "new content"
        existing_content = "old content"

        source_path.write_text(source_content)
        dest_path.write_text(existing_content)

        # Act
        await activity_env.run(copy_file_activity, str(source_path), str(dest_path))

        # Assert
        assert dest_path.read_text() == source_content

    @pytest.mark.asyncio
    async def test_copy_file_activity_with_directory_creation(
        self,
        activity_env: ActivityEnvironment,
        tmp_path: Path,
    ) -> None:
        """Test copying file creates destination directory if needed."""
        # Arrange
        source_path = tmp_path / "source_create_dir.txt"
        dest_path = tmp_path / "new_dir" / "dest_create_dir.txt"
        file_content = "content with dir creation"

        source_path.write_text(file_content)

        # Act
        await activity_env.run(copy_file_activity, str(source_path), str(dest_path))

        # Assert
        assert dest_path.exists()
        assert dest_path.read_text() == file_content
