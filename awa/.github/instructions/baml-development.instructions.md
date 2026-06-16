---
applyTo: "**/*.baml, **/baml_src/**/*.py"
---

# BAML Development Guide

This guide provides comprehensive patterns and best practices for BAML development, including schema design, function patterns, prompt engineering, testing, and Python integration.

## BAML Development Patterns

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


## AWA Integration

## Integration with Temporal Workflows

When using BAML functions within Temporal activities:

```python
from temporalio import activity
from baml_client import b
from baml_client.types import YourRequest, YourResult

@activity.defn
async def process_with_baml(request: YourRequest) -> YourResult:
    """Process data using BAML function within Temporal activity."""
    try:
        # BAML functions are synchronous in Python
        result = b.YourFunction(request)
        activity.logger.info(f"BAML processing completed: {result}")
        return result
    except Exception as e:
        activity.logger.exception("BAML processing failed")
        raise
```

## AWA Project Integration

When working with BAML in AWA projects:

1. **Code Organization**: Keep BAML files in the `baml_src/` directory
2. **Generated Code**: Generated Python client code should be imported from `baml_client`
3. **Testing**: Include BAML test blocks alongside your Python unit tests
4. **Documentation**: Document BAML functions and their expected inputs/outputs

## Development Commands

### BAML Client Generation
```bash
make baml                        # Generate BAML client
uv run -m scripts.generate_baml_client
```

Always regenerate the BAML client after making changes to BAML files:
- Run `make baml` to generate client
- Generated client code appears in the `baml_client` module
- Import types and functions from `baml_client` and `baml_client.types`

## Dynamic BAML Support

AWA's `transform_activity` core activity supports dynamic BAML. The caller provides string BAML in the `baml_content` parameter.

### How Dynamic BAML Works

1. Compute the dynamic BAML client name by combining the workflow's task queue and the BAML function name
2. Write BAML file to `awa/baml_dynamic/{queue_name}/{function_name}/baml_src/{function_name}.baml`
3. Generate BAML client for the dynamic directory
4. Provide the module name for this new BAML client to the LlmInvoker
5. Execute the transform

Client generation only happens the first time the worker sees a given BAML file, making subsequent executions fast.

## Monitoring and Observability

- Log BAML function calls and results for debugging
- Monitor token usage and costs
- Set up alerts for function failures
- Use structured logging for better observability

### Logging Best Practices

```python
from awa.core.logger.logger import LoggerComponent, get_logger

# Get appropriate logger for context
activity_logger = get_logger(LoggerComponent.ACTIVITY)

@activity.defn
async def baml_processing_activity(request: ProcessRequest) -> ProcessResult:
    """Process data using BAML with proper logging."""
    activity_logger.info("Starting BAML processing", extra={
        "request_type": type(request).__name__,
        "function_name": "ProcessData"
    })

    try:
        result = b.ProcessData(request)
        activity_logger.info("BAML processing completed successfully", extra={
            "result_type": type(result).__name__,
            "tokens_used": getattr(result, "tokens_used", None)
        })
        return result
    except Exception as e:
        activity_logger.exception("BAML processing failed", extra={
            "error_type": type(e).__name__,
            "function_name": "ProcessData"
        })
        raise
```

## Configuration Integration

BAML integrates with AWA's configuration system:

- LLM provider configurations are shared between BAML and other AWA components
- Use `config.yaml` for provider settings
- Environment variables for API keys and secrets
- Langfuse integration for LLM call monitoring

## Best Practices for AWA + BAML

### Always
- Use `{{ ctx.output_format }}` in prompts for type safety
- Generate client after BAML changes: `make baml`
- Structure prompts with `{{ _.role("system") }}` and `{{ _.role("user") }}`
- Use descriptive enums instead of numeric confidence scores

### Never
- Make arrays optional in BAML (use empty arrays)
- Hardcode JSON schema in prompts
- Use recursive types
- Skip BAML client generation after schema changes

### Error Handling Patterns

```python
from baml_client import b
from baml_client.types import MyRequest, MyResult
from awa.core.logger.logger import get_logger, LoggerComponent

logger = get_logger(LoggerComponent.ACTIVITY)

@activity.defn
async def robust_baml_activity(request: MyRequest) -> MyResult:
    """Execute BAML function with comprehensive error handling."""
    try:
        # Validate input before processing
        if not request.task or not request.inputs:
            raise ValueError("Invalid request: missing required fields")

        # Execute BAML function
        result = b.MyFunction(request)

        # Validate output
        if not isinstance(result, MyResult):
            raise TypeError(f"Unexpected result type: {type(result)}")

        logger.info("BAML function executed successfully")
        return result

    except ValueError as e:
        logger.error(f"Input validation failed: {e}")
        raise
    except TypeError as e:
        logger.error(f"Type validation failed: {e}")
        raise
    except Exception as e:
        logger.exception("Unexpected error in BAML execution")
        # Re-raise to let Temporal handle retries
        raise
```

## Testing BAML Functions

### Unit Testing with BAML Test Blocks

Include BAML test blocks in your `.baml` files:

```baml
test TestProcessData {
    functions [ProcessData]
    args {
        request {
            task "Analyze the following data"
            inputs [
                {
                    id "1"
                    content "Sample data for testing"
                }
            ]
        }
    }
}
```

### Integration Testing with Activities

```python
import pytest
from temporalio.testing import ActivityEnvironment
from baml_client.types import ProcessRequest

@pytest.mark.asyncio
async def test_baml_processing_activity():
    """Test BAML activity integration."""
    activity_env = ActivityEnvironment()

    request = ProcessRequest(
        task="Test processing",
        inputs=[{"id": "1", "content": "test data"}]
    )

    result = await activity_env.run(baml_processing_activity, request)

    assert result is not None
    assert isinstance(result, ProcessResult)
    # Add specific assertions based on expected output
```

## Performance Considerations

- BAML functions are synchronous in Python - don't await them
- Use appropriate timeouts for activities containing BAML calls
- Monitor token usage for cost optimization
- Consider caching strategies for expensive LLM calls
- Use fallback clients for better reliability
