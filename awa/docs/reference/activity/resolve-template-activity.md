# `awa-resolve-template`

Resolves a Jinja2 template string with application context.

This activity renders a given Jinja2 template string. It provides the application
configuration under the `awa.config` object in the template context. It also
adds a custom `env` filter to resolve environment variables, e.g., `{{ 'MY_VAR' | env }}`.

## Parameters

| Name           | Type  | Description                            |
| -------------- | ----- | -------------------------------------- |
| `template_str` | `str` | The Jinja2 template string to resolve. |

## Returns

| Type  | Description          |
| :---- | :------------------- |
| `str` | The resolved string. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, template: str) -> str:
        return await workflow.execute_activity(
            "resolve_template_activity",
            args=[template],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { resolve_template_activity } = proxyActivities<typeof activities>({
  startToCloseTimeout: "1 minute",
  taskQueue: "awa_default",
});

export async function myWorkflow(template: string): Promise<string> {
  return await resolve_template_activity(template);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(string template)
    {
        return await Workflow.ExecuteActivityAsync<string>(
            "resolve_template_activity",
            new object[] { template },
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
    // Assumes an interface MyActivities with a resolveTemplateActivity method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public String run(String template) {
        return activities.resolveTemplateActivity(template);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, template string) (string, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

    var result string
	err := workflow.ExecuteActivity(ctx, "resolve_template_activity", template).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $template): \Generator
    {
        return yield Workflow::executeActivity(
            'resolve_template_activity',
            [$template],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
    }
}
```

:::
