"""Log configuration utilities for AWA."""

import logging
from pathlib import Path
from typing import Any

from loguru import logger

from awa.core.models.config.env_config import EnvConfig
from awa.core.models.config.log_config import LogConfig
from awa.core.utils.config_loader import ConfigLoader


def get_log_config() -> LogConfig:
    """Get log configuration from config.yaml or defaults.

    Returns:
        LogConfig instance with logging settings

    """
    try:
        # First check if config is already loaded
        app_config = ConfigLoader.get_config()
        if app_config:
            return app_config.logging
    except Exception:  # noqa: BLE001, S110
        # Config not loaded yet, try to load it
        pass

    try:
        # Try to load from config.yaml
        config_path = Path(EnvConfig.get_env_config().config_path)
        if config_path.exists():
            ConfigLoader.load_config(config_path)
            app_config = ConfigLoader.get_config()
            return app_config.logging
    except Exception:  # noqa: BLE001, S110
        # If config loading fails, return defaults
        # This is expected when config file doesn't exist
        pass

    return LogConfig()


def get_log_level_for_component(component: str) -> str:
    """Get the log level for a specific component.

    Args:
        component: Component name (e.g., 'API', 'UI', 'WORKER')

    Returns:
        Log level string (e.g., 'DEBUG', 'INFO', 'WARNING')

    """
    # First check environment variable (highest priority)
    env_log_level = EnvConfig.get_env_config().log_level

    # Then check config.yaml
    log_config = get_log_config()
    config_log_level = log_config.get_component_log_level(component)

    # Environment variable takes precedence
    if env_log_level != "DEBUG":  # DEBUG is the default, so check if it was explicitly set
        import os

        if "LOG_LEVEL" in os.environ:
            return env_log_level

    return config_log_level


def get_python_log_level(level_str: str) -> int:
    """Convert string log level to Python logging constant.

    Args:
        level_str: Log level string (e.g., 'DEBUG', 'INFO')

    Returns:
        Python logging level constant

    """
    return getattr(logging, level_str.upper(), logging.INFO)


def create_component_level_filter(log_config: LogConfig | None = None) -> dict[str, str | int] | Any:  # noqa: ANN401
    """Create a Loguru filter for component-specific log levels.

    This creates a filter that can be used with logger.add() to control
    log levels on a per-component basis.

    Args:
        log_config: Log configuration object. If None, will load from config.

    Returns:
        A filter function or dictionary for use with Loguru's logger.add()

    """
    if log_config is None:
        log_config = get_log_config()

    # If using a single log level for all components, return it directly
    if isinstance(log_config.log_level, str):
        return log_config.log_level

    # Build a filter function that checks component and applies appropriate level
    component_levels = log_config.log_level

    def component_filter(record: dict[str, Any]) -> bool:
        """Filter log records based on component-specific levels."""
        # Get the component from the record
        component = record["extra"].get("component", "AWA")

        # Extract the component type (e.g., "AWA-API" -> "api")
        component_key = component.replace("AWA-", "").lower()

        # Handle special cases for component mapping
        if component_key == "engine":
            component_key = "server"  # Map engine to server level
        elif component_key == "socketio-server":
            component_key = "socketio"  # Map SOCKETIO-SERVER to socketio config
        elif component_key == "socketio-client":
            component_key = "socketio"  # Map SOCKETIO-CLIENT to socketio config

        # Get the configured level for this component
        if hasattr(component_levels, component_key):
            configured_level = getattr(component_levels, component_key).upper()
        else:
            configured_level = "INFO"  # Default level

        # Get the numeric level values for comparison
        try:
            configured_level_no = logger.level(configured_level).no
            record_level_no = record["level"].no

            # Include the record if its level is >= configured level
            return record_level_no >= configured_level_no
        except ValueError:
            # If level is not recognized, default to including the record
            return True

    return component_filter
