import ast
import logging
import re

from loguru import logger

from awa.core.logger.workflow_context import (
    get_is_top_level,
    get_top_level_workflow_id,
    get_top_level_workflow_type,
    workflow_context,
)

# Subprocess logger names that should be excluded from interception
# These loggers will write raw subprocess output directly without re-processing
SUBPROCESS_LOGGER_NAMES = {
    "subprocess.api",
    "subprocess.ui",
    "subprocess.worker",
    "subprocess.server",
    "subprocess.temporal",
}


class InterceptHandler(logging.Handler):
    """Handler that intercepts standard logging and routes to loguru.

    This handler automatically detects the logging source and applies appropriate
    component labels and workflow context.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Skip interception for subprocess loggers - they handle raw output directly
        if record.name in SUBPROCESS_LOGGER_NAMES:
            return

        message = record.getMessage()

        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Determine component based on logger name
        component = self._determine_component(record.name)

        # Try to get workflow ID from multiple sources
        workflow_id = self._extract_workflow_id(record)

        # If we don't have a workflow ID from the record, check the context
        if not workflow_id:
            workflow_id = workflow_context.get()

        # Build extra context
        extra_context = {
            "component": component,
        }

        if workflow_id:
            extra_context["workflow_id"] = workflow_id

        # Also add top-level workflow ID and type if available
        top_level_id = get_top_level_workflow_id()
        if top_level_id:
            extra_context["top_level_workflow_id"] = top_level_id

        top_level_type = get_top_level_workflow_type()
        if top_level_type:
            extra_context["top_level_workflow_type"] = top_level_type

        # Add is_top_level flag from context for filtering
        is_top_level = get_is_top_level()
        if is_top_level is not None and "is_top_level" not in extra_context:
            # Only override if not already set by workflow ID detection
            extra_context["is_top_level"] = is_top_level

        # Add original logger name for reference
        if record.name and record.name != "root":
            extra_context["original_logger"] = record.name

        logger.opt(depth=depth, exception=record.exc_info).bind(**extra_context).log(
            level,
            message,
        )

    def _extract_workflow_id(self, record: logging.LogRecord) -> str | None:
        """Extract workflow ID from various sources."""
        # First try the ContextVar (for main thread logging)
        workflow_id = workflow_context.get()
        if workflow_id:
            return workflow_id

        # For Temporal workflow/activity logging, check if the record has workflow context
        # Temporal adds context to log records via MDC/thread-local storage
        if hasattr(record, "workflow_id"):
            return record.workflow_id

        # Check for workflow execution context in record attributes
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if "workflow" in key.lower() and isinstance(value, str) and value:
                    return value

        # Check if this is a temporal workflow logger with context info
        if hasattr(record, "args") and record.args and isinstance(record.args, tuple):
            # Look for workflow context in the log record args
            for arg in record.args:
                if isinstance(arg, dict) and "workflow_id" in arg:
                    return arg["workflow_id"]

        # Try to extract from the logger name if it contains workflow ID patterns
        # This handles cases where Temporal embeds workflow IDs in logger names
        if record.name and "workflow" in record.name.lower():
            # Look for UUID patterns (standard format: 8-4-4-4-12 hex digits)
            # This is more readable than the previous regex and handles the most common case
            uuid_parts = [
                r"[0-9a-f]{8}",  # 8 hex digits
                r"[0-9a-f]{4}",  # 4 hex digits
                r"[0-9a-f]{4}",  # 4 hex digits
                r"[0-9a-f]{4}",  # 4 hex digits
                r"[0-9a-f]{12}",  # 12 hex digits
            ]
            uuid_pattern = r"-".join(uuid_parts)
            match = re.search(uuid_pattern, record.name, re.IGNORECASE)
            if match:
                return match.group()

        # For Temporal workflow/activity logging, try to extract from the message
        message = record.getMessage()
        return self._extract_workflow_id_from_message(message)

    def _extract_workflow_id_from_message(self, message: str | None | int) -> str | None:
        """Extract workflow ID from temporal message format.

        Temporal messages often contain context in the format: "message ({key: value, ...})"
        or embedded in token bytes for internal worker logs.
        This function extracts the workflow_id from such messages.

        Args:
            message: The log message to parse (can be string, None, or int for edge case testing)

        Returns:
            The workflow_id if found and valid, None otherwise

        """
        if not message or not isinstance(message, str):
            return None

        # First, try to extract from Temporal worker token format
        # Pattern: "Running activity ... (token b'...\x12(workflow_id\x1a..."
        # or "Completing activity with completion: ... isolated_agent_..."
        if "token" in message or "isolated_agent_" in message:
            # Look for workflow ID patterns like "isolated_agent_20250808_111231_339_884c6"
            # This matches the child workflow naming convention
            pattern = r"isolated_agent_\d{8}_\d{6}_\d{3}_[a-f0-9]{5}"
            match = re.search(pattern, message)
            if match:
                return match.group()

            # Also try to extract other workflow patterns from token
            # Look for patterns like "workflow_id_timestamp_random"
            pattern = r"[a-zA-Z_]+_\d{8}_\d{6}_\d{3}_[a-f0-9]{5}"
            match = re.search(pattern, message)
            if match and not match.group().startswith("awa_"):  # Exclude temp directory patterns
                return match.group()

        # Fall back to original check for ({workflow_id: ...}) pattern
        if "({" not in message or "workflow_id" not in message:
            return None

        # Find all potential context blocks and try to extract workflow_id from each
        start_pos = 0
        while start_pos < len(message):
            start = message.find("({", start_pos)
            if start == -1:
                break

            # Find the matching closing marker
            end = message.find("})", start)
            if end == -1:
                break

            try:
                context_str = message[start + 1 : end + 1]
                context = ast.literal_eval(context_str)

                if isinstance(context, dict) and "workflow_id" in context:
                    workflow_id = context["workflow_id"]
                    # Ensure workflow_id is a string and not empty
                    if isinstance(workflow_id, str) and workflow_id.strip():
                        return workflow_id.strip()

            except (SyntaxError, ValueError, TypeError):
                # If parsing fails, continue to next potential context block
                pass

            # Move to next potential context block
            start_pos = start + 1

        return None

    def _determine_component(self, logger_name: str | None) -> str:
        """Determine the component based on the logger name."""
        if not logger_name or logger_name == "root":
            return "AWA"

        # Import here to avoid circular import
        from awa.core.logger.logger import LoggerComponent

        # Map logger names to components
        if logger_name.startswith("uvicorn"):
            return LoggerComponent.API
        if logger_name.startswith("fastapi"):
            return LoggerComponent.API
        if logger_name.startswith("temporalio.workflow"):
            return LoggerComponent.WORKFLOW
        if logger_name.startswith("temporalio.activity"):
            return LoggerComponent.ACTIVITY
        # Only temporalio.worker logs should be AWA-WORKER
        if logger_name.startswith("temporalio.worker"):
            return LoggerComponent.WORKER
        # Other temporalio logs (client, server) and engine logs are CLI/service management
        if logger_name.startswith("temporalio") or "engine" in logger_name.lower():
            return LoggerComponent.WORKER
        if "service manager" in logger_name.lower():
            return LoggerComponent.CLI
        if "cli" in logger_name.lower():
            return LoggerComponent.CLI
        if "api" in logger_name.lower():
            return LoggerComponent.API
        return "AWA"
