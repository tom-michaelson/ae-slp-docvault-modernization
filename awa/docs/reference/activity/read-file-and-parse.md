# `awa-read-file-and-parse`

Reads and parses a file from a specified path, converting to markdown if supported.

This function uses MarkItDown to parse specific whitelisted document formats into markdown.

## Supported File Types

<!--@include: ../../.shared/supported-file-types.md -->

## Parameters

| Name      | Type          | Description                                    |
| --------- | ------------- | ---------------------------------------------- |
| `path`    | `str`         | A string representing the file path or URI.    |
| `default` | `str \| None` | A string to return if the file does not exist. |

## Returns

| Type  | Description                                                                               |
| :---- | :---------------------------------------------------------------------------------------- |
| `str` | A string containing the parsed content (markdown) or raw content for unsupported formats. |

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
            "awa-read-file-and-parse",
            args=[path, default_content],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=30)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
// Assuming activities are in an "activities.ts" file
import type * as activities from "./activities";

const { read_file_and_parse } = proxyActivities<typeof activities>({
  startToCloseTimeout: "30 seconds",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  path: string,
  defaultContent: string | null
): Promise<string> {
  return await read_file_and_parse(path, defaultContent);
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
            "awa-read-file-and-parse",
            new object?[] { path, defaultContent },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(30)
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
    // Assumes an interface MyActivities with a readFileAndParse method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(30))
            .build());

    @Override
    public String run(String path, String defaultContent) {
        return activities.readFileAndParse(path, defaultContent);
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
		StartToCloseTimeout: time.Second * 30,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result string
	err := workflow.ExecuteActivity(ctx, "awa-read-file-and-parse", path, defaultContent).Get(ctx, &result)
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
            'awa-read-file-and-parse',
            [$path, $defaultContent],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(30)
        );
        return $result;
    }
}
```

:::
