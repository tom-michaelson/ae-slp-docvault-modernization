# PydanticAI Agent Workflow

A powerful demonstration of PydanticAI agent mode integration with MCP (Model Context Protocol) tools for autonomous task execution.

**Example Usage:** [View example prompt and generated outputs](./DemoScript.md)

## Overview

The `AgentModePydanticAIWorkflow` showcases how to leverage PydanticAI agents with MCP server integration to execute complex, multi-step tasks autonomously. This workflow demonstrates agent-driven automation using the Desktop Commander MCP tools for real file operations, process execution, and system management.

## Key Features

- **PydanticAI Agent Integration**: Uses the PydanticAI agent provider for intelligent task execution
- **MCP Tool Support**: Integrates with Model Context Protocol servers for extended capabilities
- **Autonomous Execution**: Agent makes decisions and performs operations without step-by-step guidance
- **Configurable Agent Modes**: Supports ANALYZE mode for read-only operations and ACT mode for modifications
- **Progress Tracking**: Maintains task checklist for transparent progress monitoring
- **Error Resilience**: Handles failures gracefully with retry logic and alternative approaches

## How It Works

1. **Configuration Loading**: Reads MCP server configuration from `input/mcp.json` file
2. **Agent Setup**: Configures a PydanticAI agent with:
   - Agent mode (ANALYZE/ACT)
   - Working directory
   - System prompt with task instructions
   - MCP server connections
   - Execution timeout
3. **Task Execution**: Agent autonomously:
   - Creates project structure
   - Writes implementation code
   - Generates tests
   - Executes validation
   - Documents operations
4. **Result Collection**: Returns comprehensive task execution results

## Usage

### Input Parameters

The workflow accepts an optional `prompt` string parameter:

- `prompt` (optional): Custom instructions for the agent. If not provided, uses a default demonstration prompt.

### Output

Returns a dictionary containing:

- Task execution results
- File operation summaries
- Progress tracking information
- Any errors or warnings encountered

## MCP Configuration

The workflow uses an MCP configuration file for tool server setup:

**Location**: `recipes/workflows/pydantic_ai/input/mcp.json`

```json
{
  "mcpServers": {
    "desktop-commander": {
      "command": "npx",
      "args": ["-y", "@wonderwhy-er/desktop-commander@latest"],
      "timeout_ms": 30000
    }
  }
}
```

### Desktop Commander MCP Server

This workflow leverages the [Desktop Commander MCP server](https://github.com/wonderwhy-er/DesktopCommanderMCP) by @wonderwhy-er, which provides comprehensive system access similar to third-party autonomous agents. Desktop Commander gives the PydanticAI agent powerful capabilities through 18+ specialized tools:

**Terminal & Process Control:**

- Execute terminal commands with streaming output and timeout support
- Manage background processes (list, monitor, kill)
- Interactive REPL support (SSH, Python, Node.js)
- Execute code in-memory (Python, Node.js, R) without file creation

**File System Operations:**

- Full read/write file access
- Directory creation, listing, and management
- Move and organize files/directories
- Advanced file reading (including tail-like negative offsets)
- File metadata retrieval

**Code Editing & Search:**

- Surgical text replacements with pattern matching
- Complete file rewrites
- Multi-file editing operations
- Recursive code search using vscode-ripgrep
- Find and replace across codebases

**Configuration & Utilities:**

- Dynamic configuration management
- Instant data analysis (CSV/JSON files)
- Comprehensive audit logging with rotation
- Cross-platform support (Windows, macOS, Linux)

This extensive toolset enables the agent to autonomously perform complex tasks like project scaffolding, code generation, testing, and documentation—essentially functioning as a full-capability autonomous coding agent within the AWA framework.

## Command Line Execution

```bash
# Basic usage with default prompt
uv run -m awa.main run -w "awa-agent-mode-pydantic-ai"
```

```bash
# Custom prompt for specific task
uv run -m awa.main run -w "awa-agent-mode-pydantic-ai" -i '{
  "prompt": "Create a Python calculator with comprehensive tests"
}'
```

## Agent Configuration

The workflow uses `AgentConfiguration` for setup:

```python
AgentConfiguration(
    mode=AgentModeEnum.ANALYZE,           # Or ANALYZE for read-only
    provider=AgentProviderEnum.PYDANTIC_AI,
    prompt=actual_prompt,
    timeout_seconds=90,
    initialize=True,
    working_directory="/path/to/workspace",
    mcp=mcp_config
)
```

### Configuration Options

- **mode**: `ANALYZE` (read-only) or `ACT` (can modify files)
- **provider**: can use either `PYDANTIC_AI` or `DEFAULT` for PydanticAI agent
- **timeout_seconds**: Maximum execution time
- **initialize**: Whether to initialize the agent environment
- **working_directory**: Base directory for agent operations
- **mcp**: MCP server configuration object

## Related Workflows

- [SampleIsolatedAgentAnalyzeWorkflow](../agent-isolation/sample-isolated-agent-analyze-workflow.md) – Isolated agent execution in ANALYZE mode
- [SampleIsolatedAgentActWorkflow](../agent-isolation/sample-isolated-agent-act-workflow.md) – Isolated agent execution in ACT mode
- [Use MCP Tools](../use-mcp-tools/sample-mcp-tool-stdio-workflow.md) – MCP tool integration patterns
