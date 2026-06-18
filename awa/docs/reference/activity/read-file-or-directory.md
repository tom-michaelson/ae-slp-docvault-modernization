# `awa-read-file-or-directory`

Read content from either a file or directory based on the path type.

This function dynamically determines whether the given path is a file or directory and reads accordingly. For directories, it reads all files recursively and returns their combined content using customizable join templates. For files, it reads the individual file content.

## Parameters

| Name           | Type          | Description                                                 |
| :------------- | :------------ | :---------------------------------------------------------- |
| `input_params` | `InputParams` | Configuration object containing path and formatting options |

### InputParams Fields

| Name                          | Type          | Description                                                                                                 |
| :---------------------------- | :------------ | :---------------------------------------------------------------------------------------------------------- |
| `path`                        | `str`         | The file or directory path to read from                                                                     |
| `name`                        | `str \| None` | A descriptive name for the input (not used in processing)                                                   |
| `ignore_file_path`            | `str \| None` | Optional path to .gitignore-style file for directories                                                      |
| `default`                     | `str \| None` | Default content to return if file doesn't exist                                                             |
| `directory_join_str`          | `str \| None` | String used to join multiple file contents (defaults to "\n")                                               |
| `directory_join_template_str` | `str \| None` | Template string for formatting each file's content (defaults to `<file name="{file}">\n{content}\n</file>`) |

## Returns

| Type  | Description                                                                              |
| :---- | :--------------------------------------------------------------------------------------- |
| `str` | The file content or combined directory content formatted according to the join templates |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta
from awa.core.models.input_params import InputParams

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, path: str) -> str:
        input_params = InputParams(
            path=path,
            name="source_files",
            ignore_file_path=".gitignore",
            default="File not found"
        )

        content = await workflow.execute_activity(
            "awa-read-file-or-directory",
            args=[input_params],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=60)
        )
        return content
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { "awa-read-file-or-directory": readFileOrDirectory } = proxyActivities<
  typeof activities
>({
  startToCloseTimeout: "1 minute",
  taskQueue: "awa_default",
});

export async function myWorkflow(path: string): Promise<string> {
  const inputParams = {
    path: path,
    name: "source_files",
    ignore_file_path: ".gitignore",
    default: "File not found",
    directory_join_str: "\n",
    directory_join_template_str: '<file name="{file}">\n{content}\n</file>',
  };

  return await readFileOrDirectory(inputParams);
}
```

```csharp [C#]
using Temporalio.Workflows;

[Workflow]
public class MyWorkflow
{
    [WorkflowRun]
    public async Task<string> RunAsync(string path)
    {
        var inputParams = new InputParams
        {
            Path = path,
            Name = "source_files",
            IgnoreFilePath = ".gitignore",
            Default = "File not found",
            DirectoryJoinStr = "\n",
            DirectoryJoinTemplateStr = "<file name=\"{file}\">\n{content}\n</file>"
        };

        return await Workflow.ExecuteActivityAsync(
            "awa-read-file-or-directory",
            new object[] { inputParams },
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
    private final MyActivities activities = Workflow.newActivityStub(MyActivities.class,
        ActivityOptions.newBuilder()
            .setTaskQueue("awa_default")
            .setStartToCloseTimeout(Duration.ofSeconds(60))
            .build());

    @Override
    public String run(String path) {
        InputParams inputParams = new InputParams.Builder()
            .setPath(path)
            .setName("source_files")
            .setIgnoreFilePath(".gitignore")
            .setDefault("File not found")
            .setDirectoryJoinStr("\n")
            .setDirectoryJoinTemplateStr("<file name=\"{file}\">\n{content}\n</file>")
            .build();

        return activities.readFileOrDirectoryActivity(inputParams);
    }
}
```

```go [Go]
import (
	"time"
	"go.temporal.io/sdk/workflow"
)

func MyWorkflow(ctx workflow.Context, path string) (string, error) {
	ao := workflow.ActivityOptions{
		TaskQueue:           "awa_default",
		StartToCloseTimeout: time.Second * 60,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	inputParams := InputParams{
		Path:                      path,
		Name:                      "source_files",
		IgnoreFilePath:           ".gitignore",
		Default:                  "File not found",
		DirectoryJoinStr:         "\n",
		DirectoryJoinTemplateStr: "<file name=\"{file}\">\n{content}\n</file>",
	}

	var result string
	err := workflow.ExecuteActivity(ctx, "awa-read-file-or-directory", inputParams).Get(ctx, &result)
	return result, err
}
```

```php [PHP]
use Temporal\Workflow;
use Temporal\Activity\ActivityOptions;

class MyWorkflow implements MyWorkflowInterface
{
    public function run(string $path): \Generator
    {
        $inputParams = [
            'path' => $path,
            'name' => 'source_files',
            'ignore_file_path' => '.gitignore',
            'default' => 'File not found',
            'directory_join_str' => "\n",
            'directory_join_template_str' => '<file name="{file}">' . "\n" . '{content}' . "\n" . '</file>'
        ];

        return yield Workflow::executeActivity(
            'awa-read-file-or-directory',
            [$inputParams],
            ActivityOptions::new()
                ->withTaskQueue('awa_default')
                ->withStartToCloseTimeout(60)
        );
    }
}
```

:::

## Example Outputs

### Single File Read

```text
def hello_world():
    print("Hello, World!")
```

### Directory Read (with default template)

```xml
<file name="main.py">
def main():
    print("Main function")

if __name__ == "__main__":
    main()
</file>

<file name="utils.py">
def helper_function():
    return "helper"
</file>
```

### Directory Read (custom template)

```text
=== src/main.py ===
def main():
    print("Main function")

=== src/utils.py ===
def helper_function():
    return "helper"
```

## Notes

- Automatically detects whether the path is a file or directory
- For directories, processes all files recursively
- Supports .gitignore-style patterns for excluding files
- Uses `fsspec` internally to support various file systems (local, S3, GCS, etc.)
- Template strings support `{file}` and `{content}` placeholders
- Falls back to default content if a single file doesn't exist
