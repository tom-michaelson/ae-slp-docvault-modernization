"""Utilities for mapping Temporal workflow status to string representations."""

from temporalio.api.enums.v1 import WorkflowExecutionStatus

from awa.core.models.config.env_config import EnvConfig

# Canonical status mapping
STATUS_MAP = {
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_COMPLETED: "COMPLETED",
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_FAILED: "FAILED",
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CANCELED: "CANCELLED",
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TERMINATED: "TERMINATED",
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CONTINUED_AS_NEW: "CONTINUED_AS_NEW",
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TIMED_OUT: "TIMED_OUT",
    WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_RUNNING: "RUNNING",
}


def map_temporal_status_to_string(status: WorkflowExecutionStatus) -> str:
    """Convert Temporal status enum to string representation.

    Args:
        status: Temporal WorkflowExecutionStatus enum value

    Returns:
        String representation of status (e.g., "COMPLETED", "FAILED", "RUNNING")
        Returns "UNKNOWN" for unmapped statuses

    """
    return STATUS_MAP.get(status, "UNKNOWN")


def create_temporal_ui_link(workflow_id: str, run_id: str) -> str:
    """Create Temporal UI link for workflow monitoring.

    Args:
        workflow_id: The workflow ID
        run_id: The workflow run ID

    Returns:
        URL to view the workflow in Temporal UI

    """
    env_config = EnvConfig.get_env_config()
    return (
        f"http://{env_config.temporal_ui_host}:{env_config.temporal_ui_port}/"
        f"namespaces/default/workflows/{workflow_id}/{run_id}"
    )
