# Temporal Workflow and Activity Patterns

This guide covers essential patterns for developing Temporal workflows and activities in AWA, including naming conventions, best practices, and common patterns.

## Naming Conventions

Follow these naming conventions for Temporal workflows and activities:
- **Workflow Classes**: Use PascalCase with `Workflow` suffix (e.g., `ProcessDataWorkflow`)
- **Activity Functions**: Use snake_case with `_activity` suffix (e.g., `read_file_activity`)
- **File Names**: Use snake_case with appropriate suffixes (`*_workflow.py`, `*_activity.py`)

## Workflow Definition Standards

- **Structure**: Use class-based workflows, one per file, with `@workflow.defn` and `@workflow.run`.
- **Validation**: Use Pydantic models for complex inputs.
- **Determinism**: All non-deterministic code (I/O, network, etc.) must be in activities.

```python
# Good: Proper workflow structure
from datetime import timedelta
from pydantic import BaseModel
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from awa.core.activities.sample import sample_activity

class MyWorkflowInput(BaseModel):
    name: str

@workflow.defn
class MyWorkflow:
    @workflow.run
    async def run(self, inp: MyWorkflowInput) -> str:
        return await workflow.execute_activity(
            sample_activity, inp.name, start_to_close_timeout=timedelta(seconds=10)
        )

# Bad: Non-deterministic code in workflow
@workflow.defn
class BadWorkflow:
    @workflow.run
    async def run(self, name: str):
        import requests  # Non-deterministic import
        return requests.get("http://example.com")
```

## Activity Patterns

- **Definition**: Use the `@activity.defn` decorator.
- **Type Annotations**: All activity functions must have type hints.
- **Heartbeats**: Use `activity.heartbeat()` for long-running operations to report progress and handle timeouts.
- **Error Handling**: Catch specific exceptions and log them with `activity.logger`.

```python
# Good: Proper activity structure
from datetime import timedelta
from temporalio import activity

@activity.defn
async def process_data_activity(data: dict) -> str:
    try:
        activity.logger.info("Processing data...")
        # Simulate long-running work
        for i in range(10):
            activity.heartbeat(f"Processed {i+1}/10 chunks")
            await asyncio.sleep(1)
        return "Success"
    except Exception:
        activity.logger.exception("Data processing failed")
        raise

# Bad: Missing heartbeats and error handling
@activity.defn
async def bad_activity(data: dict):
    # No heartbeats for long tasks can lead to timeouts.
    # No try/except block hides errors.
    result = do_long_work(data)
    return result
```

## Activity Execution Patterns

- **Timeouts**: Always specify `start_to_close_timeout` for activities.
- **Failures**: Catch and handle activity exceptions gracefully.
- **Imports**: Use `with workflow.unsafe.imports_passed_through():` to import activities.

```python
# Good: Execute activities with timeouts and error handling
try:
    content = await workflow.execute_activity(
        read_file, input_path, start_to_close_timeout=timedelta(seconds=10)
    )
except Exception as e:
    workflow.logger.error(f"Activity failed: {e}")
    raise

# Bad: No timeout or error handling
# This is dangerous and can cause stuck workflows.
content = await workflow.execute_activity(read_file, input_path)
```

## Resource Management

- **Cleanup**: Ensure resources like file handles and network connections are always closed, preferably with context managers (`async with`).
- **Timeouts**: Respect activity timeouts and use them for external calls.

```python
# Good: Proper resource management
import aiohttp

@activity.defn
async def fetch_url_activity(url: str) -> dict:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        activity.logger.error(f"HTTP request failed: {e}")
        raise

# Bad: Leaking resources
@activity.defn
async def leaky_activity(url: str) -> dict:
    # The session is never closed, leading to resource leaks.
    session = aiohttp.ClientSession()
    response = await session.get(url)
    return await response.json()
```

## Deterministic Programming Rules

- **Use Workflow APIs**: Use `workflow.sleep`, `workflow.wait`, and `workflow.logger`.
- **No direct external calls**: All I/O, network, subprocess calls must be in activities.

```python
# Good: Deterministic operations
await workflow.sleep(timedelta(seconds=10))
workflow.logger.info("Logging deterministically")

# Bad: Non-deterministic operations
import asyncio
await asyncio.sleep(10) # Use workflow.sleep instead
print("Side effect")    # Use workflow.logger instead
```

## Long-Running Workflow Patterns

- **Continue-As-New**: Use `workflow.continue_as_new()` for workflows with large event histories (over 10k events) to avoid limits.
- **Signals & Queries**: Use signals for external events (e.g., human approval) and queries to expose state. Keep signal handlers simple.

```python
# Good: Continue-as-new for batch processing
if workflow.info().is_continue_as_new_suggested():
    workflow.continue_as_new(next_page_token)

# Good: Simple signal handler
@workflow.signal
def approve(self, approver_name: str) -> None:
    self.approved = True
    self.approved_by = approver_name
```

## Error Handling & Timeouts

- **Retries**: Use `RetryPolicy` when executing activities that may fail intermittently.
- **Timeouts**: Set reasonable timeouts based on the activity's purpose (e.g., short for file I/O, long for LLM calls).

```python
# Good: Retries for a flaky activity
await workflow.execute_activity(
    flaky_activity,
    data,
    start_to_close_timeout=timedelta(minutes=1),
    retry_policy=RetryPolicy(maximum_attempts=3),
)
```

## Child Workflow Patterns

Use child workflows for:
- Independent logical units that could be started separately
- Operations that need their own retry/timeout policies
- Workloads that benefit from parallel execution

```python
# Good: Child workflow execution
result = await workflow.execute_child_workflow(
    ProcessSubDataWorkflow,
    sub_data,
    id=f"process-sub-{workflow.info().workflow_id}",
    task_queue="data-processing"
)

# Good: Parallel child workflows
async def process_multiple_items(items: list[Item]) -> list[Result]:
    # Start all child workflows in parallel
    child_handles = []
    for i, item in enumerate(items):
        handle = await workflow.start_child_workflow(
            ProcessItemWorkflow,
            item,
            id=f"item-{i}-{workflow.info().workflow_id}"
        )
        child_handles.append(handle)

    # Wait for all to complete
    results = []
    for handle in child_handles:
        result = await handle
        results.append(result)

    return results
```

## Common Anti-Patterns to Avoid

- **Non-deterministic calls**: `random`, `datetime.now()`, file I/O, network calls.
- **Broad exceptions**: `except:` without a specific type.
- **Missing timeouts**: Executing an activity without `start_to_close_timeout`.
- **Complex signal handlers**: Signal handlers should only modify state, not perform complex logic or I/O.
- **Resource leaks**: Not closing file handles, network connections, or other resources.
- **Blocking operations in workflows**: Use activities for any I/O or external operations.
