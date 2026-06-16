"""Cross-platform config path utilities for AWA global configuration."""

from pathlib import Path


class ConfigPaths:
    """Utility class for managing AWA configuration paths across platforms."""

    @staticmethod
    def get_global_config_dir() -> Path:
        """Get platform-specific global AWA config directory.

        Returns:
            Path: Platform-appropriate global config directory (~/.awa/)

        """
        return Path.home() / ".awa"

    @staticmethod
    def get_config_file_paths() -> dict[str, list[Path]]:
        """Get ordered list of config file paths by precedence.

        Returns:
            dict: Config file paths ordered by precedence (highest to lowest)
                 - env_files: .env file locations
                 - yaml_files: config.yaml file locations

        """
        global_dir = ConfigPaths.get_global_config_dir()

        return {
            "env_files": [
                Path.cwd() / ".env",  # 1. Current directory (highest)
                global_dir / ".env",  # 2. Global config directory
            ],
            "yaml_files": [
                Path.cwd() / "config.yaml",  # 1. Current directory (highest)
                global_dir / "config.yaml",  # 2. Global config directory
            ],
        }

    @staticmethod
    def get_global_state_file() -> Path:
        """Get the global state file path.

        Returns:
            Path: Global state file location (~/.awa/services.json)

        """
        return ConfigPaths.get_global_config_dir() / "services.json"
