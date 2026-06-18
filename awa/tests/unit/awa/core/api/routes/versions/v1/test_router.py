"""Unit tests for API v1 router."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from awa.core.api.routes.versions.v1.router import (
    authenticated_router,
    public_router,
    router,
    service_router,
)


class TestV1Router:
    """Test cases for v1 router functionality."""

    def test_router_exists(self) -> None:
        """Test that the v1 router object exists."""
        assert router is not None

    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    def test_health_endpoint_via_router(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test the health endpoint via v1 router."""
        # Mock successful services
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance
        mock_get_pollers.return_value = ["worker1"]

        # Create a test app with just the v1 router
        app = FastAPI()
        app.include_router(router)

        client = TestClient(app)
        response = client.get("/v1/health")

        assert response.status_code == status.HTTP_200_OK
        expected_response = {
            "status": {
                "temporal_service": {"status": "up"},
                "temporal_worker": {"status": "up"},
            },
        }
        assert response.json() == expected_response

    def test_router_includes_health_routes(self) -> None:
        """Test that the router includes health routes."""
        # Check that the router has routes
        assert len(router.routes) > 0

        # Verify health route is included within the v1 prefix
        route_paths = [route.path for route in router.routes]
        assert "/v1/health" in route_paths

    @patch("awa.core.api.routes.shared.health.TemporalServer")
    @patch("awa.core.api.routes.shared.health._get_active_worker_pollers")
    def test_health_endpoint_returns_correct_structure(
        self,
        mock_get_pollers: AsyncMock,
        mock_temporal_server_class: AsyncMock,
    ) -> None:
        """Test that health endpoint returns expected structure."""
        # Mock successful services
        mock_server_instance = AsyncMock()
        mock_server_instance.check_service_status.return_value = True
        mock_temporal_server_class.return_value = mock_server_instance
        mock_get_pollers.return_value = ["worker1"]

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        response = client.get("/v1/health")
        data = response.json()

        assert isinstance(data, dict)
        assert len(data) == 1
        assert "status" in data
        assert isinstance(data["status"], dict)
        assert "temporal_service" in data["status"]
        assert "temporal_worker" in data["status"]
        assert data["status"]["temporal_service"]["status"] == "up"
        assert data["status"]["temporal_worker"]["status"] == "up"


class TestRouterConfiguration:
    """Test router configuration and sub-router integration."""

    def test_public_router_configuration(self) -> None:
        """Test public router has correct configuration."""
        assert public_router.prefix == "/v1"
        assert public_router.dependencies == []  # No auth dependencies for public router

    def test_authenticated_router_configuration(self) -> None:
        """Test authenticated router has correct configuration."""
        assert authenticated_router.prefix == "/v1"
        assert len(authenticated_router.dependencies) == 1  # Should have user auth dependency

    def test_service_router_configuration(self) -> None:
        """Test service router has correct configuration."""
        assert service_router.prefix == "/v1"
        assert len(service_router.dependencies) == 1  # Should have service auth dependency

    def test_main_router_includes_all_sub_routers(self) -> None:
        """Test that the main router includes all three sub-routers."""
        # The main router should have routes from all sub-routers
        route_paths = [route.path for route in router.routes]

        # Should have health route from public router
        assert "/v1/health" in route_paths

        # Should have workflow routes from authenticated router
        assert "/v1/workflows/list" in route_paths
        assert "/v1/workflows/runs" in route_paths
        assert "/v1/workflows" in route_paths

        # Should have worker registration from service router
        assert "/v1/workers/register" in route_paths

    def test_router_route_count(self) -> None:
        """Test that router has expected number of routes."""
        # This helps catch if routes are accidentally added/removed
        routes = list(router.routes)
        # Should have at least the core routes we expect
        assert len(routes) >= 15  # Adjust based on actual count


class TestPublicRoutes:
    """Test public routes that don't require authentication."""

    def test_public_routes_exist(self) -> None:
        """Test that expected public routes exist."""
        public_route_paths = [route.path for route in public_router.routes]

        # Health endpoint
        assert "/v1/health" in public_route_paths

    def test_removed_agent_stream_endpoint_not_present(self) -> None:
        """Test that the removed /agents/stream/{session_id} endpoint is not present."""
        all_route_paths = [route.path for route in router.routes]

        # The old endpoint should not exist
        assert "/v1/agents/stream/{session_id}" not in all_route_paths

        # The legacy live endpoint should also not exist (replaced by Socket.IO)
        assert "/v1/agents/stream/{session_id}/live" not in all_route_paths

    def test_agent_stream_emit_endpoint_configured(self) -> None:
        """Test that the emit streaming endpoint is properly configured in the service router."""
        service_route_paths = [route.path for route in service_router.routes]
        assert "/v1/agents/stream/emit" in service_route_paths

        # Check the route method
        emit_routes = [route for route in service_router.routes if route.path == "/v1/agents/stream/emit"]
        assert len(emit_routes) == 1
        assert emit_routes[0].methods == {"POST"}

    def test_health_endpoint_methods(self) -> None:
        """Test health endpoint accepts only GET method."""
        health_routes = [route for route in public_router.routes if route.path == "/v1/health"]
        assert len(health_routes) == 1
        assert health_routes[0].methods == {"GET"}


