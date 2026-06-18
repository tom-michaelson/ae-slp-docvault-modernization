# `awa-transform`

Execute a BAML-defined transformation using an LLM.

This activity invokes a specified BAML function to perform a transformation on the
input data. It can operate with pre-existing BAML functions or generate a BAML client
dynamically if `baml_content` is provided in the parameters. The transformation is
executed using the configured LLM.

## Parameters

The activity accepts a `TransformParams` object with the following fields:

| Name                 | Type                        | Required | Description                                                                                   |
| :------------------- | :-------------------------- | :------- | :-------------------------------------------------------------------------------------------- |
| `baml_function_name` | `str`                       | Yes      | The name of the BAML function to execute                                                      |
| `request`            | `Any`                       | Yes      | The request object/data to pass to the BAML function                                         |
| `baml_content`       | `str \| None`               | No       | Optional BAML function definition content (if not using existing BAML files)                 |
| `model_name`         | `str \| None`               | No       | Optional model name override                                                                  |
| `inputs`             | `list[InputParams] \| None` | No       | Optional list of input files to read and include in the request                               |
| `images`             | `list[BamlImageInputParams] \| None` | No | Optional list of images to include in the request                                             |
| `timeout_seconds`    | `int \| None`               | No       | Timeout for the BAML execution (default: 120 seconds)                                        |
| `baml_src_dir`       | `str \| None`               | No       | Optional BAML source directory (usually auto-generated)                                      |

**Note**: The `output_path` and `output_json_path` parameters are handled by the Transform workflow, not directly by this activity. This activity only executes the BAML function and returns the raw response.

## Returns

| Type   | Description                                                     |
| :----- | :-------------------------------------------------------------- |
| `dict` | A dictionary containing the transformation result from the LLM. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.sdk.models.transform_params import TransformParams

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, params: TransformParams) -> dict:
        return await workflow.execute_activity(
            "awa-transform",
            args=[params],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=params.timeout_seconds or 60)
        )
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

// Assuming TransformParams is defined as an interface in TypeScript
interface TransformParams {
  model_name?: string;
  baml_function_name: string;
  baml_content?: string;
  request: any;
  timeout_seconds?: number;
}

const { "awa-transform": transform } = proxyActivities<typeof activities>({
  startToCloseTimeout: "1 minute", // This might be dynamic based on params
  taskQueue: "awa_default",
});

export async function myWorkflow(
  params: TransformParams
): Promise<Record<string, any>> {
  return await transform(params);
}
```

```csharp [C#]
using Temporalio.Workflows;
using System.Threading.Tasks;
using System.Collections.Generic;

// Assuming TransformParams is defined as a class in C#
public class TransformParams
{
    public string? ModelName { get; set; }
    public required string BamlFunctionName { get; set; }
    public string? BamlContent { get; set; }
    public object? Request { get; set; }
    public int? TimeoutSeconds { get; set; }
}

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<Dictionary<string, object>> RunAsync(TransformParams params)
    {
        return await Workflow.ExecuteActivityAsync<Dictionary<string, object>>(
            "awa-transform",
            new object[] { params },
            new() {
                TaskQueue = "awa_default",
                StartToCloseTimeout = TimeSpan.FromSeconds(params.TimeoutSeconds ?? 60)
            }
        );
    }
}
```

```java [Java]
import io.temporal.workflow.Workflow;
import io.temporal.activity.ActivityOptions;
import java.time.Duration;
import java.util.Map;

// Assuming TransformParams is a POJO
public class TransformParams {
    public String modelName;
    public String bamlFunctionName;
    public String bamlContent;
    public Object request;
    public Integer timeoutSeconds;
}

public class MyWorkflowImpl implements MyWorkflow {
    // Assumes an interface MyActivities with a transformActivity method
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60)) // May need to be dynamic
            .build());

    @Override
    public Map<String, Object> run(TransformParams params) {
        return activities.transformActivity(params);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

// Assuming TransformParams is a struct in Go
type TransformParams struct {
	ModelName        *string
	BamlFunctionName string
	BamlContent      *string
	Request          interface{}
	TimeoutSeconds   *int
}

func MyWorkflow(ctx workflow.Context, params TransformParams) (map[string]interface{}, error) {
    timeout := time.Second * 60
    if params.TimeoutSeconds != nil {
        timeout = time.Second * time.Duration(*params.TimeoutSeconds)
    }
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: timeout,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

    var result map[string]interface{}
	err := workflow.ExecuteActivity(ctx, "awa-transform", params).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

// Assuming TransformParams is a class in PHP
class TransformParams {
    public ?string $model_name;
    public string $baml_function_name;
    public ?string $baml_content;
    public $request;
    public ?int $timeout_seconds;
}

class MyWorkflow implements MyWorkflowInterface
{
    public function run(TransformParams $params): \Generator
    {
        $timeout = $params->timeout_seconds ?? 60;
        return yield Workflow::executeActivity(
            'awa-transform',
            [$params],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout($timeout)
        );
    }
}
```

:::
