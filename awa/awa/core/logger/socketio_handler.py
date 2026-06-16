"""Socket.IO log handler for streaming logs to the central server.

This handler forwards logs from any process to the Socket.IO server
for real-time streaming and aggregation.
"""

import contextlib
import json
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime
from queue import Empty, Queue

import socketio as socketio_client
from loguru import logger

from awa.core.constants import MAX_LOG_MESSAGE_SIZE
from awa.core.logger.workflow_context import workflow_context
from awa.core.models.config.env_config import EnvConfig

# Create a separate logger for Socket.IO handler to avoid recursion
socketio_logger = logging.getLogger("socketio_handler")
socketio_logger.setLevel(logging.WARNING)  # Only log warnings and errors


class SocketIOLogHandler:
    """Handler that forwards logs to Socket.IO server.

    This handler:
    1. Connects to the Socket.IO server
    2. Buffers logs if disconnected
    3. Forwards logs with workflow context
    4. Handles reconnection automatically
    """

    def __init__(
        self,
        server_url: str | None = None,
        source_name: str = "unknown",
        filter_func: Callable[[dict], bool] | None = None,
    ) -> None:
        """Initialize the Socket.IO log handler.

        Args:
            server_url: Socket.IO server URL (defaults to API URL)
            source_name: Name of this log source (e.g., "recipes-worker")
            filter_func: Optional filter function for logs

        """
        self.server_url = server_url or self._get_default_server_url()
        self.source_name = source_name
        self.filter_func = filter_func

        # Get service token from environment for authentication
        self.service_token = os.getenv("AWA_SERVICE_TOKEN")
        if self.service_token:
            socketio_logger.debug("Core service token found for SocketIO authentication")
        else:
            socketio_logger.debug("No core service token configured")

        # Socket.IO client
        self.sio = socketio_client.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite attempts
            reconnection_delay=1,
            reconnection_delay_max=30,
            logger=False,  # Disable Socket.IO logging to avoid recursion
            engineio_logger=False,
        )

        # Log buffer for when disconnected
        self.buffer: Queue[dict] = Queue(maxsize=10000)
        self.connected = False

        # Background thread for Socket.IO client
        self.client_thread: threading.Thread | None = None
        self.stop_event = threading.Event()

        # Set up event handlers
        self._setup_handlers()

        # Start the client
        self.start()

    def _get_default_server_url(self) -> str:
        """Get default server URL from environment config."""
        env_config = EnvConfig.get_env_config()
        host = env_config.awa_api_host
        port = env_config.awa_api_port
        return f"http://{host}:{port}"

    def _setup_handlers(self) -> None:
        """Set up Socket.IO event handlers."""

        @self.sio.event
        def connect() -> None:
            """Handle connection to server."""
            self.connected = True
            socketio_logger.info(f"SocketIO log handler connected to {self.server_url}")

            # Flush buffered logs
            self._flush_buffer()

        @self.sio.event
        def disconnect() -> None:
            """Handle disconnection from server."""
            self.connected = False
            socketio_logger.warning("SocketIO log handler disconnected from server")

    def start(self) -> None:
        """Start the Socket.IO client in a background thread."""
        if self.client_thread and self.client_thread.is_alive():
            return

        self.client_thread = threading.Thread(
            target=self._run_client,
            daemon=True,
            name=f"SocketIOLogHandler-{self.source_name}",
        )
        self.client_thread.start()

    def _run_client(self) -> None:
        """Run the Socket.IO client (blocking)."""
        while not self.stop_event.is_set():
            try:
                # Only connect if not already connected
                if not self.sio.connected:
                    # Connect to server with authentication if available
                    auth_data = {"token": self.service_token} if self.service_token else None
                    self.sio.connect(
                        self.server_url,
                        auth=auth_data,
                        transports=["websocket", "polling"],
                    )

                # Wait while connected
                while self.connected and not self.stop_event.is_set():
                    self.sio.sleep(1)

            except Exception:
                socketio_logger.exception("SocketIO connection error")
                self.connected = False

            # Wait before reconnecting
            if not self.stop_event.is_set():
                self.stop_event.wait(5)

    def stop(self) -> None:
        """Stop the Socket.IO client."""
        self.stop_event.set()
        if self.sio.connected:
            self.sio.disconnect()
        if self.client_thread:
            self.client_thread.join(timeout=5)

    def _flush_buffer(self) -> None:
        """Flush buffered logs to server."""
        flushed = 0
        while not self.buffer.empty() and self.connected:
            try:
                log_entry = self.buffer.get_nowait()
                self._send_log(log_entry)
                flushed += 1
            except Empty:
                break
            except Exception:
                socketio_logger.exception("Error flushing log")
                # Put it back in the buffer
                with contextlib.suppress(Exception):
                    self.buffer.put_nowait(log_entry)
                break

        if flushed > 0:
            socketio_logger.debug(f"Flushed {flushed} buffered logs")

    def _send_log(self, log_entry: dict) -> None:
        """Send a log entry to the server.

        Args:
            log_entry: Log entry to send

        """
        if not self.connected:
            # Buffer the log
            try:
                self.buffer.put_nowait(log_entry)
            except Exception:  # noqa: BLE001
                # Buffer full, drop oldest
                with contextlib.suppress(Exception):
                    self.buffer.get_nowait()
                    self.buffer.put_nowait(log_entry)
            return

        try:
            # Send via Socket.IO
            self.sio.emit("forward_log", log_entry)
        except Exception:
            socketio_logger.exception("Error sending log via Socket.IO")
            # Try to buffer it
            with contextlib.suppress(Exception):
                self.buffer.put_nowait(log_entry)

    def emit(self, message: str | dict) -> None:
        """Emit a log record to the Socket.IO server.

        Args:
            message: Either a formatted string or serialized JSON record

        """
        try:
            # If message is a string (serialized JSON), parse it
            record = json.loads(message.strip()) if isinstance(message, str) else message

            # Apply filter if provided
            if self.filter_func and not self.filter_func(record):
                return

            # Use raw record when present (serialize=True), otherwise fallback to record
            actual_record = record["record"] if "record" in record and "text" in record else record

            # Extract relevant fields from the actual record
            timestamp = actual_record.get("time", actual_record.get("timestamp"))
            if isinstance(timestamp, str) and timestamp != "None":
                # Already a valid string
                timestamp_str = timestamp
            elif hasattr(timestamp, "isoformat"):
                # It's a datetime-like object, convert to ISO format
                timestamp_str = timestamp.isoformat()
            else:
                # Fallback to current time if timestamp is invalid or None
                timestamp_str = datetime.now(UTC).isoformat()

            level_info = actual_record.get("level", {})
            level_name = level_info.get("name", "INFO") if isinstance(level_info, dict) else str(level_info)

            extra_info = actual_record.get("extra", {})
            component = extra_info.get("component", "AWA")
            workflow_id = extra_info.get("workflow_id") or workflow_context.get()
            workflow_type = extra_info.get("top_level_workflow_type")

            # Get the message - use the actual message from the record, not the formatted text
            # which includes timestamp/level/component prefixes
            message = actual_record.get("message", "")

            # If there's an exception, append the exception message for better error context
            exception_info = actual_record.get("exception")
            if exception_info and isinstance(exception_info, dict) and exception_info.get("value"):
                try:
                    exc_message = str(exception_info["value"]).strip()
                    # Only append if the exception message isn't already in the base message
                    if exc_message and exc_message not in message:
                        message += f": {exc_message}"
                except (TypeError, AttributeError):
                    # Silently skip if exception value can't be converted to string
                    pass

            # Truncate very large messages to prevent stream limit crashes
            if isinstance(message, str) and len(message.encode("utf-8")) > MAX_LOG_MESSAGE_SIZE:
                # Truncate message and add indicator
                truncated_bytes = message.encode("utf-8")[: MAX_LOG_MESSAGE_SIZE - 100]  # Leave room for suffix
                message = truncated_bytes.decode("utf-8", errors="ignore")
                message += "\n... [MESSAGE TRUNCATED - exceeded 1MB limit]"

            log_entry = {
                "source": self.source_name,
                "timestamp": timestamp_str,
                "level": level_name,
                "component": component,
                "message": message,
                "workflow_id": workflow_id,
            }

            # Add workflow type if available
            if workflow_type:
                log_entry["workflow_type"] = workflow_type

            # Add any additional extra fields
            if extra_info:
                # Exclude some fields to avoid duplication
                exclude_fields = {"component", "workflow_id"}
                extra = {k: v for k, v in extra_info.items() if k not in exclude_fields}
                if extra:
                    log_entry["extra"] = extra

            # Send the log
            self._send_log(log_entry)

        except Exception:
            # If there's an error processing the log, log to separate logger
            socketio_logger.exception("Error in emit method")


def setup_socketio_logging(
    source_name: str,
    server_url: str | None = None,
    filter_func: Callable[[dict], bool] | None = None,
    wait_for_connection: bool = True,
) -> int:
    """Set up Socket.IO log forwarding.

    Args:
        source_name: Name of this log source
        server_url: Socket.IO server URL
        filter_func: Optional filter function
        wait_for_connection: Whether to wait for initial connection

    Returns:
        Handler ID for removal

    """
    handler = SocketIOLogHandler(
        server_url=server_url,
        source_name=source_name,
        filter_func=filter_func,
    )

    # Wait for connection if requested
    if wait_for_connection:
        max_wait = 5  # seconds
        start_time = time.time()
        while not handler.connected and (time.time() - start_time) < max_wait:
            time.sleep(0.1)

    # Add to loguru with serialize=True to get raw record data
    handler_id = logger.add(
        handler.emit,
        level="DEBUG",  # Capture all levels
        enqueue=True,  # Thread-safe
        serialize=True,  # Get raw record data instead of formatted string
    )

    return handler_id
