"""MCP Server Resolution Utility for resolving server configurations by name.

This module provides utilities to resolve MCP server configurations by name from
VSCode MCP JSON configuration files, with validation and caching for performance.
"""

from pathlib import Path
from typing import ClassVar

from awa.core.models.config.mcp_json_config import MCPJsonConfig, MCPServerConfig
from awa.core.utils.mcp_config_loader import MCPConfigLoader


class MCPServerResolver:
    """Resolver for MCP server configurations with caching and validation."""

    _resolved_config_cache: ClassVar[MCPJsonConfig | None] = None

    @classmethod
    def resolve_mcp_servers(
        cls,
        server_names: list[str],
        working_dir: Path | None = None,
        inputs: dict[str, str] | None = None,
    ) -> dict[str, MCPServerConfig]:
        """Resolve multiple MCP server configurations by name.

        Args:
            server_names: List of server names to resolve.
            working_dir: Directory to search for config files. Defaults to current working directory.
            inputs: Dictionary of input values for ${input:id} substitutions.

        Returns:
            Dictionary mapping server names to their configurations.

        Raises:
            ValueError: If any requested servers don't exist or configuration is invalid.
            FileNotFoundError: If no MCP configuration file is found.

        """
        # Validate server names first
        cls.validate_server_names(server_names, working_dir, inputs)

        config = cls._get_config(working_dir, inputs)
        if config is None:
            raise FileNotFoundError("No MCP configuration file found")

        # Return resolved server configurations
        return {name: config.servers[name] for name in server_names}

    @classmethod
    def resolve_mcp_server(
        cls,
        server_name: str,
        working_dir: Path | None = None,
        inputs: dict[str, str] | None = None,
    ) -> MCPServerConfig:
        """Resolve a single MCP server configuration by name.

        Args:
            server_name: Name of the server to resolve.
            working_dir: Directory to search for config files. Defaults to current working directory.
            inputs: Dictionary of input values for ${input:id} substitutions.

        Returns:
            Server configuration for the requested server.

        Raises:
            ValueError: If the requested server doesn't exist or configuration is invalid.
            FileNotFoundError: If no MCP configuration file is found.

        """
        servers = cls.resolve_mcp_servers([server_name], working_dir, inputs)
        return servers[server_name]

    @classmethod
    def validate_server_names(
        cls,
        server_names: list[str],
        working_dir: Path | None = None,
        inputs: dict[str, str] | None = None,
    ) -> None:
        """Validate that all requested server names exist in the configuration.

        Args:
            server_names: List of server names to validate.
            working_dir: Directory to search for config files. Defaults to current working directory.
            inputs: Dictionary of input values for ${input:id} substitutions.

        Raises:
            ValueError: If any requested servers don't exist or if server_names is empty.
            FileNotFoundError: If no MCP configuration file is found.

        """
        if not server_names:
            raise ValueError("Server names list cannot be empty")

        config = cls._get_config(working_dir, inputs)
        if config is None:
            raise FileNotFoundError("No MCP configuration file found")

        available_servers = set(config.servers.keys())
        missing_servers = set(server_names) - available_servers

        if missing_servers:
            missing_list = ", ".join(f"'{name}'" for name in sorted(missing_servers))
            available_list = ", ".join(f"'{name}'" for name in sorted(available_servers))
            raise ValueError(
                f"The following servers are not configured: {missing_list}. Available servers: {available_list}",
            )

    @classmethod
    def get_available_servers(
        cls,
        working_dir: Path | None = None,
        inputs: dict[str, str] | None = None,
    ) -> list[str]:
        """Get list of available server names from the configuration.

        Args:
            working_dir: Directory to search for config files. Defaults to current working directory.
            inputs: Dictionary of input values for ${input:id} substitutions.

        Returns:
            List of available server names, sorted alphabetically.

        Raises:
            FileNotFoundError: If no MCP configuration file is found.

        """
        config = cls._get_config(working_dir, inputs)
        if config is None:
            raise FileNotFoundError("No MCP configuration file found")

        return sorted(config.servers.keys())

    @classmethod
    def _get_config(
        cls,
        working_dir: Path | None = None,
        inputs: dict[str, str] | None = None,
    ) -> MCPJsonConfig | None:
        """Get MCP configuration with caching.

        Args:
            working_dir: Directory to search for config files.
            inputs: Dictionary of input values for substitutions.

        Returns:
            MCPJsonConfig instance if found, None otherwise.

        """
        # For simplicity, we'll rely on MCPConfigLoader's internal caching
        # rather than implementing our own cache here, since the loader already
        # handles file modification time-based cache invalidation
        return MCPConfigLoader.load_mcp_config(working_dir, inputs)

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the resolver cache.

        This delegates to the underlying config loader's cache clearing mechanism.
        Useful for testing or when configuration files have been modified externally.
        """
        MCPConfigLoader.clear_cache()
        cls._resolved_config_cache = None


# Convenience function for direct module-level access
def load_mcp_config(
    working_dir: Path | None = None,
    inputs: dict[str, str] | None = None,
) -> MCPJsonConfig | None:
    """Load MCP configuration - convenience wrapper around MCPConfigLoader.

    Args:
        working_dir: Directory to search for config files. Defaults to current working directory.
        inputs: Dictionary of input values for ${input:id} substitutions.

    Returns:
        MCPJsonConfig instance if configuration found and valid, None otherwise.

    Raises:
        ValueError: If configuration file is malformed or invalid.
        FileNotFoundError: If referenced envFile doesn't exist.

    """
    return MCPConfigLoader.load_mcp_config(working_dir, inputs)
