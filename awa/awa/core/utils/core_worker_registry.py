"""Core worker registry utility for creating local workflow registry file."""

from datetime import UTC, datetime

from awa.core.api.registry.storage import FileSystemRegistryStorage
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.api import WorkerRegistration, WorkflowDefinition


async def register_core_workflows(workflows: list, task_queue: str) -> None:
    """Register core workflows in the local registry.

    Creates a core-worker.json file similar to external workers,
    so that get_workflow_queue() can find all workflows in registry files.

    Args:
        workflows: List of discovered workflow classes
        task_queue: The task queue for core workflows (usually "awa_default")

    """
    logger = get_logger(LoggerComponent.WORKER)

    workflow_definitions = []
    for workflow_class in workflows:
        # Extract workflow name from Temporal decorator
        workflow_name = None
        try:
            definition = getattr(workflow_class, "__temporal_workflow_definition", None)
            if definition and hasattr(definition, "name") and definition.name:
                workflow_name = definition.name
                logger.debug(f"Found workflow with Temporal name: {workflow_name} (class: {workflow_class.__name__})")
        except AttributeError:
            logger.debug(
                f"No Temporal definition for workflow class: {
                    getattr(workflow_class, '__name__', str(workflow_class))
                }",
            )

        # Fallback to class name if no Temporal name found
        if not workflow_name and hasattr(workflow_class, "__name__"):
            workflow_name = workflow_class.__name__
            logger.debug(f"Using class name as workflow name: {workflow_name}")

        if workflow_name:
            # Create workflow definition
            workflow_def = WorkflowDefinition(
                name=workflow_name,
                task_queue=task_queue,
                input_schema={
                    "type": "object",
                    "properties": {},  # Simplified for now
                },
                exposed=False,  # Core workflows handle exposure separately
                description=None,
            )
            workflow_definitions.append(workflow_def)
            logger.debug(f"Added workflow '{workflow_name}' to registry")
        else:
            logger.warning(f"Could not extract name from workflow class: {workflow_class}")

    # Create worker registration
    registration = WorkerRegistration(
        worker_name="core-worker",
        worker_version="1.0.0",
        task_queue=task_queue,
        workflows=workflow_definitions,
        activities=[],  # Simplified - activities aren't needed for queue lookup
        generated_at=datetime.now(UTC),
    )

    # Store in registry
    storage = FileSystemRegistryStorage()
    await storage.store_worker_registration(registration)

    logger.info(f"Core worker registry created with {len(workflow_definitions)} workflows")
