# `awa-apply-single-file-diff`

This workflow applies natural language differences to a file using an AI agent.

This workflow reads a source file, applies the specified natural language changes using an AI agent through the diff_application_activity, and outputs the modified content.

## Parameters

| Name             | Type                  | Description                                                                                  |
| :--------------- | :-------------------- | :------------------------------------------------------------------------------------------- |
| `workflow_input` | `SingleFileDiffInput` | An object containing the file path and the natural language description of changes to apply. |

### SingleFileDiffInput

| Name                    | Type  | Description                                                       |
| :---------------------- | :---- | :---------------------------------------------------------------- |
| `file_path`             | `str` | Path to the file to be modified.                                  |
| `natural_language_diff` | `str` | Natural language description of the changes to apply to the file. |

## Returns

| Type  | Description                                                         |
| :---- | :------------------------------------------------------------------ |
| `str` | The modified file content after applying the natural language diff. |

## Usage

The following examples show how to start the `awa-apply-single-file-diff` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.workflows.single_file_diff import SingleFileDiffInput

# Create parameters
workflow_input = SingleFileDiffInput(
    file_path="src/example.py",
    natural_language_diff="Add a docstring to the main function explaining what it does"
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-apply-single-file-diff",
    workflow_input
)

print(result)  # Modified file content with the docstring added
```

```typescript [TypeScript]
// Define the parameters interface
interface SingleFileDiffInput {
  file_path: string;
  natural_language_diff: string;
}

// Create parameters
const workflowInput: SingleFileDiffInput = {
  file_path: "src/example.py",
  natural_language_diff:
    "Add a docstring to the main function explaining what it does",
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-apply-single-file-diff", {
  args: [workflowInput],
});

console.log(result); // Modified file content with the docstring added
```

```csharp [.NET]
// Define the parameters class
public class SingleFileDiffInput
{
    public string FilePath { get; set; }
    public string NaturalLanguageDiff { get; set; }
}

// Create parameters
var workflowInput = new SingleFileDiffInput
{
    FilePath = "src/example.py",
    NaturalLanguageDiff = "Add a docstring to the main function explaining what it does"
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync<string>("awa-apply-single-file-diff", workflowInput);

Console.WriteLine(result); // Modified file content with the docstring added
```

```java [Java]
// Define the parameters class
public class SingleFileDiffInput {
    public String filePath;
    public String naturalLanguageDiff;
}

// Create parameters
SingleFileDiffInput workflowInput = new SingleFileDiffInput();
workflowInput.filePath = "src/example.py";
workflowInput.naturalLanguageDiff = "Add a docstring to the main function explaining what it does";

// Execute the child workflow and wait for completion
String result = Workflow.executeChildWorkflow("awa-apply-single-file-diff", String.class, workflowInput);

System.out.println(result); // Modified file content with the docstring added
```

```go [Go]
// Define the parameters struct
type SingleFileDiffInput struct {
    FilePath            string `json:"file_path"`
    NaturalLanguageDiff string `json:"natural_language_diff"`
}

// Create parameters
workflowInput := SingleFileDiffInput{
    FilePath:            "src/example.py",
    NaturalLanguageDiff: "Add a docstring to the main function explaining what it does",
}

// Execute the child workflow and wait for completion
var result string
err := workflow.ExecuteChildWorkflow(ctx, "awa-apply-single-file-diff", workflowInput).Get(ctx, &result)
if err != nil {
    return "", err
}
fmt.Println(result) // Modified file content with the docstring added
```

```php [PHP]
// Define the parameters class
class SingleFileDiffInput {
    public string $file_path;
    public string $natural_language_diff;
}

// Create parameters
$workflowInput = new SingleFileDiffInput();
$workflowInput->file_path = "src/example.py";
$workflowInput->natural_language_diff = "Add a docstring to the main function explaining what it does";

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-apply-single-file-diff',
    [$workflowInput]
);

echo $result; // Modified file content with the docstring added
```

:::
