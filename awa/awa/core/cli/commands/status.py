import asyncio
from typing import Annotated

import typer
from loguru import logger

from awa.core.cli import constants as cli_constants
from awa.core.cli.service_manager import ServiceManager
from awa.core.cli.service_utils import parse_service_list
from awa.core.logger.logger import init_logging
from awa.core.models.cli.ui_mode import UIMode

app = typer.Typer()
logger = logger.bind(name="AWA Status")


@app.command(name="status")
def status(
    services: Annotated[
        str | None,
        typer.Option(
            "--services",
            "-s",
            help=f"Comma-delimited list of services to check. {cli_constants.SERVICES_HELP_LIST}",
        ),
    ] = None,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Quiet mode - no output, only exit codes (for CI/automation)",
        ),
    ] = False,
) -> None:
    """Check the status of AWA services."""
    init_logging()
    asyncio.run(_status(services, quiet))


async def _status(services: str | None = None, quiet: bool = False) -> None:
    """Check the status of AWA services."""
    # Parse and validate services if provided
    requested_services = None
    if services is not None:
        requested_services = parse_service_list(services)

    # Get service manager
    service_manager = await ServiceManager.create()

    # Check service statuses using existing methods
    all_status = await service_manager.check_all_services(ui_mode=UIMode.DEV)

    # Filter to requested services if specified
    status_to_check = {name: all_status[name] for name in requested_services} if requested_services else all_status

    # Display status for each service
    all_running = True
    for service_name, is_running in status_to_check.items():
        if not quiet:
            # Normal mode: show all services
            status_symbol = "[OK]" if is_running else "[X]"
            status_text = "RUNNING" if is_running else "STOPPED"
            logger.info(f"{status_symbol} {service_name}: {status_text}")
        # Quiet mode: no output, only exit codes matter for CI

        if not is_running:
            all_running = False

    # Exit with appropriate code based on service status
    if not all_running:
        raise typer.Exit(1)
