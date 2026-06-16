---
title: API Reference
description: Agentic Workflow Accelerator API
outline: [2, 3]
---

# API Reference

This documentation is automatically generated from the FastAPI OpenAPI specification.

## Endpoints

### Emit stream event

#### POST `/api/v1/agents/stream/emit`

Emit a stream event via HTTP (stores and broadcasts via Socket.IO). Service-authenticated only.

#### Request Body

::: code-group

```json [Example]
// Request body structure
{
  // See schema below
}
```

:::

**Content Type:** `application/json`

| Property | Type | Details |
|----------|------|---------|
| `session_id` | `string` | <Badge type="warning" text="required" />  |
| `event_type` | `string` | <Badge type="warning" text="required" />  |
| `event_data` | `object` | <Badge type="warning" text="required" />  |
| `timestamp` | `unknown` | |

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `success` | `boolean` | <Badge type="warning" text="required" />  |
| `message` | `string` | <Badge type="warning" text="required" />  |
| `event_count` | `unknown` | |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Health

#### GET `/api/v1/health`

Check the health of the AWA services.

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `status` | `HealthStatus` | <Badge type="warning" text="required" />  |

---

### HITL: Get HITL task details

#### GET `/api/v1/hitl/task/{workflow_id}`

Get detailed information about a specific HITL task.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `workflow_id` | `string` | <Badge type="warning" text="required" />  |
| `id` | `string` | <Badge type="warning" text="required" /> Temporal run id |
| `parent_run_id` | `string` | <Badge type="warning" text="required" /> Parent workflow run id |
| `title` | `string` | <Badge type="warning" text="required" />  |
| `description` | `string` | <Badge type="warning" text="required" />  |
| `start_time` | `string` | <Badge type="warning" text="required" />  |
| `markdown` | `string` | <Badge type="warning" text="required" />  |
| `input_schema` | `object` | <Badge type="warning" text="required" />  |
| `attachments` | `string[]` |List of attachment file paths |
| `chat_mode` | `boolean` |Whether task uses chat mode |
| `chat_history` | `HITLChatMessage[]` |List of chat messages |
| `response_received` | `boolean` |Whether a response has been received |
| `timed_out` | `boolean` |Whether the task has timed out |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HITL: Get HITL chat history

#### GET `/api/v1/hitl/task/{workflow_id}/chat/history`

Get the current chat history for a HITL task.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`object[]`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HITL: Send user message to HITL task

#### POST `/api/v1/hitl/task/{workflow_id}/chat/user-message`

Send a user message to a HITL task, triggering workflow processing.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Request Body

::: code-group

```json [Example]
// Request body structure
{
  // See schema below
}
```

:::

**Content Type:** `application/json`

`object`

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`object`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HITL: Send HITL chat message

#### POST `/api/v1/hitl/task/{workflow_id}/message`

Send a chat message to a HITL task in chat mode.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Request Body

::: code-group

```json [Example]
// Request body structure
{
  // See schema below
}
```

:::

**Content Type:** `application/json`

`object`

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`object`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HITL: Submit HITL task response

#### POST `/api/v1/hitl/task/{workflow_id}/submit`

Submit a response to complete a HITL task.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Request Body

::: code-group

```json [Example]
// Request body structure
{
  // See schema below
}
```

:::

**Content Type:** `application/json`

`object`

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`object`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HITL: List HITL tasks

#### GET `/api/v1/hitl/tasks`

List all Human-in-the-Loop tasks awaiting interaction.

#### Parameters

- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`HITLTaskInfo[]`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HITL: List HITL tasks for workflow

#### GET `/api/v1/hitl/tasks/{workflow_id}`

List all HITL tasks for a specific parent workflow.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`HITLTaskInfo[]`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Logs: Get workflow logs

#### GET `/api/v1/logs/workflows/{workflow_id}`

Get execution logs for a workflow.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`offset`** (`string`) <Badge type="info" text="query" /> <Badge type="tip" text="optional" />
- **`limit`** (`string`) <Badge type="info" text="query" /> <Badge type="tip" text="optional" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `workflow_id` | `string` | <Badge type="warning" text="required" />  |
| `logs` | `string[]` | <Badge type="warning" text="required" />  |
| `total_lines` | `integer` | <Badge type="warning" text="required" />  |
| `has_more` | `boolean` | <Badge type="warning" text="required" />  |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Registration: Register worker capabilities

#### POST `/api/v1/workers/register`

Register a worker with its available workflows and activities.

#### Schema Requirements:
* Must have `type: object` at root level
* Must include `properties` field containing property definitions
* Each property must specify a `type` field
* Optional: Include `required` array for mandatory fields
* Optional: Add validation rules (minimum, maximum, pattern, etc.)

