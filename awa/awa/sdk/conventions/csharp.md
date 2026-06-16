# C# Utility Function Conventions

## Overview

This document defines the C# conventions for generating utility functions in the AWA SDK. These conventions ensure consistency with the existing C# SDK models and follow C# best practices.

## Project Context

All constants should be placed in a file here: `Awa.Client/Constants/AwaConstants.cs` in a class called `AwaConstants` within a namespace called `Awa.Client.Constants`.

## Naming Conventions

### Namespaces

- **Convention**: Must match the folder structure, preceeded by the project name. So a class in a folder called "MyFolder" within a project called "Projects.MyProject" would have a namespace of `Projects.MyProject.MyFolder`.
- **Example**: `Awa.Client.Utilities`
- **Rationale**: Consistent with C# naming conventions and generated SDK model classes

### Classes

- **Convention**: PascalCase for class names
- **Example**: `MyUtil`, `DataProcessor`, `ValidationHelper`
- **Rationale**: Consistent with C# naming conventions and generated SDK model classes

### Methods

- **Convention**: PascalCase for method names. NEVER append `Async` suffix, even for async methods
- **Generated Utilities**: Preserve the Python utility name in PascalCase. Keep tokens like `Activity`/`Workflow` in place.
  - Examples:
    - Python `read_file_activity` → C# `ReadFileActivity`
    - Python `execute_agent_workflow` → C# `ExecuteAgentWorkflow`
- **Method References**: When calling utility methods from within the same utility class, use the full method name including namespace qualifiers if needed:
  - Example: `ActivityUtilities.ReadFileActivity(...)` when calling from another utility
- **Rationale**: Ensures consistent callsites and prevents confusion. The async nature is indicated by the return type (`Task` or `Task<T>`).

### Variables and Parameters

- **Convention**: camelCase for variables and parameters
- **Example**: `inputModel`, `outputData`, `isValid`
- **Rationale**: Standard C# convention for local variables and parameters

### Properties

- **Convention**: PascalCase for properties (consistent with generated models)
- **Example**: `PropA`, `PropB`, `PropC`
- **Rationale**: Matches existing SDK model property naming

## Class Structure

### Constants Classes

See the example below for how to structure a constants class.

```csharp
using System;

namespace MyNamespace
{
    public static class XyzConstants
    {
        public const string MyConstant = "my-constant-value";
    }
}
```

### Utility Classes

```csharp
public static class MyUtil
{
    public static MyOutputModel MyUtilFunction(MyInputModel inputModel)
    {
        // Implementation
        return new MyOutputModel
        {
            PropC = new MyChildOutputModel { PropE = inputModel.PropA },
            PropD = true
        };
    }
}
```

### Key Patterns:

- Use static classes for utility functions
- All methods should be public static
- Group related utility functions in the same class
- Use object initializer syntax for model creation

## Method Signatures

### Static Methods

```csharp
public static ReturnType MethodName(ParameterType parameterName)
{
    // Implementation
    return result;
}
```

### Access Modifiers

- **Public**: All utility methods should be public
- **Static**: All utility methods should be static
- **Class**: Utility classes should be public static

### Type Annotations

- **Required**: All parameters and return types must have explicit type declarations
- **Nullable Types**: IMPORTANT - Use `?` for nullable reference types when appropriate (parameters and return types)
- **Generic Types**: Use generic type constraints when applicable

## Import Conventions

### Using Statements

```csharp
using System;
using System.Collections.Generic;
using System.Linq;
using SdkModels;
```

### Using Order

1. System namespaces
2. Third-party namespaces
3. Local/SDK namespaces

## Temporal Activity/Workflow Calls (AWA-Specific)

- When calling Temporal activities/child workflows, use nullable object arrays for args:

```csharp
await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
    ActivityConstants.METHOD_NAME,
    new object?[] { arg1, nullableArg },
    new() { StartToCloseTimeout = TimeSpan.FromMinutes(5) });

await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<string?>(
    WorkflowConstants.WORKFLOW_NAME,
    new object?[] { arg1, nullableArg },
    new() { ExecutionTimeout = TimeSpan.FromHours(1) });
```

