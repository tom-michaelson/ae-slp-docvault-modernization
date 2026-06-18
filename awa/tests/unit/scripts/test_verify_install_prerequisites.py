from unittest.mock import Mock, patch

from scripts.verify_install_prerequisites import (
    Colors,
    Dependency,
    _check_dependency,
    _compare_versions,
    _get_dependencies,
    _parse_version,
)


class TestVerifyInstallPrerequisites:
    """Test cases for verify_install_prerequisites.py."""

    def test_dependency_dataclass(self) -> None:
        """Test Dependency dataclass creation."""
        dep = Dependency(
            name="test",
            min_version="1.0.0",
            commands=["test"],
            version_args=["--version"],
            version_regex=r"(\d+\.\d+\.\d+)",
            description="Test dependency",
        )
        assert dep.name == "test"
        assert dep.min_version == "1.0.0"
        assert dep.commands == ["test"]

    def test_colors_class(self) -> None:
        """Test Colors class methods."""
        # Test color methods
        assert Colors.green("test") == f"{Colors.GREEN}test{Colors.RESET}"
        assert Colors.red("test") == f"{Colors.RED}test{Colors.RESET}"
        assert Colors.yellow("test") == f"{Colors.YELLOW}test{Colors.RESET}"
        assert Colors.blue("test") == f"{Colors.BLUE}test{Colors.RESET}"
        assert Colors.bold("test") == f"{Colors.BOLD}test{Colors.RESET}"

    def test_parse_version_success(self) -> None:
        """Test _parse_version with successful extraction."""
        # Test various version formats
        assert _parse_version("Python 3.12.0", r"Python (\d+\.\d+\.\d+)") == "3.12.0"
        assert _parse_version("v22.16.0", r"v(\d+\.\d+\.\d+)") == "22.16.0"
        assert _parse_version("uv 0.7.12", r"uv (\d+\.\d+\.\d+)") == "0.7.12"
        assert _parse_version("10.6.2", r"(\d+\.\d+\.\d+)") == "10.6.2"

    def test_parse_version_failure(self) -> None:
        """Test _parse_version with no match."""
        assert _parse_version("No version here", r"(\d+\.\d+\.\d+)") is None
        assert _parse_version("", r"(\d+\.\d+\.\d+)") is None

    def test_compare_versions(self) -> None:
        """Test _compare_versions function."""
        # Test exact matches
        assert _compare_versions("1.0.0", "1.0.0") is True

        # Test newer versions
        assert _compare_versions("1.1.0", "1.0.0") is True
        assert _compare_versions("2.0.0", "1.9.9") is True
        assert _compare_versions("1.0.1", "1.0.0") is True

        # Test older versions
        assert _compare_versions("1.0.0", "1.1.0") is False
        assert _compare_versions("1.9.9", "2.0.0") is False
        assert _compare_versions("1.0.0", "1.0.1") is False

    def test_compare_versions_with_suffixes(self) -> None:
        """Test _compare_versions with version suffixes."""
        assert _compare_versions("1.0.0-alpha", "1.0.0") is True
        assert _compare_versions("1.0.0-beta.1", "1.0.0") is True

    def test_compare_versions_invalid(self) -> None:
        """Test _compare_versions with invalid versions."""
        # Should return True for unparseable versions
        assert _compare_versions("invalid", "1.0.0") is True
        assert _compare_versions("1.0.0", "invalid") is True

    @patch("scripts.verify_install_prerequisites.subprocess.run")
    def test_check_dependency_success(self, mock_subprocess_run: Mock) -> None:
        """Test _check_dependency with successful dependency check."""
        # Arrange
        dep = Dependency(
            name="Python",
            min_version="3.12.0",
            commands=["python"],
            version_args=["--version"],
            version_regex=r"Python (\d+\.\d+\.\d+)",
            description="Python interpreter",
        )
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.12.1"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        # Act
        success, message, version = _check_dependency(dep)

        # Assert
        assert success is True
        assert "Python 3.12.1" in message
        assert version == "3.12.1"

    @patch("scripts.verify_install_prerequisites.subprocess.run")
    def test_check_dependency_version_too_old(self, mock_subprocess_run: Mock) -> None:
        """Test _check_dependency with version too old."""
        # Arrange
        dep = Dependency(
            name="Python",
            min_version="3.12.0",
            commands=["python"],
            version_args=["--version"],
            version_regex=r"Python (\d+\.\d+\.\d+)",
            description="Python interpreter",
        )
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.11.0"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        # Act
        success, message, version = _check_dependency(dep)

        # Assert
        assert success is False
        assert "requires >=" in message
        assert version == "3.11.0"

    @patch("scripts.verify_install_prerequisites.subprocess.run")
    def test_check_dependency_command_not_found(self, mock_subprocess_run: Mock) -> None:
        """Test _check_dependency when command is not found."""
        # Arrange
        dep = Dependency(
            name="NonExistent",
            min_version="1.0.0",
            commands=["nonexistent"],
            version_args=["--version"],
            version_regex=r"(\d+\.\d+\.\d+)",
            description="Non-existent tool",
        )
        mock_subprocess_run.side_effect = FileNotFoundError()

        # Act
        success, message, version = _check_dependency(dep)

        # Assert
        assert success is False
        assert "not found" in message
        assert version is None

    @patch("scripts.verify_install_prerequisites.platform.system")
    def test_get_dependencies_windows(self, mock_system: Mock) -> None:
        """Test _get_dependencies on Windows."""
        # Arrange
        mock_system.return_value = "Windows"

        # Act
        dependencies = _get_dependencies()

        # Assert
        assert len(dependencies) > 0
        python_dep = next((d for d in dependencies if d.name == "Python"), None)
        assert python_dep is not None
        assert "python" in python_dep.commands
        assert "py" in python_dep.commands

    @patch("scripts.verify_install_prerequisites.platform.system")
    def test_get_dependencies_unix(self, mock_system: Mock) -> None:
        """Test _get_dependencies on Unix-like systems."""
        # Arrange
        mock_system.return_value = "Linux"

        # Act
        dependencies = _get_dependencies()

        # Assert
        assert len(dependencies) > 0
        python_dep = next((d for d in dependencies if d.name == "Python"), None)
        assert python_dep is not None
        assert "python3" in python_dep.commands
