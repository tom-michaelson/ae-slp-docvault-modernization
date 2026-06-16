"""Integration tests for API authentication."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from awa.core.api.api import Api


class TestAPIAuthentication:
    """Test API authentication integration."""

    @pytest.fixture
    def mock_env_config_anonymous(self) -> Mock:
        """Mock environment config with anonymous mode."""
        config = Mock()
        config.public_auth_mode = "none"
        config.awa_ui_host = "localhost"
        config.awa_ui_port = 8000
        config.awa_api_host = "localhost"
        config.awa_api_port = 8001
        return config

    @pytest.fixture
    def mock_env_config_cognito(self) -> Mock:
        """Mock environment config with Cognito mode."""
        config = Mock()
        config.public_auth_mode = "cognito"
        config.awa_ui_host = "localhost"
        config.awa_ui_port = 8000
        config.awa_api_host = "localhost"
        config.awa_api_port = 8001
        config.auth_cognito_issuer = "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_TestPool"
        config.auth_cognito_client_id = "test-client-id"
        return config

    @pytest.fixture
    def api_client_anonymous(self, mock_env_config_anonymous: Mock) -> TestClient:
        """Create test client with anonymous auth."""
        from awa.core.models.config.env_config import EnvConfig

        # Store original config
        original_config = EnvConfig._env_config

        # Set mock config
        EnvConfig._env_config = mock_env_config_anonymous

        try:
            api = Api()
            yield TestClient(api.app)
        finally:
            # Restore original config
            EnvConfig._env_config = original_config

    @pytest.fixture
    def api_client_cognito(self, mock_env_config_cognito: Mock) -> TestClient:
        """Create test client with Cognito auth."""
        from awa.core.models.config.env_config import EnvConfig

        # Store original config
        original_config = EnvConfig._env_config

        # Set mock config
        EnvConfig._env_config = mock_env_config_cognito

        try:
            api = Api()
            yield TestClient(api.app)
        finally:
            # Restore original config
            EnvConfig._env_config = original_config

    @pytest.mark.parametrize(
        ("client_fixture", "expected_status"),
        [
            ("api_client_anonymous", 200),
            ("api_client_cognito", 200),
        ],
    )
    def test_health_endpoint_accessible(
        self,
        client_fixture: str,
        expected_status: int,
        request: pytest.FixtureRequest,
    ) -> None:
        """Test health endpoint is accessible without authentication in both modes."""
        client = request.getfixturevalue(client_fixture)

        with (
            patch("awa.core.api.routes.shared.health.TemporalServer") as mock_server,
            patch("awa.core.api.routes.shared.health._get_active_worker_pollers") as mock_pollers,
        ):
            mock_server_instance = mock_server.return_value
            mock_server_instance.check_service_status = AsyncMock(return_value=True)
            mock_pollers.return_value = ["worker1"]

            response = client.get("/api/v1/health")
            assert response.status_code == expected_status

    def test_workflows_list_anonymous(self, api_client_anonymous: TestClient) -> None:
        """Test workflows list endpoint in anonymous mode."""
        with (
            patch("awa.core.api.routes.shared.workflows.get_workflow_metadata", return_value=[]),
            patch("awa.core.api.routes.shared.workflows.get_registry_storage") as mock_storage,
        ):
            # Mock empty external registry
            mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

            response = api_client_anonymous.get("/api/v1/workflows/list")
            assert response.status_code == 200
            assert response.json()["workflows"] == []

    @pytest.mark.parametrize(
        ("has_auth", "expected_status", "expected_content"),
        [
            (False, 401, "Authentication required"),
            (True, 200, None),
        ],
    )
    def test_workflows_list_cognito_auth_scenarios(
        self,
        api_client_cognito: TestClient,
        has_auth: bool,
        expected_status: int,
        expected_content: str | None,
    ) -> None:
        """Test workflows list endpoint in Cognito mode with and without authentication."""
        if has_auth:
            mock_user = {"sub": "user123", "email": "user@example.com"}
            headers = {"Authorization": "Bearer valid-jwt-token"}

            with (
                patch("awa.core.api.auth.cognito_auth.validate_token", return_value=mock_user),
                patch("awa.core.api.routes.shared.workflows.get_workflow_metadata", return_value=[]),
                patch("awa.core.api.routes.shared.workflows.get_registry_storage") as mock_storage,
            ):
                # Mock empty external registry
                mock_storage.return_value.list_active_workers = AsyncMock(return_value=[])

                response = api_client_cognito.get("/api/v1/workflows/list", headers=headers)
                assert response.status_code == expected_status
                assert response.json()["workflows"] == []
        else:
            response = api_client_cognito.get("/api/v1/workflows/list")
            assert response.status_code == expected_status
            assert expected_content in response.json()["detail"]

    def test_workflows_runs_anonymous(self, api_client_anonymous: TestClient) -> None:
        """Test workflows runs endpoint in anonymous mode."""
        mock_client = Mock()
        mock_client.list_workflow_runs = AsyncMock(return_value=[])

        with patch("awa.core.api.routes.shared.workflows.TemporalClient.create", return_value=mock_client):
            response = api_client_anonymous.get("/api/v1/workflows/runs")
            assert response.status_code == 200
            assert response.json()["workflows"] == []

    @pytest.mark.parametrize(
        ("has_auth", "expected_status", "expected_content"),
        [
            (False, 401, "Authentication required"),
            (True, 200, None),
        ],
    )
    def test_workflows_runs_cognito_auth_scenarios(
        self,
        api_client_cognito: TestClient,
        has_auth: bool,
        expected_status: int,
        expected_content: str | None,
    ) -> None:
        """Test workflows runs endpoint in Cognito mode with and without authentication."""
        if has_auth:
            mock_user = {"sub": "user123", "email": "user@example.com"}
            mock_client = Mock()
            mock_client.list_workflow_runs = AsyncMock(return_value=[])
            headers = {"Authorization": "Bearer valid-jwt-token"}

            with (
                patch("awa.core.api.auth.cognito_auth.validate_token", return_value=mock_user),
                patch("awa.core.api.routes.shared.workflows.TemporalClient.create", return_value=mock_client),
            ):
                response = api_client_cognito.get("/api/v1/workflows/runs", headers=headers)
                assert response.status_code == expected_status
                assert response.json()["workflows"] == []
        else:
            response = api_client_cognito.get("/api/v1/workflows/runs")
            assert response.status_code == expected_status
            assert expected_content in response.json()["detail"]

    def test_invalid_bearer_token_format(self, api_client_cognito: TestClient) -> None:
        """Test invalid bearer token format."""
        headers = {"Authorization": "InvalidFormat token"}
        response = api_client_cognito.get("/api/v1/workflows/list", headers=headers)
        assert response.status_code == 401

    def test_cors_headers(self, api_client_anonymous: TestClient) -> None:
        """Test CORS headers are properly set."""
        response = api_client_anonymous.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:8000"
        assert response.headers["access-control-allow-credentials"] == "true"
        assert "authorization" in response.headers["access-control-allow-headers"].lower()

    @pytest.mark.parametrize(
        ("malicious_token", "should_not_contain"),
        [
            ("Bearer ' OR '1'='1", None),
            ("Bearer <script>alert('xss')</script>", "<script>"),
            ("Bearer javascript:alert('xss')", "javascript:"),
            ("Bearer onload=alert('xss')", "onload="),
        ],
    )
    def test_security_attack_protection(
        self,
        api_client_cognito: TestClient,
        malicious_token: str,
        should_not_contain: str | None,
    ) -> None:
        """Test protection against various security attacks in JWT tokens."""
        headers = {"Authorization": malicious_token}
        response = api_client_cognito.get("/api/v1/workflows/list", headers=headers)
        assert response.status_code == 401

        # Ensure malicious content is not reflected in response
        if should_not_contain:
            assert should_not_contain not in response.text

    def test_large_token_dos_protection(self, api_client_cognito: TestClient) -> None:
        """Test protection against DoS with extremely large tokens."""
        # Create a very large fake token (10MB)
        large_token = "Bearer " + "A" * 10_000_000
        headers = {"Authorization": large_token}
        response = api_client_cognito.get("/api/v1/workflows/list", headers=headers)
        assert response.status_code == 401

    @pytest.mark.parametrize(
        ("origin", "has_origin_header", "should_allow"),
        [
            (None, False, False),  # Missing origin - no CORS headers
            ("http://evil.com", True, False),  # Invalid origin - not allowed
            ("http://localhost:8000", True, True),  # Valid origin - allowed
        ],
    )
    def test_cors_origin_validation(
        self,
        api_client_anonymous: TestClient,
        origin: str | None,
        has_origin_header: bool,
        should_allow: bool,
    ) -> None:
        """Test CORS behavior with different origin scenarios."""
        headers = {}
        if origin:
            headers["Origin"] = origin
            headers["Access-Control-Request-Method"] = "GET"

        if has_origin_header and not should_allow:
            # Test preflight request for invalid origin
            response = api_client_anonymous.options("/api/v1/health", headers=headers)
            assert response.headers.get("access-control-allow-origin") != origin
        else:
            # Test regular request or valid origin
            with (
                patch("awa.core.api.routes.shared.health.TemporalServer") as mock_server,
                patch("awa.core.api.routes.shared.health._get_active_worker_pollers") as mock_pollers,
            ):
                mock_server_instance = mock_server.return_value
                mock_server_instance.check_service_status = AsyncMock(return_value=True)
                mock_pollers.return_value = []

                if origin:
                    response = api_client_anonymous.options("/api/v1/health", headers=headers)
                    if should_allow:
                        assert response.headers.get("access-control-allow-origin") == origin
                else:
                    response = api_client_anonymous.get("/api/v1/health")
                    assert "access-control-allow-origin" not in response.headers
