from pathlib import Path

import yaml

from awa.core.models.config.app_config import AppConfig
from awa.core.utils.config_paths import ConfigPaths


class ConfigLoader:
    """Utility class for loading application configuration from YAML files."""

    _config: AppConfig = None

    @classmethod
    def load_config_with_hierarchy(cls) -> None:
        """Load configuration with hierarchical precedence.

        Precedence order: CLI args > local config > global config > defaults

        Raises:
            yaml.YAMLError: If any YAML file is malformed.
            ValueError: If the configuration doesn't match the expected schema.

        """
        config_paths = ConfigPaths.get_config_file_paths()

        # Start with empty config data
        merged_config = {}

        # Load config files in reverse order (lowest to highest precedence)
        for yaml_path in reversed(config_paths["yaml_files"]):
            if yaml_path.exists():
                try:
                    with Path.open(yaml_path, encoding="utf-8") as file:
                        config_data = yaml.safe_load(file)

                    if config_data:
                        # Merge config data with higher precedence overriding lower
                        merged_config = cls._deep_merge_configs(merged_config, config_data)

                except yaml.YAMLError as e:
                    raise yaml.YAMLError(f"Error parsing YAML file {yaml_path}: {e}") from e

        # If no config files found, use empty config (will use defaults)
        if not merged_config:
            merged_config = {}

        try:
            cls._config = AppConfig(**merged_config)
        except Exception as e:
            raise ValueError(f"Invalid configuration schema: {e}") from e

    @classmethod
    def _deep_merge_configs(cls, base: dict, override: dict) -> dict:
        """Deep merge two configuration dictionaries.

        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary

        Returns:
            dict: Merged configuration with override values taking precedence

        """
        merged = base.copy()

        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = cls._deep_merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    @classmethod
    def load_config(cls, config_path: str | Path | None = None) -> None:
        """Load the application configuration from a YAML file.

        Args:
            config_path: Optional path to the config file. If not provided,
                        uses hierarchical loading.

        Raises:
            FileNotFoundError: If the config file doesn't exist.
            yaml.YAMLError: If the YAML file is malformed.
            ValueError: If the configuration doesn't match the expected schema.

        """
        if config_path is None:
            # Use hierarchical loading
            cls.load_config_with_hierarchy()
            return

        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with Path.open(config_path, encoding="utf-8") as file:
                config_data = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML file {config_path}: {e}") from e

        try:
            cls._config = AppConfig(**config_data)
        except Exception as e:
            raise ValueError(f"Invalid configuration schema: {e}") from e

    @classmethod
    def get_default_config(cls) -> AppConfig:
        """Load the default config using hierarchical loading.

        Returns:
            AppConfig: The loaded configuration.

        """
        cls.load_config()
        return cls._config

    @classmethod
    def get_config(cls) -> AppConfig:
        """Load the pre-loaded config.yaml file from the config_path, or the default if not loaded prior.

        Returns:
            AppConfig: The loaded configuration.

        """
        if cls._config is None:
            return cls.get_default_config()
        return cls._config
