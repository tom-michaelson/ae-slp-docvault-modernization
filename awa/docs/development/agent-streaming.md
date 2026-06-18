# Agent Streaming Implementation Specification

## Overview

This specification documents the current implementation of real-time streaming for agent activities in the Agentic Workflow Accelerator (AWA). The system provides transparent, real-time streams of agent execution that can be consumed by frontend applications through Socket.IO.

**Key Feature:** Simply set `stream_enabled=True` in your `AgentConfiguration` - session IDs are automatically managed based on workflow hierarchy. No manual configuration required!

**⚠️ Current Support:** Agent streaming is currently only available for **Claude agents**. Other agents (Goose, Codex, OpenCode, Q) do not currently support streaming output. Future updates will add streaming support to additional agents as their underlying CLIs add streaming capabilities.

## Architecture Overview

### Core Components

1. **ExecuteAgentWorkflow** - Stores parent_session_id for query-based discovery
2. **Socket.IO Server** - Centralized streaming event emission
3. **Agent Activities** - Stream-enabled agent execution
4. **Streaming Utilities** - Workflow-level streaming helper classes
5. **API Endpoints** - Session discovery through Temporal queries

### High-Level Flow

1. Workflow sets `stream_enabled=True` in `AgentConfiguration`
2. ExecuteAgentWorkflow automatically sets session IDs:
   - `stream_session_id` defaults to current workflow ID
   - `parent_session_id` defaults to parent workflow ID
3. ExecuteAgentWorkflow stores parent_session_id and exposes it via query
4. Agent activities execute with streaming enabled via `stream_output()`
5. Real-time output is emitted through centralized Socket.IO functions
6. Clients subscribe to specific agent streams via Socket.IO
7. Historical output is stored and replayed for late subscribers
8. API endpoint discovers sessions by querying all ExecuteAgent workflows

### Simplified Configuration Pattern

**The New Way (Recommended):**
```python
agent_config = AgentConfiguration(
    provider="claude",  # ⚠️ Streaming only supported for Claude currently
    mode="act",
    prompt="Your prompt here",
    stream_enabled=True,  # ✅ Only this is required!
    working_directory="/path/to/dir",
)
```

**What Happens Automatically:**
- ✅ `stream_session_id` is set to the current workflow ID
- ✅ `parent_session_id` is set to the parent workflow ID (if workflow has a parent)
- ✅ Streaming activity (`ACTIVITY_EXECUTE_AGENT_STREAMING`) is used automatically
- ✅ Session is discoverable via API (`/api/v1/workflows/{workflow_id}/agent-sessions`)

**When to Override (Advanced):**
```python
agent_config = AgentConfiguration(
    provider="claude",  # ⚠️ Streaming only supported for Claude currently
    mode="act",
    prompt="Your prompt here",
    stream_enabled=True,
    stream_session_id="custom-stream-id",     # ⚙️ Override: custom event destination
    parent_session_id="custom-parent-id",     # ⚙️ Override: custom session grouping
    working_directory="/path/to/dir",
)
```

Use custom IDs only for:
- **Custom session grouping** - Group multiple agents under one parent session
- **Cross-workflow coordination** - Share sessions across different workflow hierarchies
- **Custom session hierarchy** - Build complex session relationships

**For 99% of use cases, just set `stream_enabled=True`!**

**Note:** While streaming is currently only available for Claude agents, the configuration pattern works for all agents. Non-Claude agents will execute normally but won't emit real-time streaming events until their CLIs add streaming support.

## Implementation Guide

### Step 1: Add Agent Streaming to a Workflow

Agent streaming is now fully automatic! Simply set `stream_enabled=True` in your `AgentConfiguration`.

**⚠️ Supported Agents:** Streaming is currently only available for **Claude agents**. Other agents will fall back to non-streaming execution.

#### 1.1 Configure Agent with Streaming

