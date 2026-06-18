# BAML Development Patterns

This guide provides comprehensive patterns and best practices for BAML development, including schema design, function patterns, prompt engineering, testing, and Python integration.

## Schema Definition Patterns

### Classes
```baml
class MyObject {
    // Required fields
    name string
    count int
    enabled bool
    score float

    // Optional fields use ?
    description string? @description("Optional field description")

    // Arrays (cannot be optional)
    tags string[]

    // Enums (must be declared separately)
    status MyEnum?

    // Union types
    type "success" | "error"

    // Nested objects
    nested MyNestedObject

    // Image type for multimodal functions
    image_input image
}

// Enums are declared separately
enum MyEnum {
    PENDING
    ACTIVE @description("Item is currently active")
    COMPLETE
}
```

### Key Schema Rules
- Use descriptive class names in PascalCase
- Add `@description` annotations for complex or non-obvious fields
- Arrays cannot be optional - use empty arrays instead
- Enums must be declared before use
- Use `image` type for visual inputs
- Keep classes focused and cohesive

## Function Patterns

### Basic Function Structure
```baml
function MyFunction(request: MyObject) -> MyResult {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert assistant specializing in [domain].

        {{ _.role("user") }}
        Task: {{ request.task }}

        {{ ctx.output_format }}
    "#
}
```

### Multi-Client Functions (Fallback Support)
```baml
function RobustTransform(request: TransformRequest) -> string {
    client "openai/gpt-4o"
    client "anthropic/claude-3-5-sonnet-latest"
    // First client is primary, others are fallbacks
    prompt #"
        {{ TransformPrompt(request) }}
        {{ ctx.output_format }}
    "#
}
```

### Dynamic Return Types
```baml
class FlexibleWrapper {
    @@dynamic
}

function UserDefinedTransform(request: TransformRequest) -> FlexibleWrapper {
    client "openai/gpt-4o"
    prompt #"
        {{ TransformPrompt(request) }}
        {{ ctx.output_format }}
    "#
}
```

## Template String Patterns

Use template strings for reusable prompt components:

```baml
template_string StandardContext(request: MyRequest) #"
    {% if request.project_context %}
    <project_context>
    {{ request.project_context }}
    </project_context>
    {% endif %}

    {% if request.history %}
    <history>
    {{ request.history }}
    </history>
    {% endif %}
"#

function MyFunction(request: MyRequest) -> MyResult {
    client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are an expert assistant.

        {{ _.role("user") }}
        {{ StandardContext(request) }}

        Task: {{ request.task }}
        {{ ctx.output_format }}
    "#
}
```

## Prompt Engineering Best Practices

- **Output Schema**: Always include `{{ ctx.output_format }}` to ensure the output matches the expected schema.
- **Roles**: Use `{{ _.role("system") }}` and `{{ _.role("user") }}` to structure prompts.
- **Structure**: Use XML-like tags (e.g., `<task>`, `<context>`) to organize prompt sections.
- **Conditionals**: Use Jinja2 syntax (`{% if %}`, `{% for %}`) for dynamic prompts.

```baml
// Good: Structured prompt with required elements
prompt #"
    {{ _.role("system") }}
    You are a helpful assistant.

    {{ _.role("user") }}
    <task>{{ request.task }}</task>

    {{ ctx.output_format }}
"#
```

## Testing Patterns

- **Structure**: Define tests using the `test` block.
- **Coverage**: Test for realistic scenarios, edge cases, and optional fields.

```baml
// Good: A well-defined test case
test TestMyFunction {
    functions [MyFunction]
    args {
        request {
            task "A sample task for testing."
        }
    }
}
```

## Error Handling & Validation

- **Retries**: Configure a `retry_policy` for functions that might fail intermittently.
- **Validation**: Use `@assert` for field-level validation instead of creating validation functions.
- **Enums**: Prefer enums over string literals for constrained choices (e.g., confidence scores).

## Python Integration Patterns

### Usage Patterns
```python
from baml_client import b
from baml_client.types import TransformRequest, TransformResult

# Synchronous execution (BAML functions are sync in Python)
def execute_transform(task: str, content: str) -> TransformResult:
    request = TransformRequest(
        task=task,
        inputs=[{"id": "1", "content": content}],
        role="Expert Assistant"
    )
    return b.ExecuteTransform(request)

# Error handling
try:
    result = b.MyFunction(request)
    assert isinstance(result, ExpectedType)
except Exception as e:
    logger.exception("BAML function execution failed")
    # Handle gracefully
```

### Type Safety
- Generated types are Pydantic classes in Python
- Use type hints consistently
- Validate inputs before calling BAML functions
- Handle exceptions gracefully with proper logging

## Common Anti-Patterns to Avoid

- **Don't** manually write JSON schema in prompts; use `{{ ctx.output_format }}`.
- **Don't** use numbers for confidence scores; use descriptive enums (e.g., `"high" | "medium" | "low"`).
- **Don't** hardcode API keys; use environment variables.
- **Don't** use recursive types or inline class definitions.
- **Don't** make arrays optional; use empty arrays instead.
