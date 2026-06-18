from collections.abc import Callable
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.generate_baml_client import (
    _find_latest_timestamped_directory,
    _is_valid_timestamp,
    generate_baml_client_activity,
)


class TestTimestampHelpers:
    """Test the helper functions for timestamp validation and directory finding."""

    def test_is_valid_timestamp_valid_timestamps(self) -> None:
        """Test that valid timestamps are recognized correctly."""
        # Valid timestamps (17 characters, proper format)
        valid_timestamps = [
            "20240101123456789",
            "20231231235959999",
            "20230601000000000",
            "20240229120000000",  # Leap year
            "20240101000000000",  # Midnight
            "20240101120000500",  # 500 milliseconds
        ]

        for timestamp in valid_timestamps:
            assert _is_valid_timestamp(timestamp), f"Should be valid: {timestamp}"

    def test_is_valid_timestamp_invalid_timestamps(self) -> None:
        """Test that invalid timestamps are rejected correctly."""
        invalid_timestamps = [
            "2024010112345678",  # Too short (16 characters)
            "202401011234567890",  # Too long (18 characters)
            "20240101123456abc",  # Contains letters
            "20240132123456789",  # Invalid day (32)
            "20240001123456789",  # Invalid month (0)
            "20240100123456789",  # Invalid day (0)
            "20241301123456789",  # Invalid month (13)
            "20240101250000000",  # Invalid hour (25)
            "20240101236000000",  # Invalid minute (60)
            "20240101123560000",  # Invalid second (60)
            "2024010112345614a",  # Letter in milliseconds
            "2024010112345614@",  # Symbol in milliseconds
            "not_a_timestamp",
            "",
            "1234567890",
        ]

        for timestamp in invalid_timestamps:
            assert not _is_valid_timestamp(timestamp), f"Should be invalid: {timestamp}"

    def test_find_latest_timestamped_directory_no_directory(self) -> None:
        """Test that function returns None when base directory doesn't exist."""
        non_existent_path = Path("/non/existent/path")
        result = _find_latest_timestamped_directory(non_existent_path)
        assert result is None

    def test_find_latest_timestamped_directory_no_timestamped_dirs(self, tmp_path: Path) -> None:
        """Test that function returns None when no timestamped directories exist."""
        # Create some non-timestamped directories
        (tmp_path / "regular_dir").mkdir()
        (tmp_path / "another_dir").mkdir()
        (tmp_path / "not_timestamped").mkdir()

        result = _find_latest_timestamped_directory(tmp_path)
        assert result is None

    def test_find_latest_timestamped_directory_with_timestamped_dirs(self, tmp_path: Path) -> None:
        """Test that function returns the latest timestamped directory."""
        # Create timestamped directories with proper prefix
        older_dir = tmp_path / "awa_ts_20240101120000000"
        newer_dir = tmp_path / "awa_ts_20240101130000000"
        latest_dir = tmp_path / "awa_ts_20240101140000000"

        older_dir.mkdir()
        newer_dir.mkdir()
        latest_dir.mkdir()

        # Create some non-timestamped directories that should be ignored
        (tmp_path / "regular_dir").mkdir()
        (tmp_path / "awa_ts_invalid_timestamp").mkdir()

        result = _find_latest_timestamped_directory(tmp_path)
        assert result == latest_dir

    def test_find_latest_timestamped_directory_with_invalid_timestamps(self, tmp_path: Path) -> None:
        """Test that function ignores directories with invalid timestamps."""
        # Create a valid timestamped directory
        valid_dir = tmp_path / "awa_ts_20240101120000000"
        valid_dir.mkdir()

        # Create directories with invalid timestamps
        (tmp_path / "awa_ts_invalid_timestamp").mkdir()
        (tmp_path / "awa_ts_2024010112345678").mkdir()  # Too short
        (tmp_path / "awa_ts_202401011234567890").mkdir()  # Too long
        (tmp_path / "awa_ts_20240132123456789").mkdir()  # Invalid date

        result = _find_latest_timestamped_directory(tmp_path)
        assert result == valid_dir

    def test_find_latest_timestamped_directory_different_prefix(self, tmp_path: Path) -> None:
        """Test that function ignores directories with different prefix."""
        # Create directories with different prefixes
        (tmp_path / "ts_20240101120000000").mkdir()  # Wrong prefix
        (tmp_path / "other_prefix_20240101120000000").mkdir()  # Wrong prefix

        result = _find_latest_timestamped_directory(tmp_path)
        assert result is None


