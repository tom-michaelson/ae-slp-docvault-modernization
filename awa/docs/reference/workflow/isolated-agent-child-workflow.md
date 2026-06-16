# `IsolatedAgentChildWorkflow`

Workflow for executing agents in isolated environments.

This workflow implements complete separation of concerns for safe agent execution:

1. **Environment Setup**: Creates an isolated environment (git worktree for ACT mode, temporary directory for ANALYZE mode)
2. **Agent Execution**: Runs the agent in the isolated environment without knowledge of the environment context
3. **Output Handling**: Processes results based on the agent mode (ACT or ANALYZE)
4. **Cleanup**: Removes the isolated environment and any temporary resources

The agent receives a pre-configured environment and executes normally, with complete isolation from the source repository.

## Agent Modes

The workflow supports two distinct execution modes:

### ACT Mode

- **Purpose**: Make direct changes to the codebase
- **Behavior**: Agent can modify, create, or delete files in the isolated environment (git worktree)
- **Output**: Changes are automatically committed and merged back to the source branch
- **Use Case**: Code modifications, refactoring, bug fixes

### ANALYZE Mode

- **Purpose**: Generate analysis outputs without modifying the source code
- **Behavior**: Agent writes outputs to a configurable output directory in the isolated environment (defaults to `awa-agent-output/`)
- **Output**: Contents of the output directory are copied to the source repository
- **Use Case**: Code analysis, documentation generation, audit reports

## Parameters

| Name     | Type                  | Description                                                            |
| :------- | :-------------------- | :--------------------------------------------------------------------- |
| `params` | `IsolatedAgentParams` | Parameters containing source repo, agent config, and execution options |

### `IsolatedAgentParams` Structure

| Field                             | Type                 | Description                                                                            |
| :-------------------------------- | :------------------- | :------------------------------------------------------------------------------------- |
| `source_directory`                | `str`                | Source directory path (can be Git repo or regular directory)                           |
| `source_branch`                   | `str`                | Source branch name (only used for Git repositories)                                    |
| `agent_config`                    | `AgentConfiguration` | Agent configuration for execution including mode, provider, prompt, and other settings |
| `agent_execution_timeout_minutes` | `int`                | Timeout in minutes for agent execution. Defaults to 10 minutes                         |
| `output_directory`                | `str`                | Directory name for agent outputs in analyze mode. Defaults to "awa-agent-output"       |

### `AgentConfiguration` Structure

| Field               | Type                       | Description                                                                            |
| :------------------ | :------------------------- | :------------------------------------------------------------------------------------- |
| `mode`              | `AgentModeEnum`            | Agent execution mode: `ACT` or `ANALYZE`                                               |
| `provider`          | `AgentProviderEnum \| str` | Agent provider: `CLAUDE`, `GOOSE`, `CODEX`, `Q`, or custom string                      |
| `prompt`            | `str \| None`              | Prompt or instructions for the agent                                                   |
| `command_file_path` | `str \| None`              | Path to a file containing commands to execute                                          |
| `working_directory` | `str \| None`              | Working directory for agent execution (automatically set to isolated environment path) |
| `mcp`               | `McpServer \| None`        | MCP (Model Context Protocol) server configuration                                      |
| `initialize`        | `bool \| None`             | Whether to initialize the agent environment (defaults to True)                         |

## Returns

| Type                | Description                |
| :------------------ | :------------------------- |
| `TaskResponseModel` | The agent execution result |

### `TaskResponseModel` Structure

| Field       | Type          | Description                                                |
| :---------- | :------------ | :--------------------------------------------------------- |
| `status`    | `str`         | Status of the task execution (e.g., "completed", "failed") |
| `reason`    | `str`         | Additional context or reason for the status                |
| `output`    | `str`         | Output from the agent execution                            |
| `exception` | `str \| None` | Exception details if the task failed                       |

## Usage

The following examples show how to start the `IsolatedAgentChildWorkflow` as a child workflow.

::: code-group

