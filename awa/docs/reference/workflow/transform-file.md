# `awa-transform-file`

This workflow applies a transformation to an input file and saves the result to an output file.

This workflow reads a JSON request from a file specified in the input, uses the transform_activity to process it, and writes the final poem to an output file.

## Parameters

| Name             | Type                      | Description                                           |
| :--------------- | :------------------------ | :---------------------------------------------------- |
| `workflow_input` | `FileBasedTransformInput` | An object containing the input and output file paths. |

### FileBasedTransformInput

| Name          | Type  | Description                                         |
| :------------ | :---- | :-------------------------------------------------- |
| `input_path`  | `str` | Path to the input file containing the JSON request. |
| `output_path` | `str` | Path to save the transformed output.                |

## Returns

| Type  | Description                                                        |
| :---- | :----------------------------------------------------------------- |
| `str` | A string indicating the successful completion and the output path. |

## Usage

The following examples show how to start the `awa-transform-file` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.workflows.file_based_transform import FileBasedTransformInput

# Create parameters
workflow_input = FileBasedTransformInput(
    input_path="request.json",
    output_path="poem.txt"
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-transform-file",
    workflow_input
)

print(result)  # "Poem successfully written to poem.txt"
```

```typescript [TypeScript]
// Define the parameters interface
interface FileBasedTransformInput {
  input_path: string;
  output_path: string;
}

// Create parameters
const workflowInput: FileBasedTransformInput = {
  input_path: "request.json",
  output_path: "poem.txt",
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-transform-file", {
  args: [workflowInput],
});

console.log(result); // "Poem successfully written to poem.txt"
```

```csharp [.NET]
// Define the parameters class
public class FileBasedTransformInput
{
    public string InputPath { get; set; }
    public string OutputPath { get; set; }
}

// Create parameters
var workflowInput = new FileBasedTransformInput
{
    InputPath = "request.json",
    OutputPath = "poem.txt"
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync<string>("awa-transform-file", workflowInput);

Console.WriteLine(result); // "Poem successfully written to poem.txt"
```

```java [Java]
// Define the parameters class
public class FileBasedTransformInput {
    public String inputPath;
    public String outputPath;
}

// Create parameters
FileBasedTransformInput workflowInput = new FileBasedTransformInput();
workflowInput.inputPath = "request.json";
workflowInput.outputPath = "poem.txt";

// Execute the child workflow and wait for completion
String result = Workflow.executeChildWorkflow("awa-transform-file", String.class, workflowInput);

System.out.println(result); // "Poem successfully written to poem.txt"
```

```go [Go]
// Define the parameters struct
type FileBasedTransformInput struct {
    InputPath  string `json:"input_path"`
    OutputPath string `json:"output_path"`
}

// Create parameters
workflowInput := FileBasedTransformInput{
    InputPath:  "request.json",
    OutputPath: "poem.txt",
}

// Execute the child workflow and wait for completion
var result string
err := workflow.ExecuteChildWorkflow(ctx, "awa-transform-file", workflowInput).Get(ctx, &result)
if err != nil {
    return "", err
}
fmt.Println(result) // "Poem successfully written to poem.txt"
```

```php [PHP]
// Define the parameters class
class FileBasedTransformInput {
    public string $input_path;
    public string $output_path;
}

// Create parameters
$workflowInput = new FileBasedTransformInput();
$workflowInput->input_path = "request.json";
$workflowInput->output_path = "poem.txt";

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-transform-file',
    [$workflowInput]
);

echo $result; // "Poem successfully written to poem.txt"
```

:::
