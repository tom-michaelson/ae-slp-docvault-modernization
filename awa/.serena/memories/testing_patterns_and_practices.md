# AWA Testing Patterns and Practices

## Testing Framework & Configuration

### Primary Framework: Pytest
- **Configuration**: `pytest.ini`
- **Python Path**: Project root automatically included
- **Async Support**: `asyncio_mode = auto`
- **Cache Directory**: `./.cache/pytest`
- **Default Timeout**: 30 seconds per test
- **Test Discovery**: Automatic from `tests/` directory

### Coverage Configuration
- **Tool**: pytest-cov
- **Source Paths**: `["awa", "scripts"]`
- **Omitted Paths**: tests, cache, venv, node_modules, generated files
- **Report**: Terminal and HTML coverage reports

## Test Organization Structure

### Directory Structure
```
tests/
├── unit/           # Fast, isolated unit tests
│   └── awa/core/mcp/  # MCP server unit tests
├── api/            # API integration tests
├── workflow/       # Temporal workflow integration tests
├── ui/             # Playwright browser tests
├── utils/          # Test utilities and helpers
├── conftest.py     # Shared pytest configuration
└── models.py       # Test data models
```

### Test File Naming
- **Pattern**: `test_*.py`
- **Mirror Source**: Test structure mirrors `awa/` package structure
- **Descriptive Names**: `test_workflow_execution.py`, `test_api_endpoints.py`
- **MCP Tests**: `test_mcp_server.py`, `test_async_workflows.py`

## Testing Categories & Commands

### 1. Unit Tests (`tests/unit/`)
**Purpose**: Fast, isolated tests of individual components
**Command**: `make test` or `make test-verbose`
**Coverage**: `make test-coverage`

```python
# Example unit test
import pytest
from awa.core.models.config import LLMConfig

class TestLLMConfig:
    """Test LLM configuration model."""

    def test_default_configuration(self):
        """Test default LLM configuration values."""
        config = LLMConfig()
        assert config.default_model is not None

    def test_invalid_model_raises_error(self):
        """Test that invalid model configuration raises error."""
        with pytest.raises(ValidationError):
            LLMConfig(default_model="")
```

### 2. MCP Server Unit Tests (`tests/unit/awa/core/mcp/`)
**Purpose**: Test MCP server functionality in isolation
**Command**: `uv run -m pytest tests/unit/awa/core/mcp/`

```python
# Example MCP server unit test
import pytest
from unittest.mock import AsyncMock, MagicMock
from awa.core.mcp.mcp_server import start_workflow_async, get_workflow_status

class TestAsyncWorkflowTools:
    """Test non-blocking workflow MCP tools."""

    @pytest.fixture
    def mock_temporal_client(self):
        """Mock TemporalClient for testing."""
        mock_client = AsyncMock()
        mock_handle = MagicMock()
        mock_handle.id = "test-workflow-123"
        mock_handle.result_run_id = "run-456"
        mock_client.start_workflow.return_value = mock_handle
        return mock_client

    async def test_start_workflow_async_returns_immediately(self, mock_temporal_client):
        """Test that start_workflow_async returns workflow info immediately."""
        with patch("awa.core.mcp.mcp_server.get_temporal_client", return_value=mock_temporal_client):
            result = await start_workflow_async(
                ctx=MagicMock(),
                workflow="test_workflow",
                workflow_input={"test": "data"}
            )

            assert result["workflow_id"] == "test-workflow-123"
            assert result["status"] == "RUNNING"
            assert "started_at" in result
            mock_temporal_client.start_workflow.assert_called_once()

    async def test_get_workflow_status_returns_current_state(self):
        """Test workflow status retrieval."""
        workflow_id = "test-workflow-123"

        with patch("awa.core.mcp.mcp_server._get_workflow_handle") as mock_get_handle:
            mock_handle = MagicMock()
            mock_handle.describe.return_value.status = "RUNNING"
            mock_get_handle.return_value = mock_handle

            result = await get_workflow_status(ctx=MagicMock(), workflow_id=workflow_id)

            assert result["workflow_id"] == workflow_id
            assert result["status"] == "RUNNING"

    def test_workflow_handle_storage_and_cleanup(self):
        """Test workflow handle storage and cleanup functionality."""
        from awa.core.mcp.mcp_server import (
            _store_workflow_handle,
            _get_workflow_handle,
            _cleanup_completed_workflow
        )

        workflow_id = "test-workflow"
        mock_handle = MagicMock()
        metadata = {"started_at": "2024-01-01T00:00:00Z"}

        # Test storage
        _store_workflow_handle(workflow_id, mock_handle, metadata)
        retrieved_handle = _get_workflow_handle(workflow_id)
        assert retrieved_handle == mock_handle

        # Test cleanup
        _cleanup_completed_workflow(workflow_id)
        assert _get_workflow_handle(workflow_id) is None
```

