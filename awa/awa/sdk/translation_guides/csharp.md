# Temporal SDK Translation Guide: Python to C#

Quick reference for converting Python Temporal SDK utility functions to C# equivalents.

## Project Context

The utility classes are organized by type:
- Activity utilities: `Awa.Client.Utilities.Activity.ActivityUtilities`
- Workflow utilities: `Awa.Client.Utilities.Workflow.WorkflowUtilities`
- General utilities: `Awa.Client.Utilities.General.GeneralUtilities`

The utility function you are translating will be a static method on one of these classes, so you can use other utility functions without a class reference when within the same class.

## Important: Naming and Nullability Guidelines

- Always preserve the Python utility name in the generated C# method name.
  - Method name = PascalCase(Python function/file name). NEVER add `Async` suffix.
  - Keep tokens from the original name. Examples:
    - Python `read_file_activity` → C# `Awa.Client.Utilities.Activity.ActivityUtilities.ReadFileActivity(...)`
    - Python `execute_agent_workflow` → C# `Awa.Client.Utilities.Workflow.WorkflowUtilities.ExecuteAgentWorkflow(...)`
    - Python `get_workflow_paths` → C# `Awa.Client.Utilities.General.GeneralUtilities.GetWorkflowPaths(...)`
- Annotate nullable parameters/returns with `?` when values can be null.
- Use `object?[]` for the argument arrays passed to Temporal activities/child workflows.
- Use `Dictionary<string, object?>` where values can be null.
- Prefer safe access patterns (`TryGetValue`, null-propagation) when reading nullable values.

## CRITICAL: Temporal Namespace Qualifiers

**ALWAYS use the full namespace qualifier `Temporalio.Workflows.Workflow` when calling Temporal's Workflow methods.** This prevents compilation errors when the utility classes don't have the appropriate using statements or when there are naming conflicts.

### Required Full Namespace Qualifiers:
- For executing activities: `Temporalio.Workflows.Workflow.ExecuteActivityAsync`
- For executing child workflows: `Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync`
- For accessing workflow info: `Temporalio.Workflows.Workflow.Info`
- For any other Workflow static method: `Temporalio.Workflows.Workflow.<MethodName>`

### Examples:
```csharp
// ✅ CORRECT - Full namespace qualifier
await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(...)
await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<ResultType>(...)
var workflowId = Temporalio.Workflows.Workflow.Info.WorkflowId;

// ❌ INCORRECT - Missing namespace qualifier (will cause compilation errors)
await Workflow.ExecuteActivityAsync<string?>(...)  // WRONG!
await Workflow.ExecuteChildWorkflowAsync<ResultType>(...)  // WRONG!
var workflowId = Workflow.Info.WorkflowId;  // WRONG!
```

## Key Differences

| Python SDK                                                         | C# SDK                                                                                                                                         |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `timedelta(minutes=5)`                                             | `TimeSpan.FromMinutes(5)`                                                                                                                      |
| `workflow.execute_activity(func, arg1, arg2, timeout=...)`         | `Temporalio.Workflows.Workflow.ExecuteActivityAsync(ActivityConstants.METHOD_NAME, new object[] { arg1, arg2 }, new() { Timeout = ... })`     |
| `workflow.execute_child_workflow(WorkflowClass.run, args, id=...)` | `Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync(WorkflowConstants.WORKFLOW_NAME, new object[] { args }, new() { Id = ... })`         |
| Named parameters                                                   | Options objects                                                                                                                                |
| `await asyncio.gather(*tasks)`                                     | `await Task.WhenAll(tasks)`                                                                                                                    |

**CRITICAL**: Always use the full namespace qualifier `Temporalio.Workflows.Workflow` when calling Temporal's Workflow methods. Never use just `Workflow` without the namespace qualifier.

## Activity Execution

**Python:**

```python
# Basic activity with timeout and retry
result: str = await workflow.execute_activity(
    process_data,
    user_id, data_dict,
    start_to_close_timeout=timedelta(minutes=5),
    schedule_to_close_timeout=timedelta(minutes=10),
    retry_policy=RetryPolicy(maximum_attempts=3, initial_interval=timedelta(seconds=1))
)
```

**C#:**

```csharp
// Basic activity with timeout and retry
var result = await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
    ActivityConstants.PROCESS_DATA,
    new object?[] { userId, dataDict },
    new()
    {
        StartToCloseTimeout = TimeSpan.FromMinutes(5),
        ScheduleToCloseTimeout = TimeSpan.FromMinutes(10),
        RetryPolicy = new RetryPolicy
        {
            MaximumAttempts = 3,
            InitialInterval = TimeSpan.FromSeconds(1)
        }
    });
```

## Child Workflow Execution

**Python:**

