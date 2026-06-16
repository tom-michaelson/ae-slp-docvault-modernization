# `awa-invoke-mcp-tool`

Temporal Activity that invokes an MCP tool programmatically using MCPConfig.

## Parameters

| Name         | Type             | Description                                                                                                                                                                                                                                                                                                                                |
| ------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `mcp_config` | `dict[str, Any]` | MCP configuration dictionary containing server definitions. <br/> Format: <br/> `json <br/> { <br/>   "mcpServers": { <br/>     "server_name": { <br/>       "url": "http://127.0.0.1:9000/mcp", <br/>       "transport": "streamable-http", <br/>       "env": {"EXAMPLE_ENV_VAR": "example_value"} <br/>     } <br/>   } <br/> } <br/> ` |
| `tool_name`  | `str`            | The name of the MCP tool to invoke (can include server prefix if multiple servers).                                                                                                                                                                                                                                                        |
| `parameters` | `dict[str, Any]` | Dictionary of parameters to pass to the tool.                                                                                                                                                                                                                                                                                              |

## Returns

| Type  | Description                            |
| :---- | :------------------------------------- |
| `Any` | The result of the MCP tool invocation. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from typing import Any, Dict

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, mcp_config: Dict[str, Any], tool_name: str, parameters: Dict[str, Any]) -> Any:
        return await workflow.execute_activity(
            "invoke_mcp_tool",
            args=[mcp_config, tool_name, parameters],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { invoke_mcp_tool } = proxyActivities<typeof activities>({
  startToCloseTimeout: "1 minute",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  mcpConfig: Record<string, any>,
  toolName: string,
  parameters: Record<string, any>
): Promise<any> {
  return await invoke_mcp_tool(mcpConfig, toolName, parameters);
}
```

```csharp [C#]
using Temporalio.Workflows;
using System.Collections.Generic;
using System.Threading.Tasks;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<object> RunAsync(Dictionary<string, object> mcpConfig, string toolName, Dictionary<string, object> parameters)
    {
        return await Workflow.ExecuteActivityAsync<object>(
            "invoke_mcp_tool",
            new object[] { mcpConfig, toolName, parameters },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(60)
            }
        );
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;
import java.util.Map;

// Assumes a workflow interface, e.g., MyWorkflow
public class MyWorkflowImpl implements MyWorkflow {
    // Assumes an activity interface MyActivities with an invokeMcpTool method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public Object run(Map<String, Object> mcpConfig, String toolName, Map<String, Object> parameters) {
        return activities.invokeMcpTool(mcpConfig, toolName, parameters);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, mcpConfig map[string]interface{}, toolName string, parameters map[string]interface{}) (interface{}, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result interface{}
	err := workflow.ExecuteActivity(ctx, "invoke_mcp_tool", mcpConfig, toolName, parameters).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(array $mcpConfig, string $toolName, array $parameters): \Generator
    {
        return yield Workflow::executeActivity(
            'invoke_mcp_tool',
            [$mcpConfig, $toolName, $parameters],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
    }
}
```

:::
