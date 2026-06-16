"""Unit tests for the api CLI command."""

from unittest.mock import MagicMock, patch

import pytest
import typer.testing

from awa.core.cli.commands.api import app


@pytest.fixture
def cli_runner() -> typer.testing.CliRunner:
    """Provide a CLI runner for testing."""
    return typer.testing.CliRunner()


@pytest.fixture
def mock_logger() -> MagicMock:
    """Provide a mock logger."""
    return MagicMock()


@pytest.fixture
def mock_api() -> MagicMock:
    """Provide a mock API instance."""
    return MagicMock()


class TestApiCommand:
    """Test cases for api CLI command."""

    @patch("awa.core.cli.commands.api.Api")
    @patch("awa.core.cli.commands.api.init_logging")
    @patch("awa.core.cli.commands.api.get_logger")
    def test_api_command_basic(
        self,
        mock_get_logger: MagicMock,
        mock_init_logging: MagicMock,
        mock_api_class: MagicMock,
        cli_runner: typer.testing.CliRunner,
        mock_logger: MagicMock,
        mock_api: MagicMock,
    ) -> None:
        """Test api command with no parameters."""
        # Arrange
        mock_get_logger.return_value = mock_logger
        mock_init_logging.return_value = None
        mock_api.run_docker = MagicMock()
        mock_api_class.return_value = mock_api

        # Act
        result = cli_runner.invoke(app, [])

        # Assert
        assert result.exit_code == 0
        mock_init_logging.assert_called_once()
        mock_get_logger.assert_called_once()
        mock_api_class.assert_called_once()
        mock_api.run_docker.assert_called_once()
        mock_logger.info.assert_called_once_with("Starting AWA API server for debugging...")

    def test_api_command_help(self, cli_runner: typer.testing.CliRunner) -> None:
        """Test the api command help output."""
        result = cli_runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Start the AWA API server directly" in result.stdout
        assert "useful for debugging" in result.stdout

    @patch("awa.core.cli.commands.api.Api")
    @patch("awa.core.cli.commands.api.init_logging")
    @patch("awa.core.cli.commands.api.get_logger")
    def test_api_command_keyboard_interrupt(
        self,
        mock_get_logger: MagicMock,
        mock_init_logging: MagicMock,
        mock_api_class: MagicMock,
        cli_runner: typer.testing.CliRunner,
        mock_logger: MagicMock,
        mock_api: MagicMock,
    ) -> None:
        """Test api command handles KeyboardInterrupt gracefully."""
        # Arrange
        mock_get_logger.return_value = mock_logger
        mock_init_logging.return_value = None
        mock_api.run_docker.side_effect = KeyboardInterrupt()
        mock_api_class.return_value = mock_api

        # Act
        result = cli_runner.invoke(app, [])

        # Assert
        assert result.exit_code == 0
        mock_init_logging.assert_called_once()
        mock_get_logger.assert_called_once()
        mock_api_class.assert_called_once()
        mock_api.run_docker.assert_called_once()
        mock_logger.info.assert_any_call("Starting AWA API server for debugging...")
        mock_logger.info.assert_any_call("Received shutdown signal, stopping API server...")

    @patch("awa.core.cli.commands.api.Api")
    @patch("awa.core.cli.commands.api.init_logging")
    @patch("awa.core.cli.commands.api.get_logger")
    def test_api_command_generic_exception(
        self,
        mock_get_logger: MagicMock,
        mock_init_logging: MagicMock,
        mock_api_class: MagicMock,
        cli_runner: typer.testing.CliRunner,
        mock_logger: MagicMock,
        mock_api: MagicMock,
    ) -> None:
        """Test api command handles generic exceptions by re-raising."""
        # Arrange
        mock_get_logger.return_value = mock_logger
        mock_init_logging.return_value = None
        test_exception = RuntimeError("API startup failed")
        mock_api.run_docker.side_effect = test_exception
        mock_api_class.return_value = mock_api

        # Act
        result = cli_runner.invoke(app, [])

        # Assert
        assert result.exit_code != 0  # Should exit with error
        mock_init_logging.assert_called_once()
        mock_get_logger.assert_called_once()
        mock_api_class.assert_called_once()
        mock_api.run_docker.assert_called_once()
        mock_logger.info.assert_called_once_with("Starting AWA API server for debugging...")
        mock_logger.exception.assert_called_once_with("API server error")

    @patch("awa.core.cli.commands.api.Api")
    @patch("awa.core.cli.commands.api.init_logging")
    @patch("awa.core.cli.commands.api.get_logger")
    def test_api_command_api_creation_exception(
        self,
        mock_get_logger: MagicMock,
        mock_init_logging: MagicMock,
        mock_api_class: MagicMock,
        cli_runner: typer.testing.CliRunner,
        mock_logger: MagicMock,
    ) -> None:
        """Test api command when Api creation fails."""
        # Arrange
        mock_get_logger.return_value = mock_logger
        mock_init_logging.return_value = None
        test_exception = Exception("Api creation failed")
        mock_api_class.side_effect = test_exception

        # Act
        result = cli_runner.invoke(app, [])

        # Assert
        assert result.exit_code != 0  # Should exit with error
        mock_init_logging.assert_called_once()
        mock_get_logger.assert_called_once()
        mock_api_class.assert_called_once()
        mock_logger.info.assert_called_once_with("Starting AWA API server for debugging...")
        mock_logger.exception.assert_called_once_with("API server error")