#### Request Body

::: code-group

```json [Example]
// Request body structure
{
  // See schema below
}
```

:::

**Content Type:** `application/json`

| Property | Type | Details |
|----------|------|---------|
| `worker_name` | `string` | <Badge type="warning" text="required" /> Unique identifier for the worker |
| `worker_version` | `string` | <Badge type="warning" text="required" /> Version of the worker |
| `task_queue` | `string` | <Badge type="warning" text="required" /> Primary task queue for the worker |
| `generated_at` | `string` |Timestamp when registration was generated |
| `workflows` | `WorkflowDefinition[]` |List of available workflows |
| `activities` | `ActivityDefinition[]` |List of available activities |

#### Responses

#### <Badge type="tip" text="201" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `message` | `string` | <Badge type="warning" text="required" /> Success message |
| `worker_name` | `string` | <Badge type="warning" text="required" /> Name of the registered worker |
| `registration_id` | `string` | <Badge type="warning" text="required" /> Unique registration identifier |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Workflows: Run workflow

#### POST `/api/v1/workflows`

Run a workflow.

#### Parameters

- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Request Body

::: code-group

```json [Example]
// Request body structure
{
  // See schema below
}
```

:::

**Content Type:** `application/json`

| Property | Type | Details |
|----------|------|---------|
| `name` | `string` | <Badge type="warning" text="required" />  |
| `input` | `string` | <Badge type="warning" text="required" />  |
| `task_queue` | `string` |Optional task queue for workflow execution |

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

`object`

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Workflows: List all workflows

#### GET `/api/v1/workflows/list`

List all available workflows from both core application and external workers.

#### Parameters

- **`task_queue`** (`string`) <Badge type="info" text="query" /> <Badge type="tip" text="optional" /> - Filter by task queue
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `workflows` | `WorkflowInfo[]` | <Badge type="warning" text="required" />  |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Workflow Runs: List workflow runs

#### GET `/api/v1/workflows/runs`

List all running and completed workflow runs.

#### Parameters

- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `workflows` | `WorkflowRun[]` | <Badge type="warning" text="required" />  |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Workflows: Get workflow run details

#### GET `/api/v1/workflows/runs/{run_id}`

Get detailed information about a specific workflow run by run ID.

#### Parameters