```python
# Child workflow with options
result: str = await workflow.execute_child_workflow(
    ChildWorkflow.run,
    input_data, config,
    id=f"child-{workflow.info().workflow_id}",
    task_queue="processing-queue",
    execution_timeout=timedelta(hours=1)
)
```

**C#:**

```csharp
// Child workflow with options
var result = await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<string?>(
    WorkflowConstants.CHILD_WORKFLOW,
    new object?[] { inputData, config },
    new()
    {
        Id = $"child-{Temporalio.Workflows.Workflow.Info.WorkflowId}",
        TaskQueue = "processing-queue",
        ExecutionTimeout = TimeSpan.FromHours(1)
    });
```

## Parallel Execution

**Python:**

```python
# Parallel activities
tasks = [
    workflow.execute_activity(process_item, item, start_to_close_timeout=timedelta(minutes=5))
    for item in items
]
results = await asyncio.gather(*tasks)
```

**C#:**

```csharp
// Parallel activities
var tasks = items.Select(item =>
    Temporalio.Workflows.Workflow.ExecuteActivityAsync(
        ActivityConstants.PROCESS_ITEM,
        new object?[] { item },
        new() { StartToCloseTimeout = TimeSpan.FromMinutes(5) }));
var results = await Task.WhenAll(tasks);
```

## Error Handling

**Python:**

```python
try:
    result: str = await workflow.execute_activity(risky_activity, data)
except ActivityError as e:
    return {"error": str(e)}
except ApplicationError as e:
    return {"error": f"App error: {e}"}
```

**C#:**

```csharp
try
{
    var result = await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
        ActivityConstants.RISKY_ACTIVITY,
        new object?[] { data },
        options);
}
catch (ActivityFailureException e)
{
    return new { error = e.Message };
}
catch (ApplicationFailureException e)
{
    return new { error = $"App error: {e.Message}" };
}
```

## Utility Class Translation Example

**Python:**

```python
class WorkflowUtils:
    @staticmethod
    async def read_file(file_path: str | Path, default: str | None = None) -> str:
        return await workflow.execute_activity(
            constants.AWA_ACTIVITY_READ_FILE,
            args=[str(file_path), default],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
        )

    @staticmethod
    async def execute_agent(agent_config: dict[str, Any], timeout_seconds: int | None = None) -> str:
        return await workflow.execute_child_workflow(
            workflow=constants.AWA_WORKFLOW_EXECUTE_AGENT,
            args=[agent_config],
            task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
            execution_timeout=timedelta(seconds=timeout_seconds or constants.AGENT_TIMEOUT_SECONDS),
        )
```

**C#:**

```csharp
public partial static class WorkflowUtilities
{
    public static async Task<string?> ReadFileActivity(string filePath, string? defaultValue = null)
    {
        return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
            Constants.AWA_ACTIVITY_READ_FILE,
            new object?[] { filePath, defaultValue },
            new()
            {
                TaskQueue = Constants.AwaDefaultTaskQueue,
                StartToCloseTimeout = TimeSpan.FromSeconds(Constants.FileIoTimeoutSeconds)
            });
    }

    public static async Task<string?> ExecuteAgentWorkflow(Dictionary<string, object?> agentConfig, int? timeoutSeconds = null)
    {
        return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<string?>(
            Constants.AWA_WORKFLOW_EXECUTE_AGENT,
            new object?[] { agentConfig },
            new()
            {
                TaskQueue = Constants.AwaDefaultTaskQueue,
                ExecutionTimeout = TimeSpan.FromSeconds(timeoutSeconds ?? Constants.AgentTimeoutSeconds)
            });
    }
}
```

## Cross-Utility Method Calls

When utility methods need to call other utility methods, follow these patterns:

### Within Same Utility Class
When calling methods within the same partial class, you can call them directly:

```csharp
public static partial class WorkflowUtilities
{
    public static async Task<WorkflowPaths> GetWorkflowPaths(string workflowId)
    {
        // Direct call to another method in the same partial class
        return await GetWorkflowPathsDirect(workflowId);
    }
}
```

### Cross-Utility Class Calls
When calling methods from a different utility class, use the full class name:

```csharp
public static partial class WorkflowUtilities
{
    public static async Task<TransformResult> ExecuteBamlTransformWorkflow(TransformParams parameters)
    {
        // Call to Activity utilities from within Workflow utilities
        var fileContent = await Awa.Client.Utilities.Activity.ActivityUtilities.ReadFileActivity(parameters.FilePath);

        // Call to General utilities from within Workflow utilities
        var paths = await Awa.Client.Utilities.General.GeneralUtilities.GetWorkflowPaths(workflowId);
        // ... rest of implementation
    }
}
```

**Important**: Ensure the proper class reference is used (ActivityUtilities vs WorkflowUtilities vs GeneralUtilities) based on where the target method is defined.

