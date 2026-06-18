# AWA MCP Server Architecture

## Overview
The AWA MCP server provides a clean, minimal interface for workflow management with just 5 core tools. Auto-discovered workflow tools have been removed to prevent namespace pollution.

## Core Tools (5 Total)

### 1. `mcp__awa__health`
- **Purpose**: Health check endpoint
- **Returns**: "OK" string
- **Usage**: Verify MCP server is running

### 2. `mcp__awa__start_workflow`
- **Purpose**: Unified workflow execution (blocking or non-blocking)
- **Parameters**:
  - `workflow` (required): Workflow name
  - `workflow_input` (optional): Input data (JSON string, dict, or list)
  - `task_queue` (optional): Task queue name for external workflows
  - `wait_for_completion` (optional, default: false): If true, blocks until completion
- **Returns**:
  - If `wait_for_completion=false`: `{workflow_id, run_id, status, temporal_ui_link, started_at}`
  - If `wait_for_completion=true`: `{workflow_id, run_id, status, completed_at, temporal_ui_link, result/error}`
- **Usage**:
  - Non-blocking: `start_workflow(workflow="awa-hello-world", workflow_input={"name": "Test"}, wait_for_completion=false)`
  - Blocking: `start_workflow(workflow="awa-hello-world", workflow_input={"name": "Test"}, wait_for_completion=true)`

### 3. `mcp__awa__get_workflow_result`
- **Purpose**: Get result of completed async workflow
- **Parameters**:
  - `workflow_id` (required): Workflow ID from start_workflow
- **Returns**: `{workflow_id, status, completed_at, temporal_ui_link, result/error}`
- **Usage**: `get_workflow_result(workflow_id="20250930_114305_185_46af2")`

### 4. `mcp__awa__list_workflows`
- **Purpose**: List/filter running workflows or get specific workflow details
- **Parameters**:
  - `status` (optional): Filter by status (RUNNING, COMPLETED, FAILED, etc.)
  - `workflow_id` (optional): Get specific workflow by ID
- **Returns**: List of workflow objects with `{workflow_id, run_id, status, workflow_type, duration, pending_tasks_count, temporal_ui_link}`
- **Usage**:
  - List all: `list_workflows()`
  - Filter by status: `list_workflows(status="COMPLETED")`
  - Get specific: `list_workflows(workflow_id="20250930_114305_185_46af2")`

### 5. `mcp__awa__list_available_workflows`
- **Purpose**: Discover available workflows and get their schemas
- **Parameters**:
  - `workflow_name` (optional): Get detailed schema for specific workflow
- **Returns**:
  - If no workflow_name: List of `{name, description, module, is_external}`
  - If workflow_name provided: Detailed schema with `{name, description, module, is_external, parameters, example_usage}`
- **Usage**:
  - List all workflows: `list_available_workflows()`
  - Get workflow schema: `list_available_workflows(workflow_name="awa-hello-world")`

## Workflow Discovery Pattern

**Recommended agent workflow:**
1. Call `list_available_workflows()` to see all available workflows
2. Call `list_available_workflows(workflow_name="...")` to get detailed schema
3. Call `start_workflow(...)` with appropriate parameters to execute
4. If non-blocking, call `get_workflow_result(...)` or `list_workflows(...)` to check status

## Architecture Benefits

- **Clean namespace**: Only 5 tools instead of 30+
- **Dynamic discovery**: Workflows discovered at runtime
- **Flexible execution**: Single tool handles both blocking and non-blocking
- **Consistent monitoring**: All tools return temporal_ui_link for easy debugging
- **Type safety**: Schema provides parameter types and examples

## Removed Features

- **Auto-discovered workflow tools**: Previously registered 25+ individual tools (workflow_awa_hello_world, etc.)
- **execute_workflow function**: Replaced by start_workflow with wait_for_completion parameter
- **get_workflow_status function**: Consolidated into list_workflows

## Implementation Details

File: `awa/core/mcp/mcp_server.py`
- Core tools registered in `create_mcp_app()` function (lines ~1289-1314)
- Auto-discovery still works but tools are NOT registered individually
- Workflows discovered via `discover_mcp_workflows()` function
- Schema extraction via `WorkflowMetadata.parameter_info`
