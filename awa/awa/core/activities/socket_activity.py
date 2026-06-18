"""Activities for Socket.IO operations."""

from datetime import datetime
from typing import Any

from temporalio import activity

from awa.core.api.socketio_server import emit_hitl_system_message
from awa.core.logger.logger import LoggerComponent, get_logger


@activity.defn
async def emit_hitl_chat_message(
    task_id: str,
    message: str,
    data: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
) -> None:
    """Activity to emit a HITL system message via Socket.IO.

    Args:
        task_id: The HITL task ID
        message: The message content
        data: Optional structured data
        timestamp: Optional timestamp (defaults to current time)

    """
    logger = get_logger(LoggerComponent.ACTIVITY)
    logger.debug(f"Emitting HITL system message for task {task_id}")

    try:
        await emit_hitl_system_message(
            task_id=task_id,
            message=message,
            data=data,
            timestamp=timestamp,
        )
        logger.debug(f"Successfully emitted HITL system message for task {task_id}")
    except Exception:
        logger.exception(f"Failed to emit HITL system message for task {task_id}")
        # Don't re-raise - socket emission failures shouldn't fail the workflow
