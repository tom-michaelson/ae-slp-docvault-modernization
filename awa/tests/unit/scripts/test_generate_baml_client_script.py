import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from awa.core.utils.baml_utils import (
    _copy_baml_files_to_global_directory,
    generate_baml_client,
    generate_baml_client_for_dir,
)


class TestGenerateBamlClient:
    """Test cases for generate_baml_client.py."""

    @patch("awa.core.utils.baml_utils.CommandUtils.run_command")
    @patch("pathlib.Path.exists")
    def test_generate_baml_client_for_dir_success(self, mock_exists: Mock, mock_run_command: Mock) -> None:
        """Test generate_baml_client_for_dir with successful execution."""
        # Arrange
        mock_run_command.return_value = (True, "success output")
        # Mock the __init__.py file to exist (successful generation)
        mock_exists.return_value = True

        # Act
        generate_baml_client_for_dir("/mock/baml/src")

        # Assert
        mock_run_command.assert_called_once_with(
            command="uv run baml-cli generate",
            working_dir="/mock/baml",
        )

    @patch("awa.core.utils.baml_utils.CommandUtils.run_command")
    def test_generate_baml_client_for_dir_failure(self, mock_run_command: Mock) -> None:
        """Test generate_baml_client_for_dir with command failure."""
        # Arrange
        mock_run_command.return_value = (False, "error output")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to generate BAML after 5 attempts: error output"):
            generate_baml_client_for_dir("/mock/baml/src")

    def test_copy_baml_files_no_baml_dirs(self) -> None:
        """Test _copy_baml_files_to_global_directory when no baml_src directories exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            global_awa_dir = Path(temp_dir)

            # Act
            _copy_baml_files_to_global_directory(global_awa_dir)

            # Assert
            global_baml_dir = global_awa_dir / "baml_src"
            assert global_baml_dir.exists()

    def test_copy_baml_files_with_dirs(self) -> None:
        """Test _copy_baml_files_to_global_directory with existing baml_src directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            global_awa_dir = Path(temp_dir)

            # Create a source baml_src directory with a file
            source_dir = global_awa_dir / "subproject" / "baml_src"
            source_dir.mkdir(parents=True)
            test_file = source_dir / "test.baml"
            test_file.write_text("test content")

            # Act
            _copy_baml_files_to_global_directory(global_awa_dir)

            # Assert
            copied_file = global_awa_dir / "baml_src" / "_copied" / "subproject" / "test.baml"
            assert copied_file.exists()
            assert copied_file.read_text() == "test content"

    @patch("awa.core.utils.baml_utils.generate_baml_client_for_dir")
    @patch("awa.core.utils.baml_utils._copy_baml_files_to_global_directory")
    def test_generate_baml_client_success(self, mock_copy: Mock, mock_generate: Mock) -> None:
        """Test successful generate_baml_client execution."""
        # Arrange
        mock_generate.return_value = None
        mock_copy.return_value = None

        # Act
        generate_baml_client()

        # Assert
        mock_copy.assert_called_once()
        mock_generate.assert_called_once()

    @patch("awa.core.utils.baml_utils.generate_baml_client_for_dir")
    @patch("awa.core.utils.baml_utils._copy_baml_files_to_global_directory")
    def test_generate_baml_client_generation_failure(self, mock_copy: Mock, mock_generate: Mock) -> None:
        """Test generate_baml_client when baml generation fails."""
        # Arrange
        mock_generate.side_effect = RuntimeError("Failed to generate BAML")
        mock_copy.return_value = None

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to generate BAML"):
            generate_baml_client()

    def test_copy_baml_files_creates_directory_structure(self) -> None:
        """Test that _copy_baml_files_to_global_directory creates proper directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            global_awa_dir = Path(temp_dir)

            # Create nested source structure
            source_dir = global_awa_dir / "deep" / "nested" / "project" / "baml_src"
            source_dir.mkdir(parents=True)

            # Create a file in a subdirectory
            sub_dir = source_dir / "subdir"
            sub_dir.mkdir()
            test_file = sub_dir / "nested.baml"
            test_file.write_text("nested content")

            # Act
            _copy_baml_files_to_global_directory(global_awa_dir)

            # Assert
            copied_file = (
                global_awa_dir / "baml_src" / "_copied" / "deep" / "nested" / "project" / "subdir" / "nested.baml"
            )
            assert copied_file.exists()
            assert copied_file.read_text() == "nested content"

    @patch("awa.core.utils.baml_utils.logger")
    def test_copy_baml_files_handles_invalid_relative_path(self, mock_logger: Mock) -> None:
        """Test that _copy_baml_files_to_global_directory handles invalid relative paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Arrange
            global_awa_dir = Path(temp_dir)

            # Create a baml_src directory outside the global_awa_dir
            outside_dir = Path(temp_dir).parent / "outside" / "baml_src"
            outside_dir.mkdir(parents=True, exist_ok=True)

            # Mock rglob to return the outside directory
            with patch.object(Path, "rglob") as mock_rglob:
                mock_rglob.return_value = [outside_dir]

                # Act
                _copy_baml_files_to_global_directory(global_awa_dir)

                # Assert - should log warning
                mock_logger.warning.assert_called()
                warning_calls = [
                    call
                    for call in mock_logger.warning.call_args_list
                    if "Could not determine relative path" in str(call)
                ]
                assert len(warning_calls) > 0
