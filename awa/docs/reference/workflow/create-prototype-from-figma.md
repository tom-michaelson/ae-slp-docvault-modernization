# `awa-create-prototype-from-figma`

A workflow for interacting with Figma to create HTML prototypes from Figma designs.

This workflow uses an AI agent with MCP (Model Context Protocol) tools to fetch data from Figma and generate working HTML pages that simulate a clickable prototype. The workflow is specifically designed to work with Figma designs and can create interactive prototypes with working links between pages.

## Parameters

| Name     | Type                  | Description                                                 |
| :------- | :-------------------- | :---------------------------------------------------------- |
| `params` | `FigmaWorkflowParams` | An object containing the workflow configuration parameters. |

### FigmaWorkflowParams

| Name          | Type  | Description                                                                 |
| :------------ | :---- | :-------------------------------------------------------------------------- |
| `output_path` | `str` | The directory path where the generated HTML files and assets will be saved. |

## Returns

| Type   | Description                                                                                                                                             |
| :----- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `None` | This workflow creates HTML files as a side effect and doesn't return a value. The generated prototype files will be saved to the specified output path. |

## Usage

The following examples show how to start the `awa-create-prototype-from-figma` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.workflows.figma_workflow import FigmaWorkflowParams

# Create parameters
params = FigmaWorkflowParams(
    output_path="./prototype_output"
)

# Execute the child workflow and wait for completion
await workflow.execute_child_workflow(
    "awa-create-prototype-from-figma",
    params
)

print("Figma prototype generation completed")
```

```typescript [TypeScript]
// Define the parameters interface
interface FigmaWorkflowParams {
  output_path: string;
}

// Create parameters
const params: FigmaWorkflowParams = {
  output_path: "./prototype_output",
};

// Execute the child workflow and wait for completion
await executeChild("awa-create-prototype-from-figma", {
  args: [params],
});

console.log("Figma prototype generation completed");
```

```csharp [.NET]
// Define the parameters class
public class FigmaWorkflowParams
{
    public string OutputPath { get; set; }
}

// Create parameters
var params = new FigmaWorkflowParams
{
    OutputPath = "./prototype_output"
};

// Execute the child workflow and wait for completion
await Workflow.ExecuteChildAsync("awa-create-prototype-from-figma", params);

Console.WriteLine("Figma prototype generation completed");
```

```java [Java]
// Define the parameters class
public class FigmaWorkflowParams {
    public String outputPath;
}

// Create parameters
FigmaWorkflowParams params = new FigmaWorkflowParams();
params.outputPath = "./prototype_output";

// Execute the child workflow and wait for completion
Workflow.executeChildWorkflow("awa-create-prototype-from-figma", Void.class, params);

System.out.println("Figma prototype generation completed");
```

```go [Go]
// Define the parameters struct
type FigmaWorkflowParams struct {
    OutputPath string `json:"output_path"`
}

// Create parameters
params := FigmaWorkflowParams{
    OutputPath: "./prototype_output",
}

// Execute the child workflow and wait for completion
err := workflow.ExecuteChildWorkflow(ctx, "awa-create-prototype-from-figma", params).Get(ctx, nil)
if err != nil {
    return err
}
fmt.Println("Figma prototype generation completed")
```

```php [PHP]
// Define the parameters class
class FigmaWorkflowParams {
    public string $output_path;
}

// Create parameters
$params = new FigmaWorkflowParams();
$params->output_path = "./prototype_output";

// Execute the child workflow and wait for completion
yield Workflow::executeChildWorkflow(
    'awa-create-prototype-from-figma',
    [$params]
);

echo "Figma prototype generation completed";
```

:::
