# Agents

AWA provides powerful agent execution capabilities, enabling you to integrate various AI-powered agents into your workflows for code generation, analysis, and automated task execution. These features allow you to leverage specialized agents while maintaining safe, isolated execution environments.

## Overview

AWA offers comprehensive agent integration through two main execution modes:

- **`awa-execute-agent`**: Direct agent execution with configurable prompts and settings
- **`IsolatedAgentChildWorkflow`**: Safe agent execution in isolated environments with automatic cleanup

These capabilities support multiple agent providers and execution modes, making it easy to integrate AI agents into your development workflows.

## Agent Execution

AWA provides multiple approaches for executing AI agents, depending on your specific needs and the agent type.

### Direct Agent Execution

The `awa-execute-agent` workflow provides a straightforward interface for executing external AI agents with configurable prompts and settings. It handles agent initialization, prompt execution, and result processing.

**Common use cases:**
- Code review and analysis with specialized agents
- Automated bug fixing using external tools
- Documentation generation with agent-specific capabilities
- Code refactoring suggestions
- Custom development tasks requiring specific agent environments

See the workflow reference documentation for [`awa-execute-agent`](/reference/workflow/execute-agent.md).

### Isolated Agent Execution

The `IsolatedAgentChildWorkflow` provides safe agent execution in completely isolated environments, ensuring that agents cannot affect your source code directly while still enabling powerful automation capabilities.

**Key benefits:**
- **Complete isolation**: Agents run in separate environments (git worktrees or temporary directories)
- **Safe execution**: No risk of unintended changes to your main codebase
- **Automatic cleanup**: Isolated environments are automatically removed after execution
- **Flexible modes**: Support for both code modification (ACT) and analysis (ANALYZE) modes

See the workflow reference documentation for [`IsolatedAgentChildWorkflow`](/reference/workflow/isolated-agent-child-workflow.md).

## Agent Modes

AWA supports two distinct execution modes for agents:

### ACT Mode
- **Purpose**: Make direct changes to the codebase
- **Behavior**: Agent can create, modify, or delete files in the isolated environment
- **Output**: Changes are automatically committed and merged back to the source branch
- **Use Cases**: Code modifications, refactoring, bug fixes, feature implementation

### ANALYZE Mode
- **Purpose**: Generate analysis outputs without modifying source code
- **Behavior**: Agent writes outputs to a configurable directory in the isolated environment
- **Output**: Analysis results are copied to the source repository
- **Use Cases**: Code analysis, security audits, documentation generation, test reports

## Supported Agent Providers

AWA integrates with multiple AI agent providers, each offering specialized capabilities:

<!--@include: ../../installation/agents/parts/agent_list.md-->

PydanticAI is built into AWA and requires no additional installation. All other agents require separate installation and setup. Each agent provider has unique strengths and installation requirements. For setup instructions, see the [agent installation documentation](/installation/agents/overview.md).

## Agent Activities

In addition to the high-level workflows, AWA provides lower-level agent activities for more granular control:

- **Agent Execute Activity**: Direct agent execution at the activity level for custom workflow integration
- **Streaming Monitor Activity**: Real-time monitoring of streaming events for debugging and observability

See the activity reference documentation:
- [`awa-execute-agent`](/reference/activity/agent-execute.md)
- [`streaming-monitor-activity`](/reference/activity/streaming-monitor-activity.md)

## How It Works

### Agent Execution Flow

1. **Configuration**: Provide agent configuration including provider, mode, and prompt
2. **Initialization**: AWA initializes the specified agent with provided settings
3. **Execution**: Agent processes the prompt or command file
4. **Result**: Structured output is returned with execution status and results

### Isolated Execution Flow

1. **Environment Setup**: Create isolated environment (git worktree for ACT mode, temporary directory for ANALYZE mode)
2. **Agent Execution**: Run agent in the isolated environment with complete separation from source
3. **Output Processing**:
   - **ACT Mode**: Commit changes and merge back to source branch
   - **ANALYZE Mode**: Copy analysis outputs to source repository
4. **Cleanup**: Remove isolated environment and temporary resources

## MCP Integration

AWA agents support [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) integration, enabling agents to access additional tools and capabilities:

- **Tool Access**: Agents can use MCP-compatible tools for enhanced functionality
- **Configurable**: Control which tools agents can access through MCP server configuration
- **Secure**: Tool access is controlled and auditable

## Getting Started

To start using agents in your workflows:

1. **Install Agent Providers**: Choose and install the agent providers you want to use from the [agent installation guide](/installation/agents/overview.md)
2. **Configure Authentication**: Set up API keys and credentials for your chosen providers
3. **Define Agent Configuration**: Specify agent mode, provider, and execution parameters
4. **Execute Workflows**: Use agent workflows in your applications with appropriate isolation settings

For hands-on examples and advanced usage patterns, explore the [cookbook recipes](/cookbook/) that demonstrate agent integration in real-world scenarios.
