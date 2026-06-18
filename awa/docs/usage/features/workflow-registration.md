---
title: Workflow Registration
description: How to register workflows from external workers with AWA
outline: [2, 3]
---

# AWA Workflow Registration

AWA provides a workflow registration mechanism that allows external workers to register their workflows with the AWA platform. Once registered, these workflows become discoverable and executable through the AWA Web UI and the AWA MCP server.

:::warning AWA Registration vs. Temporal Registration
AWA's workflow registration mechanism is distinct from [Temporal's native type (workflow and activity) registration mechanism](https://docs.temporal.io/develop/python/core-application#register-types).

Your worker MUST register all activities and workflows with Temporal for them to be executed via Temporal.

AWA workflow registration is optional and only required if you want your workflow to show up in the AWA Web UI and MCP server.
:::

## What Happens During Registration

When a worker registers with AWA:

1. **Storage**: The registration data is stored in AWA's registry (located in `~/.awa/registry/workers/`)
2. **Web UI Discovery**: Registered workflows appear in the AWA Web UI's workflow list, allowing users to execute them through the interface
3. **MCP Tool Generation**: Workflows marked with `exposed: true` become available as MCP tools, enabling AI agents to discover and execute them
4. **Overwrite Behavior**: If a worker with the same name already exists, the new registration overwrites the previous one (latest registration wins)

## Registration Data Model

### WorkerRegistration

The main registration payload contains:

| Field            | Type                     | Required | Description                                                          |
| ---------------- | ------------------------ | -------- | -------------------------------------------------------------------- |
| `worker_name`    | string                   | Yes      | Unique identifier for the worker                                     |
| `worker_version` | string                   | Yes      | Version of the worker                                                |
| `task_queue`     | string                   | Yes      | Primary Temporal task queue for the worker                           |
| `generated_at`   | datetime                 | No       | Timestamp when registration was generated (defaults to current time) |
| `workflows`      | list[WorkflowDefinition] | No       | List of available workflows                                          |
| `activities`     | list[ActivityDefinition] | No       | List of available activities                                         |

### WorkflowDefinition

Each workflow in the registration includes:

| Field             | Type    | Required | Description                                                                      |
| ----------------- | ------- | -------- | -------------------------------------------------------------------------------- |
| `name`            | string  | Yes      | Workflow class name                                                              |
| `task_queue`      | string  | Yes      | Task queue for workflow execution                                                |
| `input_schema`    | object  | Yes      | JSON Schema for workflow input validation                                        |
| `exposed`         | boolean | No       | Whether to expose as public (API + MCP tool) (default: false)                    |
| `description`     | string  | No\*     | Human-readable description for the workflow (\*required if exposed is true)      |
| `mcp_exposed`     | boolean | No       | **DEPRECATED:** Use `exposed` instead. Whether to expose as an MCP tool          |
| `mcp_description` | string  | No       | **DEPRECATED:** Use `description` instead. Human-readable description for MCP    |

:::info Backward Compatibility
The `mcp_exposed` and `mcp_description` fields are deprecated but still supported for backward compatibility. If both old and new fields are provided, the new fields (`exposed` and `description`) take precedence. Support for the deprecated fields will be removed in a future version.
:::

### ActivityDefinition

Each activity in the registration includes:

| Field          | Type   | Required | Description                               |
| -------------- | ------ | -------- | ----------------------------------------- |
| `name`         | string | Yes      | Activity function name                    |
| `task_queue`   | string | Yes      | Task queue for activity execution         |
| `input_schema` | object | Yes      | JSON Schema for activity input validation |

### Input Schema Requirements

The `input_schema` field must be a valid JSON Schema with:

- `type: "object"` at the root level
- `properties` object containing parameter definitions
- Each property must specify a `type` field
- Optional: `required` array for mandatory fields
- Optional: Validation rules (minimum, maximum, pattern, etc.)

Example input schema:

```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "The message to process"
    },
    "timeout": {
      "type": "integer",
      "minimum": 1,
      "maximum": 300,
      "description": "Processing timeout in seconds"
    }
  },
  "required": ["message"]
}
```

## Making the Registration API Call

To register your worker, send a POST request to the AWA API registration endpoint:

### Endpoint

```
POST /api/v1/workers/register
```

### Request Body Example

```json
{
  "worker_name": "my-custom-worker",
  "worker_version": "1.0.0",
  "task_queue": "my-custom-queue",
  "workflows": [
    {
      "name": "ProcessDataWorkflow",
      "task_queue": "my-custom-queue",
      "input_schema": {
        "type": "object",
        "properties": {
          "data_url": {
            "type": "string",
            "description": "URL of the data to process"
          },
          "format": {
            "type": "string",
            "enum": ["json", "csv", "xml"],
            "description": "Data format"
          }
        },
        "required": ["data_url", "format"]
      },
      "exposed": true,
      "description": "Process data from a URL in various formats"
    }
  ],
  "activities": [
    {
      "name": "fetch_data",
      "task_queue": "my-custom-queue",
      "input_schema": {
        "type": "object",
        "properties": {
          "url": {
            "type": "string"
          }
        },
        "required": ["url"]
      }
    },
    {
      "name": "transform_data",
      "task_queue": "my-custom-queue",
      "input_schema": {
        "type": "object",
        "properties": {
          "data": {
            "type": "object"
          },
          "format": {
            "type": "string"
          }
        },
        "required": ["data", "format"]
      }
    }
  ]
}
```

### Response

A successful registration returns a `201 Created` status with:

```json
{
  "message": "Worker registered successfully",
  "worker_name": "my-custom-worker",
  "registration_id": "my-custom-worker_2024-01-15T10:30:00.000000"
}
```

### Error Responses

- **401 Unauthorized**: Invalid or missing service token
- **422 Unprocessable Entity**: Invalid registration data (e.g., malformed JSON schema)
- **500 Internal Server Error**: Registration storage failure

## Implementation Example (Python)

See the example implementation at `cookbook/recipes/utilities/registration_client.py` for Python code demonstrating worker registration on startup (including automatic discovery of workflows).

## API Reference

For complete API documentation, see the [Worker Registration API Reference](/reference/api#registration-register-worker-capabilities).
