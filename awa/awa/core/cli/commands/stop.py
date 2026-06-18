import asyncio
import contextlib
import gc
import os
import platform
import re
import signal
import subprocess
import time
from typing import Annotated, NamedTuple

import typer
from loguru import logger as loguru_logger

from awa.core.cli import constants
from awa.core.cli.service_manager import ServiceManager
from awa.core.cli.service_utils import parse_service_list
from awa.core.cli.state_manager import StateManager
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.models.cli.ui_mode import UIMode
from awa.core.utils.platform_utils import PlatformUtils

app = typer.Typer()

# Constants to avoid magic numbers
WINDOWS_WMIC_MIN_PARTS = 4
UNIX_PS_MIN_PARTS = 3
WINDOWS_PS_MIN_PARTS = 3  # ProcessId, ParentProcessId, CommandLine


class ServiceStopResult(NamedTuple):
    """Result of stopping a single service."""

    service_name: str
    success: bool
    verified: bool
    error_message: str | None = None
    retry_count: int = 0


@app.command(name="stop")
def stop(
    services: Annotated[
        str | None,
        typer.Option(
            "--services",
            "-s",
            help=f"Comma-delimited list of services to stop. {constants.SERVICES_HELP_LIST}",
        ),
    ] = None,
) -> None:
    """Stop AWA services."""
    init_logging()

    # Setup signal handlers for graceful shutdown
    # Use a flag to track if we're in the middle of terminating processes
    signal_received = {"value": False}

    def signal_handler(signum: int, _frame: object) -> None:
        logger = get_logger(LoggerComponent.CLI)
        if signal_received["value"]:
            # Already handling a signal, ignore subsequent ones to prevent interrupt loops
            logger.debug(f"Ignoring additional signal {signum} during shutdown")
            return

        signal_received["value"] = True
        logger.info(f"Received signal {signum}, performing graceful shutdown...")

        # On Windows, be more careful about signal handling during subprocess operations
        if PlatformUtils.is_windows():
            logger.debug("Windows signal handling: allowing current operation to complete")
            # Give current operations a moment to complete before triggering shutdown
            time.sleep(0.1)

        # Let the asyncio event loop handle the shutdown gracefully
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(_stop(services))
    except KeyboardInterrupt:
        logger = get_logger(LoggerComponent.CLI)
        # Emergency cleanup if needed
        try:
            asyncio.run(_emergency_cleanup())
        except (OSError, RuntimeError, ValueError) as e:
            logger.warning(f"Emergency cleanup failed: {e}")
        raise typer.Exit(1) from None


async def _stop(services: str | None = None) -> None:
    """Stop services tracked in state files with enhanced verification and error handling."""
    logger = get_logger(LoggerComponent.CLI)
    logger.info("Stopping AWA services...")

    try:
        # Parse and validate services if provided
        requested_services = None
        if services is not None:
            requested_services = parse_service_list(services)
            logger.info(f"Stopping specific services: {', '.join(requested_services)}")
        else:
            logger.debug("Stopping all services")

        state_manager = StateManager()

        # Check if there are any services to stop
        state = await state_manager.load_state()

        if not state or not state.services:
            return

        # Filter services to only requested ones if specified
        if requested_services:
            services_to_stop = [name for name in requested_services if name in state.services]
            services_not_found = [name for name in requested_services if name not in state.services]

            if services_not_found:
                logger.info(f"Services not found in state: {', '.join(services_not_found)}")

            if not services_to_stop:
                logger.info("No requested services are currently running.")
                return
        else:
            services_to_stop = list(state.services.keys())

        logger.info(f"Found {len(services_to_stop)} service(s) to stop: {', '.join(services_to_stop)}")

        # Enhanced stop operation with verification and retry logic
        stop_results = await _execute_enhanced_stop_operation(state_manager, services_to_stop, logger)

        # Report final results
        _report_stop_operation_results(stop_results, logger)

        # Clean up any remaining subprocess transports on Windows to prevent warnings
        if PlatformUtils.is_windows():
            await _cleanup_subprocess_transports(logger)

    except (KeyboardInterrupt, asyncio.CancelledError):
        await _emergency_cleanup()
        raise
    except Exception:
        logger.exception("Unexpected error during stop operation")
        await _emergency_cleanup()
        raise


