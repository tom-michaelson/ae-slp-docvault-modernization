"""API versioning configuration and utilities."""

from typing import Literal

# API Version Configuration (Hard-coded)
CURRENT_API_VERSION: Literal["v1"] = "v1"
SUPPORTED_VERSIONS: list[str] = ["v1"]
API_PREFIX: str = "/api"

# Type alias for supported versions
SupportedVersion = Literal["v1"]


def is_version_supported(version: str) -> bool:
    """Check if a given API version is supported.

    Args:
        version: The version string to check (e.g., "v1")

    Returns:
        True if the version is supported, False otherwise

    """
    return version in SUPPORTED_VERSIONS


def get_versioned_prefix(version: str) -> str:
    """Get the full versioned API prefix for a given version.

    Args:
        version: The version string (e.g., "v1")

    Returns:
        The full versioned prefix (e.g., "/api/v1")

    Raises:
        ValueError: If the version is not supported

    """
    if not is_version_supported(version):
        raise ValueError(f"Unsupported API version: {version}. Supported versions: {SUPPORTED_VERSIONS}")

    return f"{API_PREFIX}/{version}"


def get_current_version_prefix() -> str:
    """Get the full versioned API prefix for the current version.

    Returns:
        The full versioned prefix for the current version (e.g., "/api/v1")

    """
    return get_versioned_prefix(CURRENT_API_VERSION)
