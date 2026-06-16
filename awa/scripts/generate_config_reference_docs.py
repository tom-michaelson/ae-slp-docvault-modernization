#!/usr/bin/env python3
"""Generate reference documentation for the application configuration schema.

This script reads the app_config.schema.json file and generates comprehensive
markdown documentation that is written to docs/reference/configuration/application.md.
"""

import json
import sys
from pathlib import Path
from typing import Any

# Constant for minimum properties threshold for nested documentation
MIN_PROPERTIES_FOR_NESTED_DOCS = 1


def load_existing_content(file_path: Path) -> str | None:
    """Load existing file content as a string if it exists."""
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return None


def content_has_changed(existing_content: str | None, new_content: str) -> bool:
    """Check if content has actually changed."""
    if existing_content is None:
        return True
    return existing_content.strip() != new_content.strip()


def write_content_to_file(content: str, output_path: Path) -> None:
    """Write content to file, ensuring it ends with a newline."""
    content = content.rstrip() + "\n"
    with output_path.open("w", encoding="utf-8") as f:
        f.write(content)


def load_schema(schema_path: Path) -> dict[str, Any]:
    """Load the JSON schema from file."""
    with schema_path.open() as f:
        return json.load(f)


def format_type_info(prop: dict[str, Any]) -> str:
    """Format type information for a property, showing YAML types instead of class names."""
    if "type" in prop:
        if prop["type"] == "array" and "items" in prop:
            if "$ref" in prop["items"]:
                return "Array of objects"
            if "type" in prop["items"]:
                return f"Array of {prop['items']['type']}"
            return "Array"
        return prop["type"]
    if "$ref" in prop:
        # Check if this references an enum
        ref_name = prop["$ref"].split("/")[-1]
        if ref_name.endswith("Enum"):
            return "string (enum)"
        return "object"
    if "anyOf" in prop:
        types = []
        for option in prop["anyOf"]:
            if "type" in option:
                types.append(option["type"])
            elif "$ref" in option:
                types.append("object")
        return " or ".join(types)
    if "enum" in prop:
        return "string (enum)"
    return "Unknown"


def format_default_value(prop: dict[str, Any]) -> str | None:
    """Format the default value for a property."""
    if "default" in prop:
        default = prop["default"]
        if isinstance(default, str):
            return f'`"{default}"`'
        if default is None:
            return "`null`"
        if isinstance(default, bool):
            return f"`{str(default).lower()}`"
        return f"`{default}`"
    return None


def is_required_property(prop_name: str, obj: dict[str, Any]) -> bool:
    """Check if a property is required."""
    return prop_name in obj.get("required", [])


def get_enum_values_for_ref(ref_name: str, schema: dict[str, Any]) -> list[str] | None:
    """Get enum values for a referenced enum type."""
    if "$defs" in schema and ref_name in schema["$defs"]:
        enum_def = schema["$defs"][ref_name]
        if "enum" in enum_def:
            return enum_def["enum"]
    return None


def enhance_description_with_enum(description: str, prop_def: dict[str, Any], schema: dict[str, Any]) -> str:
    """Enhance property description with enum values if applicable."""
    enum_values = None

    # Check if this property directly references an enum
    if "$ref" in prop_def:
        ref_name = prop_def["$ref"].split("/")[-1]
        if ref_name.endswith("Enum"):
            enum_values = get_enum_values_for_ref(ref_name, schema)

    # Check if this property has inline enum
    elif "enum" in prop_def:
        enum_values = prop_def["enum"]

    if enum_values:
        enum_text = ", ".join(f"`{value}`" for value in enum_values)
        if description:
            return f"{description} Allowed values: {enum_text}."
        return f"Allowed values: {enum_text}."

    return description


def generate_property_table(
    properties: dict[str, Any],
    obj: dict[str, Any],
    schema: dict[str, Any],
    level: int = 0,
) -> str:
    """Generate a markdown table for properties."""
    if not properties:
        return ""

    indent = "  " * level
    table = f"{indent}| Property | Type | Required | Default | Description |\n"
    table += f"{indent}|----------|------|----------|---------|-------------|\n"

    for prop_name, prop_def in properties.items():
        type_info = format_type_info(prop_def)
        required = "Yes" if is_required_property(prop_name, obj) else "No"
        default = format_default_value(prop_def) or ""
        description = prop_def.get("description", "")

        # Enhance description with enum values if applicable
        description = enhance_description_with_enum(description, prop_def, schema)

        table += f"{indent}| `{prop_name}` | {type_info} | {required} | {default} | {description} |\n"

    return table


def generate_enum_documentation(enum_def: dict[str, Any]) -> str:
    """Generate documentation for enum types."""
    if "enum" not in enum_def:
        return ""

    doc = "**Allowed values:**\n\n"
    for value in enum_def["enum"]:
        doc += f"- `{value}`\n"

    return doc


