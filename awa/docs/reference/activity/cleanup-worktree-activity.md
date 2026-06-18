# `cleanup_isolated_environment_activity`

Clean up an isolated agent environment (git worktree or temporary directory).

This activity removes the isolated environment directory, cleans up any git worktree references,
and deletes any temporary branches that were created for the environment.

## Parameters

| Name               | Type                           | Description                                            |
| :----------------- | :----------------------------- | :----------------------------------------------------- |
| `environment_info` | `IsolatedAgentEnvironmentInfo` | Information about the isolated environment to clean up |

## Returns

| Type                             | Description                       |
| :------------------------------- | :-------------------------------- |
| `IsolatedAgentEnvironmentResult` | Result object with success status |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.core.activities.agent_modes.models.isolated_agent_models import IsolatedAgentEnvironmentInfo
from awa.core.activities.agent_modes.models.agent_configuration import AgentConfiguration

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, environment_info: IsolatedAgentEnvironmentInfo, agent_config: AgentConfiguration):
        return await workflow.execute_activity(
            "cleanup_isolated_environment_activity",
            args=[environment_info, agent_config],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(minutes=5)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { cleanup_isolated_environment_activity } = proxyActivities<
  typeof activities
>({
  startToCloseTimeout: "5 minutes",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  environmentInfo: any,
  agentConfig: any
): Promise<any> {
  return await cleanup_isolated_environment_activity(
    environmentInfo,
    agentConfig
  );
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<object> RunAsync(object environmentInfo, object agentConfig)
    {
        return await Workflow.ExecuteActivityAsync<object>(
            "cleanup_isolated_environment_activity",
            new object[] { environmentInfo, agentConfig },
            new() {
                TaskQueue = "awa_default",
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

public class MyWorkflowImpl implements MyWorkflow {
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofMinutes(5))
            .build());

    @Override
    public Object run(Object environmentInfo, Object agentConfig) {
        return activities.cleanupIsolatedEnvironmentActivity(environmentInfo, agentConfig);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, environmentInfo interface{}, agentConfig interface{}) (interface{}, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result interface{}
	err := workflow.ExecuteActivity(ctx, "cleanup_isolated_environment_activity", environmentInfo, agentConfig).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run($environmentInfo, $agentConfig): \Generator
    {
        return yield Workflow::executeActivity(
            'cleanup_isolated_environment_activity',
            [$environmentInfo, $agentConfig],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(300)
        );
    }
}
```

:::
