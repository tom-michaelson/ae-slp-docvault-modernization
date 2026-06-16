"""Unit tests for API versioning module."""

import pytest

from awa.core.api.versioning import (
    API_PREFIX,
    CURRENT_API_VERSION,
    SUPPORTED_VERSIONS,
    get_current_version_prefix,
    get_versioned_prefix,
    is_version_supported,
)


class TestVersioning:
    """Test cases for API versioning functionality."""

    def test_constants(self) -> None:
        """Test that versioning constants are defined correctly."""
        assert CURRENT_API_VERSION == "v1"
        assert SUPPORTED_VERSIONS == ["v1"]
        assert API_PREFIX == "/api"

    def test_is_version_supported_valid(self) -> None:
        """Test is_version_supported with valid version."""
        assert is_version_supported("v1") is True

    def test_is_version_supported_invalid(self) -> None:
        """Test is_version_supported with invalid version."""
        assert is_version_supported("v2") is False
        assert is_version_supported("v0") is False
        assert is_version_supported("invalid") is False
        assert is_version_supported("") is False

    def test_get_versioned_prefix_valid(self) -> None:
        """Test get_versioned_prefix with valid version."""
        result = get_versioned_prefix("v1")
        assert result == "/api/v1"

    def test_get_versioned_prefix_invalid(self) -> None:
        """Test get_versioned_prefix with invalid version."""
        with pytest.raises(ValueError, match="Unsupported API version: v2"):
            get_versioned_prefix("v2")

        with pytest.raises(ValueError, match="Unsupported API version: invalid"):
            get_versioned_prefix("invalid")

    def test_get_current_version_prefix(self) -> None:
        """Test get_current_version_prefix returns correct prefix."""
        result = get_current_version_prefix()
        assert result == "/api/v1"

    def test_error_message_includes_supported_versions(self) -> None:
        """Test that error message includes supported versions."""
        with pytest.raises(ValueError) as exc_info:
            get_versioned_prefix("v2")

        error_message = str(exc_info.value)
        assert "Supported versions: ['v1']" in error_message
