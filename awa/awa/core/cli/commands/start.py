"""Start command implementation."""

import asyncio
import gc
from typing import Annotated

import typer
import yaml

from awa.core.cli import constants as cli_constants
from awa.core.cli.commands.stop import _stop_all
from awa.core.cli.options import handle_options
from awa.core.cli.service_manager import ServiceManager
from awa.core.cli.service_utils import parse_service_list
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.models.cli.ui_mode import UIMode
from awa.core.utils.cli_utils import is_packaged_mode
from awa.core.utils.config_paths import ConfigPaths
from awa.core.utils.platform_utils import PlatformUtils

app = typer.Typer()

init_logging()
logger = get_logger(LoggerComponent.CLI)


async def validate_global_configuration() -> bool:
    """Check if global configuration exists and is valid."""
    if not is_packaged_mode():
        # In development mode, don't require global configuration
        return True

    config_paths = ConfigPaths()
    global_config_file = config_paths.get_global_config_dir() / "config.yaml"
    global_env_file = config_paths.get_global_config_dir() / ".env"

    # Check if configuration files exist
    if not global_config_file.exists() or not global_env_file.exists():
        return False

    # Basic validation - check if files are readable and contain basic structure
    try:
        with global_config_file.open() as f:
            config_data = yaml.safe_load(f)

            # Check for required structure
        return not (not config_data or "llm" not in config_data)
    except (OSError, yaml.YAMLError, KeyError):
        return False


@app.command(name="start")
def start(
    ui_mode: Annotated[
        UIMode | None,
        typer.Option("--ui-mode", "-u", help="UI mode to use"),
    ] = None,
    terminate_all: Annotated[
        bool | None,
        typer.Option("--terminate", "-t", help="Terminate all workflows currently running"),
    ] = None,
    detach: Annotated[
        bool,
        typer.Option("--detach", "-d", help="Start services and exit CLI (services continue running in background)"),
    ] = False,
    services: Annotated[
        str | None,
        typer.Option(
            "--services",
            "-s",
            help=f"Comma-delimited list of services to start. {cli_constants.SERVICES_HELP_LIST}",
        ),
    ] = None,
    env: Annotated[
        str | None,
        typer.Option("--env", "-e", help="Optional .env path, overwriting any defaults or values from local"),
    ] = None,
    config: Annotated[
        str | None,
        typer.Option("--config", "-c", help="Optional config.yaml path, overwriting any defaults or values from local"),
    ] = None,
) -> None:
    """Start AWA services."""
    handle_options(env, config)
    asyncio.run(_start(ui_mode, terminate_all, detach, services))


def _filter_services_for_package_mode(requested_services: list[str] | None) -> list[str] | None:
    """Filter out UI service if in package mode and warn user.

    Args:
        requested_services: Original list of requested services

    Returns:
        Filtered list with UI removed if in package mode, None if no filtering needed

    """
    if not is_packaged_mode() or requested_services is None:
        return requested_services

    # Check if UI was requested
    if cli_constants.SERVICE_UI in requested_services:
        logger.warning(cli_constants.UI_PACKAGE_MODE_WARNING)
        # Filter out UI service
        filtered_services = [s for s in requested_services if s != cli_constants.SERVICE_UI]
        if filtered_services:
            logger.info(f"Starting remaining services: {', '.join(filtered_services)}")
        return filtered_services if filtered_services else None

    return requested_services


async def _setup_and_validate_inputs(
    ui_mode: UIMode | None,
    terminate_all: bool | None,
    services: str | None,
) -> tuple[UIMode, ServiceManager, list[str] | None]:
    """Set up and validate inputs for service startup.

    Args:
        ui_mode: UI mode to use
        terminate_all: Whether to terminate all workflows
        services: Comma-delimited string of services to start

    Returns:
        Tuple of (validated_ui_mode, service_manager, requested_services)

    """
    logger.info(cli_constants.INTRO)

    # Check global configuration requirements for packaged mode
    if not await validate_global_configuration():
        logger.error(
            "❌ No global configuration found. Please run 'awa init' first to set up required API keys and settings.",
        )
        raise typer.Exit(1)

    logger.info("Checking AWA service statuses...")

    # Check if UI mode was provided
    if ui_mode is None:
        ui_mode = UIMode.DEV

    # Parse and validate services if provided
    requested_services = None
    if services is not None:
        requested_services = parse_service_list(services)
        logger.info(f"Starting specific services: {', '.join(requested_services)}")

        # Filter services for package mode
        requested_services = _filter_services_for_package_mode(requested_services)
        if requested_services is None:
            logger.error("No services to start after filtering.")
            raise typer.Exit(1)
    # Handle case where all services requested but we're in package mode
    elif is_packaged_mode():
        logger.warning(cli_constants.UI_PACKAGE_MODE_WARNING)
        # Start all services except UI
        requested_services = [
            cli_constants.SERVICE_API,
            cli_constants.SERVICE_TEMPORAL_SERVER,
            cli_constants.SERVICE_TEMPORAL_WORKER,
        ]
        logger.info(f"Starting services (UI excluded): {', '.join(requested_services)}")
    else:
        logger.info("Starting all services")

    service_manager = await ServiceManager.create(terminate_all=terminate_all or False)

    return ui_mode, service_manager, requested_services