```python [Python - ACT Mode]
from awa.core.activities.agent_modes.models.isolated_agent_models import IsolatedAgentParams
from awa.core.activities.agent_modes.models.agent_configuration import AgentConfiguration
from awa.core.activities.agent_modes.models.agent_mode_enum import AgentModeEnum
from awa.core.activities.agent_modes.models.agent_provider_enum import AgentProviderEnum

# ACT Mode: Make direct changes to the codebase
params = IsolatedAgentParams(
    source_directory="/path/to/repository",
    source_branch="main",
    agent_config=AgentConfiguration(
        mode=AgentModeEnum.ACT,
        provider=AgentProviderEnum.CLAUDE,
        prompt="Fix the authentication bug in the user service",
        initialize=True
    ),

    agent_execution_timeout_minutes=20
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "IsolatedAgentChildWorkflow",
    params
)

print(f"Status: {result.status}")
print(f"Changes merged: {result.output}")
```

```python [Python - ANALYZE Mode]
from awa.core.activities.agent_modes.models.isolated_agent_models import IsolatedAgentParams
from awa.core.activities.agent_modes.models.agent_configuration import AgentConfiguration
from awa.core.activities.agent_modes.models.agent_mode_enum import AgentModeEnum
from awa.core.activities.agent_modes.models.agent_provider_enum import AgentProviderEnum

# ANALYZE Mode: Generate analysis outputs
params = IsolatedAgentParams(
    source_directory="/path/to/repository",
    source_branch="main",
    agent_config=AgentConfiguration(
        mode=AgentModeEnum.ANALYZE,
        provider=AgentProviderEnum.CLAUDE,
        prompt="Analyze the codebase for security vulnerabilities and generate a report",
        initialize=True
    ),

    agent_execution_timeout_minutes=30
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "IsolatedAgentChildWorkflow",
    params
)

print(f"Status: {result.status}")
print(f"Analysis complete: {result.output}")
# Check the output directory for generated reports (defaults to awa-agent-output/)
```

```typescript [TypeScript - ACT Mode]
import { executeChild } from "@temporalio/workflow";

// ACT Mode: Make direct changes to the codebase
const params = {
  sourceDirectory: "/path/to/repository",
  sourceBranch: "main",
  agentConfig: {
    mode: "act",
    provider: "claude",
    prompt: "Fix the authentication bug in the user service",
    initialize: true,
  },

  agentExecutionTimeoutMinutes: 20,
};

// Execute the child workflow and wait for completion
const result = await executeChild(IsolatedAgentChildWorkflow, {
  args: [params],
});

console.log(`Status: ${result.status}`);
console.log(`Changes merged: ${result.output}`);
```

```typescript [TypeScript - ANALYZE Mode]
import { executeChild } from "@temporalio/workflow";

// ANALYZE Mode: Generate analysis outputs
const params = {
  sourceDirectory: "/path/to/repository",
  sourceBranch: "main",
  agentConfig: {
    mode: "analyze",
    provider: "claude",
    prompt:
      "Analyze the codebase for security vulnerabilities and generate a report",
    initialize: true,
  },

  agentExecutionTimeoutMinutes: 30,
};

// Execute the child workflow and wait for completion
const result = await executeChild(IsolatedAgentChildWorkflow, {
  args: [params],
});

console.log(`Status: ${result.status}`);
console.log(`Analysis complete: ${result.output}`);
// Check the output directory for generated reports (defaults to awa-agent-output/)
```

```csharp [.NET - ACT Mode]
using Temporalio.Workflows;

// ACT Mode: Make direct changes to the codebase
var parameters = new IsolatedAgentParams
{
    SourceDirectory = "/path/to/repository",
    SourceBranch = "main",
    AgentConfig = new AgentConfiguration
    {
        Mode = AgentModeEnum.Act,
        Provider = AgentProviderEnum.Claude,
        Prompt = "Fix the authentication bug in the user service",
        Initialize = true
    },

    AgentExecutionTimeoutMinutes = 20
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync<IsolatedAgentChildWorkflow>(parameters);

Console.WriteLine($"Status: {result.Status}");
Console.WriteLine($"Changes merged: {result.Output}");
```

