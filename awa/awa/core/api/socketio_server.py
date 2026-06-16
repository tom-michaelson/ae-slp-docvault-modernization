"""Socket.IO server for real-time log streaming.

This module provides WebSocket-based real-time log streaming
for workflow execution logs across multiple processes.
"""

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import socketio

from awa.core.api.auth import validate_service_token
from awa.core.constants import CORE_WORKER_NAME, MAX_LOG_MESSAGE_SIZE
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.log_filters import should_include_in_worker_log
from awa.core.utils.workflow_logging_utils import find_workflow_log_file, get_workflow_log_path


def _get_allowed_cors_origins() -> list[str] | str:
    """Get allowed CORS origins based on environment configuration.

    Returns:
        List of allowed origins or '*' for anonymous mode only

    """
    env_config = EnvConfig.get_env_config()

    # Only allow wildcard in anonymous mode for development
    if env_config.public_auth_mode.lower() == "none":
        return "*"

    # For authenticated modes, use specific allowed origins
    # Default to common development and production URLs
    allowed_origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8000",  # AWA UI
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]

    # Add the API server's own URL for internal service connections
    api_port = env_config.awa_api_port
    allowed_origins.extend(
        [
            f"http://localhost:{api_port}",
            f"http://127.0.0.1:{api_port}",
        ],
    )

    # Add configured origins if available
    if hasattr(env_config, "cors_allowed_origins") and env_config.cors_allowed_origins:
        # Assume comma-separated string
        additional_origins = [origin.strip() for origin in env_config.cors_allowed_origins.split(",")]
        allowed_origins.extend(additional_origins)

    return allowed_origins


# Create async Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=_get_allowed_cors_origins(),
    logger=False,  # Disable Socket.IO's own logging to avoid recursion
    engineio_logger=False,
)

# Track connected clients and their workflow subscriptions
connected_clients: dict[str, set[str]] = defaultdict(set)

# Track connected clients and their agent stream subscriptions
agent_stream_clients: dict[str, set[str]] = defaultdict(set)

# Session-based storage for agent stream output (for replay to late subscribers)
agent_session_storage: dict[str, list[dict[str, Any]]] = defaultdict(list)

# Logger for Socket.IO events
sio_logger = get_logger(LoggerComponent.SOCKETIO)


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> bool:
    """Handle client connection with authentication.

    Args:
        sid: Socket ID
        environ: Environment data
        auth: Authentication data (can contain 'token' field)

    Returns:
        True to accept connection, False to reject

    """
    sio_logger.debug(f"Socket.IO client connection attempt: {sid}")

    env_config = EnvConfig.get_env_config()

    # Skip authentication entirely when disabled
    if env_config.public_auth_mode.lower() == "none":
        sio_logger.debug(f"Socket.IO client connected (auth disabled): {sid}")
        connected_clients[sid] = set()
        return True

    # Authentication is enabled - extract token from multiple sources
    token = None

    # 1. From auth dict (when client provides auth object)
    if auth and isinstance(auth, dict):
        token = auth.get("token")
        sio_logger.debug("Using token from auth object")

    # 2. From query parameters (when client provides token in URL)
    if not token and "QUERY_STRING" in environ:
        query_string = environ["QUERY_STRING"]
        if "token=" in query_string:
            # Simple extraction from query string
            for param in query_string.split("&"):
                if param.startswith("token="):
                    token = param.split("=", 1)[1]
                    sio_logger.debug("Using token from query parameter")
                    break

    # Validate the service token
    if not validate_service_token(token):
        # For frontend connections without a token, check if auth is disabled
        # or allow connections in development mode
        env_config = EnvConfig.get_env_config()
        if env_config.public_auth_mode.lower() != "none":
            sio_logger.warning(f"Unauthorized Socket.IO connection attempt from {sid} - allowing for development")
            # TODO: In production, this should return False
            # See AWA-318 - https://slalom.atlassian.net/browse/AWA-318
            # return False
        else:
            sio_logger.debug("Auth disabled, allowing connection")

    sio_logger.debug(f"Socket.IO client authenticated and connected: {sid}")
    connected_clients[sid] = set()
    return True


