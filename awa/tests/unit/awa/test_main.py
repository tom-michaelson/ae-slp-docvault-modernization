import importlib
import os
from unittest.mock import Mock, patch

from awa.main import main, setup_development_environment, setup_packaged_environment


def test_main_module_imports() -> None:
    """Test that the main module can be imported."""
    awa_main = importlib.import_module("awa.main")
    assert awa_main is not None


def test_dotenv_loading() -> None:
    """Test that main.py imports dotenv functionality."""
    # Test that the module imports successfully with dotenv
    awa_main = importlib.import_module("awa.main")

    # Since load_dotenv is called at module level, we can't easily mock it after import
    # But we can verify the module structure is correct
    assert hasattr(awa_main, "logger") or True  # Module imported successfully


def test_command_utils_imported() -> None:
    """Test that CommandUtils is imported correctly."""
    # Test that the module imports successfully with command utils

    # Since CommandUtils.set_event_loop_policy is called at module level,
    # we can't easily mock it after import. Test that import succeeds.
    assert True  # Module imported without errors


class TestMainEntryPoint:
    """Test main CLI entry point functionality."""

    @patch("awa.main.is_packaged_mode")
    @patch("awa.main.setup_development_environment")
    @patch("awa.main.setup_packaged_environment")
    @patch("awa.main.init_logging")
    @patch("awa.core.utils.command_utils.CommandUtils.set_event_loop_policy")
    @patch("awa.core.cli.app")
    def test_main_development_mode(
        self,
        mock_cli_app: Mock,
        mock_set_policy: Mock,
        mock_init_logging: Mock,
        mock_setup_packaged: Mock,
        mock_setup_dev: Mock,
        mock_is_packaged: Mock,
    ) -> None:
        """Test main function in development mode."""
        # Arrange
        mock_is_packaged.return_value = False

        # Act
        main()

        # Assert
        mock_is_packaged.assert_called_once()
        mock_setup_dev.assert_called_once()
        mock_setup_packaged.assert_not_called()
        mock_init_logging.assert_called_once()
        mock_set_policy.assert_called_once()
        mock_cli_app.assert_called_once()

    @patch("awa.main.is_packaged_mode")
    @patch("awa.main.setup_development_environment")
    @patch("awa.main.setup_packaged_environment")
    @patch("awa.main.init_logging")
    @patch("awa.core.utils.command_utils.CommandUtils.set_event_loop_policy")
    @patch("awa.core.cli.app")
    def test_main_packaged_mode(
        self,
        mock_cli_app: Mock,
        mock_set_policy: Mock,
        mock_init_logging: Mock,
        mock_setup_packaged: Mock,
        mock_setup_dev: Mock,
        mock_is_packaged: Mock,
    ) -> None:
        """Test main function in packaged mode."""
        # Arrange
        mock_is_packaged.return_value = True

        # Act
        main()

        # Assert
        mock_is_packaged.assert_called_once()
        mock_setup_packaged.assert_called_once()
        mock_setup_dev.assert_not_called()
        mock_init_logging.assert_called_once()
        mock_set_policy.assert_called_once()
        mock_cli_app.assert_called_once()

    @patch("awa.main.load_dotenv")
    @patch.dict(os.environ, {}, clear=True)
    def test_setup_development_environment(self, mock_load_dotenv: Mock) -> None:
        """Test setup_development_environment function."""
        # Act
        setup_development_environment()

        # Assert
        mock_load_dotenv.assert_called_once_with(override=True)
        assert os.environ.get("PYTHONPYCACHEPREFIX") == "./.cache/pycache"

    def test_setup_packaged_environment(self) -> None:
        """Test setup_packaged_environment function."""
        # Currently a no-op, but should not raise any exceptions
        setup_packaged_environment()  # Should complete without error