async def _emergency_cleanup() -> None:
    """Perform emergency cleanup when stop operation is interrupted."""
    logger = get_logger(LoggerComponent.CLI)

    try:
        # Try to clean up state files
        state_manager = StateManager()
        await state_manager.cleanup_state()
        logger.debug("Emergency state cleanup completed")
    except (OSError, RuntimeError, ValueError) as e:
        logger.warning(f"Emergency cleanup failed: {e}")

    # Give any remaining async operations a moment to complete
    with contextlib.suppress(Exception):
        await asyncio.sleep(0.1)


async def _execute_enhanced_stop_operation(
    state_manager: StateManager,
    services_to_stop: list[str],
    logger: loguru_logger,
) -> list[ServiceStopResult]:
    """Execute enhanced stop operation with verification and retry logic.

    Args:
        state_manager: StateManager instance for service operations
        services_to_stop: List of service names to stop
        logger: Logger instance for reporting

    Returns:
        List of ServiceStopResult objects with detailed stop results

    """
    results = []

    # Apply overall timeout to the entire stop operation
    try:
        async with asyncio.timeout(constants.DEFAULT_STOP_TIMEOUT):
            for service_name in services_to_stop:
                logger.debug(f"Starting enhanced stop operation for {service_name}")
                result = await _stop_service_with_verification(state_manager, service_name, logger)
                results.append(result)

                # Log immediate result
                if result.success and result.verified:
                    logger.debug(f"[OK] Successfully stopped and verified {service_name}")
                elif result.success:
                    logger.warning(f"[WARNING] Stopped {service_name} but verification incomplete")
                else:
                    logger.error(f"[FAIL] Failed to stop {service_name}: {result.error_message}")

    except TimeoutError:
        logger.exception(f"Stop operation timed out after {constants.DEFAULT_STOP_TIMEOUT} seconds")
        # Mark any remaining services as failed
        processed_services = {result.service_name for result in results}
        results.extend(
            [
                ServiceStopResult(
                    service_name=service_name,
                    success=False,
                    verified=False,
                    error_message="Operation timed out",
                )
                for service_name in services_to_stop
                if service_name not in processed_services
            ],
        )

    return results


