# `emit_hitl_chat_message`

Emit a Human-In-The-Loop (HITL) system message via Socket.IO.

This activity enables workflows to send real-time messages to connected HITL chat sessions through Socket.IO. It's designed to be fault-tolerant, meaning socket emission failures won't cause the workflow to fail.

## Parameters

| Name        | Type                    | Description                                              |
| :---------- | :---------------------- | :------------------------------------------------------- |
| `task_id`   | `str`                   | The HITL task identifier for routing messages.          |
| `message`   | `str`                   | The message content to send.                            |
| `data`      | `dict[str, Any] | None` | Optional structured data to include with the message.   |
| `timestamp` | `datetime | None`       | Optional timestamp (defaults to current time if not provided). |

## Returns

| Type   | Description |
| :----- | :---------- |
| `None` | No return value. |

## Usage

::: code-group

```python [Python]
from temporalio import workflow
from datetime import timedelta, datetime

@workflow.defn
class HITLWorkflow:
    @workflow.run
    async def run(self, task_id: str, user_message: str):
        # Send a simple message
        await workflow.execute_activity(
            "emit_hitl_chat_message",
            args=[task_id, "Processing your request..."],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Send a message with additional data
        await workflow.execute_activity(
            "emit_hitl_chat_message",
            args=[
                task_id,
                "Analysis complete",
                {"status": "completed", "results": {"score": 95}},
                datetime.now()
            ],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=10)
        )
```

```typescript [TypeScript]
import { proxyActivities } from '@temporalio/workflow';
import type * as activities from './activities';

const { emit_hitl_chat_message } = proxyActivities<typeof activities>({
  startToCloseTimeout: '10 seconds',
  taskQueue: 'awa_default'
});

export async function hitlWorkflow(taskId: string, userMessage: string) {
  // Send a simple message
  await emit_hitl_chat_message(taskId, "Processing your request...");

  // Send a message with additional data
  await emit_hitl_chat_message(
    taskId,
    "Analysis complete",
    { status: "completed", results: { score: 95 } },
    new Date()
  );
}
```

:::

## Error Handling

This activity is designed to be resilient to Socket.IO connection issues:

- Socket emission failures are caught and logged but don't cause the activity to fail
- The workflow will continue even if the message cannot be delivered
- Failed emissions are logged for debugging purposes

## Common Use Cases

### Progress Updates

```python
await workflow.execute_activity(
    "emit_hitl_chat_message",
    args=[task_id, f"Processing step {step}/{total_steps}..."],
    task_queue="awa_default",
    start_to_close_timeout=timedelta(seconds=10)
)
```

### Structured Status Updates

```python
await workflow.execute_activity(
    "emit_hitl_chat_message",
    args=[
        task_id,
        "Validation results",
        {
            "validation_passed": True,
            "checks": {
                "syntax": "passed",
                "logic": "passed",
                "performance": "warning"
            }
        }
    ],
    task_queue="awa_default",
    start_to_close_timeout=timedelta(seconds=10)
)
```

### Error Notifications

```python
await workflow.execute_activity(
    "emit_hitl_chat_message",
    args=[
        task_id,
        "An error occurred",
        {"error_type": "ValidationError", "details": str(error)}
    ],
    task_queue="awa_default",
    start_to_close_timeout=timedelta(seconds=10)
)
```

## Integration with HITL Chat Mode

This activity is primarily used within HITL (Human-In-The-Loop) workflows where real-time communication with users is required. It integrates with the AWA Socket.IO server to deliver messages to connected chat clients.

### Typical HITL Workflow Pattern

```python
@workflow.defn
class InteractiveRequirementsWorkflow:
    @workflow.run
    async def run(self, task_id: str, initial_request: str):
        # Notify user that processing has started
        await workflow.execute_activity(
            "emit_hitl_chat_message",
            args=[task_id, "Analyzing your requirements..."],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Process requirements...

        # Send clarifying questions
        await workflow.execute_activity(
            "emit_hitl_chat_message",
            args=[
                task_id,
                "I have some clarifying questions:",
                {"questions": questions_list}
            ],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=10)
        )

        # Wait for user response...

        # Send final results
        await workflow.execute_activity(
            "emit_hitl_chat_message",
            args=[
                task_id,
                "Requirements analysis complete",
                {"requirements": structured_requirements}
            ],
            task_queue="awa_default",
            start_to_close_timeout=timedelta(seconds=10)
        )
```