```python
from temporalio import workflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration

@workflow.defn(name="MyWorkflow")
class MyWorkflow:
    """Your workflow with agent streaming."""

    @workflow.run
    async def run(self, workflow_input: MyWorkflowInput) -> str:
        # Configure agent with streaming - only stream_enabled is required!
        agent_config = AgentConfiguration(
            provider="claude",  # ⚠️ Only Claude supports streaming currently
            mode="act",
            prompt="Your prompt here",
            stream_enabled=True,  # This is all you need!
            working_directory="/path/to/dir",
        )

        # Execute agent as child workflow (automatically discoverable)
        agent_result = await workflow.execute_child_workflow(
            sdk_constants.WORKFLOW_EXECUTE_AGENT,
            agent_config,
            id=f"MyAgent-{workflow.info().workflow_id}",
        )

        return agent_result.output
```

**That's it!** When `stream_enabled=True`, the ExecuteAgentWorkflow automatically:
- Sets `stream_session_id` to the current workflow ID (where events are emitted)
- Sets `parent_session_id` to the parent workflow ID (for API discovery)
- Stores the `parent_session_id` and exposes it via a Temporal query
- Uses the streaming activity for real-time output
- No manual configuration or mixins required!

**Optional Customization:**
You can override the automatic session IDs if needed:
```python
agent_config = AgentConfiguration(
    provider="claude",  # ⚠️ Only Claude supports streaming currently
    mode="act",
    prompt="Your prompt here",
    stream_enabled=True,
    stream_session_id="custom-stream-id",     # Override: where to emit events
    parent_session_id="custom-parent-id",     # Override: for API discovery
    working_directory="/path/to/dir",
)
```

**Note:** Setting `stream_enabled=True` on non-Claude agents (Goose, Codex, OpenCode, Q) is safe - they will execute normally but won't emit real-time streaming events. Streaming support will be added to these agents in future releases as their underlying CLIs add streaming capabilities.

### Step 2: Create Streaming Events (Optional)

For workflow-level streaming (progress updates, status messages), create a streaming client:

#### 2.1 Create Streaming Client Class

```python
from awa.core.utils.agent_streaming_utils import AgentStreaming

class MyWorkflowStreaming:
    """Streaming client for MyWorkflow progress updates."""

    def __init__(self, session_id: str):
        """Initialize streaming client."""
        self.session_id = session_id

    async def step_started(self, step_name: str) -> None:
        """Emit step start event."""
        await AgentStreaming.publish_step_start(
            session_id=self.session_id,
            step_name=step_name,
            description=f"Starting {step_name}",
        )

    async def step_completed(self, step_name: str, result: str) -> None:
        """Emit step completion event."""
        await AgentStreaming.publish_step_complete(
            session_id=self.session_id,
            step_name=step_name,
            result=result,
        )

    async def progress_update(self, current: int, total: int, description: str) -> None:
        """Emit progress update."""
        await AgentStreaming.publish_progress(
            session_id=self.session_id,
            current=current,
            total=total,
            description=description,
        )
```

#### 2.2 Use Streaming Client in Workflow

```python
@workflow.run
async def run(self, workflow_input: MyWorkflowInput) -> str:
    # Use workflow ID as session ID for progress updates
    session_id = workflow.info().workflow_id

    # Create streaming client
    streaming = MyWorkflowStreaming(session_id)

    # Emit events at key points
    await streaming.step_started("initialization")
    # ... do work
    await streaming.step_completed("initialization", "Ready to process")

    await streaming.progress_update(0, 10, "Processing files")
    # ... process files
    await streaming.progress_update(10, 10, "All files processed")

    # Execute agent with streaming enabled
    agent_config = AgentConfiguration(
        provider="claude",
        mode="act",
        prompt="Your prompt here",
        stream_enabled=True,  # Automatic session management!
        working_directory="/path/to/dir",
    )
    agent_result = await workflow.execute_child_workflow(
        sdk_constants.WORKFLOW_EXECUTE_AGENT,
        agent_config,
    )
```

### Step 3: Frontend Integration

