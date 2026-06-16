"""Unit tests for shared registry endpoints."""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from awa.core.api.auth import require_service_authentication
from awa.core.api.routes.shared.registry import register_worker
from awa.core.models.api import (
    ActivityDefinition,
    StoredWorkerRegistration,
    WorkerRegistration,
    WorkflowDefinition,
)


@pytest.fixture
def mock_service_auth() -> Any:  # noqa: ANN401
    """Mock service authentication that returns service auth info."""

    async def _mock_service_auth() -> dict[str, str]:
        return {"type": "service", "service_name": "worker"}

    return _mock_service_auth


@pytest.fixture
def test_app(mock_service_auth: Any) -> FastAPI:  # noqa: ANN401
    """Create test FastAPI app with registry routes."""
    app = FastAPI()
    app.add_api_route(
        "/workers/register",
        register_worker,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
    )
    # Override the authentication dependency for testing
    app.dependency_overrides[require_service_authentication] = mock_service_auth
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(test_app)


@pytest.fixture
def sample_registration_data() -> dict:
    """Sample worker registration data."""
    return {
        "worker_name": "test-worker",
        "worker_version": "1.0.0",
        "task_queue": "test-queue",
        "workflows": [
            {
                "name": "TestWorkflow",
                "task_queue": "test-queue",
                "input_schema": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
            },
        ],
        "activities": [
            {
                "name": "test_activity",
                "task_queue": "test-queue",
                "input_schema": {"type": "object"},
            },
        ],
    }


@pytest.fixture
def mock_stored_registration() -> StoredWorkerRegistration:
    """Create mock stored worker registration."""
    return StoredWorkerRegistration(
        worker_name="test-worker",
        worker_version="1.0.0",
        task_queue="test-queue",
        generated_at=datetime.now(UTC),
        stored_at=datetime.now(UTC),
        workflows=[
            WorkflowDefinition(
                name="TestWorkflow",
                task_queue="test-queue",
                input_schema={"type": "object", "properties": {"message": {"type": "string"}}},
            ),
        ],
        activities=[
            ActivityDefinition(
                name="test_activity",
                task_queue="test-queue",
                input_schema={"type": "object"},
            ),
        ],
    )


