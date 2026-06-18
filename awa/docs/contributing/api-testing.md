# API Tests

Auto-generated API tests for the AWA (Agentic Workflow Accelerator) system with configurable delays to ensure reliable test execution.

## Quick Start

```bash
# Generate tests from OpenAPI spec
make generate-api-tests

# Run tests with recommended settings
export AWA_TEST_DELAY=1.5
make test-api
```

## Common Commands

| Task | Command |
|------|---------|
| Generate tests | `make generate-api-tests` |
| Run all tests (reliable) | `export AWA_TEST_DELAY=1.5 && make test-api` |
| Run tests fast (dev) | `export AWA_TEST_DELAY=0.0 && make test-api` |
| Run specific test | `make test-api ARGS='-k "test_name"'` |
| Debug with verbose | `export AWA_TEST_DELAY_VERBOSE=1 && make test-api ARGS='-v -s'` |

## Test Data

The test data is organized to support comprehensive testing of API endpoints with various payload scenarios.

### Directory Structure

```
tests/api/test-data/
├── generated/                          # 🆕 Auto-generated test data (gitignored)
│   ├── workflow_run_payload_basic.json
│   ├── workflow_run_payload_variants.json
│   ├── workflow_run_payload_invalid.json
│   ├── worker_registration_basic.json
│   ├── worker_registration_variants.json
│   └── worker_registration_invalid.json
├── hello_human_inputs.json            # Manual test data
├── hello_world_inputs.json            # Manual test data
└── transform_inputs.json              # Manual test data
```

### Test Data Types

#### Auto-Generated Data (`generated/` directory)

The test generation system automatically creates these files based on OpenAPI schemas:

- **`*_basic.json`**: Simple, valid payloads for basic testing
- **`*_variants.json`**: Multiple payload variants including workflow-specific examples
- **`*_invalid.json`**: Invalid payloads for error handling tests

These files are:
- ✅ **Auto-generated** from OpenAPI schemas
- ✅ **Gitignored** to avoid version control conflicts
- ✅ **Regenerated** when schemas change
- ✅ **Comprehensive** covering all POST/PUT endpoints

#### Manual Test Data

These files contain curated test data that requires domain expertise:

- **`hello_human_inputs.json`**: Name variations for hello-human workflow
- **`hello_world_inputs.json`**: Name variations for hello-world workflow
- **`transform_inputs.json`**: Task and content variations for transform workflow

These files are:
- ✅ **Manually maintained** with domain expertise
- ✅ **Version controlled** for consistency
- ✅ **Workflow-specific** with realistic examples
- ✅ **Edge case focused** with special characters and boundary conditions

### Available Workflows

The following AWA workflows are available for testing:

| Workflow Name         | Description                           | Required Input Fields           |
| --------------------- | ------------------------------------- | ------------------------------- |
| `awa-hello-human`     | Interactive human greeting workflow   | `name`                          |
| `awa-hello-world`     | Simple hello world demonstration      | `name`                          |
| `awa-transform`       | Content transformation using LLM      | `task`, `inputs`, `role`        |
| `awa-build-prompt`    | Build prompts from templates          | `template`, `variables`         |
| `awa-execute-agent`   | Execute agent-based tasks             | `agent_mode`, `task`, `context` |
| `awa-transform-batch` | Batch transformation processing       | Multiple transform inputs       |
| `awa-isolated-agent`  | Execute agent in isolated environment | Agent configuration             |

### File Formats

#### Basic Workflow Payloads
Single JSON object with `name` and `input` fields:
```json
{
  "name": "awa-hello-human",
  "input": "{\"name\": \"TestUser\"}"
}
```

#### Workflow Variants
Array of objects with `description` and `payload` fields:
```json
[
  {
    "description": "Hello Human workflow with basic name",
    "payload": {
      "name": "awa-hello-human",
      "input": "{\"name\": \"Alice\"}"
    }
  }
]
```

#### Invalid Payloads
Array of objects with `description`, `payload`, and `expected_error` fields:
```json
[
  {
    "description": "Missing required 'name' field",
    "payload": {
      "input": "{\"name\": \"Test\"}"
    },
    "expected_error": "422 - Validation Error"
  }
]
```

### Regeneration Commands

```bash
# Regenerate all test data and API tests
make generate-api-tests

# Regenerate test data only
python -m tests.api.generation data

# Regenerate API tests only (uses existing test data)
python -m tests.api.generation.generate_api_tests
```

