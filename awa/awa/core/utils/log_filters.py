"""Centralized log filtering utilities.

This module provides unified filtering functions to reduce duplication
across the logging system.
"""

from awa.core.logger.logger import LoggerComponent


def should_exclude_workflow_logs(record: dict) -> bool:
    """Check if workflow/activity logs should be excluded.

    This is used for application logs and worker logs that should NOT
    include workflow execution logs.

    Args:
        record: Log record (either loguru format or SocketIO format)

    Returns:
        True if workflow/activity logs should be excluded

    """
    # Handle both loguru record format and SocketIO log entry format
    component = record["extra"].get("component", "") if "extra" in record else record.get("component", "")

    # Exclude workflow and activity execution logs
    return component in {LoggerComponent.WORKFLOW, LoggerComponent.ACTIVITY}


def should_include_in_application_log(record: dict) -> bool:
    """Filter for application log files.

    Args:
        record: Loguru log record

    Returns:
        True if log should be included in application log

    """
    return not should_exclude_workflow_logs(record)


def should_include_in_worker_log(log_entry: dict) -> bool:
    """Filter for worker log files.

    Args:
        log_entry: SocketIO log entry

    Returns:
        True if log should be included in worker log

    """
    return not should_exclude_workflow_logs(log_entry)


def should_include_in_workflow_log(record: dict, top_level_workflow_id: str) -> bool:
    """Filter for workflow-specific log files.

    Args:
        record: Loguru log record
        top_level_workflow_id: The top-level workflow ID

    Returns:
        True if log should be included in workflow file

    """
    # Get workflow ID and component from record
    record_workflow_id = record["extra"].get("workflow_id")
    record_top_level_id = record["extra"].get("top_level_workflow_id")
    component = record["extra"].get("component", "AWA")

    if not record_workflow_id:
        return False

    # Exclude AWA-WORKER logs from workflow files - they should only appear in worker terminal/main log
    if component == LoggerComponent.WORKER:
        return False

    # Include logs that belong to this workflow hierarchy
    return record_workflow_id in {
        top_level_workflow_id,
        record_top_level_id,
    } or record_workflow_id.startswith(f"{top_level_workflow_id}-")
