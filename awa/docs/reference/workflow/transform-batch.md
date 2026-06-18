# `awa-transform-batch`

Execute transform workflows for multiple inputs in parallel.

This workflow executes child transform workflows for each input in parallel, allowing for efficient batch processing of BAML-based transformations. It provides centralized orchestration and result aggregation for multiple transformation operations.

## Parameters

| Name             | Type                   | Description                                                                  |
| :--------------- | :--------------------- | :--------------------------------------------------------------------------- |
| `workflow_input` | `TransformBatchParams` | Configuration object containing multiple transform parameters mapped by keys |

### TransformBatchParams Fields

| Name              | Type                         | Description                                                          |
| :---------------- | :--------------------------- | :------------------------------------------------------------------- |
| `params_by_key`   | `dict[str, TransformParams]` | Dictionary mapping keys to individual TransformParams configurations |
| `timeout_seconds` | `int \| None`                | Global timeout for the entire batch operation                        |

### TransformParams Fields

| Name                 | Type                        | Required | Description                                                                                   |
| :------------------- | :-------------------------- | :------- | :-------------------------------------------------------------------------------------------- |
| `baml_function_name` | `str`                       | Yes      | The name of the BAML function to execute                                                      |
| `request`            | `Any`                       | Yes      | The request object/data to pass to the BAML function                                         |
| `baml_content`       | `str \| None`               | No       | Optional BAML function definition content (if not using existing BAML files)                 |
| `model_name`         | `str \| None`               | No       | Optional model name override                                                                  |
| `inputs`             | `list[InputParams] \| None` | No       | Optional list of input files to read and include in the request                               |
| `images`             | `list[BamlImageInputParams] \| None` | No | Optional list of images to include in the request                                             |
| `timeout_seconds`    | `int \| None`               | No       | Timeout for the BAML execution (default: 120 seconds)                                        |
| `output_path`        | `str \| None`               | No       | Optional file path to write the response to                                                   |
| `output_json_path`   | `str \| None`               | No       | Optional JSON path query to extract specific data from response before writing to output_path |
| `baml_src_dir`       | `str \| None`               | No       | Optional BAML source directory (usually auto-generated)                                      |

## Returns

| Type             | Description                                                                      |
| :--------------- | :------------------------------------------------------------------------------- |
| `dict[str, Any]` | Dictionary mapping the original input keys to their respective transform results |

## Usage

The following examples show how to start the `awa-transform-batch` workflow as a child workflow.

### Basic Usage

::: code-group

```python [Python]
from awa.sdk.models.transform_params import TransformBatchParams, TransformParams

# Execute multiple transformations in parallel
batch_params = TransformBatchParams(
    params_by_key={
        "summary": TransformParams(
            baml_function_name="SummarizeText",
            request={"text": "Long document content..."}
        ),
        "translation": TransformParams(
            baml_function_name="TranslateText",
            request={"text": "Hello world", "target_language": "Spanish"}
        ),
        "analysis": TransformParams(
            baml_function_name="AnalyzeCode",
            request={"code": "def hello(): pass"}
        )
    },
    timeout_seconds=300
)

# Execute the child workflow and wait for completion
results = await workflow.execute_child_workflow(
    "awa-transform-batch",
    batch_params
)

print(results["summary"])     # Summary result
print(results["translation"]) # Translation result
print(results["analysis"])    # Analysis result
```

```typescript [TypeScript]
import { executeChild } from "@temporalio/workflow";

// Execute batch transformations with different BAML functions
const batchParams = {
  params_by_key: {
    extract: {
      baml_function_name: "ExtractData",
      request: { document: "PDF content..." },
    },
    classify: {
      baml_function_name: "ClassifyDocument",
      request: { content: "Article text..." },
    },
  },
  timeout_seconds: 600,
};

// Execute the child workflow and wait for completion
const results = await executeChild("awa-transform-batch", {
  args: [batchParams],
});

console.log(results.extract); // Extraction results
console.log(results.classify); // Classification results
```

```csharp [.NET]
using Temporalio.Workflows;

// Execute batch transformations with file outputs
var batchParams = new TransformBatchParams
{
    ParamsByKey = new Dictionary<string, TransformParams>
    {
        ["report"] = new TransformParams
        {
            BamlFunctionName = "GenerateReport",
            Request = new { data = "metrics..." },
            OutputPath = "/output/report.md"
        },
        ["dashboard"] = new TransformParams
        {
            BamlFunctionName = "CreateDashboard",
            Request = new { charts = "chart_data..." },
            OutputPath = "/output/dashboard.html"
        }
    },
    TimeoutSeconds = 900
};

// Execute the child workflow and wait for completion
var results = await Workflow.ExecuteChildAsync("awa-transform-batch", batchParams);

Console.WriteLine(results["report"]);    // Report generation result
Console.WriteLine(results["dashboard"]); // Dashboard creation result
```

