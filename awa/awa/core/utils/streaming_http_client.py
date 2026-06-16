"""HTTP client for cross-process streaming events.

This module provides utilities for Temporal worker processes to emit
streaming events to the API server's Socket.IO instance via HTTP.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

import aiohttp
from loguru import logger

from awa.core.models.config.env_config import EnvConfig


async def emit_streaming_event_via_http(
    session_id: str,
    event_type: str,
    event_data: dict[str, Any],
    timestamp: datetime | None = None,
) -> bool:
    """Emit a streaming event to the API server via HTTP.

    This function enables cross-process communication between Temporal worker
    processes and the API server's Socket.IO instance.

    Args:
        session_id: The session identifier for the agent execution
        event_type: Type of the streaming event
        event_data: Event data payload
        timestamp: Optional timestamp, defaults to current UTC time

    Returns:
        bool: True if event was successfully emitted, False otherwise

    """
    if not session_id:
        logger.debug("No session_id provided, skipping event emission")
        return False

    try:
        # Get API server configuration
        env_config = EnvConfig.get_env_config()
        api_host = env_config.awa_api_host
        api_port = env_config.awa_api_port

        # Build API endpoint URL
        api_url = f"http://{api_host}:{api_port}/api/v1/agents/stream/emit"

        # Prepare timestamp
        event_timestamp = timestamp or datetime.now(UTC)

        # Prepare request payload
        payload = {
            "session_id": session_id,
            "event_type": event_type,
            "event_data": event_data,
            "timestamp": event_timestamp.isoformat(),
        }

        # Make HTTP request with timeout
        timeout = aiohttp.ClientTimeout(total=5.0)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(
                api_url,
                json=payload,
            ) as response,
        ):
            http_ok = 200
            if response.status == http_ok:
                return True
            error_text = await response.text()
            logger.error(f"Failed to emit streaming event, status {response.status}: {error_text}")
            return False

    except TimeoutError:
        logger.error(f"Timeout emitting streaming event for session {session_id}")
        return False
    except aiohttp.ClientError as e:
        logger.error(f"Client error emitting streaming event: {e}")
        return False
    except (ConnectionError, OSError) as e:
        logger.exception(f"Unexpected error emitting streaming event for session {session_id}: {e}")
        return False


async def emit_streaming_event_multi(
    session_ids: list[str],
    event_type: str,
    event_data: dict[str, Any],
    timestamp: datetime | None = None,
) -> list[bool]:
    """Emit a streaming event to multiple sessions via HTTP.

    This function enables broadcasting the same event to multiple session IDs
    for hierarchical workflow streaming (e.g., parent and child sessions).

    Args:
        session_ids: List of session identifiers
        event_type: Type of the streaming event
        event_data: Event data payload
        timestamp: Optional timestamp, defaults to current UTC time

    Returns:
        list[bool]: List of success status for each session emission

    """
    if not session_ids:
        logger.debug("No session_ids provided, skipping event emission")
        return []

    # Emit to all sessions concurrently
    tasks = [emit_streaming_event_via_http(session_id, event_type, event_data, timestamp) for session_id in session_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to False
    return [result if isinstance(result, bool) else False for result in results]


def emit_streaming_event_sync(
    session_id: str,
    event_type: str,
    event_data: dict[str, Any],
    timestamp: datetime | None = None,
) -> bool:
    """Emit streaming events via HTTP synchronously.

    This function provides a synchronous interface for environments where
    async/await isn't available or convenient.

    Args:
        session_id: The session identifier for the agent execution
        event_type: Type of the streaming event
        event_data: Event data payload
        timestamp: Optional timestamp, defaults to current UTC time

    Returns:
        bool: True if event was successfully emitted, False otherwise

    """
    try:
        # Run the async function in the current event loop if available,
        # otherwise create a new one
        try:
            loop = asyncio.get_running_loop()
            # If we're in an event loop, create a task
            task = loop.create_task(emit_streaming_event_via_http(session_id, event_type, event_data, timestamp))
            del task  # Suppress unused variable warning
            # Note: We can't await here since this is a sync function
            # The task will run in the background
            return True
        except RuntimeError:
            # No event loop running, create one
            return asyncio.run(emit_streaming_event_via_http(session_id, event_type, event_data, timestamp))
    except (RuntimeError, OSError, ValueError) as e:
        logger.exception(f"Error in sync streaming wrapper for session {session_id}: {e}")
        return False