#### 3.1 Discover Agent Sessions

```typescript
// Get all agent sessions for a workflow
const response = await fetch(`/api/v1/workflows/${workflowId}/agent-sessions`);
const data = await response.json();

// Returns:
// {
//   "workflow_id": "workflow-123",
//   "parent_session_id": "workflow-123",
//   "sessions": [
//     {
//       "session_id": "20250103-abc123",
//       "session_type": "agent",
//       "registered_at": "2025-01-03T10:30:00Z",
//       "metadata": {
//         "agent_provider": "claude",
//         "agent_mode": "act",
//         "prompt_preview": "Implement authentication..."
//       }
//     }
//   ],
//   "count": 1
// }
```

#### 3.2 Subscribe to Agent Stream

```typescript
import io from 'socket.io-client';

// Connect to Socket.IO server
const socket = io('http://localhost:8000', {
  auth: { token: 'your-auth-token' }
});

// Subscribe to agent stream
socket.emit('subscribe_agent_stream', { session_id: 'agent-session-123' });

// Listen for stream events
socket.on('agent_stream_start', (data) => {
  console.log('Agent started:', data);
  // { session_id, timestamp, agent_type, status: 'started' }
});

socket.on('agent_stream_output', (data) => {
  console.log('Agent output:', data.content);
  // { session_id, content, chunk_index, is_final, timestamp, agent_type }
});

socket.on('agent_stream_complete', (data) => {
  console.log('Agent completed:', data);
  // { session_id, timestamp, final_result, execution_time, agent_type, status: 'completed' }
});

socket.on('agent_stream_error', (data) => {
  console.error('Agent error:', data);
  // { session_id, timestamp, error, error_code, agent_type, status: 'error' }
});

// Receive historical output for late subscribers
socket.on('agent_stream_history', (data) => {
  console.log('Historical events:', data.history);
  // { session_id, history: [...all previous events] }
});

// Unsubscribe when done
socket.emit('unsubscribe_agent_stream', { session_id: 'agent-session-123' });
```

#### 3.3 Listen to Workflow-Level Events

```typescript
// Subscribe to workflow logs/messages
socket.emit('subscribe_workflow', { workflow_id: 'workflow-123' });

// Listen for workflow events (emitted by streaming clients)
socket.on('log_entry', (data) => {
  console.log('Workflow message:', data.message);
  // { workflow_id, timestamp, level, component, message }
});
```

## Core Components Reference

### ExecuteAgentWorkflow

**Location:** `awa/core/workflows/execute_agent_workflow.py`

**Purpose:** Executes AI agents and provides query-based session discovery with automatic session ID management.

**Query Methods:**
- `get_parent_session_id()` - Returns the parent_session_id from AgentConfiguration

**How it works:**
1. When ExecuteAgentWorkflow receives an AgentConfiguration with `stream_enabled=True`:
   - Automatically sets `stream_session_id` to current workflow ID (if not provided)
   - Automatically sets `parent_session_id` to parent workflow ID (if not provided)
2. Stores `parent_session_id` in `self._parent_session_id`
3. Uses streaming activity (`ACTIVITY_EXECUTE_AGENT_STREAMING`) automatically
4. API can query all ExecuteAgent workflows and filter by parent_session_id
5. No manual session ID configuration or mixins needed!

**Automatic Session ID Logic:**
```python
if agent_config.stream_enabled:
    workflow_info = workflow.info()

    # Auto-set parent_session_id to parent workflow ID
    if not agent_config.parent_session_id:
        agent_config.parent_session_id = (
            workflow_info.parent.workflow_id if workflow_info.parent else None
        )

    # Auto-set stream_session_id to current workflow ID
    if not agent_config.stream_session_id:
        agent_config.stream_session_id = workflow_info.workflow_id
```

### Socket.IO Emission Functions

**Location:** `awa/core/api/socketio_server.py`

**Agent Streaming Functions:**

