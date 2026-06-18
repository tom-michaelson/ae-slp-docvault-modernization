import asyncio
from typing import Annotated

import typer

from awa.core import constants
from awa.core.engine.temporal_server import TemporalServer
from awa.core.logger.logger import init_logging

app = typer.Typer()


@app.command(name="server")
def server(
    retries: Annotated[
        int | None,
        typer.Option("--retries", "-r", help="Number of times to retry connections"),
    ] = constants.SERVER_START_MAX_RETRIES,
) -> None:
    """Start the Temporal Server."""
    init_logging()
    asyncio.run(_server(retries))


async def _server(retries: int = constants.SERVER_START_MAX_RETRIES) -> None:
    """Start server using unified retry logic."""
    server = TemporalServer()
    # Use the same logic as worker
    await server.run_with_retries(max_retries=retries)
