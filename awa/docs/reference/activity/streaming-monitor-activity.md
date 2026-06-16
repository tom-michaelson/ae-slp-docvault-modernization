# `streaming-monitor-activity`

Monitors streaming events for a session via the API in real-time.

This activity connects to AWA's streaming API endpoint and captures events as they are emitted during agent execution. It's designed to work in parallel with activities that emit streaming events, providing real-time monitoring and event capture capabilities for debugging and observability.

## Parameters

| Name              | Type  | Description                                                    |
| ----------------- | ----- | -------------------------------------------------------------- |
| `session_id`      | `str` | The session identifier to monitor for streaming events        |
| `timeout_seconds` | `int` | Maximum time to monitor for events. Defaults to 60 seconds.   |

## Returns

| Type                 | Description                                                                                                 |
| :------------------- | :---------------------------------------------------------------------------------------------------------- |
| `dict[str, Any]`     | Dictionary containing monitoring results, captured events, and session metadata                            |

### Return Dictionary Fields

| Name               | Type           | Description                                                           |
| ------------------ | -------------- | --------------------------------------------------------------------- |
| `success`          | `bool`         | Whether monitoring completed successfully                             |
| `events_captured`  | `int`          | Total number of events captured during monitoring                     |
| `events`           | `list[dict]`   | Array of captured event objects with full event data                 |
| `session_id`       | `str`          | The monitored session identifier                                      |
| `stream_url`       | `str`          | The streaming endpoint URL that was monitored                        |
| `error`            | `str` (optional) | Error message if monitoring failed or timed out                      |

## Event Types Captured

The activity captures various streaming event types:

- **`connection`** - Initial connection established
- **`execution_start`** - Agent execution begins
- **`agent_created`** - Agent instance created successfully
- **`agent_execution_start`** - Agent starts processing prompt
- **`model_response_delta`** - Incremental response generation
- **`model_response_complete`** - Final response generated
- **`execution_complete`** - Successful execution completion
- **`execution_error`** - Error during execution
- **`stream_complete`** - Stream ended normally
- **`error`** - Stream error occurred

## Configuration

The activity automatically reads API server configuration from environment:

- **API Host**: From `AWA_API_HOST` environment variable (default: `localhost`)
- **API Port**: From `AWA_API_PORT` environment variable (default: `8001`)
- **Endpoint**: Constructs URL as `http://{host}:{port}/api/v1/agents/stream/{session_id}/live`

## Usage

::: code-group

```python [Python - Parallel Monitoring]
import asyncio
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class StreamingWorkflow:
    @workflow.run
    async def run(self, config: dict) -> dict:
        session_id = workflow.info().workflow_id

        # Start monitoring and agent execution in parallel
        monitor_task = asyncio.create_task(
            workflow.execute_activity(
                "monitor_streaming_events",
                args=[session_id, 30],
                start_to_close_timeout=timedelta(seconds=40)
            )
        )

        agent_task = asyncio.create_task(
            workflow.execute_activity(
                "agent-execute",
                args=[config],
                start_to_close_timeout=timedelta(seconds=120)
            )
        )

        # Wait for both tasks
        agent_result = await agent_task
        monitor_result = await monitor_task

        return {
            "agent_result": agent_result,
            "streaming_events": monitor_result
        }
```

```python [Python - Sequential Monitoring]
from temporalio import workflow
from datetime import timedelta

@workflow.defn
class DebugWorkflow:
    @workflow.run
    async def run(self, session_id: str) -> dict:
        # Monitor an existing session
        result = await workflow.execute_activity(
            "monitor_streaming_events",
            args=[session_id, 60],
            start_to_close_timeout=timedelta(seconds=70)
        )

        workflow.logger.info(f"Captured {result['events_captured']} events")

        return result
```

```typescript [TypeScript]
import { proxyActivities } from "@temporalio/workflow";
import type * as activities from "./activities";

const { "monitor_streaming_events": monitorStreaming } = proxyActivities<
  typeof activities
>({
  startToCloseTimeout: "1 minute",
});

export async function debugWorkflow(sessionId: string): Promise<any> {
  const result = await monitorStreaming(sessionId, 60);

  console.log(`Captured ${result.events_captured} events`);

  return result;
}
```

```csharp [C#]
using Temporalio.Workflows;
using System.Threading.Tasks;

[Workflow]
public class DebugWorkflow
{
    [WorkflowRun]
    public async Task<object> RunAsync(string sessionId)
    {
        var result = await Workflow.ExecuteActivityAsync<object>(
            "monitor_streaming_events",
            new object[] { sessionId, 60 },
            new() {
                StartToCloseTimeout = TimeSpan.FromMinutes(1)
            }
        );

        return result;
    }
}
```

:::

## Streaming Event Structure

Captured events follow this general structure:

```json
{
  "type": "execution_start",
  "data": {
    "agent_name": "my-agent",
    "model": "azure:gpt-4",
    "prompt_length": 150
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "session_id": "workflow-123"
}
```

### Common Event Fields

| Field       | Type   | Description                                   |
| ----------- | ------ | --------------------------------------------- |
| `type`      | `str`  | Event type identifier                         |
| `data`      | `dict` | Event-specific payload data                   |
| `timestamp` | `str`  | ISO timestamp when event was emitted         |
| `session_id`| `str`  | Session identifier for the streaming session |

## Error Handling

The activity handles various error conditions gracefully:

### Connection Errors
- **HTTP Status**: Non-200 responses from streaming endpoint
- **Network Issues**: Connection failures, timeouts
- **Return**: `{"success": false, "error": "HTTP 404", ...}`

### Timeout Handling
- **Behavior**: Stops monitoring after specified timeout
- **Return**: `{"success": false, "error": "timeout", ...}`

### Cancellation
- **Behavior**: Graceful handling of workflow cancellation
- **Return**: `{"success": true, "error": "cancelled", ...}`

### JSON Parsing Errors
- **Behavior**: Logs warning and continues monitoring
- **Impact**: Malformed events are skipped, monitoring continues

## Best Practices

### Parallel Execution Pattern
```python
# Recommended: Start monitor before agent execution
monitor_task = asyncio.create_task(monitor_activity)
await asyncio.sleep(1.0)  # Let monitor establish connection
agent_task = asyncio.create_task(agent_activity)

# Wait with proper timeout handling
done, pending = await asyncio.wait(
    [agent_task, monitor_task],
    return_when=asyncio.FIRST_COMPLETED
)
```

### Timeout Configuration
- **Monitor Timeout**: Should be longer than expected agent execution time
- **Activity Timeout**: Should be longer than monitor timeout to allow cleanup
- **Recommended**: Monitor timeout + 10 seconds for activity timeout

### Event Processing
```python
monitor_result = await monitor_task
events = monitor_result.get("events", [])

# Filter specific event types
execution_events = [e for e in events if e.get("type") == "execution_start"]

# Extract streaming content
for event in events:
    if event.get("type") == "model_response_delta":
        content = event.get("data", {}).get("content", "")
        # Process streaming content
```

## Integration with Agent Streaming

This activity is designed to work with agents that emit streaming events:

1. **Custom Agents**: Any agent that emits events via AWA's streaming HTTP client
2. **Session Coordination**: Uses workflow ID as session ID for automatic coordination
