import importlib.util
import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any

from temporalio import activity

from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError
from awa.workflows.generate_sdk import constants
from awa.workflows.generate_sdk.models.generate_sdk_schemas_input import GenerateSdkSchemasInput


@activity.defn(name=constants.ACTIVITY_GENERATE_SCHEMAS)
async def generate_schemas_activity(activity_input: GenerateSdkSchemasInput) -> list[str]:
    """Generate JSON schemas from Pydantic models in the SDK models directory.

    Args:
        activity_input: Input containing the Pydantic models path and output path for generated schemas

    Returns:
        List of generated schema file paths

    """
    # Set up paths
    models_dir = Path(activity_input.models_path)
    output_dir = Path(activity_input.output_path)

    # Validate models directory exists
    if not models_dir.exists():
        raise InvalidInputApplicationError(f"Models directory not found: {models_dir}")

    # Discover models
    models = _discover_models(models_dir)

    if not models:
        activity.logger.warning("No Pydantic models found!")
        return []

    activity.logger.info(f"Found {len(models)} model(s)")

    # Generate schemas
    generated_files = _generate_schemas(models, output_dir)

    activity.logger.info(f"Successfully generated schemas for {len(generated_files)} models")
    return generated_files


def _discover_models(models_dir: Path) -> dict[str, Any]:
    """Discover all Pydantic models in the models directory."""
    activity.logger.info("Discovering Pydantic models...")

    models = {}
    seen_model_classes = set()  # Track unique model classes by their id

    # Add models directory to sys.path
    sys.path.insert(0, str(models_dir.parent))

    try:
        # Walk through the models directory
        for py_file in models_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            # Calculate relative path and module name
            rel_path = py_file.relative_to(models_dir.parent)
            module_name = str(rel_path.with_suffix("")).replace("/", ".")

            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find all Pydantic BaseModel classes and Enum classes
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)

                    # Check for BaseModel classes
                    is_base_model = hasattr(attr, "__bases__") and any(
                        base.__name__ == "BaseModel" for base in attr.__bases__
                    )

                    # Check for Enum classes (including StrEnum)
                    is_enum = hasattr(attr, "__bases__") and any(
                        base.__name__ in ("Enum", "StrEnum", "IntEnum")
                        or (hasattr(base, "__bases__") and any(b.__name__ == "Enum" for b in base.__bases__))
                        for base in attr.__bases__
                    )

                    if is_base_model or is_enum:
                        # Check if we've already seen this exact class
                        class_id = id(attr)
                        if class_id in seen_model_classes:
                            model_type = "enum" if is_enum else "model"
                            activity.logger.info(
                                f"Skipping duplicate: {attr_name} ({model_type}) in {rel_path} (already found)",
                            )
                            continue

                        # Check if model is defined in this file (not just imported)
                        if hasattr(attr, "__module__") and attr.__module__ == module_name:
                            models[attr_name] = attr
                            seen_model_classes.add(class_id)
                            model_type = "enum" if is_enum else "model"
                            activity.logger.info(f"Found {model_type}: {attr_name} in {rel_path}")
                        else:
                            module_name_str = getattr(attr, "__module__", "unknown")
                            model_type = "enum" if is_enum else "model"
                            activity.logger.info(
                                f"Skipping imported {model_type}: {attr_name} in {rel_path} "
                                f"(defined in {module_name_str})",
                            )

            except (ImportError, AttributeError, SyntaxError) as e:
                activity.logger.warning(f"Could not import {module_name}: {e}")
                continue

    except (OSError, ImportError) as e:
        activity.logger.error(f"Error discovering models: {e}")
        return {}
    finally:
        # Clean up sys.path
        if str(models_dir.parent) in sys.path:
            sys.path.remove(str(models_dir.parent))

    return models