```python
async def emit_agent_stream_start(
    session_id: str,
    agent_type: str | None = None
) -> None:
    """Emit agent stream start notification."""

async def emit_agent_stream_output(
    session_id: str,
    content: str,
    chunk_index: int,
    is_final: bool = False,
    agent_type: str | None = None,
    timestamp: datetime | None = None,
) -> None:
    """Emit real-time agent output."""

async def emit_agent_stream_complete(
    session_id: str,
    final_result: dict[str, Any] | None = None,
    execution_time: float | None = None,
    agent_type: str | None = None,
) -> None:
    """Emit agent execution completion."""

async def emit_agent_stream_error(
    session_id: str,
    error_message: str,
    error_code: str | None = None,
    agent_type: str | None = None,
) -> None:
    """Emit agent execution error."""

async def cleanup_agent_session(session_id: str) -> None:
    """Clean up completed agent session data."""
```

**Room Naming Convention:**
- Agent streams: `agent-stream-{session_id}`
- Workflow logs: `{workflow_id}` (workflow ID as room name)

**Session Storage:**
- Global dict: `agent_session_storage[session_id]` - stores all events for history replay
- Automatically populated by emission functions
- Sent to late subscribers via `agent_stream_history` event

### Agent Streaming Utilities

**Location:** `awa/core/utils/agent_streaming_utils.py`

**AgentStreaming Class Methods:**

```python
# Message publishing
await AgentStreaming.publish_message(session_id, message, data)
await AgentStreaming.publish_message_multi(session_ids, message, data)

# Step tracking
await AgentStreaming.publish_step_start(session_id, step_name, description, metadata)
await AgentStreaming.publish_step_complete(session_id, step_name, result, metadata)
await AgentStreaming.publish_step_error(session_id, step_name, error, metadata)

# Progress tracking
await AgentStreaming.publish_progress(session_id, current, total, description, metadata)

# File processing
await AgentStreaming.publish_file_processed(session_id, file_path, status, details, metadata)

# Agent execution
await AgentStreaming.publish_agent_execution(
    session_id, agent_name, operation, file_path, status, result, metadata
)
```

**File/Agent Status Enums:**
```python
from awa.core.utils.agent_streaming_utils import FileStatus, AgentExecutionStatus

# FileStatus: STARTED, COMPLETED, SKIPPED, FAILED
# AgentExecutionStatus: STARTED, COMPLETED, FAILED
```

### Agent Activity Streaming

**Location:** `awa/core/activities/agent.py`

**Streaming Activity:**
```python
@activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT_STREAMING)
async def execute_agent_activity_streaming(
    agent_config: AgentConfiguration
) -> StreamingTaskResponseModel
```

**Agent Configuration Fields for Streaming:**
```python
agent_config = AgentConfiguration(
    provider="claude",                  # Agent provider
    mode="act",                         # Agent mode
    prompt="Your prompt here",          # Agent prompt
    stream_enabled=True,                # Enable streaming (required)
    stream_session_id=None,             # Optional: defaults to workflow ID
    parent_session_id=None,             # Optional: defaults to parent workflow ID
    working_directory="/path/to/dir",
    # ... other config fields
)
```

**How Automatic Session IDs Work:**
- When `stream_enabled=True`, the ExecuteAgentWorkflow automatically sets:
  - `stream_session_id` = current workflow ID (if not provided)
  - `parent_session_id` = parent workflow ID (if not provided and workflow has a parent)
- These defaults work for 99% of use cases
- Override them only for advanced scenarios (e.g., custom session grouping)

**Agent Base Class - stream_output() Method:**

All agent implementations must implement `stream_output()` in their agent mode class:

```python
async def stream_output(
    self,
    prompt: str | None = None,
    command_path: str | None = None,
    working_dir: str | None = None,
    mcp_tools: list[str] | None = None,
    session_id: str | None = None,
) -> CommandResult:
    """Stream live output from agent execution.

    This method should:
    1. Start the agent process
    2. Capture output in real-time
    3. Emit via emit_agent_stream_output()
    4. Store complete output
    5. Return CommandResult with final status
    """
```

