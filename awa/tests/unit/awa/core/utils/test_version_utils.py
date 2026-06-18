"""Tests for version utilities."""

import tempfile
import tomllib
from pathlib import Path
from unittest import mock

import pytest

from awa.core.utils.version_utils import get_project_version


class TestGetProjectVersion:
    """Test get_project_version function."""

    def test_get_project_version_success(self) -> None:
        """Test successful version reading from pyproject.toml."""
        # Read the actual version from pyproject.toml to compare against
        project_root = Path(__file__).resolve().parents[5]  # Navigate to project root
        pyproject_path = project_root / "pyproject.toml"

        with pyproject_path.open("rb") as f:
            pyproject_data = tomllib.load(f)
        expected_version = pyproject_data["project"]["version"]

        # Call the function which should find the real pyproject.toml
        version = get_project_version()

        # Verify we get the same version as what's actually in the file
        assert isinstance(version, str)
        assert version == expected_version
        # Verify it looks like a valid version string (basic format check)
        assert len(version.split(".")) >= 2  # At least major.minor

    def test_get_project_version_no_pyproject_file(self) -> None:
        """Test error when pyproject.toml doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Mock __file__ to point to a directory without pyproject.toml
            with mock.patch("awa.core.utils.version_utils.Path") as mock_path:
                # Create a mock path that walks up but never finds pyproject.toml
                mock_file_path = mock.MagicMock()
                mock_file_path.resolve.return_value = temp_path / "fake_file.py"
                mock_file_path.parents = [temp_path, temp_path.parent]
                mock_path.return_value = mock_file_path

                # Mock the existence check to always return False
                with (
                    mock.patch.object(Path, "exists", return_value=False),
                    pytest.raises(FileNotFoundError, match=r"Could not find pyproject.toml"),
                ):
                    get_project_version()

    def test_get_project_version_no_project_section(self) -> None:
        """Test error when pyproject.toml has no [project] section."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pyproject_path = temp_path / "pyproject.toml"

            # Create a pyproject.toml without [project] section
            pyproject_path.write_text('[build-system]\nrequires = ["setuptools"]\n', encoding="utf-8")

            # Mock __file__ to point to this temp directory
            with mock.patch("awa.core.utils.version_utils.Path") as mock_path:
                mock_file_path = mock.MagicMock()
                mock_file_path.resolve.return_value = temp_path / "fake_file.py"
                mock_file_path.parents = [temp_path]
                mock_path.return_value = mock_file_path

                with pytest.raises(KeyError, match="No \\[project\\] section found"):
                    get_project_version()

    def test_get_project_version_no_version_field(self) -> None:
        """Test error when [project] section has no version field."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pyproject_path = temp_path / "pyproject.toml"

            # Create a pyproject.toml with [project] but no version
            pyproject_path.write_text('[project]\nname = "test-package"\n', encoding="utf-8")

            # Mock __file__ to point to this temp directory
            with mock.patch("awa.core.utils.version_utils.Path") as mock_path:
                mock_file_path = mock.MagicMock()
                mock_file_path.resolve.return_value = temp_path / "fake_file.py"
                mock_file_path.parents = [temp_path]
                mock_path.return_value = mock_file_path

                with pytest.raises(KeyError, match="No version found in \\[project\\] section"):
                    get_project_version()

    def test_get_project_version_valid_toml(self) -> None:
        """Test successful version reading from a valid pyproject.toml."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pyproject_path = temp_path / "pyproject.toml"

            # Create a valid pyproject.toml
            pyproject_path.write_text(
                '[project]\nname = "test-package"\nversion = "2.3.4"\n',
                encoding="utf-8",
            )

            # Mock __file__ to point to this temp directory
            with mock.patch("awa.core.utils.version_utils.Path") as mock_path:
                mock_file_path = mock.MagicMock()
                mock_file_path.resolve.return_value = temp_path / "fake_file.py"
                mock_file_path.parents = [temp_path]
                mock_path.return_value = mock_file_path

                version = get_project_version()
                assert version == "2.3.4"

    def test_get_project_version_invalid_toml(self) -> None:
        """Test error when pyproject.toml has invalid TOML syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            pyproject_path = temp_path / "pyproject.toml"

            # Create an invalid pyproject.toml
            pyproject_path.write_text("invalid toml content [", encoding="utf-8")

            # Mock __file__ to point to this temp directory
            with mock.patch("awa.core.utils.version_utils.Path") as mock_path:
                mock_file_path = mock.MagicMock()
                mock_file_path.resolve.return_value = temp_path / "fake_file.py"
                mock_file_path.parents = [temp_path]
                mock_path.return_value = mock_file_path

                with pytest.raises(tomllib.TOMLDecodeError):
                    get_project_version()