def _has_self_references(schema: dict[str, Any], model_name: str) -> bool:
    """Check if a schema contains references to itself.

    Args:
        schema: The JSON schema to check
        model_name: The name of the model being checked

    Returns:
        True if the schema contains self-references

    """

    def check_for_self_refs(obj: object) -> bool:
        if isinstance(obj, dict):
            # Check if this is a reference to the model itself
            if "$ref" in obj:
                ref_value = obj["$ref"]
                # Check both internal and potential external references
                # Also handle Pydantic's generated unique identifiers
                if ref_value in {f"#/$defs/{model_name}", f"./{model_name}.json"} or (
                    ref_value.startswith("#/$defs/") and model_name in ref_value
                ):
                    return True

            # Recursively check all values in the dictionary
            for value in obj.values():
                if check_for_self_refs(value):
                    return True

        elif isinstance(obj, list):
            # Check each item in the list
            for item in obj:
                if check_for_self_refs(item):
                    return True

        return False

    # Check the entire schema for self-references
    return check_for_self_refs(schema)


def _process_self_referential_schema(schema: dict[str, Any], model_name: str) -> dict[str, Any]:
    """Process a schema that contains self-references.

    For self-referential models, we keep the $defs section but convert
    external references to file references.

    Args:
        schema: The JSON schema to process
        model_name: The name of the model being processed

    Returns:
        Processed schema with proper reference handling

    """

    def process_refs(obj: object) -> object:
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref_value = obj["$ref"]
                # Check if this is an internal reference
                if ref_value.startswith("#/$defs/"):
                    ref_model = ref_value.replace("#/$defs/", "")

                    # Check if this is a self-reference (including Pydantic's unique identifiers)
                    if ref_model == model_name or (model_name in ref_model and "__" in ref_model):
                        # Keep self-references intact but normalize them to just the model name
                        obj["$ref"] = f"#/$defs/{model_name}"
                        activity.logger.info(f"Preserving self-reference: {ref_value} -> #/$defs/{model_name}")
                    else:
                        # This is a reference to a different model - extract just the model name
                        # Handle cases like "models__openai_agents__openai_agent_config__OpenAIAgentConfig__1"
                        # by extracting the actual model name (last part before __number)
                        if "__" in ref_model:
                            # Split by __ and find the model name part
                            parts = ref_model.split("__")
                            # The model name is typically the last part before the number
                            if parts[-1].isdigit():
                                actual_model = parts[-2] if len(parts) > 1 else ref_model
                            else:
                                actual_model = parts[-1]
                        else:
                            actual_model = ref_model

                        obj["$ref"] = f"./{actual_model}.json"
                        activity.logger.info(f"Converting external reference: {ref_model} to ./{actual_model}.json")

            # Recursively process all values except "$ref" itself
            for key, value in obj.items():
                if key != "$ref":  # Don't process the $ref key again
                    obj[key] = process_refs(value)

        elif isinstance(obj, list):
            # Process each item in the list
            for i, item in enumerate(obj):
                obj[i] = process_refs(item)

        return obj

    # Make a deep copy to avoid modifying the original
    processed_schema = schema.copy()

    # Special handling for schemas where root is just a $ref to self
    if "$ref" in processed_schema:
        ref_value = processed_schema["$ref"]
        # Check if this is a self-reference (including Pydantic's unique identifiers)
        if ref_value.startswith("#/$defs/") and model_name in ref_value:
            # Find the actual definition key (might be model_name or a variant with __1, __2, etc.)
            actual_def_key = None
            if "$defs" in processed_schema:
                for def_key in processed_schema["$defs"]:
                    if def_key == model_name or (model_name in def_key and "__" in def_key):
                        actual_def_key = def_key
                        break

            if actual_def_key and actual_def_key in processed_schema["$defs"]:
                # Get the definition
                model_def = processed_schema["$defs"][actual_def_key]
                # Replace root with the expanded definition
                processed_schema = model_def.copy()
                # Keep the self-definition in $defs for internal references
                processed_schema["$defs"] = {model_name: model_def}
                activity.logger.info(f"Expanded root self-reference for {model_name} (was {actual_def_key})")

    # Now process all references in the schema
    processed_schema = process_refs(processed_schema)

    # Process $defs to convert external references but keep self-references
    if "$defs" in processed_schema:
        # Process references within each definition
        for def_name, def_schema in processed_schema["$defs"].items():
            processed_schema["$defs"][def_name] = process_refs(def_schema)

        # Keep only the self-referential definition and remove external model definitions
        # that should be referenced from their own files
        filtered_defs = {
            def_name: def_schema for def_name, def_schema in processed_schema["$defs"].items() if def_name == model_name
        }

        if filtered_defs:
            processed_schema["$defs"] = filtered_defs
            activity.logger.info(f"Kept $defs section for self-referential model: {model_name}")
        else:
            # No self-definitions needed, remove $defs
            del processed_schema["$defs"]

    return processed_schema


