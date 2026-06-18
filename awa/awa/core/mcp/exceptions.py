"""MCP-specific exception classes."""

from fastmcp.exceptions import ToolError


class WorkflowNotFoundError(ToolError):
    """Raised when workflow ID not found in storage."""


class WorkflowNotCompletedError(ToolError):
    """Raised when trying to get result from incomplete workflow."""


class WorkflowExecutionError(ToolError):
    """Raised when workflow execution fails."""


# Helper functions for error handling (TRY301 compliance)
def raise_workflow_not_completed(workflow_id: str) -> None:
    """Raise WorkflowNotCompletedError for running workflows."""
    raise WorkflowNotCompletedError(
        f"Workflow '{workflow_id}' is still running. Please wait for completion before retrieving results.",
    )


def raise_workflow_not_found(workflow_id: str) -> None:
    """Raise WorkflowNotFoundError when workflow is not found."""
    raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found")


def raise_temporal_client_not_initialized() -> None:
    """Raise WorkflowExecutionError when temporal client is not initialized."""
    raise WorkflowExecutionError("Temporal client not initialized")


def raise_workflow_name_required() -> None:
    """Raise ToolError when workflow name is missing."""
    raise ToolError("Workflow name is required")