### 3. API Integration Tests (`tests/api/`)
**Purpose**: Test REST API endpoints and integration
**Command**: `make test-api`
**Requirements**: API server must be running

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test API health check endpoint."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_mcp_server_integration():
    """Test MCP server integration endpoints."""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Test MCP server status
        response = await client.get("/mcp/health")
        assert response.status_code == 200

        # Test workflow execution via API
        workflow_data = {
            "workflow": "test_workflow",
            "input": {"test": "data"}
        }
        response = await client.post("/mcp/workflows/start", json=workflow_data)
        assert response.status_code == 200
```

### 4. Workflow Integration Tests (`tests/workflow/`)
**Purpose**: Test Temporal workflows end-to-end including MCP integration
**Command**: `make test-workflow` (manual service management)
**Command**: `make run-test-workflow` (automatic service management)
**Requirements**: Temporal server and worker must be running

```python
import pytest
from temporalio.testing import WorkflowEnvironment
from awa.core.workflows.data_processing_workflow import DataProcessingWorkflow

@pytest.mark.asyncio
async def test_data_processing_workflow():
    """Test data processing workflow execution."""
    async with WorkflowEnvironment() as env:
        async with env.get_temporal_client() as client:
            result = await client.execute_workflow(
                DataProcessingWorkflow.run,
                input_data={"test": "data"},
                id="test-workflow",
                task_queue="test-queue",
            )
            assert result.success is True

@pytest.mark.asyncio
async def test_mcp_async_workflow_execution():
    """Test non-blocking workflow execution via MCP server."""
    # Start workflow asynchronously
    start_result = await start_workflow_async(
        ctx=test_context,
        workflow="data_processing_workflow",
        workflow_input={"data": "test"}
    )

    workflow_id = start_result["workflow_id"]
    assert start_result["status"] == "RUNNING"

    # Poll for completion
    max_polls = 10
    for _ in range(max_polls):
        status = await get_workflow_status(ctx=test_context, workflow_id=workflow_id)
        if status["status"] == "COMPLETED":
            break
        await asyncio.sleep(1)

    # Get final result
    result = await get_workflow_result(ctx=test_context, workflow_id=workflow_id)
    assert result["status"] == "COMPLETED"
    assert "result" in result
