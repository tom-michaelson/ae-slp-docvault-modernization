# `awa-write-file`

Writes string content to a file at a specified path.

This function uses `fsspec` to open and write to a file, which allows it to
handle various file systems. If the file already exists, its content will
be overwritten. If the file does not exist, it will be created.

## Parameters

| Name      | Type  | Description                                   |
| --------- | ----- | --------------------------------------------- |
| `path`    | `str` | A string representing the file path or URI.   |
| `content` | `str` | The string content to be written to the file. |

## Returns

| Type   | Description                            |
| :----- | :------------------------------------- |
| `None` | This activity does not return a value. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, path: str, content: str) -> None:
        await workflow.execute_activity(
            "awa-write-file",
            args=[path, content],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { "awa-write-file": writeFile } = proxyActivities<typeof activities>({
  startToCloseTimeout: "1 minute",
  taskQueue: "awa_default",
});

export async function myWorkflow(path: string, content: string): Promise<void> {
  await writeFile(path, content);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task RunAsync(string path, string content)
    {
        await Workflow.ExecuteActivityAsync(
            "awa-write-file",
            new object[] { path, content },
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

public class MyWorkflowImpl implements MyWorkflow {
    // Assumes an interface MyActivities with a writeFile method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public void run(String path, String content) {
        activities.writeFile(path, content);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, path string, content string) error {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	return workflow.ExecuteActivity(ctx, "awa-write-file", path, content).Get(ctx, nil)
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $path, string $content): \Generator
    {
        yield Workflow::executeActivity(
            'awa-write-file',
            [$path, $content],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
    }
}
```

:::