async def _stop_service_with_verification(
    state_manager: StateManager,
    service_name: str,
    logger: loguru_logger,
) -> ServiceStopResult:
    """Stop a single service with comprehensive verification and retry logic.

    Args:
        state_manager: StateManager instance
        service_name: Name of the service to stop
        logger: Logger instance

    Returns:
        ServiceStopResult with detailed stop outcome

    """
    retry_count = 0
    last_error = None

    for attempt in range(constants.DEFAULT_RETRY_ATTEMPTS):
        try:
            logger.debug(f"Stop attempt {attempt + 1}/{constants.DEFAULT_RETRY_ATTEMPTS} for {service_name}")

            # Get service info before stopping to track what we're terminating
            service_info = await state_manager.get_service_info(service_name)
            if not service_info:
                logger.debug(f"Service {service_name} not found in state - considering it stopped")
                return ServiceStopResult(
                    service_name=service_name,
                    success=True,
                    verified=True,
                    retry_count=retry_count,
                )

            # Check if service is unhealthy (PID exists but health check fails)
            # This allows us to be more aggressive with services that are already problematic
            service_is_unhealthy = False
            try:
                # Quick health check to identify unhealthy services
                service_manager = await ServiceManager.create()
                service_status = await service_manager.check_all_services(ui_mode=UIMode.DEV, startup_mode=True)
                service_is_healthy = service_status.get(service_name, False)

                # If PID exists but service is not healthy, mark as unhealthy
                if not service_is_healthy and state_manager.is_process_running(service_info.pid):
                    service_is_unhealthy = True
                    logger.debug(f"Service {service_name} identified as unhealthy (PID exists but health check failed)")
            except (ConnectionError, TimeoutError, ValueError) as e:
                logger.debug(f"Health check failed for {service_name}, treating as unhealthy: {e}")
                service_is_unhealthy = True

            # Service termination will be logged at debug level only
            status_suffix = "[UNHEALTHY]" if service_is_unhealthy else ""
            logger.debug(
                f"Terminating {service_name} (PID {service_info.pid}){status_suffix}...",
            )

            # Use aggressive termination for unhealthy services to avoid timeouts
            if service_is_unhealthy:
                logger.debug(f"Using aggressive termination for unhealthy service {service_name}")
                stop_success = await state_manager.stop_service_with_verification_aggressive(service_name)
            else:
                # Normal termination for healthy services
                logger.debug(f"Using normal termination for healthy service {service_name}")
                stop_success = await state_manager.stop_service_with_verification(service_name)

            if stop_success:
                # Verify termination was successful
                verification_result = await _verify_service_termination(
                    state_manager,
                    service_name,
                    service_info.pid,
                    logger,
                )

                if verification_result:
                    logger.debug(f"Service {service_name} successfully stopped and verified")
                    return ServiceStopResult(
                        service_name=service_name,
                        success=True,
                        verified=True,
                        retry_count=retry_count,
                    )
                logger.debug(f"Service {service_name} stop succeeded but verification failed")
                last_error = "Process verification failed after stop"
            else:
                last_error = "Stop service operation returned failure"

        except (OSError, TimeoutError, ValueError) as e:
            last_error = str(e)
            logger.warning(f"Stop attempt {attempt + 1} failed for {service_name}: {last_error}")

        retry_count += 1

        # If not the last attempt, wait before retrying with exponential backoff
        if attempt < constants.DEFAULT_RETRY_ATTEMPTS - 1:
            backoff_delay = constants.RETRY_BACKOFF_BASE**attempt
            logger.debug(f"Waiting {backoff_delay:.1f}s before retry for {service_name}")
            await asyncio.sleep(backoff_delay)

    # All retry attempts failed
    logger.error(f"All {constants.DEFAULT_RETRY_ATTEMPTS} stop attempts failed for {service_name}")
    return ServiceStopResult(
        service_name=service_name,
        success=False,
        verified=False,
        error_message=last_error,
        retry_count=retry_count,
    )


async def _verify_service_termination(
    state_manager: StateManager,
    service_name: str,
    original_pid: int,
    logger: loguru_logger,
    verification_timeout: float = constants.STOP_VERIFICATION_TIMEOUT,
) -> bool:
    """Verify that a service has been completely terminated.

    Args:
        state_manager: StateManager instance
        service_name: Name of the service
        original_pid: Original PID of the service
        logger: Logger instance
        verification_timeout: Maximum time to spend on verification

    Returns:
        True if service termination is verified, False otherwise

    """
    logger.debug(f"Starting termination verification for {service_name} (PID: {original_pid})")

    try:
        async with asyncio.timeout(verification_timeout):
            # Check 1: Verify the original process is no longer running
            if state_manager.is_process_running(original_pid):
                logger.debug(f"Original process {original_pid} for {service_name} is still running")
                return False

            # Check 2: Verify service is no longer in state
            service_info = await state_manager.get_service_info(service_name)
            if service_info:
                logger.warning(f"Service {service_name} still exists in state after stop")
                return False

            # Check 3: For services with ports, verify port is no longer in use
            port_check_result = await _verify_service_port_released(state_manager, service_name, logger)
            if not port_check_result:
                logger.warning(f"Port verification failed for {service_name}")
                return False

            logger.debug(f"Termination verification successful for {service_name}")
            return True

    except TimeoutError:
        logger.warning(f"Termination verification timed out for {service_name}")
        return False
    except (OSError, ValueError, RuntimeError) as e:
        logger.warning(f"Termination verification error for {service_name}: {e}")
        return False