@sio.event
async def disconnect(sid: str) -> None:
    """Handle client disconnection.

    Args:
        sid: Socket ID

    """
    # Leave all workflow rooms
    for workflow_id in connected_clients[sid]:
        await sio.leave_room(sid, workflow_id)

    # Leave all agent stream rooms
    for session_id in agent_stream_clients[sid]:
        room_name = f"agent-stream-{session_id}"
        await sio.leave_room(sid, room_name)

    del connected_clients[sid]
    del agent_stream_clients[sid]
    sio_logger.debug(f"Socket.IO client disconnected: {sid}")


@sio.event
async def subscribe_workflow(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Subscribe to a workflow's logs.

    Args:
        sid: Socket ID
        data: Subscription data containing workflow_id

    Returns:
        Response with subscription status

    """
    workflow_id = data.get("workflow_id")
    sio_logger.debug(f"subscribe_workflow called by {sid} for workflow_id: {workflow_id}")

    if not workflow_id:
        return {"status": "error", "message": "workflow_id required"}

    # Join the room for this workflow
    await sio.enter_room(sid, workflow_id)
    connected_clients[sid].add(workflow_id)

    room_size = len([s for s, rooms in connected_clients.items() if workflow_id in rooms])
    sio_logger.debug(f"Client {sid} joined room '{workflow_id}' - total clients in room: {room_size}")
    sio_logger.debug(f"Client {sid} subscribed to workflow {workflow_id}")

    # Send recent logs if available (last 100 lines)
    await send_recent_logs(sid, workflow_id)

    return {"status": "subscribed", "workflow_id": workflow_id}


async def _write_to_worker_file(worker_name: str, log_entry: dict[str, Any]) -> None:
    """Write log entry to worker-specific log file.

    Args:
        worker_name: Name of the worker (from source field)
        log_entry: Log data to write

    """
    # Skip creating worker log file for core worker (awa-worker)
    # Core worker logs go to app.log since they share the same terminal
    if worker_name == CORE_WORKER_NAME:
        return

    # Apply centralized filtering - skip if this log shouldn't be in worker file
    if not should_include_in_worker_log(log_entry):
        return

    # Get log directory from config
    log_dir = Path(EnvConfig.get_env_config().log_path)
    workers_dir = log_dir / "workers"

    # Create workers directory if it doesn't exist
    workers_dir.mkdir(parents=True, exist_ok=True)

    # Create worker log file path
    worker_log_path = workers_dir / f"{worker_name}.log"

    # Extract log data
    timestamp_str = log_entry.get("timestamp")
    if timestamp_str and timestamp_str != "None":
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            timestamp = datetime.now(UTC)
    else:
        timestamp = datetime.now(UTC)
    level = log_entry.get("level", "INFO")
    component = log_entry.get("component", "AWA")
    message = log_entry.get("message", "")

    # Truncate very large messages to prevent file write issues
    if isinstance(message, str) and len(message.encode("utf-8")) > MAX_LOG_MESSAGE_SIZE:
        # Truncate message and add indicator
        truncated_bytes = message.encode("utf-8")[: MAX_LOG_MESSAGE_SIZE - 100]  # Leave room for suffix
        message = truncated_bytes.decode("utf-8", errors="ignore")
        message += "\n... [MESSAGE TRUNCATED - exceeded size limit]"

    # Format the log entry for text file
    log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | {level: <8} | {component: <12} | {message}"

    # Write to worker log file
    try:
        with worker_log_path.open("a", encoding="utf-8") as f:
            f.write(log_line + "\n")
            f.flush()
    except Exception:
        sio_logger.exception(f"Failed to write to worker log file: {worker_log_path}")

    # Write JSON format worker log file if enabled using Loguru's native serialization
    if EnvConfig.get_env_config().log_enable_json:
        json_worker_log_path = worker_log_path.with_suffix(".json")

        # Create a temporary logger for JSON serialization
        from loguru import logger as json_logger

        # Build context ensuring no duplicate kwargs
        base_context: dict[str, Any] = {
            "component": component,
            "worker_name": worker_name,
        }
        if log_entry.get("workflow_id"):
            base_context["workflow_id"] = log_entry["workflow_id"]
        if log_entry.get("top_level_workflow_id"):
            base_context["top_level_workflow_id"] = log_entry["top_level_workflow_id"]
        if log_entry.get("workflow_type"):
            base_context["workflow_type"] = log_entry["workflow_type"]
        if log_entry.get("top_level_workflow_type"):
            base_context["top_level_workflow_type"] = log_entry["top_level_workflow_type"]

        extra_fields = {
            k: v
            for k, v in (log_entry.get("extra", {}) or {}).items()
            if k
            not in {
                "component",
                "workflow_id",
                "top_level_workflow_id",
                "workflow_type",
                "top_level_workflow_type",
                "worker_name",
            }
        }
        base_context.update(extra_fields)

        context_logger = json_logger.bind(**base_context)

        # Add a temporary JSON sink with Loguru's native serialization
        handler_id = json_logger.add(
            sink=str(json_worker_log_path),
            serialize=True,  # Loguru's native JSON serialization
            level=0,  # Accept all levels since we're already filtering
            enqueue=True,
            catch=False,
        )

        try:
            # Log the message with the proper level
            context_logger.log(level, message)
        finally:
            # Remove the temporary handler
            json_logger.remove(handler_id)


def _parse_timestamp(timestamp_str: str | None) -> datetime:
    """Parse timestamp string or return current time.

    Args:
        timestamp_str: ISO format timestamp string or None

    Returns:
        Parsed datetime or current UTC time

    """
    if timestamp_str and timestamp_str != "None":
        try:
            return datetime.fromisoformat(timestamp_str)
        except (ValueError, TypeError):
            return datetime.now(UTC)
    return datetime.now(UTC)


def _truncate_message(message: str) -> str:
    """Truncate message if it exceeds size limit.

    Args:
        message: Message to potentially truncate

    Returns:
        Truncated message with indicator if needed

    """
    if isinstance(message, str) and len(message.encode("utf-8")) > MAX_LOG_MESSAGE_SIZE:
        truncated_bytes = message.encode("utf-8")[: MAX_LOG_MESSAGE_SIZE - 100]
        truncated_message = truncated_bytes.decode("utf-8", errors="ignore")
        return truncated_message + "\n... [MESSAGE TRUNCATED - exceeded size limit]"
    return message


async def _handle_core_worker_logs(data: dict[str, Any], workflow_id: str) -> None:
    """Handle logs from the core AWA worker.

    Core worker logs are handled specially:
    - Top-level workflows: Skip file writing (handled by core worker's interceptor)
    - Child workflows: Write to file (core worker doesn't set up file logging for children)

    Args:
        data: Log entry data
        workflow_id: Workflow ID

    """
    timestamp = _parse_timestamp(data.get("timestamp"))
    streaming_message = _truncate_message(data.get("message", ""))

    # Check for top-level workflow ID for child workflows
    extra_data = data.get("extra", {})
    top_level_workflow_id = extra_data.get("top_level_workflow_id")
    top_level_workflow_type = extra_data.get("top_level_workflow_type")
    is_top_level = extra_data.get("is_top_level", True)  # Default to True for backward compat

    # Extract component and level
    component = data.get("component", "AWA")
    level = data.get("level", "INFO")

    # For child workflows, we need to write to the workflow log file
    # because the core worker only sets up file logging for top-level workflows
    if not is_top_level and top_level_workflow_id and component in {LoggerComponent.WORKFLOW, LoggerComponent.ACTIVITY}:
        # Get the log file path using top-level workflow info
        log_file_path = get_workflow_log_path(top_level_workflow_id, top_level_workflow_type)

        # Write text format log file
        log_line = (
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
            f"{level: <8} | {component: <12} | {workflow_id} | {streaming_message}"
        )

        try:
            with log_file_path.open("a", encoding="utf-8") as f:
                f.write(log_line + "\n")
                f.flush()
        except Exception:
            sio_logger.exception(f"Failed to write child workflow log to file: {log_file_path}")

        # Write JSON format log if enabled
        workflow_type = data.get("workflow_type") or extra_data.get("workflow_type")
        await _write_workflow_json_log(
            log_file_path=log_file_path,
            data=data,
            component=component,
            workflow_id=workflow_id,
            message=streaming_message,
            level=level,
            top_level_workflow_id=top_level_workflow_id,
            top_level_workflow_type=top_level_workflow_type,
            workflow_type=workflow_type,
        )

    # Filter out AWA-WORKER logs from being emitted
    if component != LoggerComponent.WORKER:
        # For child workflows, emit to the top-level workflow's room
        emit_workflow_id = top_level_workflow_id if top_level_workflow_id else workflow_id

        await emit_log_entry(
            workflow_id=emit_workflow_id,
            level=level,
            component=component,
            message=streaming_message,
            timestamp=timestamp,
            extra=data.get("extra"),
        )


async def _write_workflow_json_log(
    log_file_path: Path,
    data: dict[str, Any],
    component: str,
    workflow_id: str,
    message: str,
    level: str,
    top_level_workflow_id: str | None,
    top_level_workflow_type: str | None,
    workflow_type: str | None,
) -> None:
    """Write JSON format log if enabled.

    Args:
        log_file_path: Base log file path
        data: Original log data
        component: Component name
        workflow_id: Workflow ID
        message: Log message
        level: Log level
        top_level_workflow_id: Top-level workflow ID if child
        top_level_workflow_type: Top-level workflow type if child
        workflow_type: Workflow type

    """
    if not EnvConfig.get_env_config().log_enable_json:
        return

    json_log_path = log_file_path.with_suffix(".json")

    # Create a temporary logger for JSON serialization
    from loguru import logger as json_logger

    # Build context ensuring no duplicate kwargs
    base_context: dict[str, Any] = {
        "component": component,
        "workflow_id": workflow_id,
        "top_level_workflow_id": top_level_workflow_id,
        "top_level_workflow_type": top_level_workflow_type,
        "workflow_type": workflow_type,
        "is_top_level": (top_level_workflow_id == workflow_id) if top_level_workflow_id else True,
    }
    extra_fields = {
        k: v
        for k, v in (data.get("extra", {}) or {}).items()
        if k
        not in {
            "component",
            "workflow_id",
            "top_level_workflow_id",
            "workflow_type",
            "top_level_workflow_type",
            "is_top_level",
        }
    }
    base_context.update(extra_fields)

    context_logger = json_logger.bind(**base_context)

    # Add a temporary JSON sink with Loguru's native serialization
    handler_id = json_logger.add(
        sink=str(json_log_path),
        serialize=True,  # Loguru's native JSON serialization
        level=0,  # Accept all levels since we're already filtering
        enqueue=True,
        catch=False,
    )

    try:
        # Log the message with the proper level
        context_logger.log(level, message)
    finally:
        # Remove the temporary handler
        json_logger.remove(handler_id)


@sio.event
async def forward_log(sid: str, data: dict[str, Any]) -> None:  # noqa: ARG001
    """Handle forwarded log entries from workers.

    This is the centralized log routing and filtering logic for all worker logs.
    Workers send ALL logs here, and we decide where they should go:

    1. Worker log files: Non-workflow/activity logs (filtered by should_include_in_worker_log)
    2. Workflow log files: All logs with a workflow_id
    3. Real-time UI streaming: Logs for subscribed clients

    Args:
        sid: Socket ID (from worker)
        data: Log entry data

    """
    workflow_id = data.get("workflow_id")
    worker_name = data.get("source")

    # Route to worker log file (applies filtering)
    if worker_name:
        await _write_to_worker_file(worker_name, data)

    # If there is no workflow_id, we don't need to continue processing
    # (likely a log from a non-workflow process)
    if not workflow_id:
        return

    # Skip workflow file writing for core worker logs to prevent duplication
    # The core worker's interceptor handles workflow file logging directly
    if worker_name == CORE_WORKER_NAME:
        await _handle_core_worker_logs(data, workflow_id)
        return

    # For remote workers (cookbook, etc.), write to workflow log files
    # Extract workflow metadata - check both top-level and extra fields
    extra_data = data.get("extra", {})
    workflow_type = data.get("workflow_type") or extra_data.get("workflow_type")
    top_level_workflow_type = data.get("top_level_workflow_type") or extra_data.get("top_level_workflow_type")
    top_level_workflow_id = data.get("top_level_workflow_id") or extra_data.get("top_level_workflow_id")

    # Determine the correct path - use top-level info if this is a child workflow
    workflow_id_for_path = top_level_workflow_id or workflow_id
    workflow_type_for_path = top_level_workflow_type or workflow_type

    log_file_path = get_workflow_log_path(workflow_id_for_path, workflow_type_for_path)

    # Extract log data
    level = data.get("level", "INFO")
    component = data.get("component", "AWA")
    message = _truncate_message(data.get("message", ""))
    timestamp = _parse_timestamp(data.get("timestamp"))

    # Filter AWA-WORKER logs from remote workers - they should only appear in worker terminal
    # Only write AWA-WORKFLOW and AWA-ACTIVITY logs to workflow log files
    if component != LoggerComponent.WORKER:
        # Write text format log file
        log_line = (
            f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} | "
            f"{level: <8} | {component: <12} | {workflow_id} | {message}"
        )

        try:
            with log_file_path.open("a", encoding="utf-8") as f:
                f.write(log_line + "\n")
                f.flush()
        except Exception:
            sio_logger.exception(f"Failed to write to workflow log file: {log_file_path}")

        # Write JSON format log file if enabled
        await _write_workflow_json_log(
            log_file_path=log_file_path,
            data=data,
            component=component,
            workflow_id=workflow_id,
            message=message,
            level=level,
            top_level_workflow_id=top_level_workflow_id,
            top_level_workflow_type=top_level_workflow_type,
            workflow_type=workflow_type,
        )

    # Emit to UI clients for real-time streaming (message already truncated above)
    # Filter out AWA-WORKER logs from non-core workers - they should only appear in the worker terminal
    # AWA-WORKFLOW and AWA-ACTIVITY logs should be forwarded to the invoking terminal
    if component != LoggerComponent.WORKER:
        # For child workflows, emit to the top-level workflow's room so CLI clients can see all logs
        emit_workflow_id = top_level_workflow_id if top_level_workflow_id else workflow_id
        await emit_log_entry(
            workflow_id=emit_workflow_id,
            level=level,
            component=component,
            message=message,  # Already truncated in the message processing above
            timestamp=timestamp,  # Use the already parsed timestamp from above
            extra=data.get("extra"),
        )


@sio.event
async def join_hitl_chat(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Join a HITL task chat room for real-time chat updates.

    Args:
        sid: Socket ID
        data: Chat join data containing task_id

    Returns:
        Response with join status

    """
    task_id = data.get("task_id")
    sio_logger.debug(f"join_hitl_chat called by {sid} for task_id: {task_id}")

    if not task_id:
        return {"status": "error", "message": "task_id required"}

    # Join the room for this HITL task chat
    chat_room = f"hitl_chat_{task_id}"
    await sio.enter_room(sid, chat_room)
    connected_clients[sid].add(chat_room)

    room_size = len([s for s, rooms in connected_clients.items() if chat_room in rooms])
    sio_logger.debug(f"Client {sid} joined chat room '{chat_room}' - total clients in room: {room_size}")

    return {"status": "joined", "task_id": task_id, "room": chat_room}


@sio.event
async def leave_hitl_chat(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Leave a HITL task chat room.

    Args:
        sid: Socket ID
        data: Chat leave data containing task_id

    Returns:
        Response with leave status

    """
    task_id = data.get("task_id")
    if not task_id:
        return {"status": "error", "message": "task_id required"}

    # Leave the chat room
    chat_room = f"hitl_chat_{task_id}"
    await sio.leave_room(sid, chat_room)
    connected_clients[sid].discard(chat_room)

    sio_logger.debug(f"Client {sid} left chat room '{chat_room}'")

    return {"status": "left", "task_id": task_id, "room": chat_room}


@sio.event
async def send_hitl_chat_message(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Send a chat message in a HITL task chat room.

    Args:
        sid: Socket ID
        data: Chat message data containing task_id, message, and optional user info

    Returns:
        Response with send status

    """
    task_id = data.get("task_id")
    message = data.get("message")
    user_info = data.get("user_info", {})

    if not task_id or not message:
        return {"status": "error", "message": "task_id and message are required"}

    # Emit the chat message to all clients in the chat room
    chat_room = f"hitl_chat_{task_id}"

    chat_message = {
        "task_id": task_id,
        "message": message,
        "user_info": user_info,
        "timestamp": datetime.now(UTC).isoformat(),
        "is_human": True,
    }

    await sio.emit("hitl_chat_message", chat_message, room=chat_room)

    sio_logger.debug(f"Chat message sent to room '{chat_room}' from client {sid}")

    return {"status": "sent", "task_id": task_id}


@sio.event
async def unsubscribe_workflow(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Unsubscribe from a workflow's logs.

    Args:
        sid: Socket ID
        data: Unsubscription data containing workflow_id

    Returns:
        Response with unsubscription status

    """
    workflow_id = data.get("workflow_id")
    if not workflow_id:
        return {"status": "error", "message": "workflow_id required"}

    # Leave the room
    await sio.leave_room(sid, workflow_id)
    connected_clients[sid].discard(workflow_id)

    sio_logger.debug(f"Client {sid} unsubscribed from workflow {workflow_id}")

    return {"status": "unsubscribed", "workflow_id": workflow_id}


@sio.event
async def subscribe_agent_stream(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Subscribe to an agent session's stream output.

    Args:
        sid: Socket ID
        data: Subscription data containing session_id

    Returns:
        Response with subscription status

    """
    session_id = data.get("session_id")

    if not session_id:
        return {"status": "error", "message": "session_id required"}

    # Join the room for this agent stream
    room_name = f"agent-stream-{session_id}"
    await sio.enter_room(sid, room_name)
    agent_stream_clients[sid].add(session_id)

    # Send stored output if available for immediate replay
    await send_agent_session_history(sid, session_id)

    return {"status": "subscribed", "session_id": session_id}


@sio.event
async def unsubscribe_agent_stream(sid: str, data: dict[str, Any]) -> dict[str, Any]:
    """Unsubscribe from an agent session's stream output.

    Args:
        sid: Socket ID
        data: Unsubscription data containing session_id

    Returns:
        Response with unsubscription status

    """
    session_id = data.get("session_id")
    if not session_id:
        return {"status": "error", "message": "session_id required"}

    # Leave the room
    room_name = f"agent-stream-{session_id}"
    await sio.leave_room(sid, room_name)
    agent_stream_clients[sid].discard(session_id)

    sio_logger.debug(f"Client {sid} unsubscribed from agent stream {session_id}")

    return {"status": "unsubscribed", "session_id": session_id}


async def send_agent_session_history(sid: str, session_id: str) -> None:
    """Send stored agent session output to a newly subscribed client.

    Args:
        sid: Socket ID
        session_id: Agent session ID

    """
    stored_output = agent_session_storage.get(session_id, [])
    if stored_output:
        try:
            # Send stored output as a batch for immediate replay
            await sio.emit(
                "agent_stream_history",
                {
                    "session_id": session_id,
                    "history": stored_output,
                },
                room=sid,
            )
            sio_logger.info(f"Replayed {len(stored_output)} events to client for session {session_id}")
        except Exception:
            sio_logger.exception(f"Error sending agent session history for session {session_id}")


async def emit_agent_stream_start(session_id: str, agent_type: str | None = None) -> None:
    """Emit agent stream start notification to subscribed clients.

    Args:
        session_id: Agent session ID
        agent_type: Type of agent (optional)

    """
    room_name = f"agent-stream-{session_id}"

    start_notification = {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "agent_type": agent_type,
        "status": "started",
    }

    # Store the start notification
    agent_session_storage[session_id].append(
        {
            "type": "start",
            **start_notification,
        },
    )

    # Emit to all clients in the agent stream room
    await sio.emit("agent_stream_start", start_notification, room=room_name)
    sio_logger.debug(f"Emitted agent stream start for session {session_id}")


async def emit_agent_stream_output(
    session_id: str,
    content: str,
    chunk_index: int,
    is_final: bool = False,
    agent_type: str | None = None,
    timestamp: datetime | None = None,
) -> None:
    """Emit real-time agent output to subscribed clients (separate from emit_log_entry).

    Args:
        session_id: Agent session ID
        content: Content chunk from agent
        chunk_index: Index of this chunk in the sequence
        is_final: Whether this is the final chunk
        agent_type: Type of agent (optional)
        timestamp: Output timestamp (defaults to current time)

    """
    room_name = f"agent-stream-{session_id}"

    output_entry = {
        "session_id": session_id,
        "content": content,
        "chunk_index": chunk_index,
        "is_final": is_final,
        "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
        "agent_type": agent_type,
    }

    # Store the output for replay to late subscribers
    agent_session_storage[session_id].append(
        {
            "type": "output",
            **output_entry,
        },
    )

    # Emit to all clients in the agent stream room
    await sio.emit("agent_stream_output", output_entry, room=room_name)


async def emit_agent_stream_complete(
    session_id: str,
    final_result: dict[str, Any] | None = None,
    execution_time: float | None = None,
    agent_type: str | None = None,
) -> None:
    """Emit agent execution completion notification to subscribed clients.

    Args:
        session_id: Agent session ID
        final_result: Final result data (optional)
        execution_time: Total execution time in seconds (optional)
        agent_type: Type of agent (optional)

    """
    room_name = f"agent-stream-{session_id}"

    completion_notification = {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "final_result": final_result,
        "execution_time": execution_time,
        "agent_type": agent_type,
        "status": "completed",
    }

    # Store the completion notification
    agent_session_storage[session_id].append(
        {
            "type": "complete",
            **completion_notification,
        },
    )

    # Emit to all clients in the agent stream room
    await sio.emit("agent_stream_complete", completion_notification, room=room_name)
    sio_logger.debug(f"Emitted agent stream completion for session {session_id}")


async def emit_agent_stream_error(
    session_id: str,
    error_message: str,
    error_code: str | None = None,
    agent_type: str | None = None,
) -> None:
    """Emit agent execution error notification to subscribed clients.

    Args:
        session_id: Agent session ID
        error_message: Error message to send
        error_code: Error code for categorization (optional)
        agent_type: Type of agent (optional)

    """
    room_name = f"agent-stream-{session_id}"

    error_notification = {
        "session_id": session_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "error": error_message,
        "error_code": error_code,
        "agent_type": agent_type,
        "status": "error",
    }

    # Store the error notification
    agent_session_storage[session_id].append(
        {
            "type": "error",
            **error_notification,
        },
    )

    # Emit to all clients in the agent stream room
    await sio.emit("agent_stream_error", error_notification, room=room_name)
    sio_logger.debug(f"Emitted agent stream error for session {session_id}: {error_message}")


async def cleanup_agent_session(session_id: str) -> None:
    """Clean up completed agent session data.

    Args:
        session_id: Agent session ID to clean up

    """
    if session_id in agent_session_storage:
        stored_count = len(agent_session_storage[session_id])
        del agent_session_storage[session_id]
        sio_logger.debug(f"Cleaned up agent session {session_id} - removed {stored_count} stored entries")


async def send_recent_logs(sid: str, workflow_id: str, limit: int = 100) -> None:
    """Send recent logs to a newly connected client.

    Args:
        sid: Socket ID
        workflow_id: Workflow ID
        limit: Maximum number of recent logs to send

    """
    # Check if we have a log file for this workflow
    log_file_path = find_workflow_log_file(workflow_id)
    if log_file_path and log_file_path.exists():
        try:
            # Read last N lines from log file
            with log_file_path.open() as f:
                lines = f.readlines()
                recent_lines = lines[-limit:] if len(lines) > limit else lines

            # Send as a batch
            await sio.emit(
                "log_history",
                {
                    "workflow_id": workflow_id,
                    "logs": [line.rstrip() for line in recent_lines],
                },
                room=sid,
            )
        except Exception:
            sio_logger.exception(f"Error sending recent logs for workflow {workflow_id}")


async def emit_log_entry(
    workflow_id: str,
    level: str,
    component: str,
    message: str,
    timestamp: datetime | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a log entry to all clients subscribed to a workflow.

    Args:
        workflow_id: Workflow ID
        level: Log level
        component: Component name
        message: Log message
        timestamp: Log timestamp
        extra: Additional context

    """
    log_entry = {
        "workflow_id": workflow_id,
        "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
        "level": level,
        "component": component,
        "message": message,
        **(extra or {}),
    }

    # Emit to all clients in the workflow room
    await sio.emit("log_entry", log_entry, room=workflow_id)


async def emit_hitl_system_message(
    task_id: str,
    message: str,
    data: dict[str, Any] | None = None,
    timestamp: datetime | None = None,
    is_human: bool = False,
) -> None:
    """Emit a message to all clients in a HITL task chat room.

    Args:
        task_id: HITL task ID
        message: Message content
        data: Optional structured data
        timestamp: Message timestamp
        is_human: Whether this is a human message (default: False for system messages)

    """
    chat_room = f"hitl_chat_{task_id}"

    chat_message = {
        "task_id": task_id,
        "message": message,
        "data": data,
        "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
        "is_human": is_human,
    }

    await sio.emit("hitl_chat_message", chat_message, room=chat_room)


async def emit_pydantic_ai_streaming_event(
    session_id: str,
    event_type: str,
    event_data: dict[str, Any],
    timestamp: datetime | None = None,
) -> None:
    """Emit a PydanticAI streaming event to all clients subscribed to the session.

    This function broadcasts real-time streaming events from PydanticAI agent execution
    to clients listening for streaming updates.

    Args:
        session_id: Session ID (typically workflow_id) for the streaming session
        event_type: Type of the streaming event (e.g., 'execution_start', 'model_response_delta')
        event_data: Event-specific data payload
        timestamp: Event timestamp

    """
    streaming_event = {
        "session_id": session_id,
        "event_type": event_type,
        "event_data": event_data,
        "timestamp": (timestamp or datetime.now(UTC)).isoformat(),
    }

    # Emit to the workflow room (session_id is typically the workflow_id)
    await sio.emit("pydantic_ai_streaming_event", streaming_event, room=session_id)

    sio_logger.debug(f"📡 Emitted PydanticAI streaming event '{event_type}' for session {session_id}")


# Global reference to Socket.IO app for mounting
def get_socketio_app() -> socketio.ASGIApp:
    """Get the Socket.IO ASGI app for mounting in FastAPI.

    Returns:
        Socket.IO ASGI application

    """
    return socketio.ASGIApp(sio)
