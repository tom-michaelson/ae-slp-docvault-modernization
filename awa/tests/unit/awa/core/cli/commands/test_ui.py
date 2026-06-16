import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from unittest.mock import Mock, patch

import pytest
import typer.testing

from awa.core.cli.commands.ui import app, ui_async
from awa.core.models.cli.ui_mode import UIMode

MOCK_DEV_COMMAND_COUNT = 3
MOCK_PROD_COMMAND_COUNT = 4


def mock_asyncio_run_func(coro: Callable[..., Awaitable[None]]) -> None:
    """Mock asyncio.run function."""
    if hasattr(coro, "close"):
        coro.close()


@pytest.fixture
def runner() -> typer.testing.CliRunner:
    """Create a Typer test runner."""
    return typer.testing.CliRunner()


@patch("awa.core.cli.commands.ui.asyncio.run")
def test_ui_command_default_mode(
    mock_asyncio_run: Mock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test ui command with default mode."""
    mock_asyncio_run.side_effect = mock_asyncio_run_func

    result = runner.invoke(app, [])

    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@patch("awa.core.cli.commands.ui.asyncio.run")
def test_ui_command_dev_mode(mock_asyncio_run: Mock, runner: typer.testing.CliRunner) -> None:
    """Test ui command with dev mode."""
    mock_asyncio_run.side_effect = mock_asyncio_run_func

    result = runner.invoke(app, ["--ui", "dev"])

    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@patch("awa.core.cli.commands.ui.asyncio.run")
def test_ui_command_prod_mode(mock_asyncio_run: Mock, runner: typer.testing.CliRunner) -> None:
    """Test ui command with prod mode."""
    mock_asyncio_run.side_effect = mock_asyncio_run_func

    result = runner.invoke(app, ["--ui", "prod"])

    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()


@pytest.mark.asyncio
async def test_ui_async_none_mode() -> None:
    """Test ui_async with NONE mode."""
    # Act
    await ui_async(mode=UIMode.NONE)

    # Assert - should return early without errors


@pytest.mark.asyncio
async def test_ui_async_none_mode_not_set() -> None:
    """Test ui_async with mode not set (None)."""
    # Act
    await ui_async(mode=UIMode.NONE)

    # Assert - should return early without errors


@pytest.mark.asyncio
@patch("awa.core.cli.commands.ui.CommandUtils.stream_command_async")
@patch("awa.core.cli.commands.ui.CommandUtils.run_command_async")
@patch("awa.core.cli.commands.ui.EnvConfig.get_env_config")
async def test_ui_async_dev_mode(
    mock_get_env_config: Mock,
    mock_run_command: Mock,
    mock_stream_command: Mock,
) -> None:
    """Test ui_async with DEV mode."""
    # Arrange
    mock_run_command.return_value = None
    mock_get_env_config().awa_ui_host = "localhost"
    mock_get_env_config().awa_ui_port = 3000
    mock_get_env_config().awa_api_host = "localhost"
    mock_get_env_config().awa_api_port = 8000
    mock_get_env_config().temporal_ui_host = "localhost"
    mock_get_env_config().temporal_ui_port = 8080

    # Mock the streaming command for UI server
    async def mock_stream_generator() -> AsyncGenerator[str | Mock, None]:
        # First yield: process handle
        proc_mock = Mock()
        proc_mock.pid = 12345
        yield proc_mock
        # Subsequent yields: output lines
        yield "UI server started"
        yield "Server listening on port 3000"

    mock_stream_command.return_value = mock_stream_generator()

    # Act
    await ui_async(mode=UIMode.DEV)

    # Assert
    # Should have 3 calls to run_command_async (copy recipes, generate CLI docs, and docs build)
    assert mock_run_command.call_count == 3
    mock_run_command.assert_any_call(command="pnpm run copy-cookbook-docs")
    mock_run_command.assert_any_call(command="uv run scripts/generate_cli_docs.py")
    mock_run_command.assert_any_call(command="pnpm run docs:build")
    # Should call stream_command_async for UI dev server
    mock_stream_command.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.ui.CommandUtils.stream_command_async")
@patch("awa.core.cli.commands.ui.CommandUtils.run_command_async")
@patch("awa.core.cli.commands.ui.EnvConfig.get_env_config")
async def test_ui_async_prod_mode(
    mock_get_env_config: Mock,
    mock_run_command: Mock,
    mock_stream_command: Mock,
) -> None:
    """Test ui_async with PROD mode."""
    # Arrange
    mock_run_command.return_value = None
    mock_get_env_config().awa_ui_host = "localhost"
    mock_get_env_config().awa_ui_port = 3000
    mock_get_env_config().awa_api_host = "localhost"
    mock_get_env_config().awa_api_port = 8000
    mock_get_env_config().temporal_ui_host = "localhost"
    mock_get_env_config().temporal_ui_port = 8080

    # Mock the streaming command for UI server
    async def mock_stream_generator() -> AsyncGenerator[str | Mock, None]:
        # First yield: process handle
        proc_mock = Mock()
        proc_mock.pid = 54321
        yield proc_mock
        # Subsequent yields: output lines
        yield "UI server started"
        yield "Server listening on port 3000"

    mock_stream_command.return_value = mock_stream_generator()

    # Act
    await ui_async(mode=UIMode.PROD)

    # Assert
    # Should have 4 calls to run_command_async (copy recipes, generate CLI docs, docs build, and UI build)
    assert mock_run_command.call_count == 4
    mock_run_command.assert_any_call(command="pnpm run copy-cookbook-docs")
    mock_run_command.assert_any_call(command="uv run scripts/generate_cli_docs.py")
    mock_run_command.assert_any_call(command="pnpm run docs:build")
    mock_run_command.assert_any_call(command="pnpm run ui:build")
    # Should call stream_command_async for UI preview server
    mock_stream_command.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.ui.CommandUtils.stream_command_async")
@patch("awa.core.cli.commands.ui.CommandUtils.run_command_async")
@patch("awa.core.cli.commands.ui.EnvConfig.get_env_config")
@patch.dict(os.environ, {"EXISTING_VAR": "existing_value"}, clear=True)
async def test_ui_async_environment_variables(
    mock_get_env_config: Mock,
    mock_run_command: Mock,
    mock_stream_command: Mock,
) -> None:
    """Test that environment variables are correctly set."""
    # Arrange
    mock_run_command.return_value = None
    mock_get_env_config().awa_ui_host = "test-ui-host"
    mock_get_env_config().awa_ui_port = 3001
    mock_get_env_config().awa_api_host = "test-api-host"
    mock_get_env_config().awa_api_port = 8001
    mock_get_env_config().temporal_ui_host = "test-temporal-host"
    mock_get_env_config().temporal_ui_port = 8081

    # Mock the streaming command for UI server
    async def mock_stream_generator() -> AsyncGenerator[str | Mock, None]:
        # First yield: process handle
        proc_mock = Mock()
        proc_mock.pid = 99999
        yield proc_mock
        # Subsequent yields: output lines
        yield "UI server started"

    mock_stream_command.return_value = mock_stream_generator()

    # Act
    await ui_async(mode=UIMode.DEV)

    # Assert
    # Check that environment variables were passed correctly to stream_command_async
    env_arg = mock_stream_command.call_args[1]["env"]
    assert env_arg["AWA_UI_HOST"] == "test-ui-host"
    assert env_arg["AWA_UI_PORT"] == "3001"
    assert env_arg["AWA_API_HOST"] == "test-api-host"
    assert env_arg["AWA_API_PORT"] == "8001"
    assert env_arg["TEMPORAL_UI_HOST"] == "test-temporal-host"
    assert env_arg["TEMPORAL_UI_PORT"] == "8081"
    assert env_arg["EXISTING_VAR"] == "existing_value"  # Original env vars preserved


@pytest.mark.asyncio
@patch("awa.core.cli.commands.ui.is_packaged_mode")
@patch("awa.core.cli.commands.ui.build_and_serve_dynamic")
async def test_ui_async_package_mode_early_exit(
    mock_build_and_serve: Mock,
    mock_is_packaged_mode: Mock,
) -> None:
    """Test ui_async exits early in package mode without calling build_and_serve_dynamic."""
    # Arrange
    mock_is_packaged_mode.return_value = True

    # Act
    await ui_async(mode=UIMode.DEV)

    # Assert
    mock_is_packaged_mode.assert_called_once()
    mock_build_and_serve.assert_not_called()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.ui.is_packaged_mode")
@patch("awa.core.cli.commands.ui.build_and_serve_dynamic")
async def test_ui_async_package_mode_all_ui_modes(
    mock_build_and_serve: Mock,
    mock_is_packaged_mode: Mock,
) -> None:
    """Test ui_async exits early for all UI modes in package mode."""
    # Arrange
    mock_is_packaged_mode.return_value = True

    # Test DEV mode
    await ui_async(mode=UIMode.DEV)
    assert mock_build_and_serve.call_count == 0

    # Test PROD mode
    await ui_async(mode=UIMode.PROD)
    assert mock_build_and_serve.call_count == 0

    # Assert mocks called correctly
    assert mock_is_packaged_mode.call_count == 2
    mock_build_and_serve.assert_not_called()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.ui.is_packaged_mode")
@patch("awa.core.cli.commands.ui.build_and_serve_dynamic")
async def test_ui_async_development_mode_still_works(
    mock_build_and_serve: Mock,
    mock_is_packaged_mode: Mock,
) -> None:
    """Test ui_async still works normally in development mode."""
    # Arrange
    mock_is_packaged_mode.return_value = False
    mock_build_and_serve.return_value = None

    # Act
    await ui_async(mode=UIMode.DEV)

    # Assert
    mock_is_packaged_mode.assert_called_once()
    mock_build_and_serve.assert_called_once_with(UIMode.DEV)
