"""Logging configuration for AWA.

This module provides:
- Component-based logging (AWA API, AWA CLI, AWA Engine)
- Temporal workflow logging integration
- Configurable file rotation
- Optional structured JSON logging
- Console and file output
"""

import contextlib
import io
import logging
import os
import platform
import re
import sys
from enum import StrEnum
from pathlib import Path
from pprint import pformat
from typing import Any

from loguru import logger
from loguru._logger import Logger

from cookbook.recipes.models.env_config import EnvConfig
from cookbook.recipes.utilities.logger.intercept_handler import InterceptHandler


class LoggerComponent(StrEnum):
    """Component identifiers for logging."""

    API = "AWA-API"
    CLI = "AWA-CLI"
    UI = "AWA-UI"
    SERVER = "AWA-SERVER"
    CLIENT = "AWA-CLIENT"
    WORKER = "AWA-WORKER"
    WORKFLOW = "AWA-WORKFLOW"
    ACTIVITY = "AWA-ACTIVITY"
    SCRIPT = "AWA-SCRIPT"
    AUTH = "AWA-AUTH"
    HTTP = "HTTP"
    COOKBOOK = "AWA-COOKBOOK"
    SOCKETIO = "SOCKETIO-CLIENT"
    LOADER = "AWA-LOADER"
    REGISTRATION = "AWA-REGISTRATION"
    ACTIVITIES = "AWA-ACTIVITIES"
    WORKFLOWS = "AWA-WORKFLOWS"


def format_record(record: dict) -> str:
    """Apply custom format for loguru loggers.

    Formats logs with component info and handles payload pretty-printing.
    """
    # Get component and workflow context
    component = record["extra"].get("component", "AWA")
    workflow_id = record["extra"].get("workflow_id")
    format_string = (
        f"<green>{{time:YYYY-MM-DD HH:mm:ss.SSS}}</green> | "
        f"<level>{{level: <8}}</level> | <cyan>{component: <12}</cyan>"
    )

    # Add workflow ID if present
    if workflow_id:
        format_string += f" | <yellow>{workflow_id}</yellow>"

    format_string += " | <level>{message}</level>"

    # Handle pretty-printed payloads
    if record["extra"].get("payload") is not None:
        record["extra"]["payload"] = pformat(
            record["extra"]["payload"],
            indent=4,
            compact=True,
            width=88,
        )
        format_string += "\n<level>{extra[payload]}</level>"

    format_string += "{exception}\n"
    return format_string


def init_logging(file_only: bool = False) -> None:
    """Initialize comprehensive logging system.

    Args:
        file_only: If True, only log to files (no console output)

    """
    # Create log directories
    log_dir = Path(EnvConfig.get_env_config().log_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers
    logger.remove()

    # Prepare handlers list
    handlers = []

    # Console handler (if enabled and not file_only)
    if not file_only and EnvConfig.get_env_config().log_console_enabled:
        handlers.append(
            {
                "sink": sys.stdout,
                "level": EnvConfig.get_env_config().log_level,
                "format": format_record,
                "colorize": True,
            },
        )

    # Single application log file for ALL logs (if enabled)
    if EnvConfig.get_env_config().log_file_enabled:
        app_log_path = log_dir / "app.log"
        handlers.append(
            {
                "sink": app_log_path,
                "level": EnvConfig.get_env_config().log_level,
                "format": format_record,
                "rotation": EnvConfig.get_env_config().log_file_rotation_size,
                "retention": "30 days",
                "compression": "zip",
            },
        )

    # JSON structured log file for ALL logs - both application and workflow (if enabled)
    if EnvConfig.get_env_config().log_enable_json:
        json_log_path = log_dir / "app.json"
        handlers.append(
            {
                "sink": json_log_path,
                "level": EnvConfig.get_env_config().log_level,
                "serialize": True,
                "rotation": EnvConfig.get_env_config().log_file_rotation_size,
                "retention": "30 days",
                "compression": "zip",
            },
        )

    # Configure loguru with all handlers
    logger.configure(handlers=handlers)

    # Install InterceptHandler to capture standard Python logging
    intercept_handler = InterceptHandler()

    # Remove existing handlers from root logger and install our interceptor
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(intercept_handler)
    root_logger.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))

    # Specifically intercept Temporal loggers and other key loggers
    temporal_loggers = [
        "temporalio.workflow",
        "temporalio.activity",
        "temporalio.worker",
        "temporalio.client",
        "temporalio",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
    ]

    for logger_name in temporal_loggers:
        temporal_logger = logging.getLogger(logger_name)
        temporal_logger.handlers.clear()
        temporal_logger.addHandler(intercept_handler)
        temporal_logger.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))
        temporal_logger.propagate = False  # Don't propagate to avoid double logging

    # Set up httpx/httpcore loggers to use HTTP component
    class HTTPInterceptHandler(InterceptHandler):
        """Intercept handler that routes HTTP library logs to HTTP component."""

        def emit(self, record: logging.LogRecord) -> None:
            # Route all httpx/httpcore logs through HTTP component
            http_logger = logger.bind(component="HTTP")
            level = record.levelname.lower()
            message = self.format(record)

            if hasattr(http_logger, level):
                getattr(http_logger, level)(message)

    # Set up httpx/httpcore with HTTP component handler
    http_handler = HTTPInterceptHandler()
    for logger_name in ["httpx", "httpcore"]:
        http_logger = logging.getLogger(logger_name)
        http_logger.handlers.clear()
        http_logger.addHandler(http_handler)
        http_logger.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))
        http_logger.propagate = False