```java [Java]
import io.temporal.workflow.Workflow;
import java.util.Map;
import java.util.HashMap;

// Execute batch transformations with custom models
Map<String, TransformParams> paramsByKey = new HashMap<>();
paramsByKey.put("gpt4_analysis", new TransformParams.Builder()
    .setModelName("gpt-4")
    .setBamlFunctionName("AnalyzeCode")
    .setRequest(Map.of("code", "function example() { return true; }"))
    .build());
paramsByKey.put("claude_review", new TransformParams.Builder()
    .setModelName("claude-3-sonnet")
    .setBamlFunctionName("ReviewCode")
    .setRequest(Map.of("code", "const data = fetch('/api');"))
    .build());

TransformBatchParams batchParams = new TransformBatchParams.Builder()
    .setParamsByKey(paramsByKey)
    .setTimeoutSeconds(450)
    .build();

// Execute the child workflow and wait for completion
var results = Workflow.executeChildWorkflow("awa-transform-batch", Map.class, batchParams);

System.out.println(results.get("gpt4_analysis")); // GPT-4 analysis result
System.out.println(results.get("claude_review"));  // Claude review result
```

```go [Go]
import (
    "go.temporal.io/sdk/workflow"
)

// Execute batch transformations with dynamic BAML content
paramsByKey := map[string]TransformParams{
    "custom_transform": {
        BamlFunctionName: "CustomProcessor",
        BamlContent:      "function CustomProcessor(input: string) -> string { ... }",
        Request:          map[string]interface{}{"input": "process this"},
    },
    "standard_transform": {
        BamlFunctionName: "StandardProcessor",
        Request:          map[string]interface{}{"data": "standard input"},
    },
}

batchParams := TransformBatchParams{
    ParamsByKey:    paramsByKey,
    TimeoutSeconds: 180,
}

// Execute the child workflow and wait for completion
var results map[string]interface{}
err := workflow.ExecuteChildWorkflow(ctx, "awa-transform-batch", batchParams).Get(ctx, &results)
if err != nil {
    return nil, err
}

fmt.Println(results["custom_transform"])   // Custom transform result
fmt.Println(results["standard_transform"]) // Standard transform result
```

```php [PHP]
use Temporal\Workflow;

// Execute batch transformations with input files
$batchParams = [
    'params_by_key' => [
        'process_docs' => [
            'baml_function_name' => 'ProcessDocuments',
            'request' => ['query' => 'summarize'],
            'inputs' => [
                ['path' => '/docs/file1.txt', 'name' => 'doc1'],
                ['path' => '/docs/file2.txt', 'name' => 'doc2']
            ]
        ],
        'generate_index' => [
            'baml_function_name' => 'GenerateIndex',
            'request' => ['format' => 'json']
        ]
    ],
    'timeout_seconds' => 720
];

// Execute the child workflow and wait for completion
$results = yield Workflow::executeChildWorkflow(
    'awa-transform-batch',
    [$batchParams]
);

echo $results['process_docs'];   // Document processing results
echo $results['generate_index']; // Index generation results
```

:::

### With JSON Path Extraction

Use `output_json_path` to extract specific parts of responses and write them to files:

```python [Python]
from awa.sdk.models.transform_params import TransformBatchParams, TransformParams

# Batch translate utility functions and extract only the translated code
batch_params = TransformBatchParams(
    params_by_key={
        "activity_utils": TransformParams(
            baml_function_name="TranslateUtilityFunction",
            request={
                "function_name": "read_file_activity",
                "function_content": "def read_file_activity(path: str) -> str: ...",
                "target_language": "csharp"
            },
            output_path="/output/ReadFileActivity.cs",
            output_json_path="$.translated_function_content"  # Extract only the C# code
        ),
        "workflow_utils": TransformParams(
            baml_function_name="TranslateUtilityFunction",
            request={
                "function_name": "execute_agent_workflow",
                "function_content": "async def execute_agent_workflow(...): ...",
                "target_language": "csharp"
            },
            output_path="/output/ExecuteAgentWorkflow.cs",
            output_json_path="$.translated_function_content"  # Extract only the C# code
        )
    },
    timeout_seconds=300
)

# Execute the batch workflow
results = await workflow.execute_child_workflow(
    "awa-transform-batch",
    batch_params
)

# Full results are still returned, but extracted parts are written to files
print(results["activity_utils"])  # Full response with metadata
print(results["workflow_utils"])  # Full response with metadata
# Files contain only the extracted C# code from $.translated_function_content
```
