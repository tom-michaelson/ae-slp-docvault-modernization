"""Workflow context management for logging.

This module provides utilities for managing workflow context
across different execution environments.
"""

from contextvars import ContextVar

from temporalio import workflow

# Context variable for tracking the current workflow ID
workflow_context: ContextVar[str | None] = ContextVar("workflow_context", default=None)

# Context variable for tracking the top-level workflow ID
top_level_workflow_context: ContextVar[str | None] = ContextVar("top_level_workflow_context", default=None)

# Context variable for tracking the top-level workflow type
top_level_workflow_type_context: ContextVar[str | None] = ContextVar("top_level_workflow_type_context", default=None)

# Context variable for tracking whether this is a top-level workflow
is_top_level_context: ContextVar[bool | None] = ContextVar("is_top_level_context", default=None)


def setup_workflow_context() -> None:
    """Set up workflow context from within a Temporal workflow.

    This should be called at the beginning of each workflow's run method.
    """
    if workflow.info():
        # Set the current workflow ID
        workflow_id = workflow.info().workflow_id
        workflow_context.set(workflow_id)

        # For now, also set as top-level (will be updated by child workflows)
        if not top_level_workflow_context.get():
            top_level_workflow_context.set(workflow_id)


def set_top_level_workflow_id(workflow_id: str) -> None:
    """Set the top-level workflow ID for logging context.

    Args:
        workflow_id: The ID of the top-level workflow

    """
    top_level_workflow_context.set(workflow_id)


def get_current_workflow_id() -> str | None:
    """Get the current workflow ID from context."""
    return workflow_context.get()


def get_top_level_workflow_id() -> str | None:
    """Get the top-level workflow ID from context."""
    return top_level_workflow_context.get()


def set_workflow_context(workflow_id: str) -> None:
    """Set the current workflow ID in context.

    Args:
        workflow_id: The ID of the current workflow

    """
    workflow_context.set(workflow_id)


def set_top_level_workflow_type(workflow_type: str) -> None:
    """Set the top-level workflow type for logging context.

    Args:
        workflow_type: The type of the top-level workflow

    """
    top_level_workflow_type_context.set(workflow_type)


def get_top_level_workflow_type() -> str | None:
    """Get the top-level workflow type from context."""
    return top_level_workflow_type_context.get()


def set_is_top_level(is_top_level: bool) -> None:
    """Set whether this is a top-level workflow.

    Args:
        is_top_level: True if this is a top-level workflow, False if it's a child

    """
    is_top_level_context.set(is_top_level)


def get_is_top_level() -> bool | None:
    """Get whether this is a top-level workflow from context."""
    return is_top_level_context.get()