class TestGenerateBamlClientActivity:
    def _create_mock_path_chain(
        self,
        function_base_dir: MagicMock,
        project_root: MagicMock,
    ) -> Callable[[str], MagicMock]:
        """Create a mock path chain for testing."""

        def mock_path_chain(path_part: str) -> MagicMock:
            if path_part in {"awa", "baml_dynamic", "test_queue"}:
                return project_root
            if path_part == "test_function":
                return function_base_dir
            return project_root

        return mock_path_chain

    @pytest.mark.asyncio
    async def test_generate_baml_client_activity_success_new_content(self, activity_env: ActivityEnvironment) -> None:
        """Tests that the BAML client generation activity works correctly with new content."""
        # Arrange
        baml_function_name = "test_function"
        baml_content = "function test_function(input: string) -> string { ... }"
        workflow_task_queue = "test_queue"
        expected_baml_src_dir = (
            "/mock/project/awa/baml_dynamic/test_queue/test_function/awa_ts_20240101120000000/baml_src"
        )

        with (
            patch("awa.core.activities.generate_baml_client.Path") as mock_path_class,
            patch("awa.core.activities.generate_baml_client.LocalFileSystem") as mock_fs_class,
            patch("awa.core.activities.generate_baml_client.FileSystemUtils") as mock_file_utils,
            patch("awa.core.activities.generate_baml_client.CacheUtils") as mock_cache_utils,
            patch("awa.core.activities.generate_baml_client.generate_baml_client_for_dir") as mock_generate,
            patch("awa.core.activities.generate_baml_client.datetime") as mock_datetime,
            patch("awa.core.activities.generate_baml_client._find_latest_timestamped_directory") as mock_find_latest,
        ):
            # Mock datetime to return a predictable timestamp
            mock_now = MagicMock()
            mock_now.strftime.return_value = "20240101120000000"
            mock_datetime.now.return_value = mock_now

            # Mock that no existing timestamped directory exists
            mock_find_latest.return_value = None

            # Set up file system mocks
            mock_fs = MagicMock()
            mock_fs_class.return_value = mock_fs

            # Create mock baml_src_dir that returns correct string
            mock_baml_src_dir = MagicMock()
            mock_baml_src_dir.__str__.return_value = expected_baml_src_dir
            mock_baml_src_dir.mkdir = MagicMock()

            # Mock baml_client_dir (parent)
            mock_baml_client_dir = MagicMock()
            mock_baml_client_dir.exists.return_value = False
            mock_baml_src_dir.parent = mock_baml_client_dir

            # Mock the dynamic file path
            mock_dynamic_file_path = MagicMock()
            mock_baml_src_dir.__truediv__ = MagicMock(return_value=mock_dynamic_file_path)

            # Mock the Path class and ensure the chain returns the correct baml_src_dir
            mock_file = MagicMock()
            mock_project_root = MagicMock()
            mock_file.parent.parent.parent.parent = mock_project_root
            mock_path_class.return_value = mock_file

            # Mock the path chain for directory creation
            mock_function_base_dir = MagicMock()
            mock_timestamped_dir = MagicMock()
            mock_function_base_dir.__truediv__.return_value = mock_timestamped_dir
            mock_timestamped_dir.__truediv__.return_value = mock_baml_src_dir

            # Build the proper path chain
            mock_path_chain = self._create_mock_path_chain(mock_function_base_dir, mock_project_root)
            mock_project_root.__truediv__.side_effect = mock_path_chain

            # Mock cache utils
            mock_cache_utils.hash.return_value = "test_hash"

            # Mock file operations
            mock_file_utils.write = MagicMock()
            mock_file_utils.copy_directory_async = AsyncMock()

            # Act
            result = await activity_env.run(
                generate_baml_client_activity,
                baml_function_name,
                baml_content,
                workflow_task_queue,
            )

            # Assert
            assert result == expected_baml_src_dir
            mock_file_utils.write.assert_called_once()
            mock_file_utils.copy_directory_async.assert_called_once()
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_baml_client_activity_with_existing_content(self, activity_env: ActivityEnvironment) -> None:
        """Tests that the activity skips generation when content hasn't changed."""
        # Arrange
        baml_function_name = "test_function"
        baml_content = "function test_function(input: string) -> string { ... }"
        workflow_task_queue = "test_queue"
        expected_baml_src_dir = (
            "/mock/project/awa/baml_dynamic/test_queue/test_function/awa_ts_20240101120000000/baml_src"
        )

        with (
            patch("awa.core.activities.generate_baml_client.LocalFileSystem") as mock_fs_class,
            patch("awa.core.activities.generate_baml_client.FileSystemUtils") as mock_file_utils,
            patch("awa.core.activities.generate_baml_client.CacheUtils") as mock_cache_utils,
            patch("awa.core.activities.generate_baml_client.generate_baml_client_for_dir") as mock_generate,
            patch("awa.core.activities.generate_baml_client._find_latest_timestamped_directory") as mock_find_latest,
        ):
            # Mock that existing timestamped directory exists
            mock_latest_dir = MagicMock()
            mock_latest_baml_src_dir = MagicMock()
            mock_latest_baml_src_dir.__str__.return_value = expected_baml_src_dir
            mock_latest_dir.__truediv__.return_value = mock_latest_baml_src_dir
            mock_find_latest.return_value = mock_latest_dir

            # Mock that file exists with same content
            mock_existing_file = MagicMock()
            mock_existing_file.exists.return_value = True
            mock_latest_baml_src_dir.__truediv__.return_value = mock_existing_file

            # Mock baml_client_dir (parent) - exists since we have existing content
            mock_baml_client_dir = MagicMock()
            mock_baml_client_dir.exists.return_value = True
            mock_latest_baml_src_dir.parent = mock_baml_client_dir

            # Mock file system operations
            mock_fs = MagicMock()
            mock_fs_class.return_value = mock_fs

            # Mock that content is the same (same hash)
            mock_file_utils.read.return_value = baml_content
            mock_cache_utils.hash.return_value = "same_hash"

            # Act
            result = await activity_env.run(
                generate_baml_client_activity,
                baml_function_name,
                baml_content,
                workflow_task_queue,
            )

            # Assert
            assert result == expected_baml_src_dir
            # Should not write file or generate client when content is unchanged
            mock_file_utils.write.assert_not_called()
            mock_file_utils.copy_directory_async.assert_not_called()
            mock_generate.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_baml_client_activity_with_different_existing_content(
        self,
        activity_env: ActivityEnvironment,
    ) -> None:
        """Tests that the activity generates a new client when content has changed."""
        # Arrange
        baml_function_name = "test_function"
        baml_content = "function test_function(input: string) -> string { ... }"
        workflow_task_queue = "test_queue"
        expected_baml_src_dir = (
            "/mock/project/awa/baml_dynamic/test_queue/test_function/awa_ts_20240101130000000/baml_src"
        )

        with (
            patch("awa.core.activities.generate_baml_client.Path") as mock_path_class,
            patch("awa.core.activities.generate_baml_client.LocalFileSystem") as mock_fs_class,
            patch("awa.core.activities.generate_baml_client.FileSystemUtils") as mock_file_utils,
            patch("awa.core.activities.generate_baml_client.CacheUtils") as mock_cache_utils,
            patch("awa.core.activities.generate_baml_client.generate_baml_client_for_dir") as mock_generate,
            patch("awa.core.activities.generate_baml_client.datetime") as mock_datetime,
            patch("awa.core.activities.generate_baml_client._find_latest_timestamped_directory") as mock_find_latest,
        ):
            # Mock datetime to return a predictable timestamp
            mock_now = MagicMock()
            mock_now.strftime.return_value = "20240101130000000"
            mock_datetime.now.return_value = mock_now

            # Mock that existing timestamped directory exists
            mock_latest_dir = MagicMock()
            mock_latest_baml_src_dir = MagicMock()
            mock_latest_dir.__truediv__.return_value = mock_latest_baml_src_dir
            mock_find_latest.return_value = mock_latest_dir

            # Mock that file exists with different content
            mock_existing_file = MagicMock()
            mock_existing_file.exists.return_value = True
            mock_latest_baml_src_dir.__truediv__.return_value = mock_existing_file

            # Mock file system operations
            mock_fs = MagicMock()
            mock_fs_class.return_value = mock_fs

            # Mock that content is different (different hash)
            mock_file_utils.read.return_value = "different content"
            mock_cache_utils.hash.side_effect = lambda x: "old_hash" if x == "different content" else "new_hash"

            # Create mock for new baml_src_dir
            mock_new_baml_src_dir = MagicMock()
            mock_new_baml_src_dir.__str__.return_value = expected_baml_src_dir
            mock_new_baml_src_dir.mkdir = MagicMock()

            # Mock baml_client_dir (parent)
            mock_baml_client_dir = MagicMock()
            mock_baml_client_dir.exists.return_value = False
            mock_new_baml_src_dir.parent = mock_baml_client_dir

            # Mock the dynamic file path
            mock_dynamic_file_path = MagicMock()
            mock_new_baml_src_dir.__truediv__ = MagicMock(return_value=mock_dynamic_file_path)

            # Mock the Path class and ensure the chain returns the correct baml_src_dir
            mock_file = MagicMock()
            mock_project_root = MagicMock()
            mock_file.parent.parent.parent.parent = mock_project_root
            mock_path_class.return_value = mock_file

            # Mock the path chain for directory creation
            mock_function_base_dir = MagicMock()
            mock_timestamped_dir = MagicMock()
            mock_function_base_dir.__truediv__.return_value = mock_timestamped_dir
            mock_timestamped_dir.__truediv__.return_value = mock_new_baml_src_dir

            # Build the proper path chain
            mock_path_chain = self._create_mock_path_chain(mock_function_base_dir, mock_project_root)
            mock_project_root.__truediv__.side_effect = mock_path_chain

            # Mock file operations
            mock_file_utils.write = MagicMock()
            mock_file_utils.copy_directory_async = AsyncMock()

            # Act
            result = await activity_env.run(
                generate_baml_client_activity,
                baml_function_name,
                baml_content,
                workflow_task_queue,
            )

            # Assert
            assert result == expected_baml_src_dir
            mock_file_utils.write.assert_called_once()
            mock_file_utils.copy_directory_async.assert_called_once()
            mock_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_baml_client_activity_handles_exception(self, activity_env: ActivityEnvironment) -> None:
        """Tests that the activity properly handles exceptions during generation."""
        # Arrange
        baml_function_name = "test_function"
        baml_content = "function test_function(input: string) -> string { ... }"
        workflow_task_queue = "test_queue"

        with patch("awa.core.activities.generate_baml_client.generate_baml_client_for_dir") as mock_generate:
            mock_generate.side_effect = Exception("BAML generation failed")

            # Act & Assert
            with pytest.raises(Exception, match="BAML generation failed"):
                await activity_env.run(
                    generate_baml_client_activity,
                    baml_function_name,
                    baml_content,
                    workflow_task_queue,
                )

    @pytest.mark.asyncio
    async def test_generate_baml_client_activity_concurrent_access(self, activity_env: ActivityEnvironment) -> None:
        """Tests that the activity handles concurrent access properly with the lock."""
        # This test would require more complex async mocking to test the lock behavior
        # For now, we test that the activity can be called multiple times without issues

        baml_function_name = "test_function"
        baml_content = "function test_function(input: string) -> string { ... }"
        workflow_task_queue = "test_queue"

        with (
            patch("awa.core.activities.generate_baml_client._find_latest_timestamped_directory") as mock_find_latest,
            patch("awa.core.activities.generate_baml_client.datetime") as mock_datetime,
            patch("awa.core.activities.generate_baml_client.LocalFileSystem"),
            patch("awa.core.activities.generate_baml_client.FileSystemUtils") as mock_file_utils,
            patch("awa.core.activities.generate_baml_client.CacheUtils") as mock_cache_utils,
            patch("awa.core.activities.generate_baml_client.generate_baml_client_for_dir"),
            patch("awa.core.activities.generate_baml_client.Path") as mock_path_class,
        ):
            # Mock that no existing timestamped directory exists
            mock_find_latest.return_value = None

            # Mock datetime to return a predictable timestamp
            mock_now = MagicMock()
            mock_now.strftime.return_value = "20240101120000000"
            mock_datetime.now.return_value = mock_now

            # Mock cache utils
            mock_cache_utils.hash.return_value = "test_hash"

            # Mock file operations
            mock_file_utils.write = MagicMock()
            mock_file_utils.copy_directory_async = AsyncMock()

            # Mock the Path class to return proper chain
            mock_file = MagicMock()
            mock_project_root = MagicMock()
            mock_file.parent.parent.parent.parent = mock_project_root
            mock_path_class.return_value = mock_file

            # Mock the path chain for directory creation
            mock_function_base_dir = MagicMock()
            mock_timestamped_dir = MagicMock()
            mock_baml_src_dir = MagicMock()
            mock_baml_src_dir.__str__.return_value = "/mock/path"
            mock_function_base_dir.__truediv__.return_value = mock_timestamped_dir
            mock_timestamped_dir.__truediv__.return_value = mock_baml_src_dir

            # Build the proper path chain
            mock_path_chain = self._create_mock_path_chain(mock_function_base_dir, mock_project_root)
            mock_project_root.__truediv__.side_effect = mock_path_chain

            # Mock baml_client_dir (parent)
            mock_baml_client_dir = MagicMock()
            mock_baml_client_dir.exists.return_value = False
            mock_baml_src_dir.parent = mock_baml_client_dir

            # Call the activity multiple times - should not raise any exceptions
            for i in range(3):
                result = await activity_env.run(
                    generate_baml_client_activity,
                    f"{baml_function_name}_{i}",
                    baml_content,
                    workflow_task_queue,
                )
                assert result is not None