def get_logger(
    component: LoggerComponent | str,
    **extra_context: dict[str, Any],
) -> Logger:
    """Get a logger bound to a specific component and optional workflow.

    Args:
        component: Component identifier (LoggerComponent enum or string)
        **extra_context: Additional context to bind to the logger

    Returns:
        A loguru logger bound with the specified context

    """
    # Get string value from enum or use string directly
    component_str = component.value if isinstance(component, LoggerComponent) else component

    context = {
        "component": component_str,
        **extra_context,
    }

    return logger.bind(**context)  # type: ignore[return-value]


def get_subprocess_logger(service_name: str) -> logging.Logger:
    """Get a raw subprocess logger that bypasses loguru formatting.

    These loggers write subprocess output directly to console and files
    without re-processing through loguru formatting. This prevents
    double-logging of already-formatted subprocess output.

    Args:
        service_name: Name of the service (api, ui, worker, server, temporal)

    Returns:
        A standard Python logger configured for raw subprocess output

    """
    logger_name = f"subprocess.{service_name.lower()}"

    # Get or create the subprocess logger
    subprocess_logger = logging.getLogger(logger_name)

    # Only configure if not already configured
    if not subprocess_logger.handlers:
        # Create console handler for raw output with robust encoding handling
        # On Windows, we need to handle Unicode characters more carefully

        if platform.system() == "Windows":
            # On Windows, try to set UTF-8 mode and use a more robust approach
            with contextlib.suppress(Exception):
                # Try to set UTF-8 mode for the console
                os.system("chcp 65001 > nul 2>&1")  # noqa: S605, S607

            # Create a stream handler that can handle Unicode characters
            # Use errors="replace" to handle any problematic characters
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))

            # Use a simple format that just outputs the raw message
            console_formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(console_formatter)

            # Override the emit method to handle encoding issues
            original_emit = console_handler.emit

            def safe_emit(record: logging.LogRecord) -> None:
                try:
                    # Try to encode/decode the message to handle Unicode issues
                    message = record.getMessage()
                    # Replace problematic Unicode characters with safe alternatives
                    safe_message = message.encode("utf-8", errors="replace").decode("utf-8")
                    record.msg = safe_message
                    original_emit(record)
                except UnicodeEncodeError:
                    # If encoding still fails, try to clean the message further
                    with contextlib.suppress(Exception):
                        message = record.getMessage()
                        # Remove or replace problematic characters

                        # Remove ANSI color codes and problematic Unicode
                        clean_message = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", message)
                        clean_message = clean_message.encode("ascii", errors="replace").decode("ascii")
                        record.msg = clean_message
                        original_emit(record)

            console_handler.emit = safe_emit
        else:
            # On non-Windows systems, use the original UTF-8 approach
            utf8_stream = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
            console_handler = logging.StreamHandler(utf8_stream)
            console_handler.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))

            # Use a simple format that just outputs the raw message
            console_formatter = logging.Formatter("%(message)s")
            console_handler.setFormatter(console_formatter)

        # Add console handler
        subprocess_logger.addHandler(console_handler)

        # Also add file handler if file logging is enabled
        if EnvConfig.get_env_config().log_file_enabled:
            log_dir = Path(EnvConfig.get_env_config().log_path)
            app_log_path = log_dir / "app.log"

            file_handler = logging.FileHandler(app_log_path, encoding="utf-8")
            file_handler.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))
            file_handler.setFormatter(console_formatter)  # Same raw format

            subprocess_logger.addHandler(file_handler)

        # Set logger level and prevent propagation to avoid double logging
        subprocess_logger.setLevel(getattr(logging, EnvConfig.get_env_config().log_level))
        subprocess_logger.propagate = False

    return subprocess_logger
