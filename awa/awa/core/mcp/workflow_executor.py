"""Workflow execution helpers for MCP server."""

import json
from datetime import UTC, datetime
from typing import Any

from fastmcp import Context
from fastmcp.exceptions import ToolError
from temporalio.api.enums.v1 import WorkflowExecutionStatus
from temporalio.client import Client, WorkflowHandle

from awa.core.cli.service_manager import ServiceManager
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.mcp import StartWorkflowResponse, WorkflowResultResponse

from .exceptions import (
    WorkflowExecutionError,
    WorkflowNotCompletedError,
    WorkflowNotFoundError,
    raise_temporal_client_not_initialized,
    raise_workflow_name_required,
    raise_workflow_not_completed,
)
from .workflow_status_mapper import create_temporal_ui_link

logger = get_logger(LoggerComponent.SERVER)


async def prepare_workflow_input(
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


async def initialize_service_manager() -> ServiceManager:
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


async def start_temporal_workflow(
    temporal_client: Client,
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


async def execute_workflow(
    workflow: str,
    ctx: Context,
    workflow_input: str | dict | list | None = None,
    task_queue: str | None = None,
    wait_for_completion: bool = False,
) -> StartWorkflowResponse | dict[str, Any]:
    """Execute a workflow with optional blocking behavior.

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

    Raises:
        WorkflowNotFoundError: If the workflow is not registered
        WorkflowExecutionError: If workflow start fails
        ToolError: For other validation or execution errors

    """
    try:
        mode = "blocking" if wait_for_completion else "non-blocking"
        await ctx.info(f"Starting workflow '{workflow}' on task queue '{task_queue or 'default'}' ({mode})...")

        # Validate workflow name
        if not workflow:
            raise_workflow_name_required()

        # Prepare workflow input
        input_for_workflow = await prepare_workflow_input(workflow_input)

        # Initialize service manager
        service_manager = await initialize_service_manager()

        # Get the temporal client directly
        if service_manager.temporal_client is None:
            raise_temporal_client_not_initialized()

        temporal_client = service_manager.temporal_client

        # Start the workflow using the TemporalClient's start_workflow method
        workflow_handle = await start_temporal_workflow(
            temporal_client,
            workflow,
            input_for_workflow,
            task_queue,
        )

        # Extract workflow ID and run ID from the handle
        workflow_id = workflow_handle.id
        run_id = workflow_handle.first_execution_run_id or workflow_handle.result_run_id

        # Generate temporal UI link
        temporal_ui_link = create_temporal_ui_link(workflow_id, run_id)

        # If wait_for_completion is False, return immediately
        if not wait_for_completion:
            started_at = datetime.now(UTC).isoformat()

            # Create response
            response = StartWorkflowResponse(
                workflow_id=workflow_id,
                run_id=run_id,
                status="RUNNING",
                temporal_ui_link=temporal_ui_link,
                started_at=started_at,
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

    except (WorkflowNotFoundError, WorkflowExecutionError, ToolError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_msg = f"Unexpected error starting workflow '{workflow}': {e}"
        logger.exception(error_msg)
        await ctx.error(error_msg)
        raise WorkflowExecutionError(error_msg) from e


async def retrieve_workflow_result(workflow_id: str, ctx: Context | None = None) -> WorkflowResultResponse:  # noqa: PLR0915, ARG001
    """Get the result of a completed workflow.

    This function retrieves the result of a workflow that has completed execution.
    It queries Temporal directly for the workflow status and result.

    Args:
        workflow_id: Unique identifier for the workflow
        ctx: Optional FastMCP context for logging

    Returns:
        WorkflowResultResponse containing workflow result or error

    Raises:
        WorkflowNotFoundError: If workflow ID is not found in Temporal
        WorkflowNotCompletedError: If workflow is still running or in an incomplete state

    """
    # Initialize service manager to get Temporal client
    service_manager = await initialize_service_manager()

    if service_manager.temporal_client is None:
        raise_temporal_client_not_initialized()

    temporal_client = service_manager.temporal_client

    try:
        # Get workflow handle directly from Temporal
        handle = temporal_client.get_workflow_handle(workflow_id)
    except Exception as e:
        logger.exception(f"Failed to get workflow handle for {workflow_id}")
        raise WorkflowNotFoundError(f"Workflow '{workflow_id}' not found in Temporal: {e}") from e

    try:
        # Get the workflow description to check status
        description = await handle.describe()

        # Map Temporal status to our status strings
        status_mapping = {
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_COMPLETED: "COMPLETED",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_FAILED: "FAILED",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CANCELED: "CANCELLED",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TERMINATED: "TERMINATED",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_CONTINUED_AS_NEW: "CONTINUED_AS_NEW",
            WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_TIMED_OUT: "TIMED_OUT",
        }

        # Check if workflow is still running
        if description.status == WorkflowExecutionStatus.WORKFLOW_EXECUTION_STATUS_RUNNING:
            logger.info(f"Workflow {workflow_id} is still running")
            raise_workflow_not_completed(workflow_id)

        # Get the status string
        status_str = status_mapping.get(description.status, "UNKNOWN")

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

    except (WorkflowNotFoundError, WorkflowNotCompletedError):
        # Re-raise our custom errors
        raise
    except Exception as e:
        # Handle any unexpected errors
        logger.exception(f"Unexpected error retrieving result for workflow {workflow_id}")
        raise ToolError(f"Failed to retrieve workflow result: {e!s}") from e
