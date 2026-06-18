"""Workflow-related API endpoints."""

from typing import Annotated

from fastapi import Depends, HTTPException, Query, status

from awa.core.api.auth import require_authenticated_user
from awa.core.api.dependencies import get_temporal_client
from awa.core.api.registry.storage import get_registry_storage
from awa.core.constants import TASK_QUEUE
from awa.core.engine.temporal_client import TemporalClient
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import (
    PostResponse,
    WorkflowInfo,
    WorkflowListResponse,
    WorkflowRun,
    WorkflowRunListResponse,
    WorkflowRunPayload,
)
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.workflow_metadata import format_workflow_parameters, get_workflow_metadata
from awa.sdk.models.exceptions.invalid_input_error import InvalidInputApplicationError


async def workflow_runs(
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> WorkflowRunListResponse:
    """Workflow runs endpoint that returns a list of running and completed workflows.

    Args:
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        WorkflowRunsResponse containing the list of workflow runs

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Listing workflow runs for user {user_info}")

    runs = await client.list_workflow_runs()
    return WorkflowRunListResponse(
        workflows=runs,
    )


async def list_workflows(
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    task_queue: str | None = Query(None, description="Filter by task queue"),
) -> WorkflowListResponse:
    """List all available workflows from both core discovery and registry.

    Combines workflows from:
    - Core application (via TemporalDiscovery)
    - External workers (via registry)

    Args:
        current_user: Authenticated user
        task_queue: Optional filter by task queue

    Returns:
        WorkflowListResponse containing unified list of workflow information.

    Raises:
        HTTPException: 500 if workflow discovery fails.

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Listing workflows for user {user_info}")

    # Get config to check recipes flag
    config = ConfigLoader.get_config()
    include_recipes = config.recipes

    try:
        workflow_info_list = []
        skipped_recipe_count = 0
        skipped_non_exposed_count = 0

        # 1. Get core workflows from temporal discovery
        try:
            workflow_metadata = get_workflow_metadata(include_recipes)

            for metadata in workflow_metadata:
                try:
                    # Apply task queue filter if specified
                    if task_queue and task_queue != TASK_QUEUE:
                        continue

                    # Filter recipe workflows based on config flag
                    is_recipe_workflow = "cookbook.recipes" in metadata.module
                    if is_recipe_workflow and not include_recipes:
                        logger.debug(f"Skipping recipe workflow (recipes disabled): {metadata.name}")
                        skipped_recipe_count += 1
                        continue

                    # Filter core workflows that are not exposed
                    if not metadata.exposed:
                        logger.debug(f"Skipping non-exposed core workflow: {metadata.name}")
                        skipped_non_exposed_count += 1
                        continue

                    workflow_info = WorkflowInfo(
                        name=metadata.name,
                        module=metadata.module,
                        parameters=format_workflow_parameters(metadata),
                        queues=[TASK_QUEUE],  # Core workflows use default queue
                        description=metadata.description,
                    )
                    workflow_info_list.append(workflow_info)

                except Exception as e:  # noqa: BLE001
                    logger.warning(f"Failed to process workflow {metadata.name}: {e}")
                    # Continue processing other workflows

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to discover core workflows: {e}")
            # Continue with registry workflows even if core discovery fails

        # 2. Get registered workflows from registry
        try:
            storage = get_registry_storage()
            active_workers = await storage.list_active_workers()

            # Track workflow names already added to avoid duplicates
            existing_workflow_names = {wf.name for wf in workflow_info_list}

            # Process each worker's workflows (no worker_name filtering)
            for worker in active_workers:
                # Skip core-worker as those workflows are already included from temporal discovery
                if worker.worker_name == "core-worker":
                    continue
                for workflow_def in worker.workflows:
                    # Skip if workflow with this name already exists
                    if workflow_def.name in existing_workflow_names:
                        logger.debug(f"Skipping duplicate workflow: {workflow_def.name}")
                        continue

                    # Apply task queue filter if specified
                    if task_queue and task_queue != workflow_def.task_queue:
                        continue

                    # Convert input schema to parameter list
                    parameters = []
                    if (workflow_def.input_schema is not None) & (len(workflow_def.input_schema) > 0):
                        parameters = workflow_def.input_schema
                    else:
                        parameters = {}

                    workflow_info = WorkflowInfo(
                        name=workflow_def.name,
                        module="external",  # All registry workflows marked as external
                        parameters=parameters,
                        queues=[workflow_def.task_queue],
                        description=workflow_def.description,
                    )
                    workflow_info_list.append(workflow_info)
                    existing_workflow_names.add(workflow_def.name)

        except Exception as e:  # noqa: BLE001
            logger.warning(f"Failed to get registry workflows: {e}")
            # Continue with core workflows even if registry fails

        # Sort by module then name for consistent ordering
        workflow_info_list.sort(key=lambda x: (x.module, x.name))

        recipe_status = "enabled" if include_recipes else "disabled"
        logger.info(
            f"Listed {len(workflow_info_list)} workflows "
            f"(recipes {recipe_status}, {skipped_recipe_count} recipe workflows skipped, "
            f"{skipped_non_exposed_count} non-exposed workflows skipped)",
        )
        return WorkflowListResponse(workflows=workflow_info_list)

    except Exception as e:
        logger.exception("Failed to list workflows")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list workflows: {e!s}",
        ) from e


async def run_workflow(
    run_payload: WorkflowRunPayload,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> PostResponse:
    """Run Workflow endpoint to iniate new workflow run.

    Args:
        run_payload: Workflow run configuration
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        PostResponse with success message

    Raises:
        HTTPException: 400 if input JSON is invalid, 500 if workflow execution fails

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.info(f"Starting workflow '{run_payload.name}' for user {user_info}")

    try:
        await client.start_workflow(
            workflow=run_payload.name,
            workflow_input=run_payload.input,
            task_queue=run_payload.task_queue,
        )
        return {
            "data": "success",
        }
    except InvalidInputApplicationError as e:
        logger.warning(f"Invalid JSON input for workflow '{run_payload.name}': {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON format in input field") from e
    except Exception as e:
        # Handle other errors as 500s
        logger.exception(f"Workflow execution failed for '{run_payload.name}'")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {e!s}",
        ) from e


async def get_workflow_run(
    run_id: str,
    current_user: Annotated[dict, Depends(require_authenticated_user)],
    client: Annotated[TemporalClient, Depends(get_temporal_client)],
) -> WorkflowRun:
    """Get details about a specific workflow run by run ID.

    Args:
        run_id: The workflow run ID
        current_user: Authenticated user
        client: Temporal client instance for workflow operations

    Returns:
        WorkflowRun containing the workflow run details

    Raises:
        HTTPException: If workflow run is not found or retrieval fails

    """
    logger = get_logger(LoggerComponent.API)
    user_info = current_user.get("sub", "unknown") if current_user else "anonymous"
    logger.debug(f"Getting workflow run {run_id} for user {user_info}")

    try:
        workflow_run = await client.get_workflow_run(run_id)

        if workflow_run is None:
            logger.warning(f"Workflow run {run_id} not found")
            raise HTTPException(  # noqa: TRY301
                status_code=404,
                detail=f"Workflow run {run_id} not found",
            )

        logger.info(f"Retrieved workflow run {run_id}")
        return workflow_run

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get workflow run {run_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow run: {e!s}",
        ) from e