**Current Streaming Support:**

| Agent | Streaming Support | Notes |
|-------|------------------|-------|
| **Claude** | ✅ Fully Supported | Real-time streaming via `stream_output()` |
| Goose | ❌ Not Supported | Falls back to `execute_prompt()` - full result returned at once |
| Codex | ❌ Not Supported | Falls back to `execute_prompt()` - full result returned at once |
| OpenCode | ❌ Not Supported | Falls back to `execute_prompt()` - full result returned at once |
| Q (AWS) | ❌ Not Supported | Falls back to `execute_prompt()` - full result returned at once |

**Implementation Reference:**
- **Claude Agent (Streaming):** `awa/core/activities/agent_modes/claude_agent.py:stream_output()` - Full streaming implementation
- **Other Agents (Fallback):** `awa/core/activities/agent_modes/{agent}_agent.py:stream_output()` - Falls back to non-streaming execution

**Future Support:** As agent CLIs add streaming capabilities, their implementations will be updated to provide real-time streaming output.

### API Endpoints

**Get Workflow Agent Sessions:**
```
GET /api/v1/workflows/{workflow_id}/agent-sessions
```

**Response:**
```json
{
  "workflow_id": "string",
  "parent_session_id": "string | null",
  "sessions": [
    {
      "session_id": "string",
      "session_type": "parent | agent | file | custom",
      "registered_at": "ISO datetime",
      "metadata": {
        "agent_provider": "claude",
        "agent_mode": "act",
        "prompt_preview": "First 100 chars...",
        "custom_field": "custom_value"
      }
    }
  ],
  "count": 1
}
```

**Authentication:** Requires user authentication.

## Socket.IO Events Reference

### Client → Server Events

```typescript
// Subscribe to agent stream
socket.emit('subscribe_agent_stream', {
  session_id: 'string'
});

// Unsubscribe from agent stream
socket.emit('unsubscribe_agent_stream', {
  session_id: 'string'
});

// Subscribe to workflow logs
socket.emit('subscribe_workflow', {
  workflow_id: 'string'
});

// Unsubscribe from workflow logs
socket.emit('unsubscribe_workflow', {
  workflow_id: 'string'
});
```

### Server → Client Events

```typescript
// Agent stream started
socket.on('agent_stream_start', {
  session_id: string,
  timestamp: string,
  agent_type: string | null,
  status: 'started'
});

// Real-time agent output
socket.on('agent_stream_output', {
  session_id: string,
  content: string,
  chunk_index: number,
  is_final: boolean,
  timestamp: string,
  agent_type: string | null
});

// Agent stream completed
socket.on('agent_stream_complete', {
  session_id: string,
  timestamp: string,
  final_result: object | null,
  execution_time: number | null,
  agent_type: string | null,
  status: 'completed'
});

// Agent stream error
socket.on('agent_stream_error', {
  session_id: string,
  timestamp: string,
  error: string,
  error_code: string | null,
  agent_type: string | null,
  status: 'error'
});

// Historical events (for late subscribers)
socket.on('agent_stream_history', {
  session_id: string,
  history: Array<Event>  // All previous events
});

// Workflow log entry
socket.on('log_entry', {
  workflow_id: string,
  timestamp: string,
  level: string,
  component: string,
  message: string
});
```

## Example Workflows

### Example 1: TestDoctorWorkflow

**Location:** `awa/core/workflows/test_doctor_workflow.py`

This workflow demonstrates:
- Using workflow ID as parent session ID
- Creating custom streaming client (`TestDoctorStreaming`)
- Emitting workflow-level progress events
- Passing parent_session_id to child workflows for automatic discovery

