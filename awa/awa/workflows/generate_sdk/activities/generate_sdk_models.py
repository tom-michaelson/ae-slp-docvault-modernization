from pathlib import Path

from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.utils.command_utils import CommandUtils
from awa.sdk.models.exceptions.fatal_application_error import FatalApplicationError
from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError
from awa.workflows.generate_sdk import constants
from awa.workflows.generate_sdk.models.generate_sdk_models_input import GenerateSdkModelsInput
from awa.workflows.generate_sdk.models.sdk_config import SdkLanguageConfig

logger = get_logger(LoggerComponent.ACTIVITY)


@activity.defn(name=constants.ACTIVITY_GENERATE_SDK_MODELS)
async def generate_sdk_models_activity(workflow_input: GenerateSdkModelsInput) -> list[str]:
    """Generate SDK models from JSON schemas using quicktype.

    Args:
        workflow_input: Input containing schemas path, target language, and output path

    Returns:
        List of generated file paths

    Raises:
        Exception: If quicktype is not available or generation fails

    """
    activity.logger.info(f"Starting SDK model generation for language: {workflow_input.language_config.name}")

    # Convert paths to Path objects
    schemas_path = Path(workflow_input.json_schemas_path)
    output_path = Path(workflow_input.output_path)

    # Validate input paths
    if not schemas_path.exists():
        raise InvalidInputApplicationError(f"JSON schemas directory not found: {schemas_path}")

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    activity.heartbeat("Created output directory")

    # Discover JSON schema files
    schema_files = _discover_schema_files(schemas_path)
    if not schema_files:
        activity.logger.warning("No JSON schema files found")
        return []

    activity.logger.info(f"Found {len(schema_files)} schema files")
    activity.heartbeat(f"Discovered {len(schema_files)} schema files")

    # Generate models for the specified language
    generated_files = await _generate_models_for_language(
        workflow_input.language_config,
        schema_files,
        output_path,
    )

    activity.logger.info(f"Successfully generated {len(generated_files)} model files")
    return generated_files


def _discover_schema_files(schemas_dir: Path) -> list[Path]:
    """Discover all JSON schema files in the given directory.

    Args:
        schemas_dir: Directory to search for schema files

    Returns:
        List of schema file paths

    """
    schema_files = list(schemas_dir.glob("*.json"))

    for schema_file in schema_files:
        logger.info(f"Found schema: {schema_file.name}")

    return schema_files


async def _generate_models_for_language(
    language_config: SdkLanguageConfig,
    schema_files: list[Path],
    output_dir: Path,
) -> list[str]:
    """Generate models for a specific language using quicktype.

    Args:
        language_config: Target language config for code generation
        schema_files: List of JSON schema files to process
        output_dir: Directory where generated models will be saved

    Returns:
        List of generated file paths

    Raises:
        FatalApplicationError: If model generation fails

    """
    activity.logger.info(f"Generating {language_config.name} models...")

    # Generate all models in a single quicktype command to handle cross-references
    output_file = (
        output_dir
        / language_config.name
        / language_config.model_path
        / f"{language_config.model_file_name}{language_config.ext}"
    )

    if not output_file.parent.exists():
        output_file.parent.mkdir(parents=True, exist_ok=True)

    # Build quicktype command
    cmd_parts = [
        "npx",
        "quicktype",
        "--lang",
        language_config.name,
        "--src-lang",
        "schema",  # Specify that input is JSON Schema
    ]

    # Add all schema files as sources
    for schema_file in schema_files:
        cmd_parts.extend(["--src", str(schema_file)])

    # Set output file
    cmd_parts.extend(["--out", str(output_file)])

    # Add language-specific options
    if language_config.namespace:
        cmd_parts.extend(["--namespace", language_config.namespace])
    if language_config.package:
        cmd_parts.extend(["--package", language_config.package])

    # Join command parts for execution
    command = " ".join(cmd_parts)
    activity.heartbeat(f"Executing quicktype for {language_config.name}: {command}")

    # Run quicktype command
    success, output = await CommandUtils.run_command_async(command)

    if not success:
        raise FatalApplicationError(f"Failed to generate {language_config.name} models: {output}")

    # Verify output file was created
    if not output_file.exists():
        raise FatalApplicationError(f"Expected output file was not created: {output_file}")

    activity.logger.info(f"Generated {language_config.name} models: {output_file}")
    activity.heartbeat(f"Completed {language_config.name} model generation")

    return [str(output_file)]
