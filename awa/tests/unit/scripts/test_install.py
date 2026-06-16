"""Unit tests for the installation script."""

# Import the installation script functions
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from install import (
    backup_existing_config,
    detect_existing_installation,
    get_global_config_dir,
    get_installed_awa_version,
    install_awa_wheel,
    run_command,
)


class TestInstallationScript:
    """Test cases for installation script functions."""

    @patch("install.run_command")
    def test_get_installed_awa_version_success(self, mock_run_command: MagicMock) -> None:
        """Test successful AWA version detection."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "AWA version 1.0.0\n"
        mock_run_command.return_value = mock_result

        version = get_installed_awa_version()
        assert version == "AWA version 1.0.0"
        mock_run_command.assert_called_once_with("awa --version", capture_output=True, check=False)

    @patch("install.run_command")
    def test_get_installed_awa_version_not_found(self, mock_run_command: MagicMock) -> None:
        """Test AWA version detection when not installed."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run_command.return_value = mock_result

        version = get_installed_awa_version()
        assert version is None

    @patch("install.run_command")
    def test_get_installed_awa_version_exception(self, mock_run_command: MagicMock) -> None:
        """Test AWA version detection with exception."""
        import subprocess

        mock_run_command.side_effect = subprocess.SubprocessError("Command failed")

        version = get_installed_awa_version()
        assert version is None

    @patch("install.get_global_config_dir")
    @patch("install.get_installed_awa_version")
    def test_detect_existing_installation_found(
        self,
        mock_get_version: MagicMock,
        mock_get_config_dir: MagicMock,
    ) -> None:
        """Test detection of existing installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            mock_get_config_dir.return_value = config_dir
            mock_get_version.return_value = "AWA version 1.0.0"

            # Create some config files
            (config_dir / "config.yaml").write_text("test: config")
            (config_dir / ".env").write_text("TEST=value")
            (config_dir / "services.json").write_text("{}")

            result = detect_existing_installation()

            assert result["awa_installed"] is True
            assert result["awa_version"] == "AWA version 1.0.0"
            assert result["config_exists"] is True
            assert len(result["config_files"]) == 3

    @patch("install.get_global_config_dir")
    @patch("install.get_installed_awa_version")
    def test_detect_existing_installation_not_found(
        self,
        mock_get_version: MagicMock,
        mock_get_config_dir: MagicMock,
    ) -> None:
        """Test detection when no existing installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "nonexistent"
            mock_get_config_dir.return_value = config_dir
            mock_get_version.return_value = None

            result = detect_existing_installation()

            assert result["awa_installed"] is False
            assert result["awa_version"] is None
            assert result["config_exists"] is False
            assert len(result["config_files"]) == 0

    @patch("install.get_global_config_dir")
    def test_backup_existing_config_success(self, mock_get_config_dir: MagicMock) -> None:
        """Test successful configuration backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            mock_get_config_dir.return_value = config_dir

            # Create config files
            config_file = config_dir / "config.yaml"
            env_file = config_dir / ".env"

            config_file.write_text("test: config")
            env_file.write_text("TEST=value")

            installation_info = {
                "config_exists": True,
                "config_files": [config_file, env_file],
            }

            with patch("install.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101_120000"

                result = backup_existing_config(installation_info)

                assert result is True

                # Check that backup directory was created
                backup_dir = config_dir / "backup_20240101_120000"
                assert backup_dir.exists()
                assert (backup_dir / "config.yaml").exists()
                assert (backup_dir / ".env").exists()

                # Check backup contents
                assert (backup_dir / "config.yaml").read_text() == "test: config"
                assert (backup_dir / ".env").read_text() == "TEST=value"

    def test_backup_existing_config_no_config(self) -> None:
        """Test backup when no config exists."""
        installation_info = {
            "config_exists": False,
            "config_files": [],
        }

        result = backup_existing_config(installation_info)
        assert result is True

    def test_backup_existing_config_failure(self) -> None:
        """Test backup failure handling."""
        installation_info = {
            "config_exists": True,
            "config_files": [Path("/nonexistent/config.yaml")],
        }

        # Patch Path.home to return a writable path, then mock mkdir to raise exception
        with (
            patch("install.Path.home", return_value=Path("/tmp/test_home")),  # noqa: S108
            patch("pathlib.Path.mkdir", side_effect=OSError("Permission denied")),
        ):
            result = backup_existing_config(installation_info)
            assert result is False

    @patch("install.run_command")
    @patch("install.Path")
    def test_install_awa_wheel_success(
        self,
        mock_path: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        """Test successful wheel installation."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__str__ = lambda _: "test-wheel.whl"
        mock_path.return_value = mock_path_instance

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_command.return_value = mock_result

        result = install_awa_wheel("test-wheel.whl", upgrade=False)

        assert result is True
        mock_run_command.assert_called_once_with(
            "uv pip install --system 'test-wheel.whl'",
            capture_output=False,
            check=True,
        )

    @patch("install.run_command")
    @patch("install.Path")
    def test_install_awa_wheel_upgrade(
        self,
        mock_path: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        """Test wheel upgrade installation."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__str__ = lambda _: "test-wheel.whl"
        mock_path.return_value = mock_path_instance

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run_command.return_value = mock_result

        result = install_awa_wheel("test-wheel.whl", upgrade=True)

        assert result is True
        mock_run_command.assert_called_once_with(
            "uv pip install --system --upgrade 'test-wheel.whl'",
            capture_output=False,
            check=True,
        )

    @patch("install.Path")
    def test_install_awa_wheel_missing_file(self, mock_path: MagicMock) -> None:
        """Test wheel installation with missing file."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = False
        mock_path.return_value = mock_path_instance

        result = install_awa_wheel("nonexistent-wheel.whl")

        assert result is False

    @patch("install.run_command")
    @patch("install.Path")
    def test_install_awa_wheel_failure(
        self,
        mock_path: MagicMock,
        mock_run_command: MagicMock,
    ) -> None:
        """Test wheel installation failure."""
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.__str__ = lambda _: "test-wheel.whl"
        mock_path.return_value = mock_path_instance

        mock_run_command.return_value = None  # Simulate failure

        result = install_awa_wheel("test-wheel.whl")

        assert result is False

    def test_install_awa_wheel_no_path(self) -> None:
        """Test wheel installation with no path provided."""
        result = install_awa_wheel(None)
        assert result is False

    @patch("install.subprocess.run")
    def test_run_command_success(self, mock_subprocess_run: MagicMock) -> None:
        """Test successful command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_subprocess_run.return_value = mock_result

        result = run_command("echo test")

        assert result == mock_result
        mock_subprocess_run.assert_called_once()

    @patch("install.subprocess.run")
    def test_run_command_failure(self, mock_subprocess_run: MagicMock) -> None:
        """Test command execution failure."""
        from subprocess import CalledProcessError

        mock_subprocess_run.side_effect = CalledProcessError(1, "echo test", stderr="error")

        result = run_command("echo test")

        assert result is None

    @patch("install.subprocess.run")
    def test_run_command_failure_no_check(self, mock_subprocess_run: MagicMock) -> None:
        """Test command execution failure with check=False."""
        from subprocess import CalledProcessError

        error = CalledProcessError(1, "echo test", stderr="error")
        mock_subprocess_run.side_effect = error

        result = run_command("echo test", check=False)

        assert result == error

    @patch("install.Path.home")
    def test_get_global_config_dir(self, mock_home: MagicMock) -> None:
        """Test global config directory path."""
        mock_home.return_value = Path("/home/user")

        # Mock the mkdir method to avoid permission errors
        with patch("pathlib.Path.mkdir") as mock_mkdir:
            result = get_global_config_dir()

            assert result == Path("/home/user/.awa")
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestUpgradeScenarios:
    """Test cases for upgrade scenarios."""

    @patch("install.get_global_config_dir")
    @patch("install.get_installed_awa_version")
    def test_upgrade_with_existing_config(
        self,
        mock_get_version: MagicMock,
        mock_get_config_dir: MagicMock,
    ) -> None:
        """Test upgrade scenario with existing configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            mock_get_config_dir.return_value = config_dir
            mock_get_version.return_value = "AWA version 1.0.0"

            # Create existing config
            (config_dir / "config.yaml").write_text("existing: config")
            (config_dir / ".env").write_text("EXISTING=value")

            # Detect installation
            installation_info = detect_existing_installation()

            # Backup config
            with patch("install.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
                backup_result = backup_existing_config(installation_info)

            assert backup_result is True
            assert installation_info["awa_installed"] is True
            assert installation_info["config_exists"] is True

            # Verify backup was created
            backup_dir = config_dir / "backup_20240101_120000"
            assert backup_dir.exists()
            assert (backup_dir / "config.yaml").read_text() == "existing: config"
            assert (backup_dir / ".env").read_text() == "EXISTING=value"

    @patch("install.get_global_config_dir")
    @patch("install.get_installed_awa_version")
    def test_fresh_installation_no_backup(
        self,
        mock_get_version: MagicMock,
        mock_get_config_dir: MagicMock,
    ) -> None:
        """Test fresh installation doesn't create backup."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "nonexistent"
            mock_get_config_dir.return_value = config_dir
            mock_get_version.return_value = None

            installation_info = detect_existing_installation()
            backup_result = backup_existing_config(installation_info)

            assert backup_result is True
            assert installation_info["awa_installed"] is False
            assert installation_info["config_exists"] is False

            # No backup should be created
            assert not config_dir.exists()

    @patch("install.get_global_config_dir")
    @patch("install.get_installed_awa_version")
    def test_upgrade_partial_config(
        self,
        mock_get_version: MagicMock,
        mock_get_config_dir: MagicMock,
    ) -> None:
        """Test upgrade with only some config files present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir)
            mock_get_config_dir.return_value = config_dir
            mock_get_version.return_value = "AWA version 1.0.0"

            # Create only config.yaml, not .env
            (config_dir / "config.yaml").write_text("partial: config")

            installation_info = detect_existing_installation()

            assert installation_info["awa_installed"] is True
            assert installation_info["config_exists"] is True
            assert len(installation_info["config_files"]) == 1

            # Backup should still work with partial config
            with patch("install.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
                backup_result = backup_existing_config(installation_info)

            assert backup_result is True
            backup_dir = config_dir / "backup_20240101_120000"
            assert backup_dir.exists()
            assert (backup_dir / "config.yaml").exists()
            assert not (backup_dir / ".env").exists()  # Should not exist