- **`run_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `type` | `string` | <Badge type="warning" text="required" />  |
| `id` | `string` | <Badge type="warning" text="required" />  |
| `workflow_id` | `string` | <Badge type="warning" text="required" />  |
| `status` | `WorkflowRunStatus` | <Badge type="warning" text="required" />  |
| `started` | `string` | <Badge type="warning" text="required" />  |
| `duration` | `string` | <Badge type="warning" text="required" />  |
| `monitor` | `string` | <Badge type="warning" text="required" />  |
| `pending_tasks_count` | `integer` | |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### Get workflow agent sessions

#### GET `/api/v1/workflows/{workflow_id}/agent-sessions`

Get all agent streaming sessions associated with a specific workflow.

#### Parameters

- **`workflow_id`** (`string`) <Badge type="info" text="path" /> <Badge type="warning" text="required" />
- **`awa_auth_token`** (`string`) <Badge type="info" text="cookie" /> <Badge type="tip" text="optional" />

#### Responses

#### <Badge type="tip" text="200" />

Successful Response

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `workflow_id` | `string` | <Badge type="warning" text="required" /> The parent workflow ID |
| `sessions` | `AgentSession[]` | <Badge type="warning" text="required" /> List of discovered agent sessions |
| `count` | `integer` | <Badge type="warning" text="required" /> Total number of sessions |

#### <Badge type="warning" text="422" />

Validation Error

**Response Schema** (`application/json`):

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---


## Data Models

### ActivityDefinition

Definition of an activity that can be executed.

| Property | Type | Details |
|----------|------|---------|
| `name` | `string` | <Badge type="warning" text="required" /> The activity function name |
| `task_queue` | `string` | <Badge type="warning" text="required" /> Task queue for activity execution |
| `input_schema` | `object` | <Badge type="warning" text="required" /> JSON Schema for activity input validation (must be valid JSON Schema) |

---

### AgentSession

Model for an individual agent streaming session.

| Property | Type | Details |
|----------|------|---------|
| `session_id` | `string` | <Badge type="warning" text="required" /> Unique session identifier (typically the workflow ID) |
| `session_type` | `AgentSessionType` | <Badge type="warning" text="required" /> Type of session ('agent' or 'parent') |

---

### AgentSessionType

Type of agent streaming session.

`string`

---

### HITLChatMessage

Represents a message in the chat history.

When used as an inbound payload for the `add_system_message` signal, only
`message` and optional `data` need to be supplied. `timestamp` and
`is_human` will be normalized by the workflow (timestamp assigned, is_human
forced to False for system messages / True for human responses).

| Property | Type | Details |
|----------|------|---------|
| `message` | `string` | <Badge type="warning" text="required" />  |
| `data` | `unknown` | |
| `timestamp` | `unknown` | |
| `is_human` | `unknown` | |

---

### HITLTaskDetail

Detailed Information around a HITL Task.

| Property | Type | Details |
|----------|------|---------|
| `workflow_id` | `string` | <Badge type="warning" text="required" /> Parent workflow id |
| `id` | `string` | <Badge type="warning" text="required" /> Temporal run id |
| `parent_run_id` | `string` | <Badge type="warning" text="required" /> Parent workflow run id |
| `title` | `string` | <Badge type="warning" text="required" /> Task title |
| `description` | `string` | <Badge type="warning" text="required" /> Description of task |
| `start_time` | `string` | <Badge type="warning" text="required" /> Datetime of task start |
| `markdown` | `string` | <Badge type="warning" text="required" /> Task Markdown |
| `input_schema` | `object` | <Badge type="warning" text="required" /> Task Schema |
| `attachments` | `string[]` |List of attachment file paths |
| `chat_mode` | `boolean` |Whether task uses chat mode |
| `chat_history` | `HITLChatMessage[]` |List of chat messages |
| `response_received` | `boolean` |Whether a response has been received |
| `timed_out` | `boolean` |Whether the task has timed out |

---

### HITLTaskInfo

Information around a HITL Task.

| Property | Type | Details |
|----------|------|---------|
| `id` | `string` | <Badge type="warning" text="required" /> Unique identifier for a task |
| `workflow_id` | `string` | <Badge type="warning" text="required" /> Parent workflow id |
| `title` | `string` | <Badge type="warning" text="required" /> Task title |
| `description` | `string` | <Badge type="warning" text="required" /> Description of task |
| `start_time` | `string` | <Badge type="warning" text="required" /> Datetime of task start |
| `chat_mode` | `boolean` |Whether task uses chat mode |
| `non_blocking` | `boolean` |Whether task is non-blocking |

---

### HTTPValidationError

| Property | Type | Details |
|----------|------|---------|
| `detail` | `ValidationError[]` | |

---

### HealthResponse

Complete health check response.

| Property | Type | Details |
|----------|------|---------|
| `status` | `HealthStatus` | <Badge type="warning" text="required" /> The health status containing all service components |

---

### HealthStatus

Overall health status containing all service components.

| Property | Type | Details |
|----------|------|---------|
| `temporal_service` | `ServiceStatus` | <Badge type="warning" text="required" /> Status of the Temporal server service |
| `temporal_worker` | `ServiceStatus` | <Badge type="warning" text="required" /> Status of the Temporal worker service |

---

### ServiceStatus

Status of an individual service component.

| Property | Type | Details |
|----------|------|---------|
| `status` | `string` | <Badge type="warning" text="required" /> The status of the service ("up" or "down") |
| `message` | `unknown` |Optional message providing additional details about the status |

---

### StreamEventRequest

Request model for emitting a stream event.

| Property | Type | Details |
|----------|------|---------|
| `session_id` | `string` | <Badge type="warning" text="required" />  |
| `event_type` | `string` | <Badge type="warning" text="required" />  |
| `event_data` | `object` | <Badge type="warning" text="required" />  |
| `timestamp` | `unknown` | |

---

### StreamEventResponse

Response model for stream event operations.

| Property | Type | Details |
|----------|------|---------|
| `success` | `boolean` | <Badge type="warning" text="required" />  |
| `message` | `string` | <Badge type="warning" text="required" />  |
| `event_count` | `unknown` | |

---

### ValidationError

| Property | Type | Details |
|----------|------|---------|
| `loc` | `unknown[]` | <Badge type="warning" text="required" />  |
| `msg` | `string` | <Badge type="warning" text="required" />  |
| `type` | `string` | <Badge type="warning" text="required" />  |

---

### WorkerRegistration

Worker registration payload.

| Property | Type | Details |
|----------|------|---------|
| `worker_name` | `string` | <Badge type="warning" text="required" /> Unique identifier for the worker |
| `worker_version` | `string` | <Badge type="warning" text="required" /> Version of the worker |
| `task_queue` | `string` | <Badge type="warning" text="required" /> Primary task queue for the worker |
| `generated_at` | `string` |Timestamp when registration was generated |
| `workflows` | `WorkflowDefinition[]` |List of available workflows |
| `activities` | `ActivityDefinition[]` |List of available activities |

---

### WorkerRegistrationResponse

Response for successful worker registration.

| Property | Type | Details |
|----------|------|---------|
| `message` | `string` | <Badge type="warning" text="required" /> Success message |
| `worker_name` | `string` | <Badge type="warning" text="required" /> Name of the registered worker |
| `registration_id` | `string` | <Badge type="warning" text="required" /> Unique registration identifier |

---

### WorkflowAgentSessionsResponse

Response model for workflow agent sessions query.

| Property | Type | Details |
|----------|------|---------|
| `workflow_id` | `string` | <Badge type="warning" text="required" /> The parent workflow ID that was queried |
| `sessions` | `AgentSession[]` | <Badge type="warning" text="required" /> List of discovered agent sessions |
| `count` | `integer` | <Badge type="warning" text="required" /> Total number of sessions discovered |

---

### WorkflowDefinition

Definition of a workflow that can be executed.

| Property | Type | Details |
|----------|------|---------|
| `name` | `string` | <Badge type="warning" text="required" /> The workflow class name |
| `task_queue` | `string` | <Badge type="warning" text="required" /> Task queue for workflow execution |
| `input_schema` | `object` | <Badge type="warning" text="required" /> JSON Schema for workflow input validation (must be valid JSON Schema) |
| `exposed` | `boolean` |Whether this workflow should be publicly exposed (API and MCP) |
| `description` | `unknown` |Human-readable description for exposed workflows |
| `mcp_exposed` | `boolean` |[DEPRECATED] Use 'exposed' instead. Whether this workflow should be exposed as an MCP tool |
| `mcp_description` | `unknown` |[DEPRECATED] Use 'description' instead. Human-readable description for MCP tool |

---

### WorkflowInfo

Information about a discovered workflow.

| Property | Type | Details |
|----------|------|---------|
| `name` | `string` | <Badge type="warning" text="required" /> The name of the workflow |
| `module` | `string` | <Badge type="warning" text="required" /> The module where the workflow is defined |
| `parameters` | `object` | <Badge type="warning" text="required" /> List of parameter names with types for the workflow's run method |
| `queues` | `string[]` |List of task queues this workflow is registered to |
| `description` | `unknown` |Optional human-readable description of the workflow |

---

### WorkflowListResponse

Response containing a list of available workflows.

| Property | Type | Details |
|----------|------|---------|
| `workflows` | `WorkflowInfo[]` | <Badge type="warning" text="required" /> List of workflow information objects |

---

### WorkflowLogsResponse

Response containing workflow logs.

| Property | Type | Details |
|----------|------|---------|
| `workflow_id` | `string` | <Badge type="warning" text="required" />  |
| `logs` | `string[]` | <Badge type="warning" text="required" />  |
| `total_lines` | `integer` | <Badge type="warning" text="required" />  |
| `has_more` | `boolean` | <Badge type="warning" text="required" />  |

---

### WorkflowRun

Overall workflow run data.

| Property | Type | Details |
|----------|------|---------|
| `type` | `string` | <Badge type="warning" text="required" /> Name of the workflow |
| `id` | `string` | <Badge type="warning" text="required" /> Temporal Run id |
| `workflow_id` | `string` | <Badge type="warning" text="required" /> Temporal Workflow id |
| `status` | `WorkflowRunStatus` | <Badge type="warning" text="required" /> Workflow status from Temporal |
| `started` | `string` | <Badge type="warning" text="required" /> Timestamp for when the workflow started |
| `duration` | `string` | <Badge type="warning" text="required" /> Duration for how long the workflow ran (or has been running, if it's not completed or terminated) |
| `monitor` | `string` | <Badge type="warning" text="required" /> Link to Temporal UI for monitoring this workflow run |
| `pending_tasks_count` | `integer` |Count of pending child tasks (0 for non-running workflows) |

---

### WorkflowRunListResponse

Lists running and completed workflows.

| Property | Type | Details |
|----------|------|---------|
| `workflows` | `WorkflowRun[]` | <Badge type="warning" text="required" />  |

---

### WorkflowRunPayload

POST data needed to initate a new workflow run.

| Property | Type | Details |
|----------|------|---------|
| `name` | `string` | <Badge type="warning" text="required" /> The name of the workflow to initiate |
| `input` | `string` | <Badge type="warning" text="required" /> Input payload to initiate workflow, in json |
| `task_queue` | `string` |Optional task queue to use for workflow execution |

---

### WorkflowRunStatus

`string`

---
