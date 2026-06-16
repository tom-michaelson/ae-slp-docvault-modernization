# `awa-execute-agent`

Executes a task using a configured agent.

This activity initializes an agent based on the provided configuration, executes a command or prompt, and returns the result. It supports different agent providers and modes, and can be configured to use MCP tools.

## Parameters

The activity takes a single `agent_config` parameter of type `AgentConfiguration`.

### AgentConfiguration

| Name                | Type                         | Description                                                                          |
| ------------------- | ---------------------------- | ------------------------------------------------------------------------------------ |
| `mode`              | `AgentModeEnum`              | The mode of the agent (e.g., `CODEX`, `SWE_BENCH`). Defaults to `UNKNOWN`.           |
| `provider`          | `AgentProviderEnum` or `str` | The agent provider (e.g., `SWE_AGENT`, `OPEN_AGENT`). Defaults to `UNKNOWN`.         |
| `prompt`            | `str` or `None`              | A prompt to be executed by the agent.                                                |
| `command_file_path` | `str` or `None`              | The path to a command file to be executed by the agent.                              |
| `working_directory` | `str` or `None`              | The working directory for the agent execution.                                       |
| `mcp`               | `McpServer` or `None`        | Configuration for MCP (Multi-Capability-Program) tools. See `McpServer` model below. |
| `initialize`        | `bool` or `None`             | Whether to run the agent's initialization routine. Defaults to `True`.               |

### McpServer

| Name       | Type            | Description                         |
| ---------- | --------------- | ----------------------------------- |
| `mcp_json` | `str` or `None` | JSON string defining the MCP tools. |
| `allowed`  | `list[McpTool]` | A list of allowed MCP tools.        |

### McpTool

| Name     | Type        | Description                                   |
| -------- | ----------- | --------------------------------------------- |
| `server` | `str`       | The name of the MCP server.                   |
| `tools`  | `list[str]` | A list of tool names available on the server. |

## Returns

| Type                | Description                                                                                                                     |
| :------------------ | :------------------------------------------------------------------------------------------------------------------------------ |
| `TaskResponseModel` | An object containing the status of the execution (`completed` or `failed`), the output content, and an optional failure reason. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, config: AgentConfiguration) -> dict:
        return await workflow.execute_activity(
            "awa-execute-agent",
            args=[config],
            task_queue="awa_agent_operations",
            start_to_close_timeout=timedelta(seconds=300)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

// Assuming AgentConfiguration and related models are defined as interfaces
interface AgentConfiguration {
  //... fields
}

const { "awa-execute-agent": executeAgent } = proxyActivities<
  typeof activities
>({
  startToCloseTimeout: "5 minutes",
  taskQueue: "awa_agent_operations",
});

export async function myWorkflow(config: AgentConfiguration): Promise<any> {
  return await executeAgent(config);
}
```

```csharp [C#]
using Temporalio.Workflows;
using System.Threading.Tasks;

// Assuming AgentConfiguration and related models are defined as classes
public class AgentConfiguration {
    //... properties
}

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<object> RunAsync(AgentConfiguration config)
    {
        return await Workflow.ExecuteActivityAsync<object>(
            "awa-execute-agent",
            new object[] { config },
            new() {
                TaskQueue = "awa_agent_operations",
                StartToCloseTimeout = TimeSpan.FromMinutes(5)
            }
        );
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;

// Assuming AgentConfiguration and related models are POJOs
public class AgentConfiguration {
    //... fields
}

public class MyWorkflowImpl implements MyWorkflow {
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_agent_operations")
            .setStartToCloseTimeout(Duration.ofMinutes(5))
            .build());

    @Override
    public Object run(AgentConfiguration config) {
        return activities.executeAgent(config);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

// Assuming AgentConfiguration and related models are structs
type AgentConfiguration struct {
    //... fields
}

func MyWorkflow(ctx workflow.Context, config AgentConfiguration) (interface{}, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_agent_operations",
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

    var result interface{}
	err := workflow.ExecuteActivity(ctx, "awa-execute-agent", config).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

// Assuming AgentConfiguration and related models are classes
class AgentConfiguration {
    //... properties
}

class MyWorkflow implements MyWorkflowInterface
{
    public function run(AgentConfiguration $config): \Generator
    {
        return yield Workflow::executeActivity(
            'awa-execute-agent',
            [$config],
            ActivityOptions::new()
                ->withTaskQueue('awa_agent_operations')
                ->withStartToCloseTimeout(300)
        );
    }
}
```

:::
