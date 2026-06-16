"""Data models for service state management."""

from datetime import datetime

from pydantic import BaseModel, Field


class ServiceInfo(BaseModel):
    """Information about a running service.

    Attributes:
        pid: Process ID of the service
        port: Port number if the service uses one (optional for services like Temporal Worker)
        started_at: Timestamp when the service was started

    """

    pid: int
    port: int | None = Field(default=None)
    started_at: datetime


class ServiceState(BaseModel):
    """Complete state of all tracked services.

    Attributes:
        timestamp: When this state was last updated
        services: Dictionary mapping service names to their information

    """

    timestamp: datetime
    services: dict[str, ServiceInfo] = Field(default_factory=dict)
