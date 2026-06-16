# Human-in-the-Loop (HITL) Workflow

The HITL workflow enables human interaction within automated workflows, supporting approval flows, data collection, and interactive chat-based processes.

## Overview

The `HITLChildWorkflow` is a reusable child workflow that can be called from any parent workflow to incorporate human decisions or input.

## Supported Patterns

### 1. Blocking Pattern (Default)
Workflow waits for human response before continuing.

```python
# Parent workflow example
from temporalio import workflow
from awa.core.models.hitl import HITLInput
from awa.core.workflows.hitl_child_workflow import HITLChildWorkflow

input_data = HITLInput(
    title="Deployment Approval",
    description="Please approve the production deployment",
    markdown="## Changes\n- Updated API endpoints\n- Database migrations",
    input_schema={
        "type": "object",
        "properties": {
            "approved": {"type": "boolean"},
            "comments": {"type": "string"}
        }
    }
)

result = await workflow.execute_child_workflow(
    HITLChildWorkflow.run,
    input_data,
    id=f"hitl-{workflow.info().workflow_id}",
)

if result.timed_out:
    # Handle timeout
    pass
elif result.response and result.response.data.get("approved"):
    # Proceed with deployment
    pass
```

### 2. Non-Blocking Pattern
Workflow continues immediately while human interaction happens asynchronously.

```python
input_data = HITLInput(
    title="Optional Review",
    description="Review if you have time",
    markdown="# Optional Review Task",
    input_schema={"type": "object"},
    non_blocking=True
)
# Child workflow returns immediately. Parent can poll with queries/signals later.
```

### 3. Chat Mode
Interactive conversation with message history.

```python
input_data = HITLInput(
    title="Interactive Debugging",
    description="Help debug this issue",
    markdown="# Error Details\n...",
    input_schema={"type": "object"},
    chat_mode=True
)

# After starting child workflow, parent can send signals:
# workflow.signal_child_workflow(child_handle, "add_system_message", "Update...", {"status": "progress"})
# workflow.signal_child_workflow(child_handle, "submit_response", HITLResponse(...))
```

## Best Practices

1. Always specify an input_schema – even if empty, provide a valid JSON Schema
2. Use meaningful titles and descriptions to provide clear context
3. Set appropriate timeouts and handle timeout cases by checking `timed_out`
4. Use non-blocking mode for optional or long-running tasks where workflow progress should continue
5. Reserve chat mode for collaborative or iterative tasks

## Queries & Signals

Signals:
- `submit_response(HITLResponse)` – Provide the human's response
- `add_system_message(message: str, data: dict | None)` – Append a system message (chat mode only)

Queries:
- `get_context()` – Static context of the interaction
- `get_chat_history()` – Chat transcript (chat mode)
- `is_response_received()` – Boolean flag

## Future API Integration

Planned endpoints (future stories) will support:
- Listing pending HITL tasks
- Retrieving task details
- Submitting responses
- Real-time updates via WebSocket

These enable UI and automation tooling to integrate with HITL workflows seamlessly.
