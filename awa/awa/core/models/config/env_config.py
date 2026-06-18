import os
from pathlib import Path

from loguru import logger  # Use loguru logger
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from awa.core.utils.config_paths import ConfigPaths


class Settings(BaseSettings):
    config_path: Path = Field(default=Path("config.yaml"))

    # AWA Service Configuration
    awa_ui_host: str = Field(default="localhost")
    awa_ui_port: int = Field(default=8000)
    awa_api_host: str = Field(default="localhost")
    awa_api_port: int = Field(default=8001)

    # Temporal Service Configuration
    temporal_ui_host: str = Field(default="localhost")
    temporal_ui_port: int = Field(default=8002)
    temporal_server_host: str = Field(default="localhost")
    temporal_server_port: int = Field(default=7233)
    temporal_metrics_port: int = Field(default=8004)
    temporal_namespace: str = Field(default="default")

    # Temporal Version Configuration
    temporal_version: str = Field(default="1.27.2")
    temporal_admintools_version: str = Field(default="1.27.2-tctl-1.18.2-cli-1.3.0")
    temporal_ui_version: str = Field(default="2.34.0")

    # PostgreSQL Configuration
    postgresql_version: str = Field(default="16")
    postgres_password: str = Field(default="temporal")
    postgres_user: str = Field(default="temporal")
    postgres_default_port: int = Field(default=5432)

    # LLM API Keys
    openai_api_key: str = Field(default="")
    azure_openai_api_key: str = Field(default="")
    google_application_credentials: str = Field(default="")
    lite_llm_api_key: str = Field(default="")
    github_copilot_api_key: str = Field(default="", description="GitHub Copilot API Key. Device flow is preferred.")
    anthropic_api_key: str = Field(default="")

    # Other service API keys
    jira_api_key: str = Field(default="")

    # Authentication Configuration
    public_auth_mode: str = Field(default="none")  # Options: "none", "cognito"
    auth_cognito_client_id: str = Field(default="")
    auth_cognito_client_secret: str = Field(default="")
    auth_cognito_issuer: str = Field(default="")
    auth_secret: str = Field(default="")  # Auth.js secret
    awa_service_token: str = Field(default="")  # Service-to-service authentication token

    # Cache and Debug Configuration
    pythonpycacheprefix: str | None = Field(default=".cache/pycache")
    llm_cache_path: str = Field(default="./.cache/llm")
    debug_mode: bool = Field(default=True)

    # Logging Configuration
    log_level: str = Field(default="DEBUG")
    log_path: str = Field(default="logs")
    log_file_rotation_size: str = Field(default="1 MB")
    log_enable_json: bool = Field(default=False)
    log_workflow_dir: str = Field(default="logs/workflows")
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

        # Create settings with hierarchical .env file loading
        return cls(_env_file=env_files)


class EnvConfig:
    _env_config: Settings = None

    @classmethod
    def set_env_config(cls, file_path: str | None = None) -> None:
        """Set config with optional explicit file path or hierarchical loading.

        Args:
            file_path: Optional explicit .env file path. If None, uses hierarchical loading.

        """
        try:
            if file_path:
                cls._env_config = Settings(_env_file=file_path)
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
        return cls._env_config

    @classmethod
    def get_env_config_value(cls, key: str) -> str | None:
        if cls._env_config is None:
            cls.set_env_config()
        return os.environ.get(key)