async def _check_initial_status_and_early_exit(
    service_manager: ServiceManager,
    ui_mode: UIMode,
    requested_services: list[str] | None,
) -> tuple[dict, bool]:
    """Check initial service status and determine if early exit is needed.

    Args:
        service_manager: Service manager instance
        ui_mode: UI mode to use
        requested_services: List of specific services to check

    Returns:
        Tuple of (initial_status, should_exit_early)

    """
    initial_status = await service_manager.check_all_services(ui_mode)

    # Filter to requested services if specified
    status_to_check = (
        {name: initial_status[name] for name in requested_services} if requested_services else initial_status
    )

    # Check if all requested services are already running
    all_running = all(status_to_check.values())
    if all_running:
        logger.info("All requested services are already running.")
        running_services = [name for name, status in status_to_check.items() if status]
        if running_services:
            logger.info(f"Running services: {', '.join(running_services)}")
        return initial_status, True

    # Display current status
    logger.info("Current service status:")
    for service_name, is_running in status_to_check.items():
        status = "[OK] Running" if is_running else "[X] Stopped"
        logger.info(f"  {service_name}: {status}")

    return initial_status, False


async def _start_requested_services(
    service_manager: ServiceManager,
    ui_mode: UIMode,
    terminate_all: bool | None,
    detach: bool,
    requested_services: list[str] | None,
) -> None:
    """Start the requested services.

    Args:
        service_manager: Service manager instance
        ui_mode: UI mode to use
        terminate_all: Whether to terminate all workflows
        detach: Whether to detach services
        requested_services: List of specific services to start

    """
    logger.info("Starting AWA services...")

    try:
        # Use the existing ensure_all_services_running method
        await service_manager.ensure_all_services_running(
            ui_mode=ui_mode,
            terminate_all=terminate_all or False,
            detach=detach,
            services=requested_services,
        )

        # Display service URLs
        service_manager.display_service_urls(requested_services)

    except Exception as e:
        logger.exception("Failed to start services")
        raise typer.Exit(1) from e


async def _handle_post_start_monitoring(
    service_manager: ServiceManager,
    detach: bool,
    requested_services: list[str] | None,
    initial_status: dict,
) -> None:
    """Handle post-start monitoring and cleanup.

    Args:
        service_manager: Service manager instance
        ui_mode: UI mode to use
        detach: Whether services are detached
        requested_services: List of specific services that were started
        initial_status: Initial service status before starting

    """
    if detach:
        if PlatformUtils.is_windows():
            # Clean up subprocess transports and background tasks before exit to prevent errors
            await service_manager.cleanup_subprocess_transports()
            await service_manager.cleanup_background_tasks()
        logger.info("Services started in detached mode. Use 'awa stop' to stop them.")
        return

    logger.info("All services running. Press Ctrl+C to stop.")

    # Run basic monitoring for attached services
    try:
        await asyncio.Event().wait()  # Wait indefinitely until interrupted
    except (asyncio.CancelledError, KeyboardInterrupt):
        logger.info("Received interrupt signal. Stopping services...")

        # CRITICAL: Clean up subprocess transports FIRST, then background tasks to prevent event loop errors
        await service_manager.cleanup_subprocess_transports()
        await service_manager.cleanup_background_tasks()

        # Stop only services that were started by this session
        services_to_stop = []
        for service_name, was_running in initial_status.items():
            if not was_running and (requested_services is None or service_name in requested_services):
                services_to_stop.append(service_name)

        if services_to_stop:
            # Use aggressive stop-all logic for interrupt scenarios to handle orphaned processes
            logger.info("Using comprehensive cleanup due to interrupt signal...")
            await _stop_all()

        # Return cleanly after successful interrupt handling
        return
    except Exception as e:
        logger.exception("Error during service monitoring")

        # Clean up subprocess transports and background tasks to prevent event loop errors
        await service_manager.cleanup_subprocess_transports()
        await service_manager.cleanup_background_tasks()

        # Stop services that were started by this session
        services_to_stop = []
        for service_name, was_running in initial_status.items():
            if not was_running and (requested_services is None or service_name in requested_services):
                services_to_stop.append(service_name)

        if services_to_stop:
            # Use aggressive stop-all logic for interrupt scenarios to handle orphaned processes
            logger.info("Using comprehensive cleanup due to interrupt signal...")
            await _stop_all()

        raise typer.Exit(1) from e


async def _cleanup_subprocess_transports() -> None:
    """Clean up any remaining subprocess transports to prevent Windows event loop warnings."""
    try:
        # Give the event loop time to finish any pending subprocess operations
        await asyncio.sleep(0.1)

        # Force garbage collection to clean up any unreferenced transports
        gc.collect()

        # Give a final moment for cleanup
        await asyncio.sleep(0.1)

    except (OSError, RuntimeError) as e:
        # Log cleanup issues for debugging if needed
        logger.debug(f"Subprocess transport cleanup encountered minor issues: {e}")


async def _start(
    ui_mode: UIMode | None = UIMode.DEV,
    terminate_all: bool | None = None,
    detach: bool = False,
    services: str | None = None,
) -> None:
    """Start AWA services with the specified configuration."""
    # Step 1: Setup and validate inputs
    ui_mode, service_manager, requested_services = await _setup_and_validate_inputs(
        ui_mode,
        terminate_all,
        services,
    )

    # Step 2: Check initial status and handle early exit
    initial_status, should_exit_early = await _check_initial_status_and_early_exit(
        service_manager,
        ui_mode,
        requested_services,
    )

    if should_exit_early:
        return

    # Step 3: Start requested services using unified logic
    await _start_requested_services(
        service_manager,
        ui_mode,
        terminate_all,
        detach,
        requested_services,
    )

    # Step 4: Handle post-start monitoring and cleanup
    await _handle_post_start_monitoring(
        service_manager,
        detach,
        requested_services,
        initial_status,
    )

    # Clean up any remaining subprocess transports on Windows to prevent warnings
    if detach and PlatformUtils.is_windows():
        await _cleanup_subprocess_transports()
