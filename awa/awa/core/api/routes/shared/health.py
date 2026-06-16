"""Shared health check endpoint implementation."""

from fastapi import HTTPException, status

from awa.core.constants import TASK_QUEUE
from awa.core.engine.temporal_server import TemporalServer
from awa.core.models.api import (
    HealthResponse,
    HealthStatus,
    ServerDownReasons,
    ServiceStatus,
    ServiceStatusValues,
    WorkerDownReasons,
)
from awa.core.utils.temporal_utils import _get_active_worker_pollers


async def health() -> HealthResponse:
    """Health check endpoint that returns the status of the Temporal services.

    Returns:
        HealthResponse containing the status of Temporal server and worker services

    """
    # Check Temporal server status first
    server_status = ServiceStatus(status=ServiceStatusValues.UP)
    worker_status = ServiceStatus(status=ServiceStatusValues.UP)

    try:
        temporal_server = TemporalServer()
        server_healthy = await temporal_server.check_service_status()

        if not server_healthy:
            server_status = ServiceStatus(status=ServiceStatusValues.DOWN, message=ServerDownReasons.UNREACHABLE)
            # Skip worker check when server is down
            worker_status = ServiceStatus(status=ServiceStatusValues.DOWN, message=WorkerDownReasons.SERVER_DOWN)
        else:
            # Server is healthy, check worker status
            try:
                active_pollers = await _get_active_worker_pollers(TASK_QUEUE)
                if len(active_pollers) < 1:
                    worker_status = ServiceStatus(
                        status=ServiceStatusValues.DOWN,
                        message=WorkerDownReasons.NO_ACTIVE_POLLERS,
                    )
            except Exception:  # noqa: BLE001
                worker_status = ServiceStatus(
                    status=ServiceStatusValues.DOWN,
                    message=WorkerDownReasons.NO_ACTIVE_POLLERS,
                )

    except Exception:  # noqa: BLE001
        server_status = ServiceStatus(status=ServiceStatusValues.DOWN, message=ServerDownReasons.UNREACHABLE)
        # Skip worker check when server is down
        worker_status = ServiceStatus(status=ServiceStatusValues.DOWN, message=WorkerDownReasons.SERVER_DOWN)

    health_status = HealthStatus(
        temporal_service=server_status,
        temporal_worker=worker_status,
    )

    response = HealthResponse(status=health_status)

    # Return 500 status code if either service is unhealthy
    if ServiceStatusValues.DOWN in {server_status.status, worker_status.status}:
        response_detail = response.model_dump(exclude_unset=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response_detail)

    # Both services are healthy, return 200 (default)
    return response
