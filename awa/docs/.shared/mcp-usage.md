You can run an MCP server via the AWA CLI that includes tools for running workflows.

<!--@include: /../.shared/running-mcp.md -->

You can run the MCP server using the official [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector).

```bash
npx @modelcontextprotocol/inspector uv run --directory "path/to/agentic-workflow-accelerator" -m awa.main mcp
```

Or you can configure the AWA MCP server in your agentic tool (e.g. Cursor, VS Code, Claude Desktop).

```json
{
  "mcpServers": {
    "awa": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "path/to/agentic-workflow-accelerator",
        "-m",
        "awa.main",
        "mcp"
      ]
    }
  }
}
```
