:::warning Running MCP
The MCP server should be run **in addition to** running the AWA backing services (Temporal, AWA API). Both can be done via the AWA CLI, but they are two separate processes. Typically, the AWA backing services can be started once and left running, while the MCP server itself is run on-demand by your agentic tool (e.g. Cursor, VS Code, Claude Desktop).
:::
