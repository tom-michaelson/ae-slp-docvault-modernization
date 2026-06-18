"""Registry-related API endpoints."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from awa.core.api.auth import require_service_authentication
from awa.core.api.registry.storage import FileSystemRegistryStorage
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import (
    WorkerRegistration,
    WorkerRegistrationResponse,
)

logger = get_logger(LoggerComponent.API)
storage = FileSystemRegistryStorage()


async def register_worker(
    registration: WorkerRegistration,
    service_auth: Annotated[dict, Depends(require_service_authentication)],
) -> WorkerRegistrationResponse:
    """Register a worker with its available workflows and activities.

    If a worker with the same name already exists, it will be overwritten.
    Uses service token authentication for worker-to-API communication.

    Args:
        registration: Worker registration data containing capabilities
        service_auth: Service authentication info

    Returns:
        WorkerRegistrationResponse with registration confirmation details

    Raises:
        HTTPException: 401 if authentication fails, 500 if worker registration fails

    """
    try:
        # Check if worker already exists
        existing_worker = await storage.get_worker_registration(registration.worker_name)

        # Store worker registration (overwrites if exists)
        await storage.store_worker_registration(registration)

        # Log appropriately based on whether this was new or update
        service_name = service_auth.get("service_name", "worker")
        service_info = f"service:{service_name}"

        if existing_worker:
            logger.info(f"Worker '{registration.worker_name}' registration updated by {service_info}")
        else:
            logger.info(f"Worker '{registration.worker_name}' registered successfully by {service_info}")

        return WorkerRegistrationResponse(
            message="Worker registered successfully",
            worker_name=registration.worker_name,
            registration_id=f"{registration.worker_name}_{registration.generated_at.isoformat()}",
        )
    except Exception as e:
        logger.exception(f"Failed to register worker '{registration.worker_name}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register worker",
        ) from e
