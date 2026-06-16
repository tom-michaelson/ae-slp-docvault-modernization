"""Field value generators for test data generation."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

FieldValue = str | int | float | bool | dict[str, Any] | list[Any]
SchemaDict = dict[str, Any]

logger = logging.getLogger(__name__)


class FieldValueGenerator:
    """Protocol for field value generators."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool: ...
    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> FieldValue: ...


class BaseFieldGenerator(ABC):
    """Base class for field value generators."""

    @abstractmethod
    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool: ...
    @abstractmethod
    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> FieldValue: ...


class WorkerNameGenerator(BaseFieldGenerator):
    """Generator for worker name fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_name.lower() in ["name", "worker_name"]

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:  # noqa: ARG002
        values = {
            "basic": "test-worker",
            "variant": "my-test-worker",
            "minimal": "worker",
        }
        return values.get(variant, "test-worker")


class VersionGenerator(BaseFieldGenerator):
    """Generator for version fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_name.lower() in ["version", "worker_version"]

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:  # noqa: ARG002
        values = {
            "basic": "1.0.0",
            "variant": "2.1.0",
            "minimal": "1.0",
        }
        return values.get(variant, "1.0.0")


class TaskQueueGenerator(BaseFieldGenerator):
    """Generator for task queue fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_name.lower() in ["task_queue"]

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:  # noqa: ARG002
        values = {
            "basic": "default-task-queue",
            "variant": "worker-task-queue",
            "minimal": "default",
        }
        return values.get(variant, "default-task-queue")


class InputGenerator(BaseFieldGenerator):
    """Generator for input fields (JSON strings)."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_name.lower() == "input"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:  # noqa: ARG002
        values = {
            "basic": '{"name": "TestUser"}',
            "variant": '{"name": "VariantUser", "type": "test"}',
            "minimal": "{}",
        }
        return values.get(variant, '{"name": "TestUser"}')


class WorkflowNameGenerator(BaseFieldGenerator):
    """Generator for workflow name fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:
        return field_name.lower() == "name" and field_schema.get("type") == "string"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:  # noqa: ARG002
        values = {
            "basic": "awa-hello-human",
            "variant": "awa-hello-world",
            "minimal": "awa-test",
        }
        return values.get(variant, "awa-hello-human")


class WorkflowDefinitionGenerator(BaseFieldGenerator):
    """Generator for WorkflowDefinition objects."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        # Check if this is a WorkflowDefinition object
        return (
            field_schema.get("type") == "object"
            and "name" in field_schema.get("properties", {})
            and "task_queue" in field_schema.get("properties", {})
            and "input_schema" in field_schema.get("properties", {})
        )

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> dict[str, Any]:  # noqa: ARG002
        """Generate a WorkflowDefinition object."""
        workflows = [
            {
                "name": "awa-hello-world",
                "task_queue": "awa_default",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "title": "Name",
                            "type": "string",
                        },
                    },
                    "required": ["name"],
                    "title": "HelloWorldInput",
                },
            },
            {
                "name": "awa-hello-human",
                "task_queue": "awa_default",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                        },
                    },
                },
            },
        ]

        if variant in {"minimal", "basic"}:
            return workflows[0]
        return workflows[1]


class ActivityDefinitionGenerator(BaseFieldGenerator):
    """Generator for ActivityDefinition objects."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:
        # Check if this is an ActivityDefinition object
        # Look for activity-specific field names, schema title, or check if it's in an activities array
        return (
            field_schema.get("type") == "object"
            and "name" in field_schema.get("properties", {})
            and "task_queue" in field_schema.get("properties", {})
            and "input_schema" in field_schema.get("properties", {})
            and (
                "activity" in field_name.lower()
                or "activities" in field_name.lower()
                or field_schema.get("title") == "ActivityDefinition"
            )
        )

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> dict[str, Any]:  # noqa: ARG002
        """Generate an ActivityDefinition object."""
        activities = [
            {
                "name": "test-activity",
                "task_queue": "awa_default",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "input": {
                            "type": "string",
                            "description": "Activity input data",
                        },
                    },
                    "required": ["input"],
                },
            },
            {
                "name": "another-activity",
                "task_queue": "awa_default",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "value": {
                            "type": "number",
                            "description": "Numeric input value",
                        },
                    },
                    "required": ["value"],
                },
            },
        ]

        if variant in {"minimal", "basic"}:
            return activities[0]
        return activities[1]


class StringTypeGenerator(BaseFieldGenerator):
    """Generator for generic string fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_schema.get("type") == "string"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:
        field_format = field_schema.get("format")

        if field_format == "date-time":
            return datetime.now(UTC).isoformat()
        if field_format == "email":
            return "test@example.com"
        if field_format == "uri":
            return "https://example.com"
        min_length = field_schema.get("minLength", 1)
        base_value = f"test-{field_name}"

        if variant == "minimal":
            return base_value[: max(min_length, len(base_value))]
        if variant == "edge":
            return "a" * min_length if min_length > 0 else base_value
        return base_value


class IntegerTypeGenerator(BaseFieldGenerator):
    """Generator for integer fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_schema.get("type") == "integer"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> int:  # noqa: ARG002
        minimum = field_schema.get("minimum", 1)
        maximum = field_schema.get("maximum", 100)
        values = {
            "basic": min(10, maximum),
            "variant": min(50, maximum),
            "minimal": minimum,
        }
        return values.get(variant, min(10, maximum))


class NumberTypeGenerator(BaseFieldGenerator):
    """Generator for number fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_schema.get("type") == "number"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> float:  # noqa: ARG002
        minimum = field_schema.get("minimum", 1.0)
        maximum = field_schema.get("maximum", 100.0)
        values = {
            "basic": min(10.5, maximum),
            "variant": min(75.25, maximum),
            "minimal": minimum,
        }
        return values.get(variant, min(10.5, maximum))


