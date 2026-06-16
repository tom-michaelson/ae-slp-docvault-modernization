# BAML Integration with AWA

This guide covers how to integrate BAML functions within AWA projects, focusing on Temporal workflow integration, monitoring, and best practices.

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