- Use `Dictionary<string, object?>` where values may be null.
- Prefer safe access patterns:

```csharp
return dict.TryGetValue("key", out var value) ? value : null;
```

## Model Instantiation Patterns

### Creating New Models

```csharp
// Object initializer syntax (preferred)
var outputModel = new MyOutputModel
{
    PropC = new MyChildOutputModel { PropE = inputModel.PropA },
    PropD = true
};

// With conditional logic
var outputModel = new MyOutputModel
{
    PropC = condition ? new MyChildOutputModel { PropE = inputModel.PropA } : null,
    PropD = someBoolean
};
```

### Accessing Model Properties

```csharp
// Direct property access
var value = inputModel.PropA;
var optionalValue = inputModel.PropB; // May be null

// Safe access with null coalescing
var value = inputModel.PropB ?? 0;
```

## Error Handling Patterns

### Basic Validation

```csharp
public static MyOutputModel ValidateAndProcess(MyInputModel inputModel)
{
    if (string.IsNullOrEmpty(inputModel.PropA))
    {
        throw new ArgumentException("PropA is required", nameof(inputModel));
    }

    return new MyOutputModel
    {
        PropC = new MyChildOutputModel { PropE = inputModel.PropA },
        PropD = true
    };
}
```

### Exception Types

- Use `ArgumentException` for invalid input data
- Use `ArgumentNullException` for null parameters
- Use `InvalidOperationException` for invalid state

### Null Checks

```csharp
public static MyOutputModel ProcessInput(MyInputModel inputModel)
{
    if (inputModel == null)
        throw new ArgumentNullException(nameof(inputModel));

    // Implementation
}
```

## Documentation Patterns

### XML Documentation

```csharp
/// <summary>
/// Processes input model and returns transformed output.
/// </summary>
/// <param name="inputModel">The input data to process</param>
/// <returns>The processed output data</returns>
/// <exception cref="ArgumentNullException">Thrown when inputModel is null</exception>
/// <exception cref="ArgumentException">Thrown when inputModel is invalid</exception>
public static MyOutputModel MyUtilFunction(MyInputModel inputModel)
{
    // Implementation
}
```

### Class Documentation

```csharp
/// <summary>
/// Utility functions for processing AWA SDK models.
/// </summary>
/// <remarks>
/// This class provides static methods for common data transformations
/// and processing operations on SDK models.
/// </remarks>
public static class MyUtil
{
    // Methods
}
```

## File Organization

### Directory Structure

```
/
├── Models/
│   └── Models.cs
├── Utilities/
│   ├── Activity/
│   │   └── MyActivityUtil.cs
│   ├── Workflow/
│   │   └── MyWorkflowUtil.cs
│   └── General/
│       └── MyGeneralUtil.cs
└── Awa.Client.csproj
```

### Utility Organization

