"""Logging configuration for AWA.

This module provides:
- Component-based logging (AWA API, AWA CLI, AWA Engine)
- Temporal workflow logging integration
- Configurable file rotation
- Optional structured JSON logging
- Console and file output
"""

import contextlib
import logging
import os
import platform
import re
import sys
import warnings
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path
from pprint import pformat
from typing import Any

from loguru import logger
from loguru._logger import Logger

from awa.core.logger.intercept_handler import InterceptHandler
from awa.core.logger.log_config import create_component_level_filter, get_log_config, get_log_level_for_component
from awa.core.logger.workflow_context import workflow_context
from awa.core.models.config.env_config import EnvConfig
from awa.core.models.config.log_config import ComponentLogLevels


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
    SOCKETIO = "SOCKETIO-SERVER"
    UVICORN = "UVICORN"


def _filter_application_logs(record: dict) -> bool:
    """Filter logs to exclude workflow execution logs from application log.

    Args:
        record: Loguru log record

    Returns:
        True if log should be included in application log, False otherwise

    """
    component = record["extra"].get("component", "")

    # Workflow and activity logs should not appear in the main application console
    # but should still be processed by other handlers (like SocketIO)
    # This filter is only for the console/app.log handlers
    if component in {LoggerComponent.WORKFLOW, LoggerComponent.ACTIVITY}:
        return False

    # Exclude logs that have a workflow_id (they go to workflow-specific logs)
    # Exception: AWA-WORKER logs with workflow_id should still appear in app logs
    # BUT only for top-level workflows, not child workflows
    if record["extra"].get("workflow_id"):
        if component == LoggerComponent.WORKER:
            # For AWA-WORKER logs, only include if it's a top-level workflow
            # Child workflow AWA-WORKER logs should not appear in console
            is_top_level = record["extra"].get("is_top_level", True)  # Default to True for backward compat
            if not is_top_level:
                return False
        else:
            # All other components with workflow_id are excluded from app logs
            return False

    return True


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


def _create_combined_filter(component_filter: Any) -> Any:  # noqa: ANN401
    """Create a combined filter for application and component-level filtering.

    Args:
        component_filter: Component-level filter from configuration

    Returns:
        Combined filter function

    """

    def combined_filter(record: dict) -> bool:
        """Apply both application and component-level filtering."""
        # First check if it should be included in application logs
        if not _filter_application_logs(record):
            return False

        # Then apply component-level filtering
        if callable(component_filter):
            return component_filter(record)
        # If component_filter is a string (single level), we'll handle it via the level param
        return True

    return combined_filter


def _create_log_handlers(
    log_dir: Path,
    base_level: int | str,
    combined_filter: Any,  # noqa: ANN401
    component_filter: Any,  # noqa: ANN401
    file_only: bool,
) -> list[dict[str, Any]]:
    """Create log handlers based on configuration.

    Args:
        log_dir: Log directory path
        base_level: Base logging level
        combined_filter: Combined filter function
        component_filter: Component filter for JSON logs
        file_only: If True, only log to files

    Returns:
        List of handler configurations

    """
    handlers = []
    env_config = EnvConfig.get_env_config()

    # Console handler (if enabled and not file_only)
    if not file_only and env_config.log_console_enabled:
        # Enable colorization unless NO_COLOR environment variable is set
        colorize = not os.environ.get("NO_COLOR", "").strip()

        handlers.append(
            {
                "sink": sys.stdout,
                "level": base_level,
                "format": format_record,
                "filter": combined_filter,
                "colorize": colorize,
                "catch": True,  # Catch any encoding errors
            },
        )

    # Single application log file for ALL logs (if enabled)
    if env_config.log_file_enabled:
        app_log_path = log_dir / "app.log"
        handlers.append(
            {
                "sink": app_log_path,
                "level": base_level,
                "format": format_record,
                "filter": combined_filter,
                # Disable rotation to avoid Windows permission issues
                "catch": True,  # Catch any remaining errors
            },
        )

    # JSON structured log file for ALL logs - both application and workflow (if enabled)
    if env_config.log_enable_json:
        json_log_path = log_dir / "app.json"
        # For JSON logs, we don't filter workflow logs out
        json_filter = component_filter if callable(component_filter) else None
        handlers.append(
            {
                "sink": json_log_path,
                "level": base_level,
                "serialize": True,
                "filter": json_filter,
                # Disable rotation to avoid Windows permission issues
                "catch": True,  # Catch any remaining errors
            },
        )

    return handlers


