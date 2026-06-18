import json
from datetime import UTC, datetime
from typing import Any

from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from temporalio.api.enums.v1 import WorkflowExecutionStatus
from temporalio.client import WorkflowHandle

from awa.core.api.routes.shared.workflows import get_registry_storage
from awa.core.cli.service_manager import ServiceManager
from awa.core.engine.temporal_client import TemporalClient
from awa.core.engine.workflow_management_client import WorkflowManagementClient
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.mcp.workflow_status_mapper import create_temporal_ui_link, map_temporal_status_to_string
from awa.core.models.api import WorkflowDefinition
from awa.core.models.mcp import (
    StartWorkflowResponse,
    WorkflowProgressInfo,
    WorkflowResultResponse,
    WorkflowStatusResponse,
)
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.workflow_metadata import WorkflowMetadata, format_workflow_parameters, get_workflow_metadata

logger = get_logger(LoggerComponent.SERVER)


# Custom error classes for workflow operations
# These are kept for potential use in internal code, but MCP tools return error dicts instead
class WorkflowNotFoundError(ToolError):
    """Raised when workflow ID not found in storage."""


class WorkflowNotCompletedError(ToolError):
    """Raised when trying to get result from incomplete workflow."""


class WorkflowExecutionError(ToolError):
    """Raised when workflow execution fails."""


# Helper functions for start_workflow refactoring (PLR0915 compliance)
async def _prepare_workflow_input(
    workflow_input: str | dict | list | None,
) -> str | None:
    """Convert workflow input to JSON string if needed.

    Args:
        workflow_input: Input data for the workflow (JSON string, dict, or list)

    Returns:
        JSON string representation of input or None

    Raises:
        ToolError: If serialization fails

    """
    if isinstance(workflow_input, (dict, list)):
        try:
            return json.dumps(workflow_input)
        except (TypeError, ValueError) as e:
            raise ToolError(f"Failed to serialize input data: {e}") from e
    return workflow_input


async def get_workflow_result(workflow_id: str) -> WorkflowResultResponse | dict[str, Any]:
    """Get the result of a completed workflow.

    This function retrieves the result of a workflow that has completed execution.
    It verifies the workflow is complete before attempting result retrieval.

    Args:
        workflow_id: Unique identifier for the workflow

    Returns:
        WorkflowResultResponse containing:
            - workflow_id: The requested workflow ID
            - status: The workflow completion status (COMPLETED, FAILED, CANCELLED, etc.)
            - completed_at: ISO 8601 formatted completion timestamp
            - temporal_ui_link: Link to Temporal UI for monitoring
            - result: The workflow result (only for COMPLETED status)
            - error: The error message (only for FAILED status)
        Or error dict with:
            - error: Error message
            - workflow_id: The requested workflow ID

    """
    # Get workflow handle directly from Temporal
    try:
        service_manager = await ServiceManager.create(terminate_all=False)
        if not service_manager.temporal_client:
            error_msg = "Temporal client not available"
            logger.error(error_msg)
            return {"error": error_msg, "workflow_id": workflow_id}

        client = await service_manager.temporal_client.get_client()
        handle = client.get_workflow_handle(workflow_id)
    except Exception:
        logger.exception(f"Failed to get workflow handle for {workflow_id}")
        return {
            "error": f"Workflow '{workflow_id}' not found. It may have expired or never existed.",
            "workflow_id": workflow_id,
        }

    try:
        # Get the workflow description to check status
        description = await handle.describe()

        # Check if workflow is still running
        if description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_RUNNING:
            logger.info(f"Workflow {workflow_id} is still running")
            return {
                "error": (
                    f"Workflow '{workflow_id}' is still running. Please wait for completion before retrieving results."
                ),
                "workflow_id": workflow_id,
                "status": "RUNNING",
            }

        # Get the status string
        status_str = map_temporal_status_to_string(description.status)

        # Get completion time - use close_time for completed workflows
        completed_at = description.close_time.isoformat() if description.close_time else datetime.now(UTC).isoformat()

        # Generate temporal UI link
        temporal_ui_link = create_temporal_ui_link(workflow_id, description.run_id)

        # Build the base response
        response: dict[str, Any] = {
            "workflow_id": workflow_id,
            "status": status_str,
            "completed_at": completed_at,
            "temporal_ui_link": temporal_ui_link,
        }

        # Handle different completion states
        if description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_COMPLETED:
            # Workflow completed successfully - get the result
            try:
                workflow_result = await handle.result()
                response["result"] = workflow_result
                logger.info(f"Successfully retrieved result for workflow {workflow_id}")
            except Exception as e:
                logger.exception(f"Failed to retrieve result for completed workflow {workflow_id}")
                # Still treat as completed but with error retrieving result
                response["result"] = None
                response["error"] = f"Failed to retrieve result: {e!s}"

        elif description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_FAILED:
            # Workflow failed - try to get error details
            try:
                # Attempt to get the failure details
                await handle.result()  # This will raise the failure exception
            except Exception as e:  # noqa: BLE001
                # Capture the failure reason
                response["error"] = str(e)
                logger.info(f"Workflow {workflow_id} failed with error: {e}")

        elif description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CANCELED:
            # Workflow was cancelled
            response["error"] = "Workflow was cancelled"
            logger.info(f"Workflow {workflow_id} was cancelled")

        elif description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TERMINATED:
            # Workflow was terminated
            response["error"] = "Workflow was terminated"
            logger.info(f"Workflow {workflow_id} was terminated")

        elif description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TIMED_OUT:
            # Workflow timed out
            response["error"] = "Workflow execution timed out"
            logger.info(f"Workflow {workflow_id} timed out")

        else:
            # Other statuses
            response["error"] = f"Workflow ended with status: {status_str}"
            logger.warning(f"Workflow {workflow_id} ended with unexpected status: {status_str}")

        # Return as WorkflowResultResponse
        return WorkflowResultResponse(**response)  # type: ignore[typeddict-item]

    except Exception as e:
        # Handle any unexpected errors
        logger.exception(f"Unexpected error retrieving result for workflow {workflow_id}")
        return {
            "error": f"Failed to retrieve workflow result: {e!s}",
            "workflow_id": workflow_id,
        }


