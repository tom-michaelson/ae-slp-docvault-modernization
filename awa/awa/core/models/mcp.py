"""MCP (Model Context Protocol) related models and types."""

from typing import Any, TypedDict


class WorkflowExecutionResult(TypedDict):
    """Structured output for MCP workflow execution."""

    status: str  # "success" or "failed"
    result: Any  # Workflow result or error message


class WorkflowProgressInfo(TypedDict):
    """Progress information for a workflow."""

    duration: str  # Human-readable duration string
    pending_tasks_count: int  # Number of pending tasks


class WorkflowStatusResponse(TypedDict):
    """Structured response for workflow status queries."""

    workflow_id: str  # Unique workflow identifier
    run_id: str  # Temporal run ID
    status: str  # "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED"
    progress: WorkflowProgressInfo  # Progress information
    temporal_ui_link: str  # Link to Temporal UI


class StartWorkflowResponse(TypedDict):
    """Response format for non-blocking workflow start."""

    workflow_id: str
    run_id: str
    status: str  # "RUNNING"
    temporal_ui_link: str
    started_at: str  # ISO 8601 format


class WorkflowResultResponse(TypedDict, total=False):
    """Structured response for workflow result retrieval."""

    workflow_id: str  # Unique workflow identifier
    status: str  # Workflow execution status
    completed_at: str  # ISO 8601 format timestamp
    result: Any  # Present only for COMPLETED workflows
    error: str  # Present only for FAILED workflows
