import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.engine.temporal_server import TemporalServer


@pytest.fixture
def mock_config() -> MagicMock:
    """Mock configuration for testing."""
    config = MagicMock()
    config.model_dump_json.return_value = '{"test": "config"}'
    return config


@pytest.fixture
def mock_env_config() -> MagicMock:
    """Mock environment configuration for testing."""
    env_config = MagicMock()
    env_config.temporal_ui_port = 8002
    env_config.temporal_server_port = 7233
    env_config.temporal_metrics_port = 8004
    env_config.temporal_server_host = "localhost"
    env_config.temporal_namespace = "default"
    return env_config


@pytest.fixture
def mock_logger() -> MagicMock:
    """Mock logger for testing."""
    return MagicMock()


@pytest.fixture
def temporal_server(mock_config: MagicMock, mock_logger: MagicMock) -> TemporalServer:
    """Create a TemporalServer instance with mocked dependencies."""
    with (
        patch("awa.core.engine.temporal_server.ConfigLoader.get_config", return_value=mock_config),
        patch("awa.core.engine.temporal_server.get_logger", return_value=mock_logger),
    ):
        server = TemporalServer()
        server.logger = mock_logger
        return server


class TestTemporalServerInitialization:
    """Test TemporalServer initialization."""

    def test_init_creates_required_attributes(self, temporal_server: TemporalServer) -> None:
        """Test that __init__ creates all required attributes."""
        assert hasattr(temporal_server, "server_started_event")
        assert isinstance(temporal_server.server_started_event, asyncio.Event)
        assert hasattr(temporal_server, "logger")
        assert hasattr(temporal_server, "config")
        assert hasattr(temporal_server, "_server_task")
        assert hasattr(temporal_server, "_temporal_proc")
        assert temporal_server._server_task is None
        assert temporal_server._temporal_proc is None

    def test_init_logs_config(self, mock_config: MagicMock, mock_logger: MagicMock) -> None:
        """Test that __init__ logs the configuration."""
        mock_config.model_dump_json.return_value = '{"test": "config"}'
        with (
            patch("awa.core.engine.temporal_server.ConfigLoader.get_config", return_value=mock_config),
            patch("awa.core.engine.temporal_server.get_logger", return_value=mock_logger),
        ):
            TemporalServer()
            mock_logger.debug.assert_called_once()
            assert "CONFIG" in mock_logger.debug.call_args[0][0]


