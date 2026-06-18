"""Main router for API v1 endpoints."""

from fastapi import APIRouter, status

from awa.core.api.authenticated_router import AuthType, create_authenticated_router, create_public_router
from awa.core.api.routes.shared.agent_streaming import (
    StreamEventResponse,
    emit_stream_event,
    get_workflow_agent_sessions,
)
from awa.core.api.routes.shared.health import health
from awa.core.api.routes.shared.logs import router as logs_router
from awa.core.api.routes.shared.registry import register_worker
from awa.core.api.routes.shared.tasks import (
    HITLTaskInfo,
    get_hitl_chat_history,
    get_hitl_task,
    list_hitl_tasks,
    list_hitl_tasks_for_workflow,
    send_hitl_message,
    send_hitl_user_message,
    submit_hitl_task,
)
from awa.core.api.routes.shared.workflows import get_workflow_run, list_workflows, run_workflow, workflow_runs
from awa.core.models.api import (
    HealthResponse,
    HITLTaskDetail,
    WorkerRegistrationResponse,
    WorkflowAgentSessionsResponse,
    WorkflowListResponse,
    WorkflowRun,
    WorkflowRunListResponse,
)

# Create separate routers for different authentication requirements

# Public router for endpoints that don't require authentication
public_router = create_public_router(prefix="/v1")

# Authenticated router for user endpoints (requires user authentication)
authenticated_router = create_authenticated_router(auth_type=AuthType.USER, prefix="/v1")

# Service router for service-to-service endpoints (requires service authentication)
service_router = create_authenticated_router(auth_type=AuthType.SERVICE, prefix="/v1")

# Add public endpoints (no authentication required)
public_router.add_api_route(
    "/health",
    health,
    methods=["GET"],
    tags=["health"],
    response_model=HealthResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Health",
    description="Check the health of the AWA services.",
)

# Add authenticated endpoints (require user authentication)
# Workflow endpoints
authenticated_router.add_api_route(
    "/workflows/list",
    list_workflows,
    methods=["GET"],
    tags=["workflows"],
    response_model=WorkflowListResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Workflows: List all workflows",
    description="List all available workflows from both core application and external workers.",
)

authenticated_router.add_api_route(
    "/workflows/runs",
    workflow_runs,
    methods=["GET"],
    tags=["workflows"],
    response_model=WorkflowRunListResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Workflow Runs: List workflow runs",
    description="List all running and completed workflow runs.",
)

authenticated_router.add_api_route(
    "/workflows",
    run_workflow,
    methods=["POST"],
    tags=["workflows"],
    response_model=dict,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Workflows: Run workflow",
    description="Run a workflow.",
)

# Workflow run details endpoint
authenticated_router.add_api_route(
    "/workflows/runs/{run_id}",
    get_workflow_run,
    methods=["GET"],
    tags=["workflows"],
    response_model=WorkflowRun,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Workflows: Get workflow run details",
    description="Get detailed information about a specific workflow run by run ID.",
)

# Agent Streaming endpoints (legacy endpoints removed - see AgentSessionTrackingMixin for current implementation)

authenticated_router.add_api_route(
    "/workflows/{workflow_id}/agent-sessions",
    get_workflow_agent_sessions,
    methods=["GET"],
    tags=["workflows", "agent-streaming"],
    response_model=WorkflowAgentSessionsResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Get workflow agent sessions",
    description="Get all agent streaming sessions associated with a specific workflow.",
)

# HITL Task endpoints
authenticated_router.add_api_route(
    "/hitl/tasks",
    list_hitl_tasks,
    methods=["GET"],
    tags=["hitl"],
    response_model=list[HITLTaskInfo],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="HITL: List HITL tasks",
    description="List all Human-in-the-Loop tasks awaiting interaction.",
)

authenticated_router.add_api_route(
    "/hitl/tasks/{workflow_id}",
    list_hitl_tasks_for_workflow,
    methods=["GET"],
    tags=["hitl"],
    response_model=list[HITLTaskInfo],
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="HITL: List HITL tasks for workflow",
    description="List all HITL tasks for a specific parent workflow.",
)

authenticated_router.add_api_route(
    "/hitl/task/{workflow_id}",
    get_hitl_task,
    methods=["GET"],
    tags=["hitl"],
    response_model=HITLTaskDetail,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="HITL: Get HITL task details",
    description="Get detailed information about a specific HITL task.",
)

authenticated_router.add_api_route(
    "/hitl/task/{workflow_id}/submit",
    submit_hitl_task,
    methods=["POST"],
    tags=["hitl"],
    response_model=dict,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="HITL: Submit HITL task response",
    description="Submit a response to complete a HITL task.",
)

authenticated_router.add_api_route(
    "/hitl/task/{workflow_id}/message",
    send_hitl_message,
    methods=["POST"],
    tags=["hitl"],
    response_model=dict,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="HITL: Send HITL chat message",
    description="Send a chat message to a HITL task in chat mode.",
)

authenticated_router.add_api_route(
    "/hitl/task/{workflow_id}/chat/history",
    get_hitl_chat_history,
    methods=["GET"],
    tags=["hitl"],
    response_model=list[dict],
    status_code=status.HTTP_200_OK,
    response_model_exclude_unset=True,
    summary="HITL: Get HITL chat history",
    description="Get the current chat history for a HITL task.",
)

authenticated_router.add_api_route(
    "/hitl/task/{workflow_id}/chat/user-message",
    send_hitl_user_message,
    methods=["POST"],
    tags=["hitl"],
    response_model=dict,
    status_code=status.HTTP_200_OK,
    response_model_exclude_unset=True,
    summary="HITL: Send user message to HITL task",
    description="Send a user message to a HITL task, triggering workflow processing.",
)

# Include the logs router (authenticated)
authenticated_router.include_router(logs_router, tags=["logs"])

# Add service endpoints (require service authentication)
worker_reg_desc = """
Register a worker with its available workflows and activities.

#### Schema Requirements:
* Must have `type: object` at root level
* Must include `properties` field containing property definitions
* Each property must specify a `type` field
* Optional: Include `required` array for mandatory fields
* Optional: Add validation rules (minimum, maximum, pattern, etc.)
"""

service_router.add_api_route(
    "/workers/register",
    register_worker,
    methods=["POST"],
    tags=["workers"],
    response_model=WorkerRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Registration: Register worker capabilities",
    description=worker_reg_desc,
)

# Agent streaming emit endpoint (service-authenticated)
service_router.add_api_route(
    "/agents/stream/emit",
    emit_stream_event,
    methods=["POST"],
    tags=["agent-streaming"],
    response_model=StreamEventResponse,
    response_model_exclude_unset=True,
    response_model_exclude_none=True,
    summary="Emit stream event",
    description="Emit a stream event via HTTP (stores and broadcasts via Socket.IO). Service-authenticated only.",
)

# Create a main router that combines all sub-routers
router = APIRouter()
router.include_router(public_router)
router.include_router(authenticated_router)
router.include_router(service_router)
