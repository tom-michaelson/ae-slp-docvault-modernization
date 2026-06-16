"""Utilities for workflow logging setup and context management."""

from datetime import timedelta
from pathlib import Path
from typing import TypeVar

from loguru import logger as loguru_logger
from temporalio import workflow

from awa.core.logger.workflow_context import (
    get_top_level_workflow_id,
    get_top_level_workflow_type,
    set_top_level_workflow_id,
    set_top_level_workflow_type,
    setup_workflow_context,
)
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.log_filters import should_include_in_workflow_log

T = TypeVar("T")


async def setup_workflow_logging_context() -> str | None:
    """Set up workflow logging context for the current workflow.

    This function should be called at the beginning of each workflow's run method.
    It sets up the workflow context and determines the top-level workflow ID.

    Returns:
        The top-level workflow ID if found, None otherwise

    """
    # Set up basic workflow context
    setup_workflow_context()

    # Try to get top-level workflow ID from context first
    top_level_id = get_top_level_workflow_id()
    if top_level_id:
        return top_level_id

    # If we don't have a top-level ID, execute the activity to get it
    # The activity will also set the workflow type in context as a side effect
    try:
        from awa.sdk.constants import ACTIVITY_GET_TOP_LEVEL_WORKFLOW_INFO

        # Execute the activity to get the top-level workflow ID
        # As a side effect, this will also set the workflow type in context
        top_level_id = await workflow.execute_local_activity(
            activity=ACTIVITY_GET_TOP_LEVEL_WORKFLOW_INFO,
            start_to_close_timeout=timedelta(seconds=30),
        )

        # Set the ID in context
        set_top_level_workflow_id(top_level_id)

        # The workflow type was already set by the activity as a side effect
        workflow_type = get_top_level_workflow_type() or "UnknownWorkflow"

        # Also log this information
        workflow.logger.info(f"Top-level workflow determined - ID: {top_level_id}, Type: {workflow_type}")

        return top_level_id
    except Exception:  # noqa: BLE001
        # If we can't determine the parent, assume we are the top-level
        current_workflow_id = workflow.info().workflow_id
        current_workflow_type = workflow.info().workflow_type

        set_top_level_workflow_id(current_workflow_id)
        set_top_level_workflow_type(current_workflow_type)

        workflow.logger.info(
            f"Assuming current workflow is top-level - ID: {current_workflow_id}, Type: {current_workflow_type}",
        )
        return current_workflow_id


def get_workflow_logging_context() -> dict[str, str]:
    """Get the current workflow logging context.

    Returns:
        Dictionary with workflow_id and top_level_workflow_id

    """
    context = {}

    if workflow.info():
        context["workflow_id"] = workflow.info().workflow_id

    top_level_id = get_top_level_workflow_id()
    if top_level_id:
        context["top_level_workflow_id"] = top_level_id

    return context


def find_workflow_log_file(workflow_id: str) -> Path | None:
    """Find an existing workflow log file by searching all workflow type directories.

    Args:
        workflow_id: The workflow ID to search for

    Returns:
        Path to the log file if found, None otherwise

    """
    log_path = Path(EnvConfig.get_env_config().log_path)
    workflows_dir = log_path / "workflows"

    if not workflows_dir.exists():
        return None

    # Check if file exists in the old flat structure first
    old_path = workflows_dir / f"{workflow_id}.log"
    if old_path.exists():
        return old_path

    # Search in workflow type/id subdirectories
    for type_dir in workflows_dir.iterdir():
        if type_dir.is_dir():
            log_file = type_dir / workflow_id / "workflow.log"
            if log_file.exists():
                return log_file

    return None


def get_workflow_log_path(workflow_id: str, workflow_type: str | None = None) -> Path:
    """Get the log file path for a workflow.

    Args:
        workflow_id: The workflow ID (uses top-level workflow ID for directory organization)
        workflow_type: The workflow type (optional, used for directory organization)

    Returns:
        Path to the workflow log file

    """
    log_path = Path(EnvConfig.get_env_config().log_path)
    workflows_dir = log_path / "workflows"

    if workflow_type:
        # Create directory structure: workflows/{workflow_type}/{workflow_id}/workflow.log
        workflow_id_dir = workflows_dir / workflow_type / workflow_id
        workflow_id_dir.mkdir(parents=True, exist_ok=True)
        return workflow_id_dir / "workflow.log"
    # Fallback to old behavior
    workflows_dir.mkdir(parents=True, exist_ok=True)
    return workflows_dir / f"{workflow_id}.log"


def setup_workflow_file_logging(
    _workflow_id: str,
    top_level_workflow_id: str,
    workflow_type: str | None = None,
) -> int | None:
    """Set up file logging for a workflow.

    Args:
        _workflow_id: The current workflow ID (unused, kept for interface compatibility)
        top_level_workflow_id: The top-level workflow ID (used for directory organization)
        workflow_type: The workflow type (optional, will get from context if not provided)

    Returns:
        Handler ID for cleanup, or None if setup failed

    """
    try:
        # Get the workflow type from parameter or context
        if not workflow_type:
            workflow_type = get_top_level_workflow_type()
        log_file_path = get_workflow_log_path(top_level_workflow_id, workflow_type)

        # Add file sink with workflow filtering
        handler_id = loguru_logger.add(
            sink=str(log_file_path),
            filter=lambda record: should_include_in_workflow_log(record, top_level_workflow_id),
            format=_format_workflow_log,
            level=EnvConfig.get_env_config().log_level,
            enqueue=True,  # Thread-safe for cross-process logging
        )

        # Add JSON file sink if enabled
        if EnvConfig.get_env_config().log_enable_json:
            json_log_path = log_file_path.with_suffix(".json")
            loguru_logger.add(
                sink=str(json_log_path),
                filter=lambda record: should_include_in_workflow_log(record, top_level_workflow_id),
                serialize=True,  # Enable JSON serialization
                level=EnvConfig.get_env_config().log_level,
                enqueue=True,  # Thread-safe for cross-process logging
            )

        return handler_id
    except Exception:  # noqa: BLE001
        # Don't fail workflow execution if logging setup fails
        return None


def _format_workflow_log(record: dict) -> str:
    """Format log record for workflow file output.

    Args:
        record: Loguru log record

    Returns:
        Formatted log string

    """
    # Use similar format to main logger but include workflow context
    component = record["extra"].get("component", "AWA")
    workflow_id = record["extra"].get("workflow_id", "")

    format_parts = [
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>",
        "<level>{level: <8}</level>",
        f"<cyan>{component: <12}</cyan>",
    ]

    if workflow_id:
        format_parts.append(f"<yellow>{workflow_id}</yellow>")

    format_parts.append("<level>{message}</level>")

    # Handle pretty-printed payloads
    if record["extra"].get("payload") is not None:
        format_parts.append("\n<level>{extra[payload]}</level>")

    format_parts.append("{exception}\n")

    return " | ".join(format_parts)
