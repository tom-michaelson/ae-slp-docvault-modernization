"""MCP configuration loader with VSCode variable substitution support.

This module provides utilities to load and parse MCP configuration files from
.vscode/mcp.json or mcp.json with support for VSCode-style variable substitution,
environment file loading, and configuration validation.
"""

import hashlib
import json
import os
import re
from pathlib import Path
from re import Match
from typing import Any, ClassVar

from awa.core.models.config.mcp_json_config import MCPJsonConfig, MCPServerConfig


class MCPConfigLoader:
    """Loader for MCP configuration files with VSCode variable substitution."""

    _config_cache: ClassVar[dict[str, MCPJsonConfig]] = {}
    _config_hash_cache: ClassVar[dict[str, str]] = {}

    @classmethod
    def load_mcp_config(
        cls,
        working_dir: Path | None = None,
        inputs: dict[str, str] | None = None,
    ) -> MCPJsonConfig | None:
        """Load MCP configuration with priority: .vscode/mcp.json > mcp.json.

        Args:
            working_dir: Directory to search for config files. Defaults to current working directory.
            inputs: Dictionary of input values for ${input:id} substitutions.

        Returns:
            MCPJsonConfig instance if configuration found and valid, None otherwise.

        Raises:
            ValueError: If configuration file is malformed or invalid.
            FileNotFoundError: If referenced envFile doesn't exist.

        """
        if working_dir is None:
            working_dir = Path.cwd()

        # Define potential config paths in priority order
        config_paths = [
            working_dir / "mcp.json",
            working_dir / ".mcp.json",
        ]

        config_path = None
        for path in config_paths:
            if path.exists():
                config_path = path
                break

        if config_path is None:
            return None

        # Generate cache key based on file path and modification time
        cache_key = f"{config_path}:{config_path.stat().st_mtime}"

        # Check if we have a cached version
        current_hash = cls._hash_string(cache_key)
        if cache_key in cls._config_cache and cls._config_hash_cache.get(cache_key) == current_hash:
            return cls._config_cache[cache_key]

        try:
            with config_path.open(encoding="utf-8") as file:
                config_data = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {config_path}: {e}") from e

        # Substitute variables in the configuration
        config_data = cls._substitute_variables(
            config_data,
            working_dir=working_dir,
            inputs=inputs or {},
        )

        # Process envFile references and load environment variables
        cls._process_env_files(config_data, working_dir)

        # Validate and create the configuration object
        try:
            config = MCPJsonConfig(**config_data)
        except Exception as e:
            raise ValueError(f"Invalid MCP configuration in {config_path}: {e}") from e

        # Validate individual server configurations
        for server_name, server_config in config.servers.items():
            cls._validate_server_config(server_name, server_config)

        # Cache the validated configuration
        cls._config_cache[cache_key] = config
        cls._config_hash_cache[cache_key] = current_hash

        return config

    @classmethod
    def _substitute_variables(
        cls,
        data: dict | list | str | float | bool | None,
        working_dir: Path,
        inputs: dict[str, str],
    ) -> dict | list | str | int | float | bool | None:
        """Handle VSCode variable substitution in configuration data.

        Supports:
        - ${input:id} - replace with value from inputs
        - ${workspaceFolder} - replace with working directory
        - ${env:VAR_NAME} - replace with environment variable

        Args:
            data: Configuration data to process (dict, list, or string).
            working_dir: Current working directory for ${workspaceFolder} substitution.
            inputs: Dictionary of input values for ${input:id} substitutions.

        Returns:
            Configuration data with variables substituted.

        Raises:
            ValueError: If variable substitution fails or required variables are missing.

        """
        if isinstance(data, dict):
            return {key: cls._substitute_variables(value, working_dir, inputs) for key, value in data.items()}
        if isinstance(data, list):
            return [cls._substitute_variables(item, working_dir, inputs) for item in data]
        if isinstance(data, str):
            return cls._substitute_string_variables(data, working_dir, inputs)
        return data

    @classmethod
    def _substitute_string_variables(
        cls,
        text: str,
        working_dir: Path,
        inputs: dict[str, str],
    ) -> str:
        """Substitute variables in a string value.

        Args:
            text: String containing variable references.
            working_dir: Current working directory.
            inputs: Dictionary of input values.

        Returns:
            String with variables substituted.

        Raises:
            ValueError: If variable substitution fails.

        """
        # Pattern to match ${variable:value} or ${variable}
        pattern = r"\$\{([^}]+)\}"

        def replace_variable(match: Match[str]) -> str:
            variable = match.group(1)

            # Handle input variables: ${input:id}
            if variable.startswith("input:"):
                input_id = variable[6:]  # Remove "input:" prefix
                if input_id not in inputs:
                    raise ValueError(f"Missing input value for '${{{variable}}}'")
                return inputs[input_id]

            # Handle workspace folder: ${workspaceFolder}
            if variable == "workspaceFolder":
                return str(working_dir)

            # Handle environment variables: ${env:VAR_NAME}
            if variable.startswith("env:"):
                env_var = variable[4:]  # Remove "env:" prefix
                env_value = os.getenv(env_var)
                if env_value is None:
                    raise ValueError(f"Environment variable '{env_var}' not found for '${{{variable}}}'")
                return env_value

            raise ValueError(f"Unsupported variable type: '${{{variable}}}'")

        try:
            return re.sub(pattern, replace_variable, text)
        except Exception as e:
            raise ValueError(f"Error substituting variables in '{text}': {e}") from e

    @classmethod
    def _process_env_files(cls, config_data: dict[str, Any], working_dir: Path) -> None:
        """Process envFile references and load environment variables.

        Args:
            config_data: Configuration data to process in-place.
            working_dir: Working directory for resolving relative paths.

        Raises:
            FileNotFoundError: If referenced envFile doesn't exist.

        """
        if "servers" not in config_data:
            return

        for server_config in config_data["servers"].values():
            if not isinstance(server_config, dict):
                continue

            env_file_path = server_config.get("envFile")
            if env_file_path:
                env_file = Path(env_file_path)

                # Resolve relative paths relative to working directory
                if not env_file.is_absolute():
                    env_file = working_dir / env_file

                if not env_file.exists():
                    raise FileNotFoundError(f"Environment file not found: {env_file}")

                # Load environment variables from file
                env_vars = cls._load_env_file(env_file)

                # Merge with existing env variables (existing ones take precedence)
                if "env" in server_config:
                    env_vars.update(server_config["env"])

                server_config["env"] = env_vars

    @classmethod
    def _load_env_file(cls, env_file_path: Path) -> dict[str, str]:
        """Load environment variables from a .env file.

        Args:
            env_file_path: Path to the environment file.

        Returns:
            Dictionary of environment variables.

        Raises:
            ValueError: If the environment file is malformed.

        """
        env_vars = {}

        try:
            with env_file_path.open(encoding="utf-8") as file:
                for line_num, raw_line in enumerate(file, 1):
                    line = raw_line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE format
                    if "=" not in line:
                        cls._raise_invalid_format_error(line_num, line)

                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or (
                        value.startswith("'") and value.endswith("'")
                    ):
                        value = value[1:-1]

                    env_vars[key] = value

        except Exception as e:
            raise ValueError(f"Error reading environment file {env_file_path}: {e}") from e

        return env_vars

    @classmethod
    def _hash_string(cls, value: str) -> str:
        """Generate a SHA-256 hash of a string.

        Args:
            value: String to hash.

        Returns:
            Hexadecimal representation of the hash.

        """
        return hashlib.sha256(value.encode()).hexdigest()

    @classmethod
    def _raise_invalid_format_error(cls, line_num: int, line: str) -> None:
        """Raise a ValueError for invalid env file format.

        Args:
            line_num: Line number where the error occurred.
            line: The problematic line content.

        Raises:
            ValueError: Always raises with formatted error message.

        """
        raise ValueError(f"Invalid format on line {line_num}: {line}")

    @classmethod
    def _validate_server_config(cls, server_name: str, server_config: MCPServerConfig) -> None:
        """Validate server configuration based on transport type.

        Args:
            server_name: Name of the server for error reporting.
            server_config: Server configuration object to validate.

        Raises:
            ValueError: If server configuration is invalid for its transport type.

        """
        # The MCPServerConfig model already handles validation through Pydantic validators,
        # but we can add additional checks here if needed

        transport_type = server_config.type

        if transport_type == "stdio":
            if not server_config.command:
                raise ValueError(f"Server '{server_name}': stdio transport requires a command")

        elif transport_type in ["http", "sse"]:
            if not server_config.url:
                raise ValueError(f"Server '{server_name}': {transport_type} transport requires a url")

        else:
            raise ValueError(f"Server '{server_name}': unsupported transport type '{transport_type}'")

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the configuration cache.

        This is useful for testing or when configuration files have been modified
        externally and you want to force a reload.
        """
        cls._config_cache.clear()
        cls._config_hash_cache.clear()
