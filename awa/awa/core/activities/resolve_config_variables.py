import json
import os
import re

from temporalio import activity

from awa.sdk import constants as sdk_constants

# Type alias for JSON-like data structures
ConfigObject = dict[str, "ConfigObject"] | list["ConfigObject"] | str | int | float | bool | None

# Constants
LOG_PREVIEW_LENGTH = 500  # Maximum length for logging preview


def _resolve_recursive(obj: ConfigObject) -> ConfigObject:
    """Recursively resolve environment variables in the given configuration object."""
    if isinstance(obj, dict):
        return {k: _resolve_recursive(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_recursive(v) for v in obj]
    if isinstance(obj, str):
        # Use built-in os.expandvars to handle both $VAR and ${VAR} patterns
        expanded = os.path.expandvars(obj)

        # Check if any ${VAR} patterns remain unresolved
        env_placeholder_pattern = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
        missing = env_placeholder_pattern.findall(expanded)
        if missing:
            missing_vars = sorted(set(missing))
            activity.logger.error(f"Missing environment variables: {missing_vars}")
            raise ValueError(f"Required environment variables not set: {', '.join(missing_vars)}")

        return expanded

    return obj


@activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_CONFIG_VARIABLES)
async def resolve_config_variables_activity(config_json_str: str) -> str:
    """Recursively resolve configuration variables and environment placeholders in JSON configuration.

    Handles ${VAR_NAME} and $VAR patterns in strings within nested dicts/lists.
    Raises an error if any required environment variables are not found.

    Args:
        config_json_str: JSON string containing the configuration to process.

    Returns:
        JSON string with environment variable placeholders expanded.

    Raises:
        ValueError: If required environment variables are not set or JSON is invalid.

    """
    try:
        # Parse the JSON string into an object
        config_obj = json.loads(config_json_str)

        # Process the object
        resolved_obj = _resolve_recursive(config_obj)

        # Convert back to JSON string
        resolved_json_str = json.dumps(resolved_obj)

        return resolved_json_str

    except json.JSONDecodeError as e:
        activity.logger.error(f"Invalid JSON input: {e}")
        raise ValueError(f"Invalid JSON configuration: {e}") from e
    except Exception as e:
        activity.logger.error(f"resolve_config_variables_activity failed with error: {e}")
        raise
