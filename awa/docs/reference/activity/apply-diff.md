# `awa-apply-diff`

Apply a diff to files.

This activity applies a diff in a custom format to files. The diff format is
parsed by the diff_utilities module.

## Parameters

| Name        | Type  | Description                                                                |
| ----------- | ----- | -------------------------------------------------------------------------- |
| `diff_text` | `str` | A diff in a custom format that can be parsed by the diff_utilities module. |

## Returns

| Type   | Description                                                 |
| :----- | :---------------------------------------------------------- |
| `bool` | True if the diff was applied successfully, False otherwise. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, diff_text: str) -> bool:
        return await workflow.execute_activity(
            "awa-apply-diff",
            args=[diff_text],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { "awa-apply-diff": applyDiff } = proxyActivities<typeof activities>({
  startToCloseTimeout: "1 minute",
  taskQueue: "awa_default",
});

export async function myWorkflow(diffText: string): Promise<boolean> {
  return await applyDiff(diffText);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<bool> RunAsync(string diffText)
    {
        return await Workflow.ExecuteActivityAsync<bool>(
            "awa-apply-diff",
            new object[] { diffText },
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

// Assumes a workflow interface, e.g., MyWorkflow
public class MyWorkflowImpl implements MyWorkflow {
    // Assumes an activity interface MyActivities with an applyDiff method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public boolean run(String diffText) {
        return activities.applyDiff(diffText);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, diffText string) (bool, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result bool
	err := workflow.ExecuteActivity(ctx, "awa-apply-diff", diffText).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $diffText): \Generator
    {
        return yield Workflow::executeActivity(
            'awa-apply-diff',
            [$diffText],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
    }
}
```

:::