async def _verify_service_port_released(
    state_manager: StateManager,
    service_name: str,
    logger: loguru_logger,
) -> bool:
    """Verify that a service's port has been released.

    Args:
        state_manager: StateManager instance
        service_name: Name of the service
        logger: Logger instance

    Returns:
        True if port is released or service doesn't use ports, False if port is still in use

    """
    try:
        # For services that don't typically bind ports, skip port verification
        if service_name in {constants.SERVICE_TEMPORAL_WORKER}:
            logger.debug(f"Skipping port verification for {service_name} (no port binding expected)")
            return True

        # Use the existing service status checking logic
        if service_name in {constants.SERVICE_API, constants.SERVICE_UI, constants.SERVICE_TEMPORAL_SERVER}:
            # If we can't connect to the service, the port is considered released
            is_still_running = await state_manager.is_service_running(service_name, check_port=True)
            if is_still_running:
                logger.debug(f"Port verification failed - {service_name} is still responding on its port")
                return False

        logger.debug(f"Port verification successful for {service_name}")
        return True

    except (OSError, ValueError, RuntimeError) as e:
        logger.debug(f"Port verification encountered error for {service_name}: {e} (assuming port released)")
        return True  # Assume port is released if we can't check it


def _report_stop_operation_results(results: list[ServiceStopResult], logger: loguru_logger) -> None:
    """Report comprehensive results of the stop operation.

    Args:
        results: List of ServiceStopResult objects
        logger: Logger instance

    """
    if not results:
        logger.info("No services were processed during stop operation")
        return

    successful_stops = [r for r in results if r.success and r.verified]
    partial_stops = [r for r in results if r.success and not r.verified]
    failed_stops = [r for r in results if not r.success]

    if successful_stops:
        logger.debug(f"Successfully stopped: {', '.join(r.service_name for r in successful_stops)}")

    if partial_stops:
        logger.warning(f"[WARNING] Stopped but verification incomplete: {len(partial_stops)}")
        for result in partial_stops:
            retry_info = f" (after {result.retry_count} retries)" if result.retry_count > 0 else ""
            logger.warning(f"  - {result.service_name}{retry_info}")

    if failed_stops:
        logger.error(f"[FAIL] Failed to stop: {len(failed_stops)}")
        for result in failed_stops:
            retry_info = f" (after {result.retry_count} retries)" if result.retry_count > 0 else ""
            error_info = f" - {result.error_message}" if result.error_message else ""
            logger.error(f"  - {result.service_name}{retry_info}{error_info}")

    # Provide guidance for failed operations
    if failed_stops or partial_stops:
        logger.info("\n=== Recovery Recommendations ===")
        if failed_stops:
            logger.info("For failed stops:")
            logger.info("  - Check if processes are still running manually")
            logger.info("  - Use system tools (Task Manager/Activity Monitor) to terminate stubborn processes")
            logger.info("  - Consider restarting your system if processes are unresponsive")

        if partial_stops:
            logger.info("For partial stops:")
            logger.info("  - Processes may have been terminated but state cleanup is incomplete")
            logger.info("  - Try running the stop command again")
            logger.info("  - Check if services are actually still running")
    # All services processed successfully - detailed information already logged above


