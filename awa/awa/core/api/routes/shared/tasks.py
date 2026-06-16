"""HITL Task-related API endpoints."""

from typing import Annotated

from fastapi import Depends, HTTPException

from awa.core.api.auth import require_authenticated_user
from awa.core.api.dependencies import get_temporal_client
from awa.core.api.socketio_server import emit_hitl_system_message
from awa.core.engine.temporal_client import TemporalClient
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import HITLTaskDetail, HITLTaskInfo


async def list_hitl_tasks(
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> list[HITLTaskInfo]:
    """List all HITL tasks for the current user.

    Args:
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        List of HITL task information

    Raises:
        HTTPException: If task listing fails

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Listing HITL tasks for user {user_info}")

    try:
        tasks = await client.list_pending_tasks()

        logger.info(f"Retrieved {len(tasks)} HITL tasks for user {user_info}")
        return tasks

    except Exception as e:
        logger.exception("Failed to list HITL tasks")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list HITL tasks: {e!s}",
        ) from e


async def get_hitl_task(
    workflow_id: str,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> HITLTaskDetail:
    """Get detailed information about a specific HITL task.

    Args:
        workflow_id: The task ID
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        Detailed HITL task information

    Raises:
        HTTPException: If task is not found or retrieval fails

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Getting HITL task {workflow_id} for user {user_info}")

    try:
        details = await client.get_hitl_task_details(workflow_id)

        logger.info(f"Task details for task {workflow_id} retrieved")
        return details

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get HITL task {workflow_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get HITL task: {e!s}",
        ) from e


async def submit_hitl_task(
    workflow_id: str,
    response: dict,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> dict[str, str]:
    """Submit a response to complete a HITL task.

    Args:
        workflow_id: The workflow execution ID
        response: The task submission payload
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        Success response

    Raises:
        HTTPException: If submission fails or task is not found

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.info(f"Submitting HITL task {workflow_id} for user {user_info}")
    logger.info(f"Submitting HITL response {response} of type {type(response)}")

    try:
        await client.submit_hitl_response(task_id=workflow_id, response_data=response)

        logger.info(f"Task response sent for task {workflow_id}")

        return {"data": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to submit HITL task {workflow_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit HITL task: {e!s}",
        ) from e


async def send_hitl_message(
    workflow_id: str,
    message_payload: dict,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> dict[str, str]:
    """Send a chat message to a HITL task in chat mode.

    Args:
        workflow_id: The workflow execution ID
        message_payload: The chat message payload with 'message' and optional 'data' fields
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        Success response

    Raises:
        HTTPException: If message sending fails or task is not in chat mode

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.info(f"Sending message to HITL task {workflow_id} for user {user_info}")

    try:
        # Extract message and data from payload
        message = message_payload.get("message")
        data = message_payload.get("data")
        is_human = message_payload.get("is_human", True)  # Default to human message

        if not message:
            detail = "Message field is required"
            raise HTTPException(status_code=400, detail=detail)  # noqa: TRY301

        # Send message to workflow
        if is_human:
            await client.send_hitl_human_message(task_id=workflow_id, message=message, data=data)

            # Check if this is a child workflow and signal the parent
            parent_workflow_id = await client.get_workflow_parent_id(workflow_id)
            if parent_workflow_id:
                try:
                    await client.signal_workflow(parent_workflow_id, "notify_user_message_received", message)
                    logger.info(f"Signaled parent workflow {parent_workflow_id} about user message: {message}")
                except Exception as e:
                    logger.warning(f"Failed to signal parent workflow {parent_workflow_id}: {e}")
                    raise HTTPException(status_code=500, detail=str(e)) from e

        else:
            await client.send_hitl_message(task_id=workflow_id, message=message)
            # Also emit to socket.io for live updates
            await emit_hitl_system_message(
                task_id=workflow_id,
                message=message,
                data=data,
            )

        logger.info(f"Chat message sent for task {workflow_id}")

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to send message to HITL task {workflow_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send message to HITL task: {e!s}",
        ) from e


async def get_hitl_chat_history(
    workflow_id: str,
    _current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> list[dict]:
    """Get current chat history for a HITL task.

    Args:
        workflow_id: The workflow execution ID
        _current_user: Authenticated user (unused)
        client: Temporal client instance for workflow operations

    Returns:
        List of chat messages with timestamp, isHuman flag, and data

    Raises:
        HTTPException: If task is not found or retrieval fails

    """
    logger = get_logger(LoggerComponent.API)
    logger.info(f"Getting chat history for workflow {workflow_id}")

    try:
        # Get the child workflow ID for HITL
        task_detail = await client.get_hitl_task_details(workflow_id)
        if not task_detail:
            raise HTTPException(status_code=404, detail="HITL task not found")  # noqa: TRY301

        # Get chat history from the workflow
        chat_history = task_detail.chat_history or []

        # Convert to API format
        return [
            {
                "message": msg.message,
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                "isHuman": msg.is_human,
                "data": msg.data,
            }
            for msg in chat_history
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting chat history for workflow {workflow_id}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def send_hitl_user_message(
    workflow_id: str,
    message_payload: dict,
    _current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> dict:
    """Send a user message to a HITL task.

    Args:
        workflow_id: The workflow execution ID
        message_payload: Message payload with 'message' and optional 'user_info' fields
        _current_user: Authenticated user (unused)
        client: Temporal client instance for workflow operations

    Returns:
        Success response with status

    Raises:
        HTTPException: If message is empty or sending fails

    """
    logger = get_logger(LoggerComponent.API)
    message = message_payload.get("message", "").strip()
    user_info = message_payload.get("user_info", {})

    if not message:
        raise HTTPException(status_code=400, detail="Message is required")

    logger.info(f"Sending user message to workflow {workflow_id}: {message[:100]}...")

    try:
        # Send human message to workflow
        await client.send_hitl_human_message(task_id=workflow_id, message=message, data=user_info)

        # Check if this is a child workflow and signal the parent
        parent_workflow_id = await client.get_workflow_parent_id(workflow_id)
        if parent_workflow_id:
            try:
                await client.signal_workflow(parent_workflow_id, "notify_user_message_received", message)
                logger.info(f"Signaled parent workflow {parent_workflow_id} about user message: {message}")
            except Exception as e:
                logger.warning(f"Failed to signal parent workflow {parent_workflow_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e)) from e
        else:
            logger.info(f"No parent workflow found for {workflow_id}")

        # Also emit to socket.io for real-time updates
        await emit_hitl_system_message(
            task_id=workflow_id,
            message=message,
            data=user_info,
        )

        return {"status": "User message sent successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error sending user message to workflow {workflow_id}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def list_hitl_tasks_for_workflow(
    workflow_id: str,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> list[HITLTaskInfo]:
    """List all HITL tasks for a specific parent workflow.

    Args:
        workflow_id: The parent workflow ID or run ID
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        List of HITL task information for the specified workflow

    Raises:
        HTTPException: If task listing fails

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Listing HITL tasks for workflow {workflow_id} for user {user_info}")

    try:
        tasks = await client.list_pending_tasks_for_workflow(workflow_id)

        logger.info(f"Retrieved {len(tasks)} HITL tasks for workflow {workflow_id} for user {user_info}")
        return tasks

    except Exception as e:
        logger.exception(f"Failed to list HITL tasks for workflow {workflow_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list HITL tasks for workflow: {e!s}",
        ) from e
