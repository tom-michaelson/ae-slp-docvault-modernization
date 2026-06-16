"""Test data generator for API endpoints."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from fastapi.openapi.utils import get_openapi

from awa.core.api.api import Api
from tests.api.generation.core.constants import DEFAULT_GENERATED_DIR, MAX_INVALID_CASES, MAX_OPTIONAL_FIELDS
from tests.api.generation.core.data_writer import TestDataWriter
from tests.api.generation.core.field_generators import (
    FieldGeneratorRegistry,
    FieldValueGenerator,
    WrongTypeValueGenerator,
)
from tests.api.generation.core.schema_parser import SchemaParser
from tests.api.generation.core.validation import OpenAPIValidator, TestDataValidator, ValidationError
from tests.api.generation.core.workflow_templates import WorkflowTemplateProvider, WorkflowTemplateRegistry

logger = logging.getLogger(__name__)


class TestDataGenerator:
    """Orchestrates test data generation from OpenAPI schemas."""

    def __init__(
        self,
        openapi_spec: dict[str, Any],
        output_dir: str | Path = DEFAULT_GENERATED_DIR,
    ) -> None:
        """Initialize the test data generator.

        Args:
            openapi_spec: Complete OpenAPI specification
            output_dir: Directory to write generated test data files

        Raises:
            ValidationError: If inputs are invalid

        """
        # Validate inputs
        OpenAPIValidator.validate_openapi_spec(openapi_spec)

        # Initialize components
        self.schema_parser = SchemaParser(openapi_spec)
        self.writer = TestDataWriter(output_dir)
        self.field_registry = FieldGeneratorRegistry(openapi_spec)
        self.workflow_registry = WorkflowTemplateRegistry()
        self.wrong_type_generator = WrongTypeValueGenerator()

        logger.info(f"Initialized TestDataGenerator with output directory: {self.writer.output_dir}")

    def generate_all_endpoint_data(self) -> dict[str, Any]:
        """Generate test data for all POST/PUT/PATCH endpoints.

        Returns:
            Dictionary mapping schema names to generated data info

        """
        generated_data = {}
        unique_schemas = self.schema_parser.get_unique_request_schemas()

        logger.info(f"Generating test data for {len(unique_schemas)} unique schemas")

        for schema_name in unique_schemas:
            try:
                logger.info(f"Generating test data for schema: {schema_name}")
                data_info = self.generate_for_schema(schema_name)
                generated_data[schema_name] = data_info
            except (ValidationError, ValueError, TypeError, OSError):
                logger.exception(f"Failed to generate data for schema {schema_name}")
                continue

        return generated_data

    def generate_for_schema(self, schema_name: str) -> dict[str, Any]:
        """Generate complete test data set for a schema.

        Args:
            schema_name: Name of the schema to generate data for

        Returns:
            Dictionary with information about generated files

        Raises:
            ValidationError: If schema is not found or invalid

        """
        schema = self.schema_parser.get_schema(schema_name)
        if not schema:
            raise ValidationError(f"Schema {schema_name} not found in OpenAPI spec")

        # Validate schema
        if not self.schema_parser.validate_schema(schema_name):
            raise ValidationError(f"Schema {schema_name} validation failed")

        # Generate different types of test data
        basic_payload = self._generate_basic_payload(schema)
        variants = self._generate_payload_variants(schema_name, schema)
        invalid_payloads = self._generate_invalid_payloads(schema)

        # Write to files
        files_written = self.writer.write_schema_data_set(
            schema_name=schema_name,
            basic_payload=basic_payload,
            variants=variants,
            invalid_payloads=invalid_payloads,
        )

        return {
            "schema_name": schema_name,
            "files": files_written,
            "basic_payload": basic_payload,
            "variant_count": len(variants) if variants else 0,
            "invalid_count": len(invalid_payloads) if invalid_payloads else 0,
        }

    def _generate_basic_payload(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Generate a minimal valid payload for the schema.

        Args:
            schema: Schema definition

        Returns:
            Basic valid payload

        """
        if schema.get("type") != "object":
            return {}

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        payload = {}

        # Add all required fields with appropriate defaults
        for field_name in required:
            if field_name in properties:
                field_schema = properties[field_name]
                payload[field_name] = self.field_registry.generate_value(
                    field_name,
                    field_schema,
                    "basic",
                )

        # Add some optional fields for completeness
        optional_fields = [name for name in properties if name not in required]
        for field_name in optional_fields[:MAX_OPTIONAL_FIELDS]:
            field_schema = properties[field_name]
            payload[field_name] = self.field_registry.generate_value(
                field_name,
                field_schema,
                "basic",
            )

        # Validate generated payload
        TestDataValidator.validate_payload_structure(payload, "basic")

        return payload

    def _generate_payload_variants(self, schema_name: str, schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate multiple valid payload variations.

        Args:
            schema_name: Name of the schema
            schema: Schema definition

        Returns:
            List of payload variants with descriptions

        """
        if schema.get("type") != "object":
            return []

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        variants = []

        # For WorkflowRunPayload, generate workflow-specific variants first
        if schema_name == "WorkflowRunPayload":
            workflow_variants = self.workflow_registry.get_workflow_specific_variants()
            variants.extend(workflow_variants)

        # Generate standard schema-based variants

        # Variant 1: All required fields only
        variant1 = {}
        for field_name in required:
            if field_name in properties:
                field_schema = properties[field_name]
                variant1[field_name] = self.field_registry.generate_value(
                    field_name,
                    field_schema,
                    "minimal",
                )

        if variant1:
            variant_data = {
                "description": f"Minimal {schema_name} with required fields only",
                "payload": variant1,
            }
            TestDataValidator.validate_variant_structure(variant_data)
            variants.append(variant_data)

        # Variant 2: All fields
        variant2 = {}
        for field_name, field_schema in properties.items():
            variant2[field_name] = self.field_registry.generate_value(
                field_name,
                field_schema,
                "complete",
            )

        if variant2:
            variant_data = {
                "description": f"Complete {schema_name} with all fields",
                "payload": variant2,
            }
            TestDataValidator.validate_variant_structure(variant_data)
            variants.append(variant_data)

        # Variant 3: Edge case values
        variant3 = {}
        for field_name in required:
            if field_name in properties:
                field_schema = properties[field_name]
                variant3[field_name] = self.field_registry.generate_value(
                    field_name,
                    field_schema,
                    "edge",
                )

        if variant3 and variant3 != variant1:
            variant_data = {
                "description": f"{schema_name} with edge case values",
                "payload": variant3,
            }
            TestDataValidator.validate_variant_structure(variant_data)
            variants.append(variant_data)

        return variants

    def _generate_invalid_payloads(self, schema: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate systematic invalid payload cases.

        Args:
            schema: Schema definition

        Returns:
            List of invalid payloads with expected errors

        """
        if schema.get("type") != "object":
            return []

        properties = schema.get("properties", {})
        required = schema.get("required", [])
        invalid_cases = []

        # Generate a basic valid payload to modify
        base_payload = {}
        for field_name, field_schema in properties.items():
            base_payload[field_name] = self.field_registry.generate_value(
                field_name,
                field_schema,
                "basic",
            )

        # Missing required fields
        for field_name in required:
            invalid_payload = base_payload.copy()
            del invalid_payload[field_name]
            invalid_cases.append(
                {
                    "description": f"Missing required '{field_name}' field",
                    "payload": invalid_payload,
                    "expected_error": "422 - Validation Error",
                },
            )

        # Wrong types for fields
        for field_name, field_schema in properties.items():
            field_type = field_schema.get("type")
            if field_type:
                invalid_payload = base_payload.copy()
                invalid_payload[field_name] = self.wrong_type_generator.generate_wrong_type_value(field_type)
                invalid_cases.append(
                    {
                        "description": f"Wrong type for '{field_name}' field",
                        "payload": invalid_payload,
                        "expected_error": "422 - Validation Error",
                    },
                )

        # Empty values where not allowed
        for field_name, field_schema in properties.items():
            min_length = field_schema.get("minLength")
            if min_length and min_length > 0:
                invalid_payload = base_payload.copy()
                invalid_payload[field_name] = ""
                invalid_cases.append(
                    {
                        "description": f"Empty '{field_name}' field (minLength={min_length})",
                        "payload": invalid_payload,
                        "expected_error": "422 - Validation Error",
                    },
                )

        return invalid_cases[:MAX_INVALID_CASES]  # Limit to prevent excessive cases

    def register_custom_field_generator(self, generator: FieldValueGenerator) -> None:
        """Register a custom field generator.

        Args:
            generator: Custom field generator implementing FieldValueGenerator protocol

        Example:
            generator.register_custom_field_generator(MyCustomGenerator())

        """
        self.field_registry.register_generator(generator)

    def register_custom_workflow_provider(self, provider: WorkflowTemplateProvider) -> None:
        """Register a custom workflow template provider.

        Args:
            provider: Custom workflow provider implementing WorkflowTemplateProvider interface

        Example:
            generator.register_custom_workflow_provider(MyWorkflowProvider())

        """
        self.workflow_registry.register_provider(provider)

    def get_generation_summary(self) -> dict[str, Any]:
        """Get summary of the generation capabilities.

        Returns:
            Dictionary with generation summary

        """
        schema_summary = self.schema_parser.get_schema_summary()
        supported_workflows = self.workflow_registry.get_supported_workflows()

        return {
            "schema_info": schema_summary,
            "supported_workflows": supported_workflows,
            "output_directory": str(self.writer.output_dir),
            "field_generators": len(self.field_registry.generators),
            "workflow_providers": len(self.workflow_registry.providers),
        }


def main() -> None:
    """Generate test data from OpenAPI specification."""
    # Create API instance to get OpenAPI spec
    api = Api()
    openapi_spec = get_openapi(
        title="Agentic Workflow Accelerator API",
        version="1.0.0",
        description="API for the Agentic Workflow Accelerator",
        routes=api.app.routes,
    )

    # Generate test data
    try:
        generator = TestDataGenerator(openapi_spec)
        generated_data = generator.generate_all_endpoint_data()

        # Report results
        logger.info("Test data generation completed!")
        for schema_name, info in generated_data.items():
            files = info.get("files", {})
            logger.info(f"Schema {schema_name}: {len(files)} files generated")
            for file_type, file_path in files.items():
                logger.info(f"  - {file_type}: {file_path}")

        # Print summary
        summary = generator.get_generation_summary()
        logger.info(f"Generation summary: {summary}")

    except ValidationError as e:
        logger.exception("Validation error")
        if e.details:
            logger.info(f"Details: {e.details}")
    except Exception:
        logger.exception("Unexpected error during test data generation")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
