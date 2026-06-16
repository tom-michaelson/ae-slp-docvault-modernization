# `awa-hello-world`

A simple workflow that demonstrates basic functionality.

This workflow takes a name as input, logs a greeting message, and returns a greeting string using the say_hello_activity.

## Parameters

| Name             | Type              | Description                                               |
| :--------------- | :---------------- | :-------------------------------------------------------- |
| `workflow_input` | `HelloWorldInput` | An object containing the name to include in the greeting. |

### HelloWorldInput

| Name   | Type  | Description                          |
| :----- | :---- | :----------------------------------- |
| `name` | `str` | The name to include in the greeting. |

## Returns

| Type  | Description                                       |
| :---- | :------------------------------------------------ |
| `str` | A greeting string in the format "Hello, {name}!". |

## Usage

The following examples show how to start the `awa-hello-world` workflow as a child workflow.

::: code-group

```python [Python]
from awa.core.workflows.hello_world import HelloWorldInput

# Create parameters
workflow_input = HelloWorldInput(name="World")

# Execute the child workflow and wait for completion
result = await workflow.execute_child_workflow(
    "awa-hello-world",
    workflow_input
)

print(result)  # "Hello, World!"
```

```typescript [TypeScript]
// Define the parameters interface
interface HelloWorldInput {
  name: string;
}

// Create parameters
const workflowInput: HelloWorldInput = {
  name: "World",
};

// Execute the child workflow and wait for completion
const result = await executeChild("awa-hello-world", {
  args: [workflowInput],
});

console.log(result); // "Hello, World!"
```

```csharp [.NET]
// Define the parameters class
public class HelloWorldInput
{
    public string Name { get; set; }
}

// Create parameters
var workflowInput = new HelloWorldInput
{
    Name = "World"
};

// Execute the child workflow and wait for completion
var result = await Workflow.ExecuteChildAsync("awa-hello-world", workflowInput);

Console.WriteLine(result); // "Hello, World!"
```

```java [Java]
// Define the parameters class
public class HelloWorldInput {
    public String name;
}

// Create parameters
HelloWorldInput workflowInput = new HelloWorldInput();
workflowInput.name = "World";

// Execute the child workflow and wait for completion
String result = Workflow.executeChildWorkflow("awa-hello-world", workflowInput);

System.out.println(result); // "Hello, World!"
```

```go [Go]
// Define the parameters struct
type HelloWorldInput struct {
    Name string `json:"name"`
}

// Create parameters
workflowInput := HelloWorldInput{
    Name: "World",
}

// Execute the child workflow and wait for completion
var result string
err := workflow.ExecuteChildWorkflow(ctx, "awa-hello-world", workflowInput).Get(ctx, &result)
if err != nil {
    return "", err
}
fmt.Println(result) // "Hello, World!"
```

```php [PHP]
// Define the parameters class
class HelloWorldInput {
    public string $name;
}

// Create parameters
$workflowInput = new HelloWorldInput();
$workflowInput->name = "World";

// Execute the child workflow and wait for completion
$result = yield Workflow::executeChildWorkflow(
    'awa-hello-world',
    [$workflowInput]
);

echo $result; // "Hello, World!"
```

:::
