"""Socket.IO client for receiving workflow logs in CLI."""

import contextlib
import os
import time
from typing import Any

import socketio
from loguru import logger

from awa.core.models.config.env_config import EnvConfig


class WorkflowLogReceiver:
    """Receives and displays workflow logs via Socket.IO."""

    def __init__(self) -> None:
        """Initialize the Socket.IO client."""
        self.sio = socketio.Client(
            reconnection=False,  # Don't reconnect automatically
            logger=False,  # Disable Socket.IO logging
            engineio_logger=False,
        )
        self.connected = False
        self.workflow_id: str | None = None

        # Get service token for authentication if available
        self.service_token = os.getenv("AWA_SERVICE_TOKEN")
        if self.service_token:
            logger.debug("CLI service token found for SocketIO authentication")
        else:
            logger.debug("No CLI service token configured")

        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up Socket.IO event handlers."""

        @self.sio.event
        def connect() -> None:
            """Handle connection to server."""
            self.connected = True
            if self.workflow_id:
                # Subscribe to workflow logs
                self.sio.emit("subscribe_workflow", {"workflow_id": self.workflow_id})

        @self.sio.event
        def disconnect() -> None:
            """Handle disconnection from server."""
            self.connected = False

        @self.sio.event
        def log_entry(data: dict[str, Any]) -> None:
            """Handle received log entries."""
            # Extract log data
            level = data.get("level", "INFO")
            component = data.get("component", "AWA")
            message = data.get("message", "")
            workflow_id = data.get("workflow_id", "")

            # For workflow logs received via Socket.IO, we need to display them directly
            # because the main logger filters out workflow logs to prevent double logging
            import sys

            from loguru import logger

            # Create a temporary logger configuration just for this output
            # This bypasses the filtering that prevents workflow logs from appearing
            handler_id = logger.add(
                sink=sys.stdout,
                format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                f"<cyan>{component: <12}</cyan> | "
                f"<yellow>{workflow_id}</yellow> | "
                "<level>{message}</level>\n",
                level=level,
                colorize=True,
                filter=lambda _: True,  # Don't filter anything
                enqueue=False,  # Immediate output
            )

            # Log the message with bound context to preserve component and workflow_id
            bound_logger = logger.bind(component=component, workflow_id=workflow_id)
            log_method = getattr(bound_logger, level.lower(), bound_logger.info)
            log_method(message)

            # Remove the temporary handler
            logger.remove(handler_id)

            # Force flush to ensure immediate output
            sys.stdout.flush()

        @self.sio.event
        def log_history(data: dict[str, Any]) -> None:
            """Handle historical logs batch."""
            logs = data.get("logs", [])
            for log_line in logs:
                logger.info(log_line)

    def connect_and_subscribe(self, workflow_id: str) -> bool:
        """Connect to Socket.IO server and subscribe to workflow logs.

        Args:
            workflow_id: Workflow ID to subscribe to

        Returns:
            True if connected successfully, False otherwise

        """
        self.workflow_id = workflow_id

        try:
            # Get server URL from environment config
            env_config = EnvConfig.get_env_config()
            server_url = f"http://{env_config.awa_api_host}:{env_config.awa_api_port}"

            # Connect to server with authentication if available
            auth_data = {"token": self.service_token} if self.service_token else None
            self.sio.connect(
                server_url,
                auth=auth_data,
                transports=["websocket", "polling"],
            )

            # Wait briefly for connection and subscription
            # This is synchronous but quick
            time.sleep(0.1)

            return self.connected
        except (ConnectionError, OSError, TimeoutError) as e:
            logger.debug(f"Failed to connect to Socket.IO server: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Socket.IO server."""
        if self.connected and self.workflow_id:
            # Unsubscribe from workflow
            self.sio.emit("unsubscribe_workflow", {"workflow_id": self.workflow_id})

        if self.sio.connected:
            self.sio.disconnect()

    def run_in_background(self) -> None:
        """Run the Socket.IO client in a background thread."""
        # The client needs to run its event loop
        # This will block until disconnected
        with contextlib.suppress(Exception):
            self.sio.wait()