## Configuration

### Test Delays

Delays prevent API server overload and ensure reliable test execution:

| Delay | Use Case | Reliability | Speed |
|-------|----------|-------------|-------|
| `0.0` | Development | ⚠️ Low | 🚀 Fastest |
| `1.0` | Standard testing | ✅ Good | 🚶 Moderate |
| `1.5` | **Recommended** | ✅ High | 🐌 Slower |
| `2.0` | Maximum reliability | ✅ Highest | 🐌 Slowest |
| `random` | Chaos testing | ⚠️ Variable | 🎲 Variable |

### Environment Variables

```bash
export AWA_TEST_DELAY=1.5        # Delay between tests (seconds)
export AWA_TEST_DELAY_VERBOSE=1  # Show timing information
```

### Test Categories

- **Happy Path**: `make test-api ARGS='-k "happy_path"'` - Successful requests
- **Error Handling**: `make test-api ARGS='-k "invalid"'` - Error scenarios
- **Performance**: `make test-api ARGS='-m "performance"'` - Response time tests
- **Schema Validation**: `make test-api ARGS='-k "schema_validation"'` - Response validation

## Directory Structure

```
tests/api/
├── README.md                    # This file
├── conftest.py                  # Test configuration
├── test_generated_api.py        # Generated tests
├── generation/                  # Test generation system
│   └── DEVELOPER.md            # Developer documentation
├── test-data/                   # Test data files
└── openapi_spec.json           # API specification
```

## Troubleshooting

### Quick Diagnosis

```bash
# 1. Verify test generation works
make generate-api-tests

# 2. Check if tests can be collected
make test-api ARGS='--collect-only'

# 3. Run a simple test
export AWA_TEST_DELAY=0.0
make test-api ARGS='-k "health" -v'
```

### Common Issues

#### Tests failing with 500 errors?
- **Solution**: Increase delay: `export AWA_TEST_DELAY=1.5`
- **Why**: API server may be overloaded by rapid requests

#### Tests too slow?
- **Solution**: Reduce delay: `export AWA_TEST_DELAY=0.5` (may see occasional failures)
- **Why**: Trade-off between speed and reliability

#### Module Import Errors?
```bash
# Run from project root
cd /path/to/agentic-workflow-accelerator
python -m tests.api.generation.generate_test_data
```

#### Missing Test Data?
```bash
# Regenerate test data
python -m tests.api.generation data

# Check file structure
ls -la tests/api/test-data/
ls -la tests/api/test-data/generated/
```

#### 404 Not Found Errors?
```bash
# Check API server is running
curl http://localhost:8001/api/v1/health

# Regenerate tests for current API
make generate-api-tests
```

### Debug Techniques

#### Enable Verbose Output
```bash
# Enable verbose pytest output
make test-api ARGS='-v -s --tb=long'

# With delay information
export AWA_TEST_DELAY_VERBOSE=1
make test-api ARGS='-v -s'
```

#### Run Tests Individually
```bash
# Run specific test with no delay
export AWA_TEST_DELAY=0.0
make test-api ARGS='-k "specific_test_name" -v'
```

#### Check System Resources
```bash
# Monitor API server
top -p $(pgrep -f "uvicorn.*api")

# Check server logs
tail -f logs/api.log
```

## Best Practices

### Test Generation
1. **Keep schemas updated**: Ensure OpenAPI spec reflects current API
2. **Validate generated data**: Check that generated payloads are valid
3. **Customize when needed**: Add custom generators for domain-specific fields
4. **Document changes**: Update documentation when adding new workflows

### Test Execution
1. **Use appropriate delays**: Balance speed vs reliability
2. **Monitor failures**: Use verbose mode to understand timing issues
3. **Isolate problems**: Run individual tests for debugging
4. **Validate results**: Check both response codes and content

### Maintenance
1. **Regular regeneration**: Regenerate tests after schema changes
2. **Quality checks**: Run linting and validation
3. **Documentation updates**: Keep documentation synchronized
4. **Performance monitoring**: Track test execution times

## Development Guide

For detailed information about the test generation system, custom generators, and extending the framework, see [API Test Generation - Developer Guide](./api-test-generation-developer.md).

## Related Documentation

- **[API Test Generation - Developer Guide](./api-test-generation-developer.md)** - Test generation system implementation
- **[Main Project Documentation](/introduction/)** - AWA project documentation