- **Convention**: Utilities are organized into three subdirectories within the Utilities folder
- **Activity/**: Contains utility functions that interact with Temporal activities
- **Workflow/**: Contains utility functions that work within Temporal workflows
- **General/**: Contains general-purpose utility functions used by both activities and workflows

### File Naming

- **Convention**: PascalCase for utility class files
- **Example**: `MyUtil.cs`, `DataProcessor.cs`
- **Rationale**: Matches class name and C# conventions

### Namespace Structure

```csharp
namespace Awa.Client.Utilities.Activity
{
    /// <summary>
    /// Activity utility functions for AWA SDK.
    /// </summary>
    public static class MyActivityUtil
    {
        // Methods
    }
}

namespace Awa.Client.Utilities.Workflow
{
    /// <summary>
    /// Workflow utility functions for AWA SDK.
    /// </summary>
    public static class MyWorkflowUtil
    {
        // Methods
    }
}

namespace Awa.Client.Utilities.General
{
    /// <summary>
    /// General utility functions for AWA SDK.
    /// </summary>
    public static class MyGeneralUtil
    {
        // Methods
    }
}
```

## Testing Patterns

### Unit Test Structure

```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Awa.Client.Models;
using Awa.Client.Utilities.Activity;
using Awa.Client.Utilities.Workflow;
using Awa.Client.Utilities.General;

[TestClass]
public class MyUtilTests
{
    [TestMethod]
    public void MyUtilFunction_ValidInput_ReturnsExpectedOutput()
    {
        // Arrange
        var inputModel = new MyInputModel
        {
            PropA = "test",
            PropB = 42
        };

        // Act
        var result = MyWorkflowUtil.MyUtilFunction(inputModel);

        // Assert
        Assert.IsNotNull(result);
        Assert.AreEqual("test", result.PropC.PropE);
        Assert.IsTrue(result.PropD);
    }

    [TestMethod]
    [ExpectedException(typeof(ArgumentNullException))]
    public void MyUtilFunction_NullInput_ThrowsArgumentNullException()
    {
        // Act
        MyUtil.MyUtilFunction(null);
    }
}
```

## Code Style Guidelines

### Formatting

- Use 4 spaces for indentation
- Opening braces on new lines
- Use var when type is obvious
- Use explicit types for clarity when needed

### Comments

- Use `//` for inline comments
- Use `/// <summary>` for XML documentation
- Comment complex logic and business rules

### Blank Lines

- One blank line between methods
- One blank line between logical sections within methods
- Two blank lines between classes (if multiple classes in same file)

## Async/Await Patterns (Future Consideration)

### Async Methods

```csharp
public static async Task<MyOutputModel> MyUtilFunction(MyInputModel inputModel)
{
    // Async implementation
    return await Process(inputModel);
}
```

### Naming Convention

- NEVER append "Async" to method names, even for async methods
- Return `Task<T>` for async methods with return values
- Return `Task` for async methods without return values
- The async nature is indicated by the return type, not the name

## Async/Sync Method Patterns

### Single Implementation Rule

**NEVER create both sync and async versions of the same function.** Each utility function should have only ONE implementation:

- If the operation is inherently asynchronous (I/O, network calls, Temporal activities), create only the async version
- The async nature is indicated by the return type (`Task<T>` or `Task`), not the method name
- NEVER use "Async" suffix in method names

```csharp
// CORRECT: Single async implementation
public static async Task<WorkflowPaths> GetWorkflowPaths(string workflowId)
{
    return await GetWorkflowPathsDirect(workflowId);
}

// INCORRECT: Do NOT create duplicate sync/async pairs
// public static WorkflowPaths GetWorkflowPaths(string workflowId) // ❌ Don't do this
// public static async Task<WorkflowPaths> GetWorkflowPaths(string workflowId) // ❌ Don't have both
```

**Important**:
- Never mix async signatures without proper await. If a method is marked as async, it must await all async calls within it.
- One function = one implementation (async if needed, sync otherwise)
- Let the caller handle async/await patterns as needed

## LINQ and Extension Methods

### LINQ Usage

```csharp
public static List<MyOutputModel> ProcessMultiple(IEnumerable<MyInputModel> inputs)
{
    return inputs
        .Where(input => !string.IsNullOrEmpty(input.PropA))
        .Select(input => new MyOutputModel
        {
            PropC = new MyChildOutputModel { PropE = input.PropA },
            PropD = true
        })
        .ToList();
}
```

### Extension Methods (if needed)

```csharp
public static class MyInputModelExtensions
{
    public static bool IsValid(this MyInputModel model)
    {
        return !string.IsNullOrEmpty(model.PropA);
    }
}
```

## Performance Considerations

### String Handling

- Use `string.IsNullOrEmpty()` and `string.IsNullOrWhiteSpace()` for validation
- Use `StringBuilder` for complex string operations
- Use string interpolation for simple formatting

### Memory Management

- Prefer object initializer syntax
- Use `using` statements for disposable resources
- Avoid unnecessary allocations in loops
