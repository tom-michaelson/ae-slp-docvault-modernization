"""Unit tests for service utilities module."""

import pytest
import typer

from awa.core.cli.service_utils import (
    get_all_service_names,
    parse_service_list,
    validate_service_names,
)


class TestGetAllServiceNames:
    """Test get_all_service_names function."""

    def test_returns_all_valid_services(self) -> None:
        """Test that all valid service names are returned."""
        service_names = get_all_service_names()

        # Should contain all expected service names
        expected_services = {
            "temporal_server",
            "temporal_worker",
            "api",
            "ui",
        }
        assert set(service_names) == expected_services

        # Should return exactly 4 services
        assert len(service_names) == 4

    def test_returns_list_of_strings(self) -> None:
        """Test that the function returns a list of strings."""
        service_names = get_all_service_names()
        assert isinstance(service_names, list)
        assert all(isinstance(name, str) for name in service_names)


class TestParseServiceList:
    """Test parse_service_list function."""

    def test_parse_single_service(self) -> None:
        """Test parsing a single service name."""
        result = parse_service_list("api")
        assert result == ["api"]

    def test_parse_multiple_services(self) -> None:
        """Test parsing multiple service names."""
        result = parse_service_list("api,ui,temporal_server")
        assert result == ["api", "ui", "temporal_server"]

    def test_parse_with_spaces(self) -> None:
        """Test parsing with spaces around service names."""
        result = parse_service_list("api, ui , temporal_server")
        assert result == ["api", "ui", "temporal_server"]

    def test_parse_duplicates_removed(self) -> None:
        """Test that duplicate service names are removed."""
        result = parse_service_list("api,ui,api,temporal_server")
        assert result == ["api", "ui", "temporal_server"]

    def test_parse_empty_string_raises_error(self) -> None:
        """Test that empty string raises typer.Exit."""
        with pytest.raises(typer.Exit):
            parse_service_list("")

    def test_parse_whitespace_only_raises_error(self) -> None:
        """Test that whitespace-only string raises typer.Exit."""
        with pytest.raises(typer.Exit):
            parse_service_list("   ")

    def test_parse_invalid_service_raises_error(self) -> None:
        """Test that invalid service name raises typer.Exit."""
        with pytest.raises(typer.Exit):
            parse_service_list("invalid_service")

    def test_parse_mixed_valid_invalid_raises_error(self) -> None:
        """Test that mix of valid and invalid services raises typer.Exit."""
        with pytest.raises(typer.Exit):
            parse_service_list("api,invalid_service,ui")

    def test_parse_empty_segments_ignored(self) -> None:
        """Test that empty segments (from consecutive commas) are ignored."""
        result = parse_service_list("api,,ui")
        assert result == ["api", "ui"]

    def test_parse_trailing_comma(self) -> None:
        """Test parsing with trailing comma."""
        result = parse_service_list("api,ui,")
        assert result == ["api", "ui"]

    def test_parse_leading_comma(self) -> None:
        """Test parsing with leading comma."""
        result = parse_service_list(",api,ui")
        assert result == ["api", "ui"]


class TestValidateServiceNames:
    """Test validate_service_names function."""

    def test_validate_all_valid_services(self) -> None:
        """Test validation of all valid service names."""
        valid_services = get_all_service_names()
        # Should not raise any exception
        validate_service_names(valid_services)

    def test_validate_single_valid_service(self) -> None:
        """Test validation of single valid service."""
        validate_service_names(["api"])

    def test_validate_multiple_valid_services(self) -> None:
        """Test validation of multiple valid services."""
        validate_service_names(["api", "ui", "temporal_server"])

    def test_validate_empty_list(self) -> None:
        """Test validation of empty list."""
        validate_service_names([])

    def test_validate_invalid_service_raises_error(self) -> None:
        """Test that invalid service name raises typer.Exit."""
        with pytest.raises(typer.Exit):
            validate_service_names(["invalid_service"])

    def test_validate_mixed_valid_invalid_raises_error(self) -> None:
        """Test that mix of valid and invalid services raises typer.Exit."""
        with pytest.raises(typer.Exit):
            validate_service_names(["api", "invalid_service", "ui"])

    def test_validate_multiple_invalid_services_raises_error(self) -> None:
        """Test that multiple invalid services raises typer.Exit."""
        with pytest.raises(typer.Exit):
            validate_service_names(["invalid1", "invalid2"])

    def test_validate_duplicates_allowed(self) -> None:
        """Test that duplicate valid service names are allowed."""
        validate_service_names(["api", "api", "ui"])
