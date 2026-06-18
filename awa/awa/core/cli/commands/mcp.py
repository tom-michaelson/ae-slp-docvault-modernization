from typing import Annotated

import typer

from awa.core.cli import constants as cli_constants
from awa.core.cli.options import handle_options
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging

app = typer.Typer()


@app.command(name="mcp")
def mcp(
    env: Annotated[
        str | None,
        typer.Option("--env", "-e", help="Optional .env path, overwriting any defaults or values from local"),
    ] = None,
    config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Optional config.yaml path, overwriting any defaults or values from local"),
    ] = None,
) -> None:
    """Run the AWA MCP server."""
    init_logging(file_only=False)  # Show logs in console for debugging
    handle_options(env, config)

    logger = get_logger(LoggerComponent.CLI)
    logger.info(cli_constants.INTRO)
    logger.info("Running AWA MCP server...")

    # Import mcp_server only when needed
    from awa.core.mcp import mcp_server

    # Start the MCP server (this will handle its own event loop)
    # Note: Workflows are now executed via start_workflow tool, not auto-registered
    mcp_server.mcp.run()
