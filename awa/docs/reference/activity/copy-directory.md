# `awa-copy-directory`

Recursively copies a directory from a source to a destination.

This function uses `fsspec` to copy a directory. It determines the
filesystem (e.g., local, S3, GCS) from the protocol prefix of the
source path. The copy operation is performed within this single
filesystem. Cross-filesystem copies are not supported by this activity.

If an ignore file is provided, it will be parsed using .gitignore patterns.
Files matching these patterns will not be copied.

## Parameters

| Name               | Type          | Description                                                                                                     |
| ------------------ | ------------- | --------------------------------------------------------------------------------------------------------------- |
| `source_path`      | `str`         | The path or URI of the source directory. Must include a protocol prefix (e.g., 's3://') for remote filesystems. |
| `destination_path` | `str`         | The path or URI for the destination, which must be on the same filesystem as the source.                        |
| `ignore_file_path` | `str \| None` | Optional path to a file containing .gitignore-style patterns for files to ignore during the copy.               |

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
    async def run(self, source: str, destination: str, ignore_path: str | None) -> None:
        await workflow.execute_activity(
            "copy_directory",
            args=[source, destination, ignore_path],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=300)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { copy_directory } = proxyActivities<typeof activities>({
  startToCloseTimeout: "5 minutes",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  source: string,
  destination: string,
  ignorePath: string | null
): Promise<void> {
  await copy_directory(source, destination, ignorePath);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task RunAsync(string source, string destination, string? ignorePath)
    {
        await Workflow.ExecuteActivityAsync(
            "copy_directory",
            new object?[] { source, destination, ignorePath },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(300)
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
    // Assumes an interface MyActivities with a copyDirectory method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(300))
            .build());

    @Override
    public void run(String source, String destination, String ignorePath) {
        activities.copyDirectory(source, destination, ignorePath);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, source string, destination string, ignorePath *string) error {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 300,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	return workflow.ExecuteActivity(ctx, "copy_directory", source, destination, ignorePath).Get(ctx, nil)
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $source, string $destination, ?string $ignorePath): \Generator
    {
        yield Workflow::executeActivity(
            'copy_directory',
            [$source, $destination, $ignorePath],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(300)
        );
    }
}
```

:::
