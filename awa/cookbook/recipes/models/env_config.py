import os
from pathlib import Path

from loguru import logger
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from cookbook.recipes.utilities.config_paths import ConfigPaths


class Settings(BaseSettings):
    config_path: Path = Field(default=Path("config.yaml"))

    # Logging Configuration
    log_level: str = Field(default="INFO")
    log_level_http: str = Field(default="INFO")
    log_path: str = Field(default="logs")
    log_file_rotation_size: str = Field(default="1 MB")
    log_enable_json: bool = Field(default=False)
    log_console_enabled: bool = Field(default=True)
    log_file_enabled: bool = Field(default=True)

    model_config = SettingsConfigDict(env_file=[], extra="allow")  # Will be populated dynamically

    @classmethod
    def load_with_hierarchy(cls) -> "Settings":
        """Load settings with hierarchical config precedence.

        Precedence order: CLI args > local config > global config > defaults

        Returns:
            Settings: Configured settings instance with proper hierarchy

        """
        config_paths = ConfigPaths.get_config_file_paths()

        # Load .env files in reverse order (lowest to highest precedence)
        env_files = [str(env_path) for env_path in reversed(config_paths["env_files"]) if env_path.exists()]
        cls.model_config = SettingsConfigDict(env_file=env_files, extra="allow")

        # Create settings with hierarchical .env file loading
        return cls()


class EnvConfig:
    _env_config: Settings | None = None

    @classmethod
    def set_env_config(cls, file_path: str | None = None) -> None:
        """Set config with optional explicit file path or hierarchical loading.

        Args:
            file_path: Optional explicit .env file path. If None, uses hierarchical loading.

        """
        try:
            if file_path:
                # Note: For explicit file paths, we'd need to set environment variables manually
                # or use a different approach as BaseSettings doesn't accept _env_file parameter
                cls._env_config = Settings()
            else:
                cls._env_config = Settings.load_with_hierarchy()
        except ValidationError as e:
            logger.error(f"EnvConfig validation error: {e}", exc_info=True)
            raise

    @classmethod
    def update_env_config(cls, file_path: str) -> None:
        """Update config with explicit file path."""
        cls.set_env_config(file_path)

    @classmethod
    def get_env_config(cls) -> Settings:
        if cls._env_config is None:
            cls.set_env_config()
        if cls._env_config is None:
            raise RuntimeError("EnvConfig could not be initialized and is None.")
        return cls._env_config

    @classmethod
    def get_env_config_value(cls, key: str) -> str | None:
        if cls._env_config is None:
            cls.set_env_config()
        return os.environ.get(key)
