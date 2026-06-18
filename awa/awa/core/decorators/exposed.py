"""Decorators for exposing workflows as public tools via API and MCP (Model Context Protocol)."""

from collections.abc import Callable
from typing import TypeVar, cast

T = TypeVar("T")


def exposed(description: str) -> Callable[[type[T]], type[T]]:
    """Mark a workflow class for public exposure via both API and MCP.

    This decorator adds metadata to workflow classes indicating they should be exposed
    as public workflows accessible through both the Web UI/API and MCP (Model Context
    Protocol) tools. It must be applied BEFORE the @workflow.defn decorator.

    Workflows without this decorator are considered internal-only and will not appear
    in the public API or MCP tool listings.

    Args:
        description: Human-readable description of what the workflow does.
                    This will be shown in the Web UI and to AI assistants using MCP.

    Returns:
        Decorator function that adds exposure metadata to the workflow class.

    Note:
        Internal attributes __exposed__ and __description__ are maintained
        for backward compatibility with existing MCP server implementation.

    Example:
        @exposed("Generates a greeting message for a given name")
        @workflow.defn(name=constants.WORKFLOW_HELLO_WORLD)
        class HelloWorldWorkflow:
            ...

    """

    def decorator(cls: type[T]) -> type[T]:
        """Add MCP metadata to the workflow class.

        Args:
            cls: The workflow class to decorate.

        Returns:
            The same class with MCP metadata attributes added.

        """
        # Add MCP metadata attributes to the class
        cls.__exposed__ = True
        cls.__description__ = description

        return cast("type[T]", cls)

    return decorator