**Key Features:**
```python
@workflow.defn(name="test-doctor")
class TestDoctorWorkflow:
    @workflow.run
    async def run(self, workflow_input: TestDoctorWorkflowInput) -> str:
        # Use workflow ID as parent session
        parent_session_id = workflow.info().workflow_id

        # Custom streaming client for progress
        streaming = TestDoctorStreaming(parent_session_id)

        await streaming.git_diff_started()
        # ... work
        await streaming.git_diff_completed(file_count)

        # Execute child workflows - they automatically become discoverable
        # by passing parent_session_id in their input
```

### Example 2: TestAndLintPipelineWorkflow

**Location:** `awa/core/workflows/test_and_lint_pipeline_workflow.py`

Similar pattern to TestDoctorWorkflow with additional pipeline-specific streaming events.

## Best Practices

### Session Management

1. **Enable streaming with a single flag** (recommended for most cases):
   ```python
   agent_config = AgentConfiguration(
       provider="claude",
       mode="act",
       prompt="Your prompt here",
       stream_enabled=True,  # Automatic session IDs!
       working_directory="/path/to/dir",
   )
   ```
   The system automatically sets:
   - `stream_session_id` to the current workflow ID
   - `parent_session_id` to the parent workflow ID (for discoverability)

2. **Override session IDs only when needed** (advanced use cases):
   ```python
   agent_config = AgentConfiguration(
       ...
       stream_enabled=True,
       stream_session_id="custom-stream-id",  # Custom: where to emit events
       parent_session_id="custom-parent-id",  # Custom: for API discovery
   )
   ```
   Use custom IDs for scenarios like:
   - Grouping multiple agents under one session
   - Cross-workflow session coordination
   - Custom session hierarchy

3. **Use descriptive workflow IDs** when executing child workflows:
   ```python
   await workflow.execute_child_workflow(
       sdk_constants.WORKFLOW_EXECUTE_AGENT,
       agent_config,
       id=f"TestGenerator-{file_path.replace('/', '_')}-{parent_id}",
   )
   ```
   This makes session metadata easier to parse from the workflow ID.

### Streaming Events

1. **Emit step boundaries** for clear progress tracking:
   ```python
   await streaming.step_started("data_processing")
   # ... do work
   await streaming.step_completed("data_processing", "Processed 100 files")
   ```

2. **Include progress updates** for long-running operations:
   ```python
   for i, file in enumerate(files):
       await streaming.progress_update(i+1, len(files), f"Processing {file}")
   ```

3. **Use structured metadata** instead of encoding info in messages:
   ```python
   # Good
   await streaming.publish_step_start(
       session_id=sid,
       step_name="validation",
       description="Validating inputs",
       metadata={"file_count": 42}
   )

   # Avoid
   await streaming.publish_message(sid, "Validating 42 files")
   ```

### Error Handling

1. **Always emit error events** when operations fail:
   ```python
   try:
       result = await some_operation()
   except Exception as e:
       await streaming.step_error(
           step_name="some_operation",
           error=str(e),
           metadata={"context": "additional info"}
       )
       raise
   ```

2. **Use error codes** for categorization:
   ```python
   await emit_agent_stream_error(
       session_id=sid,
       error_message="Connection timeout",
       error_code="TIMEOUT"
   )
   ```

### Performance Considerations

1. **Batch updates** for high-frequency events (use debouncing in frontend)
2. **Clean up sessions** after workflow completion if needed
3. **Limit metadata size** - keep metadata objects small and focused
4. **Use multi-session helpers** for broadcasting to multiple sessions:
   ```python
   await AgentStreaming.publish_message_multi(
       session_ids=[s1, s2, s3],
       message="Batch processing complete"
   )
   ```

## Security Considerations

### Authentication
- Socket.IO connections require authentication via token
- API endpoints use existing AWA authentication middleware
- Sessions are scoped to authenticated users

### Access Control
- Users can only query sessions for workflows they have access to
- Session IDs are UUIDs to prevent enumeration attacks
- Historical output is stored temporarily and cleaned up

### Data Exposure
- Agent output follows existing logging patterns
- No additional sensitive data exposure beyond normal workflow execution
- Standard log filtering and truncation applies

