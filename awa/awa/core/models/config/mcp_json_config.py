"""Pydantic models for parsing VSCode's MCP JSON configuration format.

This module provides models for validating and parsing the MCP (Model Context Protocol)
JSON configuration format used by VSCode extensions to define server configurations
and input variables.
"""

from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator


class MCPInputVariable(BaseModel):
    """Model representing an input variable in MCP JSON configuration.

    Input variables allow dynamic configuration of server parameters through
    user-provided values or environment variables.
    """

    type: Literal["text", "password", "select"] = Field(
        ...,
        description="The type of input field to display to the user",
    )
    id: str = Field(
        ...,
        description="Unique identifier for this input variable",
    )
    description: str = Field(
        ...,
        description="Human-readable description shown to the user",
    )
    password: bool | None = Field(
        default=False,
        description="Whether this input should be treated as a password (hidden input)",
    )


class MCPServerConfig(BaseModel):
    """Model representing a server configuration in MCP JSON format.

    Supports all transport types (stdio, http, sse) with their respective
    configuration options.
    """

    command: str | None = Field(
        default=None,
        description="Command to execute for stdio transport",
    )
    args: list[str] | None = Field(
        default=None,
        description="Arguments to pass to the command for stdio transport",
    )
    url: str | None = Field(
        default=None,
        description="URL for HTTP or SSE transport",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="HTTP headers for HTTP or SSE transport",
    )
    env: dict[str, str] | None = Field(
        default=None,
        description="Environment variables to set when running the server",
    )
    envFile: str | None = Field(  # noqa: N815
        default=None,
        description="Path to environment file to load",
    )
    type: Literal["stdio", "http", "sse"] = Field(
        default="stdio",
        description="Transport type for the server connection",
    )

    @model_validator(mode="after")
    def validate_transport_requirements(self) -> "MCPServerConfig":
        """Validate that transport types have their required fields."""
        if self.type == "stdio" and not self.command:
            raise ValueError("stdio transport requires a command")
        if self.type in ["http", "sse"] and not self.url:
            raise ValueError(f"{self.type} transport requires a url")
        return self


class MCPJsonConfig(BaseModel):
    """Main model for the complete MCP JSON configuration structure.

    This represents the root configuration object that contains input variables
    and server configurations for MCP setup. Supports both "servers" and "mcpServers"
    field names for server configurations.
    """

    inputs: dict[str, MCPInputVariable] | None = Field(
        default=None,
        description="Dictionary of input variables keyed by their IDs",
    )
    servers: dict[str, MCPServerConfig] = Field(
        ...,
        description="Dictionary of server configurations keyed by server names",
        validation_alias=AliasChoices("servers", "mcpServers"),
    )

    model_config = ConfigDict(
        extra="forbid",  # Don't allow extra fields
        validate_assignment=True,  # Validate on assignment
    )