def _setup_temporal_loggers(intercept_handler: InterceptHandler) -> None:
    """Set up Temporal and framework loggers.

    Args:
        intercept_handler: InterceptHandler instance

    """
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

        # Determine appropriate component level
        if "workflow" in logger_name:
            level_str = get_log_level_for_component("workflow")
        elif "activity" in logger_name:
            level_str = get_log_level_for_component("activity")
        elif logger_name == "temporalio.worker":
            # For temporalio.worker specifically, suppress DEBUG logs
            # These are internal Temporal logs that don't have proper context
            level_str = get_log_level_for_component("worker")
            if level_str == "DEBUG":
                level_str = "INFO"
        elif "worker" in logger_name:
            level_str = get_log_level_for_component("worker")
        elif any(x in logger_name for x in ["uvicorn", "fastapi"]):
            level_str = get_log_level_for_component("uvicorn")
        else:
            level_str = get_log_level_for_component("cli")

        temporal_logger.setLevel(getattr(logging, level_str))
        temporal_logger.propagate = False  # Don't propagate to avoid double logging


def _setup_http_loggers() -> None:
    """Set up HTTP library loggers."""

    class HTTPInterceptHandler(InterceptHandler):
        """Intercept handler that routes HTTP library logs to HTTP component."""

        def emit(self, record: logging.LogRecord) -> None:
            # Route all httpx/httpcore logs through HTTP component
            http_logger = logger.bind(component="HTTP")
            level = record.levelname.lower()
            message = self.format(record)

            if hasattr(http_logger, level):
                getattr(http_logger, level)(message)

    # Set log level for LiteLLM SDK (which is used by the OpenAI Agents SDK)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)

    # Set up httpx/httpcore with HTTP component handler
    http_handler = HTTPInterceptHandler()
    http_level_str = get_log_level_for_component("http")

    for logger_name in ["httpx", "httpcore"]:
        http_logger = logging.getLogger(logger_name)
        http_logger.handlers.clear()
        http_logger.addHandler(http_handler)
        http_logger.setLevel(getattr(logging, http_level_str))
        http_logger.propagate = False


def init_logging(file_only: bool = False) -> None:
    """Initialize comprehensive logging system.

    Args:
        file_only: If True, only log to files (no console output)

    """
    # Suppress deprecation warning from litellm during cleanup
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="litellm")

    # Create log directories
    log_dir = Path(EnvConfig.get_env_config().log_path)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers
    logger.remove()

    # Get log configuration
    log_config = get_log_config()

    # Create component-level filter
    component_filter = create_component_level_filter(log_config)

    # Create combined filter
    combined_filter = _create_combined_filter(component_filter)

    # Determine the base level to use
    # If using component-specific levels, set to TRACE (0) to let filter control
    # If using single level, use that level
    base_level = 0 if isinstance(log_config.log_level, ComponentLogLevels) else log_config.log_level

    # Create handlers
    handlers = _create_log_handlers(
        log_dir=log_dir,
        base_level=base_level,
        combined_filter=combined_filter,
        component_filter=component_filter,
        file_only=file_only,
    )

    # Configure loguru with all handlers
    logger.configure(handlers=handlers)

    # Install InterceptHandler to capture standard Python logging
    intercept_handler = InterceptHandler()

    # Remove existing handlers from root logger and install our interceptor
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(intercept_handler)

    # Set root logger to NOTSET (0) to let component filters control levels
    root_logger.setLevel(logging.NOTSET)

    # Set up Temporal and framework loggers
    _setup_temporal_loggers(intercept_handler)

    # Set up HTTP library loggers
    _setup_http_loggers()


