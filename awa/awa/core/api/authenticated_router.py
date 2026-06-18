"""Authenticated API Router with built-in dependency injection."""

from enum import Enum
from typing import Any

from fastapi import APIRouter, Depends

from awa.core.api.auth import require_authenticated_user, require_service_authentication


class AuthType(Enum):
    """Authentication types for routers."""

    USER = "user"  # Regular user authentication
    SERVICE = "service"  # Service-to-service authentication
    NONE = "none"  # No authentication required


def create_router(
    auth_type: AuthType = AuthType.NONE,
    prefix: str = "",
    tags: list[str] | None = None,
    **kwargs: dict[str, Any],
) -> APIRouter:
    """Create a router with optional authentication.

    This creates a standard APIRouter with authentication dependencies
    automatically applied at the router level based on the auth_type.

    Args:
        auth_type: Type of authentication to apply (default: NONE for public)
        prefix: Path prefix for the router
        tags: Tags for OpenAPI documentation
        **kwargs: Additional arguments passed to APIRouter

    Returns:
        Configured APIRouter instance with or without authentication dependencies

    """
    # Set up authentication dependency based on type
    auth_dependencies = []
    if auth_type == AuthType.USER:
        auth_dependencies = [Depends(require_authenticated_user)]
    elif auth_type == AuthType.SERVICE:
        auth_dependencies = [Depends(require_service_authentication)]
    # AuthType.NONE adds no dependencies

    # Add auth dependencies to router-level dependencies
    existing_deps = kwargs.get("dependencies", [])
    kwargs["dependencies"] = existing_deps + auth_dependencies

    return APIRouter(
        prefix=prefix,
        tags=tags,
        **kwargs,
    )


# Convenience functions for backward compatibility and clarity
def create_authenticated_router(
    auth_type: AuthType = AuthType.USER,
    prefix: str = "",
    tags: list[str] | None = None,
    **kwargs: dict[str, Any],
) -> APIRouter:
    """Create an authenticated router (convenience function)."""
    return create_router(auth_type=auth_type, prefix=prefix, tags=tags, **kwargs)


def create_public_router(
    prefix: str = "",
    tags: list[str] | None = None,
    **kwargs: dict[str, Any],
) -> APIRouter:
    """Create a public router (convenience function)."""
    return create_router(auth_type=AuthType.NONE, prefix=prefix, tags=tags, **kwargs)