```java [Java - ACT Mode]
import io.temporal.workflow.Workflow;
import io.temporal.workflow.Async;

// ACT Mode: Make direct changes to the codebase
IsolatedAgentParams params = IsolatedAgentParams.builder()
    .sourceDirectory("/path/to/repository")
    .sourceBranch("main")
    .agentConfig(AgentConfiguration.builder()
        .mode(AgentModeEnum.ACT)
        .provider(AgentProviderEnum.CLAUDE)
        .prompt("Fix the authentication bug in the user service")
        .initialize(true)
        .build())

    .agentExecutionTimeoutMinutes(20)
    .build();

// Execute the child workflow and wait for completion
IsolatedAgentChildWorkflow child = Workflow.newChildWorkflowStub(IsolatedAgentChildWorkflow.class);
TaskResponseModel result = Async.function(child::run, params);

System.out.println("Status: " + result.getStatus());
System.out.println("Changes merged: " + result.getOutput());
```

```go [Go - ACT Mode]
import (
    "context"
    "fmt"
    "go.temporal.io/sdk/workflow"
)

// ACT Mode: Make direct changes to the codebase
params := IsolatedAgentParams{
    SourceDirectory: "/path/to/repository",
    SourceBranch:    "main",
    AgentConfig: AgentConfiguration{
        Mode:       "act",
        Provider:   "claude",
        Prompt:     "Fix the authentication bug in the user service",
        Initialize: true,
    },

    AgentExecutionTimeoutMinutes:   20,
}

// Execute the child workflow and wait for completion
var isolatedAgentWorkflow IsolatedAgentChildWorkflow
var result TaskResponseModel
err := workflow.ExecuteChildWorkflow(ctx, isolatedAgentWorkflow.Run, params).Get(ctx, &result)
if err != nil {
    return TaskResponseModel{}, err
}

fmt.Printf("Status: %s\n", result.Status)
fmt.Printf("Changes merged: %s\n", result.Output)
```

```php [PHP - ACT Mode]
<?php

// ACT Mode: Make direct changes to the codebase
$params = [
    'sourceDirectory' => '/path/to/repository',
    'sourceBranch' => 'main',
    'agentConfig' => [
        'mode' => 'act',
        'provider' => 'claude',
        'prompt' => 'Fix the authentication bug in the user service',
        'initialize' => true
    ],

    'agentExecutionTimeoutMinutes' => 20
];

// Execute the child workflow and wait for completion
$child = $this->workflowClient->newChildWorkflowStub(IsolatedAgentChildWorkflow::class);
$result = $this->workflowClient->run($child, $params);

echo "Status: " . $result['status'] . "\n";
echo "Changes merged: " . $result['output'] . "\n";
```

:::

## Workflow Execution Flow

1. **Setup Phase**: Creates an isolated environment (git worktree for ACT mode, temporary directory for ANALYZE mode)
2. **Agent Execution**: Runs the configured agent in the isolated environment
3. **Output Processing**:
   - **ACT Mode**: Commits changes and merges them back to the source branch
   - **ANALYZE Mode**: Copies contents from the configurable output directory to the source repository
4. **Cleanup**: Removes the isolated environment and any temporary resources regardless of success or failure

## Error Handling

The workflow includes comprehensive error handling:

- Failed environment setup prevents agent execution
- Agent execution failures are captured in the `TaskResponseModel`
- Cleanup always occurs, even if the workflow fails
- Merge or copy failures are reported but don't prevent cleanup

## Best Practices

- **ACT Mode**: Use for code changes, refactoring, and bug fixes
- **ANALYZE Mode**: Use for generating reports, documentation, or analysis outputs
- **Timeout**: Set appropriate timeout values based on expected agent execution time
- **Source Directory**: Use absolute paths for reliable directory access
