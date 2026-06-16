"""Storage abstraction layer for registry operations."""

import json
from abc import ABC, abstractmethod
from pathlib import Path

from pydantic import ValidationError

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import StoredWorkerRegistration, WorkerRegistration
from awa.core.utils.config_paths import ConfigPaths
from awa.core.utils.file_system_utils import FileSystemUtils


class RegistryStorage(ABC):
    """Abstract interface for registry storage operations."""

    @abstractmethod
    async def store_worker_registration(self, registration: WorkerRegistration) -> None:
        """Store a worker registration.

        Args:
            registration: Worker registration data to store

        """

    @abstractmethod
    async def get_worker_registration(self, worker_name: str) -> StoredWorkerRegistration | None:
        """Retrieve a worker registration by name.

        Args:
            worker_name: Name of the worker to retrieve

        Returns:
            Stored worker registration or None if not found

        """

    @abstractmethod
    async def list_active_workers(self) -> list[StoredWorkerRegistration]:
        """List all active worker registrations.

        Returns:
            List of all stored worker registrations

        """


class FileSystemRegistryStorage(RegistryStorage):
    """File-based registry storage using AWA's FileSystemUtils."""

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize with optional base path override for testing.

        Args:
            base_path: Optional base path override for testing

        """
        self.logger = get_logger(LoggerComponent.API)
        if base_path:
            self.registry_dir = base_path / "registry" / "workers"
        else:
            # Use global AWA directory following existing patterns
            global_dir = ConfigPaths.get_global_config_dir()
            self.registry_dir = global_dir / "registry" / "workers"

    async def store_worker_registration(self, registration: WorkerRegistration) -> None:
        """Store worker registration as JSON file.

        Args:
            registration: Worker registration data to store

        """
        # Create stored registration with metadata
        stored_registration = StoredWorkerRegistration(**registration.model_dump())
        # Write to file using existing utilities
        file_path = str(self.registry_dir / f"{registration.worker_name}.json")
        content = stored_registration.model_dump_json(indent=2)
        await FileSystemUtils.write_async(file_path, content)
        self.logger.debug(f"Stored registration for worker: {registration.worker_name}")

    async def get_worker_registration(self, worker_name: str) -> StoredWorkerRegistration | None:
        """Retrieve worker registration from JSON file.

        Args:
            worker_name: Name of the worker to retrieve
        Returns:
            Stored worker registration or None if not found

        """
        file_path = str(self.registry_dir / f"{worker_name}.json")
        try:
            content = await FileSystemUtils.read_async(file_path)
            registration = StoredWorkerRegistration.model_validate_json(content)
            return registration
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, ValidationError) as e:
            self.logger.warning(f"Invalid registration file {file_path}: {e}")
            return None

    async def list_active_workers(self) -> list[StoredWorkerRegistration]:
        """List all active worker registrations.

        Returns:
            List of all stored worker registrations

        """
        registry_path = str(self.registry_dir)
        try:
            # Use existing file listing utility
            file_paths = await FileSystemUtils.list_directory_async(registry_path)
            json_files = [f for f in file_paths if f.endswith(".json")]
            active_workers = []
            for file_path in json_files:
                try:
                    content = await FileSystemUtils.read_async(file_path)
                    registration = StoredWorkerRegistration.model_validate_json(content)
                    active_workers.append(registration)
                except (json.JSONDecodeError, ValidationError) as e:
                    self.logger.warning(f"Invalid registration file {file_path}: {e}")
                    continue
            return active_workers
        except FileNotFoundError:
            return []
        except OSError:
            self.logger.exception("Failed to list active workers")
            return []


def get_registry_storage() -> FileSystemRegistryStorage:
    """Create a registry storage instance using a factory function."""
    return FileSystemRegistryStorage()
