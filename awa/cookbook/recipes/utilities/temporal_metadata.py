"""Shared utilities for extracting Temporal workflow and activity metadata."""

from typing import Any, get_args, get_origin


class ParameterInfo:
    """Contains information about a workflow or activity parameter."""

    def __init__(
        self,
        name: str,
        type_str: str | None = None,
    ) -> None:
        self.name = name
        self.type_str = type_str


def format_type_annotation(annotation: Any) -> str:  # noqa: ANN401
    """Format a type annotation as a string.

    Args:
        annotation: The type annotation to format.

    Returns:
        String representation of the type annotation.

    """
    # Handle None type
    if annotation is type(None):
        return "None"

    # Handle generic types (e.g., list[str], dict[str, Any], List[str], Dict[str, Any])
    origin = get_origin(annotation)
    if origin is not None:
        args = get_args(annotation)
        if args:
            formatted_args = ", ".join(format_type_annotation(arg) for arg in args)
            origin_name = getattr(origin, "__name__", str(origin))
            return f"{origin_name}[{formatted_args}]"
        return getattr(origin, "__name__", str(origin))

    # Handle basic types with __name__
    if hasattr(annotation, "__name__"):
        return annotation.__name__

    # Handle union types (e.g., str | None)
    if hasattr(annotation, "__class__") and "UnionType" in annotation.__class__.__name__:
        return str(annotation)

    # Default: convert to string
    return str(annotation)
