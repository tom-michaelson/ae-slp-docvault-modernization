import typer

from awa.core.api.api import Api
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging

app = typer.Typer()


@app.command(name="api")
def api() -> None:
    """Start the AWA API server directly (useful for debugging)."""
    init_logging()
    logger = get_logger(LoggerComponent.CLI)

    logger.info("Starting AWA API server for debugging...")

    try:
        api = Api()
        # Use run_docker() which uses uvicorn.run() directly
        # This runs in the current process and allows breakpoints to work
        api.run_docker()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping API server...")
    except Exception:
        logger.exception("API server error")
        raise
