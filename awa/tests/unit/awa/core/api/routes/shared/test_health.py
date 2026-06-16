"""Unit tests for shared health endpoint."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from awa.core.api.routes.shared.health import health
from awa.core.models.api import HealthResponse, HealthStatus, ServiceStatus


class TestSharedHealth:
    """Test cases for the shared health function."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_direct_success(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test calling the health function directly with successful services."""
        # Mock successful server status
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance

        # Mock successful worker pollers
        mock_get_pollers.return_value = ["worker1", "worker2"]

        result = await health()

        assert isinstance(result, HealthResponse)
        assert result.status.temporal_service.status == "up"
        assert result.status.temporal_worker.status == "up"
        assert result.status.temporal_service.message is None
        assert result.status.temporal_worker.message is None

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_returns_health_response(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test that health function returns a HealthResponse."""
        # Mock successful services
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance
        mock_get_pollers.return_value = ["worker1"]

        result = await health()
        assert isinstance(result, HealthResponse)
        assert isinstance(result.status, HealthStatus)
        assert isinstance(result.status.temporal_service, ServiceStatus)
        assert isinstance(result.status.temporal_worker, ServiceStatus)

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_status_values(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test that health function returns correct status values."""
        # Mock successful services
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance
        mock_get_pollers.return_value = ["worker1"]

        result = await health()
        assert result.status.temporal_service.status == "up"
        assert result.status.temporal_worker.status == "up"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_server_down_via_false_return(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test server down scenario when check_service_status returns False."""
        # Mock server down (returns False)
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = False
        mock_temporal_server_class.return_value = mock_server_instance

        # Worker check should be skipped, but set return anyway
        mock_get_pollers.return_value = ["worker1"]

        with pytest.raises(HTTPException) as exc_info:
            await health()

        assert exc_info.value.status_code == 500
        detail = exc_info.value.detail
        assert detail["status"]["temporal_service"]["status"] == "down"
        assert detail["status"]["temporal_service"]["message"] == "Temporal service unreachable"
        assert detail["status"]["temporal_worker"]["status"] == "down"
        assert detail["status"]["temporal_worker"]["message"] == "Server down (worker checks skipped)"

        # Verify worker check was skipped
        mock_get_pollers.assert_not_called()

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_server_down_via_exception(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test server down scenario when check_service_status raises exception."""
        # Mock server exception
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.side_effect = Exception("Connection failed")
        mock_temporal_server_class.return_value = mock_server_instance

        with pytest.raises(HTTPException) as exc_info:
            await health()

        assert exc_info.value.status_code == 500
        detail = exc_info.value.detail
        assert detail["status"]["temporal_service"]["status"] == "down"
        assert detail["status"]["temporal_service"]["message"] == "Temporal service unreachable"
        assert detail["status"]["temporal_worker"]["status"] == "down"
        assert detail["status"]["temporal_worker"]["message"] == "Server down (worker checks skipped)"

        # Verify worker check was skipped
        mock_get_pollers.assert_not_called()

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_worker_down_no_pollers(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test worker down scenario when no active pollers found."""
        # Mock successful server
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance

        # Mock no active worker pollers
        mock_get_pollers.return_value = []

        with pytest.raises(HTTPException) as exc_info:
            await health()

        assert exc_info.value.status_code == 500
        detail = exc_info.value.detail
        assert detail["status"]["temporal_service"]["status"] == "up"
        # With exclude_unset=True, message field is excluded when None
        assert "message" not in detail["status"]["temporal_service"]
        assert detail["status"]["temporal_worker"]["status"] == "down"
        assert detail["status"]["temporal_worker"]["message"] == "No active worker pollers found"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_worker_exception(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test worker down scenario when _get_active_worker_pollers raises exception."""
        # Mock successful server
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance

        # Mock worker pollers exception
        mock_get_pollers.side_effect = Exception("Failed to get pollers")

        with pytest.raises(HTTPException) as exc_info:
            await health()

        assert exc_info.value.status_code == 500
        detail = exc_info.value.detail
        assert detail["status"]["temporal_service"]["status"] == "up"
        # With exclude_unset=True, message field is excluded when None
        assert "message" not in detail["status"]["temporal_service"]
        assert detail["status"]["temporal_worker"]["status"] == "down"
        assert detail["status"]["temporal_worker"]["message"] == "No active worker pollers found"

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_temporal_server_constructor_exception(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test server down scenario when TemporalServer constructor raises exception."""
        # Mock TemporalServer constructor exception
        mock_temporal_server_class.side_effect = Exception("Failed to create server")

        with pytest.raises(HTTPException) as exc_info:
            await health()

        assert exc_info.value.status_code == 500
        detail = exc_info.value.detail
        assert detail["status"]["temporal_service"]["status"] == "down"
        assert detail["status"]["temporal_service"]["message"] == "Temporal service unreachable"
        assert detail["status"]["temporal_worker"]["status"] == "down"
        assert detail["status"]["temporal_worker"]["message"] == "Server down (worker checks skipped)"

        # Verify worker check was skipped
        mock_get_pollers.assert_not_called()

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    async def test_health_function_response_format_and_status_codes(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test that response format and status codes are correct for all scenarios."""
        # Test successful case (should return HealthResponse, not raise HTTPException)
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance
        mock_get_pollers.return_value = ["worker1"]

        result = await health()
        assert isinstance(result, HealthResponse)
        assert result.status.temporal_service.status == "up"
        assert result.status.temporal_worker.status == "up"

        # Test failure case (should raise HTTPException with 500)
        mock_server_instance.check_service_status.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await health()

        assert exc_info.value.status_code == 500
        assert isinstance(exc_info.value.detail, dict)
        assert "status" in exc_info.value.detail
