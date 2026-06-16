import asyncio
from typing import Annotated, Any

import typer

from awa.core.cli import constants as cli_constants
from awa.core.cli.service_manager import ServiceManager
from awa.core.engine.temporal_client import WorkflowExecutionError
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging

app = typer.Typer()


@app.command(name="run")
def run(
    workflow: Annotated[str | None, typer.Option("--workflow", "-w", help="Workflow to run")] = None,
    workflow_input: Annotated[
        str | None,
        typer.Option("--input", "-i", help="Input for workflow (can be JSON string)"),
    ] = None,
    task_queue: Annotated[
        str | None,
        typer.Option("--task-queue", "-q", help="Task queue to use"),
    ] = None,
) -> None:
    """Run the AWA Engine, API, and UI (including docs)."""
    init_logging()
    asyncio.run(_run(workflow, workflow_input, task_queue))


async def _run(
    workflow: str | None = None,
    workflow_input: str | None = None,
    task_queue: str | None = None,
) -> Any:  # noqa: ANN401
    # Get CLI logger with component context
    logger = get_logger(LoggerComponent.CLI)

    logger.info(cli_constants.INTRO)
    service_manager = await ServiceManager.create()

    workflow_output: Any | None = None
    if workflow:
        logger.info("Executing workflow...")
        logger.info(f"Workflow: {workflow}, Input: {workflow_input}, Task Queue: {task_queue}")

        try:
            workflow_output = await service_manager.execute_workflow(workflow, workflow_input, task_queue)
            logger.info(f"Workflow output: {workflow_output}")
            logger.info("Workflow execution complete.")
        except WorkflowExecutionError:
            logger.exception("Workflow execution failed")
            # Exit gracefully without crashing services
            return None
    else:
        logger.error("No workflow specified. Use the `-w` flag to specify a workflow to run.")
    logger.info("Exited.")
    return workflow_output
