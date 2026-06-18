# SampleMCPToolNPXStdioWorkflow

A reusable Temporal workflow for demonstrating how to integrate NPX-based MCP (Model Context Protocol) servers with the AWA workflow system using a filesystem server over stdio transport.

## Overview

The `SampleMCPToolNPXStdioWorkflow` demonstrates how to perform programmatic tool calls to an NPX-based MCP server with AWA workflows. It uses the [`@modelcontextprotocol/server-filesystem`](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) package to explore and interact with the filesystem, showing how to integrate third-party NPX-based MCP servers with AWA workflows.

## Key Features

- **NPX Integration**: Uses NPX to run the official filesystem MCP server
- **Filesystem Operations**: Demonstrates file listing, reading, and metadata retrieval
- **Automatic Startup**: Automatically starts the NPX server as a subprocess
- **Stdio Transport**: Uses stdio transport for less complexity

## How It Works

1. The workflow takes a directory path as input
2. It automatically starts the NPX filesystem MCP server as a subprocess
3. It invokes `list_directory` to explore the specified directory
4. It invokes `read_file` to read the contents of README.md
5. It invokes `get_file_info` to get metadata about README.md
6. The workflow returns all results in a dictionary
7. The subprocess is automatically cleaned up when the workflow completes

## Usage

### Input

The workflow requires a `NPXStdioFilesystemInput` object with the following properties:

- `directory_path`: Path to the directory to explore (defaults to "." if not specified)

### Output

The workflow returns a dictionary with:

- `list_directory`: Result of listing files in the specified directory
- `read_file`: Contents of README.md file
- `file_info`: Metadata about README.md file
- `explored_directory`: The directory path that was explored

### Example

```python
from temporalio.client import Client
from workflows.mcp_tools.sample_mcp_tool_npx_stdio_workflow import SampleMCPToolNPXStdioWorkflow
from workflows.mcp_tools.models.workflow_input import NPXStdioFilesystemInput
from loguru import logger
import asyncio

async def main() -> None:
    logger.info("Starting test client")
    # Connect to Temporal
    client = await Client.connect("localhost:7233")
    logger.info("Connected to Temporal")

    # Define the input
    input_data = NPXStdioFilesystemInput(directory_path="./docs")
    logger.info(f"Input data: {input_data}")

    # Execute the workflow
    result = await client.execute_workflow(
        SampleMCPToolNPXStdioWorkflow.run,
        input_data,
        id="sample-mcp-npx-stdio-workflow",
    )

    logger.info(f"Directory listing: {result['list_directory']}")
    logger.info(f"README content length: {len(result['read_file'])}")
    logger.info(f"File info: {result['file_info']}")

if __name__ == "__main__":
    asyncio.run(main())
```

## MCP Configuration

The workflow uses the following MCP configuration that automatically starts the NPX server:

```python
mcp_config = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": [
                "-y",
                "@modelcontextprotocol/server-filesystem",
                ".",  # path that the server is allowed to explore
            ],
            "transport": "stdio",
            "env": {"EXAMPLE_ENV_VAR": "example_value"},
        },
    },
}
```

### Configuration Details

- **command**: The command to start the MCP server (`npx`)
- **args**: Arguments to pass to the command:
  - `-y`: Automatically answer "yes" to prompts
  - `@modelcontextprotocol/server-filesystem`: The NPX package to run
  - `.`: The root path the server is allowed to explore
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
   uv run -m awa.main run -w sample-mcp-tool-npx-stdio --input '{"directory_path": "./docs"}'
   ```

The workflow will automatically:

1. Start the NPX filesystem MCP server as a subprocess
2. Execute the filesystem operations
3. Clean up the subprocess when complete

## Additional Prerequisites

- **Node.js and NPX**: The workflow requires Node.js and NPX to be installed
- **Network Access**: NPX needs internet access to download the filesystem server package (first time only)

## Related Workflows

- [Sample MCP Tool HTTP Workflow](./sample-mcp-tool-server-http-workflow.md) - Uses HTTP transport with calculator server
- [SampleMCPToolStdioWorkflow](./sample-mcp-tool-stdio-workflow.md) - Uses stdio transport with calculator server
