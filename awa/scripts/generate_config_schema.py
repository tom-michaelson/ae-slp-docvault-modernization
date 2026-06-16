#!/usr/bin/env python3
"""Generate JSON schema for the AppConfig Pydantic model.

This script creates a JSON schema from the AppConfig model and saves it
to awa/schemas/app_config.schema.json for use in configuration validation
and documentation.
"""

import json
import sys
from pathlib import Path

# Add project root to path to allow importing AWA modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from awa.core.models.config.app_config import AppConfig  # noqa: E402


def load_existing_schema_content(file_path: Path) -> str | None:
    """Load existing schema file content as a string if it exists."""
    if not file_path.exists():
        return None

    try:
        with file_path.open("r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def format_schema_content(schema: dict) -> str:
    """Format schema as it would be written to file."""
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True)


def schemas_are_equal(existing_content: str | None, new_schema: dict) -> bool:
    """Compare existing file content with new schema content."""
    if existing_content is None:
        return False

    try:
        new_content = format_schema_content(new_schema)
        # Normalize both contents by stripping whitespace for comparison
        return existing_content.strip() == new_content.strip()
    except (TypeError, ValueError):
        return False


def write_schema_to_file(schema: dict, output_file: Path) -> None:
    """Write schema to file with consistent formatting."""
    content = format_schema_content(schema)
    # Ensure content ends with a newline to satisfy end-of-file-fixer
    if not content.endswith("\n"):
        content += "\n"
    with output_file.open("w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    """Generate and save the JSON schema for AppConfig."""
    # Get the project root directory (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Create schemas directory if it doesn't exist
    schemas_dir = project_root / "awa" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    # Define output file path
    output_file = schemas_dir / "app_config.schema.json"

    try:
        # Generate JSON schema from the Pydantic model
        new_schema = AppConfig.model_json_schema()

        # Load existing schema for comparison
        existing_content = load_existing_schema_content(output_file)

        # Only write if the schema has changed
        if existing_content is None or not schemas_are_equal(existing_content, new_schema):
            write_schema_to_file(new_schema, output_file)
            print(f"JSON schema generated successfully: {output_file}")
            print(f"Schema contains {len(new_schema.get('properties', {}))} top-level properties")
        else:
            print(f"Schema unchanged, skipping write: {output_file}")
            print(f"Schema contains {len(new_schema.get('properties', {}))} top-level properties")

    except (ValueError, TypeError, ImportError, AttributeError) as e:
        print(f"Error generating schema: {e}")
        print("Attempting to generate schema with mode='serialization'...")

        try:
            # Try with serialization mode to avoid some validation issues
            new_schema = AppConfig.model_json_schema(mode="serialization")

            # Load existing schema for comparison
            existing_content = load_existing_schema_content(output_file)

            # Only write if the schema has changed
            if existing_content is None or not schemas_are_equal(existing_content, new_schema):
                write_schema_to_file(new_schema, output_file)
                print(f"JSON schema generated successfully (with serialization mode): {output_file}")
                print(f"Schema contains {len(new_schema.get('properties', {}))} top-level properties")
            else:
                print(f"Schema unchanged, skipping write (serialization mode): {output_file}")
                print(f"Schema contains {len(new_schema.get('properties', {}))} top-level properties")

        except (ValueError, TypeError, ImportError, AttributeError) as e2:
            print(f"Error with serialization mode: {e2}")
            print("Attempting manual schema generation...")

            # Create a basic schema manually
            manual_schema = {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "title": "AppConfig",
                "description": "Main application configuration.",
                "type": "object",
                "properties": {
                    "llm": {
                        "title": "LLMConfig",
                        "description": "Configuration for LLM settings.",
                        "type": "object",
                    },
                    "jira": {
                        "title": "JiraConfig",
                        "description": "Configuration for Jira integration.",
                        "type": "object",
                    },
                },
                "required": ["llm"],
            }

            # Load existing schema for comparison
            existing_content = load_existing_schema_content(output_file)

            # Only write if the schema has changed
            if existing_content is None or not schemas_are_equal(existing_content, manual_schema):
                write_schema_to_file(manual_schema, output_file)
                print(f"Manual JSON schema generated: {output_file}")
            else:
                print(f"Manual schema unchanged, skipping write: {output_file}")

            print("Note: This is a simplified schema. For complete schema generation,")
            print("resolve the dependency issues in the Pydantic models.")


if __name__ == "__main__":
    main()