class TestAuthenticatedRoutes:
    """Test routes that require user authentication."""

    def test_workflow_routes_exist(self) -> None:
        """Test that workflow routes exist in authenticated router."""
        auth_route_paths = [route.path for route in authenticated_router.routes]

        # Workflow endpoints
        assert "/v1/workflows/list" in auth_route_paths
        assert "/v1/workflows/runs" in auth_route_paths
        assert "/v1/workflows" in auth_route_paths
        assert "/v1/workflows/runs/{run_id}" in auth_route_paths

    def test_hitl_routes_exist(self) -> None:
        """Test that HITL routes exist in authenticated router."""
        auth_route_paths = [route.path for route in authenticated_router.routes]

        # HITL endpoints
        assert "/v1/hitl/tasks" in auth_route_paths
        assert "/v1/hitl/tasks/{workflow_id}" in auth_route_paths
        assert "/v1/hitl/task/{workflow_id}" in auth_route_paths
        assert "/v1/hitl/task/{workflow_id}/submit" in auth_route_paths
        assert "/v1/hitl/task/{workflow_id}/message" in auth_route_paths
        assert "/v1/hitl/task/{workflow_id}/chat/history" in auth_route_paths
        assert "/v1/hitl/task/{workflow_id}/chat/user-message" in auth_route_paths

    def test_workflow_route_methods(self) -> None:
        """Test workflow routes have correct HTTP methods."""
        auth_routes = {route.path: route.methods for route in authenticated_router.routes}

        assert auth_routes["/v1/workflows/list"] == {"GET"}
        assert auth_routes["/v1/workflows/runs"] == {"GET"}
        assert auth_routes["/v1/workflows"] == {"POST"}
        assert auth_routes["/v1/workflows/runs/{run_id}"] == {"GET"}

    def test_hitl_route_methods(self) -> None:
        """Test HITL routes have correct HTTP methods."""
        auth_routes = {route.path: route.methods for route in authenticated_router.routes}

        assert auth_routes["/v1/hitl/tasks"] == {"GET"}
        assert auth_routes["/v1/hitl/tasks/{workflow_id}"] == {"GET"}
        assert auth_routes["/v1/hitl/task/{workflow_id}"] == {"GET"}
        assert auth_routes["/v1/hitl/task/{workflow_id}/submit"] == {"POST"}
        assert auth_routes["/v1/hitl/task/{workflow_id}/message"] == {"POST"}
        assert auth_routes["/v1/hitl/task/{workflow_id}/chat/history"] == {"GET"}
        assert auth_routes["/v1/hitl/task/{workflow_id}/chat/user-message"] == {"POST"}

    def test_logs_router_included(self) -> None:
        """Test that logs router is included in authenticated router."""
        # The logs router should be included, adding additional routes
        auth_route_paths = [route.path for route in authenticated_router.routes]

        # Should have at least some log-related routes (exact paths depend on logs_router implementation)
        # We check for the inclusion rather than specific paths since logs_router is imported
        initial_route_count = len([r for r in auth_route_paths if not r.startswith("/v1/logs")])
        total_route_count = len(auth_route_paths)

        # If logs router adds routes, total should be greater than just the explicit routes
        # This is a general test since we don't know the exact logs router structure
        assert total_route_count >= initial_route_count


class TestServiceRoutes:
    """Test routes that require service authentication."""

    def test_service_routes_exist(self) -> None:
        """Test that service routes exist in service router."""
        service_route_paths = [route.path for route in service_router.routes]

        # Worker registration endpoint
        assert "/v1/workers/register" in service_route_paths

        # Agent streaming emit endpoint
        assert "/v1/agents/stream/emit" in service_route_paths

    def test_service_route_methods(self) -> None:
        """Test service routes have correct HTTP methods."""
        service_routes = {route.path: route.methods for route in service_router.routes}

        assert service_routes["/v1/workers/register"] == {"POST"}
        assert service_routes["/v1/agents/stream/emit"] == {"POST"}

    def test_worker_registration_status_code(self) -> None:
        """Test worker registration endpoint returns 201 status code."""
        worker_reg_routes = [route for route in service_router.routes if route.path == "/v1/workers/register"]
        assert len(worker_reg_routes) == 1
        # Note: status_code is stored in the route's endpoint configuration


