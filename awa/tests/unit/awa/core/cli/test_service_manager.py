import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.cli import constants
from awa.core.cli.service_manager import ServiceManager
from awa.core.models.cli.service_state import ServiceInfo
from awa.core.models.cli.ui_mode import UIMode


class TestServiceManager:
    """Comprehensive tests for ServiceManager class."""

    @pytest.fixture
    def mock_env_config(self) -> MagicMock:
        """Mock environment configuration."""
        with patch("awa.core.cli.service_manager.EnvConfig.get_env_config") as mock_env:
            mock_env.return_value = MagicMock(
                awa_ui_host="localhost",
                awa_ui_port=8000,
                awa_api_host="localhost",
                awa_api_port=8001,
                temporal_ui_host="localhost",
                temporal_ui_port=8002,
                temporal_server_host="localhost",
                temporal_server_port=7233,
                temporal_metrics_port=9090,
            )
            yield mock_env

    @pytest.fixture
    def mock_logger(self) -> MagicMock:
        """Mock logger for testing."""
        with patch("awa.core.cli.service_manager.get_logger") as mock_logger:
            yield mock_logger.return_value

    @pytest.fixture
    def mock_temporal_client(self) -> MagicMock:
        """Mock temporal client."""
        with patch("awa.core.cli.service_manager.TemporalClient.create") as mock_create:
            mock_client = AsyncMock()
            mock_client.terminate_all = False
            mock_create.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def mock_temporal_worker(self) -> MagicMock:
        """Mock temporal worker."""
        with patch("awa.core.cli.service_manager.TemporalWorker") as mock_worker:
            mock_instance = mock_worker.return_value
            mock_instance.default_task_queue = "test-queue"
            yield mock_instance

    @pytest.fixture
    async def service_manager(self, mock_env_config: MagicMock) -> ServiceManager:  # noqa: ARG002
        """Create a service manager for testing."""
        with (
            patch("awa.core.cli.service_manager.TemporalClient.create") as mock_create,
            patch("awa.core.cli.service_manager.TemporalWorker") as mock_worker,
        ):
            mock_client = AsyncMock()
            mock_client.terminate_all = False
            mock_create.return_value = mock_client
            mock_worker.return_value.default_task_queue = "test-queue"

            manager = await ServiceManager.create()
            return manager

    @pytest.mark.asyncio
    async def test_validate_service_process_service_running(self) -> None:
        """Test validate_service_process when service exists and is running."""
        manager = await ServiceManager.create()

        mock_service_info = ServiceInfo(
            pid=12345,
            port=8001,
            started_at=datetime.now(UTC),
        )

        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=mock_service_info)),
            patch.object(manager, "_verify_pid_exists", return_value=True),
        ):
            result = await manager.validate_service_process("test_service")

            assert result is True
            manager.state_manager.get_service_info.assert_called_once_with("test_service")
            manager._verify_pid_exists.assert_called_once_with(12345)

    @pytest.mark.asyncio
    async def test_validate_service_process_service_not_in_state(self) -> None:
        """Test validate_service_process when service not in state file."""
        manager = await ServiceManager.create()

        with patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=None)):
            result = await manager.validate_service_process("test_service")

            assert result is False

    @pytest.mark.asyncio
    async def test_validate_service_process_service_not_running(self) -> None:
        """Test validate_service_process when service exists but process not running."""
        manager = await ServiceManager.create()

        mock_service_info = ServiceInfo(
            pid=12345,
            port=8001,
            started_at=datetime.now(UTC),
        )

        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=mock_service_info)),
            patch.object(manager.state_manager, "is_process_running", return_value=False),
            patch.object(manager.state_manager, "remove_service", new=AsyncMock()),
        ):
            result = await manager.validate_service_process("test_service")

            assert result is False
            manager.state_manager.remove_service.assert_called_once_with("test_service")

    @pytest.mark.asyncio
    async def test_check_all_services_all_running(self) -> None:
        """Test check_all_services when all services are running (PID + external health checks pass)."""
        manager = await ServiceManager.create()
        with (
            patch.object(manager, "validate_service_process", new=AsyncMock(return_value=True)),
            patch.object(manager, "_perform_external_health_check", new=AsyncMock(return_value=True)),
        ):
            result = await manager.check_all_services(ui_mode=UIMode.DEV)
            assert result == {"temporal_server": True, "temporal_worker": True, "api": True, "ui": True}

    @pytest.mark.asyncio
    async def test_check_all_services_pid_validation_fails(self) -> None:
        """Test check_all_services when PID validation fails (services not running)."""
        manager = await ServiceManager.create()
        with patch.object(manager, "validate_service_process", new=AsyncMock(return_value=False)):
            result = await manager.check_all_services(ui_mode=UIMode.DEV)
            # All services should be False because PID validation failed
            assert result == {"temporal_server": False, "temporal_worker": False, "api": False, "ui": False}

    @pytest.mark.asyncio
    async def test_check_all_services_external_health_fails(self) -> None:
        """Test check_all_services when PID validation passes but external health checks fail."""
        manager = await ServiceManager.create()
        with (
            patch.object(manager, "validate_service_process", new=AsyncMock(return_value=True)),
            patch.object(manager, "_perform_external_health_check", new=AsyncMock(return_value=False)),
        ):
            result = await manager.check_all_services(ui_mode=UIMode.DEV)
            # All services should be False because external health check failed
            assert result == {"temporal_server": False, "temporal_worker": False, "api": False, "ui": False}

    @pytest.mark.asyncio
    async def test_perform_external_health_check_temporal_server(self) -> None:
        """Test _perform_external_health_check for temporal server."""
        manager = await ServiceManager.create()

        # Test successful connection
        with patch.object(manager.temporal_client, "get_client", new=AsyncMock()):
            result = await manager._perform_external_health_check(constants.SERVICE_TEMPORAL_SERVER)
            assert result is True

        # Test connection failure
        with patch.object(
            manager.temporal_client,
            "get_client",
            new=AsyncMock(side_effect=Exception("Connection failed")),
        ):
            result = await manager._perform_external_health_check(constants.SERVICE_TEMPORAL_SERVER)
            assert result is False

    @pytest.mark.asyncio
    async def test_perform_external_health_check_temporal_worker(self) -> None:
        """Test _perform_external_health_check for temporal worker."""
        manager = await ServiceManager.create()

        # Test with active pollers
        with patch(
            "awa.core.cli.service_manager._get_active_worker_pollers",
            new=AsyncMock(return_value=["worker-1@host-1"]),
        ):
            result = await manager._perform_external_health_check(constants.SERVICE_TEMPORAL_WORKER)
            assert result is True

        # Test with no active pollers
        with patch(
            "awa.core.cli.service_manager._get_active_worker_pollers",
            new=AsyncMock(return_value=[]),
        ):
            result = await manager._perform_external_health_check(constants.SERVICE_TEMPORAL_WORKER)
            assert result is False

    @pytest.mark.asyncio
    async def test_perform_external_health_check_api_service(self) -> None:
        """Test _perform_external_health_check for API service."""
        manager = await ServiceManager.create()

        # Test successful port check
        with patch(
            "awa.core.utils.command_utils.CommandUtils.check_service_status",
            new=AsyncMock(return_value=True),
        ):
            result = await manager._perform_external_health_check(constants.SERVICE_API)
            assert result is True

        # Test failed port check
        with patch(
            "awa.core.utils.command_utils.CommandUtils.check_service_status",
            new=AsyncMock(return_value=False),
        ):
            result = await manager._perform_external_health_check(constants.SERVICE_API)
            assert result is False

    @pytest.mark.asyncio
    async def test_perform_external_health_check_unknown_service(self) -> None:
        """Test _perform_external_health_check for unknown service."""
        manager = await ServiceManager.create()

        result = await manager._perform_external_health_check("unknown_service")
        assert result is False

    @pytest.mark.asyncio
    async def test_check_all_services_ui_none(self) -> None:
        """Test check_all_services with UI mode NONE."""
        manager = await ServiceManager.create()
        with (
            patch.object(manager, "validate_service_process", new=AsyncMock(return_value=True)),
            patch.object(manager, "_perform_external_health_check", new=AsyncMock(return_value=True)),
        ):
            result = await manager.check_all_services(ui_mode=UIMode.NONE)
            # UI should be True regardless since UIMode.NONE
            assert result == {"temporal_server": True, "temporal_worker": True, "api": True, "ui": True}

    @pytest.mark.asyncio
    async def test_stop_services(self) -> None:
        manager = await ServiceManager.create()

        # Mock StateManager methods
        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=None)),
            patch.object(
                manager.state_manager,
                "stop_service",
                new=AsyncMock(return_value=True),
            ),
        ):
            await manager.stop_services(stop_temporal=True, stop_api=True, stop_ui=True)

    @pytest.mark.asyncio
    async def test_display_service_urls_all_services(self) -> None:
        """Test display_service_urls with no filter (shows all services)."""
        manager = await ServiceManager.create()

        with patch.object(manager, "logger") as mock_logger:
            manager.display_service_urls()

            # Should log the header and all 6 URL entries
            assert mock_logger.info.call_count == 7
            mock_logger.info.assert_any_call("Services running!")
            # Check that calls include URLs for all services
            calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("AWA UI:" in call for call in calls)
            assert any("AWA Docs:" in call for call in calls)
            assert any("AWA API:" in call for call in calls)
            assert any("Temporal UI:" in call for call in calls)
            assert any("Temporal Server:" in call for call in calls)
            assert any("Temporal Metrics:" in call for call in calls)

    @pytest.mark.asyncio
    async def test_display_service_urls_filtered_services(self) -> None:
        """Test display_service_urls with service filter."""
        manager = await ServiceManager.create()

        with patch.object(manager, "logger") as mock_logger:
            # Only show API and UI services
            manager.display_service_urls([constants.SERVICE_API, constants.SERVICE_UI])

            # Should log the header plus UI (2 entries) and API (1 entry) = 4 total
            assert mock_logger.info.call_count == 4
            mock_logger.info.assert_any_call("Services running!")

            # Check that calls include URLs for filtered services only
            calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("AWA UI:" in call for call in calls)
            assert any("AWA Docs:" in call for call in calls)
            assert any("AWA API:" in call for call in calls)
            # Should NOT include temporal URLs
            assert not any("Temporal UI:" in call for call in calls)
            assert not any("Temporal Server:" in call for call in calls)
            assert not any("Temporal Metrics:" in call for call in calls)

    @pytest.mark.asyncio
    async def test_display_service_urls_single_service(self) -> None:
        """Test display_service_urls with single service filter."""
        manager = await ServiceManager.create()

        with patch.object(manager, "logger") as mock_logger:
            # Only show temporal server
            manager.display_service_urls([constants.SERVICE_TEMPORAL_SERVER])

            # Should log the header plus temporal entries (3) = 4 total
            assert mock_logger.info.call_count == 4
            mock_logger.info.assert_any_call("Services running!")

            # Check that calls include URLs for temporal server only
            calls = [call.args[0] for call in mock_logger.info.call_args_list]
            assert any("Temporal UI:" in call for call in calls)
            assert any("Temporal Server:" in call for call in calls)
            assert any("Temporal Metrics:" in call for call in calls)
            # Should NOT include UI/API URLs
            assert not any("AWA UI:" in call for call in calls)
            assert not any("AWA Docs:" in call for call in calls)
            assert not any("AWA API:" in call for call in calls)

    @pytest.mark.timeout(30)
    @pytest.mark.asyncio
    async def test_ensure_all_services_running_with_service_filter(self) -> None:
        """Test ensure_all_services_running with services parameter."""
        manager = await ServiceManager.create()

        # Mock check_all_services to return different statuses on subsequent calls
        initial_status = {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: False,
            constants.SERVICE_UI: True,
        }

        # After services are started, API should be running
        final_status = {
            constants.SERVICE_TEMPORAL_SERVER: False,  # Still not running (not requested)
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: True,  # Now running
            constants.SERVICE_UI: True,
        }

        with (
            patch.object(
                manager,
                "check_all_services",
                new=AsyncMock(side_effect=[initial_status, initial_status, final_status]),
            ),
            patch.object(manager, "start_missing_services", new=AsyncMock(return_value=True)),
        ):
            # Only try to start API service
            result = await manager.ensure_all_services_running(services=[constants.SERVICE_API])

            # Should return started status only for requested service
            assert constants.SERVICE_API in result
            assert result[constants.SERVICE_API] is True  # Was started (was False, now True)

            # start_missing_services should be called with modified status
            # where non-requested services are marked as already running
            manager.start_missing_services.assert_called()
            called_status = manager.start_missing_services.call_args[0][0]

            # API should still be False (needs starting)
            assert called_status[constants.SERVICE_API] is False
            # Other services should be set to True (don't start them)
            assert called_status[constants.SERVICE_TEMPORAL_SERVER] is True
            assert called_status[constants.SERVICE_TEMPORAL_WORKER] is True
            assert called_status[constants.SERVICE_UI] is True

    @pytest.mark.asyncio
    async def test_ensure_all_services_running_no_filter(self) -> None:
        """Test ensure_all_services_running without services parameter (all services)."""
        manager = await ServiceManager.create()

        # Mock all services as already running
        status = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        with patch.object(manager, "check_all_services", new=AsyncMock(return_value=status)):
            result = await manager.ensure_all_services_running()

            # Should return started status for all services (all False since already running)
            assert len(result) == 4
            assert all(not started for started in result.values())

    @pytest.mark.asyncio
    async def test_rollback_started_services_success(self) -> None:
        """Test rollback_started_services successfully stops services."""
        manager = await ServiceManager.create()

        # Add some mock processes to track
        manager.service_processes[constants.SERVICE_API] = MagicMock()
        manager.service_processes[constants.SERVICE_UI] = MagicMock()

        with (
            patch.object(manager.state_manager, "stop_service", new=AsyncMock(return_value=True)),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager.rollback_started_services([constants.SERVICE_API, constants.SERVICE_UI])

            # Should call stop_service for each service
            assert manager.state_manager.stop_service.call_count == 2
            manager.state_manager.stop_service.assert_any_call(constants.SERVICE_API)
            manager.state_manager.stop_service.assert_any_call(constants.SERVICE_UI)

            # Should remove from tracking
            assert constants.SERVICE_API not in manager.service_processes
            assert constants.SERVICE_UI not in manager.service_processes

            # Should log success messages
            mock_logger.info.assert_any_call(f"Successfully stopped {constants.SERVICE_API} during rollback")
            mock_logger.info.assert_any_call(f"Successfully stopped {constants.SERVICE_UI} during rollback")

    @pytest.mark.asyncio
    async def test_rollback_started_services_empty_list(self) -> None:
        """Test rollback_started_services with empty list does nothing."""
        manager = await ServiceManager.create()

        with patch.object(manager.state_manager, "stop_service", new=AsyncMock()) as mock_stop:
            await manager.rollback_started_services([])

            # Should not call stop_service
            mock_stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_rollback_started_services_failure(self) -> None:
        """Test rollback_started_services when stop_service fails."""
        manager = await ServiceManager.create()

        with (
            patch.object(manager.state_manager, "stop_service", new=AsyncMock(return_value=False)),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager.rollback_started_services([constants.SERVICE_API])

            # Should call stop_service
            manager.state_manager.stop_service.assert_called_once_with(constants.SERVICE_API)

            # Should log error message
            mock_logger.error.assert_any_call(f"Failed to stop {constants.SERVICE_API} during rollback")

    @pytest.mark.asyncio
    async def test_rollback_started_services_exception(self) -> None:
        """Test rollback_started_services when an exception occurs."""
        manager = await ServiceManager.create()

        with (
            patch.object(manager.state_manager, "stop_service", new=AsyncMock(side_effect=Exception("Test error"))),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager.rollback_started_services([constants.SERVICE_API])

            # Should log exception message
            mock_logger.exception.assert_any_call(f"Error stopping {constants.SERVICE_API} during rollback")

    # Test __init__ method
    def test_init(self) -> None:
        """Test ServiceManager initialization."""
        with (
            patch("awa.core.cli.service_manager.get_logger") as mock_get_logger,
            patch("awa.core.cli.service_manager.StateManager") as mock_state,
        ):
            manager = ServiceManager()

            # Check that all components are initialized
            mock_get_logger.assert_called_once()
            mock_state.assert_called_once()

            # Check initial state
            assert manager.temporal_client is None
            assert manager.temporal_worker is None
            assert manager.service_processes == {}
            assert manager.background_tasks == {}
            assert manager.subprocess_transports == {}
            assert manager.service_startup_flags == {}

    # Test create class method
    @pytest.mark.asyncio
    async def test_create_with_terminate_all(self) -> None:
        """Test ServiceManager.create with terminate_all parameter."""
        with (
            patch("awa.core.cli.service_manager.TemporalClient.create") as mock_create,
            patch("awa.core.cli.service_manager.TemporalWorker") as mock_worker,
        ):
            mock_client = AsyncMock()
            mock_create.return_value = mock_client

            manager = await ServiceManager.create(terminate_all=True)

            # Should call TemporalClient.create with terminate_all=True
            mock_create.assert_called_once_with(terminate_all=True)
            mock_worker.assert_called_once_with(mock_client)

            assert manager.temporal_client is mock_client
            assert manager.temporal_worker is mock_worker.return_value

    # Test _async_init method
    @pytest.mark.asyncio
    async def test_async_init(self) -> None:
        """Test ServiceManager._async_init method."""
        with (
            patch("awa.core.cli.service_manager.TemporalClient.create") as mock_create,
            patch("awa.core.cli.service_manager.TemporalWorker") as mock_worker,
        ):
            mock_client = AsyncMock()
            mock_create.return_value = mock_client

            manager = ServiceManager()
            await manager._async_init(terminate_all=True)

            mock_create.assert_called_once_with(terminate_all=True)
            mock_worker.assert_called_once_with(mock_client)

    # Test check_all_services edge cases
    @pytest.mark.asyncio
    async def test_check_all_services_not_initialized(self) -> None:
        """Test check_all_services when temporal_worker is None."""
        manager = ServiceManager()

        with pytest.raises(RuntimeError, match="ServiceManager not properly initialized"):
            await manager.check_all_services()

    @pytest.mark.asyncio
    async def test_check_all_services_temporal_server_down(self) -> None:
        """Test check_all_services when temporal server external health check fails."""
        manager = await ServiceManager.create()

        # Mock PID validation to pass, but external health check to fail
        with (
            patch.object(manager, "validate_service_process", new=AsyncMock(return_value=True)),
            patch.object(
                manager,
                "_perform_external_health_check",
                new=AsyncMock(
                    side_effect=lambda service, **_: service != constants.SERVICE_TEMPORAL_SERVER,
                ),
            ),
        ):
            result = await manager.check_all_services()

            assert result == {
                constants.SERVICE_TEMPORAL_SERVER: False,  # External health check failed
                constants.SERVICE_TEMPORAL_WORKER: True,  # External health check passed
                constants.SERVICE_API: True,  # External health check passed
                constants.SERVICE_UI: True,  # External health check passed
            }

    # Test _start_service_subprocess method
    @pytest.mark.asyncio
    async def test_start_service_subprocess_success(self) -> None:
        """Test _start_service_subprocess successful execution."""
        manager = await ServiceManager.create()

        # Mock process with PID
        mock_process = AsyncMock()
        mock_process.pid = 12345

        # Mock async generator
        async def mock_stream_gen() -> AsyncGenerator[object, None]:
            yield mock_process
            yield "Process output line 1"
            yield "Process output line 2"

        mock_gen = mock_stream_gen()

        with (
            patch("awa.core.cli.service_manager.CommandUtils.stream_command_async", return_value=mock_gen),
            patch.object(manager.state_manager, "update_service", new=AsyncMock()),
            patch("awa.core.cli.service_manager.get_subprocess_logger"),
            patch("asyncio.create_task") as mock_task,
        ):

            def close_coroutine_and_return_task(coro: object) -> AsyncMock:
                if hasattr(coro, "close"):
                    coro.close()
                task = AsyncMock()
                return task

            mock_task.side_effect = close_coroutine_and_return_task

            result = await manager._start_service_subprocess(
                "test_service",
                "test command",
                port=8080,
                env_vars={"TEST_VAR": "test_value"},
                detach=False,
            )

            assert result is True
            assert "test_service" in manager.service_processes
            assert manager.service_processes["test_service"] is mock_process

            # Should create background task for output consumption
            mock_task.assert_called_once()

            # Should update service state
            manager.state_manager.update_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_service_subprocess_no_pid(self) -> None:
        """Test _start_service_subprocess when process has no PID."""
        manager = await ServiceManager.create()

        # Mock process without PID
        mock_process = AsyncMock()
        mock_process.pid = None

        # Mock async generator
        async def mock_stream_gen() -> AsyncGenerator[object, None]:
            yield mock_process

        mock_gen = mock_stream_gen()

        with (
            patch("awa.core.cli.service_manager.CommandUtils.stream_command_async", return_value=mock_gen),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager._start_service_subprocess(
                "test_service",
                "test command",
            )

            assert result is False
            mock_logger.error.assert_called_with("Failed to get PID for test_service")

    @pytest.mark.asyncio
    async def test_start_service_subprocess_with_env_vars(self) -> None:
        """Test _start_service_subprocess with environment variables."""
        manager = await ServiceManager.create()

        # Mock process with PID
        mock_process = AsyncMock()
        mock_process.pid = 12345

        # Mock async generator
        async def mock_stream_gen() -> AsyncGenerator[object, None]:
            yield mock_process

        mock_gen = mock_stream_gen()

        original_env = os.environ.copy()

        try:
            with (
                patch("awa.core.cli.service_manager.CommandUtils.stream_command_async", return_value=mock_gen),
                patch.object(manager.state_manager, "update_service", new=AsyncMock()),
                patch("awa.core.cli.service_manager.get_subprocess_logger"),
                patch("asyncio.create_task") as mock_task,
            ):

                def close_coroutine_and_return_task(coro: object) -> AsyncMock:
                    if hasattr(coro, "close"):
                        coro.close()
                    task = AsyncMock()
                    return task

                mock_task.side_effect = close_coroutine_and_return_task

                # Set initial environment variable
                os.environ["TEST_VAR"] = "original_value"

                result = await manager._start_service_subprocess(
                    "test_service",
                    "test command",
                    env_vars={"TEST_VAR": "new_value", "NEW_VAR": "new_value"},
                )

                assert result is True

                # Environment should be restored
                assert os.environ["TEST_VAR"] == "original_value"
                assert "NEW_VAR" not in os.environ
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    @pytest.mark.asyncio
    async def test_start_service_subprocess_exception(self) -> None:
        """Test _start_service_subprocess when exception occurs."""
        manager = await ServiceManager.create()

        with (
            patch(
                "awa.core.cli.service_manager.CommandUtils.stream_command_async",
                side_effect=Exception("Test error"),
            ),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager._start_service_subprocess(
                "test_service",
                "test command",
            )

            assert result is False
            mock_logger.exception.assert_called_with("Failed to start test_service")

    # Test _consume_process_output method
    @pytest.mark.asyncio
    async def test_consume_process_output(self) -> None:
        """Test _consume_process_output method."""
        manager = await ServiceManager.create()

        # Mock async generator
        async def mock_output_gen() -> AsyncGenerator[str, None]:
            yield "Line 1\n"
            yield "Line 2\n"
            yield "Line 3\n"

        mock_subprocess_logger = MagicMock()

        with patch("awa.core.cli.service_manager.get_subprocess_logger", return_value=mock_subprocess_logger):
            await manager._consume_process_output(mock_output_gen(), "test_service")

            # Should call subprocess logger for each line
            assert mock_subprocess_logger.info.call_count == 3
            mock_subprocess_logger.info.assert_any_call("Line 1")
            mock_subprocess_logger.info.assert_any_call("Line 2")
            mock_subprocess_logger.info.assert_any_call("Line 3")

    @pytest.mark.asyncio
    async def test_consume_process_output_exception(self) -> None:
        """Test _consume_process_output when exception occurs."""
        manager = await ServiceManager.create()

        # Mock async generator that raises exception
        async def mock_output_gen() -> AsyncGenerator[str, None]:
            yield "Line 1\n"
            raise RuntimeError("Test error")

        with (
            patch("awa.core.cli.service_manager.get_subprocess_logger"),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager._consume_process_output(mock_output_gen(), "test_service")

            mock_logger.warning.assert_called_with("Output consumption stopped for test_service: Test error")

    # Test _ensure_temporal_components_initialized method
    def test_ensure_temporal_components_initialized_success(self) -> None:
        """Test _ensure_temporal_components_initialized when components are initialized."""
        manager = ServiceManager()
        manager.temporal_client = AsyncMock()
        manager.temporal_worker = AsyncMock()

        # Should not raise exception
        manager._ensure_temporal_components_initialized()

    def test_ensure_temporal_components_initialized_no_worker(self) -> None:
        """Test _ensure_temporal_components_initialized when temporal_worker is None."""
        manager = ServiceManager()
        manager.temporal_client = AsyncMock()
        manager.temporal_worker = None

        with pytest.raises(RuntimeError, match="ServiceManager not properly initialized"):
            manager._ensure_temporal_components_initialized()

    def test_ensure_temporal_components_initialized_no_client(self) -> None:
        """Test _ensure_temporal_components_initialized when temporal_client is None."""
        manager = ServiceManager()
        manager.temporal_client = None
        manager.temporal_worker = AsyncMock()

        with pytest.raises(RuntimeError, match="ServiceManager not properly initialized"):
            manager._ensure_temporal_components_initialized()

    # Test ensure_all_services_running failure scenarios
    @pytest.mark.asyncio
    async def test_ensure_all_services_running_startup_failure(self) -> None:
        """Test ensure_all_services_running when service startup fails."""
        manager = await ServiceManager.create()

        # Mock services as not running
        status = {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_TEMPORAL_WORKER: False,
            constants.SERVICE_API: False,
            constants.SERVICE_UI: False,
        }

        with (
            patch.object(manager, "check_all_services", new=AsyncMock(return_value=status)),
            patch.object(manager, "start_missing_services", new=AsyncMock(return_value=False)),
            patch.object(manager, "logger") as mock_logger,
        ):
            with pytest.raises(RuntimeError, match="Service startup failed"):
                await manager.ensure_all_services_running()

            mock_logger.error.assert_called_with("Failed to start all services, aborting startup")

    # Test start_missing_services method
    @pytest.mark.asyncio
    async def test_start_missing_services_temporal_server_failure(self) -> None:
        """Test start_missing_services when temporal server fails to start."""
        manager = await ServiceManager.create()

        status = {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        with (
            patch.object(manager, "_start_service_subprocess", new=AsyncMock(side_effect=[False])),
            patch.object(manager, "rollback_started_services", new=AsyncMock()),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager.start_missing_services(status)

            assert result is False
            mock_logger.error.assert_called_with("Failed to start Temporal server")
            manager.rollback_started_services.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_start_missing_services_temporal_worker_failure(self) -> None:
        """Test start_missing_services when temporal worker fails to start."""
        manager = await ServiceManager.create()

        status = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_TEMPORAL_WORKER: False,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        with (
            patch.object(manager, "_start_service_subprocess", new=AsyncMock(return_value=False)),
            patch.object(manager, "rollback_started_services", new=AsyncMock()),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager.start_missing_services(status)

            assert result is False
            mock_logger.error.assert_called_with("Failed to start Temporal worker")
            manager.rollback_started_services.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_start_missing_services_api_failure(self) -> None:
        """Test start_missing_services when API fails to start."""
        manager = await ServiceManager.create()

        status = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: False,
            constants.SERVICE_UI: True,
        }

        with (
            patch.object(manager, "_start_service_subprocess", new=AsyncMock(return_value=False)),
            patch.object(manager, "rollback_started_services", new=AsyncMock()),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager.start_missing_services(status)

            assert result is False
            mock_logger.error.assert_called_with("Failed to start API service")
            manager.rollback_started_services.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_start_missing_services_ui_failure(self) -> None:
        """Test start_missing_services when UI fails to start."""
        manager = await ServiceManager.create()

        status = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: False,
        }

        with (
            patch.object(manager, "_start_service_subprocess", new=AsyncMock(return_value=False)),
            patch.object(manager, "rollback_started_services", new=AsyncMock()),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager.start_missing_services(status, ui_mode=UIMode.DEV)

            assert result is False
            mock_logger.error.assert_called_with("Failed to start UI service")
            manager.rollback_started_services.assert_called_once_with([])

    @pytest.mark.asyncio
    async def test_start_missing_services_temporal_worker_with_terminate_all(self) -> None:
        """Test start_missing_services when temporal worker needs terminate_all update."""
        manager = await ServiceManager.create()
        manager.temporal_client.terminate_all = False

        status = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_TEMPORAL_WORKER: False,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        with (
            patch("awa.core.cli.service_manager.TemporalClient.create") as mock_create,
            patch("awa.core.cli.service_manager.TemporalWorker") as mock_worker,
            patch.object(manager, "_start_service_subprocess", new=AsyncMock(return_value=True)),
        ):
            mock_new_client = AsyncMock()
            mock_create.return_value = mock_new_client

            result = await manager.start_missing_services(status, terminate_all=True)

            assert result is True
            mock_create.assert_called_once_with(terminate_all=True)
            mock_worker.assert_called_with(mock_new_client)

    @pytest.mark.asyncio
    async def test_start_missing_services_ui_mode_none(self) -> None:
        """Test start_missing_services with UI mode NONE."""
        manager = await ServiceManager.create()

        status = {
            constants.SERVICE_TEMPORAL_SERVER: True,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: False,
        }

        result = await manager.start_missing_services(status, ui_mode=UIMode.NONE)

        # Should succeed without starting UI
        assert result is True

    @pytest.mark.asyncio
    async def test_start_missing_services_exception(self) -> None:
        """Test start_missing_services when exception occurs."""
        manager = await ServiceManager.create()

        status = {
            constants.SERVICE_TEMPORAL_SERVER: False,
            constants.SERVICE_TEMPORAL_WORKER: True,
            constants.SERVICE_API: True,
            constants.SERVICE_UI: True,
        }

        with (
            patch.object(
                manager,
                "_start_service_subprocess",
                new=AsyncMock(side_effect=Exception("Test error")),
            ),
            patch.object(manager, "rollback_started_services", new=AsyncMock()),
            patch.object(manager, "logger") as mock_logger,
        ):
            result = await manager.start_missing_services(status)

            assert result is False
            mock_logger.exception.assert_called_with("Error during service startup")
            manager.rollback_started_services.assert_called_once_with([])

    # Test execute_workflow method
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self) -> None:
        """Test execute_workflow successful execution."""
        manager = await ServiceManager.create()

        mock_result = {"success": True, "result": "test_result"}
        manager.temporal_client.execute_workflow = AsyncMock(return_value=mock_result)

        result = await manager.execute_workflow(
            workflow="test_workflow",
            workflow_input='{"key": "value"}',
            task_queue="test_queue",
        )

        assert result == mock_result
        manager.temporal_client.execute_workflow.assert_called_once_with(
            workflow="test_workflow",
            workflow_input='{"key": "value"}',
            task_queue="test_queue",
        )

    @pytest.mark.asyncio
    async def test_execute_workflow_not_initialized(self) -> None:
        """Test execute_workflow when temporal_client is None."""
        manager = ServiceManager()

        with pytest.raises(RuntimeError, match="ServiceManager not properly initialized"):
            await manager.execute_workflow("test_workflow")

    # Test stop_services method
    @pytest.mark.asyncio
    async def test_stop_services_success(self) -> None:
        """Test stop_services successful execution."""
        manager = await ServiceManager.create()

        # Add mock processes
        manager.service_processes[constants.SERVICE_TEMPORAL_SERVER] = MagicMock()
        manager.service_processes[constants.SERVICE_TEMPORAL_WORKER] = MagicMock()
        manager.service_processes[constants.SERVICE_API] = MagicMock()
        manager.service_processes[constants.SERVICE_UI] = MagicMock()

        # Mock service info exists
        mock_service_info = ServiceInfo(
            pid=12345,
            port=8001,
            started_at=datetime.now(UTC),
        )

        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=mock_service_info)),
            patch.object(manager.state_manager, "stop_service", new=AsyncMock(return_value=True)),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager.stop_services(stop_temporal=True, stop_api=True, stop_ui=True)

            # Should call stop_service for each service
            assert manager.state_manager.stop_service.call_count == 4

            # Should remove from tracking
            assert constants.SERVICE_TEMPORAL_SERVER not in manager.service_processes
            assert constants.SERVICE_TEMPORAL_WORKER not in manager.service_processes
            assert constants.SERVICE_API not in manager.service_processes
            assert constants.SERVICE_UI not in manager.service_processes

            # Should update flags (service_startup_flags are managed by _set_service_startup_flag)
            # Note: Flags are set to False during service stop in the actual implementation

            # Should log success
            expected_services = [
                constants.SERVICE_TEMPORAL_WORKER,
                constants.SERVICE_TEMPORAL_SERVER,
                constants.SERVICE_API,
                constants.SERVICE_UI,
            ]
            mock_logger.info.assert_called_with(
                f"Successfully stopped services: {expected_services}",
            )

    @pytest.mark.asyncio
    async def test_stop_services_partial_stop(self) -> None:
        """Test stop_services with partial service stopping."""
        manager = await ServiceManager.create()

        # Add mock processes
        manager.service_processes[constants.SERVICE_API] = MagicMock()

        # Mock service info exists
        mock_service_info = ServiceInfo(
            pid=12345,
            port=8001,
            started_at=datetime.now(UTC),
        )

        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=mock_service_info)),
            patch.object(manager.state_manager, "stop_service", new=AsyncMock(return_value=True)),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager.stop_services(stop_api=True)

            # Should only call stop_service for API
            manager.state_manager.stop_service.assert_called_once_with(constants.SERVICE_API)

            # Should remove API from tracking
            assert constants.SERVICE_API not in manager.service_processes

            # Should update API flag only (service_startup_flags are managed by _set_service_startup_flag)
            # Note: Flags are set to False during service stop in the actual implementation

            # Should log success
            mock_logger.info.assert_called_with(f"Successfully stopped services: ['{constants.SERVICE_API}']")

    @pytest.mark.asyncio
    async def test_stop_services_no_service_info(self) -> None:
        """Test stop_services when service info doesn't exist."""
        manager = await ServiceManager.create()

        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(return_value=None)),
            patch.object(manager.state_manager, "stop_service", new=AsyncMock()) as mock_stop,
        ):
            await manager.stop_services(stop_api=True)

            # Should not call stop_service
            mock_stop.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_services_exception(self) -> None:
        """Test stop_services when exception occurs."""
        manager = await ServiceManager.create()

        with (
            patch.object(manager.state_manager, "get_service_info", new=AsyncMock(side_effect=Exception("Test error"))),
            patch.object(manager, "logger") as mock_logger,
        ):
            await manager.stop_services(stop_api=True)

            mock_logger.exception.assert_called_with("Error stopping services")

    # Test stop_all_services method
    @pytest.mark.asyncio
    async def test_stop_all_services(self) -> None:
        """Test stop_all_services delegates to state_manager."""
        manager = await ServiceManager.create()

        mock_stopped_services = [constants.SERVICE_API, constants.SERVICE_UI]

        with patch.object(
            manager.state_manager,
            "stop_all_services",
            new=AsyncMock(return_value=mock_stopped_services),
        ):
            result = await manager.stop_all_services()

            assert result == mock_stopped_services
            manager.state_manager.stop_all_services.assert_called_once()