```

### 5. UI Tests (`tests/ui/`)
**Purpose**: End-to-end browser automation tests
**Commands**:
- `make test-ui` - Headless mode
- `make test-ui-headed` - Headed mode (visible browser)
- `make test-ui-debug` - Debug mode with dev tools

```python
import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_workflow_dashboard_loads():
    """Test that workflow dashboard loads correctly."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("http://localhost:3000/dashboard")

        # Wait for dashboard content
        await page.wait_for_selector('[data-testid="workflow-list"]')

        # Verify dashboard elements
        title = await page.title()
        assert "AWA Dashboard" in title

        await browser.close()
```

## Test Execution Patterns

### Service Management for Integration Tests

#### Manual Service Management
```bash
# Start services manually
make start-detach

# Run workflow tests
make test-workflow

# Run MCP integration tests
uv run -m pytest tests/workflow/ -k mcp

# Stop services
make stop
```

#### Automatic Service Management
```bash
# Services start/stop automatically
make run-test-workflow
make run-test-workflow-verbose
```

#### All Tests
```bash
make test-all  # Runs unit + api + workflow tests
```

### MCP Server Testing Workflow
```bash
# Test MCP server components in isolation
uv run -m pytest tests/unit/awa/core/mcp/ -v

# Test MCP server integration with services running
make start-detach
uv run -m pytest tests/api/ -k mcp
uv run -m pytest tests/workflow/ -k mcp
make stop
```

## Testing Best Practices

### Unit Test Patterns

#### Arrange-Act-Assert Pattern
```python
def test_workflow_input_validation():
    """Test workflow input validation."""
    # Arrange
    invalid_input = {"missing": "required_field"}

    # Act
    with pytest.raises(ValidationError) as exc_info:
        WorkflowInput(**invalid_input)

    # Assert
    assert "required_field" in str(exc_info.value)
```

#### Parameterized Tests
```python
@pytest.mark.parametrize("model_name,expected_provider", [
    ("gpt-4", "openai"),
    ("claude-3", "anthropic"),
    ("gemini-pro", "google"),
])
def test_model_provider_mapping(model_name, expected_provider):
    """Test model name to provider mapping."""
    provider = get_provider_for_model(model_name)
    assert provider == expected_provider
```

### MCP Server Testing Patterns

#### Mocking External Dependencies
```python
@pytest.fixture
def mock_service_manager():
    """Mock ServiceManager for MCP tests."""
    with patch("awa.core.mcp.mcp_server.ServiceManager") as mock_sm:
        mock_instance = AsyncMock()
        mock_sm.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_workflow_handle():
    """Mock WorkflowHandle for testing."""
    handle = MagicMock()
    handle.id = "test-workflow-123"
    handle.result_run_id = "run-456"
    handle.describe.return_value.status = "COMPLETED"
    return handle
```

#### Testing Handle Storage
```python
def test_handle_storage_prevents_memory_leaks():
    """Test that completed workflows are cleaned up."""
    from awa.core.mcp.mcp_server import (
        _active_workflow_handles,
        _workflow_metadata,
        _store_workflow_handle,
        _cleanup_completed_workflow
    )

    # Store multiple handles
    for i in range(5):
        workflow_id = f"workflow-{i}"
        handle = MagicMock()
        metadata = {"started_at": "2024-01-01T00:00:00Z"}
        _store_workflow_handle(workflow_id, handle, metadata)

    assert len(_active_workflow_handles) == 5
    assert len(_workflow_metadata) == 5

    # Clean up completed workflows
    for i in range(3):
        _cleanup_completed_workflow(f"workflow-{i}")

    assert len(_active_workflow_handles) == 2
    assert len(_workflow_metadata) == 2
```

#### Testing Error Conditions
```python
async def test_get_workflow_result_workflow_not_found():
    """Test error handling when workflow not found."""
    from awa.core.mcp.mcp_server import WorkflowNotFoundError

    with pytest.raises(WorkflowNotFoundError) as exc_info:
        await get_workflow_result(ctx=MagicMock(), workflow_id="nonexistent")

    assert "not found" in str(exc_info.value)

async def test_get_workflow_result_not_completed():
    """Test error handling when workflow not yet completed."""
    workflow_id = "running-workflow"

    with patch("awa.core.mcp.mcp_server._get_workflow_handle") as mock_get:
        mock_handle = MagicMock()
        mock_handle.describe.return_value.status = "RUNNING"
        mock_get.return_value = mock_handle

        with pytest.raises(WorkflowNotCompletedError):
            await get_workflow_result(ctx=MagicMock(), workflow_id=workflow_id)
```

### Mocking Patterns

#### External Service Mocking
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_external_api_call():
    """Test external API call with mocked response."""
    mock_response = {"status": "success", "data": "test"}

    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.status_code = 200

        result = await call_external_api("test-endpoint")
        assert result["status"] == "success"
```

#### Temporal Testing
```python
from temporalio.testing import ActivityEnvironment

@pytest.mark.asyncio
async def test_file_read_activity():
    """Test file read activity in isolation."""
    activity_env = ActivityEnvironment()

    # Mock file system
    with patch("builtins.open", mock_open(read_data="test content")):
        result = await activity_env.run(read_file_activity, "test.txt")
        assert result == "test content"
```

### Fixture Patterns

#### Shared Test Configuration
```python
# conftest.py
@pytest.fixture
async def temporal_client():
    """Provide a test Temporal client."""
    async with WorkflowEnvironment() as env:
        yield env.get_temporal_client()

@pytest.fixture
def sample_workflow_input():
    """Provide sample workflow input data."""
    return {
        "source_path": "test_data/input.txt",
        "target_path": "test_data/output.txt",
        "processing_options": {"format": "json"}
    }

@pytest.fixture
def mcp_test_context():
    """Provide MCP test context."""
    context = MagicMock()
    context.session = MagicMock()
    return context
```

#### Database Fixtures
```python
@pytest.fixture
async def test_database():
    """Provide isolated test database."""
    # Create test database
    test_db = await create_test_database()

    yield test_db

    # Cleanup
    await cleanup_test_database(test_db)
```

## Performance Testing

### Performance Markers
```python
@pytest.mark.performance
def test_large_dataset_processing():
    """Test processing performance with large datasets."""
    # This test is marked as slow/performance
    large_dataset = generate_large_test_data(1000000)

    start_time = time.time()
    result = process_dataset(large_dataset)
    execution_time = time.time() - start_time

    assert result.success
    assert execution_time < 30.0  # Should complete within 30 seconds

@pytest.mark.performance
async def test_mcp_server_concurrent_workflows():
    """Test MCP server handling multiple concurrent workflows."""
    concurrent_count = 10
    tasks = []

    for i in range(concurrent_count):
        task = start_workflow_async(
            ctx=test_context,
            workflow="test_workflow",
            workflow_input={"id": i}
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    assert len(results) == concurrent_count
    assert all(r["status"] == "RUNNING" for r in results)
```

### Running Performance Tests
```bash
# Run only performance tests
uv run -m pytest -m performance

# Skip performance tests
uv run -m pytest -m "not performance"
```

## Error Testing Patterns

### Exception Testing
```python
def test_workflow_handles_missing_file():
    """Test workflow properly handles missing file errors."""
    with pytest.raises(FileNotFoundError) as exc_info:
        process_file("nonexistent_file.txt")

    assert "nonexistent_file.txt" in str(exc_info.value)

def test_workflow_retries_on_temporary_failure():
    """Test workflow retries on temporary failures."""
    with patch("external_service.call") as mock_call:
        # First call fails, second succeeds
        mock_call.side_effect = [ConnectionError(), {"success": True}]

        result = retry_external_call()
        assert result["success"] is True
        assert mock_call.call_count == 2
```

## Test Data Management

### Test Data Files
```
tests/
├── data/
│   ├── sample_workflows/
│   ├── test_configurations/
│   ├── mcp_test_data/
│   └── expected_outputs/
```

### Dynamic Test Data
```python
@pytest.fixture
def workflow_test_data():
    """Generate test data for workflow testing."""
    return {
        "workflows": [
            {"id": f"test-workflow-{i}", "status": "completed"}
            for i in range(5)
        ],
        "expected_results": generate_expected_results()
    }

@pytest.fixture
def mcp_workflow_scenarios():
    """Test scenarios for MCP workflow testing."""
    return [
        {
            "name": "simple_workflow",
            "input": {"task": "process_data"},
            "expected_duration": 5.0
        },
        {
            "name": "complex_workflow",
            "input": {"task": "complex_analysis", "data_size": 1000},
            "expected_duration": 30.0
        }
    ]
```

## Continuous Integration Testing

### Test Matrix
- **Unit Tests**: Run on every commit
- **Integration Tests**: Run on pull requests
- **MCP Integration Tests**: Run on MCP-related changes
- **UI Tests**: Run on deployment candidates
- **Performance Tests**: Run nightly

### Test Commands in CI
```bash
# CI test execution
make test-coverage      # Unit tests with coverage
make test-api          # API integration tests
make run-test-workflow # Workflow integration tests
make test-ui           # UI tests in headless mode

# MCP-specific CI testing
uv run -m pytest tests/unit/awa/core/mcp/ --cov=awa.core.mcp
uv run -m pytest tests/workflow/ -k mcp
```

## MCP Server Testing Requirements

### Pre-Implementation Testing
- Mock-based unit tests for new MCP tools
- Handle storage and cleanup functionality tests
- Error condition and edge case coverage
- Performance tests for concurrent workflow handling

### Implementation Testing
- Integration tests with real Temporal workflows
- End-to-end MCP client testing
- Backward compatibility verification
- Memory leak prevention validation

### Test Coverage Goals
- **Unit Tests**: 95%+ coverage for new MCP functionality
- **Integration Tests**: All 4 new MCP endpoints tested
- **Error Handling**: All error conditions covered
- **Concurrent Usage**: Multiple workflow handling verified