def _generate_schemas(models: dict[str, Any], output_dir: Path) -> list[str]:
    """Generate JSON schemas for all discovered models."""
    activity.logger.info("Generating JSON schemas...")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for model_name, model_class in models.items():
        try:
            # Check if this is an enum class
            is_enum = hasattr(model_class, "__bases__") and any(
                base.__name__ in ("Enum", "StrEnum", "IntEnum")
                or (hasattr(base, "__bases__") and any(b.__name__ == "Enum" for b in base.__bases__))
                for base in model_class.__bases__
            )

            if is_enum:
                # Generate schema for enum
                schema = _generate_enum_schema(model_class)
                activity.logger.info(f"Generated enum schema for {model_name}")
            else:
                # Generate JSON schema with mode='serialization'
                schema = model_class.model_json_schema(mode="serialization")

                # Debug logging
                activity.logger.info(f"Generated schema for {model_name}, root keys: {list(schema.keys())}")
                if "$ref" in schema:
                    activity.logger.info(f"  Root $ref: {schema['$ref']}")

                # Check if this model has self-references
                if _has_self_references(schema, model_name):
                    activity.logger.info(f"Processing self-referential model: {model_name}")
                    schema = _process_self_referential_schema(schema, model_name)
                    activity.logger.info(f"  After processing, root keys: {list(schema.keys())}")
                else:
                    # For non-self-referential models, remove $defs and convert refs
                    activity.logger.info(f"Processing non-self-referential model: {model_name}")
                    if "$defs" in schema:
                        activity.logger.info(f"Removing embedded definitions from {model_name} schema")
                        del schema["$defs"]

                    # Convert any internal references to external references
                    schema = _convert_internal_refs_to_external(schema)

            # Write to file
            schema_file = output_dir / f"{model_name}.json"
            with schema_file.open("w") as f:
                json.dump(schema, f, indent=2)

            activity.logger.info(f"Generated schema for {model_name} → {schema_file}")
            generated_files.append(str(schema_file))

        except (OSError, TypeError, ValueError) as e:
            activity.logger.error(f"Failed to generate schema for {model_name}: {e}")
            continue

    return generated_files


def _convert_internal_refs_to_external(schema: dict[str, Any], current_model: str | None = None) -> dict[str, Any]:
    """Convert internal $ref references to external file references.

    Args:
        schema: The JSON schema to process
        current_model: Optional name of the current model to skip self-references

    Returns:
        Processed schema with external references

    """

    def process_value(value):  # noqa: ANN001, ANN202
        if isinstance(value, dict):
            if "$ref" in value and value["$ref"].startswith("#/$defs/"):
                # Convert internal reference to external file reference
                ref_model = value["$ref"].replace("#/$defs/", "")
                # Skip if this is a self-reference and current_model is provided
                if current_model and ref_model == current_model:
                    activity.logger.info(f"Skipping self-reference conversion for: {ref_model}")
                else:
                    value["$ref"] = f"./{ref_model}.json"
                    activity.logger.info(f"Converting internal reference to external: ./{ref_model}.json")
            else:
                # Recursively process nested dictionaries
                for k, v in value.items():
                    value[k] = process_value(v)
        elif isinstance(value, list):
            # Process list items
            for i, item in enumerate(value):
                value[i] = process_value(item)
        return value

    return process_value(schema)


def _generate_enum_schema(enum_class: type[Enum]) -> dict[str, Any]:
    """Generate JSON schema for an enum class."""
    # Get all enum values
    enum_values = [member.value for member in enum_class]

    # Determine the type based on the first value
    if enum_values:
        first_value = enum_values[0]
        if isinstance(first_value, str):
            schema_type = "string"
        elif isinstance(first_value, int):
            schema_type = "integer"
        elif isinstance(first_value, float):
            schema_type = "number"
        else:
            schema_type = "string"  # Default fallback
    else:
        schema_type = "string"  # Default for empty enums

    return {
        "type": schema_type,
        "enum": enum_values,
        "title": enum_class.__name__,
    }
