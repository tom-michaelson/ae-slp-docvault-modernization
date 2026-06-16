# `awa-transform`

This is a simple workflow that wraps the transform activity.

This workflow accepts a transform request and uses the transform_activity to process it, returning the transformed result. It can optionally write the output to a file, with support for JSON path extraction to write specific parts of the response.

<!--@include: /../../.shared/transform-vs-transform.md -->

## Parameters

| Name                | Type              | Description                                              |
| :------------------ | :---------------- | :------------------------------------------------------- |
| `transform_request` | `TransformParams` | An object containing the transformation request details. |

### TransformParams

| Name                 | Type                    | Required | Description                                                                                   |
| :------------------- | :---------------------- | :------- | :-------------------------------------------------------------------------------------------- |
| `baml_function_name` | `str`                   | Yes      | The name of the BAML function to execute                                                      |
| `request`            | `Any`                   | Yes      | The request object/data to pass to the BAML function                                         |
| `baml_content`       | `str`                   | No       | Optional BAML function definition content (if not using existing BAML files). Mutually exclusive with `baml_content_dir` |
| `baml_content_dir`   | `str`                   | No       | Optional directory containing BAML files to compile and use. Mutually exclusive with `baml_content`. All `.baml` files in the directory will be combined |
| `model_name`         | `str`                   | No       | Optional model name override                                                                  |
| `inputs`             | `list[InputParams]`     | No       | Optional list of input files to read and include in the request                               |
| `images`             | `list[BamlImageInputParams]` | No   | Optional list of images to include in the request                                             |
| `timeout_seconds`    | `int`                   | No       | Timeout for the BAML execution (default: 120 seconds)                                        |
| `output_path`        | `str`                   | No       | Optional file path to write the response to                                                   |
| `output_json_path`   | `str`                   | No       | Optional JSON path query to extract specific data from response before writing to output_path |
| `baml_src_dir`       | `str`                   | No       | Optional BAML source directory (usually auto-generated)                                      |

## Returns

| Type  | Description                                       |
| :---- | :------------------------------------------------ |
| `Any` | The full transformed result from the BAML function |

## Important Notes

- **BAML Content Sources**: You can provide BAML definitions in two ways:
  - `baml_content`: Directly provide BAML content as a string
  - `baml_content_dir`: Provide a directory path containing `.baml` files
  - These parameters are **mutually exclusive** - you cannot use both at the same time

- **Directory Processing**: When using `baml_content_dir`:
  - All `.baml` files in the directory are automatically discovered
  - Files are sorted alphabetically for consistent compilation order
  - Non-BAML files (e.g., `.md`, `.json`) are ignored
  - Source markers are added to help with debugging
  - An error is raised if no BAML files are found in the directory

## Usage

The following examples show how to start the `awa-transform` workflow as a child workflow.

### Basic Usage

::: code-group

```python [Python]
from awa.sdk.models.transform_params import TransformParams

# Basic transformation
transform_request = TransformParams(
    baml_function_name="MyFunction",
    request={"text": "Hello world", "instruction": "Convert to uppercase"}
)

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-transform",
    transform_request
)

print(result)  # Full BAML response object
```

:::

### With Output File and JSON Path Extraction

```python [Python]
from awa.sdk.models.transform_params import TransformParams

# Transform and extract specific part of response to file
transform_request = TransformParams(
    baml_function_name="TranslateUtilityFunction",
    request={
        "function_name": "my_function",
        "function_content": "def my_function():\n    pass",
        "target_language": "csharp"
    },
    output_path="/path/to/output.cs",
    output_json_path="$.translated_function_content"  # Extract only the translated code
)

# Execute the child workflow
result = await workflow.execute_child_workflow(
    "awa-transform",
    transform_request
)

# The full result is still returned, but only the extracted part is written to file
print(result)  # Full response: {"translated_function_content": "...", "metadata": "..."}
# File contains only: the translated C# code from $.translated_function_content
```

### With BAML Directory

```python [Python]
from awa.sdk.models.transform_params import TransformParams

# Use BAML definitions from a directory
transform_request = TransformParams(
    baml_function_name="MyComplexFunction",
    request={"data": "Process this data"},
    baml_content_dir="/path/to/baml/definitions"  # All .baml files in this directory will be compiled
)

# Execute the child workflow
result = await workflow.execute_child_workflow(
    "awa-transform",
    transform_request
)

# The workflow will:
# 1. Read all .baml files from the specified directory
# 2. Sort them alphabetically for consistent ordering
# 3. Combine them with source markers for debugging
# 4. Generate the BAML client with the combined definitions
# 5. Execute the specified function
print(result)
```

::: code-group

```typescript [TypeScript]
// Define the parameters interface
interface TransformParams {
  text: string;
  request: string;
}

// Create parameters
const transformRequest: TransformParams = {
  text: "Hello world",
  request: "Convert to uppercase",
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-transform", {
  args: [transformRequest],
});

console.log(result); // "HELLO WORLD"
```

```csharp [.NET]
// Define the parameters class
public class TransformParams
{
    public string Text { get; set; }
    public string Request { get; set; }
}

// Create parameters
var transformRequest = new TransformParams
{
    Text = "Hello world",
    Request = "Convert to uppercase"
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync<string>("awa-transform", transformRequest);

Console.WriteLine(result); // "HELLO WORLD"
```

```java [Java]
// Define the parameters class
public class TransformParams {
    public String text;
    public String request;
}

// Create parameters
TransformParams transformRequest = new TransformParams();
transformRequest.text = "Hello world";
transformRequest.request = "Convert to uppercase";

// Execute the child workflow and wait for completion
String result = Workflow.executeChildWorkflow("awa-transform", String.class, transformRequest);

System.out.println(result); // "HELLO WORLD"
```

```go [Go]
// Define the parameters struct
type TransformParams struct {
    Text    string `json:"text"`
    Request string `json:"request"`
}

// Create parameters
transformRequest := TransformParams{
    Text:    "Hello world",
    Request: "Convert to uppercase",
}

// Execute the child workflow and wait for completion
var result string
err := workflow.ExecuteChildWorkflow(ctx, "awa-transform", transformRequest).Get(ctx, &result)
if err != nil {
    return "", err
}
fmt.Println(result) // "HELLO WORLD"
```

```php [PHP]
// Define the parameters class
class TransformParams {
    public string $text;
    public string $request;
}

// Create parameters
$transformRequest = new TransformParams();
$transformRequest->text = "Hello world";
$transformRequest->request = "Convert to uppercase";

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-transform',
    [$transformRequest]
);

echo $result; // "HELLO WORLD"
```

:::
