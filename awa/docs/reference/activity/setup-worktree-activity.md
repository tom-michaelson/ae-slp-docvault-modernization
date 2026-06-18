# `awa-setup-worktree`

Create a git worktree for isolated agent execution.

Always creates a temporary branch for the worktree to avoid conflicts,
regardless of whether the source branch exists or is checked out elsewhere.

## Parameters

| Name               | Type  | Description                             |
| :----------------- | :---- | :-------------------------------------- |
| `source_directory` | `str` | Path to the source git repository       |
| `source_branch`    | `str` | Branch name to eventually merge back to |

## Returns

| Type                             | Description                                                   |
| :------------------------------- | :------------------------------------------------------------ |
| `IsolatedAgentEnvironmentResult` | Result object with success status and environment information |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, source_directory: str, source_branch: str):
        return await workflow.execute_activity(
            "setup_worktree_activity",
            args=[source_directory, source_branch],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(minutes=5)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { setup_worktree_activity } = proxyActivities<typeof activities>({
  startToCloseTimeout: "5 minutes",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  sourceDirectory: string,
  sourceBranch: string
): Promise<any> {
  return await setup_worktree_activity(sourceDirectory, sourceBranch);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<object> RunAsync(string sourceDirectory, string sourceBranch)
    {
        return await Workflow.ExecuteActivityAsync<object>(
            "setup_worktree_activity",
            new object[] { sourceDirectory, sourceBranch },
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
    public Object run(String sourceDirectory, String sourceBranch) {
        return activities.setupWorktreeActivity(sourceDirectory, sourceBranch);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, sourceDirectory string, sourceBranch string) (interface{}, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Minute * 5,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result interface{}
	err := workflow.ExecuteActivity(ctx, "setup_worktree_activity", sourceDirectory, sourceBranch).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $sourceDirectory, string $sourceBranch): \Generator
    {
        return yield Workflow::executeActivity(
            'setup_worktree_activity',
            [$sourceDirectory, $sourceBranch],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(300)
        );
    }
}
```

:::