## Partial Class Structure for Utility Functions

When translating individual utility functions, they should be generated as static methods within a partial class structure:

- Use the appropriate namespace based on utility type:
  - Activity utilities: `Awa.Client.Utilities.Activity`
  - Workflow utilities: `Awa.Client.Utilities.Workflow`
  - General utilities: `Awa.Client.Utilities.General`
- Class name MUST match the utility type: use `ActivityUtilities` for activity utilities, `WorkflowUtilities` for workflow utilities, `GeneralUtilities` for general utilities
- Each file should contain only one method within the partial class
- Include necessary using statements at the top of the file
- Functions are accessed with their full namespace path:
  - `Awa.Client.Utilities.Activity.ActivityUtilities.MyFunction()`
  - `Awa.Client.Utilities.Workflow.WorkflowUtilities.MyFunction()`
  - `Awa.Client.Utilities.General.GeneralUtilities.MyFunction()`

**IMPORTANT**: The class name and namespace must be determined by the utility_type parameter:

- If utility_type is "activity", use namespace `Awa.Client.Utilities.Activity` with class `public static partial class ActivityUtilities`
- If utility_type is "workflow", use namespace `Awa.Client.Utilities.Workflow` with class `public static partial class WorkflowUtilities`
- If utility_type is "general", use namespace `Awa.Client.Utilities.General` with class `public static partial class GeneralUtilities`

**Example for Activity Utility:**

```csharp
using System;
using System.Threading.Tasks;
using Temporalio.Workflows;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        public static async Task<string?> ReadFileActivity(string filePath, string? defaultValue = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
                Constants.AWA_ACTIVITY_READ_FILE,
                new object?[] { filePath, defaultValue },
                new()
                {
                    TaskQueue = Constants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(Constants.FileIoTimeoutSeconds)
                });
        }
    }
}
```

**Example for Workflow Utility:**

```csharp
using System;
using System.Threading.Tasks;
using Temporalio.Workflows;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        public static async Task<string?> ExecuteAgentWorkflow(AgentConfiguration agentConfig)
        {
            return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<string?>(
                Constants.AWA_WORKFLOW_EXECUTE_AGENT,
                new object?[] { agentConfig },
                new()
                {
                    TaskQueue = Constants.AwaDefaultTaskQueue,
                    ExecutionTimeout = TimeSpan.FromSeconds(Constants.AgentTimeoutSeconds)
                });
        }
    }
}
```

**Example for General Utility:**

```csharp
using System;
using System.IO;
using Awa.Client.Models;

namespace Awa.Client.Utilities.General
{
    public static partial class GeneralUtilities
    {
        public static WorkflowPaths GetWorkflowPaths(string workflowDir, string workflowType, string workflowId)
        {
            // Direct implementation without Temporal calls
            var projectRoot = FindProjectRoot(workflowDir);
            return new WorkflowPaths
            {
                ProjectRoot = projectRoot,
                WorkflowRoot = Path.Combine(projectRoot, "workflows", workflowType),
                WorkflowId = workflowId
            };
        }
    }
}
```

## Quick Reference

- **Timeouts**: `timedelta(minutes=5)` → `TimeSpan.FromMinutes(5)`
- **Activities**: Use constant string names: `ActivityConstants.METHOD_NAME, new object[] { args }`
- **Child Workflows**: Use constant string names: `WorkflowConstants.WORKFLOW_NAME, new object[] { args }`
- **Options**: Use `new() { Property = value }` syntax
- **Parallel**: `asyncio.gather(*tasks)` → `Task.WhenAll(tasks)`
- **Optional Parameters**: C# handles them natively in method signatures
- **Type Safety**: C# provides compile-time checking vs Python's runtime checking

## Single Implementation Rule

**NEVER create both sync and async versions of the same function.** When translating Python utilities:

### Implementation Guidelines
- Create only ONE implementation per function
- If the Python function uses `async`/`await` or calls Temporal activities/workflows, create an async version
- If the Python function is synchronous and doesn't need async operations, create a sync version
- NEVER create duplicate implementations with sync/async variants

### Examples
```csharp
// CORRECT: Single async implementation for async operations
public static async Task<WorkflowPaths> GetWorkflowPaths(string workflowId)
{
    // async implementation calling Temporal
    return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<WorkflowPaths>(...);
}

// CORRECT: Single sync implementation for sync operations
public static string FormatWorkflowId(string prefix, int id)
{
    // synchronous string formatting
    return $"{prefix}-{id}";
}

// INCORRECT: Never create both versions
// public static WorkflowPaths GetWorkflowPaths(string workflowId) // ❌
// public static async Task<WorkflowPaths> GetWorkflowPaths(string workflowId) // ❌
```

Note: The async nature is indicated by the return type (`Task<T>`), not the method name. NEVER use "Async" suffix.