class BooleanTypeGenerator(BaseFieldGenerator):
    """Generator for boolean fields."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_schema.get("type") == "boolean"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> bool:  # noqa: ARG002
        return variant != "minimal"  # True for most variants, False for minimal


class ArrayTypeGenerator(BaseFieldGenerator):
    """Generator for array fields."""

    def __init__(self, field_registry: FieldGeneratorRegistry) -> None:
        self.field_registry = field_registry

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_schema.get("type") == "array"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> list[FieldValue]:
        items_schema = field_schema.get("items", {})

        if variant == "minimal":
            return []

        # Resolve schema reference if present
        resolved_schema = items_schema
        if "$ref" in items_schema:
            ref_name = items_schema["$ref"].split("/")[-1]
            # Use the registry's schema resolver
            resolved_schema = self.field_registry.resolve_schema_reference(ref_name) or items_schema

        # Generate a few items for the array
        items = []
        for i in range(2):  # Generate 2 items
            item = self.field_registry.generate_value(f"{field_name}_item_{i}", resolved_schema, "basic")
            items.append(item)
        return items


class ObjectTypeGenerator(BaseFieldGenerator):
    """Generator for object fields."""

    def __init__(self, field_registry: FieldGeneratorRegistry) -> None:
        self.field_registry = field_registry

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return field_schema.get("type") == "object"

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> dict[str, FieldValue]:  # noqa: ARG002
        if variant == "minimal":
            return {}

        properties = field_schema.get("properties", {})
        required = field_schema.get("required", [])

        result = {}
        for prop_name, prop_schema in properties.items():
            if prop_name in required or variant != "minimal":
                result[prop_name] = self.field_registry.generate_value(prop_name, prop_schema, "basic")

        return result


class FallbackGenerator(BaseFieldGenerator):
    """Fallback generator for unknown field types."""

    def can_generate(self, field_name: str, field_schema: SchemaDict) -> bool:  # noqa: ARG002
        return True  # Always available as fallback

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> str:  # noqa: ARG002
        return f"generated-{field_name}"


class FieldGeneratorRegistry:
    """Registry for field value generators."""

    def __init__(self, openapi_spec: dict[str, Any] | None = None) -> None:
        self.generators: list[FieldValueGenerator] = []
        self.openapi_spec = openapi_spec
        self._setup_default_generators()

    def resolve_schema_reference(self, ref: str) -> dict[str, Any] | None:
        """Resolve a schema reference to its definition.

        Args:
            ref: Schema reference (e.g., "WorkflowDefinition")

        Returns:
            Resolved schema definition or None if not found

        """
        if not self.openapi_spec:
            return None

        schemas = self.openapi_spec.get("components", {}).get("schemas", {})
        return schemas.get(ref)

    def _setup_default_generators(self) -> None:
        """Set up default field generators in priority order."""
        # Specific field name generators (highest priority)
        self.generators.extend(
            [
                WorkerNameGenerator(),
                VersionGenerator(),
                TaskQueueGenerator(),
                InputGenerator(),
                WorkflowNameGenerator(),
            ],
        )

        # Object-specific generators (high priority) - order matters!
        self.generators.extend(
            [
                ActivityDefinitionGenerator(),  # More specific - check for "activity" in name
                WorkflowDefinitionGenerator(),  # More general - check for workflow-like objects
            ],
        )

        # Type-based generators
        self.generators.extend(
            [
                StringTypeGenerator(),
                IntegerTypeGenerator(),
                NumberTypeGenerator(),
                BooleanTypeGenerator(),
            ],
        )

        # Complex type generators (need registry reference)
        self.generators.append(ArrayTypeGenerator(self))
        self.generators.append(ObjectTypeGenerator(self))

        # Fallback generator (lowest priority)
        self.generators.append(FallbackGenerator())

    def register_generator(self, generator: FieldValueGenerator) -> None:
        """Register a custom field generator.

        Args:
            generator: Field generator to register

        """
        # Insert before fallback generator
        self.generators.insert(-1, generator)

    def generate_value(self, field_name: str, field_schema: SchemaDict, variant: str) -> FieldValue:
        """Generate a value for the given field.

        Args:
            field_name: Name of the field
            field_schema: Schema definition for the field
            variant: Type of variant ("basic", "minimal", "complete", "edge")

        Returns:
            Generated value appropriate for the field type

        """
        for generator in self.generators:
            if generator.can_generate(field_name, field_schema):
                try:
                    return generator.generate_value(field_name, field_schema, variant)
                except (ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning(f"Generator {generator.__class__.__name__} failed for field {field_name}: {e}")
                    continue

        # This should never happen since FallbackGenerator always returns True
        return f"fallback-{field_name}"


class WrongTypeValueGenerator:
    """Generates values of wrong types for validation testing."""

    @staticmethod
    def generate_wrong_type_value(expected_type: str) -> str | int:
        """Generate a value of wrong type for testing validation.

        Args:
            expected_type: The expected type

        Returns:
            Value of wrong type

        """
        wrong_types = {
            "string": 12345,
            "integer": "not_a_number",
            "number": "not_a_number",
            "boolean": "not_a_boolean",
            "array": "not_an_array",
            "object": "not_an_object",
        }
        return wrong_types.get(expected_type, "unknown_type")
