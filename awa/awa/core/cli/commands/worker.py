import asyncio
from typing import Annotated

import typer

from awa.core import constants
from awa.core.constants import CORE_WORKER_NAME
from awa.core.engine.temporal_client import TemporalClient
from awa.core.engine.temporal_worker import TemporalWorker
from awa.core.logger.logger import LoggerComponent, init_logging
from awa.core.logger.socketio_handler import setup_socketio_logging

app = typer.Typer()


@app.command(name="worker")
def worker(
    retries: Annotated[
        int | None,
        typer.Option("--retries", "-r", help="Number of times to retry connections"),
    ] = constants.WORKER_START_MAX_RETRIES,
) -> None:
    """Start the Temporal Worker."""
    init_logging()
    asyncio.run(_worker(retries))


async def _worker(retries: int = constants.WORKER_START_MAX_RETRIES) -> None:
    """Start worker using unified retry logic."""
    # Give the API a moment to start up before connecting Socket.IO
    await asyncio.sleep(2)

    # Set up Socket.IO log forwarding for the core worker
    # Only forward workflow/activity logs to support streaming to the invoking terminal
    def workflow_activity_filter(record: dict) -> bool:
        """Only forward workflow and activity logs via Socket.IO."""
        # When serialize=True, the record structure is different
        if "record" in record:
            # Serialized format
            actual_record = record["record"]
            component = actual_record.get("extra", {}).get("component", "")
        else:
            # Direct format
            component = record.get("extra", {}).get("component", "")

        # Only forward workflow and activity logs
        # Do NOT forward AWA-WORKER logs - they belong in the main terminal only
        return component in {LoggerComponent.WORKFLOW, LoggerComponent.ACTIVITY}

    setup_socketio_logging(
        source_name=CORE_WORKER_NAME,
        filter_func=workflow_activity_filter,
    )

    client = await TemporalClient.create()
    worker = TemporalWorker(client)
    # Use the same logic as ServiceManager
    await worker.run_with_retries(max_retries=retries)