## Troubleshooting

### Sessions Not Appearing in Discovery

**Problem:** `GET /api/v1/workflows/{workflow_id}/agent-sessions` returns empty list

**Solutions:**
1. Ensure `stream_enabled=True` is set in `AgentConfiguration`
2. Verify ExecuteAgent child workflows have been created
3. Check that workflows are using `WORKFLOW_EXECUTE_AGENT` constant
4. Confirm Temporal can list workflows (check Temporal server connectivity)
5. If using custom `parent_session_id`, verify it matches the queried workflow ID

### No Stream Output Received

**Problem:** Frontend not receiving `agent_stream_output` events

**Solutions:**
1. **Verify agent provider** - Streaming is currently only supported for Claude agents. Other agents (Goose, Codex, OpenCode, Q) will execute but won't stream output in real-time
2. Verify Socket.IO connection is established
3. Check subscription: `socket.emit('subscribe_agent_stream', {session_id})`
4. Ensure `stream_enabled=True` is set in `AgentConfiguration`
5. Verify streaming activity (`ACTIVITY_EXECUTE_AGENT_STREAMING`) is being used
6. Check that `stream_session_id` matches the session ID you're subscribing to
7. Confirm agent implements `stream_output()` method properly

### Historical Output Not Playing Back

**Problem:** Late subscribers don't receive historical events

**Solutions:**
1. Verify `agent_session_storage` is being populated (check socketio_server.py)
2. Ensure emission functions are storing events properly
3. Check that `send_agent_session_history()` is called on subscription
4. Verify session ID matches between subscription and emission

## Future Enhancements

### Planned Improvements

1. **Additional Agent Support** - Add streaming support for Goose, Codex, OpenCode, and Q agents as their CLIs add streaming capabilities
2. **Persistent Session Storage** - Move from in-memory to database storage for longer retention
3. **Session Filtering** - Enhanced discovery API with filtering by status, type, metadata
4. **Session Replay** - Full session replay from start to finish
5. **Interactive Streaming** - Support for user input during agent execution
6. **Multi-Agent Coordination** - Enhanced coordination for parallel agent execution
7. **Metrics and Analytics** - Track streaming performance and usage patterns

### Extension Points

1. **Custom Streaming Clients** - Create domain-specific streaming clients extending `AgentStreaming`
2. **Custom Session Types** - Define new session types beyond "parent", "agent", "file"
3. **Custom Events** - Add new Socket.IO events for specialized use cases
4. **Agent-Specific Metadata** - Extend session metadata for different agent types

## Reference Implementation Files

### Core Files
- `awa/core/workflows/execute_agent_workflow.py` - ExecuteAgent workflow with query support
- `awa/core/api/socketio_server.py` - Socket.IO server and emission functions
- `awa/core/utils/agent_streaming_utils.py` - Streaming utility classes
- `awa/core/activities/agent.py` - Streaming activity implementation
- `awa/core/activities/agent_modes/claude_agent.py` - Claude agent streaming example

### API Files
- `awa/core/api/routes/shared/agent_streaming.py` - Session discovery endpoint
- `awa/core/api/routes/versions/v1/router.py` - API route registration

### Example Workflows
- `awa/core/workflows/test_doctor_workflow.py` - Complete workflow example
- `awa/core/workflows/test_and_lint_pipeline_workflow.py` - Pipeline workflow example

### Frontend Files
- `ui/src/api/agentStreaming.ts` - Frontend API client
- `ui/src/components/agent-detail/AgentDetailView.tsx` - UI component example

### Test Files
- `tests/api/test_get_workflow_agent_sessions.py` - API endpoint tests

## Conclusion

The agent streaming system provides a robust, scalable solution for real-time monitoring of agent executions within AWA workflows. By following this specification, developers can easily add streaming capabilities to any workflow and provide rich, real-time feedback to end users.

For questions or issues, please refer to the AWA documentation or create an issue in the GitHub repository.
