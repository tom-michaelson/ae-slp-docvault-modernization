# `awa-list-directory`

List all files in a directory, optionally ignoring based on .gitignore.

This function recursively finds all files in the given source path.
If an ignore file is provided, it filters the file list based on
.gitignore-style patterns. It returns a flat list of full file paths.

The returned paths are suitable for use with other file activities like
`read_file` or `write_file`.

## Parameters

| Name               | Type          | Description                                       |
| ------------------ | ------------- | ------------------------------------------------- |
| `source_path`      | `str`         | The path or URI of the source directory.          |
| `ignore_file_path` | `str \| None` | Optional path to a file with .gitignore patterns. |

## Returns

| Type        | Description                                     |
| :---------- | :---------------------------------------------- |
| `list[str]` | A list of full paths to files in the directory. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, source: str, ignore_path: str | None) -> list[str]:
        return await workflow.execute_activity(
            "list_directory",
            args=[source, ignore_path],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=120)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { list_directory } = proxyActivities<typeof activities>({
  startToCloseTimeout: "2 minutes",
  taskQueue: "awa_default",
});

export async function myWorkflow(
  source: str,
  ignorePath: string | null
): Promise<string[]> {
  return await list_directory(source, ignorePath);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<List<string>> RunAsync(string source, string? ignorePath)
    {
        return await Workflow.ExecuteActivityAsync<List<string>>(
            "list_directory",
            new object?[] { source, ignorePath },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(120)
            }
        );
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;
import java.util.List;

public class MyWorkflowImpl implements MyWorkflow {
    // Assumes an interface MyActivities with a listDirectory method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(120))
            .build());

    @Override
    public List<String> run(String source, String ignorePath) {
        return activities.listDirectory(source, ignorePath);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, source string, ignorePath *string) ([]string, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 120,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result []string
	err := workflow.ExecuteActivity(ctx, "list_directory", source, ignorePath).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $source, ?string $ignorePath): \Generator
    {
        $result = yield Workflow::executeActivity(
            'list_directory',
            [$source, $ignorePath],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(120)
        );
        return $result;
    }
}
```

:::
