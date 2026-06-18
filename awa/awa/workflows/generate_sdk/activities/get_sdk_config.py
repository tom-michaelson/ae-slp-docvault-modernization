"""SDK configuration activity for loading and parsing SDK config files."""

from pathlib import Path

import yaml
from temporalio import activity

from awa.core.utils.file_system_utils import FileSystemUtils
from awa.workflows.generate_sdk import constants
from awa.workflows.generate_sdk.models.sdk_config import SdkConfig


@activity.defn(name=constants.ACTIVITY_GET_SDK_CONFIG)
async def get_sdk_config_activity(config_path: str | None = None) -> SdkConfig:
    """Load SDK configuration from a YAML file.

    Args:
        config_path: Optional path to the SDK config file. If None or empty,
                    defaults to 'awa/sdk/sdk.config.yaml'.

    Returns:
        SdkConfig: The parsed SDK configuration.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        yaml.YAMLError: If the YAML file is malformed.
        ValueError: If the configuration doesn't match the expected schema.

    """
    # Use default fallback if config_path is None or empty
    if not config_path:
        config_path = "awa/sdk/sdk.config.yaml"

    config_file_path = Path(config_path)

    if not config_file_path.exists():
        raise FileNotFoundError(f"SDK config file not found: {config_path}")

    try:
        config_content = await FileSystemUtils.read_async(config_file_path)
        config_data = yaml.safe_load(config_content)
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}") from e

    try:
        return SdkConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid SDK configuration schema: {e}") from e