class TestRegisterWorkerEndpoint:
    """Test cases for worker registration endpoint."""

    @patch("awa.core.api.routes.shared.registry.storage.get_worker_registration")
    @patch("awa.core.api.routes.shared.registry.storage.store_worker_registration")
    def test_register_worker_success(
        self,
        mock_store: AsyncMock,
        mock_get: AsyncMock,
        client: TestClient,
        sample_registration_data: dict,
    ) -> None:
        """Test successful worker registration with service authentication."""
        # Arrange
        mock_get.return_value = None  # No existing worker
        mock_store.return_value = None

        # Act
        response = client.post("/workers/register", json=sample_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Worker registered successfully"
        assert data["worker_name"] == "test-worker"
        assert "registration_id" in data

        # Verify storage was called
        mock_get.assert_called_once_with("test-worker")
        mock_store.assert_called_once()

    @patch("awa.core.api.routes.shared.registry.storage.get_worker_registration")
    @patch("awa.core.api.routes.shared.registry.storage.store_worker_registration")
    def test_register_worker_overwrite_existing(
        self,
        mock_store: AsyncMock,
        mock_get: AsyncMock,
        client: TestClient,
        sample_registration_data: dict,
        mock_stored_registration: StoredWorkerRegistration,
    ) -> None:
        """Test worker registration overwrites existing worker."""
        # Arrange
        mock_get.return_value = mock_stored_registration  # Existing worker found
        mock_store.return_value = None

        # Act
        response = client.post("/workers/register", json=sample_registration_data)

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Worker registered successfully"
        assert data["worker_name"] == "test-worker"
        assert "registration_id" in data

        # Verify storage was called
        mock_get.assert_called_once_with("test-worker")
        mock_store.assert_called_once()

    def test_register_worker_invalid_data_missing_fields(self, client: TestClient) -> None:
        """Test worker registration with missing required fields."""
        # Arrange
        invalid_data = {
            "worker_version": "1.0.0",
            "task_queue": "test-queue",
            # Missing worker_name
        }

        # Act
        response = client.post("/workers/register", json=invalid_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        error_detail = response.json()
        assert "detail" in error_detail

    def test_register_worker_invalid_data_empty_name(self, client: TestClient) -> None:
        """Test worker registration with empty worker name."""
        # Arrange
        invalid_data = {
            "worker_name": "",  # Empty name should fail validation
            "worker_version": "1.0.0",
            "task_queue": "test-queue",
        }

        # Act
        response = client.post("/workers/register", json=invalid_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_worker_invalid_workflow_schema(self, client: TestClient) -> None:
        """Test worker registration with invalid workflow definition."""
        # Arrange
        invalid_data = {
            "worker_name": "test-worker",
            "worker_version": "1.0.0",
            "task_queue": "test-queue",
            "workflows": [
                {
                    "name": "TestWorkflow",
                    # Missing task_queue and input_schema
                },
            ],
        }

        # Act
        response = client.post("/workers/register", json=invalid_data)

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @patch("awa.core.api.routes.shared.registry.storage.get_worker_registration")
    @patch("awa.core.api.routes.shared.registry.storage.store_worker_registration")
    def test_register_worker_storage_error(
        self,
        mock_store: AsyncMock,
        mock_get: AsyncMock,
        client: TestClient,
        sample_registration_data: dict,
    ) -> None:
        """Test worker registration with storage failure."""
        # Arrange
        mock_get.return_value = None  # No existing worker
        mock_store.side_effect = Exception("Storage error")

        # Act
        response = client.post("/workers/register", json=sample_registration_data)

        # Assert
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_detail = response.json()
        assert error_detail["detail"] == "Failed to register worker"

    @pytest.mark.parametrize(
        ("auth_mode", "expected_status", "expected_detail"),
        [
            ("cognito", status.HTTP_401_UNAUTHORIZED, "Service token required in Authorization header"),
            ("none", status.HTTP_201_CREATED, None),  # Anonymous mode allows access
        ],
    )
    def test_register_worker_authentication_behavior(
        self,
        sample_registration_data: dict,
        auth_mode: str,
        expected_status: int,
        expected_detail: str | None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test worker registration authentication behavior in different modes."""
        # Arrange - Set auth mode via environment variable and clear cached config
        monkeypatch.setenv("PUBLIC_AUTH_MODE", auth_mode)

        # Import EnvConfig here to avoid import-time caching issues
        from awa.core.models.config.env_config import EnvConfig

        # Clear the cached config so new environment variable is picked up
        EnvConfig._env_config = None

        # Create app without authentication override
        app = FastAPI()
        app.add_api_route(
            "/workers/register",
            register_worker,
            methods=["POST"],
            status_code=status.HTTP_201_CREATED,
        )
        client = TestClient(app)

        # Mock storage calls for successful case
        with (
            patch("awa.core.api.routes.shared.registry.storage.get_worker_registration") as mock_get,
            patch("awa.core.api.routes.shared.registry.storage.store_worker_registration") as mock_store,
        ):
            mock_get.return_value = None
            mock_store.return_value = None

            # Act - call without authentication
            response = client.post("/workers/register", json=sample_registration_data)

            # Assert - behavior depends on auth mode
            assert response.status_code == expected_status

            if expected_status == status.HTTP_401_UNAUTHORIZED:
                error_detail = response.json()
                assert error_detail["detail"] == expected_detail
            elif expected_status == status.HTTP_201_CREATED:
                data = response.json()
                assert data["message"] == "Worker registered successfully"
                assert data["worker_name"] == "test-worker"


class TestRegistryEndpointsDirectFunction:
    """Test cases for calling registry functions directly."""

    @pytest.mark.asyncio
    @patch("awa.core.api.routes.shared.registry.storage.get_worker_registration")
    @patch("awa.core.api.routes.shared.registry.storage.store_worker_registration")
    async def test_register_worker_function_direct(
        self,
        mock_store: AsyncMock,
        mock_get: AsyncMock,
        sample_registration_data: dict,
    ) -> None:
        """Test calling register_worker function directly."""
        # Arrange
        mock_get.return_value = None  # No existing worker
        mock_store.return_value = None
        registration = WorkerRegistration(**sample_registration_data)

        # Act
        mock_service_auth = {"type": "service", "service_name": "worker"}
        response = await register_worker(registration, mock_service_auth)

        # Assert
        assert response.message == "Worker registered successfully"
        assert response.worker_name == "test-worker"
        assert response.registration_id.startswith("test-worker_")

        # Verify storage was called
        mock_get.assert_called_once_with("test-worker")
        mock_store.assert_called_once()