async def discover_mcp_workflows() -> list[tuple[WorkflowMetadata, WorkflowDefinition | None]]:
    """Discover all workflows marked for MCP exposure.

    Filters recipe workflows based on the recipes configuration flag.

    Returns:
        List of tuples containing (workflow_metadata, external_definition_or_none)

    """
    workflows = []

    # Get configuration to check recipes flag
    config = ConfigLoader.get_config()
    include_recipes = config.recipes

    # Log recipe filtering status
    if include_recipes:
        logger.info("Recipe workflows are enabled for MCP discovery")
    else:
        logger.info("Recipe workflows are disabled for MCP discovery")

    try:
        # 1. Get core workflows via get_workflow_metadata() and filter by exposed
        # Pass include_recipes flag so recipe workflows are discovered (will be filtered below if disabled)
        core_workflows = get_workflow_metadata(include_recipes=include_recipes)
        for metadata in core_workflows:
            if getattr(metadata, "exposed", False):
                # Check if this is a recipe workflow
                is_recipe = "cookbook.recipes" in metadata.module

                # Skip recipe workflows if recipes are disabled
                if is_recipe and not include_recipes:
                    logger.debug(f"Skipping recipe workflow (recipes disabled): {metadata.name}")
                    continue

                workflows.append((metadata, None))
                logger.debug(f"Found exposed workflow: {metadata.name} (recipe={is_recipe})")
    except Exception:
        logger.exception("Failed to discover core workflows for exposure")

    try:
        # 2. Get external workflows via get_registry_storage and filter by exposed
        storage = get_registry_storage()
        external_workers = await storage.list_active_workers()

        for worker in external_workers:
            for workflow_def in worker.workflows:
                if getattr(workflow_def, "exposed", False):
                    # Create WorkflowMetadata-like object for external workflows
                    metadata = WorkflowMetadata(
                        name=workflow_def.name,
                        class_name=workflow_def.name,
                        module=f"external.{worker.worker_name}",
                        parameters=[],
                        parameter_info=[],
                        exposed=workflow_def.exposed,
                        description=getattr(workflow_def, "description", None),
                    )
                    # External workflows are not filtered by recipe flag
                    workflows.append((metadata, workflow_def))
                    logger.debug(f"Found MCP-exposed external workflow: {workflow_def.name}")
    except Exception:
        logger.exception("Failed to discover external workflows for MCP exposure")

    logger.info(
        f"MCP workflow discovery complete: {len(workflows)} workflows available "
        f"(recipes {'enabled' if include_recipes else 'disabled'})",
    )
    return workflows


