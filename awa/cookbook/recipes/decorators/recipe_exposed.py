"""Decorators for exposing workflows as public tools via API and MCP (Model Context Protocol)."""

from collections.abc import Callable
from typing import TypeVar, cast

T = TypeVar("T")


def recipe_exposed(description: str) -> Callable[[type[T]], type[T]]:
    """Mark a workflow class for public exposure via both API and MCP.

    Duplicated from the core @exposed decorator to avoid a core reference from the cookbook.
    """

    def decorator(cls: type[T]) -> type[T]:
        cls.__exposed__ = True
        cls.__description__ = description

        return cast("type[T]", cls)

    return decorator
