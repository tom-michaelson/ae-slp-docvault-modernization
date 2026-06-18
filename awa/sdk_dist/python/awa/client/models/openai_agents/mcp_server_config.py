from typing import Any

from pydantic import BaseModel, Field

from .enums import MCPServerTransport


class MCPServerConfig(BaseModel):
    """Configuration for MCP (Model Context Protocol) servers."""

    transport: MCPServerTransport
    server_params: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = Field(default=True)


class StdioMCPConfig(MCPServerConfig):
    """Configuration for Stdio MCP server (subprocess-based)."""

    transport: MCPServerTransport = Field(default=MCPServerTransport.STDIO)
    command: str = Field(..., description="Command to execute")
    args: list[str] | None = Field(default=None)
    env: dict[str, str] | None = Field(default=None)
    cwd: str | None = Field(default=None)


class SSEMCPConfig(MCPServerConfig):
    """Configuration for SSE (Server-Sent Events) MCP server."""

    transport: MCPServerTransport = Field(default=MCPServerTransport.SSE)
    url: str = Field(..., description="SSE endpoint URL")
    headers: dict[str, str] | None = Field(default=None)
    timeout_seconds: int | None = Field(default=30)


class StreamableHttpMCPConfig(MCPServerConfig):
    """Configuration for Streamable HTTP MCP server."""

    transport: MCPServerTransport = Field(default=MCPServerTransport.STREAMABLE_HTTP)
    endpoint: str = Field(..., description="HTTP endpoint")
    method: str = Field(default="POST")
    headers: dict[str, str] | None = Field(default=None)
    timeout_seconds: int | None = Field(default=30)
