from unittest.mock import MagicMock, patch

import pytest
import typer.testing

from awa.core.cli.commands.mcp import app


@pytest.fixture
def runner() -> typer.testing.CliRunner:
    """Create a Typer test runner."""
    return typer.testing.CliRunner()


@patch("awa.core.cli.commands.mcp.init_logging")
@patch("awa.core.mcp.mcp_server.mcp.run")
def test_mcp_command(
    mock_mcp_run: MagicMock,
    mock_init_logging: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the mcp command execution."""
    # Arrange
    mock_mcp_run.return_value = None
    mock_init_logging.return_value = None

    # Act
    result = runner.invoke(app, [])  # The command name is already "mcp" in the @app.command decorator

    # Assert
    assert result.exit_code == 0
    mock_init_logging.assert_called_once_with(file_only=False)  # Changed to False
    mock_mcp_run.assert_called_once()


@patch("awa.core.cli.commands.mcp.init_logging")
@patch("awa.core.mcp.mcp_server.mcp.run")
def test_mcp_command_with_exception(
    mock_mcp_run: MagicMock,
    mock_init_logging: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the mcp command when an exception occurs."""
    # Arrange
    mock_init_logging.return_value = None
    mock_mcp_run.side_effect = Exception("Test exception")

    # Act
    result = runner.invoke(app, [])

    # Assert - In CLI testing, exceptions are often caught and result in non-zero exit codes
    assert result.exit_code != 0
    mock_init_logging.assert_called_once_with(file_only=False)
    mock_mcp_run.assert_called_once()


@patch("awa.core.cli.commands.mcp.init_logging")
@patch("awa.core.mcp.mcp_server.mcp.run")
@patch("awa.core.cli.commands.mcp.handle_options")
def test_mcp_command_with_cli_options(
    mock_options: MagicMock,
    mock_mcp_run: MagicMock,
    mock_init_logging: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the mcp command execution."""
    # Arrange
    mock_env = ".test_env"
    mock_config = "test_config.yaml"
    mock_mcp_run.return_value = None
    mock_init_logging.return_value = None

    # Act
    result = runner.invoke(
        app,
        ["--env", mock_env, "--config", mock_config],
    )  # The command name is already "mcp" in the @app.command decorator

    # Assert
    assert result.exit_code == 0
    mock_init_logging.assert_called_once_with(file_only=False)
    mock_mcp_run.assert_called_once()
    mock_options.assert_called_once_with(mock_env, mock_config)
