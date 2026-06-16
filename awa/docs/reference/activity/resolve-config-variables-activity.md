# `awa-resolve-config-variables`

Resolves environment variable placeholders in configuration objects.

This activity recursively processes nested configuration objects (dictionaries, lists, and strings) to expand environment variable placeholders. It handles both `${VAR_NAME}` and `$VAR` patterns in strings and raises an error if any required environment variables are not found.

## Parameters

| Name            | Type  | Description                                                                         |
| --------------- | ----- | ----------------------------------------------------------------------------------- |
| `config_object` | `Any` | The configuration object to process. Can be a dict, list, string, or any other type. |

## Returns

| Type  | Description                                                           |
| :---- | :-------------------------------------------------------------------- |
| `Any` | The configuration object with environment variable placeholders expanded. |

## Behavior

- **Dictionaries**: Recursively processes all values
- **Lists**: Recursively processes all items
- **Strings**: Expands `${VAR_NAME}` and `$VAR` environment variable patterns
- **Other types**: Returned unchanged

## Exceptions

Raises `ValueError` if any required environment variables referenced by `${VAR_NAME}` patterns are not set.

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        return await workflow.execute_activity(
            "awa-resolve-config-variables",
            args=[config],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=30)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { "awa-resolve-config-variables": resolveConfigVariables } = proxyActivities<typeof activities>({
  startToCloseTimeout: "30 seconds",
  taskQueue: "awa_default",
});

export async function myWorkflow(config: any): Promise<any> {
  return await resolveConfigVariables(config);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<object> RunAsync(object config)
    {
        return await Workflow.ExecuteActivityAsync<object>(
            "awa-resolve-config-variables",
            new object[] { config },
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
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(30))
            .build());

    @Override
    public Object run(Object config) {
        return activities.resolveConfigVariablesActivity(config);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, config interface{}) (interface{}, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 30,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	var result interface{}
	err := workflow.ExecuteActivity(ctx, "awa-resolve-config-variables", config).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run($config): \Generator
    {
        return yield Workflow::executeActivity(
            'awa-resolve-config-variables',
            [$config],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(30)
        );
    }
}
```

:::

## Example

Given the following environment variables:
- `DATABASE_HOST=localhost`
- `DATABASE_PORT=5432`

Input configuration:
```python
config = {
    "database": {
        "host": "${DATABASE_HOST}",
        "port": "$DATABASE_PORT",
        "url": "postgres://${DATABASE_HOST}:${DATABASE_PORT}/mydb"
    },
    "features": ["logging", "${FEATURE_FLAG}"]  # Will raise error if FEATURE_FLAG not set
}
```

Output after processing:
```python
{
    "database": {
        "host": "localhost",
        "port": "5432",
        "url": "postgres://localhost:5432/mydb"
    },
    "features": ["logging", "some_feature_value"]
}
```
