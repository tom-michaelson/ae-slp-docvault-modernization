"""Activity for agent streaming operations."""

from typing import Any

from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.streaming_http_client import emit_streaming_event_via_http

logger = get_logger(LoggerComponent.ACTIVITY)


@activity.defn
async def emit_stream_message_activity(
    session_id: str,
    message: str,
    data: dict[str, Any] | None = None,
) -> None:
    """Activity to emit a message to an agent streaming session via HTTP.

    Args:
        session_id: The streaming session ID
        message: The message content to publish
        data: Optional metadata for the message

    """
    try:
        event_data = {
            "message": message,
            "data": data or {},
        }

        # Emit via HTTP (will be stored and broadcast to Socket.IO)
        await emit_streaming_event_via_http(
            session_id=session_id,
            event_type="message",
            event_data=event_data,
        )

    except Exception:
        logger.exception(f"Failed to emit stream message for session {session_id}")
        # Don't re-raise - emission failures shouldn't fail the workflow


@activity.defn
async def emit_stream_step_activity(
    session_id: str,
    step_name: str,
    step_type: str,  # "start", "complete", "error"
    description: str | None = None,
    result: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Activity to emit a step event to an agent streaming session via HTTP.

    Args:
        session_id: The streaming session ID
        step_name: Name of the step
        step_type: Type of step event (start, complete, error)
        description: Optional description
        result: Optional result or error message
        metadata: Optional metadata

    """
    try:
        event_data = {
            "type": f"step_{step_type}",
            "step_name": step_name,
            "description": description,
            "result": result,
            "metadata": metadata or {},
        }

        # Emit via HTTP (will be stored and broadcast to Socket.IO)
        await emit_streaming_event_via_http(
            session_id=session_id,
            event_type="step",
            event_data=event_data,
        )

    except Exception:
        logger.exception(f"Failed to emit step event for session {session_id}")
        # Don't re-raise - emission failures shouldn't fail the workflow
