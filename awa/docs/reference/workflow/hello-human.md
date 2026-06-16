# `awa-hello-human`

A workflow that demonstrates waiting for an external signal.

This workflow starts and then pauses, waiting for an `approve` signal
before it will continue execution. The signal must provide the name
of the approver.

## Parameters

| Name   | Type  | Description                          |
| :----- | :---- | :----------------------------------- |
| `name` | `str` | The name to include in the greeting. |

## Returns

| Type  | Description                                                                                       |
| :---- | :------------------------------------------------------------------------------------------------ |
| `str` | A greeting string that includes both the input name and the name of the approver from the signal. |

## Usage

The following examples show how to start the `awa-hello-human` workflow as a child workflow and then send it the `approve` signal.

::: code-group

```python [Python]
# First, start the child workflow
child_handle = await workflow.start_child_workflow(
    "awa-hello-human",
    "World"
)

# Then, signal it
await child_handle.signal("approve", {"name": "Alice"})

# Finally, get the result
result = await child_handle.result()
print(result) # "Hello, World (Alice)!"
```

```typescript [TypeScript]
// First, start the child workflow
const handle = await startChild("awa-hello-human", {
  args: ["World"],
});

// Then, signal it
await handle.signal("approve", { name: "Alice" });

// Finally, get the result
const result = await handle.result();
console.log(result); // "Hello, World (Alice)!"
```

```csharp [.NET]
// First, start the child workflow
var child = await Workflow.StartChildAsync("awa-hello-human", "World");

// Then, signal it
await child.SignalAsync("approve", new { Name = "Alice" });

// Finally, get the result
var result = await child.GetResultAsync();
Console.WriteLine(result); // "Hello, World (Alice)!"
```

```java [Java]
// First, start the child workflow
var childHandle = Workflow.executeChildWorkflow("awa-hello-human", String.class, "World");

// Then, signal it
childHandle.signal("approve", Map.of("name", "Alice"));

// Finally, get the result
String result = childHandle.get(); // This will block until the signal is received
System.out.println(result); // "Hello, World (Alice)!"
```

```go [Go]
// First, start the child workflow
childWorkflowFuture := workflow.ExecuteChildWorkflow(ctx, "awa-hello-human", "World")

// Then, signal it
workflow.SignalExternalWorkflow(ctx, childWorkflowFuture.GetWorkflowID(), "", "approve", map[string]interface{}{"name": "Alice"})

// Finally, get the result
var result string
if err := childWorkflowFuture.Get(ctx, &result); err != nil {
    return "", err
}
fmt.Println(result) // "Hello, World (Alice)!"
```

```php [PHP]
// First, start the child workflow
$childHandle = yield Workflow::startChildWorkflow('awa-hello-human', ['World']);

// Then, signal it
yield $childHandle->signal('approve', ['name' => 'Alice']);

// Finally, get the result
$result = yield $childHandle->getResult();
echo $result; // "Hello, World (Alice)!"
```

:::
