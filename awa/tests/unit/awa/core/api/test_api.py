from __future__ import annotations

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from awa.core.api.api import Api, _run_api_server, start_api_server
from awa.core.models.config.env_config import EnvConfig

MINIMUM_ROUTES_COUNT = 2
EXPECTED_STOP_CALLS = 2


class TestApi:
    """Test case class for API functionality."""

    def test_api_initialization(self) -> None:
        """Test API initialization."""
        api = Api()
        assert api.app is not None
        assert api._server is None
        assert not api._shutdown_event.is_set()
        # Check that routes are included - FastAPI includes default routes plus our health router
        assert len(api.app.routes) >= MINIMUM_ROUTES_COUNT

    def test_setup_routes(self) -> None:
        """Test that routes are set up correctly."""
        api = Api()
        # Check that routes are included - FastAPI includes default routes plus our health router
        assert len(api.app.routes) >= MINIMUM_ROUTES_COUNT

    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    def test_versioned_health_endpoint(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test that the versioned health endpoint works correctly."""
        # Mock successful services
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance
        mock_get_pollers.return_value = ["worker1"]

        api = Api()
        client = TestClient(api.app)

        # Test the versioned health endpoint
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        expected_response = {
            "status": {
                "temporal_service": {"status": "up"},
                "temporal_worker": {"status": "up"},
            },
        }
        assert response.json() == expected_response

    def test_old_health_endpoint_not_accessible(self) -> None:
        """Test that the old unversioned health endpoint is no longer accessible."""
        api = Api()
        client = TestClient(api.app)

        # Test that old health endpoint returns 404
        response = client.get("/health")
        assert response.status_code == 404

    def test_shutdown_sets_event(self) -> None:
        """Test that shutdown sets the stop event."""
        api = Api()
        assert not api._shutdown_event.is_set()
        api.shutdown()
        assert api._shutdown_event.is_set()
        # Check that the event was set
        assert api._shutdown_event.is_set()

    @patch("awa.core.api.api.uvicorn.Config")
    @patch("awa.core.api.api.uvicorn.Server")
    @patch("awa.core.api.api.asyncio.new_event_loop")
    @patch("awa.core.api.api.asyncio.set_event_loop")
    # Remove missing fixture reference
    def test_run_server_config_creation(
        self,
        _mock_set_event_loop: MagicMock,
        mock_new_event_loop: MagicMock,
        mock_server_class: MagicMock,
        mock_config_class: MagicMock,
    ) -> None:
        """Test that run creates correct config and server instances."""
        # Arrange
        mock_loop = MagicMock()
        mock_new_event_loop.return_value = mock_loop
        mock_server = MagicMock()
        mock_server_class.return_value = mock_server

        api = Api()
        # Immediately trigger shutdown to prevent hanging
        api.shutdown()

        # Act
        api.run()

        # Assert
        mock_config_class.assert_called_once_with(
            api.app,
            host=EnvConfig.get_env_config().awa_api_host,
            port=EnvConfig.get_env_config().awa_api_port,
            log_level="info",
            log_config=unittest.mock.ANY,
            access_log=True,
        )
        mock_server_class.assert_called_once()

    @patch("awa.core.api.api.uvicorn.Config")
    @patch("awa.core.api.api.uvicorn.Server")
    @patch("awa.core.api.api.asyncio.new_event_loop")
    @patch("awa.core.api.api.asyncio.set_event_loop")
    @patch("awa.core.api.api.asyncio.sleep")
    # Remove missing fixture references
    def test_run_server_main_loop_and_shutdown(
        self,
        mock_sleep: MagicMock,
        _mock_set_event_loop: MagicMock,
        mock_new_event_loop: MagicMock,
        mock_server_class: MagicMock,
        _mock_config_class: MagicMock,
    ) -> None:
        """Test that the server cleanup happens correctly."""
        # Arrange
        api = Api()
        mock_loop = MagicMock()
        mock_new_event_loop.return_value = mock_loop

        # Create a simple non-async mock for the server
        mock_server = MagicMock()
        mock_server.serve = MagicMock()
        mock_server.should_exit = False
        mock_server_class.return_value = mock_server

        # Mock asyncio.sleep to return immediately without creating a coroutine
        mock_sleep.return_value = None

        # Make run_until_complete return immediately
        mock_loop.run_until_complete.return_value = None

        # Immediately trigger shutdown to prevent hanging
        api.shutdown()

        # Act
        api.run()

        # Assert cleanup happens
        assert mock_server.should_exit is True
        mock_loop.close.assert_called_once()

    @patch("awa.core.api.api.uvicorn.run")
    def test_run_docker(self, mock_uvicorn_run: MagicMock) -> None:
        """Test that run_docker calls uvicorn.run with the correct parameters."""
        # Arrange
        api = Api()

        # Act
        api.run_docker()

        # Assert
        mock_uvicorn_run.assert_called_once_with(
            api.app,
            host=EnvConfig.get_env_config().awa_api_host,
            port=EnvConfig.get_env_config().awa_api_port,
            log_level="info",
            log_config=unittest.mock.ANY,
            access_log=True,
        )

    @pytest.mark.asyncio
    @patch("awa.core.api.api.Api")
    @patch("awa.core.api.api.threading.Thread")
    @patch("awa.core.api.api.asyncio.Event")
    async def test_run_api_server(
        self,
        mock_event: MagicMock,
        mock_thread: MagicMock,
        mock_api_class: MagicMock,
    ) -> None:
        """Test that _run_api_server starts a thread and handles cancellation."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        mock_event_instance = AsyncMock()
        mock_event.return_value = mock_event_instance

        # Make wait raise CancelledError to test the exception handler
        mock_event_instance.wait.side_effect = asyncio.CancelledError()

        # Act
        await _run_api_server()

        # Assert
        mock_api_class.assert_called_once()
        mock_thread.assert_called_once_with(target=mock_api.run)
        assert mock_thread_instance.daemon is True
        mock_thread_instance.start.assert_called_once()
        mock_event_instance.wait.assert_called_once()
        mock_api.shutdown.assert_called_once()
        mock_thread_instance.join.assert_called_once()

    @patch("awa.core.api.api.Api")
    def test_start_api_server_normal(self, mock_api_class: MagicMock) -> None:
        """Test start_api_server normal execution."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api

        # Act
        start_api_server()

        # Assert
        mock_api_class.assert_called_once()
        mock_api.run_docker.assert_called_once()

    @patch("awa.core.api.api.Api")
    def test_start_api_server_keyboard_interrupt(self, mock_api_class: MagicMock) -> None:
        """Test start_api_server with KeyboardInterrupt."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        mock_api.run_docker.side_effect = KeyboardInterrupt()

        # Act
        start_api_server()

        # Assert
        mock_api_class.assert_called_once()
        mock_api.run_docker.assert_called_once()
        mock_api.shutdown.assert_called_once()

    @patch("awa.core.api.api.Api")
    def test_start_api_server_exception(self, mock_api_class: MagicMock) -> None:
        """Test start_api_server with general exception."""
        # Arrange
        mock_api = MagicMock()
        mock_api_class.return_value = mock_api
        test_exception = ValueError("Test error")
        mock_api.run_docker.side_effect = test_exception

        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            start_api_server()

        assert str(excinfo.value) == "Test error"
        mock_api_class.assert_called_once()
        mock_api.run_docker.assert_called_once()
