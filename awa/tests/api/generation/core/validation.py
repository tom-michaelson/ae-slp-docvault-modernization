"""Validation utilities for test data generation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class OpenAPIValidator:
    """Validates OpenAPI specification structure."""

    @staticmethod
    def validate_openapi_spec(spec: dict[str, Any]) -> None:
        """Validate basic OpenAPI specification structure.

        Args:
            spec: OpenAPI specification dictionary

        Raises:
            ValidationError: If the specification is invalid

        """
        if not isinstance(spec, dict):
            raise ValidationError("OpenAPI spec must be a dictionary")

        # Check for required top-level keys
        required_keys = ["openapi", "info"]
        missing_keys = [key for key in required_keys if key not in spec]
        if missing_keys:
            raise ValidationError(
                f"Missing required OpenAPI keys: {missing_keys}",
                {"missing_keys": missing_keys},
            )

        # Validate components structure
        components = spec.get("components", {})
        if components and not isinstance(components, dict):
            raise ValidationError("Components must be a dictionary")

        # Validate schemas structure
        schemas = components.get("schemas", {})
        if schemas and not isinstance(schemas, dict):
            raise ValidationError("Schemas must be a dictionary")

        # Validate paths structure
        paths = spec.get("paths", {})
        if paths and not isinstance(paths, dict):
            raise ValidationError("Paths must be a dictionary")

    @staticmethod
    def validate_schema(schema_name: str, schema: dict[str, Any]) -> None:
        """Validate individual schema structure.

        Args:
            schema_name: Name of the schema
            schema: Schema definition

        Raises:
            ValidationError: If the schema is invalid

        """
        if not isinstance(schema, dict):
            raise ValidationError(f"Schema '{schema_name}' must be a dictionary")

        schema_type = schema.get("type")
        if schema_type and schema_type not in ["object", "array", "string", "number", "integer", "boolean"]:
            logger.warning(f"Schema '{schema_name}' has unsupported type: {schema_type}")


class FileSystemValidator:
    """Validates file system operations and permissions."""

    @staticmethod
    def validate_output_directory(output_dir: Path) -> None:
        """Validate output directory is writable.

        Args:
            output_dir: Path to output directory

        Raises:
            ValidationError: If directory cannot be created or is not writable

        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise ValidationError(
                f"Permission denied creating directory: {output_dir}",
                {"original_error": str(e)},
            ) from e
        except OSError as e:
            raise ValidationError(
                f"Failed to create directory: {output_dir}",
                {"original_error": str(e)},
            ) from e

        # Test write permissions
        test_file = output_dir / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
        except PermissionError as e:
            raise ValidationError(
                f"Directory is not writable: {output_dir}",
                {"original_error": str(e)},
            ) from e

    @staticmethod
    def validate_test_data_directory(test_data_dir: Path) -> None:
        """Validate test data directory structure.

        Args:
            test_data_dir: Path to test data directory

        Raises:
            ValidationError: If directory structure is invalid

        """
        if not test_data_dir.exists():
            raise ValidationError(f"Test data directory not found: {test_data_dir}")

        if not test_data_dir.is_dir():
            raise ValidationError(f"Test data path is not a directory: {test_data_dir}")


class TestDataValidator:
    """Validates generated test data."""

    @staticmethod
    def validate_payload_structure(payload: dict[str, Any], schema_name: str) -> None:
        """Validate payload structure against expected format.

        Args:
            payload: Generated payload
            schema_name: Name of the schema

        Raises:
            ValidationError: If payload structure is invalid

        """
        if not isinstance(payload, dict):
            raise ValidationError(f"Payload for {schema_name} must be a dictionary")

        if not payload:
            logger.warning(f"Empty payload generated for schema: {schema_name}")

    @staticmethod
    def validate_variant_structure(variant: dict[str, Any]) -> None:
        """Validate variant structure.

        Args:
            variant: Variant dictionary

        Raises:
            ValidationError: If variant structure is invalid

        """
        required_keys = ["description", "payload"]
        missing_keys = [key for key in required_keys if key not in variant]
        if missing_keys:
            raise ValidationError(
                f"Variant missing required keys: {missing_keys}",
                {"missing_keys": missing_keys},
            )

        if not isinstance(variant["description"], str):
            raise ValidationError("Variant description must be a string")

        if not isinstance(variant["payload"], dict):
            raise ValidationError("Variant payload must be a dictionary")
