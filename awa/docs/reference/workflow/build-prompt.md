# `awa-build-prompt`

Build a prompt from a template and variables.

This workflow takes a Jinja2 template and variables to generate a resolved prompt string. It supports both direct template input and template files, can read multiple input files in parallel, and optionally write the resolved template to an output file.

## Parameters

| Name             | Type                | Description                                                                        |
| :--------------- | :------------------ | :--------------------------------------------------------------------------------- |
| `workflow_input` | `BuildPromptParams` | Configuration object containing template, variables, and input file specifications |

### BuildPromptParams Fields

| Name             | Type                        | Description                                                      |
| :--------------- | :-------------------------- | :--------------------------------------------------------------- |
| `template`       | `str \| None`               | Direct template string in Jinja2 format                          |
| `template_input` | `InputParams \| None`       | Parameters for reading template from file/directory              |
| `variables`      | `dict[str, Any] \| None`    | Variables to substitute in the template                          |
| `inputs`         | `list[InputParams] \| None` | List of input files/directories to read and include as variables |
| `output_path`    | `str \| None`               | Optional path to write the resolved template                     |

### InputParams Fields

| Name                          | Type          | Description                                        |
| :---------------------------- | :------------ | :------------------------------------------------- |
| `path`                        | `str`         | Path to the file or directory to read from         |
| `name`                        | `str \| None` | Name to use as variable key (defaults to filename) |
| `ignore_file_path`            | `str \| None` | Path to .gitignore-style file for directories      |
| `default`                     | `str \| None` | Default content if file doesn't exist              |
| `directory_join_template_str` | `str \| None` | Template for formatting directory contents         |
| `directory_join_str`          | `str \| None` | String to join multiple file contents              |

## Returns

| Type  | Description                                                 |
| :---- | :---------------------------------------------------------- |
| `str` | The resolved template string with all variables substituted |

## Usage

The following examples show how to start the `awa-build-prompt` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.models.build_prompt_params import BuildPromptParams
from awa.core.models.input_params import InputParams

# Build prompt with direct template and variables
params = BuildPromptParams(
    template="Hello {{ name }}, welcome to {{ project }}!",
    variables={
        "name": "Alice",
        "project": "AWA"
    }
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-build-prompt",
    params
)

print(result)  # "Hello Alice, welcome to AWA!"
```

```typescript [TypeScript]
import { executeChild } from "@temporalio/workflow";

// Build prompt with template file and input files
const params = {
  template_input: {
    path: "/path/to/template.j2",
    name: "template",
  },
  inputs: [
    {
      path: "/path/to/source.py",
      name: "source_code",
    },
  ],
  variables: {
    version: "1.0.0",
  },
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-build-prompt", {
  args: [params],
});

console.log(result); // Resolved template string
```

```csharp [.NET]
using Temporalio.Workflows;

// Build prompt with variables and output file
var params = new BuildPromptParams
{
    Template = "Process the following code:\n{{ source_code }}",
    Variables = new Dictionary<string, object>
    {
        ["source_code"] = "def hello(): print('world')"
    },
    OutputPath = "/path/to/output.txt"
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync("awa-build-prompt", params);

Console.WriteLine(result); // Resolved template string
```

```java [Java]
import io.temporal.workflow.Workflow;
import java.util.Map;
import java.util.List;

// Build prompt with multiple input files
BuildPromptParams params = new BuildPromptParams.Builder()
    .setTemplate("Review these files:\n{% for file in files %}{{ file }}\n{% endfor %}")
    .setInputs(List.of(
        new InputParams.Builder()
            .setPath("/path/to/file1.py")
            .setName("file1")
            .build(),
        new InputParams.Builder()
            .setPath("/path/to/file2.py")
            .setName("file2")
            .build()
    ))
    .build();

// Execute the child workflow and wait for completion
String result = Workflow.executeChildWorkflow("awa-build-prompt", params);

System.out.println(result); // Resolved template string
```

```go [Go]
import (
    "go.temporal.io/sdk/workflow"
)

// Build prompt with template and variables
params := BuildPromptParams{
    Template: "Generate code for {{ task }} in {{ language }}",
    Variables: map[string]interface{}{
        "task":     "file processing",
        "language": "Python",
    },
}

// Execute the child workflow and wait for completion
var result string
err := workflow.ExecuteChildWorkflow(ctx, "awa-build-prompt", params).Get(ctx, &result)
if err != nil {
    return "", err
}
fmt.Println(result) // Resolved template string
```

```php [PHP]
use Temporal\Workflow;

// Build prompt with template file
$params = [
    'template_input' => [
        'path' => '/path/to/template.j2',
        'name' => 'template'
    ],
    'variables' => [
        'user' => 'developer',
        'task' => 'code review'
    ]
];

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-build-prompt',
    [$params]
);

echo $result; // Resolved template string
```

:::