@app.command(name="stop-all")
def stop_all() -> None:
    """Aggressively stop all AWA-related processes including orphaned ones.

    This command performs a comprehensive cleanup by:
    1. Running normal stop operation first
    2. Finding all orphaned AWA-related processes by pattern matching
    3. Terminating discovered processes with proper signal handling
    4. Cleaning up any remaining state files

    Use this when 'make stop' doesn't clean up all processes after Ctrl+C.
    """
    init_logging()

    # Setup signal handlers for graceful shutdown
    # Use a flag to track if we're in the middle of terminating processes
    signal_received = {"value": False}

    def signal_handler(signum: int, _frame: object) -> None:
        logger = get_logger(LoggerComponent.CLI)
        if signal_received["value"]:
            # Already handling a signal, ignore subsequent ones to prevent interrupt loops
            logger.debug(f"Ignoring additional signal {signum} during stop-all")
            return

        signal_received["value"] = True
        logger.info(f"Received signal {signum} during stop-all, performing emergency cleanup...")

        # On Windows, be more careful about signal handling during subprocess operations
        if PlatformUtils.is_windows():
            logger.debug("Windows signal handling: allowing current operation to complete")
            # Give current operations a moment to complete before triggering shutdown
            time.sleep(0.1)

        # Let the asyncio event loop handle the shutdown gracefully
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(_stop_all())
    except KeyboardInterrupt:
        logger = get_logger(LoggerComponent.CLI)
        # Emergency cleanup if needed
        try:
            asyncio.run(_emergency_cleanup())
        except (OSError, RuntimeError, ValueError) as e:
            logger.warning(f"Emergency cleanup failed: {e}")
        raise typer.Exit(1) from None


async def _stop_all() -> None:
    """Execute aggressive stop-all operation for orphaned processes."""
    logger = get_logger(LoggerComponent.CLI)
    logger.info("Starting comprehensive AWA process cleanup...")

    try:
        # Run normal stop first to handle tracked services
        try:
            await _stop()
        except (OSError, TimeoutError, ValueError, RuntimeError) as e:
            logger.warning(f"Normal stop operation encountered issues: {e}")
            logger.info("Proceeding with aggressive cleanup...")

        # Find and terminate orphaned AWA processes (with multiple passes)
        orphaned_processes = await _find_orphaned_awa_processes(logger)

        # If no processes found, wait briefly and try once more to catch transitional processes
        if not orphaned_processes:
            logger.debug("No orphans found in first pass, waiting briefly for process transitions...")
            await asyncio.sleep(1.0)  # Brief delay for process state transitions
            orphaned_processes = await _find_orphaned_awa_processes(logger)

        if not orphaned_processes:
            await _cleanup_state_files(logger)
            logger.info("Comprehensive cleanup completed successfully!")
            return

        # Terminate orphaned processes
        terminated_count = await _terminate_orphaned_processes(orphaned_processes, logger)

        # Final cleanup
        await _cleanup_state_files(logger)

        logger.debug(f"Comprehensive cleanup completed! Terminated {terminated_count} processes.")
        logger.info("All services stopped.")

        # Clean up any remaining subprocess transports on Windows to prevent warnings
        if PlatformUtils.is_windows():
            await _cleanup_subprocess_transports(logger)

    except (KeyboardInterrupt, asyncio.CancelledError):
        await _emergency_cleanup()
        raise
    except Exception:
        logger.exception("Unexpected error during stop-all operation")
        await _emergency_cleanup()
        raise


async def _create_process_discovery_subprocess(system: str) -> asyncio.subprocess.Process:
    """Create a subprocess for discovering processes based on the system type."""
    if system == "windows":
        # Windows process discovery using PowerShell (WMIC replacement)
        # Get-CimInstance is the modern replacement for WMIC
        powershell_script = (
            "Get-CimInstance -ClassName Win32_Process | "
            "Select-Object ProcessId,ParentProcessId,CommandLine | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        return await asyncio.create_subprocess_exec(
            "powershell",
            "-Command",
            powershell_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
            stdin=asyncio.subprocess.DEVNULL,
        )
    # Unix-based process discovery using ps
    return await asyncio.create_subprocess_exec(
        "ps",
        "ax",
        "-o",
        "pid,ppid,command",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        stdin=asyncio.subprocess.DEVNULL,
    )