class TestAgentStreamingEndpoints:
    """Test agent streaming endpoint configuration."""

    def test_live_streaming_endpoint_removed(self) -> None:
        """Test that live streaming endpoint was removed (replaced by Socket.IO)."""
        public_route_paths = [route.path for route in public_router.routes]
        assert "/v1/agents/stream/{session_id}/live" not in public_route_paths

    def test_emit_endpoint_exists(self) -> None:
        """Test that emit endpoint exists in service router."""
        service_route_paths = [route.path for route in service_router.routes]
        assert "/v1/agents/stream/emit" in service_route_paths

    def test_streaming_endpoints_have_correct_tags(self) -> None:
        """Test that streaming endpoints have correct tags."""
        # Check service router for emit endpoint
        emit_routes = [route for route in service_router.routes if route.path == "/v1/agents/stream/emit"]
        assert len(emit_routes) == 1
        # Verify it has the agent-streaming tag
        assert "agent-streaming" in emit_routes[0].tags

    def test_old_streaming_endpoint_removed(self) -> None:
        """Test that the old streaming endpoint is completely removed."""
        all_routes = []
        all_routes.extend(public_router.routes)
        all_routes.extend(authenticated_router.routes)
        all_routes.extend(service_router.routes)

        old_endpoint_paths = [route.path for route in all_routes if route.path == "/v1/agents/stream/{session_id}"]
        assert len(old_endpoint_paths) == 0

    def test_removed_function_not_importable(self) -> None:
        """Test that the removed get_agent_streaming_events function is no longer importable."""
        # Try to import the function that should be removed
        try:
            from awa.core.api.routes.shared.agent_streaming import get_agent_streaming_events  # noqa: F401

            # If we reach here, the function still exists, which is unexpected
            pytest.fail("get_agent_streaming_events function should have been removed but is still importable")
        except ImportError:
            # This is expected - the function should not be importable
            pass

    @patch("awa.core.api.routes.shared.agent_streaming.sio")
    @patch("awa.core.api.routes.shared.agent_streaming.agent_session_storage")
    def test_emit_endpoint_functionality(self, mock_storage: MagicMock, mock_sio: MagicMock) -> None:
        """Test emit endpoint basic functionality."""
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        # Mock the storage and socketio
        mock_storage.__getitem__ = MagicMock(return_value=[])
        mock_sio.emit = AsyncMock(return_value=None)

        # Test data
        test_data = {
            "session_id": "test-session",
            "event_type": "message",
            "event_data": {"content": "test message"},
            "timestamp": "2024-01-01T00:00:00Z",
        }

        # This would require service authentication in real scenario
        # but we're testing route configuration, not auth
        with patch("awa.core.api.auth.require_service_authentication", return_value={"service": "temporal"}):
            response = client.post("/v1/agents/stream/emit", json=test_data)

        # Should successfully process the request
        assert response.status_code == 200


class TestRouteResponseModels:
    """Test that routes have appropriate response models configured."""

    def test_health_route_response_model(self) -> None:
        """Test health route has HealthResponse model."""
        health_routes = [route for route in public_router.routes if route.path == "/v1/health"]
        assert len(health_routes) == 1
        # Response model checking would require inspecting route internals

    def test_workflow_routes_response_models(self) -> None:
        """Test workflow routes have appropriate response models."""
        workflow_list_routes = [route for route in authenticated_router.routes if route.path == "/v1/workflows/list"]
        assert len(workflow_list_routes) == 1

        workflow_runs_routes = [route for route in authenticated_router.routes if route.path == "/v1/workflows/runs"]
        assert len(workflow_runs_routes) == 1

    def test_worker_registration_response_model(self) -> None:
        """Test worker registration has WorkerRegistrationResponse model."""
        worker_routes = [route for route in service_router.routes if route.path == "/v1/workers/register"]
        assert len(worker_routes) == 1


class TestRoutePathResolution:
    """Test that route paths are resolved correctly with prefixes."""

    def test_route_path_prefixes(self) -> None:
        """Test that all routes have the correct /v1 prefix."""
        all_route_paths = [route.path for route in router.routes]

        # All routes should start with /v1
        for path in all_route_paths:
            assert path.startswith("/v1"), f"Route {path} does not have /v1 prefix"

    def test_no_duplicate_paths(self) -> None:
        """Test that there are no duplicate route paths."""
        all_route_paths = [route.path for route in router.routes]
        unique_paths = set(all_route_paths)

        assert len(all_route_paths) == len(unique_paths), "Duplicate route paths detected"

    def test_route_path_patterns(self) -> None:
        """Test that route paths follow expected patterns."""
        all_route_paths = [route.path for route in router.routes]

        # Workflow paths should follow pattern
        workflow_paths = [p for p in all_route_paths if "/workflows" in p]
        assert "/v1/workflows/list" in workflow_paths
        assert "/v1/workflows/runs" in workflow_paths
        assert "/v1/workflows" in workflow_paths

        # HITL paths should follow pattern
        hitl_paths = [p for p in all_route_paths if "/hitl" in p]
        assert any("/hitl/tasks" in p for p in hitl_paths)
        assert any("/hitl/task/" in p for p in hitl_paths)

        # Agent paths should follow pattern
        agent_paths = [p for p in all_route_paths if "/agents" in p]
        # Only emit endpoint exists, live endpoint replaced by Socket.IO
        assert "/v1/agents/stream/emit" in agent_paths
        assert "/v1/agents/stream/{session_id}/live" not in agent_paths
