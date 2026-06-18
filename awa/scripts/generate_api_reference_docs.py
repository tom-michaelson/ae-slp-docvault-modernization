"""Generate API reference documentation from FastAPI OpenAPI spec.

This script automatically generates markdown documentation for all API endpoints
by extracting information from the FastAPI OpenAPI specification.
"""

import json
from pathlib import Path
from typing import Any

from fastapi.openapi.utils import get_openapi

from awa.core.api.api import Api
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging


def format_parameter(param: dict[str, Any]) -> str:
    """Format a parameter for documentation."""
    param_type = param.get("type", "string")
    required = param.get("required", False)
    description = param.get("description", "")
    param_in = param.get("in", "")

    # Use badges for parameter location
    location_badge = f' <Badge type="info" text="{param_in}" />' if param_in else ""
    required_badge = (
        ' <Badge type="warning" text="required" />' if required else ' <Badge type="tip" text="optional" />'
    )
    desc_text = f" - {description}" if description else ""

    return f"- **`{param['name']}`** (`{param_type}`){location_badge}{required_badge}{desc_text}"


def extract_field_descriptions(description: str) -> dict[str, str]:
    """Extract field descriptions from docstring-style attributes section."""
    field_descriptions = {}
    if "Attributes:" in description:
        attributes_section = description.split("Attributes:")[1].strip()
        lines = attributes_section.split("\n")

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Check if this line contains a field definition (field_name: description)
            # Look for pattern like "field_name: some description"
            if ":" in stripped_line:
                parts = stripped_line.split(":", 1)
                if len(parts) == 2:  # noqa: PLR2004
                    field_name = parts[0].strip()
                    field_desc = parts[1].strip()

                    # Only consider it a field if the field name doesn't contain spaces
                    # and the description exists
                    if field_name and " " not in field_name and field_desc:
                        field_descriptions[field_name] = field_desc

    return field_descriptions


def format_schema(schema: dict[str, Any], schemas: dict[str, Any], parent_description: str = "") -> str:
    """Format a schema definition for documentation."""
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        if ref_name in schemas:
            return format_schema(schemas[ref_name], schemas, parent_description)
        return f"`{ref_name}`"

    if schema.get("type") == "object":
        properties = schema.get("properties", {})
        if not properties:
            return "`object`"

        formatted_props = []
        required_fields = schema.get("required", [])

        # Extract field descriptions from parent schema description
        field_descriptions = extract_field_descriptions(parent_description)

        for prop_name, prop_schema in properties.items():
            prop_type = get_type_string(prop_schema, schemas)
            required_badge = ' <Badge type="warning" text="required" /> ' if prop_name in required_fields else ""

            # Use description from attributes section or fall back to property description
            description = field_descriptions.get(prop_name, prop_schema.get("description", ""))
            desc_text = f"{description}" if description else ""

            formatted_props.append(f"| `{prop_name}` | `{prop_type}` |{required_badge}{desc_text} |")

        table_header = "| Property | Type | Details |\n|----------|------|---------|\n"
        return table_header + "\n".join(formatted_props)

    if schema.get("type") == "array":
        items_schema = schema.get("items", {})
        items_type = get_type_string(items_schema, schemas)
        return f"`{items_type}[]`"

    return f"`{schema.get('type', 'unknown')}`"


def get_type_string(schema: dict[str, Any], schemas: dict[str, Any]) -> str:
    """Get a simple type string for a schema."""
    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]
    if schema.get("type") == "array":
        items_schema = schema.get("items", {})
        items_type = get_type_string(items_schema, schemas)
        return f"{items_type}[]"
    return schema.get("type", "unknown")


def format_response(response: dict[str, Any], schemas: dict[str, Any]) -> str:
    """Format a response for documentation."""
    description = response.get("description", "")
    content = response.get("content", {})

    if not content:
        return f"{description}"

    # Get the first content type (usually application/json)
    content_type = next(iter(content.keys()))
    schema = content[content_type].get("schema", {})

    formatted_schema = format_schema(schema, schemas, "")

    result = f"{description}\n\n"
    if content_type == "application/json":
        result += f"**Response Schema** (`{content_type}`):\n\n{formatted_schema}"
    else:
        result += f"**Content Type**: `{content_type}`\n\n{formatted_schema}"

    return result


def get_method_badge(method: str) -> str:
    """Get a colored badge for HTTP method."""
    method_colors = {
        "get": "tip",
        "post": "info",
        "put": "warning",
        "delete": "danger",
        "patch": "warning",
    }
    color = method_colors.get(method.lower(), "info")
    return f'<Badge type="{color}" text="{method.upper()}" />'


