"""FastAPI dependencies for dependency injection."""

from awa.core.engine.temporal_client import TemporalClient
from awa.core.logger.logger import LoggerComponent, get_logger

# Singleton instance of the Temporal client
_temporal_client: TemporalClient | None = None


async def get_temporal_client() -> TemporalClient:
    """Get or create a singleton Temporal client instance.

    This function ensures that only one Temporal client connection is created
    and reused across all API requests, significantly improving performance.

    Returns:
        TemporalClient: The singleton Temporal client instance

    """
    global _temporal_client  # noqa: PLW0603

    if _temporal_client is None:
        logger = get_logger(LoggerComponent.API)
        logger.info("Creating singleton Temporal client instance")
        _temporal_client = await TemporalClient.create()

    return _temporal_client


async def cleanup_temporal_client() -> None:
    """Cleanup the Temporal client connection on shutdown.

    This should be called when the API server is shutting down.

    """
    global _temporal_client  # noqa: PLW0603

    if _temporal_client is not None:
        logger = get_logger(LoggerComponent.API)
        logger.info("Cleaning up Temporal client connection")
        # If there's a close method, call it here
        _temporal_client = None