def resolve_ref(ref: str, schema: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve a $ref to its definition in the schema."""
    if not ref.startswith("#/$defs/"):
        return None

    ref_name = ref.split("/")[-1]
    return schema.get("$defs", {}).get(ref_name)


def get_property_ref(prop_def: dict[str, Any]) -> str | None:
    """Extract a $ref from a property definition, handling direct refs and anyOf patterns."""
    # Direct reference
    if "$ref" in prop_def:
        return prop_def["$ref"]

    # Check anyOf for object references (ignoring null options)
    if "anyOf" in prop_def:
        for option in prop_def["anyOf"]:
            if "$ref" in option:
                return option["$ref"]

    return None


def should_generate_nested_docs(prop_def: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Determine if a property should have its own nested documentation section."""
    # Check for direct or anyOf references
    ref = get_property_ref(prop_def)
    if ref:
        resolved = resolve_ref(ref, schema)
        if resolved and "properties" in resolved:
            return len(resolved["properties"]) >= MIN_PROPERTIES_FOR_NESTED_DOCS

    # Check for array items that reference objects
    if prop_def.get("type") == "array" and "items" in prop_def:
        items_ref = get_property_ref(prop_def["items"])
        if items_ref:
            resolved = resolve_ref(items_ref, schema)
            if resolved and "properties" in resolved:
                return len(resolved["properties"]) >= MIN_PROPERTIES_FOR_NESTED_DOCS

    return False


def generate_nested_property_docs(
    prop_name: str,
    prop_def: dict[str, Any],
    schema: dict[str, Any],
    level: int = 4,
) -> str:
    """Generate documentation for a nested property that references another object."""
    doc = ""

    # Handle direct or anyOf object references
    ref = get_property_ref(prop_def)
    if ref:
        resolved = resolve_ref(ref, schema)
        if resolved:
            doc += generate_object_docs(prop_name, resolved, schema, level)

    # Handle array items that reference objects
    if prop_def.get("type") == "array" and "items" in prop_def:
        items_ref = get_property_ref(prop_def["items"])
        if items_ref:
            resolved = resolve_ref(items_ref, schema)
            if resolved and "properties" in resolved:
                # Use a descriptive name for array item documentation
                item_name = f"{prop_name} (array)"
                doc += generate_object_docs(item_name, resolved, schema, level)

    return doc


def generate_object_docs(
    obj_name: str,
    obj_def: dict[str, Any],
    schema: dict[str, Any],
    level: int = 4,
) -> str:
    """Generate documentation for an object definition."""
    heading = "#" * level
    doc = f"{heading} {obj_name}\n\n"

    if "description" in obj_def:
        doc += f"{obj_def['description']}\n\n"

    # Handle enum types
    if "enum" in obj_def:
        doc += generate_enum_documentation(obj_def)
        doc += "\n"
        return doc

    # Handle object properties
    if "properties" in obj_def:
        doc += generate_property_table(obj_def["properties"], obj_def, schema)
        doc += "\n"

        # Recursively generate subsections for complex nested objects
        for nested_prop_name, nested_prop_def in obj_def["properties"].items():
            if should_generate_nested_docs(nested_prop_def, schema):
                doc += generate_nested_property_docs(
                    nested_prop_name,
                    nested_prop_def,
                    schema,
                    level + 1,
                )

    return doc


def should_generate_section(prop_def: dict[str, Any], schema: dict[str, Any]) -> bool:
    """Determine if a top-level property should have its own documentation section."""
    # Check for direct or anyOf object references
    ref = get_property_ref(prop_def)
    if ref:
        resolved = resolve_ref(ref, schema)
        return resolved is not None and "properties" in resolved

    return False


def generate_section_documentation(
    section_name: str,
    section_def: dict[str, Any],
    schema: dict[str, Any],
    level: int = 3,
) -> str:
    """Generate documentation for a top-level configuration section."""
    # Resolve reference if needed
    ref = get_property_ref(section_def)
    if ref:
        resolved = resolve_ref(ref, schema)
        if not resolved:
            return ""
        return generate_object_docs(section_name, resolved, schema, level)

    return ""


def generate_documentation(schema: dict[str, Any]) -> str:
    """Generate the complete documentation dynamically from the schema."""
    doc = ""

    # Main configuration structure
    if "properties" in schema:
        doc += generate_property_table(schema["properties"], schema, schema)
        doc += "\n"

        # Generate sections for each top-level property
        for prop_name, prop_def in schema["properties"].items():
            # Only generate detailed sections for object references with sufficient complexity
            if should_generate_section(prop_def, schema):
                doc += generate_section_documentation(prop_name, prop_def, schema)

    return doc


def main() -> int:
    """Generate the documentation."""
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Paths
    schema_path = project_root / "awa" / "schemas" / "app_config.schema.json"
    output_path = project_root / "docs" / "reference" / "configuration" / "_application_generated.md"

    # Verify schema file exists
    if not schema_path.exists():
        sys.stderr.write(f"Error: Schema file not found at {schema_path}\n")
        return 1

    # Load schema
    try:
        schema = load_schema(schema_path)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"Error: Invalid JSON in schema file: {e}\n")
        return 1
    except OSError as e:
        sys.stderr.write(f"Error loading schema: {e}\n")
        return 1

    # Generate documentation
    try:
        documentation = generate_documentation(schema)
    except (KeyError, TypeError, ValueError) as e:
        sys.stderr.write(f"Error generating documentation: {e}\n")
        return 1

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing content to check for changes
    existing_content = load_existing_content(output_path)

    # Write documentation only if content has changed
    if content_has_changed(existing_content, documentation):
        try:
            write_content_to_file(documentation, output_path)
            sys.stdout.write(f"Documentation generated successfully at {output_path}\n")
        except OSError as e:
            sys.stderr.write(f"Error writing documentation: {e}\n")
            return 1
    else:
        sys.stdout.write(f"Documentation already up-to-date at {output_path}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
