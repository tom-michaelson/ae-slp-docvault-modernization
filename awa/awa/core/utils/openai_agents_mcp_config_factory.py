"""Factory for converting AWA MCP configuration models to OpenAI Agents SDK compatible formats.

This module provides utilities to transform AWA's MCP server configurations into
formats that can be consumed by the OpenAI Agents SDK's MCP integration.
"""

from typing import Any

from awa.sdk.models.openai_agents.enums import MCPServerTransport
from awa.sdk.models.openai_agents.mcp_server_config import (
    MCPServerConfig,
    SSEMCPConfig,
    StdioMCPConfig,
    StreamableHttpMCPConfig,
)


class MCPConfigurationFactory:
    """Factory for creating OpenAI Agents SDK compatible MCP configurations.

    This factory handles the conversion of AWA's MCP configuration models
    to the format expected by the OpenAI Agents SDK, supporting multiple
    transport types including Stdio, SSE, and Streamable HTTP.
    """

    @classmethod
    def create_mcp_server_config(
        cls,
        mcp_config: MCPServerConfig,
    ) -> dict[str, Any]:
        """Convert AWA MCP configuration to OpenAI Agents SDK format.

        Args:
            mcp_config: AWA MCP server configuration model

        Returns:
            Dictionary with OpenAI Agents SDK compatible MCP configuration

        Raises:
            ValueError: If the transport type is not supported or configuration is invalid

        """
        if not mcp_config.enabled:
            return {}

        # Route to appropriate handler based on transport type
        handlers = {
            MCPServerTransport.STDIO: cls._convert_stdio_config,
            MCPServerTransport.SSE: cls._convert_sse_config,
            MCPServerTransport.STREAMABLE_HTTP: cls._convert_streamable_http_config,
        }

        handler = handlers.get(mcp_config.transport)
        if not handler:
            msg = f"Unsupported MCP transport type: {mcp_config.transport}"
            raise ValueError(msg)

        try:
            return handler(mcp_config)
        except (AttributeError, KeyError, TypeError) as e:
            msg = f"Error converting MCP configuration: {e}"
            raise ValueError(msg) from e

    @classmethod
    def _convert_stdio_config(cls, config: MCPServerConfig) -> dict[str, Any]:
        """Convert Stdio MCP configuration to OpenAI Agents SDK format.

        Args:
            config: Stdio MCP server configuration

        Returns:
            Dictionary with Stdio MCP configuration for OpenAI Agents SDK

        Raises:
            ValueError: If required fields are missing

        """
        if not isinstance(config, StdioMCPConfig):
            msg = f"Expected StdioMCPConfig, got {type(config).__name__}"
            raise TypeError(msg)

        if not config.command:
            msg = "Stdio MCP configuration requires a command"
            raise ValueError(msg)

        # Build the Stdio configuration for OpenAI Agents SDK
        stdio_config = {
            "type": "stdio",
            "command": config.command,
        }

        # Add optional fields if present
        if config.args:
            stdio_config["args"] = config.args
        if config.env:
            stdio_config["env"] = config.env
        if config.cwd:
            stdio_config["cwd"] = config.cwd

        # Include any additional server parameters
        if config.server_params:
            stdio_config.update(config.server_params)

        return stdio_config

    @classmethod
    def _convert_sse_config(cls, config: MCPServerConfig) -> dict[str, Any]:
        """Convert SSE MCP configuration to OpenAI Agents SDK format.

        Args:
            config: SSE MCP server configuration

        Returns:
            Dictionary with SSE MCP configuration for OpenAI Agents SDK

        Raises:
            ValueError: If required fields are missing

        """
        if not isinstance(config, SSEMCPConfig):
            msg = f"Expected SSEMCPConfig, got {type(config).__name__}"
            raise TypeError(msg)

        if not config.url:
            msg = "SSE MCP configuration requires a URL"
            raise ValueError(msg)

        # Build the SSE configuration for OpenAI Agents SDK
        sse_config = {
            "type": "sse",
            "url": config.url,
        }

        # Add optional fields if present
        if config.headers:
            sse_config["headers"] = config.headers
        if config.timeout_seconds is not None:
            sse_config["timeout"] = config.timeout_seconds

        # Include any additional server parameters
        if config.server_params:
            sse_config.update(config.server_params)

        return sse_config

    @classmethod
    def _convert_streamable_http_config(cls, config: MCPServerConfig) -> dict[str, Any]:
        """Convert Streamable HTTP MCP configuration to OpenAI Agents SDK format.

        Args:
            config: Streamable HTTP MCP server configuration

        Returns:
            Dictionary with Streamable HTTP MCP configuration for OpenAI Agents SDK

        Raises:
            ValueError: If required fields are missing

        """
        if not isinstance(config, StreamableHttpMCPConfig):
            msg = f"Expected StreamableHttpMCPConfig, got {type(config).__name__}"
            raise TypeError(msg)

        if not config.endpoint:
            msg = "Streamable HTTP MCP configuration requires an endpoint"
            raise ValueError(msg)

        # Build the Streamable HTTP configuration for OpenAI Agents SDK
        http_config = {
            "type": "streamable_http",
            "endpoint": config.endpoint,
            "method": config.method,
        }

        # Add optional fields if present
        if config.headers:
            http_config["headers"] = config.headers
        if config.timeout_seconds is not None:
            http_config["timeout"] = config.timeout_seconds

        # Include any additional server parameters
        if config.server_params:
            http_config.update(config.server_params)

        return http_config

    @classmethod
    def create_multiple_mcp_configs(
        cls,
        mcp_configs: list[MCPServerConfig],
    ) -> list[dict[str, Any]]:
        """Convert multiple AWA MCP configurations to OpenAI Agents SDK format.

        Args:
            mcp_configs: List of AWA MCP server configuration models

        Returns:
            List of dictionaries with OpenAI Agents SDK compatible MCP configurations

        Raises:
            ValueError: If any configuration is invalid

        """
        if not mcp_configs:
            return []

        converted_configs = []
        for idx, config in enumerate(mcp_configs):
            try:
                converted = cls.create_mcp_server_config(config)
                if converted:  # Only add non-empty configurations
                    converted_configs.append(converted)
            except ValueError as e:
                msg = f"Error converting MCP configuration at index {idx}: {e}"
                raise ValueError(msg) from e

        return converted_configs