def _get_awa_process_patterns() -> list[str]:
    """Get the list of AWA process patterns to match."""
    return [
        r".*awa\.main.*",  # AWA CLI processes
        r"uv\s+run.*awa\.main.*",  # UV-managed AWA processes
        r".*-m\s+awa\.core\.api.*",  # AWA API server (python -m format)
        r".*uvicorn.*awa\.core\.api.*",  # AWA API server (uvicorn format)
        r".*-m\s+awa\.core\.worker.*",  # AWA Worker (python -m format)
        r".*temporal.*server.*",  # Temporal server
        r"^temporal\s+server\s+start-dev.*",  # Temporal server (more specific)
        r".*pnpm.*ui:dev.*",  # UI dev server
        r".*pnpm.*ui:preview.*",  # UI preview server
        r".*astro.*dev.*",  # Astro dev server
        r".*node.*astro.*",  # Node running Astro
    ]


def _parse_process_line(line: str, system: str, logger: loguru_logger) -> tuple[str, str, str] | None:
    """Parse a single process line and return (pid, ppid, command) or None if invalid."""
    try:
        if system == "windows":
            # Parse Windows PowerShell CSV output (ProcessId,ParentProcessId,CommandLine)
            parts = [p.strip('"') for p in line.split('","') if p.strip()]
            if len(parts) >= WINDOWS_PS_MIN_PARTS:
                pid = parts[0].strip('"') if parts[0] else ""
                ppid = parts[1] if parts[1] else ""
                command = parts[2].strip('"') if parts[2] else ""
                return (pid, ppid, command)
        else:
            # Parse Unix ps output
            parts = line.strip().split(None, 2)
            if len(parts) >= UNIX_PS_MIN_PARTS:
                return (parts[0], parts[1], parts[2])
    except (ValueError, IndexError) as e:
        logger.debug(f"Failed to parse process line '{line}': {e}")

    return None


def _should_skip_process(command: str, logger: loguru_logger, pid: str) -> bool:
    """Check if a process should be skipped to avoid self-termination."""
    if "stop-all" in command or ("start" in command and "awa.main" in command and "temporal" not in command):
        logger.debug(f"Skipping current AWA CLI process: PID {pid} - {command[:100]}")
        return True
    return False


async def _find_orphaned_awa_processes(logger: loguru_logger) -> list[dict]:
    """Find all AWA-related processes that might be orphaned.

    Returns:
        List of process info dictionaries with keys: pid, command, ppid

    """
    orphaned_processes = []
    system = platform.system().lower()

    try:
        proc = await _create_process_discovery_subprocess(system)
        stdout, stderr = await proc.communicate()

        # Clean up subprocess pipes to prevent Windows transport cleanup warnings
        try:
            if proc.stdout and hasattr(proc.stdout, "close"):
                proc.stdout.close()
            if proc.stderr and hasattr(proc.stderr, "close"):
                proc.stderr.close()
            if proc.stdin and hasattr(proc.stdin, "close"):
                proc.stdin.close()
        except (OSError, ValueError, AttributeError) as e:
            # Log any issues closing pipes for debugging
            logger.debug(f"Pipe cleanup encountered issues: {e}")

        if proc.returncode != 0:
            logger.warning(f"Process discovery failed: {stderr.decode()}")
            return orphaned_processes

        # Parse process output and find AWA-related processes
        lines = stdout.decode().strip().split("\n")[1:]  # Skip header
        awa_patterns = _get_awa_process_patterns()

        for line in lines:
            if not line.strip():
                continue

            parsed = _parse_process_line(line, system, logger)
            if not parsed:
                continue

            pid, ppid, command = parsed

            if not pid or not pid.isdigit() or not command:
                continue

            # Check if process matches any AWA patterns
            # Add length check to prevent regex issues with very long commands
            max_command_length = 1000
            if len(command) > max_command_length:
                command = command[:max_command_length]  # Truncate very long commands
            for pattern in awa_patterns:
                try:
                    # Use timeout-safe regex with limited backtracking
                    if re.search(pattern, command, re.IGNORECASE):
                        if _should_skip_process(command, logger, pid):
                            continue

                        orphaned_processes.append(
                            {
                                "pid": int(pid),
                                "ppid": int(ppid) if ppid.isdigit() else 0,
                                "command": command.strip(),
                            },
                        )
                        logger.debug(f"Found AWA process: PID {pid} - {command[:100]}")
                        break  # Found a match, no need to check other patterns
                except re.error as e:
                    logger.debug(f"Regex error with pattern '{pattern}' on command '{command}': {e}")
                    continue
                except (OSError, ValueError, TypeError) as e:
                    logger.debug(f"Unexpected error in pattern matching for command '{command}': {e}")
                    continue

    except (OSError, subprocess.SubprocessError, ValueError, RuntimeError):
        logger.exception("Failed to discover orphaned processes")

    return orphaned_processes