def get_logger(
    component: LoggerComponent | str,
    workflow_id: str | None = None,
    **extra_context: dict[str, Any],
) -> Logger:
    """Get a logger bound to a specific component and optional workflow.

    Args:
        component: Component identifier (LoggerComponent enum or string)
        workflow_id: Optional workflow execution ID
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

    # Add workflow_id if provided
    if workflow_id:
        context["workflow_id"] = workflow_id

    # Get component-specific log level
    component_name = component_str.replace("AWA-", "").lower()
    _ = get_log_level_for_component(component_name)  # For future use

    # Create a logger with the appropriate level
    component_logger = logger.bind(**context)
    component_logger = component_logger.opt(depth=1)

    return component_logger


def setup_workflow_logging(workflow_id: str) -> None:
    """Set up logging for a specific workflow execution.

    This should be called at the start of workflow execution to ensure
    workflow-specific logs are captured.
    """
    # Set the workflow context for this execution
    # This allows the InterceptHandler to associate logs with the workflow ID
    workflow_context.set(workflow_id)


def _get_subprocess_log_level(service_name: str) -> int:
    """Get the appropriate log level for a subprocess.

    Args:
        service_name: Name of the service

    Returns:
        Log level value

    """
    if service_name.lower() in ["api", "ui", "worker", "cli"]:
        level_str = get_log_level_for_component(service_name.lower())
    else:
        level_str = get_log_level_for_component("cli")  # Default to cli level

    try:
        return getattr(logging, str(level_str))
    except Exception:  # noqa: BLE001
        return logging.INFO


def _create_safe_emit_wrapper(
    original_emit: Callable[[logging.LogRecord], None],
) -> Callable[[logging.LogRecord], None]:
    """Create a safe emit wrapper that handles encoding issues.

    Args:
        original_emit: Original emit method

    Returns:
        Safe emit wrapper function

    """

    def safe_emit(record: logging.LogRecord) -> None:
        try:
            message = record.getMessage()
            safe_message = message.encode("utf-8", errors="replace").decode("utf-8")
            record.msg = safe_message
            original_emit(record)
        except UnicodeEncodeError:
            with contextlib.suppress(Exception):
                message = record.getMessage()
                # Remove ANSI color codes and problematic Unicode
                clean_message = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", message)
                clean_message = clean_message.encode("ascii", errors="replace").decode("ascii")
                record.msg = clean_message
                original_emit(record)

    return safe_emit


def _create_subprocess_console_handler(service_name: str) -> logging.Handler:
    """Create a console handler for subprocess output.

    Args:
        service_name: Name of the service

    Returns:
        Configured console handler

    """
    # On Windows, try to set UTF-8 mode
    if platform.system() == "Windows":
        with contextlib.suppress(Exception):
            # Try to set UTF-8 mode for the console
            os.system("chcp 65001 > nul 2>&1")  # noqa: S605, S607

    console_handler = logging.StreamHandler(sys.stdout)
    level_value = _get_subprocess_log_level(service_name)
    console_handler.setLevel(level_value)

    # Use a simple format that just outputs the raw message
    console_formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    # Override emit to handle encoding issues
    console_handler.emit = _create_safe_emit_wrapper(console_handler.emit)

    return console_handler


def _create_subprocess_file_handler(service_name: str) -> logging.Handler | None:
    """Create a file handler for subprocess output if enabled.

    Args:
        service_name: Name of the service

    Returns:
        Configured file handler or None if disabled

    """
    if not EnvConfig.get_env_config().log_file_enabled:
        return None

    log_dir = Path(EnvConfig.get_env_config().log_path)
    app_log_path = log_dir / "app.log"

    file_handler = logging.FileHandler(app_log_path, encoding="utf-8")
    level_value = _get_subprocess_log_level(service_name)
    file_handler.setLevel(level_value)

    # Use a simple format that just outputs the raw message
    console_formatter = logging.Formatter("%(message)s")
    file_handler.setFormatter(console_formatter)

    return file_handler


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
        # Create console handler
        console_handler = _create_subprocess_console_handler(service_name)
        subprocess_logger.addHandler(console_handler)

        # Add file handler if enabled
        file_handler = _create_subprocess_file_handler(service_name)
        if file_handler:
            subprocess_logger.addHandler(file_handler)

        # Set logger level and prevent propagation to avoid double logging
        subprocess_logger.setLevel(logging.NOTSET)  # Let handlers control the level
        subprocess_logger.propagate = False

    return subprocess_logger
