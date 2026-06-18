# OpenAI Agents SDK (AWA)

Temporal and the OpenAI Agents SDK have an [official integration](https://temporal.io/blog/announcing-openai-agents-sdk-integration). AWA offers a thin child workflow wrapper ... TODO and AWA provides a thin wrapper child workflow so you can run Agents inside Temporal with minimal code. Use the AWA SDK helper to execute agents as a child workflow with support for MCP servers, agent handoffs, and agents-as-tools.

- **Durable by default**: Each agent step (each generation, each tool call) is executed via individual Temporal activities with retries/timeouts
- **MCP-ready**: Connect agents to external tools and systems
- **Composition**: Use handoffs and agents-as-tools patterns
- **Structured output**: Optional JSON schema validation

:::danger Python
If you are building your client Temporal worker in Python (with the Temporal Python SDK), unless you just prefer the simpler configuration model that it provides, there is no functional reason to use the AWA wrapper for the OpenAI Agents SDK. Instead, you can use the official Temporal implementation of the OpenAI Agents SDK directly as [documented here](https://temporal.io/blog/announcing-openai-agents-sdk-integration). You can still use other AWA child workflows and activities alongside your OpenAI Agents calls, its just that you don't need this specific workflow wrapper to use the OpenAI Agents SDK itself, since it natively supports Temporal.
:::

## Feature Support

Not all OpenAI Agents SDK features are supported by the Temporal integration. And not all features supported by the Temporal integration are exposed in the AWA [openai-agent workflow](/reference/workflow/openai-agent.md).

For gaps between the raw OpenAI Agents SDK and Temporal, see the [Feature Support](https://github.com/temporalio/sdk-python/tree/main/temporalio/contrib/openai_agents#feature-support) matrix in the Temporal SDK Python repository.

See the table below for major features not yet supported by the AWA wrapper:

| Feature                                                                                                                                 | Status        |
| :-------------------------------------------------------------------------------------------------------------------------------------- | :------------ |
| [Function Tools](https://openai.github.io/openai-agents-python/tools/#function-tools)                                                   | Planned       |
| [Handoffs "on_handoff" Callback](https://openai.github.io/openai-agents-python/ref/lifecycle/#agents.lifecycle.RunHooksBase.on_handoff) | Planned       |
| [Guardrails](https://openai.github.io/openai-agents-python/guardrails/)                                                                 | Planned       |
| [OpenAI Hosted Tools](https://openai.github.io/openai-agents-python/tools/#hosted-tools)                                                | Not supported |

## Quick Start

```python
from awa.client import awa_workflow
from awa.client.models import OpenAIAgentConfig

config = OpenAIAgentConfig(
    name="assistant",
    instructions="You are a helpful assistant.",
    input="Summarize the key points about Temporal and AWA.",
    model="openai/gpt-4o",
)

result = await awa_workflow.openai_agent(config)
print(result.content)
```

## MCP

Give your agent tools via MCP servers. You can use STDIO, SSE, or streamable HTTP servers. See the [MCP Server Configuration](/configuration/mcp-servers) guide for more details.

1. Define your MCP servers in an `mcp.json` or `.mcp.json` file in the root of the AWA project so that the AWA core worker can read it:

```json
{
  "servers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    }
  }
}
```

2. Reference the servers by name from your workflow input:

```python
from awa.client import awa_workflow
from awa.client.models import OpenAIAgentConfig

config = OpenAIAgentConfig(
    name="file-reader",
    instructions="Read and summarize README.md",
    input="What does this project do?",
    model="openai/gpt-4o",
    mcp_servers=["filesystem"],
)

result = await awa_workflow.openai_agent(config)
```

## Agent Handoffs

Delegate control to another agent for the final result. Use when a specialist should take over completely.

```python
from awa.client import awa_workflow
from awa.client.models import OpenAIAgentConfig, HandoffConfig

config = OpenAIAgentConfig(
    name="coordinator",
    instructions="Delegate to specialists when appropriate",
    input="Analyze this codebase",
    model="openai/gpt-4o",
    handoffs=[
        HandoffConfig(target_agent="security_analyst"),
        HandoffConfig(target_agent="performance_optimizer"),
    ],
)

result = await awa_workflow.openai_agent(config)
# Optional: inspect handoff events
for e in (result.handoff_events or []):
    print(f"Handoff: {e.from_agent} -> {e.to_agent}")
```

## Agents as Tools

Keep an orchestrator in control while calling sub-agents as tools. Use when the main agent should compose/aggregate results.

```python
from awa.client import awa_workflow
from awa.client.models import OpenAIAgentConfig, AgentToolConfig

# Define specialized agents
analyzer = OpenAIAgentConfig(name="Analyzer", instructions="Analyze data", model="openai/gpt-4o")
writer = OpenAIAgentConfig(name="Writer", instructions="Write a report", model="openai/gpt-4o")

# Orchestrator exposes tool agents
orchestrator = OpenAIAgentConfig(
    name="Orchestrator",
    instructions="Use tools to analyze then write a report",
    input="Sales data for Q3",
    model="openai/gpt-4o",
    agent_tools=[
        AgentToolConfig(target_agent=analyzer, tool_name_override="analyze_data"),
        AgentToolConfig(target_agent=writer, tool_name_override="write_report"),
    ],
)

result = await awa_workflow.openai_agent(orchestrator)
# Optional: inspect tool usage
for e in (result.agent_tool_events or []):
    print(f"Tool: {e.tool_name} -> {e.target_agent}")
```

## Reference

For API details, see the [workflow reference](/reference/workflow/openai-agent.md).
