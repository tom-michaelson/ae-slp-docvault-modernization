# `awa-execute-agent`

Workflow for executing AI agents with configurable prompts and settings.

This workflow provides a high-level interface for agent execution, supporting
both direct prompt execution and dynamic prompt building from templates.
It handles agent configuration, prompt preparation, and result processing.

## Parameters

| Name           | Type                 | Description                                                                                               |
| :------------- | :------------------- | :-------------------------------------------------------------------------------------------------------- |
| `agent_config` | `AgentConfiguration` | Configuration object containing agent settings including mode, provider, prompt, and execution parameters |

### AgentConfiguration Fields

| Name                  | Type                        | Description                                                             |
| :-------------------- | :-------------------------- | :---------------------------------------------------------------------- |
| `mode`                | `AgentModeEnum`             | The execution mode for the agent (e.g., ACT, ANALYZE)                   |
| `provider`            | `AgentProviderEnum \| str`  | The AI provider to use (e.g., CLAUDE, GOOSE, CODEX)                     |
| `prompt`              | `str \| None`               | Direct prompt text for the agent                                        |
| `build_prompt_params` | `BuildPromptParams \| None` | Parameters for dynamic prompt building (mutually exclusive with prompt) |
| `command_file_path`   | `str \| None`               | Path to command file for certain agent modes                            |
| `working_directory`   | `str \| None`               | Working directory for agent execution                                   |
| `mcp`                 | `McpServer \| None`         | MCP server configuration for tool access                                |
| `initialize`          | `bool \| None`              | Whether to initialize the agent environment                             |
| `timeout_seconds`     | `int \| None`               | Custom timeout for agent execution                                      |
| `output_schema`       | `str \| None`               | Schema for validating agent output (not yet implemented)                |

## Returns

| Type  | Description                                                                        |
| :---- | :--------------------------------------------------------------------------------- |
| `Any` | The result returned from the agent execution, format depends on the agent and task |

## Usage

The following examples show how to start the `awa-execute-agent` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.activities.agent_modes.models.agent_configuration import AgentConfiguration
from awa.core.activities.agent_modes.models.agent_mode_enum import AgentModeEnum
from awa.core.activities.agent_modes.models.agent_provider_enum import AgentProviderEnum

# Configure the agent
agent_config = AgentConfiguration(
    mode=AgentModeEnum.ACT,
    provider=AgentProviderEnum.CLAUDE,
    prompt="Review this code and suggest improvements",
    working_directory="/path/to/project"
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-execute-agent",
    agent_config
)

print(result)  # Agent execution results
```

```typescript [TypeScript]
import { executeChild } from "@temporalio/workflow";

// Configure the agent
const agentConfig = {
  mode: "ACT",
  provider: "CLAUDE",
  prompt: "Review this code and suggest improvements",
  working_directory: "/path/to/project",
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-execute-agent", {
  args: [agentConfig],
});

console.log(result); // Agent execution results
```

```csharp [.NET]
using Temporalio.Workflows;

// Configure the agent
var agentConfig = new AgentConfiguration
{
    Mode = AgentModeEnum.ACT,
    Provider = AgentProviderEnum.CLAUDE,
    Prompt = "Review this code and suggest improvements",
    WorkingDirectory = "/path/to/project"
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync("awa-execute-agent", agentConfig);

Console.WriteLine(result); // Agent execution results
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.workflow.ChildWorkflowOptions;

// Configure the agent
AgentConfiguration agentConfig = new AgentConfiguration.Builder()
    .setMode(AgentModeEnum.ACT)
    .setProvider(AgentProviderEnum.CLAUDE)
    .setPrompt("Review this code and suggest improvements")
    .setWorkingDirectory("/path/to/project")
    .build();

// Execute the child workflow and wait for completion
Object result = Workflow.executeChildWorkflow("awa-execute-agent", agentConfig);

System.out.println(result); // Agent execution results
```

```go [Go]
import (
    "go.temporal.io/sdk/workflow"
)

// Configure the agent
agentConfig := AgentConfiguration{
    Mode:             "ACT",
    Provider:         "CLAUDE",
    Prompt:           "Review this code and suggest improvements",
    WorkingDirectory: "/path/to/project",
}

// Execute the child workflow and wait for completion
var result interface{}
err := workflow.ExecuteChildWorkflow(ctx, "awa-execute-agent", agentConfig).Get(ctx, &result)
if err != nil {
    return nil, err
}
fmt.Println(result) // Agent execution results
```

```php [PHP]
use Temporal\Workflow;

// Configure the agent
$agentConfig = [
    'mode' => 'ACT',
    'provider' => 'CLAUDE',
    'prompt' => 'Review this code and suggest improvements',
    'working_directory' => '/path/to/project'
];

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-execute-agent',
    [$agentConfig]
);

echo $result; // Agent execution results
```

:::