async def _terminate_orphaned_processes(processes: list[dict], logger: loguru_logger) -> int:
    """Terminate the given list of orphaned processes.

    Args:
        processes: List of process dictionaries
        logger: Logger instance

    Returns:
        Number of successfully terminated processes

    """
    terminated_count = 0
    system = platform.system().lower()

    for proc_info in processes:
        pid = proc_info["pid"]
        command = proc_info["command"]

        try:
            logger.debug(f"Terminating PID {pid}: {command[:80]}...")

            if system == "windows":
                # Windows process termination
                terminate_proc = await asyncio.create_subprocess_exec(
                    "taskkill",
                    "/F",
                    "/PID",
                    str(pid),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.DEVNULL,
                    stdin=asyncio.subprocess.DEVNULL,
                )
                _stdout, _ = await terminate_proc.communicate()

                # Ensure subprocess is cleaned up
                if terminate_proc.returncode is None:
                    terminate_proc.terminate()
                    await terminate_proc.wait()

                if terminate_proc.returncode == 0:
                    terminated_count += 1
                    logger.debug(f"[OK] Terminated PID {pid}")
                else:
                    logger.debug(f"Failed to terminate PID {pid} with exit code {terminate_proc.returncode}")

            else:
                # Unix process termination with escalating signals
                try:
                    # Try graceful termination first
                    os.kill(pid, signal.SIGTERM)

                    # Wait a moment for graceful shutdown
                    await asyncio.sleep(2)

                    # Check if process is still running
                    try:
                        os.kill(pid, 0)  # Signal 0 just checks if process exists
                        # Process still exists, use SIGKILL
                        os.kill(pid, signal.SIGKILL)
                        logger.debug(f"[OK] Force terminated PID {pid}")
                    except ProcessLookupError:
                        # Process already terminated gracefully
                        logger.debug(f"[OK] Gracefully terminated PID {pid}")

                    terminated_count += 1

                except ProcessLookupError:
                    logger.debug(f"Process PID {pid} already terminated")
                except PermissionError:
                    logger.warning(f"Permission denied terminating PID {pid}")

        except (OSError, PermissionError, ProcessLookupError, ValueError) as e:
            logger.warning(f"Error terminating PID {pid}: {e}")

    return terminated_count


async def _cleanup_state_files(logger: loguru_logger) -> None:
    """Clean up any remaining state files after process termination."""
    try:
        state_manager = StateManager()
        await state_manager.cleanup_state()
        logger.debug("State files cleaned up successfully")
    except (OSError, ValueError, RuntimeError) as e:
        logger.warning(f"State file cleanup encountered issues: {e}")


async def _cleanup_subprocess_transports(logger: loguru_logger) -> None:
    """Clean up any remaining subprocess transports to prevent Windows event loop warnings."""
    try:
        # Give the event loop time to finish any pending subprocess operations
        await asyncio.sleep(0.1)

        # Force garbage collection to clean up any unreferenced transports
        gc.collect()

        # Give a final moment for cleanup
        await asyncio.sleep(0.1)

        logger.debug("Subprocess transport cleanup completed")
    except (OSError, RuntimeError) as e:
        logger.debug(f"Subprocess transport cleanup encountered minor issues: {e}")
