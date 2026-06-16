# SampleMCPToolStdioWorkflow

A reusable Temporal workflow for demonstrating how to integrate MCP (Model Context Protocol) servers with the AWA workflow system using a sample calculator server over stdio transport.

## Overview

The `SampleMCPToolStdioWorkflow` demonstrates how to perform a programmatic tool call to an MCP server with AWA workflows using stdio transport. It uses a sample calculator MCP server with basic tools (add, multiply) to show how locally defined MCP tools can be invoked with automatic subprocess startup.

## Key Differences from HTTP Workflow

Unlike the HTTP workflow, this stdio workflow:

- Automatically starts the MCP server as a subprocess
- Uses stdio transport instead of HTTP
- Doesn't require manual server startup before running the workflow

## How It Works

1. The workflow takes two numbers as input (`a` and `b`)
2. It automatically starts the MCP server as a subprocess using stdio transport
3. It invokes the `add` MCP tool to calculate the sum
4. It invokes the `multiply` MCP tool to calculate the product
5. The workflow returns both results in a dictionary
6. The subprocess is automatically cleaned up when the workflow completes

## Usage

### Input

The workflow requires a `CalculatorInput` object with the following properties:

- `a`: First number for calculations
- `b`: Second number for calculations

### Output

The workflow returns a dictionary with:

- `sum`: Result of adding `a` and `b`
- `product`: Result of multiplying `a` and `b`

### Example

```python
from temporalio.client import Client
from workflows.mcp_tools.sample_mcp_tool_stdio_workflow import SampleMCPToolStdioWorkflow
from workflows.mcp_tools.models.workflow_input import CalculatorInput
from loguru import logger
import asyncio

async def main() -> None:
    logger.info("Starting test client")
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    logger.info("Connected to Temporal")

    # Define the input
    input_data = CalculatorInput(a=5, b=3)
    logger.info(f"Input data: {input_data}")

    # Execute the workflow
    result = await client.execute_workflow(
        SampleMCPToolStdioWorkflow.run,
        input_data,
        id="sample-mcp-stdio-workflow",
    )

    logger.info(f"Sum: {result['sum']}")
    logger.info(f"Product: {result['product']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## MCP Configuration

The workflow uses the following MCP configuration that automatically starts the server:

```python
mcp_config = {
    "mcpServers": {
        "calculator": {
            "command": "uv",
            "args": ["run", "-m", "mcp_servers.sample_calculator_server", "--transport", "stdio"],
            "transport": "stdio",
            "env": {"EXAMPLE_ENV_VAR": "example_value"},
        },
    },
}
```

### Configuration Details

- **command**: The command to start the MCP server (`uv`)
- **args**: Arguments to pass to the command (runs the test server with stdio transport)
- **transport**: Specifies stdio transport mode
- **env**: Optional environment variables to pass to the subprocess

## Available Tools

The workflow uses the same sample calculator MCP server with these tools:

- `add(a: float, b: float) -> float`: Add two numbers together
- `multiply(a: float, b: float) -> float`: Multiply two numbers together

## Command Line Execution

Unlike the HTTP workflow, no manual MCP server startup is required. Follow these steps:

1. **Ensure recipes are enabled** in your `config.yaml`:

   ```yaml
   recipes: true
   ```

2. **Start the AWA services**:

   ```bash
   make start
   ```

   With recipes enabled, the unified worker will automatically register all core and recipe workflows.

3. **Run the sample MCP tool workflow**:
   ```bash
   # From the main agentic-workflow-accelerator repository
   uv run -m awa.main run -w sample-mcp-tool-stdio --input '{"a": 5, "b": 3}'
   ```

The workflow will automatically:

1. Start the MCP server as a subprocess
2. Execute the calculations
3. Clean up the subprocess when complete

## Advantages of Stdio Transport

- **Automatic Process Management**: No need to manually start/stop servers
- **Better Isolation**: Each workflow execution gets its own server instance
- **Simplified Deployment**: No port management or network configuration required
- **Resource Cleanup**: Automatic cleanup of subprocesses when workflows complete

## Related Workflows

- [SampleMCPToolHTTPWorkflow](./sample-mcp-tool-server-http-workflow.md) - Uses HTTP transport (requires manual server startup)
- [SampleMCPToolNPXStdioWorkflow](./sample-mcp-tool-npx-stdio-workflow.md) - Uses NPX-based filesystem server with stdio transport
