"""Service manager for AWA."""

import asyncio
import contextlib
import os
import signal
import subprocess
import sys
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

# Add psutil import and availability check for Windows process PID resolution
try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from awa.core.cli import constants
from awa.core.cli.state_manager import StateManager
from awa.core.engine.temporal_client import TemporalClient, WorkflowExecutionError
from awa.core.engine.temporal_worker import TemporalWorker
from awa.core.logger.logger import LoggerComponent, get_logger, get_subprocess_logger
from awa.core.models.cli.service_state import ServiceInfo
from awa.core.models.cli.ui_mode import UIMode
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.cli_utils import is_packaged_mode
from awa.core.utils.command_utils import CommandUtils
from awa.core.utils.platform_utils import PlatformUtils
from awa.core.utils.temporal_utils import _get_active_worker_pollers

# Service startup timeout constants
DEFAULT_INITIAL_OUTPUT_TIMEOUT = 15
UI_INITIAL_OUTPUT_TIMEOUT = 45  # UI needs extra time for docs + UI build steps


class ServiceManager:
    def __init__(self) -> None:
        self.logger = get_logger(LoggerComponent.CLI)
        self.temporal_client: TemporalClient | None = None
        self.temporal_worker: TemporalWorker | None = None
        self.state_manager = StateManager()
        # Track running processes
        self.service_processes: dict[str, asyncio.subprocess.Process] = {}
        # Track background tasks for cleanup to prevent event loop errors
        self.background_tasks: dict[str, asyncio.Task] = {}
        # Track subprocess transports for explicit cleanup to prevent event loop errors
        self.subprocess_transports: dict[str, asyncio.subprocess.Process] = {}
        # Unified service startup state tracking
        self.service_startup_flags: dict[str, bool] = {}

    def _get_package_aware_command(self, command_suffix: str) -> str:
        """Generate package-aware command based on execution mode.

        Args:
            command_suffix: The command suffix (e.g., "worker", "ui --ui dev")

        Returns:
            Complete command string appropriate for current execution mode

        """
        if is_packaged_mode():
            return f'"{sys.executable}" -m awa.main {command_suffix}'
        return f"uv run -m awa.main {command_suffix}"

    def _set_service_startup_flag(self, service_name: str, *, started: bool) -> None:
        """Set service startup flag with logging for state tracking.

        Args:
            service_name: Name of the service
            started: Flag value to set

        """
        old_value = self.service_startup_flags.get(service_name, False)
        if old_value != started:
            self.service_startup_flags[service_name] = started
            self.logger.debug(f"Service startup flag changed: {service_name} {old_value} -> {started}")

    def _get_api_command(self) -> str:
        """Generate package-aware API service command.

        Returns:
            Complete API command string appropriate for current execution mode

        """
        # API service doesn't have a main CLI entry point, so use module directly
        if is_packaged_mode():
            return f'"{sys.executable}" -m awa.core.api'
        return "uv run -m awa.core.api"

    def _find_real_service_pid_windows(self, wrapper_pid: int, service_name: str, timeout: int = 3) -> int | None:
        """Find the actual service process PID from the wrapper process on Windows.

        Args:
            wrapper_pid: PID of the shell/wrapper process
            service_name: Name of the service to identify the correct child process
            timeout: Maximum time to wait for child process to appear

        Returns:
            Real service PID if found, None otherwise

        """
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available, using wrapper PID (may cause detach mode issues)")
            return wrapper_pid

        # Define expected executable patterns for each service
        service_executables = {
            constants.SERVICE_TEMPORAL_SERVER: ["temporal.exe", "temporal"],
            constants.SERVICE_TEMPORAL_WORKER: ["uv.exe", "python.exe", "python"],
            constants.SERVICE_API: ["uv.exe", "python.exe", "python", "uvicorn"],
            constants.SERVICE_UI: ["uv.exe", "node.exe", "node", "npm.exe", "npm"],
        }

        expected_exes = service_executables.get(service_name, [])

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                wrapper = psutil.Process(wrapper_pid)
                # Look for direct children first, then recursive
                for child in wrapper.children(recursive=True):
                    try:
                        child_name = child.name().lower()
                        # Check if child matches expected executable for this service
                        if any(exe.lower() in child_name for exe in expected_exes):
                            self.logger.debug(f"Found real service PID {child.pid} ({child_name}) for {service_name}")
                            return child.pid
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

            time.sleep(0.1)  # Brief wait before retry

        self.logger.warning(f"Could not find real service PID for {service_name}, using wrapper PID {wrapper_pid}")
        return wrapper_pid

    def _verify_pid_exists(self, pid: int) -> bool:
        """Verify that a PID actually exists and represents a running process.

        Args:
            pid: Process ID to check

        Returns:
            True if process exists and is running, False otherwise

        """
        if not PSUTIL_AVAILABLE:
            # Fallback to platform-specific checks
            if PlatformUtils.is_windows():
                try:
                    # Use tasklist command to check if PID exists
                    # Security: Using fixed command with validated integer PID parameter
                    result = subprocess.run(  # noqa: S603
                        ["tasklist", "/FI", f"PID eq {pid}"],  # noqa: S607
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    return str(pid) in result.stdout
                except (OSError, subprocess.SubprocessError, ValueError):
                    return False
            else:
                # Unix-like systems
                try:
                    os.kill(pid, 0)
                    return True
                except (OSError, ProcessLookupError):
                    return False

        try:
            process = psutil.Process(pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    @classmethod
    async def create(cls, terminate_all: bool = False) -> "ServiceManager":
        """Class method for async ServiceManager creation."""
        instance = cls()
        await instance._async_init(terminate_all=terminate_all)
        return instance

    async def _async_init(self, terminate_all: bool = False) -> None:
        """Async initialization of temporal components."""
        self.temporal_client = await TemporalClient.create(terminate_all=terminate_all)
        self.temporal_worker = TemporalWorker(self.temporal_client)

    def display_service_urls(self, services: list[str] | None = None) -> None:
        """Display service URLs for easy access.

        Args:
            services: Optional list of service names to filter URLs. If None, displays all URLs.

        """
        self.logger.info("Services running!")

        # If no services filter specified, show all URLs
        if services is None:
            services = [constants.SERVICE_UI, constants.SERVICE_API, constants.SERVICE_TEMPORAL_SERVER]

        # Display URLs based on service filter
        if constants.SERVICE_UI in services:
            self.logger.info(
                f"AWA UI: http://{EnvConfig.get_env_config().awa_ui_host}:{EnvConfig.get_env_config().awa_ui_port}",
            )
            self.logger.info(
                f"AWA Docs: http://{EnvConfig.get_env_config().awa_ui_host}:{EnvConfig.get_env_config().awa_ui_port}/docs",
            )

        if constants.SERVICE_API in services:
            self.logger.info(
                f"AWA API: http://{EnvConfig.get_env_config().awa_api_host}:{EnvConfig.get_env_config().awa_api_port}/docs",
            )

        if constants.SERVICE_TEMPORAL_SERVER in services:
            self.logger.info(
                f"Temporal UI: http://{EnvConfig.get_env_config().temporal_ui_host}:{EnvConfig.get_env_config().temporal_ui_port}",
            )
            self.logger.info(
                f"Temporal Server: grpc://{EnvConfig.get_env_config().temporal_server_host}:{EnvConfig.get_env_config().temporal_server_port},",
            )
            self.logger.info(
                f"Temporal Metrics: http://{EnvConfig.get_env_config().temporal_server_host}:{EnvConfig.get_env_config().temporal_metrics_port}/metrics",
            )

    async def validate_service_process(self, service_name: str) -> bool:
        """Validate that a service process is running based on state file PID data.

        Args:
            service_name: Name of the service to validate

        Returns:
            True if service exists in state and process is running, False otherwise

        """
        try:
            # Check if service exists in state file
            service_info = await self.state_manager.get_service_info(service_name)
            if not service_info:
                self.logger.debug(f"PID validation: {service_name} not found in state file")
                return False

            # Validate that the PID is still running using our enhanced verification
            if self._verify_pid_exists(service_info.pid):
                self.logger.debug(f"PID validation: {service_name} process {service_info.pid} is running")
                return True
            self.logger.debug(f"PID validation: {service_name} process {service_info.pid} is not running")
            # Clean up stale state entry
            await self.state_manager.remove_service(service_name)
            return False

        except (OSError, ValueError, TypeError) as e:
            self.logger.warning(f"PID validation failed for {service_name}: {e}")
            return False

    async def check_all_services(self, ui_mode: UIMode = UIMode.DEV, startup_mode: bool = False) -> dict:
        """Check all services using PID-first validation followed by external health checks.

        Implementation follows Phase 1.3 Enhanced PID-First Validation:
        1. Primary check: Process existence via PID validation from state file
        2. Secondary check: External health indicators (port/API checks)
        3. Combined result: Service is "ready" only if both checks pass

        Args:
            ui_mode: UI mode to determine if UI service should be checked
            startup_mode: If True, use extended timeout thresholds for startup phase (AWA-133 Phase 2.1)

        Returns:
            Dictionary mapping service names to their readiness status

        """
        if self.temporal_worker is None:
            raise RuntimeError("ServiceManager not properly initialized. Use ServiceManager.create()")

        self.logger.debug("Starting PID-first validation for all services")
        service_status = {}

        # Define services to check based on UI mode
        services_to_check = [
            constants.SERVICE_TEMPORAL_SERVER,
            constants.SERVICE_TEMPORAL_WORKER,
            constants.SERVICE_API,
        ]
        if ui_mode != UIMode.NONE:
            services_to_check.append(constants.SERVICE_UI)

        # Check each service with PID-first validation
        for service_name in services_to_check:
            self.logger.debug(f"Checking service: {service_name}")

            # Phase 1: Primary PID validation check
            pid_validation_passed = await self.validate_service_process(service_name)

            if not pid_validation_passed:
                # If PID validation fails, service is definitively NOT running
                self.logger.debug(f"Service {service_name}: PID validation failed - service NOT running")
                service_status[service_name] = False
                continue

            self.logger.debug(f"Service {service_name}: PID validation passed - proceeding to external health checks")

            # Phase 2: Secondary external health check (only if PID validation passed)
            external_health_passed = await self._perform_external_health_check(service_name, startup_mode=startup_mode)

            # Phase 3: Combined result - both checks must pass
            service_ready = pid_validation_passed and external_health_passed

            if service_ready:
                self.logger.debug(
                    f"Service {service_name}: Both PID validation and external health checks passed - READY",
                )
            else:
                self.logger.debug(
                    f"Service {service_name}: PID validation passed but external health check failed - NOT READY",
                )

            service_status[service_name] = service_ready

        # Handle UI service when UIMode.NONE
        if ui_mode == UIMode.NONE:
            service_status[constants.SERVICE_UI] = True

        self.logger.debug(f"Service readiness status: {service_status}")
        return service_status

    async def _perform_external_health_check(self, service_name: str, startup_mode: bool = False) -> bool:
        """Perform external health checks for a service.

        Args:
            service_name: Name of the service to check
            startup_mode: If True, use extended timeout thresholds for startup phase (AWA-133 Phase 2.1)

        Returns:
            True if external health check passes, False otherwise

        """
        try:
            if service_name == constants.SERVICE_TEMPORAL_SERVER:
                # Check if Temporal server is running by attempting to connect
                await self.temporal_client.get_client()
                self.logger.debug(f"External health check: {service_name} connection successful")
                return True

            if service_name == constants.SERVICE_TEMPORAL_WORKER:
                # Check for active worker pollers with startup mode awareness (AWA-133 Phase 2.1)
                active_pollers = await _get_active_worker_pollers(
                    self.temporal_worker.default_task_queue,
                    startup_mode=startup_mode,
                )
                result = bool(active_pollers)
                timeout_context = "startup" if startup_mode else "runtime"
                self.logger.debug(
                    f"External health check: {service_name} active pollers ({timeout_context} mode): {result}",
                )
                return result

            if service_name == constants.SERVICE_API:
                # Check API port status
                result = await CommandUtils.check_service_status(
                    EnvConfig.get_env_config().awa_api_host,
                    EnvConfig.get_env_config().awa_api_port,
                )
                self.logger.debug(f"External health check: {service_name} port check: {result}")
                return result

            if service_name == constants.SERVICE_UI:
                # Check UI port status
                result = await CommandUtils.check_service_status(
                    EnvConfig.get_env_config().awa_ui_host,
                    EnvConfig.get_env_config().awa_ui_port,
                )
                self.logger.debug(f"External health check: {service_name} port check: {result}")
                return result

            self.logger.warning(f"External health check: Unknown service {service_name}")
            return False

        except Exception as e:  # noqa: BLE001
            self.logger.debug(f"External health check failed for {service_name}: {e}")
            return False

    async def _start_service_subprocess(
        self,
        service_name: str,
        command: str,
        port: int | None = None,
        env_vars: dict[str, str] | None = None,
        detach: bool = False,
    ) -> bool:
        """Start a service as a subprocess and track its PID.

        Args:
            service_name: Name of the service (from constants)
            command: Command to run the service
            port: Port number if the service uses one
            env_vars: Additional environment variables to set
            detach: Whether to run the service in detached mode

        Returns:
            True if service started successfully, False otherwise

        """
        try:
            self.logger.info(f"Starting {service_name}...")

            # Set environment variables temporarily if provided
            original_env = {}
            if env_vars:
                for key, value in env_vars.items():
                    original_env[key] = os.environ.get(key)
                    os.environ[key] = value

            try:
                # Use CommandUtils.stream_command_async to start the process
                gen = CommandUtils.stream_command_async(command, detach=detach)
                proc = await gen.__anext__()  # Get the process handle

                if proc.pid is None:
                    self.logger.error(f"Failed to get PID for {service_name}")
                    return False

                # Store the process for management
                self.service_processes[service_name] = proc

                # In detached mode, don't store subprocess transport to avoid cleanup interference
                if not detach:
                    self.subprocess_transports[service_name] = proc
                else:
                    # For detached mode, don't close pipes immediately to avoid terminating the process
                    # The background task will handle output consumption and cleanup
                    self.logger.debug(f"Detached mode: keeping pipes open for {service_name}")

                # Determine the correct PID to track
                tracked_pid = proc.pid

                # For Windows in detach mode, find the real service PID instead of wrapper PID
                if detach and PlatformUtils.is_windows():
                    real_pid = self._find_real_service_pid_windows(proc.pid, service_name)
                    if real_pid and real_pid != proc.pid:
                        tracked_pid = real_pid
                        self.logger.info(
                            f"Tracking service PID {real_pid} instead of wrapper PID {proc.pid} for {service_name}",
                        )

                # Create service info and save to state
                service_info = ServiceInfo(
                    pid=tracked_pid,
                    port=port,
                    started_at=datetime.now(UTC),
                )
                await self.state_manager.update_service(service_name, service_info)

                self.logger.debug(f"Started {service_name} with tracked PID {tracked_pid}")

                # Handle output consumption based on detach mode
                if not detach:
                    # Non-detached: Start background task for continuous output consumption
                    task = asyncio.create_task(self._consume_process_output(gen, service_name))
                    self.background_tasks[service_name] = task  # Track for cleanup
                else:
                    # Detached mode: Consume initial output to let process stabilize, then exit
                    task = asyncio.create_task(self._consume_initial_output(gen, service_name))
                    self.background_tasks[service_name] = task  # Track for cleanup

                return True

            finally:
                # Restore original environment variables
                if env_vars:
                    for key in env_vars:
                        if original_env[key] is None:
                            os.environ.pop(key, None)
                        else:
                            os.environ[key] = original_env[key]

        except Exception:
            self.logger.exception(f"Failed to start {service_name}")
            return False

    async def _consume_process_output(
        self,
        output_generator: AsyncGenerator[str, None],
        service_name: str,
    ) -> None:
        """Consume process output in the background to prevent blocking."""
        try:
            # Use raw subprocess logger to avoid double-formatting
            # This outputs subprocess logs directly without re-processing through loguru
            subprocess_logger = get_subprocess_logger(service_name)

            async for line in output_generator:
                # Output raw subprocess line without additional processing
                # This preserves the original AWA formatting from the subprocess
                subprocess_logger.info(line.rstrip())
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Output consumption stopped for {service_name}: {e}")

    async def _consume_initial_output(
        self,
        output_generator: AsyncGenerator[str, None],
        service_name: str,
        timeout_seconds: int = DEFAULT_INITIAL_OUTPUT_TIMEOUT,
    ) -> None:
        """Consume initial process output for detached mode to let process stabilize."""
        # UI service needs more time due to build steps (docs, UI build, server start)
        if service_name == constants.SERVICE_UI and timeout_seconds == DEFAULT_INITIAL_OUTPUT_TIMEOUT:
            timeout_seconds = UI_INITIAL_OUTPUT_TIMEOUT
        try:
            subprocess_logger = get_subprocess_logger(service_name)
            start_time = time.time()

            # Consume output for a brief period to let the process start properly
            async for line in output_generator:
                subprocess_logger.info(line.rstrip())

                # Exit early if we've consumed output for the timeout period
                if time.time() - start_time > timeout_seconds:
                    self.logger.debug(f"Initial output consumption completed for {service_name}")
                    break

        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Initial output consumption stopped for {service_name}: {e}")

    async def cleanup_background_tasks(self, service_name: str | None = None) -> None:
        """Clean up background tasks to prevent event loop errors.

        Args:
            service_name: Specific service name to clean up. If None, cleans up all tasks.

        """
        # Check if event loop is still running to avoid RuntimeError during shutdown
        try:
            loop = asyncio.get_running_loop()
            if loop.is_closed():
                self.logger.debug("Event loop is closed, skipping background task cleanup")
                self.background_tasks.clear()
                self.service_startup_flags.clear()
                return
        except RuntimeError:
            # No running event loop
            self.logger.debug("No running event loop, skipping background task cleanup")
            self.background_tasks.clear()
            self.service_startup_flags.clear()
            return

        if service_name:
            task = self.background_tasks.pop(service_name, None)
            if task and not task.done():
                task.cancel()
                with contextlib.suppress(asyncio.CancelledError, RuntimeError):
                    await task
        else:
            # Clean up all background tasks
            tasks_to_cancel = [task for task in self.background_tasks.values() if not task.done()]
            if tasks_to_cancel:
                for task in tasks_to_cancel:
                    task.cancel()
                try:
                    await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
                except (RuntimeError, asyncio.CancelledError) as e:
                    self.logger.debug(f"Background task cleanup error: {e}")
            self.background_tasks.clear()
            # Reset all service startup flags when cleaning up all tasks
            self.service_startup_flags.clear()

    async def cleanup_subprocess_transports(self, service_name: str | None = None) -> None:
        """Clean up subprocess transports to prevent event loop errors.

        Args:
            service_name: Specific service name to clean up. If None, cleans up all transports.

        """
        # Check if event loop is still running to avoid RuntimeError during shutdown
        try:
            loop = asyncio.get_running_loop()
            if loop.is_closed():
                self.logger.debug("Event loop is closed, skipping subprocess transport cleanup")
                self.subprocess_transports.clear()
                return
        except RuntimeError:
            # No running event loop
            self.logger.debug("No running event loop, skipping subprocess transport cleanup")
            self.subprocess_transports.clear()
            return

        if service_name:
            proc = self.subprocess_transports.pop(service_name, None)
            if proc and proc.returncode is None:
                await self._cleanup_single_subprocess(proc, service_name)
        else:
            # Clean up all subprocess transports
            for name, proc in list(self.subprocess_transports.items()):
                if proc.returncode is None:
                    await self._cleanup_single_subprocess(proc, name)
            self.subprocess_transports.clear()

    async def _cleanup_single_subprocess(self, proc: object, name: str) -> None:
        """Clean up a single subprocess with comprehensive error handling."""
        try:
            # First try graceful termination
            proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=2)
            self.logger.debug(f"Gracefully cleaned up subprocess transport for {name}")
        except (TimeoutError, ProcessLookupError, OSError, RuntimeError) as e:
            self.logger.debug(f"Subprocess transport cleanup error for {name}: {e}")
            # If graceful termination failed, try force kill
            try:
                proc.kill()
                await asyncio.wait_for(proc.wait(), timeout=1)
                self.logger.debug(f"Force killed subprocess transport for {name}")
            except (TimeoutError, ProcessLookupError, OSError, RuntimeError, AttributeError) as e:
                # Process might already be dead or event loop closed
                self.logger.debug(f"Force kill also failed for {name}: {e}")
        except (AttributeError, TypeError, ValueError) as e:
            # Catch any other subprocess-related exceptions
            self.logger.debug(f"Unexpected error during subprocess cleanup for {name}: {e}")

    def _ensure_temporal_components_initialized(self) -> None:
        """Ensure temporal worker and client are initialized."""
        if self.temporal_worker is None or self.temporal_client is None:
            raise RuntimeError("ServiceManager not properly initialized. Use ServiceManager.create()")

    async def _handle_running_service_cleanup(
        self,
        service_name: str,
        service_info: object,
        terminated_services: list[str],
    ) -> None:
        """Handle cleanup of a running service process."""
        self.logger.warning(f"Found running process for {service_name} (PID: {service_info.pid}) - terminating")

        try:
            # Terminate the running process using StateManager's stop_service
            success = await self.state_manager.stop_service(service_name)

            if success:
                self.logger.info(f"[SUCCESS] Successfully terminated {service_name} (PID: {service_info.pid})")
                terminated_services.append(service_name)
            else:
                self.logger.error(f"[FAILED] Failed to terminate {service_name} (PID: {service_info.pid})")

                # Following Fail Fast Philosophy - this is a critical error
                def _fail_termination() -> None:
                    msg = (
                        f"Pre-start cleanup failed: Could not terminate existing "
                        f"{service_name} process (PID: {service_info.pid})"
                    )
                    raise RuntimeError(msg)  # noqa: TRY301

                _fail_termination()

        except Exception as exc:
            self.logger.exception(f"✗ Error terminating {service_name}")

            # Following Fail Fast Philosophy - don't continue with corrupted state
            def _fail_with_exception(error: Exception) -> None:
                raise RuntimeError(f"Pre-start cleanup failed: Error terminating {service_name}: {error}") from error

            _fail_with_exception(exc)

    async def _handle_stale_service_cleanup(
        self,
        service_name: str,
        service_info: object,
        invalid_entries: list[str],
    ) -> None:
        """Handle cleanup of stale service state entries."""
        msg = f"Process for {service_name} (PID: {service_info.pid}) is not running - removing stale state entry"
        self.logger.info(msg)

        try:
            await self.state_manager.remove_service(service_name)
            invalid_entries.append(service_name)
            self.logger.info(f"[CLEANED] Cleaned up stale state entry for {service_name}")
        except Exception as exc:
            self.logger.exception(f"[ERROR] Error cleaning up state entry for {service_name}")

            # Following Fail Fast Philosophy - state corruption is critical
            def _fail_state_cleanup(error: Exception) -> None:
                msg = f"Pre-start cleanup failed: Could not clean up state entry for {service_name}: {error}"
                raise RuntimeError(msg) from error

            _fail_state_cleanup(exc)

    async def _log_cleanup_summary(self, terminated_services: list[str], invalid_entries: list[str]) -> None:
        """Log comprehensive cleanup summary."""
        if terminated_services or invalid_entries:
            self.logger.info("Pre-start cleanup completed successfully:")
            if terminated_services:
                self.logger.info(f"  [SUCCESS] Terminated running processes: {', '.join(terminated_services)}")
            if invalid_entries:
                self.logger.info(f"  [SUCCESS] Cleaned up stale state entries: {', '.join(invalid_entries)}")
        else:
            self.logger.info("Pre-start cleanup completed - no cleanup actions required")

    async def _terminate_existing_startup_processes(self) -> None:
        """Terminate any existing 'awa.main start' processes to prevent conflicts.

        This prevents race conditions where an existing attached startup process
        interferes with the current startup process by auto-restarting services
        during cleanup.

        However, we need to be more careful about timing to avoid terminating
        legitimate concurrent startup processes.
        """
        try:
            # First, check if there are any actual services running
            # If no services are running, we probably don't need to terminate startup processes
            all_services = await self.state_manager.get_all_services()
            if not all_services:
                self.logger.debug("No services in state, skipping startup process termination")
                return

            # Find all 'uv run -m awa.main start' processes
            proc = await asyncio.create_subprocess_exec(
                "/bin/ps",
                "aux",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
            if proc.returncode != 0:
                self.logger.warning(f"ps command failed: {stderr.decode()}")
                return

            process_output = stdout.decode()

            startup_processes = []
            current_pid = os.getpid()

            # Get all parent processes in our process tree to avoid terminating ourselves
            # This handles cases where uv run creates wrapper processes
            excluded_pids = {current_pid}
            try:
                if PSUTIL_AVAILABLE:
                    current_proc = psutil.Process(current_pid)
                    # Add all parent processes to exclusion list
                    for parent in current_proc.parents():
                        excluded_pids.add(parent.pid)
            except (OSError, ValueError, AttributeError):
                self.logger.debug("Failed to get parent processes, using basic PID exclusion")

            for line in process_output.splitlines():
                if "uv run -m awa.main start" in line and "grep" not in line:
                    parts = line.split()
                    if len(parts) >= constants.MIN_PS_BASIC_FIELDS:
                        try:
                            pid = int(parts[1])
                            # Don't kill ourselves or our parent processes
                            if pid not in excluded_pids:
                                startup_processes.append(pid)
                        except ValueError:
                            continue

            if startup_processes:
                self.logger.info(f"Found {len(startup_processes)} existing startup process(es): {startup_processes}")

                for pid in startup_processes:
                    try:
                        self.logger.warning(f"Terminating existing startup process {pid} to prevent conflicts")
                        os.kill(pid, signal.SIGTERM)
                        # Give it a moment to terminate
                        await asyncio.sleep(0.5)

                        # Check if it's still running and force kill if needed
                        if self.state_manager.is_process_running(pid):
                            self.logger.warning(f"Force killing startup process {pid}")
                            os.kill(pid, signal.SIGKILL)
                    except (OSError, ProcessLookupError):
                        # Process already gone, which is fine
                        pass

                # Give some time for processes to clean up
                await asyncio.sleep(1.0)
                self.logger.info("[SUCCESS] Existing startup process cleanup completed")
            else:
                self.logger.debug("No existing startup processes found")

        except (OSError, ValueError, TimeoutError) as exc:
            self.logger.warning(f"Failed to check for existing startup processes: {exc}")
            # Don't fail the whole operation, just continue

    async def cleanup_existing_services(self) -> None:
        """Clean up existing services before starting new ones.

        Loads state from state file, checks if processes are still running,
        terminates running processes, and cleans up invalid state entries.
        Implements the Fail Fast Philosophy with comprehensive logging.
        """
        self.logger.info("Starting pre-start service cleanup...")

        # STEP 1: Terminate any existing startup processes first to prevent conflicts
        await self._terminate_existing_startup_processes()

        # STEP 2: Load current state from state manager
        all_services = await self.state_manager.get_all_services()

        if not all_services:
            self.logger.info("No existing services found in state - cleanup complete")
            return

        self.logger.info(f"Found {len(all_services)} services in state: {list(all_services.keys())}")

        terminated_services = []
        invalid_entries = []

        for service_name, service_info in all_services.items():
            self.logger.info(f"Checking service '{service_name}' (PID: {service_info.pid})")

            # Check if the process is still running
            if self.state_manager.is_process_running(service_info.pid):
                await self._handle_running_service_cleanup(service_name, service_info, terminated_services)
            else:
                await self._handle_stale_service_cleanup(service_name, service_info, invalid_entries)

        # Log comprehensive cleanup summary
        await self._log_cleanup_summary(terminated_services, invalid_entries)

        # Final verification - ensure no services remain in state unless they should
        remaining_services = await self.state_manager.get_all_services()
        if remaining_services:
            # This should not happen if cleanup worked correctly
            remaining_service_list = list(remaining_services.keys())
            self.logger.error(f"✗ Pre-start cleanup failed: Services still remain in state: {remaining_service_list}")

            def _fail_remaining_services() -> None:
                msg = f"Pre-start cleanup failed: Unexpected services remain in state: {remaining_service_list}"
                raise RuntimeError(msg)

            _fail_remaining_services()

        self.logger.info("[VALIDATED] Pre-start service cleanup validation passed - ready for service startup")

    async def _handle_pre_startup_checks(
        self,
        ui_mode: UIMode,
        terminate_all: bool,
        detach: bool,
        services: list[str] | None,
    ) -> tuple[dict[str, bool], dict[str, bool]]:
        """Handle pre-startup checks and cleanup if needed."""
        # Check current status first to determine if cleanup is needed
        current_status = await self.check_all_services(ui_mode=ui_mode or UIMode.DEV, startup_mode=True)

        # Filter to only requested services if specified
        if services is not None:
            requested_status = {name: current_status[name] for name in services if name in current_status}
        else:
            requested_status = current_status

        # Only cleanup if we have services that need to be restarted or if there are conflicts
        needs_cleanup = False

        # Check if any services are already running but need different mode (detached vs non-detached)
        # For now, we'll allow coexistence - existing detached services can stay while non-detached starts
        if not detach and any(requested_status.values()):
            # Non-detached start with some services already running - check if they're healthy
            all_healthy = all(requested_status.values())
            if all_healthy:
                self.logger.info("All requested services are already running and healthy. Entering monitoring mode...")
                # Return empty status to signal no services need to be started
                return {}, dict.fromkeys(requested_status.keys(), False)

        # Only do aggressive cleanup if there are unhealthy services or explicit terminate_all flag
        if needs_cleanup or terminate_all:
            try:
                await self.cleanup_existing_services()
            except RuntimeError as exc:
                self.logger.exception("Pre-start cleanup failed")
                raise RuntimeError(f"Service startup aborted due to cleanup failure: {exc}") from exc

        return current_status, requested_status

    async def _prepare_service_status(
        self,
        ui_mode: UIMode,
        services: list[str] | None,
    ) -> tuple[dict[str, bool], dict[str, bool]]:
        """Prepare and filter service status for startup."""
        # Initial startup check - use extended timeout thresholds (AWA-133 Phase 2.1)
        status = await self.check_all_services(ui_mode=ui_mode or UIMode.DEV, startup_mode=True)

        # Filter status to only requested services if specified
        if services is not None:
            filtered_status = {name: status[name] for name in services if name in status}
            # Set services not in requested list to True (already running) so they won't be started
            for service_name in status:
                if service_name not in services:
                    status[service_name] = True
        else:
            filtered_status = status

        return status, filtered_status

    async def _handle_detached_startup(
        self,
        status: dict[str, bool],
        filtered_status: dict[str, bool],
        ui_mode: UIMode,
        terminate_all: bool,
        services: list[str] | None,
    ) -> dict[str, bool]:
        """Handle startup in detached mode."""
        self.logger.debug("Detached mode: Starting services without waiting for health checks")
        success = await self.start_missing_services(
            status,  # Pass full status but with filtered services marked as already running
            ui_mode=ui_mode or UIMode.DEV,
            terminate_all=terminate_all,
            detach=True,
        )
        if not success:
            self.logger.error("Failed to start services in detached mode")
            raise RuntimeError("Service startup failed")

        # Give services time to initialize, then return
        # UI service needs extra time for docs + UI build steps in dev mode
        sleep_time = 30 if (services and constants.SERVICE_UI in services) else 12
        await asyncio.sleep(sleep_time)
        self.logger.info("Services started in detached mode. Health checks will complete in background.")
        return {k: not v for k, v in filtered_status.items()}

    async def _handle_normal_startup(
        self,
        status: dict[str, bool],
        filtered_status: dict[str, bool],
        ui_mode: UIMode,
        terminate_all: bool,
        services: list[str] | None,
    ) -> dict[str, bool]:
        """Handle startup in normal (non-detached) mode."""
        # Track which services were initially not running (these are the ones that will be "started")
        started_services: dict[str, bool] = {k: not v for k, v in filtered_status.items()}

        # Non-detached mode: Wait for all services to be fully ready
        while not all(filtered_status.values()):
            self.logger.debug(
                f"Some services are not running (status: {filtered_status}). Starting missing services...",
            )
            success = await self.start_missing_services(
                status,  # Pass full status but with filtered services marked as already running
                ui_mode=ui_mode or UIMode.DEV,
                terminate_all=terminate_all,
                detach=False,
            )
            if not success:
                self.logger.error("Failed to start all services, aborting startup")
                raise RuntimeError("Service startup failed")

            await asyncio.sleep(10)
            # Runtime monitoring check - use normal timeout thresholds (AWA-133 Phase 2.1)
            status = await self.check_all_services(ui_mode=ui_mode or UIMode.DEV, startup_mode=False)
            # Update filtered status for the next iteration
            if services is not None:
                filtered_status = {name: status[name] for name in services if name in status}
                # Set services not in requested list to True so they won't be started
                for service_name in status:
                    if service_name not in services:
                        status[service_name] = True
            else:
                filtered_status = status

        return started_services

    async def ensure_all_services_running(
        self,
        ui_mode: UIMode = UIMode.DEV,
        terminate_all: bool = False,
        detach: bool = False,
        services: list[str] | None = None,
    ) -> dict[str, bool]:
        """Ensure specified services (or all services) are running.

        Args:
            ui_mode: UI mode to use for service startup
            terminate_all: Whether to terminate all workflows when starting temporal
            detach: Whether to run services in detached mode
            services: Optional list of service names to start. If None, starts all services.

        Returns:
            Dictionary mapping service names to whether they were started by this call

        """
        # Handle pre-startup checks and cleanup
        current_status, requested_status = await self._handle_pre_startup_checks(
            ui_mode,
            terminate_all,
            detach,
            services,
        )

        # If pre-startup check returned empty status, all services are already healthy
        if not current_status:
            return requested_status

        # Prepare service status for startup
        status, filtered_status = await self._prepare_service_status(ui_mode, services)
        self.logger.debug(f"Service status: {filtered_status}")

        # Handle startup based on mode
        if detach:
            return await self._handle_detached_startup(status, filtered_status, ui_mode, terminate_all, services)
        return await self._handle_normal_startup(status, filtered_status, ui_mode, terminate_all, services)

    async def start_missing_services(
        self,
        status: dict,
        ui_mode: UIMode = UIMode.DEV,
        terminate_all: bool = False,
        detach: bool = False,
    ) -> bool:
        """Start missing services as subprocesses.

        Returns:
            True if all services started successfully, False if rollback is needed

        """
        started_services = []

        try:
            # Start Temporal Server first if needed
            if not status[constants.SERVICE_TEMPORAL_SERVER] and not self.service_startup_flags.get(
                constants.SERVICE_TEMPORAL_SERVER,
                False,
            ):
                server_command = self._get_package_aware_command("server")
                success = await self._start_service_subprocess(
                    constants.SERVICE_TEMPORAL_SERVER,
                    server_command,
                    port=EnvConfig.get_env_config().temporal_server_port,
                    detach=detach,
                )
                if success:
                    started_services.append(constants.SERVICE_TEMPORAL_SERVER)
                    self._set_service_startup_flag(constants.SERVICE_TEMPORAL_SERVER, started=True)
                else:
                    self.logger.error("Failed to start Temporal server")
                    await self.rollback_started_services(started_services)
                    return False

            # Start Temporal Worker if needed
            if not status[constants.SERVICE_TEMPORAL_WORKER] and not self.service_startup_flags.get(
                constants.SERVICE_TEMPORAL_WORKER,
                False,
            ):
                self._ensure_temporal_components_initialized()

                # Update client with terminate_all setting if needed
                if terminate_all and not self.temporal_client.terminate_all:
                    self.temporal_client = await TemporalClient.create(terminate_all=True)
                    self.temporal_worker = TemporalWorker(self.temporal_client)

                # Start worker as subprocess
                worker_command = self._get_package_aware_command("worker")
                success = await self._start_service_subprocess(
                    constants.SERVICE_TEMPORAL_WORKER,
                    worker_command,
                    port=None,  # Temporal worker doesn't have a port
                    detach=detach,
                )
                if success:
                    started_services.append(constants.SERVICE_TEMPORAL_WORKER)
                    self._set_service_startup_flag(constants.SERVICE_TEMPORAL_WORKER, started=True)
                else:
                    self.logger.error("Failed to start Temporal worker")
                    await self.rollback_started_services(started_services)
                    return False

            # Start API if needed
            if not status[constants.SERVICE_API] and not self.service_startup_flags.get(constants.SERVICE_API, False):
                api_command = self._get_api_command()
                success = await self._start_service_subprocess(
                    constants.SERVICE_API,
                    api_command,
                    port=EnvConfig.get_env_config().awa_api_port,
                    detach=detach,
                )
                if success:
                    started_services.append(constants.SERVICE_API)
                    self._set_service_startup_flag(constants.SERVICE_API, started=True)
                else:
                    self.logger.error("Failed to start API service")
                    await self.rollback_started_services(started_services)
                    return False

            # Start UI if needed
            if (
                not status[constants.SERVICE_UI]
                and ui_mode != UIMode.NONE
                and not self.service_startup_flags.get(constants.SERVICE_UI, False)
            ):
                ui_env_vars = {
                    "AWA_UI_HOST": EnvConfig.get_env_config().awa_ui_host,
                    "AWA_UI_PORT": str(EnvConfig.get_env_config().awa_ui_port),
                    "AWA_API_HOST": EnvConfig.get_env_config().awa_api_host,
                    "AWA_API_PORT": str(EnvConfig.get_env_config().awa_api_port),
                    "TEMPORAL_UI_HOST": EnvConfig.get_env_config().temporal_ui_host,
                    "TEMPORAL_UI_PORT": str(EnvConfig.get_env_config().temporal_ui_port),
                }

                ui_command = self._get_package_aware_command(f"ui --ui {ui_mode.value}")
                success = await self._start_service_subprocess(
                    constants.SERVICE_UI,
                    ui_command,
                    port=EnvConfig.get_env_config().awa_ui_port,
                    env_vars=ui_env_vars,
                    detach=detach,
                )
                if success:
                    started_services.append(constants.SERVICE_UI)
                    self._set_service_startup_flag(constants.SERVICE_UI, started=True)
                else:
                    self.logger.error("Failed to start UI service")
                    await self.rollback_started_services(started_services)
                    return False

            return True

        except Exception:
            self.logger.exception("Error during service startup")
            await self.rollback_started_services(started_services)
            return False

    async def rollback_started_services(self, started_services: list[str]) -> None:
        """Stop services that were started during a failed startup attempt.

        Args:
            started_services: List of service names that were successfully started

        """
        if not started_services:
            return
        self.logger.warning(f"Rolling back started services: {started_services}")
        for service_name in started_services:
            try:
                success = await self.state_manager.stop_service(service_name)
                if success:
                    self.logger.info(f"Successfully stopped {service_name} during rollback")
                    self.service_processes.pop(service_name, None)
                    # Reset service startup flag
                    self._set_service_startup_flag(service_name, started=False)
                    # Clean up associated subprocess transport BEFORE background tasks
                    await self.cleanup_subprocess_transports(service_name)
                    # Clean up associated background task
                    await self.cleanup_background_tasks(service_name)
                else:
                    self.logger.error(f"Failed to stop {service_name} during rollback")
            except Exception:
                self.logger.exception(f"Error stopping {service_name} during rollback")

    async def execute_workflow(
        self,
        workflow: str,
        workflow_input: str | None = None,
        task_queue: str | None = None,
    ) -> object:
        """Execute a workflow using the temporal client."""
        if self.temporal_client is None:
            raise RuntimeError("ServiceManager not properly initialized. Use ServiceManager.create()")

        try:
            return await self.temporal_client.execute_workflow(
                workflow=workflow,
                workflow_input=workflow_input,
                task_queue=task_queue,
            )
        except WorkflowExecutionError:
            # Log but don't crash the service
            self.logger.exception("Workflow execution failed")
            raise  # Re-raise to CLI but service continues running

    async def stop_services(self, stop_temporal: bool = False, stop_api: bool = False, stop_ui: bool = False) -> None:
        """Stop specified services using PID-based termination.

        Args:
            stop_temporal: Whether to stop temporal server and worker
            stop_api: Whether to stop API service
            stop_ui: Whether to stop UI service

        """
        stopped_services = []
        try:
            if stop_temporal:
                # Stop Temporal Worker
                if await self.state_manager.get_service_info(constants.SERVICE_TEMPORAL_WORKER):
                    success = await self.state_manager.stop_service(constants.SERVICE_TEMPORAL_WORKER)
                    if success:
                        stopped_services.append(constants.SERVICE_TEMPORAL_WORKER)
                    self.service_processes.pop(constants.SERVICE_TEMPORAL_WORKER, None)
                    await self.cleanup_subprocess_transports(constants.SERVICE_TEMPORAL_WORKER)
                    await self.cleanup_background_tasks(constants.SERVICE_TEMPORAL_WORKER)
                    self._set_service_startup_flag(constants.SERVICE_TEMPORAL_WORKER, started=False)
                # Stop Temporal Server
                if await self.state_manager.get_service_info(constants.SERVICE_TEMPORAL_SERVER):
                    success = await self.state_manager.stop_service(constants.SERVICE_TEMPORAL_SERVER)
                    if success:
                        stopped_services.append(constants.SERVICE_TEMPORAL_SERVER)
                    self.service_processes.pop(constants.SERVICE_TEMPORAL_SERVER, None)
                    await self.cleanup_subprocess_transports(constants.SERVICE_TEMPORAL_SERVER)
                    await self.cleanup_background_tasks(constants.SERVICE_TEMPORAL_SERVER)
                self._set_service_startup_flag(constants.SERVICE_TEMPORAL_SERVER, started=False)
            if stop_api and await self.state_manager.get_service_info(constants.SERVICE_API):
                success = await self.state_manager.stop_service(constants.SERVICE_API)
                if success:
                    stopped_services.append(constants.SERVICE_API)
                    self.service_processes.pop(constants.SERVICE_API, None)
                    await self.cleanup_subprocess_transports(constants.SERVICE_API)
                    await self.cleanup_background_tasks(constants.SERVICE_API)
                    self._set_service_startup_flag(constants.SERVICE_API, started=False)
            if stop_ui and await self.state_manager.get_service_info(constants.SERVICE_UI):
                success = await self.state_manager.stop_service(constants.SERVICE_UI)
                if success:
                    stopped_services.append(constants.SERVICE_UI)
                    self.service_processes.pop(constants.SERVICE_UI, None)
                    await self.cleanup_subprocess_transports(constants.SERVICE_UI)
                    await self.cleanup_background_tasks(constants.SERVICE_UI)
                    self._set_service_startup_flag(constants.SERVICE_UI, started=False)
            if stopped_services:
                self.logger.info(f"Successfully stopped services: {stopped_services}")
        except Exception:
            self.logger.exception("Error stopping services")

    async def stop_all_services(self) -> list[str]:
        """Stop all tracked services.

        Returns:
            List of service names that were stopped successfully

        """
        return await self.state_manager.stop_all_services()
