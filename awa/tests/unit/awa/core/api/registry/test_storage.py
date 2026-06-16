"""Unit tests for registry storage implementations."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from awa.core.api.registry.storage import FileSystemRegistryStorage
from awa.core.models.api import ActivityDefinition, WorkerRegistration, WorkflowDefinition


@pytest.fixture
def storage(tmp_path: Path) -> FileSystemRegistryStorage:
    """Create storage instance with test path."""
    storage = FileSystemRegistryStorage(base_path=tmp_path)
    return storage


@pytest.fixture
def sample_registration() -> WorkerRegistration:
    """Create sample worker registration."""
    return WorkerRegistration(
        worker_name="test-worker",
        worker_version="1.0.0",
        task_queue="test-queue",
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


class TestFileSystemRegistryStorage:
    """Test cases for file-based registry storage implementation."""

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.write_async")
    async def test_store_worker_registration(
        self,
        mock_write: AsyncMock,
        storage: FileSystemRegistryStorage,
        sample_registration: WorkerRegistration,
    ) -> None:
        """Test storing worker registration."""
        # Arrange
        mock_write.return_value = None

        # Act
        await storage.store_worker_registration(sample_registration)

        # Assert - Check that write_async was called with correct parameters
        mock_write.assert_called_once()
        call_args = mock_write.call_args
        assert sample_registration.worker_name in call_args[0][0]  # file path contains worker name

        content = call_args[0][1]
        parsed = json.loads(content)
        assert parsed["worker_name"] == sample_registration.worker_name

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.write_async")
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    async def test_store_and_retrieve_worker(
        self,
        mock_read: AsyncMock,
        mock_write: AsyncMock,
        storage: FileSystemRegistryStorage,
        sample_registration: WorkerRegistration,
    ) -> None:
        """Test storing and retrieving worker registrations."""
        # Arrange
        mock_write.return_value = None
        # Create expected stored registration JSON
        from awa.core.models.api import StoredWorkerRegistration

        stored_reg = StoredWorkerRegistration(**sample_registration.model_dump())
        mock_read.return_value = stored_reg.model_dump_json()

        # Act - Store registration
        await storage.store_worker_registration(sample_registration)

        # Act - Retrieve registration
        retrieved = await storage.get_worker_registration("test-worker")

        # Assert
        assert retrieved is not None
        assert retrieved.worker_name == "test-worker"
        assert retrieved.worker_version == "1.0.0"
        assert retrieved.task_queue == "test-queue"
        assert len(retrieved.workflows) == 1
        assert len(retrieved.activities) == 1
        assert retrieved.workflows[0].name == "TestWorkflow"
        assert retrieved.activities[0].name == "test_activity"
        # Check that stored_at timestamp was added
        assert retrieved.stored_at is not None

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    async def test_get_nonexistent_worker(
        self,
        mock_read: AsyncMock,
        storage: FileSystemRegistryStorage,
    ) -> None:
        """Test retrieving non-existent worker registration."""
        # Arrange
        mock_read.side_effect = FileNotFoundError("File not found")

        # Act
        retrieved = await storage.get_worker_registration("nonexistent-worker")

        # Assert
        assert retrieved is None

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.list_directory_async")
    async def test_list_active_workers_empty(
        self,
        mock_list_directory: AsyncMock,
        storage: FileSystemRegistryStorage,
    ) -> None:
        """Test listing active workers when registry is empty."""
        # Arrange
        mock_list_directory.side_effect = FileNotFoundError("Directory not found")

        # Act
        active_workers = await storage.list_active_workers()

        # Assert
        assert active_workers == []

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.list_directory_async")
    async def test_list_active_workers_with_registrations(
        self,
        mock_list_directory: AsyncMock,
        mock_read: AsyncMock,
        storage: FileSystemRegistryStorage,
    ) -> None:
        """Test listing active workers with multiple registrations."""
        # Arrange - Mock file listing to return JSON files
        mock_list_directory.return_value = [
            f"{storage.registry_dir}/worker-0.json",
            f"{storage.registry_dir}/worker-1.json",
            f"{storage.registry_dir}/worker-2.json",
        ]

        # Mock file reading to return worker registration JSON
        from awa.core.models.api import StoredWorkerRegistration

        mock_registrations = []
        for i in range(3):
            worker = WorkerRegistration(
                worker_name=f"worker-{i}",
                worker_version="1.0.0",
                task_queue="test-queue",
            )
            stored_worker = StoredWorkerRegistration(**worker.model_dump())
            mock_registrations.append(stored_worker.model_dump_json())

        mock_read.side_effect = mock_registrations

        # Act - List active workers
        active_workers = await storage.list_active_workers()

        # Assert
        assert len(active_workers) == 3
        worker_names = [w.worker_name for w in active_workers]
        assert "worker-0" in worker_names
        assert "worker-1" in worker_names
        assert "worker-2" in worker_names

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.write_async")
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    async def test_overwrite_existing_registration(
        self,
        mock_read: AsyncMock,
        mock_write: AsyncMock,
        storage: FileSystemRegistryStorage,
        sample_registration: WorkerRegistration,
    ) -> None:
        """Test overwriting existing worker registration."""
        # Arrange
        mock_write.return_value = None
        updated_registration = WorkerRegistration(
            worker_name="test-worker",
            worker_version="2.0.0",  # Updated version
            task_queue="test-queue",
        )

        # Mock reading the updated registration
        from awa.core.models.api import StoredWorkerRegistration

        stored_updated = StoredWorkerRegistration(**updated_registration.model_dump())
        mock_read.return_value = stored_updated.model_dump_json()

        # Act - Store initial registration
        await storage.store_worker_registration(sample_registration)

        # Act - Store updated registration
        await storage.store_worker_registration(updated_registration)

        # Act - Retrieve registration
        retrieved = await storage.get_worker_registration("test-worker")

        # Assert - Should have updated version
        assert retrieved is not None
        assert retrieved.worker_version == "2.0.0"

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.list_directory_async")
    async def test_storage_handles_invalid_json_files(
        self,
        mock_list_directory: AsyncMock,
        mock_read: AsyncMock,
        storage: FileSystemRegistryStorage,
    ) -> None:
        """Test that storage handles invalid JSON files gracefully."""
        # Arrange - Mock file listing to return a JSON file
        mock_list_directory.return_value = [f"{storage.registry_dir}/invalid-worker.json"]

        # Mock file reading to return invalid JSON
        mock_read.return_value = "invalid json content"

        # Act - List active workers should skip invalid file
        active_workers = await storage.list_active_workers()

        # Assert - Should return empty list and not crash
        assert active_workers == []

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.write_async")
    async def test_storage_creates_directory_structure(
        self,
        mock_write: AsyncMock,
        storage: FileSystemRegistryStorage,
        sample_registration: WorkerRegistration,
    ) -> None:
        """Test that storage creates necessary directory structure."""
        # Arrange
        mock_write.return_value = None

        # Act - Store registration (should create directories via write_async)
        await storage.store_worker_registration(sample_registration)

        # Assert - write_async was called, which handles directory creation
        mock_write.assert_called_once()

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    async def test_get_worker_handles_validation_error(
        self,
        mock_read: AsyncMock,
        storage: FileSystemRegistryStorage,
    ) -> None:
        """Test that get_worker handles Pydantic validation errors gracefully."""
        # Arrange - Mock reading invalid JSON that doesn't match schema
        invalid_data = json.dumps({"invalid_field": "value"})
        mock_read.return_value = invalid_data

        # Act - Try to get worker with invalid schema
        retrieved = await storage.get_worker_registration("invalid-schema")

        # Assert - Should return None and not crash
        assert retrieved is None

    @pytest.mark.asyncio
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.read_async")
    @patch("awa.core.utils.file_system_utils.FileSystemUtils.list_directory_async")
    async def test_list_workers_filters_non_json_files(
        self,
        mock_list_directory: AsyncMock,
        mock_read: AsyncMock,
        storage: FileSystemRegistryStorage,
        sample_registration: WorkerRegistration,
    ) -> None:
        """Test that list_workers only processes JSON files."""
        # Arrange - Mock file listing to return JSON and non-JSON files
        mock_list_directory.return_value = [
            f"{storage.registry_dir}/test-worker.json",
            f"{storage.registry_dir}/readme.txt",  # Should be ignored
        ]

        # Mock reading the JSON file
        from awa.core.models.api import StoredWorkerRegistration

        stored_reg = StoredWorkerRegistration(**sample_registration.model_dump())
        mock_read.return_value = stored_reg.model_dump_json()

        # Act
        active_workers = await storage.list_active_workers()

        # Assert - Should only return the valid registration
        assert len(active_workers) == 1
        assert active_workers[0].worker_name == "test-worker"
        # Should only call read_async once (for the JSON file)
        mock_read.assert_called_once()


class TestFileSystemRegistryStorageInitialization:
    """Test cases for storage initialization."""

    def test_storage_initialization_with_base_path(self, tmp_path: Path) -> None:
        """Test storage initialization with custom base path."""
        # Act
        storage = FileSystemRegistryStorage(base_path=tmp_path)

        # Assert
        expected_path = tmp_path / "registry" / "workers"
        assert storage.registry_dir == expected_path

    @patch("awa.core.utils.config_paths.ConfigPaths.get_global_config_dir")
    def test_storage_initialization_default_path(self, mock_global_config: AsyncMock) -> None:
        """Test storage initialization with default global path."""
        # Arrange
        mock_global_config.return_value = Path("/mock/.awa")

        # Act
        storage = FileSystemRegistryStorage()

        # Assert
        expected_path = Path("/mock/.awa") / "registry" / "workers"
        assert storage.registry_dir == expected_path

    def test_storage_has_logger(self, tmp_path: Path) -> None:
        """Test that storage instance has proper logger."""
        # Act
        storage = FileSystemRegistryStorage(base_path=tmp_path)

        # Assert
        assert storage.logger is not None
