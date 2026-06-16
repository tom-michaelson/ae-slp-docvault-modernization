# SampleMCPToolUVXStdioWorkflow

A reusable Temporal workflow for demonstrating how to integrate UVX-based MCP (Model Context Protocol) servers with the AWA workflow system using a time server over stdio transport.

## Overview

The `SampleMCPToolUVXStdioWorkflow` demonstrates how to perform programmatic tool calls to a UVX-based MCP server with AWA workflows. It uses the [`@modelcontextprotocol/mcp-server-time`](https://github.com/modelcontextprotocol/servers/blob/main/src/time/README.md) package to perform timezone conversions and time operations, showing how to integrate UVX-based MCP servers with AWA workflows.

## Key Features

- **UVX Integration**: Uses UVX to run the time MCP server
- **Timezone Operations**: Demonstrates time conversion, current time retrieval, and timezone handling
- **Automatic Startup**: Automatically starts the UVX server as a subprocess
- **Stdio Transport**: Uses stdio transport for less complexity

## How It Works

1. The workflow takes timezone and time information as input
2. It automatically starts the UVX time MCP server as a subprocess
3. It invokes `get_current_time` to get the current time in the source timezone
4. It invokes `convert_time` to convert the specified time between timezones
5. It invokes `get_current_time` to get the current time in the target timezone
6. The workflow returns all results in a dictionary
7. The subprocess is automatically cleaned up when the workflow completes

## Usage

### Input

The workflow requires a `UVXStdioTimeInput` object with the following properties:

- `source_timezone`: Source timezone for time operations (defaults to "America/New_York")
- `target_timezone`: Target timezone for time conversion (defaults to "Asia/Tokyo")
- `time`: Time string to convert (defaults to "16:30")

### Output

The workflow returns a dictionary with:

- `source_current_time`: Current time in the source timezone
- `time_conversion`: Result of converting the specified time between timezones
- `target_current_time`: Current time in the target timezone
- `source_timezone`: The source timezone that was used
- `target_timezone`: The target timezone that was used
- `converted_time`: The original time string that was converted

### Example

```python
from temporalio.client import Client
from workflows.mcp_tools.sample_mcp_tool_uvx_stdio_workflow import SampleMCPToolUVXStdioWorkflow
from workflows.mcp_tools.models.workflow_input import UVXStdioTimeInput
from loguru import logger
import asyncio

async def main() -> None:
    logger.info("Starting test client")
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    logger.info("Connected to Temporal")

    # Define the input
    input_data = UVXStdioTimeInput(
        source_timezone="America/New_York",
        target_timezone="Europe/London",
        time="14:30"
    )
    logger.info(f"Input data: {input_data}")

    # Execute the workflow
    result = await client.execute_workflow(
        SampleMCPToolUVXStdioWorkflow.run,
        input_data,
        id="sample-mcp-uvx-stdio-workflow",
    )

    logger.info(f"Source current time: {result['source_current_time']}")
    logger.info(f"Time conversion: {result['time_conversion']}")
    logger.info(f"Target current time: {result['target_current_time']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## MCP Configuration

The workflow uses the following MCP configuration that automatically starts the UVX server:

```python
mcp_config = {
    "mcpServers": {
        "time": {
            "command": "uvx",
            "args": [
                "mcp-server-time",
                "--local-timezone=America/Los_Angeles",
            ],
            "transport": "stdio",
            "env": {"EXAMPLE_ENV_VAR": "example_value"},
        },
    },
}
```

### Configuration Details

- **command**: The command to start the MCP server (`uvx`)
- **args**: Arguments to pass to the command:
  - `mcp-server-time`: The UVX package to run
  - `--local-timezone=America/Los_Angeles`: Sets the local timezone for the server
- **transport**: Specifies stdio transport mode
- **env**: Optional environment variables to pass to the subprocess

## Command Line Execution

No manual MCP server startup is required. Follow these steps:

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
   uv run -m awa.main run -w sample-mcp-tool-uvx-stdio --input '{"source_timezone": "America/New_York", "target_timezone": "Europe/London", "time": "14:30"}'
   ```

The workflow will automatically:

1. Start the UVX time MCP server as a subprocess
2. Execute the time operations
3. Clean up the subprocess when complete

## Additional Prerequisites

- **UVX**: The workflow requires UVX to be installed (`pip install uvx`)
- **Network Access**: UVX needs internet access to download the time server package (first time only)

## Related Workflows

- [SampleMCPToolHTTPWorkflow](./sample-mcp-tool-server-http-workflow.md) - Uses HTTP transport with calculator server
- [SampleMCPToolStdioWorkflow](./sample-mcp-tool-stdio-workflow.md) - Uses stdio transport with calculator server
- [SampleMCPToolNPXStdioWorkflow](./sample-mcp-tool-npx-stdio-workflow.md) - Uses NPX-based filesystem server with stdio transport
