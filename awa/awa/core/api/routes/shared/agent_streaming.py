"""Agent streaming API endpoints."""

from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

from awa.core.api.auth import require_authenticated_user, require_service_authentication
from awa.core.api.socketio_server import agent_session_storage, sio
from awa.core.engine.temporal_client import TemporalClient
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import AgentSession, AgentSessionType, WorkflowAgentSessionsResponse


# Request/Response Models
class StreamEventRequest(BaseModel):
    """Request model for emitting a stream event."""

    session_id: str
    event_type: str
    event_data: dict[str, Any]
    timestamp: str | None = None


class StreamEventResponse(BaseModel):
    """Response model for stream event operations."""

    success: bool
    message: str
    event_count: int | None = None


async def get_workflow_agent_sessions(
    workflow_id: str,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
) -> WorkflowAgentSessionsResponse:
    """Get all agent streaming sessions for a workflow by discovering ExecuteAgent child workflows.

    This function discovers agent sessions by:
    1. Listing all ExecuteAgent workflows in Temporal
    2. Querying each for their parent_session_id
    3. Filtering those that match the requested workflow_id

    Args:
        workflow_id: The parent workflow ID
        current_user: Authenticated user

    Returns:
        Dict with session information including discovered agent workflow sessions

    Raises:
        HTTPException: 404 if workflow not found, 500 for other errors

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Getting agent sessions for workflow {workflow_id}, user {user_info}")

    try:
        from awa.sdk import constants as sdk_constants

        # Create and initialize Temporal client
        temporal_client = await TemporalClient.create()
        await temporal_client.ensure_initialized()
        client = await temporal_client.get_client()

        # Verify parent workflow exists
        try:
            parent_handle = client.get_workflow_handle(workflow_id)
            await parent_handle.describe()
        except Exception as e:
            logger.warning(f"Parent workflow {workflow_id} not found: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found",
            ) from e

        # Discover all ExecuteAgent workflows and filter by parent_session_id
        discovered_sessions = []

        # List all ExecuteAgent workflows
        # Note: This uses a synchronous API, but we're in an async context
        async for workflow_info in client.list_workflows(
            query=f'WorkflowType="{sdk_constants.WORKFLOW_EXECUTE_AGENT}"',
        ):
            try:
                workflow_handle = client.get_workflow_handle(workflow_info.id)

                # Query for parent_session_id
                parent_session_id = await workflow_handle.query("get_parent_session_id")

                # If this agent workflow belongs to our parent, include it
                if parent_session_id == workflow_id:
                    discovered_sessions.append(
                        AgentSession(
                            session_id=workflow_info.id,
                            session_type=AgentSessionType.AGENT,
                        ),
                    )
            except Exception as e:  # noqa: BLE001
                # Skip workflows that fail to query (might be completed/terminated)
                logger.debug(f"Failed to query workflow {workflow_info.id}: {e}")
                continue

        logger.info(f"Discovered {len(discovered_sessions)} agent sessions for workflow {workflow_id}")

        if len(discovered_sessions) > 1:
            # If multiple sessions, also include the parent as a session for consolidated streaming
            discovered_sessions.append(
                AgentSession(
                    session_id=workflow_id,
                    session_type=AgentSessionType.PARENT,
                ),
            )

        return WorkflowAgentSessionsResponse(
            workflow_id=workflow_id,
            sessions=discovered_sessions,
            count=len(discovered_sessions),
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.exception(f"Failed to get agent sessions for workflow {workflow_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent sessions: {e!s}",
        ) from e


async def emit_stream_event(
    request: StreamEventRequest,
    _auth: Annotated[dict, Depends(require_service_authentication)],
) -> StreamEventResponse:
    """Emit a stream event via HTTP (stores and broadcasts via Socket.IO).

    This endpoint allows Temporal activities to emit stream events via HTTP,
    which are then stored in the agent_session_storage and broadcast to Socket.IO clients.

    Args:
        request: Stream event request
        _auth: Service authentication (ensures only authorized services can emit)

    Returns:
        StreamEventResponse with success status

    Raises:
        HTTPException: 500 if emission fails

    """
    logger = get_logger(LoggerComponent.API)

    try:
        # Parse timestamp
        event_timestamp = datetime.fromisoformat(request.timestamp) if request.timestamp else datetime.now(UTC)

        # Map event_type to the appropriate Socket.IO event and storage structure
        event_type_mapping = {
            "message": "agent_stream_message",
            "step": "agent_stream_step",
            "start": "agent_stream_start",
            "complete": "agent_stream_complete",
            "error": "agent_stream_error",
            "output": "agent_stream_output",
        }

        socketio_event = event_type_mapping.get(request.event_type, "agent_stream_message")

        # Build the event payload
        event_payload = {
            "session_id": request.session_id,
            "timestamp": event_timestamp.isoformat(),
            **request.event_data,
        }

        # Store in agent_session_storage
        stored_event = {
            "type": request.event_type,
            **event_payload,
        }
        agent_session_storage[request.session_id].append(stored_event)

        # Emit to Socket.IO room
        room_name = f"agent-stream-{request.session_id}"
        await sio.emit(socketio_event, event_payload, room=room_name)

        return StreamEventResponse(
            success=True,
            message=f"Event emitted to session {request.session_id}",
            event_count=len(agent_session_storage[request.session_id]),
        )

    except Exception as e:
        logger.exception(f"Failed to emit stream event for session {request.session_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to emit stream event: {e!s}",
        ) from e