def health() -> str:
    """Check the health of the AWA MCP server."""
    return "OK"


async def _initialize_service_manager() -> ServiceManager:
    """Initialize the service manager for workflow operations.

    Returns:
        ServiceManager instance

    Raises:
        WorkflowExecutionError: If initialization fails

    """
    try:
        return await ServiceManager.create(terminate_all=False)
    except Exception as e:
        error_msg = f"Failed to initialize service manager: {type(e).__name__}: {e}"
        logger.exception(error_msg)
        raise WorkflowExecutionError(error_msg) from e


async def _start_temporal_workflow(
    temporal_client: TemporalClient,
    workflow: str,
    input_for_workflow: str | None,
    task_queue: str | None,
) -> WorkflowHandle:
    """Start workflow using Temporal client.

    Args:
        temporal_client: The Temporal client instance
        workflow: Workflow name
        input_for_workflow: Serialized workflow input
        task_queue: Task queue name

    Returns:
        WorkflowHandle for the started workflow

    Raises:
        WorkflowNotFoundError: If workflow not found
        WorkflowExecutionError: If workflow start fails
        ToolError: For validation errors

    """
    try:
        return await temporal_client.start_workflow(
            workflow=workflow,
            workflow_input=input_for_workflow,
            task_queue=task_queue,
        )
    except ValueError as e:
        # Handle workflow not found or validation errors
        if "workflow" in str(e).lower() and "not found" in str(e).lower():
            raise WorkflowNotFoundError(f"Workflow '{workflow}' not found or not registered") from e
        raise ToolError(f"Invalid workflow parameters: {e}") from e
    except Exception as e:
        # Log the full error for debugging
        logger.exception(f"Failed to start workflow '{workflow}'")

        # Check for specific error patterns
        error_str = str(e).lower()
        if "not found" in error_str or "unknown" in error_str:
            raise WorkflowNotFoundError(f"Workflow '{workflow}' not found or not registered") from e
        if "timeout" in error_str:
            raise WorkflowExecutionError(f"Timed out starting workflow '{workflow}'") from e
        raise WorkflowExecutionError(f"Failed to start workflow '{workflow}': {e}") from e


