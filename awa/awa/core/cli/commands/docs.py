import asyncio

import typer

from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.utils.command_utils import CommandUtils

app = typer.Typer()


@app.command(name="docs")
def docs() -> None:
    """Run the AWA docs."""
    init_logging()
    asyncio.run(docs_async())


async def docs_async() -> None:
    logger = get_logger(LoggerComponent.CLI)
    logger.info(
        "Running docs in 'dev' mode. Docs will be visible at http://localhost:5173/docs/.",
    )
    await CommandUtils.run_command_async(command="pnpm run docs:dev")
