"""Factory for converting VSCode MCP JSON configurations to OpenAI Agents SDK providers.

This module provides utilities to transform VSCode's MCP server configurations into
provider instances that can be consumed by the OpenAI Agents SDK's MCP integration
through the Temporal contrib module.
"""

from agents.mcp import MCPServerSse, MCPServerSseParams, MCPServerStdio, MCPServerStdioParams
from temporalio.contrib.openai_agents import StatefulMCPServerProvider, StatelessMCPServerProvider

from awa.core.models.config.mcp_json_config import MCPJsonConfig, MCPServerConfig


class MCPProviderFactory:
    """Factory for creating OpenAI Agents SDK compatible MCP providers from VSCode MCP JSON configurations.

    This factory handles the conversion of VSCode's MCP configuration format
    to provider instances compatible with the Temporal OpenAI Agents SDK integration,
    supporting both stateless and stateful providers for different transport types.
    """

    @classmethod
    def create_mcp_providers(
        cls,
        mcp_config: MCPJsonConfig,
    ) -> tuple[list[StatelessMCPServerProvider], list[StatefulMCPServerProvider]]:
        """Convert VSCode MCP JSON configuration to OpenAI Agents SDK provider instances.

        Args:
            mcp_config: VSCode MCP JSON configuration containing server definitions

        Returns:
            Tuple of (stateless_providers, stateful_providers) lists

        Raises:
            ValueError: If a transport type is not supported or configuration is invalid

        """
        stateless_providers = []
        stateful_providers = []

        for server_name, server_config in mcp_config.servers.items():
            try:
                # Create providers based on transport type
                if server_config.type == "stdio":
                    # Stdio servers are typically stateless since they spawn new processes
                    provider = cls._create_stdio_provider(server_name, server_config)
                    stateless_providers.append(provider)

                elif server_config.type == "http":
                    # HTTP servers can be either stateless or stateful
                    # For now, default to stateless for HTTP
                    provider = cls._create_http_provider(server_name, server_config)
                    stateless_providers.append(provider)

                elif server_config.type == "sse":
                    # SSE servers benefit from persistent connections, so use stateful
                    provider = cls._create_sse_provider(server_name, server_config)
                    stateful_providers.append(provider)

                else:
                    msg = f"Unsupported MCP transport type: {server_config.type}"
                    raise ValueError(msg)

            except (AttributeError, KeyError, TypeError) as e:
                msg = f"Error creating MCP provider for server '{server_name}': {e}"
                raise ValueError(msg) from e

        return stateless_providers, stateful_providers

    @classmethod
    def _create_stdio_provider(
        cls,
        server_name: str,
        config: MCPServerConfig,
    ) -> StatelessMCPServerProvider:
        """Create a stateless provider for stdio transport.

        Args:
            server_name: Name of the MCP server
            config: Stdio MCP server configuration

        Returns:
            StatelessMCPServerProvider configured for stdio transport

        Raises:
            ValueError: If required stdio configuration is missing

        """
        if not config.command:
            msg = f"Stdio MCP server '{server_name}' requires a command"
            raise ValueError(msg)

        def server_factory() -> MCPServerStdio:
            """Create new MCPServerStdio instances."""
            # Create stdio server configuration parameters
            params = MCPServerStdioParams(
                command=config.command,
                args=config.args if config.args else [],
                env=config.env if config.env else {},
            )

            return MCPServerStdio(params=params, name=server_name)

        return StatelessMCPServerProvider(server_factory)

    @classmethod
    def _create_http_provider(
        cls,
        server_name: str,
        config: MCPServerConfig,
    ) -> StatelessMCPServerProvider:
        """Create a stateless provider for HTTP transport.

        Args:
            server_name: Name of the MCP server
            config: HTTP MCP server configuration

        Returns:
            StatelessMCPServerProvider configured for HTTP transport

        Raises:
            ValueError: If required HTTP configuration is missing
            NotImplementedError: HTTP transport is not fully implemented yet

        """
        if not config.url:
            msg = f"HTTP MCP server '{server_name}' requires a URL"
            raise ValueError(msg)

        # Note: HTTP MCP servers are not yet fully implemented in the agents package
        # This is a placeholder implementation that will need to be updated
        # when HTTP transport becomes available
        def server_factory() -> None:
            """Create new HTTP MCP server instances."""
            msg = "HTTP MCP transport is not yet implemented in the agents package"
            raise NotImplementedError(msg)

        return StatelessMCPServerProvider(server_factory)

    @classmethod
    def _create_sse_provider(
        cls,
        server_name: str,
        config: MCPServerConfig,
    ) -> StatefulMCPServerProvider:
        """Create a stateful provider for SSE transport.

        Args:
            server_name: Name of the MCP server
            config: SSE MCP server configuration

        Returns:
            StatefulMCPServerProvider configured for SSE transport

        Raises:
            ValueError: If required SSE configuration is missing

        """
        if not config.url:
            msg = f"SSE MCP server '{server_name}' requires a URL"
            raise ValueError(msg)

        def server_factory() -> MCPServerSse:
            """Create new MCPServerSse instances."""
            # Create SSE server configuration parameters
            params = MCPServerSseParams(
                url=config.url,
                headers=config.headers if config.headers else {},
            )

            return MCPServerSse(params=params, name=server_name)

        return StatefulMCPServerProvider(server_factory)

    @classmethod
    def create_single_provider(
        cls,
        server_name: str,
        server_config: MCPServerConfig,
        prefer_stateful: bool = False,
    ) -> StatelessMCPServerProvider | StatefulMCPServerProvider:
        """Create a single MCP provider for a specific server configuration.

        Args:
            server_name: Name of the MCP server
            server_config: MCP server configuration
            prefer_stateful: Whether to prefer stateful providers when both are possible

        Returns:
            Either a StatelessMCPServerProvider or StatefulMCPServerProvider

        Raises:
            ValueError: If the transport type is not supported or configuration is invalid

        """
        # Create a minimal MCPJsonConfig for the single server
        json_config = MCPJsonConfig(servers={server_name: server_config})

        # Get providers
        stateless_providers, stateful_providers = cls.create_mcp_providers(json_config)

        # Return the appropriate provider based on preference and availability
        if prefer_stateful and stateful_providers:
            return stateful_providers[0]
        if stateless_providers:
            return stateless_providers[0]
        if stateful_providers:
            return stateful_providers[0]
        msg = f"No providers could be created for server '{server_name}'"
        raise ValueError(msg)

    @classmethod
    def get_supported_transports(cls) -> list[str]:
        """Get the list of supported MCP transport types.

        Returns:
            List of supported transport type strings

        """
        return ["stdio", "sse", "http"]

    @classmethod
    def validate_mcp_config(cls, mcp_config: MCPJsonConfig) -> list[str]:
        """Validate an MCP configuration and return any validation errors.

        Args:
            mcp_config: VSCode MCP JSON configuration to validate

        Returns:
            List of validation error messages (empty if valid)

        """
        errors = []
        supported_transports = cls.get_supported_transports()

        for server_name, server_config in mcp_config.servers.items():
            # Check transport type support
            if server_config.type not in supported_transports:
                errors.append(
                    f"Server '{server_name}': Unsupported transport type '{server_config.type}'. "
                    f"Supported types: {', '.join(supported_transports)}",
                )
                continue

            # Validate transport-specific requirements
            if server_config.type == "stdio":
                if not server_config.command:
                    errors.append(f"Server '{server_name}': Stdio transport requires a command")

            elif server_config.type in ["http", "sse"] and not server_config.url:
                errors.append(f"Server '{server_name}': {server_config.type.upper()} transport requires a URL")

        return errors
