# `awa-resolve-template`

This workflow resolves a Jinja2 template by applying provided variables and writing the output to a specified file.

This workflow takes a template file path, output file path, and template variables, then uses the resolve_template_activity to render the template with the provided context and save the result.

## Parameters

| Name             | Type                        | Description                                                                       |
| :--------------- | :-------------------------- | :-------------------------------------------------------------------------------- |
| `workflow_input` | `ResolveJinjaTemplateInput` | An object containing the template file path, output path, and template variables. |

### ResolveJinjaTemplateInput

| Name                 | Type   | Description                                            |
| :------------------- | :----- | :----------------------------------------------------- |
| `template_file_path` | `str`  | Path to the Jinja2 template file.                      |
| `output_file_path`   | `str`  | Path where the resolved template will be written.      |
| `template_variables` | `dict` | Dictionary of variables to substitute in the template. |

## Returns

| Type  | Description                                                                   |
| :---- | :---------------------------------------------------------------------------- |
| `str` | A message indicating successful template resolution and the output file path. |

## Usage

The following examples show how to start the `awa-resolve-template` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.workflows.resolve_jinja_template import ResolveJinjaTemplateInput

# Create parameters
workflow_input = ResolveJinjaTemplateInput(
    template_file_path="template.j2",
    output_file_path="output.txt",
    template_variables={
        "name": "John",
        "age": 30,
        "city": "New York"
    }
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-resolve-template",
    workflow_input
)

print(result)  # "Template resolved successfully. Output written to output.txt"
```

```typescript [TypeScript]
// Define the parameters interface
interface ResolveJinjaTemplateInput {
  template_file_path: string;
  output_file_path: string;
  template_variables: Record<string, any>;
}

// Create parameters
const workflowInput: ResolveJinjaTemplateInput = {
  template_file_path: "template.j2",
  output_file_path: "output.txt",
  template_variables: {
    name: "John",
    age: 30,
    city: "New York",
  },
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-resolve-template", {
  args: [workflowInput],
});

console.log(result); // "Template resolved successfully. Output written to output.txt"
```

```csharp [.NET]
// Define the parameters class
public class ResolveJinjaTemplateInput
{
    public string TemplateFilePath { get; set; }
    public string OutputFilePath { get; set; }
    public Dictionary<string, object> TemplateVariables { get; set; }
}

// Create parameters
var workflowInput = new ResolveJinjaTemplateInput
{
    TemplateFilePath = "template.j2",
    OutputFilePath = "output.txt",
    TemplateVariables = new Dictionary<string, object>
    {
        { "name", "John" },
        { "age", 30 },
        { "city", "New York" }
    }
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync<string>("awa-resolve-template", workflowInput);

Console.WriteLine(result); // "Template resolved successfully. Output written to output.txt"
```

```java [Java]
// Define the parameters class
public class ResolveJinjaTemplateInput {
    public String templateFilePath;
    public String outputFilePath;
    public Map<String, Object> templateVariables;
}

// Create parameters
ResolveJinjaTemplateInput workflowInput = new ResolveJinjaTemplateInput();
workflowInput.templateFilePath = "template.j2";
workflowInput.outputFilePath = "output.txt";
workflowInput.templateVariables = Map.of(
    "name", "John",
    "age", 30,
    "city", "New York"
);

// Execute the child workflow and wait for completion
String result = Workflow.executeChildWorkflow("awa-resolve-template", String.class, workflowInput);

System.out.println(result); // "Template resolved successfully. Output written to output.txt"
```

```go [Go]
// Define the parameters struct
type ResolveJinjaTemplateInput struct {
    TemplateFilePath   string            `json:"template_file_path"`
    OutputFilePath     string            `json:"output_file_path"`
    TemplateVariables  map[string]interface{} `json:"template_variables"`
}

// Create parameters
workflowInput := ResolveJinjaTemplateInput{
    TemplateFilePath:  "template.j2",
    OutputFilePath:    "output.txt",
    TemplateVariables: map[string]interface{}{
        "name": "John",
        "age":  30,
        "city": "New York",
    },
}

// Execute the child workflow and wait for completion
var result string
err := workflow.ExecuteChildWorkflow(ctx, "awa-resolve-template", workflowInput).Get(ctx, &result)
if err != nil {
    return "", err
}
fmt.Println(result) // "Template resolved successfully. Output written to output.txt"
```

```php [PHP]
// Define the parameters class
class ResolveJinjaTemplateInput {
    public string $template_file_path;
    public string $output_file_path;
    public array $template_variables;
}

// Create parameters
$workflowInput = new ResolveJinjaTemplateInput();
$workflowInput->template_file_path = "template.j2";
$workflowInput->output_file_path = "output.txt";
$workflowInput->template_variables = [
    "name" => "John",
    "age" => 30,
    "city" => "New York"
];

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-resolve-template',
    [$workflowInput]
);

echo $result; // "Template resolved successfully. Output written to output.txt"
```

:::