@pytest.mark.asyncio
class TestTemporalServerStatusChecking:
    """Test TemporalServer service status checking."""

    async def test_check_service_status_server_running(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test check_service_status when server is running."""
        with (
            patch("awa.core.engine.temporal_server.Client.connect") as mock_connect,
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            mock_connect.return_value = None
            result = await temporal_server.check_service_status()
            assert result is True
            mock_connect.assert_called_once_with(
                "localhost:7233",
                namespace="default",
            )

    async def test_check_service_status_server_not_running_connection_refused(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test check_service_status when server is not running (ConnectionRefusedError)."""
        with (
            patch("awa.core.engine.temporal_server.Client.connect", side_effect=ConnectionRefusedError),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            result = await temporal_server.check_service_status()
            assert result is False

    async def test_check_service_status_server_not_running_os_error(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test check_service_status when server is not running (OSError)."""
        with (
            patch("awa.core.engine.temporal_server.Client.connect", side_effect=OSError),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            result = await temporal_server.check_service_status()
            assert result is False

    async def test_check_service_status_server_not_running_runtime_error(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test check_service_status when server is not running (RuntimeError)."""
        with (
            patch("awa.core.engine.temporal_server.Client.connect", side_effect=RuntimeError),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            result = await temporal_server.check_service_status()
            assert result is False

    async def test_check_service_status_sets_server_started_event(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test that check_service_status sets the server_started_event when server is running."""
        with (
            patch("awa.core.engine.temporal_server.Client.connect") as mock_connect,
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            mock_connect.return_value = None
            # Ensure event is not set initially
            temporal_server.server_started_event.clear()
            assert not temporal_server.server_started_event.is_set()

            result = await temporal_server.check_service_status()
            assert result is True
            assert temporal_server.server_started_event.is_set()


@pytest.mark.asyncio
class TestTemporalServerStartStop:
    """Test TemporalServer start and stop operations."""

    async def test_start_server_when_not_running(self, temporal_server: TemporalServer) -> None:
        """Test start_server when server is not running."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch("asyncio.create_task") as mock_create_task,
            patch.object(temporal_server.server_started_event, "wait", new_callable=AsyncMock) as mock_wait,
        ):
            mock_check_status.return_value = False

            def close_coroutine_and_return_task(coro: object) -> AsyncMock:
                if hasattr(coro, "close"):
                    coro.close()
                task = AsyncMock()
                task.done.return_value = True
                return task

            mock_create_task.side_effect = close_coroutine_and_return_task

            await temporal_server.start_server()

            mock_check_status.assert_called_once()
            mock_create_task.assert_called_once()
            mock_wait.assert_called_once()

    async def test_start_server_when_already_running(self, temporal_server: TemporalServer) -> None:
        """Test start_server when server is already running."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch("asyncio.create_task") as mock_create_task,
            patch.object(temporal_server.server_started_event, "wait", new_callable=AsyncMock) as mock_wait,
        ):
            mock_check_status.return_value = True

            def close_coroutine_and_return_task(coro: object) -> AsyncMock:
                if hasattr(coro, "close"):
                    coro.close()
                task = AsyncMock()
                return task

            mock_create_task.side_effect = close_coroutine_and_return_task

            await temporal_server.start_server()

            mock_check_status.assert_called_once()
            mock_create_task.assert_not_called()
            mock_wait.assert_not_called()

    async def test_start_server_with_existing_task_not_done(self, temporal_server: TemporalServer) -> None:
        """Test start_server when there's an existing task that's not done."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch("asyncio.create_task") as mock_create_task,
            patch.object(temporal_server.server_started_event, "wait", new_callable=AsyncMock) as mock_wait,
        ):
            # Server not running but existing task is not done - should not create new task
            mock_check_status.return_value = False

            def close_coroutine_and_return_task(coro: object) -> AsyncMock:
                if hasattr(coro, "close"):
                    coro.close()
                task = AsyncMock()
                return task

            mock_create_task.side_effect = close_coroutine_and_return_task
            mock_task = MagicMock()
            mock_task.done.return_value = False
            temporal_server._server_task = mock_task

            await temporal_server.start_server()

            mock_check_status.assert_called_once()
            mock_create_task.assert_not_called()
            mock_wait.assert_not_called()

    async def test_stop_server_no_task(self, temporal_server: TemporalServer) -> None:
        """Test stop_server when there's no task."""
        temporal_server._server_task = None

        await temporal_server.stop_server()

        temporal_server.logger.info.assert_called()

    async def test_stop_server_with_done_task(self, temporal_server: TemporalServer) -> None:
        """Test stop_server with a done task."""
        mock_task = MagicMock()
        mock_task.done.return_value = True
        temporal_server._server_task = mock_task

        await temporal_server.stop_server()

        mock_task.cancel.assert_not_called()
        temporal_server.logger.info.assert_called()


@pytest.mark.asyncio
class TestTemporalServerHighLevelOperations:
    """Test TemporalServer high-level operations."""

    async def test_start_temporal_server_success(self, temporal_server: TemporalServer) -> None:
        """Test start_temporal_server when everything succeeds."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch.object(temporal_server, "start_server", new_callable=AsyncMock) as mock_start_server,
        ):
            mock_check_status.return_value = False

            await temporal_server.start_temporal_server()

            mock_check_status.assert_called_once()
            mock_start_server.assert_called_once()

    async def test_start_temporal_server_already_running(self, temporal_server: TemporalServer) -> None:
        """Test start_temporal_server when server is already running."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch.object(temporal_server, "start_server", new_callable=AsyncMock) as mock_start_server,
        ):
            mock_check_status.return_value = True

            await temporal_server.start_temporal_server()

            mock_check_status.assert_called_once()
            mock_start_server.assert_not_called()

    async def test_start_temporal_server_with_exception(self, temporal_server: TemporalServer) -> None:
        """Test start_temporal_server handles exceptions and cleans up."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch.object(temporal_server, "start_server", new_callable=AsyncMock) as mock_start_server,
            patch.object(temporal_server, "stop_temporal_server", new_callable=AsyncMock) as mock_stop_server,
        ):
            mock_check_status.return_value = False
            mock_start_server.side_effect = Exception("Test exception")

            with pytest.raises(Exception, match="Test exception"):
                await temporal_server.start_temporal_server()

            mock_check_status.assert_called_once()
            mock_start_server.assert_called_once()
            mock_stop_server.assert_called_once()

    async def test_stop_temporal_server_success(self, temporal_server: TemporalServer) -> None:
        """Test stop_temporal_server when everything succeeds."""
        with patch.object(temporal_server, "stop_server", new_callable=AsyncMock) as mock_stop_server:
            await temporal_server.stop_temporal_server()

            mock_stop_server.assert_called_once()
            temporal_server.logger.info.assert_called_with("Temporal server shutdown complete")

    async def test_stop_temporal_server_with_exception(self, temporal_server: TemporalServer) -> None:
        """Test stop_temporal_server handles exceptions and continues cleanup."""
        with patch.object(temporal_server, "stop_server", new_callable=AsyncMock) as mock_stop_server:
            mock_stop_server.side_effect = Exception("Test exception")
            mock_task = MagicMock()
            mock_task.cancel = MagicMock()
            temporal_server._server_task = mock_task

            await temporal_server.stop_temporal_server()

            mock_stop_server.assert_called_once()
            temporal_server.logger.exception.assert_called_with("Error stopping server")
            assert not temporal_server.server_started_event.is_set()
            mock_task.cancel.assert_called_once()


@pytest.mark.asyncio
class TestTemporalServerEdgeCases:
    """Test TemporalServer edge cases and error conditions."""

    async def test_start_server_with_existing_done_task(self, temporal_server: TemporalServer) -> None:
        """Test start_server when there's an existing task that's done."""
        with (
            patch.object(temporal_server, "check_service_status", new_callable=AsyncMock) as mock_check_status,
            patch("asyncio.create_task") as mock_create_task,
            patch.object(temporal_server.server_started_event, "wait", new_callable=AsyncMock) as mock_wait,
        ):
            mock_check_status.return_value = False
            mock_task = MagicMock()
            mock_task.done.return_value = True
            temporal_server._server_task = mock_task

            new_task = MagicMock()

            def close_coroutine_and_return_task(coro: object) -> AsyncMock:
                if hasattr(coro, "close"):
                    coro.close()
                return new_task

            mock_create_task.side_effect = close_coroutine_and_return_task

            await temporal_server.start_server()

            mock_check_status.assert_called_once()
            mock_create_task.assert_called_once()
            mock_wait.assert_called_once()
            assert temporal_server._server_task == new_task

    async def test_stop_temporal_server_clears_task_on_exception(self, temporal_server: TemporalServer) -> None:
        """Test stop_temporal_server clears task reference even on exception."""
        with patch.object(temporal_server, "stop_server", new_callable=AsyncMock) as mock_stop_server:
            mock_stop_server.side_effect = Exception("Test exception")
            mock_task = MagicMock()
            mock_task.cancel = MagicMock()
            temporal_server._server_task = mock_task

            await temporal_server.stop_temporal_server()

            # Verify cleanup still happened
            assert not temporal_server.server_started_event.is_set()
            mock_task.cancel.assert_called_once()

    async def test_command_construction_from_env_config(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test that _temporal_server constructs the correct command from env config."""
        command_captured = None

        async def mock_stream_command_async(
            command: str,
            *_args: object,
            **_kwargs: object,
        ) -> AsyncGenerator[object, None]:
            nonlocal command_captured
            command_captured = command
            yield MagicMock()  # First yield is the process

        with (
            patch(
                "awa.core.engine.temporal_server.CommandUtils.stream_command_async",
                side_effect=mock_stream_command_async,
            ),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            # Start the server task - it should complete normally
            await temporal_server._temporal_server()

            # Verify the command was constructed correctly
            expected_command = (
                f"temporal server start-dev --ui-port {mock_env_config.temporal_ui_port} "
                f"--port {mock_env_config.temporal_server_port} "
                f"--metrics-port {mock_env_config.temporal_metrics_port} "
                f"--db-filename temporal.db"
            )
            assert command_captured == expected_command

    async def test_temporal_server_sets_proc_reference(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test _temporal_server sets process reference correctly."""
        mock_proc = MagicMock()

        async def mock_stream_command_async(*_args: object, **_kwargs: object) -> AsyncGenerator[object, None]:
            yield mock_proc  # First yield is the process

        with (
            patch(
                "awa.core.engine.temporal_server.CommandUtils.stream_command_async",
                side_effect=mock_stream_command_async,
            ),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            # Start the server task - it should complete normally
            await temporal_server._temporal_server()

            # Verify _temporal_proc was cleared after completion
            assert temporal_server._temporal_proc is None

    async def test_temporal_server_sets_event_on_output(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test _temporal_server sets server_started_event on output."""
        mock_proc = MagicMock()

        async def mock_stream_command_async(*_args: object, **_kwargs: object) -> AsyncGenerator[object, None]:
            yield mock_proc  # First yield is the process
            yield "[Temporal] Server starting...\n"

        with (
            patch(
                "awa.core.engine.temporal_server.CommandUtils.stream_command_async",
                side_effect=mock_stream_command_async,
            ),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            # Ensure event is not set initially
            temporal_server.server_started_event.clear()

            # Start the server task - it should complete normally
            await temporal_server._temporal_server()

            # Verify server_started_event was set
            assert temporal_server.server_started_event.is_set()

    async def test_temporal_server_handles_cancelled_error(
        self,
        temporal_server: TemporalServer,
        mock_env_config: MagicMock,
    ) -> None:
        """Test _temporal_server handles CancelledError during execution."""
        mock_proc = MagicMock()
        mock_proc.terminate = MagicMock()
        mock_proc.wait = AsyncMock()

        async def mock_stream_command_async(*_args: object, **_kwargs: object) -> AsyncGenerator[object, None]:
            yield mock_proc  # First yield is the process
            yield "[Temporal] Server starting...\n"
            # Simulate CancelledError during iteration
            raise asyncio.CancelledError()

        with (
            patch(
                "awa.core.engine.temporal_server.CommandUtils.stream_command_async",
                side_effect=mock_stream_command_async,
            ),
            patch("awa.core.engine.temporal_server.EnvConfig.get_env_config", return_value=mock_env_config),
        ):
            # This should handle the CancelledError gracefully
            with pytest.raises(asyncio.CancelledError):
                await temporal_server._temporal_server()

            # Verify process was terminated
            mock_proc.terminate.assert_called_once()
            mock_proc.wait.assert_called_once()

            # Verify _temporal_proc was cleared
            assert temporal_server._temporal_proc is None
