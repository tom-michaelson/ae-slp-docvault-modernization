class TranslateConstantsRequest {
    python_constants string
    target_language string
    target_language_conventions string
}

class TranslateConstantsResult {
    thoughts string @description("Your thoughts on the function and translating it to the target language.")
    translated_constants_content string @description("The translated constants content.")
}

function TranslateConstants(request: TranslateConstantsRequest) -> TranslateConstantsResult {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        You are an expert in Python and {{ request.target_language }}.

        You are given a Python constants file and you need to translate it to {{ request.target_language }}.

        <target_language_conventions>
        {{request.target_language_conventions}}
        </target_language_conventions>

        {{ _.role("user") }}

        <python_constants>
        {{request.python_constants}}
        </python_constants>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestTranslateConstants {
  functions [TranslateConstants]
  args {
    request {
        python_constants #"
# Activity Names
AWA_PREFIX = "awa-"
ACTIVITY_SAY_HELLO = f"{AWA_PREFIX}say-hello"
ACTIVITY_IS_DIRECTORY = f"{AWA_PREFIX}is-directory"
ACTIVITY_READ_FILE = f"{AWA_PREFIX}read-file"
ACTIVITY_READ_FILE_BYTES = f"{AWA_PREFIX}read-file-bytes"
ACTIVITY_READ_FILE_OR_DIRECTORY = f"{AWA_PREFIX}read-file-or-directory"
ACTIVITY_WRITE_FILE = f"{AWA_PREFIX}write-file"
ACTIVITY_COPY_DIRECTORY = f"{AWA_PREFIX}copy-directory"
ACTIVITY_LIST_DIRECTORY = f"{AWA_PREFIX}list-directory"
ACTIVITY_READ_DIRECTORY = f"{AWA_PREFIX}read-directory"
ACTIVITY_EXECUTE_AGENT = f"{AWA_PREFIX}execute-agent"
ACTIVITY_TRANSFORM = f"{AWA_PREFIX}transform"
ACTIVITY_GENERATE_BAML_CLIENT = f"{AWA_PREFIX}generate-baml-client"
ACTIVITY_INVOKE_MCP_TOOL = f"{AWA_PREFIX}invoke-mcp-tool"
ACTIVITY_RESOLVE_TEMPLATE = f"{AWA_PREFIX}resolve-template"
ACTIVITY_APPLY_DIFF = f"{AWA_PREFIX}apply-diff"
ACTIVITY_PARSE_SCHEMA = f"{AWA_PREFIX}parse-schema"
ACTIVITY_SETUP_ISOLATED_AGENT = f"{AWA_PREFIX}setup-isolated-agent"
ACTIVITY_SETUP_ISOLATED_AGENT_GIT = f"{AWA_PREFIX}setup-isolated-agent-git"
ACTIVITY_SETUP_ISOLATED_AGENT_TEMP = f"{AWA_PREFIX}setup-isolated-agent-temp"
ACTIVITY_SETUP_WORKTREE = f"{AWA_PREFIX}setup-worktree"
ACTIVITY_CLEANUP_ISOLATED_AGENT = f"{AWA_PREFIX}cleanup-isolated-environment"
ACTIVITY_MERGE_WORKTREE_CHANGES = f"{AWA_PREFIX}merge-worktree-changes"
ACTIVITY_COPY_ANALYZE_OUTPUTS = f"{AWA_PREFIX}copy-analyze-outputs"
ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE = f"{AWA_PREFIX}get-parent-workflow-task-queue"
ACTIVITY_READ_JIRA_ISSUE = f"{AWA_PREFIX}read-jira-issue"
ACTIVITY_UPSERT_JIRA_ISSUE = f"{AWA_PREFIX}upsert-jira-issue"
ACTIVITY_ADD_JIRA_COMMENT = f"{AWA_PREFIX}add-jira-comment"

# Workflow Names
WORKFLOW_BUILD_PROMPT = f"{AWA_PREFIX}build-prompt"
WORKFLOW_HELLO_HUMAN = f"{AWA_PREFIX}hello-human"
WORKFLOW_TRANSFORM = f"{AWA_PREFIX}transform"
WORKFLOW_TRANSFORM_BATCH = f"{AWA_PREFIX}transform-batch"
WORKFLOW_EXECUTE_AGENT = f"{AWA_PREFIX}execute-agent"
WORKFLOW_APPLY_SINGLE_FILE_DIFF = f"{AWA_PREFIX}apply-single-file-diff"
WORKFLOW_RESOLVE_TEMPLATE = f"{AWA_PREFIX}resolve-template"
WORKFLOW_HELLO_WORLD = f"{AWA_PREFIX}hello-world"
WORKFLOW_TRANSFORM_FILE = f"{AWA_PREFIX}transform-file"
WORKFLOW_CREATE_PROTOTYPE_FROM_FIGMA = f"{AWA_PREFIX}create-prototype-from-figma"
WORKFLOW_PARSE_SCHEMA = f"{AWA_PREFIX}parse-schema"
WORKFLOW_ISOLATED_AGENT = f"{AWA_PREFIX}isolated-agent"
        "#
        target_language "C#"
        target_language_conventions #"
# C# Utility Function Conventions

## Overview
This document defines the C# conventions for generating utility functions in the AWA SDK. These conventions ensure consistency with the existing C# SDK models and follow C# best practices.

## Naming Conventions

### Classes
- **Convention**: PascalCase for class names
- **Example**: `MyUtil`, `DataProcessor`, `ValidationHelper`
- **Rationale**: Consistent with C# naming conventions and generated SDK model classes

### Methods
- **Convention**: PascalCase for method names
- **Example**: `MyUtilFunction`, `ProcessData`, `ValidateInput`
- **Rationale**: Follows C# naming conventions and .NET guidelines

### Variables and Parameters
- **Convention**: camelCase for variables and parameters
- **Example**: `inputModel`, `outputData`, `isValid`
- **Rationale**: Standard C# convention for local variables and parameters

### Properties
- **Convention**: PascalCase for properties (consistent with generated models)
- **Example**: `PropA`, `PropB`, `PropC`
- **Rationale**: Matches existing SDK model property naming

## Class Structure

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
- **Nullable Types**: Use `?` for nullable reference types when appropriate
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
├── Utils/
│   └── MyUtil.cs
└── Awa.Client.csproj
```

### File Naming
- **Convention**: PascalCase for utility class files
- **Example**: `MyUtil.cs`, `DataProcessor.cs`
- **Rationale**: Matches class name and C# conventions

### Namespace Structure
```csharp
namespace SdkModels.Utils
{
    /// <summary>
    /// Utility functions for processing AWA SDK models.
    /// </summary>
    public static class MyUtil
    {
        // Methods
    }
}
```

## Testing Patterns

### Unit Test Structure
```csharp
using Microsoft.VisualStudio.TestTools.UnitTesting;
using SdkModels;
using SdkModels.Utils;

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
        var result = MyUtil.MyUtilFunction(inputModel);

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
public static async Task<MyOutputModel> MyUtilFunctionAsync(MyInputModel inputModel)
{
    // Async implementation
    return await ProcessAsync(inputModel);
}
```

### Naming Convention
- Append "Async" to async method names
- Return `Task<T>` for async methods with return values
- Return `Task` for async methods without return values

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
        "#
    }
  }
}
