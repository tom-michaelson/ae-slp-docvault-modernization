import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer.testing

from awa.core.cli import constants
from awa.core.cli.commands.start import (
    _check_initial_status_and_early_exit,
    _handle_post_start_monitoring,
    _setup_and_validate_inputs,
    _start,
    _start_requested_services,
    app,
)
from awa.core.models.cli.ui_mode import UIMode

MOCK_CALL_COUNT = 2


@pytest.fixture
def runner() -> typer.testing.CliRunner:
    """Create a Typer test runner."""
    return typer.testing.CliRunner()


@patch("awa.core.cli.commands.start.asyncio.run")
def test_start_command(
    mock_asyncio_run: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the start command execution."""

    # Arrange
    def close_coroutine(coro: object) -> None:
        coro.close()

    mock_asyncio_run.side_effect = close_coroutine

    # Act
    result = runner.invoke(app, [])

    # Assert
    assert result.exit_code == 0


@patch("awa.core.cli.commands.start.asyncio.run")
def test_start_command_with_terminate_flag(
    mock_asyncio_run: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the start command with terminate flag."""

    # Arrange
    def close_coroutine(coro: object) -> None:
        coro.close()

    mock_asyncio_run.side_effect = close_coroutine

    # Act
    result = runner.invoke(app, ["--terminate"])

    # Assert
    assert result.exit_code == 0


@patch("awa.core.cli.commands.start.asyncio.run")
def test_start_command_with_ui_mode_flag(
    mock_asyncio_run: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the start command with ui mode flag."""

    # Arrange
    def close_coroutine(coro: object) -> None:
        coro.close()

    mock_asyncio_run.side_effect = close_coroutine

    # Act
    result = runner.invoke(app, ["--ui-mode", "prod"])

    # Assert
    assert result.exit_code == 0


@patch("awa.core.cli.commands.start.asyncio.run")
def test_start_command_with_detach_flag(
    mock_asyncio_run: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the start command with detach flag."""

    # Arrange
    def close_coroutine(coro: object) -> None:
        coro.close()

    mock_asyncio_run.side_effect = close_coroutine

    # Act
    result = runner.invoke(app, ["--detach"])

    # Assert
    assert result.exit_code == 0


@pytest.mark.asyncio
@patch("awa.core.cli.commands.start.ServiceManager")
async def test_start_async_all_services_running(
    mock_service_manager_class: MagicMock,
) -> None:
    """Test _start async function when all services are already running."""
    # Arrange
    mock_service_manager = AsyncMock()
    mock_service_manager.check_all_services.return_value = {
        "temporal_server": True,
        "api": True,
        "ui": True,
    }
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    # Act
    await _start(ui_mode=UIMode.DEV, terminate_all=None, detach=False)

    # Assert
    mock_service_manager.check_all_services.assert_called_once_with(UIMode.DEV)
    # Should not call start_missing_services since all are already running
    mock_service_manager.start_missing_services.assert_not_called()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.start._stop_all")
@patch("awa.core.cli.commands.start.ServiceManager")
@patch("awa.core.cli.commands.start.asyncio.Event")
async def test_start_async_services_need_starting(
    mock_event_class: MagicMock,
    mock_service_manager_class: MagicMock,
    mock_stop_all: AsyncMock,
) -> None:
    """Test _start async function when services need to be started."""
    # Arrange
    mock_service_manager = AsyncMock()
    initial_status = {"temporal_server": False, "api": False, "ui": False}
    final_status = {"temporal_server": True, "api": True, "ui": True}
    mock_service_manager.check_all_services.side_effect = [
        initial_status,  # First call - services not running
        final_status,  # Second call - services running
    ]
    mock_service_manager.start_missing_services.return_value = None
    mock_service_manager.ensure_all_services_running.return_value = None
    mock_service_manager.rollback_started_services.return_value = None
    mock_service_manager.display_service_urls = MagicMock(return_value=None)
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    mock_event = AsyncMock()
    mock_event.wait.side_effect = KeyboardInterrupt()  # Simulate Ctrl+C
    mock_event_class.return_value = mock_event

    # Act - should handle the KeyboardInterrupt gracefully without re-raising
    await _start(ui_mode=UIMode.DEV, terminate_all=True, detach=False)

    # Assert
    assert mock_service_manager.check_all_services.call_count >= 1
    mock_service_manager.ensure_all_services_running.assert_called_once_with(
        ui_mode=UIMode.DEV,
        terminate_all=True,
        detach=False,
        services=None,
    )
    mock_service_manager.display_service_urls.assert_called_once_with(None)
    mock_stop_all.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.start._stop_all")
@patch("awa.core.cli.commands.start.ServiceManager")
@patch("awa.core.cli.commands.start.asyncio.Event")
async def test_start_async_cancelled_error(
    mock_event_class: MagicMock,
    mock_service_manager_class: MagicMock,
    mock_stop_all: AsyncMock,
) -> None:
    """Test _start async function when cancelled."""
    # Arrange
    mock_service_manager = AsyncMock()
    initial_status = {"temporal_server": False, "api": False, "ui": False}
    final_status = {"temporal_server": True, "api": True, "ui": True}
    mock_service_manager.check_all_services.side_effect = [
        initial_status,  # First call - services not running
        final_status,  # Second call - services running
    ]
    mock_service_manager.start_missing_services.return_value = None
    mock_service_manager.ensure_all_services_running.return_value = None
    mock_service_manager.rollback_started_services.return_value = None
    mock_service_manager.display_service_urls = MagicMock(return_value=None)
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    mock_event = AsyncMock()
    mock_event.wait.side_effect = asyncio.CancelledError()
    mock_event_class.return_value = mock_event

    # Act - should handle the cancellation gracefully without re-raising
    with contextlib.suppress(asyncio.CancelledError):
        await _start(ui_mode=UIMode.DEV, terminate_all=False, detach=False)

    # Assert
    # CancelledError is handled the same as KeyboardInterrupt, so _stop_all should be called
    mock_stop_all.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.start._stop_all")
@patch("awa.core.cli.commands.start.ServiceManager")
async def test_start_async_with_detach_mode(
    mock_service_manager_class: MagicMock,
    mock_stop_all: AsyncMock,
) -> None:
    """Test _start async function with detach mode - should exit after starting services."""
    # Arrange
    mock_service_manager = AsyncMock()
    initial_status = {"temporal_server": False, "api": False, "ui": False}
    final_status = {"temporal_server": True, "api": True, "ui": True}
    mock_service_manager.check_all_services.side_effect = [
        initial_status,  # First call - services not running
        final_status,  # Second call - services running
    ]
    mock_service_manager.start_missing_services.return_value = None
    mock_service_manager.ensure_all_services_running.return_value = None
    mock_service_manager.rollback_started_services.return_value = None
    mock_service_manager.display_service_urls = MagicMock(return_value=None)
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    # Act
    await _start(ui_mode=UIMode.DEV, terminate_all=False, detach=True)

    # Assert
    assert mock_service_manager.check_all_services.call_count >= 1
    mock_service_manager.ensure_all_services_running.assert_called_once_with(
        ui_mode=UIMode.DEV,
        terminate_all=False,
        detach=True,
        services=None,
    )
    mock_service_manager.display_service_urls.assert_called_once_with(None)
    # In detach mode, stop_all should NOT be called since we exit early
    mock_stop_all.assert_not_called()


@patch("awa.core.cli.commands.start.asyncio.run")
@patch("awa.core.cli.commands.start.handle_options")
def test_start_command_with_cli_options(
    mock_options: MagicMock,
    mock_asyncio_run: MagicMock,
    runner: typer.testing.CliRunner,
) -> None:
    """Test the start command with CLI options."""

    # Arrange
    def close_coroutine(coro: object) -> None:
        coro.close()

    mock_asyncio_run.side_effect = close_coroutine

    # Act
    result = runner.invoke(app, ["--env", "test.env", "--config", "test.yaml"])

    # Assert
    assert result.exit_code == 0
    mock_options.assert_called_once_with("test.env", "test.yaml")


# Tests for --services option functionality
@pytest.mark.asyncio
@patch("awa.core.cli.commands.start.ServiceManager")
async def test_start_specific_services_detached(
    mock_service_manager_class: MagicMock,
) -> None:
    """Test start command with specific services in detached mode."""
    # Arrange
    mock_service_manager = AsyncMock()
    mock_service_manager.check_all_services.side_effect = [
        {  # Initial call - some services not running
            "temporal_server": True,
            "temporal_worker": False,
            "api": False,
            "ui": True,
        },
        {  # After ensure_all_services_running - requested services now running
            "temporal_server": True,
            "temporal_worker": True,
            "api": True,
            "ui": True,
        },
        {  # Additional retry calls - services still running
            "temporal_server": True,
            "temporal_worker": True,
            "api": True,
            "ui": True,
        },
    ]
    mock_service_manager.start_missing_services.return_value = None
    mock_service_manager.ensure_all_services_running.return_value = None
    mock_service_manager.display_service_urls = MagicMock(return_value=None)
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    # Act
    await _start(services="api,temporal_worker", detach=True)

    # Assert
    mock_service_manager.ensure_all_services_running.assert_called_once()
    call_args = mock_service_manager.ensure_all_services_running.call_args

    # Check that the services parameter was passed correctly
    assert call_args.kwargs["services"] == ["api", "temporal_worker"]

    mock_service_manager.display_service_urls.assert_called_once_with(["api", "temporal_worker"])


@pytest.mark.asyncio
@patch("awa.core.cli.commands.start.ServiceManager")
async def test_start_single_service_detached(
    mock_service_manager_class: MagicMock,
) -> None:
    """Test start command with single service in detached mode."""
    # Arrange
    mock_service_manager = AsyncMock()
    mock_service_manager.check_all_services.return_value = {
        "temporal_server": True,
        "temporal_worker": True,
        "api": False,
        "ui": True,
    }
    mock_service_manager.start_missing_services.return_value = None
    mock_service_manager.ensure_all_services_running.return_value = None
    mock_service_manager.display_service_urls = MagicMock(return_value=None)
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    # Act
    await _start(services="api", detach=True)

    # Assert
    mock_service_manager.ensure_all_services_running.assert_called_once()
    call_args = mock_service_manager.ensure_all_services_running.call_args

    # Check that the services parameter was passed correctly
    assert call_args.kwargs["services"] == ["api"]

    mock_service_manager.display_service_urls.assert_called_once_with(["api"])


@pytest.mark.asyncio
async def test_start_invalid_service_raises_error() -> None:
    """Test that invalid service name raises typer.Exit."""
    with pytest.raises(typer.Exit):
        await _start(services="invalid_service")


@pytest.mark.asyncio
async def test_start_empty_service_string_raises_error() -> None:
    """Test that empty service string raises typer.Exit."""
    with pytest.raises(typer.Exit):
        await _start(services="")


@pytest.mark.asyncio
@patch("awa.core.cli.commands.start._stop_all")
@patch("awa.core.cli.commands.start.ServiceManager")
@patch("awa.core.cli.commands.start.asyncio.Event")
async def test_start_non_detached_with_signal_handling(
    mock_event_class: MagicMock,
    mock_service_manager_class: MagicMock,
    mock_stop_all: AsyncMock,
) -> None:
    """Test start command in non-detached mode with signal handling."""
    # Arrange
    mock_service_manager = AsyncMock()
    initial_status = {
        "temporal_server": False,
        "temporal_worker": False,
        "api": False,
        "ui": False,
    }
    final_status = {
        "temporal_server": True,
        "temporal_worker": True,
        "api": True,
        "ui": True,
    }
    mock_service_manager.check_all_services.side_effect = [
        initial_status,
        final_status,
        final_status,  # Additional calls from ensure_all_services_running retry logic
        final_status,
        final_status,
    ]
    mock_service_manager.start_missing_services.return_value = None
    mock_service_manager.ensure_all_services_running.return_value = None
    mock_service_manager.rollback_started_services.return_value = None
    mock_service_manager.display_service_urls = MagicMock(return_value=None)
    mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

    mock_event = AsyncMock()
    mock_event.wait.side_effect = KeyboardInterrupt()
    mock_event_class.return_value = mock_event

    # Act
    await _start(detach=False)

    # Assert
    mock_service_manager.ensure_all_services_running.assert_called_once()
    mock_service_manager.display_service_urls.assert_called_once_with(None)
    mock_stop_all.assert_called_once()


# Tests for _stop_started_services function
class TestHelperFunctions:
    """Test cases for the helper functions in start.py."""

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.validate_global_configuration")
    @patch("awa.core.cli.commands.start.ServiceManager")
    @patch("awa.core.cli.commands.start.parse_service_list")
    async def test_setup_and_validate_inputs_with_services(
        self,
        mock_parse_service_list: MagicMock,
        mock_service_manager_class: MagicMock,
        mock_validate_global_config: MagicMock,
    ) -> None:
        """Test _setup_and_validate_inputs with specific services."""
        # Arrange
        mock_validate_global_config.return_value = True
        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)
        mock_parse_service_list.return_value = [constants.SERVICE_API, constants.SERVICE_UI]

        # Act
        ui_mode, service_manager, requested_services = await _setup_and_validate_inputs(
            ui_mode=UIMode.PROD,
            terminate_all=True,
            services="api,ui",
        )

        # Assert
        assert ui_mode == UIMode.PROD
        assert service_manager == mock_service_manager
        assert requested_services == [constants.SERVICE_API, constants.SERVICE_UI]
        mock_parse_service_list.assert_called_once_with("api,ui")
        mock_service_manager_class.create.assert_called_once_with(terminate_all=True)

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.validate_global_configuration")
    @patch("awa.core.cli.commands.start.ServiceManager")
    async def test_setup_and_validate_inputs_defaults(
        self,
        mock_service_manager_class: MagicMock,
        mock_validate_global_config: MagicMock,
    ) -> None:
        """Test _setup_and_validate_inputs with default values."""
        # Arrange
        mock_validate_global_config.return_value = True
        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        ui_mode, service_manager, requested_services = await _setup_and_validate_inputs(
            ui_mode=None,
            terminate_all=None,
            services=None,
        )

        # Assert
        assert ui_mode == UIMode.DEV  # Default value
        assert service_manager == mock_service_manager
        assert requested_services is None
        mock_service_manager_class.create.assert_called_once_with(terminate_all=False)

    @pytest.mark.asyncio
    async def test_check_initial_status_and_early_exit_all_running(self) -> None:
        """Test _check_initial_status_and_early_exit when all services are running."""
        # Arrange
        mock_service_manager = AsyncMock()
        mock_service_manager.check_all_services.return_value = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        # Act
        initial_status, should_exit_early = await _check_initial_status_and_early_exit(
            service_manager=mock_service_manager,
            ui_mode=UIMode.DEV,
            requested_services=None,
        )

        # Assert
        assert should_exit_early is True
        assert initial_status == {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

    @pytest.mark.asyncio
    async def test_check_initial_status_and_early_exit_with_filtered_services(self) -> None:
        """Test _check_initial_status_and_early_exit with filtered services."""
        # Arrange
        mock_service_manager = AsyncMock()
        mock_service_manager.check_all_services.return_value = {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: False,
        }

        # Act
        initial_status, should_exit_early = await _check_initial_status_and_early_exit(
            service_manager=mock_service_manager,
            ui_mode=UIMode.DEV,
            requested_services=[constants.SERVICE_API],  # Only API requested and it's running
        )

        # Assert
        assert should_exit_early is True  # API is already running
        assert initial_status == {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: False,
        }

    @pytest.mark.asyncio
    async def test_check_initial_status_and_early_exit_services_need_starting(self) -> None:
        """Test _check_initial_status_and_early_exit when services need starting."""
        # Arrange
        mock_service_manager = AsyncMock()
        mock_service_manager.check_all_services.return_value = {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_API: False,
            constants.SERVICE_UI: False,
        }

        # Act
        initial_status, should_exit_early = await _check_initial_status_and_early_exit(
            service_manager=mock_service_manager,
            ui_mode=UIMode.DEV,
            requested_services=None,
        )

        # Assert
        assert should_exit_early is False
        assert initial_status == {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_API: False,
            constants.SERVICE_UI: False,
        }

    @pytest.mark.asyncio
    async def test_start_requested_services(self) -> None:
        """Test _start_requested_services calls ensure_all_services_running correctly."""
        # Arrange
        mock_service_manager = AsyncMock()
        # display_service_urls should be a regular synchronous method, not async
        mock_service_manager.display_service_urls = MagicMock(return_value=None)

        # Act
        await _start_requested_services(
            service_manager=mock_service_manager,
            ui_mode=UIMode.PROD,
            terminate_all=True,
            detach=True,
            requested_services=[constants.SERVICE_API],
        )

        # Assert
        mock_service_manager.ensure_all_services_running.assert_called_once_with(
            ui_mode=UIMode.PROD,
            terminate_all=True,
            detach=True,
            services=[constants.SERVICE_API],
        )

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.asyncio.Event")
    async def test_handle_post_start_monitoring_detached(
        self,
        mock_event_class: MagicMock,
    ) -> None:
        """Test _handle_post_start_monitoring in detached mode."""
        # Arrange
        mock_service_manager = AsyncMock()
        mock_service_manager.check_all_services.return_value = {
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        # Act
        await _handle_post_start_monitoring(
            service_manager=mock_service_manager,
            detach=True,
            requested_services=[constants.SERVICE_API, constants.SERVICE_UI],
            initial_status={constants.SERVICE_API: False, constants.SERVICE_UI: False},
        )

        # Assert
        # display_service_urls is called in _start_requested_services, not _handle_post_start_monitoring
        # Should not create Event for monitoring since detached=True
        mock_event_class.assert_not_called()

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start._stop_all")
    @patch("awa.core.cli.commands.start.asyncio.Event")
    async def test_handle_post_start_monitoring_with_keyboard_interrupt(
        self,
        mock_event_class: MagicMock,
        mock_stop_all: AsyncMock,
    ) -> None:
        """Test _handle_post_start_monitoring handles KeyboardInterrupt."""
        # Arrange
        mock_service_manager = AsyncMock()
        mock_service_manager.check_all_services.return_value = {
            constants.SERVICE_API: True,
        }

        mock_event = AsyncMock()
        mock_event.wait.side_effect = KeyboardInterrupt()
        mock_event_class.return_value = mock_event

        initial_status = {constants.SERVICE_API: False}

        # Act
        with contextlib.suppress(KeyboardInterrupt):
            await _handle_post_start_monitoring(
                service_manager=mock_service_manager,
                detach=False,
                requested_services=[constants.SERVICE_API],
                initial_status=initial_status,
            )

        # Assert
        mock_stop_all.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.validate_global_configuration")
    @patch("awa.core.cli.commands.start.is_packaged_mode")
    @patch("awa.core.cli.commands.start.ServiceManager")
    @patch("awa.core.cli.commands.start.parse_service_list")
    async def test_setup_and_validate_inputs_filters_ui_in_package_mode(
        self,
        mock_parse_service_list: MagicMock,
        mock_service_manager_class: MagicMock,
        mock_is_packaged_mode: MagicMock,
        mock_validate_global_config: MagicMock,
    ) -> None:
        """Test that UI service is filtered out when in package mode with specific services."""
        # Arrange
        mock_is_packaged_mode.return_value = True
        mock_validate_global_config.return_value = True  # Simulate valid global config
        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)
        mock_parse_service_list.return_value = ["api", "ui", "temporal_server"]

        # Act
        _ui_mode, _service_manager, requested_services = await _setup_and_validate_inputs(
            ui_mode=UIMode.DEV,
            terminate_all=False,
            services="api,ui,temporal_server",
        )

        # Assert
        assert requested_services == ["api", "temporal_server"]
        mock_parse_service_list.assert_called_once_with("api,ui,temporal_server")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.is_packaged_mode")
    @patch("awa.core.cli.commands.start.ServiceManager")
    @patch("awa.core.cli.commands.start.parse_service_list")
    async def test_setup_and_validate_inputs_ui_only_fails_in_package_mode(
        self,
        mock_parse_service_list: MagicMock,
        mock_service_manager_class: MagicMock,
        mock_is_packaged_mode: MagicMock,
    ) -> None:
        """Test that requesting only UI service fails in package mode."""
        # Arrange
        mock_is_packaged_mode.return_value = True
        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)
        mock_parse_service_list.return_value = ["ui"]

        # Act & Assert
        with pytest.raises(typer.Exit):
            await _setup_and_validate_inputs(
                ui_mode=UIMode.DEV,
                terminate_all=False,
                services="ui",
            )

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.validate_global_configuration")
    @patch("awa.core.cli.commands.start.is_packaged_mode")
    @patch("awa.core.cli.commands.start.ServiceManager")
    async def test_setup_and_validate_inputs_all_services_excludes_ui_in_package_mode(
        self,
        mock_service_manager_class: MagicMock,
        mock_is_packaged_mode: MagicMock,
        mock_validate_global_config: MagicMock,
    ) -> None:
        """Test that starting all services excludes UI in package mode."""
        # Arrange
        mock_is_packaged_mode.return_value = True
        mock_validate_global_config.return_value = True  # Simulate valid global config
        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        _ui_mode, _service_manager, requested_services = await _setup_and_validate_inputs(
            ui_mode=UIMode.DEV,
            terminate_all=False,
            services=None,  # All services
        )

        # Assert
        expected_services = ["api", "temporal_server", "temporal_worker"]
        assert set(requested_services) == set(expected_services)

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.start.is_packaged_mode")
    @patch("awa.core.utils.cli_utils.is_packaged_mode")
    @patch("awa.core.cli.commands.start.validate_global_configuration")
    @patch("awa.core.cli.commands.start.ServiceManager")
    @patch("awa.core.cli.commands.start.parse_service_list")
    async def test_setup_and_validate_inputs_development_mode_unchanged(
        self,
        mock_parse_service_list: MagicMock,
        mock_service_manager_class: MagicMock,
        mock_validate_global_config: MagicMock,
        mock_cli_utils_is_packaged_mode: MagicMock,
        mock_is_packaged_mode: MagicMock,
    ) -> None:
        """Test that development mode behavior is unchanged."""
        # Arrange
        mock_validate_global_config.return_value = True
        mock_cli_utils_is_packaged_mode.return_value = False
        mock_is_packaged_mode.return_value = False
        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)
        mock_parse_service_list.return_value = ["api", "ui"]

        # Act - test specific services including UI
        _ui_mode, _service_manager, requested_services = await _setup_and_validate_inputs(
            ui_mode=UIMode.DEV,
            terminate_all=False,
            services="api,ui",
        )

        # Assert
        assert requested_services == ["api", "ui"]
        mock_parse_service_list.assert_called_once_with("api,ui")

        # Reset mocks for second test
        mock_parse_service_list.reset_mock()

        # Act - test all services (None)
        _ui_mode, _service_manager, requested_services = await _setup_and_validate_inputs(
            ui_mode=UIMode.DEV,
            terminate_all=False,
            services=None,
        )

        # Assert
        assert requested_services is None  # All services, unchanged
        mock_parse_service_list.assert_not_called()  # Should not be called when services=None
