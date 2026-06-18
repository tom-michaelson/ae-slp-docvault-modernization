# `sample_activity`

Process a message string by adding a 'Test: ' prefix.

This activity takes a message string as input, adds a "Test: " prefix to it, and returns the modified message. It serves as a basic example of how to structure and implement a Temporal activity in AWA.

## Parameters

| Name      | Type  | Description                               |
| :-------- | :---- | :---------------------------------------- |
| `message` | `str` | The input message string to be processed. |

## Returns

| Type  | Description                                        |
| :---- | :------------------------------------------------- |
| `str` | A string with "Test: " prefixed to the input message. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, message: str) -> str:
        result = await workflow.execute_activity(
            "sample_activity",
            args=[message],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
        return result
```

```typescript [TypeScript]
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { sample_activity } = proxyActivities<typeof activities>({
  startToCloseTimeout: '1 minute',
  taskQueue: 'awa_default'
});

export async function myWorkflow(message: string): Promise<string> {
  const result = await sample_activity(message);
  return result;
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(string message)
    {
        var result = await Workflow.ExecuteActivityAsync<string>(
            "sample_activity",
            new object[] { message },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(60)
            }
        );
        return result;
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;

public class MyWorkflowImpl implements MyWorkflow {
    // Assumes an interface MyActivities with a sampleActivity method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public String run(String message) {
        return activities.sampleActivity(message);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, message string) (string, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result string
	err := workflow.ExecuteActivity(ctx, "sample_activity", message).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $message): \Generator
    {
        $result = yield Workflow::executeActivity(
            'sample_activity',
            [$message],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
        return $result;
    }
}
```

:::
