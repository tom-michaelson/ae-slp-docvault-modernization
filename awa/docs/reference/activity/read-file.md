# `awa-read-file`

Reads the entire content of a file from a specified path.

This function uses `fsspec` to open and read a file, which allows it to
handle various file systems like local, S3, GCS, etc., based on the path's
protocol prefix.

## Parameters

| Name      | Type          | Description                                    |
| --------- | ------------- | ---------------------------------------------- |
| `path`    | `str`         | A string representing the file path or URI.    |
| `default` | `str \| None` | A string to return if the file does not exist. |

## Returns

| Type  | Description                                         |
| :---- | :-------------------------------------------------- |
| `str` | A string containing the entire content of the file. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, path: str, default_content: str | None) -> str:
        return await workflow.execute_activity(
            "read_file",
            args=[path, default_content],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
// Assuming activities are in an "activities.ts" file
import type * as activities from "./activities";

const { read_file } = proxyActivities<typeof activities>({
  startToCloseTimeout: "1 minute",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  path: string,
  defaultContent: string | null
): Promise<string> {
  return await read_file(path, defaultContent);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(string path, string? defaultContent)
    {
        return await Workflow.ExecuteActivityAsync<string>(
            "read_file",
            new object?[] { path, defaultContent },
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
    // Assumes an interface MyActivities with a readFile method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public String run(String path, String defaultContent) {
        return activities.readFile(path, defaultContent);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, path string, defaultContent *string) (string, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result string
	err := workflow.ExecuteActivity(ctx, "read_file", path, defaultContent).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $path, ?string $defaultContent): \Generator
    {
        $result = yield Workflow::executeActivity(
            'read_file',
            [$path, $defaultContent],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
        return $result;
    }
}
```

:::
