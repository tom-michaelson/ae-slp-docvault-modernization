"""OpenAPI schema parsing utilities."""

from __future__ import annotations

import logging
from typing import Any

from tests.api.generation.core.constants import OPENAPI_SCHEMA_REF_PREFIX, SUPPORTED_HTTP_METHODS
from tests.api.generation.core.validation import OpenAPIValidator, ValidationError

logger = logging.getLogger(__name__)


class SchemaParser:
    """Parses OpenAPI specifications to extract schema information."""

    def __init__(self, openapi_spec: dict[str, Any]) -> None:
        """Initialize schema parser.

        Args:
            openapi_spec: Complete OpenAPI specification

        Raises:
            ValidationError: If OpenAPI spec is invalid

        """
        OpenAPIValidator.validate_openapi_spec(openapi_spec)

        self.spec = openapi_spec
        self.schemas = openapi_spec.get("components", {}).get("schemas", {})
        self.paths = openapi_spec.get("paths", {})

        logger.info(f"Parsed OpenAPI spec with {len(self.schemas)} schemas and {len(self.paths)} paths")

    def get_schemas(self) -> dict[str, dict[str, Any]]:
        """Get all schemas from the OpenAPI specification.

        Returns:
            Dictionary mapping schema names to schema definitions

        """
        return self.schemas.copy()

    def get_schema(self, schema_name: str) -> dict[str, Any] | None:
        """Get a specific schema by name.

        Args:
            schema_name: Name of the schema to retrieve

        Returns:
            Schema definition or None if not found

        """
        return self.schemas.get(schema_name)

    def get_endpoint_schemas(self) -> dict[str, str]:
        """Extract schemas for POST/PUT/PATCH endpoints.

        Returns:
            Dictionary mapping endpoint info to schema names

        """
        endpoint_schemas = {}

        for path, path_info in self.paths.items():
            for method, operation in path_info.items():
                if method.upper() in SUPPORTED_HTTP_METHODS:
                    schema_name = self._extract_request_schema(operation)
                    if schema_name:
                        endpoint_key = f"{method.upper()} {path}"
                        endpoint_schemas[endpoint_key] = schema_name
                        logger.debug(f"Found schema {schema_name} for endpoint {endpoint_key}")

        return endpoint_schemas

    def get_unique_request_schemas(self) -> set[str]:
        """Get unique schema names used in request bodies.

        Returns:
            Set of unique schema names

        """
        schema_names = set()

        for path_info in self.paths.values():
            for method, operation in path_info.items():
                if method.upper() in SUPPORTED_HTTP_METHODS:
                    schema_name = self._extract_request_schema(operation)
                    if schema_name:
                        schema_names.add(schema_name)

        logger.info(f"Found {len(schema_names)} unique request schemas: {sorted(schema_names)}")
        return schema_names

    def _extract_request_schema(self, operation: dict[str, Any]) -> str | None:
        """Extract request schema name from an operation.

        Args:
            operation: OpenAPI operation definition

        Returns:
            Schema name if found, None otherwise

        """
        try:
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema_ref = json_content.get("schema", {}).get("$ref", "")

            if schema_ref.startswith(OPENAPI_SCHEMA_REF_PREFIX):
                return schema_ref.replace(OPENAPI_SCHEMA_REF_PREFIX, "")

        except (KeyError, AttributeError) as e:
            logger.debug(f"Failed to extract schema from operation: {e}")

        return None

    def validate_schema(self, schema_name: str) -> bool:
        """Validate a specific schema structure.

        Args:
            schema_name: Name of the schema to validate

        Returns:
            True if schema is valid, False otherwise

        """
        schema = self.get_schema(schema_name)
        if not schema:
            logger.warning(f"Schema {schema_name} not found")
            return False

        try:
            OpenAPIValidator.validate_schema(schema_name, schema)
            return True
        except ValidationError:
            logger.exception(f"Schema {schema_name} validation failed")
            return False

    def get_schema_summary(self) -> dict[str, Any]:
        """Get summary information about parsed schemas.

        Returns:
            Dictionary with schema summary information

        """
        summary = {
            "total_schemas": len(self.schemas),
            "total_paths": len(self.paths),
            "request_schemas": list(self.get_unique_request_schemas()),
            "schema_types": {},
        }

        # Analyze schema types
        for schema in self.schemas.values():
            schema_type = schema.get("type", "unknown")
            if schema_type not in summary["schema_types"]:
                summary["schema_types"][schema_type] = 0
            summary["schema_types"][schema_type] += 1

        return summary
