# MCP Server Configuration

The Agentic Workflow Accelerator (AWA) provides comprehensive support for Model Context Protocol (MCP) servers, enabling seamless integration with external tools and services. This guide covers how to configure and use MCP servers with AWA using VSCode's MCP JSON format.

:::warning OpenAI Agents SDK
Currently within AWA, these MCP server configurations are only used by the [OpenAI Agents SDK wrapper](/usage/features/openai-agents-sdk).
:::

## Overview

AWA supports all three MCP transport types:

- **STDIO** - Command-line processes (most common)
- **HTTP** - REST API endpoints
- **SSE** - Server-Sent Events for real-time data streams

## Configuration Files

AWA looks for MCP server configurations in the following locations, relative to the root of the AWA core project:

1. `mcp.json`
2. `.mcp.json`

Copy the provided `mcp.example.json` file to `mcp.json` or `.mcp.json` and customize for your environment.

## Configuration Structure

The MCP configuration file follows this structure:

```json
{
  "inputs": {
    "apiKey": {
      "type": "text",
      "id": "apiKey",
      "description": "API key for external service",
      "password": true
    }
  },
  "mcpServers": {
    "serverName": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-example"],
      "env": {
        "DEBUG": "true"
      }
    }
  }
}
```

## Input Variables

Input variables provide a secure way to handle sensitive data like API keys and tokens. They are prompted from users when first needed and can be referenced throughout the configuration.

### Input Variable Types

```json
{
  "inputs": {
    "githubToken": {
      "type": "text", // Text input field
      "id": "githubToken", // Unique identifier
      "description": "GitHub API token for repository access",
      "password": true // Hide input when typing
    },
    "atlassianSite": {
      "type": "text", // Text input field
      "id": "atlassianSite",
      "description": "Atlassian site URL (e.g., https://company.atlassian.net)"
    },
    "environment": {
      "type": "select", // Selection dropdown
      "id": "environment",
      "description": "Target environment"
    }
  }
}
```

### Referencing Input Variables

Use `${input:variableName}` syntax to reference input variables:

```json
{
  "mcpServers": {
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github", "--token", "${input:githubToken}"]
    }
  }
}
```

## Transport Types

### STDIO Transport

STDIO transport runs MCP servers as command-line processes. This is the most common transport type.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/directory"
      ],
      "env": {
        "DEBUG": "true"
      }
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "python-server": {
      "command": "python",
      "args": ["-m", "your_mcp_server"],
      "env": {
        "LOG_LEVEL": "debug"
      }
    }
  }
}
```

#### STDIO Configuration Options

- `command`: The executable command to run
- `args`: Array of command-line arguments
- `env`: Environment variables to set for the process
- `envFile`: Path to `.env` file to load (optional)

### HTTP Transport

HTTP transport connects to MCP servers via REST API endpoints.

```json
{
  "mcpServers": {
    "enterpriseApi": {
      "type": "http",
      "url": "https://api.company.com/mcp/v1",
      "headers": {
        "Content-Type": "application/json",
        "Authorization": "Bearer ${ENTERPRISE_API_KEY}",
        "User-Agent": "AWA-MCP-Client/1.0"
      }
    },
    "customService": {
      "type": "http",
      "url": "http://localhost:8080/mcp",
      "headers": {
        "Content-Type": "application/json",
        "X-API-Key": "${input:serviceApiKey}"
      }
    }
  }
}
```

#### HTTP Configuration Options

- `type`: Must be "http"
- `url`: The HTTP endpoint URL
- `headers`: HTTP headers to send with requests

### SSE Transport

SSE (Server-Sent Events) transport is used for real-time data streams.

```json
{
  "mcpServers": {
    "realTimeWeather": {
      "type": "sse",
      "url": "https://api.weather.com/sse/v1/stream",
      "headers": {
        "Authorization": "Bearer ${input:weatherApiKey}",
        "Accept": "text/event-stream"
      }
    },
    "stockData": {
      "type": "sse",
      "url": "https://api.stocks.com/sse/live",
      "headers": {
        "Authorization": "Bearer ${STOCK_API_KEY}",
        "Accept": "text/event-stream"
      }
    }
  }
}
```

#### SSE Configuration Options

- `type`: Must be "sse"
- `url`: The SSE endpoint URL (can use WebSocket URLs with `wss://`)
- `headers`: HTTP headers to send with the connection request

## Environment Variables

### Variable Substitution Patterns

AWA supports several variable substitution patterns:

```json
{
  "mcpServers": {
    "example": {
      "command": "npx",
      "args": [
        "server-command",
        "--token",
        "${GITHUB_TOKEN}", // Environment variable
        "--api-key",
        "${input:apiKey}", // Input variable
        "--workspace",
        "${workspaceFolder}" // Working directory
      ],
      "env": {
        "AWS_REGION": "${AWS_REGION}",
        "DEBUG": "true"
      }
    }
  }
}
```

### Environment File Loading

Use `envFile` to automatically load environment variables from a file:

```json
{
  "mcpServers": {
    "server": {
      "command": "python",
      "args": ["-m", "server"],
      "envFile": ".env"
    }
  }
}
```

The `.env` file format supports:

```bash
# API Keys and Tokens
GITHUB_TOKEN=ghp_your_github_token_here
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
ENTERPRISE_API_KEY=your_enterprise_api_key

# AWS Credentials
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-west-2

# Service URLs
ENTERPRISE_API_URL=https://api.company.com
```