async def start_workflow(  # noqa: PLR0915
    workflow: str,
    ctx: Context,
    workflow_input: str | dict | list | None = None,
    task_queue: str | None = None,
    wait_for_completion: bool = False,
) -> StartWorkflowResponse | dict[str, Any]:
    """Start a workflow with optional blocking behavior.

    This function starts a workflow and can either return immediately (non-blocking)
    or wait for completion (blocking) based on the wait_for_completion parameter.

    Args:
        workflow: The name of the workflow to start
        ctx: The FastMCP context object
        workflow_input: Input data for the workflow (JSON string, dict, or list)
        task_queue: Optional task queue name for external workflows
        wait_for_completion: If True, blocks until workflow completes and returns result.
                           If False, returns immediately with workflow_id/run_id (default: False)

    Returns:
        If wait_for_completion=False: StartWorkflowResponse containing workflow_id, run_id, status,
            temporal_ui_link, started_at
        If wait_for_completion=True: Dict containing workflow_id, status, completed_at, temporal_ui_link,
            and result/error
        On error: Dict containing error message and workflow name

    """
    try:
        mode = "blocking" if wait_for_completion else "non-blocking"
        await ctx.info(f"Starting workflow '{workflow}' on task queue '{task_queue or 'default'}' ({mode})...")

        # Validate workflow name
        if not workflow:
            error_msg = "Workflow name is required"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow": workflow}

        # Prepare workflow input
        try:
            input_for_workflow = await _prepare_workflow_input(workflow_input)
        except ToolError as e:
            error_msg = f"Failed to prepare workflow input: {e!s}"
            logger.exception(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow": workflow}

        # Initialize service manager
        try:
            service_manager = await _initialize_service_manager()
        except WorkflowExecutionError as e:
            error_msg = f"Failed to initialize service manager: {e!s}"
            logger.exception(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow": workflow}

        # Get the temporal client directly
        if service_manager.temporal_client is None:
            error_msg = "Temporal client not initialized"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow": workflow}

        temporal_client = service_manager.temporal_client

        # Start the workflow using the TemporalClient's start_workflow method
        try:
            workflow_handle = await _start_temporal_workflow(
                temporal_client,
                workflow,
                input_for_workflow,
                task_queue,
            )
        except WorkflowNotFoundError:
            error_msg = f"Workflow '{workflow}' not found or not registered"
            logger.exception(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow": workflow}
        except (WorkflowExecutionError, ToolError) as e:
            error_msg = f"Failed to start workflow: {e!s}"
            logger.exception(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow": workflow}

        # Extract workflow ID and run ID from the handle
        workflow_id = workflow_handle.id
        run_id = workflow_handle.first_execution_run_id or workflow_handle.result_run_id

        # Generate temporal UI link
        temporal_ui_link = create_temporal_ui_link(workflow_id, run_id)

        # If wait_for_completion is False, return immediately
        if not wait_for_completion:
            # Create response
            response = StartWorkflowResponse(
                workflow_id=workflow_id,
                run_id=run_id,
                status="RUNNING",
                temporal_ui_link=temporal_ui_link,
                started_at=datetime.now(UTC).isoformat(),
            )

            await ctx.info(
                f"Workflow '{workflow}' started successfully. Workflow ID: {workflow_id}, Run ID: {run_id}",
            )

            logger.debug(f"Started workflow response: {response}")
            return response

        # If wait_for_completion is True, wait for the workflow to complete
        await ctx.info(f"Waiting for workflow '{workflow}' to complete...")

        try:
            result = await workflow_handle.result()

            # Get workflow description for completion time
            description = await workflow_handle.describe()
            completed_at = (
                description.close_time.isoformat() if description.close_time else datetime.now(UTC).isoformat()
            )

            response = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "status": "COMPLETED",
                "completed_at": completed_at,
                "temporal_ui_link": temporal_ui_link,
                "result": result,
            }

            await ctx.info(f"Workflow '{workflow}' completed successfully.")
            logger.debug(f"Workflow result: {result}")
            return response

        except Exception as e:
            # Workflow failed
            error_msg = str(e)

            # Get workflow description for completion time
            description = await workflow_handle.describe()
            completed_at = (
                description.close_time.isoformat() if description.close_time else datetime.now(UTC).isoformat()
            )

            response = {
                "workflow_id": workflow_id,
                "run_id": run_id,
                "status": "FAILED",
                "completed_at": completed_at,
                "temporal_ui_link": temporal_ui_link,
                "error": error_msg,
            }

            await ctx.error(f"Workflow '{workflow}' failed: {error_msg}")
            logger.exception(f"Workflow execution failed: {error_msg}")
            return response

    except Exception as e:
        # Catch any unexpected errors
        error_msg = f"Unexpected error starting workflow '{workflow}': {e}"
        logger.exception(error_msg)
        await ctx.error(error_msg)
        return {"error": error_msg, "workflow": workflow}


async def list_available_workflows(workflow_name: str | None = None) -> list[dict[str, Any]] | dict[str, Any]:
    """List all workflows available for execution through MCP, or get detailed schema for a specific workflow.

    Args:
        workflow_name: Optional workflow name. If provided, returns detailed schema for that workflow.
                      If None, returns list of all available workflows.

    Returns:
        If workflow_name is None: List of dictionaries containing workflow information (name, description, module, etc.)
        If workflow_name is provided: Dictionary with detailed schema including parameters, types, descriptions

    """
    try:
        # Discover all MCP-exposed workflows
        workflows = await discover_mcp_workflows()

        # If no workflow_name specified, return list of all workflows
        if workflow_name is None:
            workflow_list = []
            for metadata, external_def in workflows:
                workflow_info = {
                    "name": metadata.name,
                    "description": getattr(metadata, "mcp_description", None)
                    or f"Execute the {metadata.name} workflow",
                    "module": metadata.module,
                    "is_external": external_def is not None,
                }
                workflow_list.append(workflow_info)

            logger.debug(f"Listed {len(workflow_list)} available workflows")
            return workflow_list

        # If workflow_name specified, find and return detailed schema
        for metadata, external_def in workflows:
            if metadata.name == workflow_name:
                # Get full parameter schema with Pydantic field descriptions
                parameter_schema = format_workflow_parameters(metadata)

                # Build detailed workflow schema
                workflow_schema = {
                    "name": metadata.name,
                    "description": getattr(metadata, "mcp_description", None)
                    or f"Execute the {metadata.name} workflow",
                    "module": metadata.module,
                    "is_external": external_def is not None,
                    "parameter_schema": parameter_schema,
                    "example_usage": {
                        "workflow": metadata.name,
                        "workflow_input": {
                            param.name: f"<{param.type_str or 'string'}>" for param in metadata.parameter_info
                        },
                    },
                }

                logger.debug(f"Retrieved schema for workflow '{workflow_name}'")
                return workflow_schema

        # Workflow not found
        logger.warning(f"Workflow '{workflow_name}' not found in available workflows")
        return {
            "error": f"Workflow '{workflow_name}' not found",
            "available_workflows": [m.name for m, _ in workflows],
        }

    except Exception:
        logger.exception("Failed to list available workflows")
        # Return empty list/error on exception
        if workflow_name is None:
            return []
        return {"error": "Failed to retrieve workflow information"}


async def list_workflows(
    status: str | None = None,
    workflow_id: str | None = None,
) -> list[dict[str, Any]]:
    """List workflows with optional filtering, or get details for a specific workflow.

    Args:
        status: Optional status filter. If provided, only workflows with this status are returned.
                Valid values: RUNNING, COMPLETED, FAILED, CANCELLED, TERMINATED, TIMED_OUT, PENDING
                If None, returns all workflows regardless of status.
        workflow_id: Optional workflow ID. If provided, returns only that specific workflow.
                     Takes precedence over status filter.

    Returns a list of workflows with metadata including:
    - workflow_id: Unique workflow identifier
    - run_id: Temporal run identifier
    - status: Current workflow status
    - workflow_type: Type/name of the workflow
    - duration: Human-readable duration string
    - pending_tasks_count: Number of pending tasks
    - temporal_ui_link: Link to Temporal UI for monitoring

    Returns:
        List of dictionaries containing workflow information,
        empty list if no workflows match criteria or on service errors

    """
    try:
        # Create service manager to get temporal client
        service_manager = await ServiceManager.create(terminate_all=False)

        # Check if temporal client is available
        if not service_manager.temporal_client:
            logger.warning("Temporal client not available")
            return []

        # Get raw Temporal client and create workflow management client
        client = await service_manager.temporal_client.get_client()
        mgmt_client = WorkflowManagementClient(client)

        # If workflow_id is provided, return only that workflow
        if workflow_id:
            # Get all workflows and find the one matching the workflow_id
            all_workflows = await mgmt_client.list_workflow_runs()

            for workflow in all_workflows:
                if workflow.workflow_id == workflow_id:
                    workflow_info = {
                        "workflow_id": workflow.workflow_id,
                        "run_id": workflow.id,
                        "status": workflow.status.value,
                        "workflow_type": workflow.type,
                        "duration": workflow.duration,
                        "pending_tasks_count": workflow.pending_tasks_count,
                        "temporal_ui_link": workflow.monitor,
                    }
                    logger.debug(f"Found workflow {workflow_id}")
                    return [workflow_info]

            # Workflow not found
            logger.warning(f"Workflow {workflow_id} not found")
            return []

        # Get all workflow runs
        all_workflows = await mgmt_client.list_workflow_runs()

        # Build list of workflows to return
        workflows = []
        for workflow in all_workflows:
            workflow_info = {
                "workflow_id": workflow.workflow_id,
                "run_id": workflow.id,
                "status": workflow.status.value,
                "workflow_type": workflow.type,
                "duration": workflow.duration,
                "pending_tasks_count": workflow.pending_tasks_count,
                "temporal_ui_link": workflow.monitor,
            }

            # If status filter is provided, only include matching workflows
            if status is None or workflow.status.value.upper() == status.upper():
                workflows.append(workflow_info)

        filter_msg = f" with status '{status}'" if status else ""
        logger.debug(f"Found {len(workflows)} workflows{filter_msg} out of {len(all_workflows)} total")
        return workflows

    except Exception:
        logger.exception("Failed to list workflows")
        # Return empty list on error to gracefully handle service unavailability
        return []


async def get_workflow_status(
    workflow_id: str,
    ctx: Context,
) -> WorkflowStatusResponse | dict[str, Any]:
    """Get the status of a workflow by ID.

    This function queries Temporal directly to get workflow status.

    Args:
        workflow_id: The unique workflow identifier
        ctx: FastMCP context for logging

    Returns:
        WorkflowStatusResponse with complete status information
        Or error dict with error message and workflow_id

    """
    await ctx.info(f"Getting status for workflow '{workflow_id}'...")

    # Use WorkflowManagementClient to query Temporal
    logger.debug(f"Using WorkflowManagementClient to get status for workflow {workflow_id}")

    try:
        # Create service manager to get temporal client
        service_manager = await ServiceManager.create(terminate_all=False)

        # Check if temporal client is available
        if not service_manager.temporal_client:
            error_msg = "Temporal client not available"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow_id": workflow_id}

        # Get raw Temporal client and create management client
        client = await service_manager.temporal_client.get_client()
        mgmt_client = WorkflowManagementClient(client)

        # Try to get the workflow run - this searches all workflows
        workflow_run = await mgmt_client.get_workflow_run(workflow_id)

        if not workflow_run:
            # Workflow not found
            error_msg = f"Workflow '{workflow_id}' not found"
            logger.error(error_msg)
            await ctx.error(error_msg)
            return {"error": error_msg, "workflow_id": workflow_id}

        # Map the WorkflowRunStatus to our response format
        status_map = {
            "Running": "RUNNING",
            "Completed": "COMPLETED",
            "Failed": "FAILED",
            "Canceled": "CANCELLED",
            "Terminated": "CANCELLED",
            "Timed Out": "FAILED",
        }

        status_str = status_map.get(workflow_run.status.value, "RUNNING")

        await ctx.info(f"Workflow '{workflow_id}' status: {status_str}")

        return WorkflowStatusResponse(
            workflow_id=workflow_run.workflow_id,
            run_id=workflow_run.id,
            status=status_str,
            progress=WorkflowProgressInfo(
                duration=workflow_run.duration,
                pending_tasks_count=workflow_run.pending_tasks_count,
            ),
            temporal_ui_link=workflow_run.monitor,
        )

    except Exception as e:
        error_msg = f"Failed to get workflow status: {e!s}"
        logger.exception(error_msg)
        await ctx.error(error_msg)
        return {"error": error_msg, "workflow_id": workflow_id}


def create_mcp_app() -> FastMCP:
    """Create the AWA MCP server with core workflow management tools only.

    This server exposes 5 core tools:
    - health: Check server health
    - start_workflow: Start workflows (with optional wait_for_completion for blocking behavior)
    - get_workflow_result: Get result of completed async workflows
    - list_workflows: List/filter running workflows
    - list_available_workflows: Discover available workflows and get their schemas

    Auto-discovered workflow tools are NO LONGER registered individually.
    Instead, use list_available_workflows to discover workflows, then start_workflow to execute them.
    """
    mcp = FastMCP(name="AWA MCP")

    # Register core workflow management tools ONLY
    mcp.tool("health")(health)
    mcp.tool("start_workflow")(start_workflow)  # Unified workflow execution (blocking/non-blocking)
    mcp.tool("get_workflow_result")(get_workflow_result)  # Get async workflow results
    mcp.tool("list_workflows")(list_workflows)  # List/filter running workflows
    mcp.tool("list_available_workflows")(list_available_workflows)  # Workflow discovery with schema

    # NOTE: Auto-discovered workflow tools are NO LONGER registered
    # Workflows are discovered and executed dynamically via the core tools above

    return mcp


mcp = create_mcp_app()