def generate_endpoint_doc(path: str, method: str, operation: dict[str, Any], schemas: dict[str, Any]) -> str:
    """Generate documentation for a single endpoint."""
    summary = operation.get("summary", "")
    description = operation.get("description", "")

    method_and_path = f"{method.upper()} `{path}`"
    if not summary:
        summary = method_and_path

    # Create endpoint header with method badge
    doc = f"### {summary}\n\n"

    doc += f"#### {method_and_path}\n\n"

    if description:
        doc += f"{description}\n\n"
    else:
        doc += "(no description)\n\n"

    # Parameters
    parameters = operation.get("parameters", [])
    if parameters:
        doc += "#### Parameters\n\n"
        for param in parameters:
            doc += format_parameter(param) + "\n"
        doc += "\n"

    # Request Body
    request_body = operation.get("requestBody")
    if request_body:
        content = request_body.get("content", {})
        if content:
            content_type = next(iter(content.keys()))
            schema = content[content_type].get("schema", {})
            formatted_schema = format_schema(schema, schemas, "")

            doc += "#### Request Body\n\n"
            if content_type == "application/json":
                doc += (
                    "::: code-group\n\n"
                    "```json [Example]\n"
                    "// Request body structure\n"
                    "{\n"
                    "  // See schema below\n"
                    "}\n"
                    "```\n\n"
                    ":::\n\n"
                )
            doc += f"**Content Type:** `{content_type}`\n\n{formatted_schema}\n\n"

    # Responses
    responses = operation.get("responses", {})
    if responses:
        doc += "#### Responses\n\n"
        for status_code, response in responses.items():
            status_badge_type = (
                "tip" if status_code.startswith("2") else "warning" if status_code.startswith("4") else "danger"
            )
            status_badge = f'<Badge type="{status_badge_type}" text="{status_code}" />'
            doc += f"#### {status_badge}\n\n{format_response(response, schemas)}\n\n"

    doc += "---\n\n"

    return doc


def generate_api_reference_docs() -> None:
    """Generate API reference documentation from FastAPI OpenAPI spec."""
    init_logging()
    logger = get_logger(LoggerComponent.API)

    logger.info("Generating API reference documentation...")

    try:
        # Create FastAPI app instance
        api = Api()
        app = api.app

        # Generate OpenAPI spec
        openapi_spec = get_openapi(
            title=app.title or "AWA API",
            version=app.version or "1.0.0",
            description=app.description or "Agentic Workflow Accelerator API",
            routes=app.routes,
        )

        # Extract components
        schemas = openapi_spec.get("components", {}).get("schemas", {})
        paths = openapi_spec.get("paths", {})

        # Generate documentation with frontmatter
        description = openapi_spec.get("info", {}).get("description", "Agentic Workflow Accelerator API")

        doc_content = f"""---
title: API Reference
description: {description}
outline: [2, 3]
---

# API Reference

This documentation is automatically generated from the FastAPI OpenAPI specification.

## Endpoints

"""

        # Sort paths for consistent output
        sorted_paths = sorted(paths.items())

        for path, methods in sorted_paths:
            for method, operation in methods.items():
                if method in ["get", "post", "put", "delete", "patch", "options", "head"]:
                    doc_content += generate_endpoint_doc(path, method, operation, schemas)

        # Add schemas section
        if schemas:
            doc_content += "\n## Data Models\n\n"
            for schema_name, schema_def in sorted(schemas.items()):
                doc_content += f"### {schema_name}\n\n"
                schema_description = schema_def.get("description", "")
                if schema_description:
                    # Clean up the description by removing docstring-style "Attributes:" sections
                    if "Attributes:" in schema_description:
                        # Only take the part before "Attributes:"
                        clean_description = schema_description.split("Attributes:")[0].strip()
                        if clean_description:
                            doc_content += f"{clean_description}\n\n"
                    else:
                        doc_content += f"{schema_description}\n\n"

                # Format properties as a clean table with field descriptions from attributes
                full_description = schema_def.get("description", "")
                if schema_def.get("type") == "object" and schema_def.get("properties"):
                    doc_content += format_schema(schema_def, schemas, full_description)
                else:
                    doc_content += format_schema(schema_def, schemas, full_description)
                doc_content += "\n\n---\n\n"

        # Write to docs directory
        docs_dir = Path("docs/reference")
        docs_dir.mkdir(parents=True, exist_ok=True)

        api_docs_path = docs_dir / "api.md"
        api_docs_path.write_text(doc_content.rstrip() + "\n", encoding="utf-8")

        logger.info(f"API reference documentation generated successfully: {api_docs_path}")

        # Also save OpenAPI spec as JSON for reference
        openapi_path = docs_dir / "openapi.json"
        openapi_path.write_text(json.dumps(openapi_spec, indent=2) + "\n", encoding="utf-8")

        logger.info(f"OpenAPI specification saved: {openapi_path}")

    except Exception:
        logger.exception("Failed to generate API reference documentation")
        raise


if __name__ == "__main__":
    generate_api_reference_docs()
