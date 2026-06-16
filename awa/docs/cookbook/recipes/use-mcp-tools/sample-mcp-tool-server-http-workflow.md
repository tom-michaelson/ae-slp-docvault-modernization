# SampleMCPToolHTTPWorkflow

A reusable Temporal workflow for demonstrating how to integrate MCP (Model Context Protocol) servers with the AWA workflow system using a sample calculator server over HTTP transport.

## Overview

The `SampleMCPToolHTTPWorkflow` demonstrates how to perform a programmatic tool call to an MCP server with AWA workflows. It uses a sample calculator MCP server with basic tools (add, multiply) to show how external tools can be invoked over HTTP transport — useful for remote MCP servers.

## How It Works

1. The workflow takes two numbers as input (`a` and `b`)
2. It invokes the `add` MCP tool to calculate the sum
3. It invokes the `multiply` MCP tool to calculate the product
4. The workflow returns both results in a dictionary

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
from workflows.mcp_tools.sample_mcp_tool_http_workflow import SampleMCPToolHTTPWorkflow
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
        SampleMCPToolHTTPWorkflow.run,
        input_data,
        id="sample-mcp-http-workflow",
    )

    logger.info(f"Sum: {result['sum']}")
    logger.info(f"Product: {result['product']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Sample MCP Server

The workflow uses a sample calculator MCP server located at `recipes/mcp_servers/sample_calculator_server.py` built with FastMCP.

### Running the Server

#### Direct uv execution

```bash
# Start with default settings (HTTP on 127.0.0.1:9000)
# Run this from the recipes directory after starting the recipe worker
cd recipes
uv run -m mcp_servers.sample_calculator_server

# Start with custom host and port
uv run -m mcp_servers.sample_calculator_server --host 0.0.0.0 --port 9042

# Start with stdio transport (for FastMCP CLI testing)
uv run -m mcp_servers.sample_calculator_server --transport stdio
```

#### Using FastMCP CLI (for stdio transport)

```bash
cd recipes
uv run fastmcp run mcp_servers/sample_calculator_server.py:mcp --transport stdio
```

### Available Tools

- `add(a: float, b: float) -> float`: Add two numbers together
- `multiply(a: float, b: float) -> float`: Multiply two numbers together

### Server Configuration

The example server supports the following command-line arguments:

- `--host`: Host to bind to (default: 127.0.0.1)
- `--port`: Port to bind to (default: 9000)
- `--transport`: Transport to use - "stdio" or "streamable-http" (default: streamable-http)

### MCP Inspector

You can also use the MCP Inspector to view the tools and their descriptions:

```bash
cd recipes
npx @modelcontextprotocol/inspector uv run -m mcp_servers.sample_calculator_server --transport stdio
```

## Command Line Execution — complete workflow

Follow these steps in order:

1. **Ensure recipes are enabled** in your `config.yaml`:

   ```yaml
   recipes: true
   ```

2. **Start the AWA services**:

   ```bash
   make start
   ```

   With recipes enabled, the unified worker will automatically register all core and recipe workflows.

3. **Start the MCP server** in a separate terminal:

   ```bash
   cd cookbook/recipes
   uv run -m mcp_servers.sample_calculator_server
   ```

4. **Run the sample MCP tool workflow** in another terminal:
   ```bash
   # From the main agentic-workflow-accelerator repository
   uv run -m awa.main run -w sample-mcp-tool-http --input '{"a": 5, "b": 3}'
   ```

## Related Workflows

- [SampleMCPToolStdioWorkflow](./sample-mcp-tool-stdio-workflow.md) - Uses stdio transport with automatic subprocess startup
- [Sample MCP Tool NPX Stdio Workflow](./sample-mcp-tool-npx-stdio-workflow.md) - Uses NPX-based filesystem server with stdio transport
