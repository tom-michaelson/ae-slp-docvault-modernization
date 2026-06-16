"""Service state management for tracking detached AWA services."""

import asyncio
import errno
import os
import re
import shutil
import signal
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from awa.core.cli import constants
from awa.core.engine.temporal_server import TemporalServer
from awa.core.logger.logger import LoggerComponent, get_logger
from awa.core.models.cli.service_state import ServiceInfo, ServiceState
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.command_utils import CommandUtils
from awa.core.utils.file_system_utils import FileSystemUtils
from awa.core.utils.platform_utils import PlatformUtils

# Constants for process management
ESRCH_ERRNO = errno.ESRCH  # No such process
POWERSHELL_CSV_MIN_PARTS = 2  # ProcessId, ParentProcessId


class StateManager:
    """Manages persistent state for detached AWA services.

    Handles creating, reading, updating and cleaning up state files that track
    running service process IDs and metadata for detached service management.
    """

    def __init__(self, state_dir: Path | None = None) -> None:
        """Initialize the StateManager.

        Args:
            state_dir: Directory to store state files. Defaults to local project directory (.awa_state/).

        """
        self.logger = get_logger(LoggerComponent.CLI)
        if state_dir:
            # Allow override for testing
            self.state_dir = state_dir
            self.state_file = self.state_dir / "services.json"
        else:
            # Use local project state directory (.awa_state/ in current working directory)
            self.state_dir = Path.cwd() / constants.LOCAL_STATE_DIR
            self.state_file = self.state_dir / constants.LOCAL_STATE_FILE

    async def _safe_subprocess_cleanup(self, proc: asyncio.subprocess.Process) -> None:
        """Safely clean up subprocess pipes to prevent Windows transport warnings.

        Args:
            proc: The subprocess to clean up

        """
        try:
            if proc.stdout and not proc.stdout.is_closing():
                proc.stdout.close()
            if proc.stderr and not proc.stderr.is_closing():
                proc.stderr.close()
            if proc.stdin and not proc.stdin.is_closing():
                proc.stdin.close()
        except (OSError, ValueError) as e:
            # Log cleanup errors for debugging
            self.logger.debug(f"Subprocess cleanup encountered issues: {e}")

    async def ensure_state_directory(self) -> None:
        """Ensure the state directory exists."""
        self.state_dir.mkdir(exist_ok=True)
        self.logger.debug(f"State directory ensured at: {self.state_dir}")

    async def save_state(self, state: ServiceState) -> None:
        """Save service state to the state file.

        Args:
            state: The service state to persist

        Raises:
            Exception: If file operations fail

        """
        try:
            await self.ensure_state_directory()
            state_json = state.model_dump_json(indent=2)
            await FileSystemUtils.write_async(str(self.state_file), state_json)
            self.logger.debug(f"Service state saved to: {self.state_file}")
        except Exception:
            self.logger.exception("Failed to save service state")
            raise

    async def load_state(self) -> ServiceState | None:
        """Load the current state from the state file.

        Returns:
            ServiceState if file exists and is valid, None otherwise

        """
        if not self.state_file.exists():
            self.logger.debug("State file does not exist")
            return None

        try:
            await self.ensure_state_directory()
            state_json = await FileSystemUtils.read_async(str(self.state_file))
            return ServiceState.model_validate_json(state_json)
        except Exception:
            self.logger.exception("Failed to load service state")
            return None

    async def update_service(self, service_name: str, service_info: ServiceInfo) -> None:
        """Update or add a service to the state.

        Args:
            service_name: Name of the service (from constants)
            service_info: Service information to store

        """
        state = await self.load_state() or ServiceState(timestamp=datetime.now(UTC))
        state.services[service_name] = service_info
        state.timestamp = datetime.now(UTC)
        await self.save_state(state)
        self.logger.debug(f"Updated service state for: {service_name}")

    async def remove_service(self, service_name: str) -> None:
        """Remove a service from the state.

        Args:
            service_name: Name of the service to remove

        """
        state = await self.load_state()
        if state and service_name in state.services:
            del state.services[service_name]
            state.timestamp = datetime.now(UTC)
            await self.save_state(state)
            self.logger.debug(f"Removed service from state: {service_name}")

    async def get_service_info(self, service_name: str) -> ServiceInfo | None:
        """Get information for a specific service.

        Args:
            service_name: Name of the service

        Returns:
            ServiceInfo if service exists in state, None otherwise

        """
        state = await self.load_state()
        return state.services.get(service_name) if state else None

    async def get_all_services(self) -> dict[str, ServiceInfo]:
        """Get information for all tracked services.

        Returns:
            Dictionary mapping service names to their information

        """
        state = await self.load_state()
        return state.services if state else {}

    async def cleanup_state(self) -> None:
        """Remove the state file and directory if empty.

        This should be called after successfully stopping all services.
        """
        try:
            if self.state_file.exists():
                await FileSystemUtils.remove_async(str(self.state_file))

            # Remove directory if it's empty
            if self.state_dir.exists() and not any(self.state_dir.iterdir()):
                self.state_dir.rmdir()
                self.logger.debug("Empty state directory removed")
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Failed to cleanup state: {e}")

    def is_process_running(self, pid: int) -> bool:
        """Check if a process with the given PID is still running.

        Uses platform-appropriate methods for process existence checking.

        Args:
            pid: Process ID to check

        Returns:
            True if process is running, False otherwise

        """
        try:
            if PlatformUtils.is_windows():
                return self._is_process_running_windows(pid)
            return self._is_process_running_unix(pid)
        except (OSError, ProcessLookupError) as e:
            self.logger.debug(f"Error checking process {pid}: {e}")
            return False

    def _is_process_running_windows(self, pid: int) -> bool:
        """Enhanced Windows process detection with multiple fallback methods for detached processes."""
        try:
            # Try multiple detection methods for detached processes
            methods = [
                self._try_os_kill_detection,
                self._try_tasklist_csv_detection,
                self._try_tasklist_detailed_detection,
            ]

            for method in methods:
                try:
                    if method(pid):
                        self.logger.debug(f"Process {pid} detected via {method.__name__}")
                        return True
                except (OSError, subprocess.TimeoutExpired, ValueError) as e:
                    self.logger.debug(f"Detection method {method.__name__} failed: {e}")
                    continue

            self.logger.debug(f"All detection methods failed for process {pid}")
            return False
        except (OSError, subprocess.TimeoutExpired, ValueError):
            return False

    def _try_os_kill_detection(self, pid: int) -> bool:
        """Primary detection method using os.kill."""
        os.kill(pid, 0)
        return True

    def _try_tasklist_csv_detection(self, pid: int) -> bool:
        """Enhanced tasklist with CSV format for reliable parsing of detached processes."""
        tasklist_path = shutil.which("tasklist")
        if not tasklist_path:
            return False

        proc = subprocess.run(  # noqa: S603
            [
                tasklist_path,
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",  # CSV format for reliable parsing
                "/NH",  # No headers
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=constants.COMMAND_TIMEOUT_STANDARD,
        )

        # CSV format: "ImageName","PID","SessionName","Session#","MemUsage"
        lines = [line.strip() for line in proc.stdout.strip().split("\n") if line.strip()]
        for line in lines:
            if f'"{pid}"' in line:  # Look for quoted PID in CSV
                self.logger.debug(f"CSV detection found process {pid}: {line}")
                return True

        self.logger.debug(f"CSV detection: no process {pid} found in output: {proc.stdout}")
        return False

    def _try_tasklist_detailed_detection(self, pid: int) -> bool:
        """Detailed tasklist with verbose output for edge cases with detached processes."""
        tasklist_path = shutil.which("tasklist")
        if not tasklist_path:
            return False

        proc = subprocess.run(  # noqa: S603
            [
                tasklist_path,
                "/FI",
                f"PID eq {pid}",
                "/V",  # Verbose output
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=constants.COMMAND_TIMEOUT_STANDARD,
        )

        # Look for PID in any format within the output
        pid_found = str(pid) in proc.stdout and "No tasks are running" not in proc.stdout
        self.logger.debug(f"Detailed detection for {pid}: {pid_found}, output: {proc.stdout[:100]}...")
        return pid_found

    def _is_process_running_unix(self, pid: int) -> bool:
        """Check if process exists on Unix."""
        try:
            # Use os.kill with signal 0 to check if process exists
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            # Process exists but we don't have permission
            return True
        except OSError:
            return False

    async def is_service_running(self, service_name: str, check_port: bool = True) -> bool:
        """Check if a service is still running.

        Args:
            service_name: Name of the service to check
            check_port: Whether to verify the service's port is accessible

        Returns:
            True if service is running, False otherwise

        """
        service_info = await self.get_service_info(service_name)
        if not service_info:
            return False

        # Check if process is still running
        if not self.is_process_running(service_info.pid):
            self.logger.debug(f"Process {service_info.pid} for {service_name} not running")
            await self.remove_service(service_name)
            return False

        # For services with ports, optionally verify port is still in use
        if check_port and service_info.port:
            # Use existing port checking logic from ServiceManager
            if service_name == constants.SERVICE_API:
                port_available = await CommandUtils.check_service_status(
                    EnvConfig.get_env_config().awa_api_host,
                    service_info.port,
                )
            elif service_name == constants.SERVICE_UI:
                port_available = await CommandUtils.check_service_status(
                    EnvConfig.get_env_config().awa_ui_host,
                    service_info.port,
                )
            elif service_name == constants.SERVICE_TEMPORAL_SERVER:
                temporal_server = TemporalServer()
                port_available = await temporal_server.check_service_status()
            else:
                port_available = True  # Unknown service, assume port check passes

            if not port_available:
                self.logger.warning(f"Port check failed for service {service_name}")
                await self.remove_service(service_name)
                return False

        return True

    async def stop_service(self, service_name: str) -> bool:
        """Stop a specific service using cross-platform process group termination.

        Args:
            service_name: Name of the service to stop

        Returns:
            True if service was stopped successfully, False otherwise

        """
        service_info = await self.get_service_info(service_name)
        if not service_info:
            self.logger.debug(f"Service {service_name} not found in state")
            return True

        try:
            if self.is_process_running(service_info.pid):
                # Platform-specific process group termination
                if PlatformUtils.is_windows():
                    await self._stop_service_windows(service_info.pid, service_name)
                else:
                    # Use enhanced Unix process tree termination
                    process_tree = await self._find_unix_process_tree(service_info.pid)
                    await self._stop_unix_process_tree(process_tree, service_name)

                # Wait for graceful shutdown with timeout (only check root process)
                await self._wait_for_process_termination(service_info.pid, service_name)

            await self.remove_service(service_name)
            self.logger.info(f"Successfully stopped {service_name}")
            return True

        except (TimeoutError, OSError, ProcessLookupError) as e:
            self.logger.warning(f"Error stopping {service_name}: {e}")
            await self.remove_service(service_name)
            return True

    async def stop_service_with_verification(self, service_name: str) -> bool:
        """Stop a service with enhanced verification - only removes from state after confirmed termination.

        This method implements the Phase 3.2 enhancement that ensures processes are fully terminated
        before state cleanup occurs. State cleanup only happens after verification succeeds.

        Args:
            service_name: Name of the service to stop

        Returns:
            True if service was stopped and verified, False if termination failed

        """
        service_info = await self.get_service_info(service_name)
        if not service_info:
            self.logger.debug(f"Service {service_name} not found in state - considering it stopped")
            return True

        original_pid = service_info.pid
        self.logger.debug(f"Starting verified stop for {service_name} (PID: {original_pid})")

        try:
            # Only proceed with termination if process is actually running
            if not self.is_process_running(original_pid):
                self.logger.debug(f"Process {original_pid} for {service_name} is already terminated")
                # Clean up state since process is already gone
                await self.remove_service(service_name)
                return True

            # Perform termination without state cleanup
            termination_success = await self._terminate_service_process_only(service_name, service_info)

            if not termination_success:
                self.logger.warning(f"Process termination failed for {service_name} - keeping service in state")
                return False

            # Verify termination was successful before cleaning up state
            verification_timeout = constants.VERIFICATION_TIMEOUT_EXTENDED  # Extended timeout for verification
            verification_success = await self._verify_process_termination_complete(
                original_pid,
                service_name,
                verification_timeout,
            )

            if verification_success:
                # Only remove from state after successful verification
                await self.remove_service(service_name)
                self.logger.debug(f"Successfully stopped and verified {service_name}")
                return True
            self.logger.warning(
                f"Process termination verification failed for {service_name} - service remains in state",
            )
            return False

        except Exception:
            self.logger.exception(f"Error during verified stop of {service_name}")
            # Don't remove from state if we encountered errors during the process
            return False

    async def _terminate_service_process_only(self, service_name: str, service_info: ServiceInfo) -> bool:
        """Terminate service processes without state cleanup.

        This method performs the actual process termination but does not remove the service
        from state. It's used by stop_service_with_verification to separate termination
        from state cleanup.

        Args:
            service_name: Name of the service to terminate
            service_info: Service information containing PID and other details

        Returns:
            True if termination was attempted successfully, False if termination failed

        """
        pid = service_info.pid

        try:
            self.logger.debug(f"Terminating processes for {service_name} (PID: {pid})")

            # Platform-specific process group termination
            if PlatformUtils.is_windows():
                await self._stop_service_windows(pid, service_name)
            else:
                # Use enhanced Unix process tree termination
                process_tree = await self._find_unix_process_tree(pid)
                await self._stop_unix_process_tree(process_tree, service_name)

            # Wait for graceful shutdown with timeout (only check root process)
            await self._wait_for_process_termination(pid, service_name)

            self.logger.debug(f"Process termination completed for {service_name}")
            return True

        except (TimeoutError, OSError, ProcessLookupError) as e:
            self.logger.warning(f"Process termination failed for {service_name}: {e}")
            return False

    async def stop_service_with_verification_aggressive(self, service_name: str) -> bool:
        """Stop an unhealthy service using aggressive termination methods.

        This method is designed for services that have valid PIDs but failed health checks.
        It uses more aggressive termination methods and shorter timeouts to avoid hanging
        on services that are already in a problematic state.

        Args:
            service_name: Name of the service to stop

        Returns:
            True if service was stopped, False if termination failed

        """
        service_info = await self.get_service_info(service_name)
        if not service_info:
            self.logger.debug(f"Service {service_name} not found in state - considering it stopped")
            return True

        original_pid = service_info.pid
        self.logger.debug(f"Starting aggressive stop for {service_name} (PID: {original_pid})")

        try:
            # Check if process is still running
            if not self.is_process_running(original_pid):
                self.logger.debug(f"Process {original_pid} for {service_name} is already terminated")
                await self.remove_service(service_name)
                return True

            # Skip graceful termination - go directly to force termination for unhealthy services
            self.logger.debug(f"Skipping graceful termination for unhealthy service {service_name}")

            if PlatformUtils.is_windows():
                await self._aggressive_windows_termination(original_pid, service_name)
            else:
                await self._aggressive_unix_termination(original_pid, service_name)

            # Use shorter verification timeout for aggressive termination
            verification_success = await self._verify_process_termination_complete(
                original_pid,
                service_name,
                verification_timeout=10.0,  # Much shorter timeout for unhealthy services
            )

            if verification_success:
                # Clean up state after successful verification
                await self.remove_service(service_name)
                self.logger.debug(f"Aggressive termination and cleanup successful for {service_name}")
                return True
            # Even if verification fails, remove from state for unhealthy services
            # since they were already problematic
            self.logger.debug(
                f"Verification failed for {service_name}, but removing from state anyway (was unhealthy)",
            )
            await self.remove_service(service_name)
            return True

        except (OSError, TimeoutError, ValueError) as e:
            self.logger.warning(f"Aggressive termination failed for {service_name}: {e}")
            # For unhealthy services, still remove from state even if termination fails
            try:
                await self.remove_service(service_name)
                self.logger.info(f"Removed {service_name} from state despite termination failure (was unhealthy)")
            except (OSError, ValueError) as removal_error:
                self.logger.debug(f"Failed to remove service {service_name} from state: {removal_error}")
            return False

    async def _verify_process_termination_complete(
        self,
        original_pid: int,
        service_name: str,
        verification_timeout: float = constants.VERIFICATION_TIMEOUT_DEFAULT,
    ) -> bool:
        """Verify that process termination is complete with comprehensive checks.

        This method performs multiple verification steps to ensure the service
        has been completely terminated before allowing state cleanup.

        Args:
            original_pid: Original process ID to verify termination
            service_name: Name of the service being verified
            verification_timeout: Maximum time to spend on verification

        Returns:
            True if termination is completely verified, False otherwise

        """
        self.logger.debug(f"Starting comprehensive termination verification for {service_name} (PID: {original_pid})")

        try:
            async with asyncio.timeout(verification_timeout):
                # Verification Step 1: Check original process is gone
                if self.is_process_running(original_pid):
                    self.logger.debug(f"Original process {original_pid} for {service_name} is still running")
                    return False

                # Verification Step 2: Multi-attempt verification with backoff
                # Sometimes processes take a moment to fully clean up
                max_attempts = constants.MAX_VERIFICATION_ATTEMPTS
                backoff_delay = constants.VERIFICATION_BACKOFF_INITIAL

                for attempt in range(max_attempts):
                    await asyncio.sleep(backoff_delay)

                    # Re-check process existence
                    if self.is_process_running(original_pid):
                        self.logger.debug(f"Verification attempt {attempt + 1}: process {original_pid} still exists")
                        if attempt < max_attempts - 1:
                            backoff_delay *= constants.VERIFICATION_BACKOFF_MULTIPLIER  # Exponential backoff
                            continue
                        self.logger.warning(
                            f"Process {original_pid} still exists after {max_attempts} verification attempts",
                        )
                        return False

                    # Process is confirmed gone
                    break

                # Verification Step 3: Platform-specific additional checks
                additional_verification = await self._additional_termination_verification(original_pid, service_name)
                if not additional_verification:
                    return False

                self.logger.debug(f"Comprehensive termination verification successful for {service_name}")
                return True

        except TimeoutError:
            self.logger.warning(f"Termination verification timed out for {service_name}")
            return False
        except (OSError, ValueError, RuntimeError) as e:
            self.logger.warning(f"Termination verification error for {service_name}: {e}")
            return False

    async def _additional_termination_verification(self, pid: int, service_name: str) -> bool:
        """Perform additional platform-specific termination verification.

        Args:
            pid: Process ID to verify
            service_name: Name of the service

        Returns:
            True if additional verification passes, False otherwise

        """
        try:
            if PlatformUtils.is_windows():
                # On Windows, use tasklist to double-check process doesn't exist
                return await self._windows_final_process_verification(pid)
            # On Unix, check for zombie processes and process group cleanup
            return await self._unix_final_process_verification(pid, service_name)

        except (OSError, ValueError, RuntimeError) as e:
            self.logger.debug(f"Additional verification failed for {service_name}: {e}")
            return True  # Don't fail verification due to additional check errors

    async def _windows_final_process_verification(self, pid: int) -> bool:
        """Perform final Windows-specific process verification."""
        try:
            # Use tasklist to verify process doesn't exist
            proc = await asyncio.create_subprocess_exec(
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_STANDARD)

            # If tasklist returns successfully but no processes found, process is gone
            output = stdout.decode().strip()
            process_exists = output and f'"{pid}"' in output and "No tasks" not in output

            self.logger.debug(f"Windows final verification for PID {pid}: process_exists={process_exists}")

            # Ensure subprocess is cleaned up
            if proc.returncode is None:
                proc.terminate()
                await proc.wait()

            return not process_exists

        except (TimeoutError, OSError):
            self.logger.debug(f"Windows final verification failed for PID {pid} - assuming terminated")
            return True  # Assume process is terminated if verification fails

    async def _unix_final_process_verification(self, pid: int, _service_name: str) -> bool:
        """Perform final Unix-specific process verification."""
        try:
            # Check for zombie processes
            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-p",
                str(pid),
                "-o",
                "pid,stat,comm",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_STANDARD)

            try:
                if proc.returncode == 0:
                    # Process still exists - check if it's a zombie
                    output = stdout.decode()
                    lines = output.strip().split("\n")
                    if len(lines) > 1:  # Skip header
                        process_line = lines[1]
                        if "<defunct>" in process_line or "Z" in process_line:
                            self.logger.debug(f"Process {pid} exists as zombie - considering terminated")
                            return True
                        self.logger.warning(f"Process {pid} still active in Unix verification")
                        return False

                # Process doesn't exist according to ps
                self.logger.debug(f"Unix final verification confirmed PID {pid} is terminated")
                return True
            finally:
                # Ensure subprocess is cleaned up
                if proc.returncode is None:
                    proc.terminate()
                    await proc.wait()

        except (TimeoutError, OSError):
            self.logger.debug(f"Unix final verification failed for PID {pid} - assuming terminated")
            return True  # Assume process is terminated if verification fails

    async def _stop_service_windows(self, pid: int, service_name: str) -> None:
        """Enhanced Windows process tree termination with comprehensive discovery and cleanup."""
        try:
            # Phase 1: Discover complete Windows process tree
            process_tree = await self._find_windows_process_tree(pid, service_name)

            # Phase 2: Attempt graduated termination (graceful first, then force)
            remaining_processes = await self._terminate_windows_processes_graduated(process_tree, service_name)

            # Phase 3: Verify successful termination
            await self._verify_windows_termination(remaining_processes, service_name)

        except (TimeoutError, OSError):
            self.logger.exception(f"Enhanced Windows process termination failed for {service_name}")

    async def _aggressive_windows_termination(self, pid: int, service_name: str) -> None:
        """Aggressive Windows process termination for unhealthy services.

        Skips graceful termination and goes directly to force termination with shorter timeouts.
        """
        try:
            self.logger.debug(f"Starting aggressive Windows termination for {service_name} (PID: {pid})")

            # For aggressive termination, use simpler process discovery to avoid hangs
            process_tree = await self._find_windows_process_tree_aggressive(pid, service_name)

            # Skip graceful termination - go directly to force termination
            await self._force_terminate_windows_processes(process_tree, service_name)

            # Use shorter verification with aggressive termination
            await self._verify_windows_termination_aggressive(process_tree, service_name)

        except (TimeoutError, OSError) as e:
            self.logger.warning(f"Aggressive Windows termination failed for {service_name}: {e}")

    async def _aggressive_unix_termination(self, pid: int, service_name: str) -> None:
        """Aggressive Unix process termination for unhealthy services."""
        try:
            self.logger.debug(f"Starting aggressive Unix termination for {service_name} (PID: {pid})")

            # Find process tree
            process_tree = await self._find_unix_process_tree(pid)

            # Skip SIGTERM - go directly to SIGKILL for unhealthy services
            for tree_pid in process_tree:
                try:
                    if self.is_process_running(tree_pid):
                        os.kill(tree_pid, signal.SIGKILL)
                        self.logger.debug(f"Sent SIGKILL to PID {tree_pid}")
                except ProcessLookupError:
                    # Process already terminated
                    pass

            # Brief wait for termination
            await asyncio.sleep(1.0)

        except (OSError, ProcessLookupError, TimeoutError) as e:
            self.logger.warning(f"Aggressive Unix termination failed for {service_name}: {e}")

    async def _find_windows_process_tree(self, root_pid: int, service_name: str) -> list[int]:
        """Enhanced Windows process tree discovery using multiple methods."""
        all_processes = {root_pid}

        try:
            # Method 1: Use PowerShell for comprehensive process tree discovery
            powershell_processes = await self._discover_windows_tree_powershell_cim(root_pid)
            all_processes.update(powershell_processes)

            # Method 2: Use tasklist with filtering (skip if hangs - known Windows issue)
            try:
                # Add shorter timeout for tasklist to prevent hangs
                tasklist_processes = await asyncio.wait_for(
                    self._discover_windows_tree_tasklist(root_pid, service_name),
                    timeout=5.0,  # Short timeout to prevent hanging
                )
                all_processes.update(tasklist_processes)
            except (TimeoutError, OSError, subprocess.SubprocessError) as e:
                self.logger.debug(f"Tasklist discovery skipped (timeout/error): {e}")
                # Continue without tasklist - PowerShell methods are usually sufficient

            # Method 3: PowerShell-based discovery (fallback)
            if len(all_processes) == 1:  # Only root process found, try PowerShell
                powershell_processes = await self._discover_windows_tree_powershell(root_pid)
                all_processes.update(powershell_processes)

            # Filter out non-existent processes and log findings
            verified_processes = []
            for pid in all_processes:
                if await self._is_windows_process_running(pid):
                    verified_processes.append(pid)
                else:
                    self.logger.debug(f"Process {pid} no longer running, excluding from tree")

            self.logger.debug(
                f"Windows process tree discovery for {root_pid} ({service_name}): "
                f"found {len(verified_processes)} processes",
            )

            return verified_processes

        except (TimeoutError, OSError, ValueError) as e:
            self.logger.warning(f"Windows process tree discovery failed for {root_pid}: {e}")
            return [root_pid]

    async def _discover_windows_tree_powershell_cim(self, root_pid: int) -> list[int]:
        """Discover process tree using PowerShell (WMIC replacement)."""
        try:
            # Use PowerShell Get-CimInstance to get process parent-child relationships
            powershell_script = (
                "Get-CimInstance -ClassName Win32_Process | "
                "Select-Object ProcessId,ParentProcessId | "
                "ConvertTo-Csv -NoTypeInformation"
            )
            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                powershell_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_LONG)

            # Ensure subprocess is cleaned up
            if proc.returncode is None:
                proc.terminate()
                await proc.wait()

            if proc.returncode != 0:
                self.logger.debug("PowerShell process discovery failed with non-zero exit code")
                return []

            # Parse PowerShell CSV output
            processes = {}
            lines = stdout.decode().strip().split("\n")

            for line in lines[1:]:  # Skip header line
                if not line.strip():
                    continue

                # PowerShell CSV format: "ProcessId","ParentProcessId"
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) >= POWERSHELL_CSV_MIN_PARTS:
                    try:
                        pid = int(parts[0].strip('"')) if parts[0] else 0
                        ppid = int(parts[1]) if parts[1] else 0
                        if pid > 0:
                            processes[pid] = ppid
                    except (ValueError, IndexError):
                        continue

            # Build process tree
            process_tree = [root_pid]
            to_check = [root_pid]

            while to_check:
                parent = to_check.pop(0)
                for pid, ppid in processes.items():
                    if ppid == parent and pid not in process_tree:
                        process_tree.append(pid)
                        to_check.append(pid)

            self.logger.debug(f"PowerShell discovered {len(process_tree)} processes in tree")
            return process_tree[1:]  # Exclude root_pid as it's already included

        except (TimeoutError, OSError) as e:
            self.logger.debug(f"PowerShell process tree discovery failed: {e}")
            # Ensure subprocess cleanup on error to prevent transport warnings
            if "proc" in locals():
                await self._safe_subprocess_cleanup(proc)
            return []

    async def _discover_windows_tree_tasklist(self, root_pid: int, _service_name: str) -> list[int]:
        """Discover related processes using enhanced tasklist filtering."""
        try:
            # Get detailed process information
            proc = await asyncio.create_subprocess_exec(
                "tasklist",
                "/FO",
                "CSV",
                "/V",  # Verbose mode for command line info
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_EXTENDED)

            # Clean up subprocess to prevent Windows transport cleanup warnings
            # Note: StreamReader objects don't have close() method
            # The process cleanup is handled by wait() or communicate()
            try:
                if proc.stdin:
                    proc.stdin.close()
            except (OSError, ValueError) as e:
                # Log any issues closing stdin for debugging
                self.logger.debug(f"Stdin cleanup encountered issues: {e}")

            if proc.returncode != 0:
                self.logger.debug(f"Enhanced tasklist failed: {stderr.decode()}")
                return []

            related_pids = []
            lines = stdout.decode().strip().split("\n")

            # AWA-specific process patterns for Windows
            awa_patterns = [
                r"node\.exe.*(?:astro|vite|dev)",
                r"python\.exe.*awa",
                r"uvicorn\.exe.*awa",
                r"pnpm\.cmd",
                r"npm\.cmd",
                r"temporal.*worker",
            ]

            for line in lines:
                if not line.strip() or "Image Name" in line:
                    continue

                # Parse CSV line (basic parsing - not full CSV parser)
                parts = [p.strip('"') for p in line.split('","')]
                if len(parts) < constants.MIN_TASKLIST_CSV_PARTS:
                    continue

                try:
                    image_name = parts[0].strip('"')
                    pid_str = parts[1]

                    if not pid_str.isdigit():
                        continue

                    pid = int(pid_str)
                    if pid == root_pid:
                        continue

                    # Check if process matches AWA patterns
                    command_line = " ".join(parts) if len(parts) > constants.MAX_TASKLIST_CSV_PARTS else image_name

                    for pattern in awa_patterns:
                        if re.search(pattern, command_line, re.IGNORECASE):
                            related_pids.append(pid)
                            self.logger.debug(f"Tasklist found related process {pid}: {image_name}")
                            break

                except (ValueError, IndexError):
                    continue

            return related_pids

        except (TimeoutError, OSError) as e:
            self.logger.debug(f"Enhanced tasklist discovery failed: {e}")
            return []

    async def _discover_windows_tree_powershell(self, root_pid: int) -> list[int]:
        """PowerShell-based process tree discovery as fallback method."""
        try:
            # PowerShell command to get process tree
            ps_command = f"""
            $processes = Get-WmiObject Win32_Process
            $tree = @()
            $queue = @({root_pid})

            while ($queue.Count -gt 0) {{
                $current = $queue[0]
                $queue = $queue[1..($queue.Count-1)]
                $children = $processes | Where-Object {{ $_.ParentProcessId -eq $current }}
                foreach ($child in $children) {{
                    if ($tree -notcontains $child.ProcessId) {{
                        $tree += $child.ProcessId
                        $queue += $child.ProcessId
                    }}
                }}
            }}

            $tree | ForEach-Object {{ Write-Output $_ }}
            """

            proc = await asyncio.create_subprocess_exec(
                "powershell",
                "-Command",
                ps_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_LONG)

            # Clean up subprocess to prevent Windows transport cleanup warnings
            # Note: StreamReader objects don't have close() method
            # The process cleanup is handled by wait() or communicate()
            try:
                if proc.stdin:
                    proc.stdin.close()
            except (OSError, ValueError) as e:
                # Log any issues closing stdin for debugging
                self.logger.debug(f"Stdin cleanup encountered issues: {e}")

            if proc.returncode != 0:
                self.logger.debug(f"PowerShell process discovery failed: {stderr.decode()}")
                return []

            powershell_pids = []
            for line in stdout.decode().strip().split("\n"):
                ps_line = line.strip()
                if ps_line and ps_line.isdigit():
                    pid = int(ps_line)
                    if pid != root_pid:
                        powershell_pids.append(pid)

            self.logger.debug(f"PowerShell discovered {len(powershell_pids)} child processes")
            return powershell_pids

        except (TimeoutError, OSError) as e:
            self.logger.debug(f"PowerShell process tree discovery failed: {e}")
            return []

    async def _is_windows_process_running(self, pid: int) -> bool:
        """Enhanced Windows process existence check."""
        try:
            # Use tasklist with specific PID for accurate detection
            proc = await asyncio.create_subprocess_exec(
                "tasklist",
                "/FI",
                f"PID eq {pid}",
                "/FO",
                "CSV",
                "/NH",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_SHORT)

            if proc.returncode != 0:
                return False

            # Check if output contains the PID (process exists)
            output = stdout.decode().strip()
            return output and f'"{pid}"' in output and "No tasks" not in output

        except (TimeoutError, OSError):
            return False

    async def _terminate_windows_processes_graduated(self, pids: list[int], service_name: str) -> list[int]:
        """Graduated termination approach for Windows processes."""
        if not pids:
            return []

        self.logger.debug(f"Starting graduated Windows termination for {service_name}: {len(pids)} processes")

        # Phase 1: Attempt graceful termination (limited effectiveness on Windows)
        graceful_survivors = await self._attempt_windows_graceful_termination(pids, service_name)

        # Phase 2: Force termination of remaining processes
        force_survivors = await self._force_terminate_windows_processes(graceful_survivors, service_name)

        return force_survivors

    async def _attempt_windows_graceful_termination(self, pids: list[int], _service_name: str) -> list[int]:
        """Attempt graceful termination on Windows (limited effectiveness)."""
        # On Windows, graceful termination is often not effective for nested processes
        # But we'll attempt it for completeness
        graceful_pids = []

        for pid in pids:
            try:
                # Attempt graceful termination without /F flag
                proc = await asyncio.create_subprocess_exec(
                    "taskkill",
                    "/PID",
                    str(pid),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)

                if proc.returncode == 0:
                    self.logger.debug(f"Graceful termination sent to Windows process {pid}")
                    graceful_pids.append(pid)
                else:
                    self.logger.debug(f"Graceful termination failed for {pid}: {stderr.decode()}")

            except (TimeoutError, OSError) as e:
                self.logger.debug(f"Graceful termination error for {pid}: {e}")
                # Ensure subprocess cleanup on error to prevent transport warnings
                if "proc" in locals():
                    await self._safe_subprocess_cleanup(proc)

        if graceful_pids:
            # Wait briefly for graceful termination to take effect
            await asyncio.sleep(constants.PROCESS_GROUP_TERMINATION_DELAY)

            # Check which processes are still running using list comprehension
            survivors = [pid for pid in graceful_pids if await self._is_windows_process_running(pid)]

            # Include processes that weren't gracefully terminated
            survivors.extend([pid for pid in pids if pid not in graceful_pids])

            self.logger.debug(f"After graceful termination: {len(survivors)} processes remain")
            return survivors

        return pids

    async def _force_terminate_windows_processes(self, pids: list[int], service_name: str) -> list[int]:
        """Force terminate Windows processes using taskkill /F."""
        if not pids:
            return []

        force_survivors = []

        # Terminate individual processes with force
        for pid in pids:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "taskkill",
                    "/F",  # Force termination
                    "/T",  # Terminate process tree
                    "/PID",
                    str(pid),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_LONG)

                if proc.returncode == 0:
                    self.logger.debug(f"Force terminated Windows process tree for {pid} ({service_name})")
                else:
                    self.logger.debug(f"Force termination failed for {pid}: {stderr.decode()}")
                    if await self._is_windows_process_running(pid):
                        force_survivors.append(pid)

            except (TimeoutError, OSError):
                self.logger.exception(f"Force termination error for {pid}")
                # Ensure subprocess cleanup on error to prevent transport warnings
                if "proc" in locals():
                    await self._safe_subprocess_cleanup(proc)
                if await self._is_windows_process_running(pid):
                    force_survivors.append(pid)

        return force_survivors

    async def _verify_windows_termination(self, remaining_pids: list[int], service_name: str) -> None:
        """Verify Windows process termination with detailed reporting."""
        if not remaining_pids:
            self.logger.debug(f"Windows process termination successful for {service_name}")
            return

        # Final verification
        final_survivors = []
        final_survivors = [pid for pid in remaining_pids if await self._is_windows_process_running(pid)]

        if final_survivors:
            self.logger.error(
                f"Windows process termination incomplete for {service_name}: "
                f"{len(final_survivors)} processes remain: {final_survivors}. "
                f"Manual cleanup may be required.",
            )
        else:
            self.logger.info(f"Windows process termination eventually successful for {service_name}")

    async def _verify_windows_termination_aggressive(self, pids: list[int], service_name: str) -> None:
        """Fast verification for aggressive Windows termination.

        Uses shorter timeouts and less detailed checks for unhealthy services.
        """
        if not pids:
            self.logger.info(f"Aggressive Windows termination completed for {service_name}")
            return

        # Quick verification with shorter timeout
        await asyncio.sleep(2.0)  # Much shorter wait time

        survivors = [pid for pid in pids if await self._is_windows_process_running(pid)]

        if survivors:
            self.logger.warning(
                f"Aggressive termination incomplete for {service_name}: "
                f"{len(survivors)} processes remain, but proceeding anyway (service was unhealthy)",
            )
        else:
            self.logger.info(f"Aggressive Windows termination successful for {service_name}")

    async def _find_windows_process_tree_aggressive(self, root_pid: int, service_name: str) -> list[int]:
        """Simplified Windows process tree discovery for aggressive termination.

        Uses direct approach to avoid PowerShell hangs on unhealthy processes.
        """
        try:
            self.logger.debug(f"Starting aggressive process discovery for {root_pid} ({service_name})")

            # For aggressive termination, just return the root PID to avoid hangs
            # This is sufficient for most cases since unhealthy services are often single processes
            if self.is_process_running(root_pid):
                self.logger.debug(f"Aggressive discovery: using root PID {root_pid} only for {service_name}")
                return [root_pid]
            self.logger.debug(f"Root PID {root_pid} not running, skipping process tree discovery")
            return []

        except (OSError, ValueError, subprocess.SubprocessError) as e:
            self.logger.warning(f"Aggressive process tree discovery failed for {root_pid}: {e}")
            return [root_pid] if self.is_process_running(root_pid) else []

    async def _find_unix_process_tree(self, root_pid: int) -> list[int]:
        """Enhanced process tree discovery with improved recursive mechanisms and error handling.

        This method uses multiple strategies to discover all child processes:
        1. Direct parent-child relationships via ps command
        2. Deep recursive traversal with cycle detection
        3. Process group discovery for wrapper processes
        4. Pattern-based discovery for orphaned processes
        """
        try:
            # Strategy 1: Get comprehensive process information
            processes = await self._get_process_information()
            if not processes:
                self.logger.warning(f"No process information available, returning root process {root_pid}")
                return [root_pid]

            # Strategy 2: Build complete process tree with enhanced traversal
            process_tree = await self._build_process_tree_recursive(root_pid, processes)

            # Strategy 3: Find processes in same process group
            process_group_pids = await self._find_process_group_members(root_pid)

            # Strategy 4: Find related processes by pattern (orphaned processes)
            pattern_pids = await self._find_related_processes_by_pattern(root_pid)

            # Combine all discovered PIDs, removing duplicates
            all_pids = list(set(process_tree + process_group_pids + pattern_pids))

            # Verify all PIDs are still running and log detailed information
            verified_pids = []
            for pid in all_pids:
                if self.is_process_running(pid):
                    verified_pids.append(pid)
                    process_info = processes.get(pid, {})
                    self.logger.debug(
                        f"Verified process {pid}: "
                        f"cmd={process_info.get('comm', 'unknown')}, "
                        f"ppid={process_info.get('ppid', 'unknown')}",
                    )
                else:
                    self.logger.debug(f"Process {pid} no longer running, excluding from tree")

            self.logger.debug(
                f"Enhanced process tree discovery for {root_pid}: "
                f"found {len(verified_pids)} processes "
                f"(tree: {len(process_tree)}, group: {len(process_group_pids)}, "
                f"pattern: {len(pattern_pids)})",
            )

            return verified_pids if verified_pids else [root_pid]

        except (TimeoutError, OSError):
            self.logger.exception(f"Enhanced process tree discovery failed for {root_pid}")
            return [root_pid]

    async def _get_process_information(self) -> dict[int, dict[str, str]]:
        """Get comprehensive process information with enhanced error handling."""
        try:
            # Try platform-specific ps command first
            import platform

            system = platform.system().lower()

            if system == "darwin":  # macOS
                # macOS doesn't support 'sid' field
                ps_fields = "pid,ppid,pgid,comm,args"
                min_fields = constants.MIN_PS_OUTPUT_FIELDS - 1  # No sid field
                sid_index = None
            else:  # Linux and others
                ps_fields = "pid,ppid,pgid,sid,comm,args"
                min_fields = constants.MIN_PS_OUTPUT_FIELDS
                sid_index = 3

            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-axo",
                ps_fields,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_EXTENDED)

            if proc.returncode != 0:
                self.logger.debug(f"Enhanced ps command failed: {stderr.decode().strip()}")
                # Fallback to basic ps command
                return await self._get_basic_process_information()

            # Parse enhanced ps output
            processes = {}
            lines = stdout.decode().strip().split("\n")

            for i, line in enumerate(lines):
                if i == 0:  # Skip header
                    continue

                if not line.strip():
                    continue

                parts = line.strip().split(None, 5 if sid_index else 4)
                if len(parts) < min_fields:
                    continue

                try:
                    pid = int(parts[0])
                    ppid = int(parts[1])
                    pgid = int(parts[2])

                    if sid_index is not None:
                        sid = int(parts[3])
                        comm = parts[4]
                        args = (
                            parts[constants.PS_ARGS_FIELD_INDEX] if len(parts) > constants.PS_ARGS_FIELD_INDEX else comm
                        )
                    else:
                        sid = pgid  # Use pgid as fallback for sid on macOS
                        comm = parts[3]
                        args = (
                            parts[constants.PS_ARGS_FIELD_INDEX_MACOS]
                            if len(parts) > constants.PS_ARGS_FIELD_INDEX_MACOS
                            else comm
                        )

                    processes[pid] = {
                        "ppid": ppid,
                        "pgid": pgid,
                        "sid": sid,
                        "comm": comm,
                        "args": args,
                    }
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"Failed to parse ps line '{line}': {e}")
                    continue

            self.logger.debug(f"Enhanced ps discovered {len(processes)} processes")
            return processes

        except (TimeoutError, OSError) as e:
            self.logger.debug(f"Enhanced process information gathering failed: {e}")
            return await self._get_basic_process_information()

    async def _get_basic_process_information(self) -> dict[int, dict[str, str]]:
        """Fallback method for basic process information."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-axo",
                "pid,ppid,comm",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_LONG)

            if proc.returncode != 0:
                self.logger.error(f"Basic ps command failed: {stderr.decode()}")
                return {}

            processes = {}
            lines = stdout.decode().strip().split("\n")

            for i, line in enumerate(lines):
                if i == 0:  # Skip header
                    continue

                if not line.strip():
                    continue

                parts = line.strip().split(None, 2)
                if len(parts) < constants.MIN_PS_BASIC_FIELDS:
                    continue

                try:
                    pid = int(parts[0])
                    ppid = int(parts[1])
                    comm = (
                        parts[constants.PS_COMM_FIELD_INDEX]
                        if len(parts) > constants.PS_COMM_FIELD_INDEX
                        else "unknown"
                    )

                    processes[pid] = {
                        "ppid": ppid,
                        "comm": comm,
                    }
                except (ValueError, IndexError):
                    continue

            return processes

        except (TimeoutError, OSError):
            self.logger.exception("Basic process information gathering failed")
            return {}

    async def _build_process_tree_recursive(self, root_pid: int, processes: dict[int, dict[str, str]]) -> list[int]:
        """Build process tree with enhanced recursive traversal and cycle detection."""
        process_tree = [root_pid]
        visited = {root_pid}  # Cycle detection
        to_check = [root_pid]
        max_depth = constants.MAX_PROCESS_TREE_DEPTH  # Prevent infinite recursion
        current_depth = 0

        while to_check and current_depth < max_depth:
            current_level = list(to_check)
            to_check.clear()
            current_depth += 1

            for parent_pid in current_level:
                # Find all direct children of this parent
                children = []
                for pid, info in processes.items():
                    if info.get("ppid") == parent_pid and pid not in visited:
                        children.append(pid)

                # Add children to tree and queue for further processing
                for child_pid in children:
                    if child_pid not in visited:  # Additional cycle protection
                        process_tree.append(child_pid)
                        visited.add(child_pid)
                        to_check.append(child_pid)

        if current_depth >= max_depth:
            self.logger.warning(f"Process tree traversal reached maximum depth {max_depth} for {root_pid}")

        return process_tree

    async def _find_process_group_members(self, root_pid: int) -> list[int]:
        """Find processes in the same process group as the root process."""
        try:
            # Get process group ID for root process
            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-p",
                str(root_pid),
                "-o",
                "pgid=",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)

            if proc.returncode != 0:
                self.logger.debug(f"Could not get process group for {root_pid}: {stderr.decode()}")
                return []

            try:
                pgid = int(stdout.decode().strip())
            except ValueError:
                self.logger.debug(f"Invalid process group ID for {root_pid}: {stdout.decode()}")
                return []

            # Find all processes in the same process group
            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-g",
                str(pgid),
                "-o",
                "pid=",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=5)

            if proc.returncode != 0:
                self.logger.debug(f"Could not get process group members for {pgid}: {stderr.decode()}")
                return []

            group_pids = []
            for raw_line in stdout.decode().strip().split("\n"):
                line = raw_line.strip()
                if line:
                    try:
                        pid = int(line)
                        if pid != root_pid:  # Don't include root process again
                            group_pids.append(pid)
                    except ValueError:
                        continue

            if group_pids:
                self.logger.debug(
                    f"Found {len(group_pids)} process group members for {root_pid} (pgid={pgid}): {group_pids}",
                )

            return group_pids

        except (TimeoutError, OSError) as e:
            self.logger.debug(f"Process group discovery failed for {root_pid}: {e}")
            return []

    async def _find_related_processes_by_pattern(self, root_pid: int) -> list[int]:
        """Find related processes using pattern matching for orphaned processes."""
        try:
            # Get detailed process information with macOS-compatible options
            proc = await asyncio.create_subprocess_exec(
                "ps",
                "-axo",
                "pid,ppid,comm,args",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_LONG)

            if proc.returncode != 0:
                self.logger.warning(f"ps command failed for pattern matching: {stderr.decode()}")
                return []

            related_pids = []

            # Patterns that indicate related AWA processes
            awa_patterns = [
                r"node.*(?:astro|vite|dev)",  # Node.js dev servers
                r"pnpm.*(?:dev|start|run)",  # pnpm commands
                r"npm.*(?:dev|start|run)",  # npm commands
                r"uvicorn.*awa",  # AWA API servers
                r"python.*awa",  # AWA Python processes
                r"temporal.*worker",  # Temporal workers
            ]

            for line in stdout.decode().strip().split("\n"):
                if not line.strip():
                    continue

                parts = line.strip().split(None, constants.MIN_PS_PARTS_FOR_ARGS)
                if len(parts) < constants.MIN_PS_PARTS_FOR_ARGS:
                    continue

                try:
                    pid = int(parts[0])
                    ppid = int(parts[1])
                    comm = parts[2]
                    args = (
                        parts[constants.MIN_PS_PARTS_FOR_ARGS] if len(parts) > constants.MIN_PS_PARTS_FOR_ARGS else ""
                    )

                    # Skip the root process itself
                    if pid == root_pid:
                        continue

                    # Look for processes that match AWA patterns
                    full_command = f"{comm} {args}"
                    for pattern in awa_patterns:
                        if re.search(pattern, full_command, re.IGNORECASE) and ppid in (1, root_pid):
                            related_pids.append(pid)
                            self.logger.debug(f"Found related process by pattern {pattern}: {pid} ({full_command})")
                            break

                except (ValueError, IndexError):
                    continue

            return related_pids

        except (TimeoutError, OSError) as e:
            self.logger.warning(f"Error finding related processes by pattern: {e}")
            return []

    async def _stop_unix_process_tree(self, pids: list[int], service_name: str) -> None:
        """Enhanced process tree termination with process group management and graduated approach.

        This method implements a comprehensive termination strategy:
        1. Process group termination (when available)
        2. Graduated SIGTERM → SIGKILL with proper timeouts
        3. Individual process termination as fallback
        4. Comprehensive verification of successful termination
        """
        if not pids:
            self.logger.debug(f"No processes to terminate for {service_name}")
            return

        self.logger.debug(f"Starting enhanced termination of process tree for {service_name}: {pids}")

        # Phase 1: Attempt process group termination first
        process_groups_terminated = await self._attempt_process_group_termination(pids, service_name)

        # Phase 2: Individual process termination with graduated approach
        remaining_pids = await self._terminate_individual_processes(pids, service_name, process_groups_terminated)

        # Phase 3: Verify successful termination
        await self._verify_process_termination(remaining_pids, service_name)

    async def _attempt_process_group_termination(self, pids: list[int], service_name: str) -> set[int]:
        """Attempt to terminate processes via process groups for cleaner shutdown."""
        terminated_via_group = set()

        for pid in pids:
            try:
                # Get process group information
                proc = await asyncio.create_subprocess_exec(
                    "ps",
                    "-p",
                    str(pid),
                    "-o",
                    "pgid=",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=constants.COMMAND_TIMEOUT_SHORT)

                if proc.returncode != 0:
                    continue

                try:
                    pgid = int(stdout.decode().strip())
                except ValueError:
                    continue

                # Only terminate process group if we're the group leader or it's safe
                if pgid == pid or pgid > constants.MIN_SAFE_PROCESS_GROUP:  # Avoid terminating system process groups
                    try:
                        os.killpg(pgid, signal.SIGTERM)
                        terminated_via_group.add(pid)
                        self.logger.debug(f"Sent SIGTERM to process group {pgid} for process {pid} ({service_name})")
                    except (OSError, ProcessLookupError) as e:
                        self.logger.debug(f"Process group termination failed for {pid} (pgid={pgid}): {e}")
                        continue

            except (TimeoutError, OSError) as e:
                self.logger.debug(f"Could not determine process group for {pid}: {e}")
                continue

        if terminated_via_group:
            self.logger.debug(
                f"Process group termination attempted for {len(terminated_via_group)} processes in {service_name}",
            )
            # Give process groups time to terminate gracefully
            await asyncio.sleep(constants.PROCESS_GROUP_TERMINATION_DELAY)

        return terminated_via_group

    async def _terminate_individual_processes(
        self,
        pids: list[int],
        service_name: str,
        process_groups_terminated: set[int],
    ) -> list[int]:
        """Terminate individual processes with graduated SIGTERM → SIGKILL approach."""
        # Phase 1: Send SIGTERM to processes not handled by process group termination
        sigterm_pids = []
        for pid in pids:
            if pid in process_groups_terminated:
                # Check if process group termination was successful
                if not self.is_process_running(pid):
                    self.logger.debug(f"Process {pid} successfully terminated via process group")
                    continue
                self.logger.debug(f"Process {pid} survived process group termination, trying individual")

            try:
                if self.is_process_running(pid):
                    os.kill(pid, signal.SIGTERM)
                    sigterm_pids.append(pid)
                    self.logger.debug(f"Sent SIGTERM to individual process {pid}")
            except ProcessLookupError:
                self.logger.debug(f"Process {pid} already terminated")
            except (OSError, PermissionError) as e:
                self.logger.warning(f"Failed to send SIGTERM to process {pid}: {e}")

        if not sigterm_pids:
            self.logger.debug(f"All processes for {service_name} terminated via process groups")
            return []

        # Phase 2: Wait for graceful termination with increased timeout
        self.logger.debug(f"Waiting for graceful termination of {len(sigterm_pids)} processes for {service_name}")
        graceful_timeout = constants.GRACEFUL_TERMINATION_TIMEOUT  # Increased from 5 to 8 seconds

        try:
            async with asyncio.timeout(graceful_timeout):
                check_interval = constants.PROCESS_CHECK_INTERVAL  # Check more frequently
                while sigterm_pids:
                    still_running = []
                    for pid in sigterm_pids:
                        if self.is_process_running(pid):
                            still_running.append(pid)
                        else:
                            self.logger.debug(f"Process {pid} terminated gracefully")

                    if not still_running:
                        self.logger.info(f"All remaining processes terminated gracefully for {service_name}")
                        return []

                    sigterm_pids = still_running
                    await asyncio.sleep(check_interval)

        except TimeoutError:
            self.logger.warning(
                f"Graceful termination timeout ({graceful_timeout}s) exceeded for {service_name}, "
                f"{len(sigterm_pids)} processes still running: {sigterm_pids}",
            )

        # Phase 3: Force termination (SIGKILL) of remaining processes
        sigkill_pids = []
        for pid in sigterm_pids:
            try:
                if self.is_process_running(pid):
                    os.kill(pid, signal.SIGKILL)
                    sigkill_pids.append(pid)
                    self.logger.warning(f"Force killed process {pid} for {service_name}")
            except ProcessLookupError:
                self.logger.debug(f"Process {pid} terminated between check and SIGKILL")
            except (OSError, PermissionError):
                self.logger.exception(f"Failed to force kill process {pid}")

        return sigkill_pids

    async def _verify_process_termination(self, remaining_pids: list[int], service_name: str) -> None:
        """Verify that all processes have been successfully terminated with retry logic."""
        if not remaining_pids:
            self.logger.debug(f"Process termination verification: all processes terminated for {service_name}")
            return

        # Final verification with retry for stubborn processes
        verification_timeout = constants.VERIFICATION_TIMEOUT_FINAL
        max_retries = constants.MAX_TERMINATION_RETRIES

        for retry in range(max_retries):
            self.logger.debug(f"Process termination verification attempt {retry + 1}/{max_retries} for {service_name}")

            try:
                async with asyncio.timeout(verification_timeout):
                    still_alive = []
                    still_alive = [pid for pid in remaining_pids if self.is_process_running(pid)]

                    if not still_alive:
                        self.logger.info(
                            f"Process termination verified: all processes successfully terminated for {service_name}",
                        )
                        return

                    # Log detailed information about surviving processes
                    self.logger.warning(
                        f"Verification found {len(still_alive)} processes still running after termination: "
                        f"{still_alive}",
                    )

                    # For final retry, attempt additional force termination
                    if retry == max_retries - 1:
                        self.logger.warning(
                            f"Final attempt to terminate stubborn processes for {service_name}: {still_alive}",
                        )
                        await self._final_cleanup_attempt(still_alive, service_name)
                    else:
                        # Wait before retry
                        await asyncio.sleep(constants.RETRY_DELAY)
                        remaining_pids = still_alive

            except TimeoutError:
                self.logger.exception(f"Process termination verification timeout for {service_name}")
                break

        # Final check and reporting
        final_survivors = [pid for pid in remaining_pids if self.is_process_running(pid)]
        if final_survivors:
            self.logger.error(
                f"Process termination incomplete for {service_name}: "
                f"{len(final_survivors)} processes remain: {final_survivors}. "
                f"These processes may need manual cleanup.",
            )
        else:
            self.logger.info(f"Process termination eventually successful for {service_name}")

    async def _final_cleanup_attempt(self, pids: list[int], service_name: str) -> None:
        """Perform final aggressive cleanup attempt for stubborn processes."""
        for pid in pids:
            try:
                if self.is_process_running(pid):
                    # Try SIGKILL one more time
                    os.kill(pid, signal.SIGKILL)
                    self.logger.warning(f"Final SIGKILL attempt on stubborn process {pid} for {service_name}")

                    # Brief wait to let the signal take effect
                    await asyncio.sleep(0.5)

                    # Try process group kill as last resort
                    try:
                        os.killpg(pid, signal.SIGKILL)
                        self.logger.warning(f"Final process group kill attempt on {pid} for {service_name}")
                    except (OSError, ProcessLookupError):
                        # Expected if process group doesn't exist or process is already gone
                        pass

            except ProcessLookupError:
                self.logger.debug(f"Stubborn process {pid} terminated during final cleanup")
            except (OSError, PermissionError):
                self.logger.exception(f"Final cleanup failed for process {pid}")

    async def _stop_service_unix(self, pid: int, service_name: str) -> None:
        """Stop service on Unix using process group termination."""
        try:
            # Try process group termination first
            os.killpg(pid, signal.SIGTERM)
            self.logger.info(f"Sent SIGTERM to process group {pid} for {service_name}")
        except (ProcessLookupError, OSError):
            # Fallback to individual process termination
            try:
                os.kill(pid, signal.SIGTERM)
                self.logger.info(f"Sent SIGTERM to process {pid} for {service_name} (fallback)")
            except ProcessLookupError:
                self.logger.debug(f"Process {pid} for {service_name} already terminated")

    async def _wait_for_process_termination(self, pid: int, service_name: str) -> None:
        """Enhanced process termination waiting with comprehensive error handling and logging."""
        termination_timeout = constants.PROCESS_TERMINATION_TIMEOUT  # Increased timeout for complex process trees
        check_interval = constants.PROCESS_CHECK_INTERVAL
        max_checks = int(termination_timeout / check_interval)

        self.logger.debug(f"Waiting up to {termination_timeout}s for {service_name} (PID {pid}) to terminate")

        try:
            async with asyncio.timeout(termination_timeout):
                for check_count in range(max_checks):
                    if not self.is_process_running(pid):
                        elapsed_time = check_count * check_interval
                        self.logger.debug(
                            f"Process {pid} for {service_name} terminated gracefully after {elapsed_time:.1f}s",
                        )
                        return

                    # Log progress every few seconds
                    if check_count > 0 and check_count % 10 == 0:
                        elapsed = check_count * check_interval
                        remaining = termination_timeout - elapsed
                        self.logger.debug(
                            f"Still waiting for {service_name} (PID {pid}) to terminate: "
                            f"{elapsed:.1f}s elapsed, {remaining:.1f}s remaining",
                        )

                    await asyncio.sleep(check_interval)

        except TimeoutError:
            self.logger.warning(
                f"Graceful termination timeout ({termination_timeout}s) exceeded for {service_name} (PID {pid}). "
                f"Process is stubborn, attempting force termination.",
            )
            try:
                await self._force_terminate_process(pid, service_name)
            except Exception:
                self.logger.exception(
                    f"Force termination also failed for {service_name} (PID {pid}). "
                    f"Process may require manual cleanup.",
                )

    async def _force_terminate_process(self, pid: int, service_name: str) -> None:
        """Enhanced force termination with comprehensive error handling and verification."""
        self.logger.warning(f"Initiating force termination for {service_name} (PID {pid})")

        # Check if process is still running before attempting force termination
        if not self.is_process_running(pid):
            self.logger.info(f"Process {pid} for {service_name} already terminated, no force needed")
            return

        try:
            if PlatformUtils.is_windows():
                await self._force_terminate_windows_process(pid, service_name)
            else:
                await self._force_terminate_unix_process(pid, service_name)

            # Verify force termination was successful
            await self._verify_force_termination(pid, service_name)

        except Exception:
            self.logger.exception(f"Critical failure during force termination of {service_name} (PID {pid})")
            # Log system information for debugging
            self.logger.info(f"Platform: {PlatformUtils.get_platform()}")
            self.logger.info(f"Process still running after force attempt: {self.is_process_running(pid)}")

    async def _force_terminate_windows_process(self, pid: int, service_name: str) -> None:
        """Force terminate Windows process with enhanced error handling."""
        methods = [
            ("taskkill /F /T", ["taskkill", "/F", "/T", "/PID", str(pid)]),
            ("taskkill /F", ["taskkill", "/F", "/PID", str(pid)]),
        ]

        for method_name, cmd in methods:
            try:
                self.logger.debug(f"Attempting Windows force termination via {method_name} for PID {pid}")

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=8)

                stdout_str = stdout.decode().strip()
                stderr_str = stderr.decode().strip()

                if proc.returncode == 0:
                    self.logger.warning(f"Successfully force terminated {service_name} (PID {pid}) via {method_name}")
                    self.logger.debug(f"Force termination output: {stdout_str}")
                    return
                self.logger.warning(
                    f"Force termination method {method_name} failed for PID {pid}: "
                    f"return_code={proc.returncode}, stderr={stderr_str}",
                )
            # Try next method

            except TimeoutError:
                self.logger.exception(f"Force termination method {method_name} timed out for PID {pid}")
            except OSError:
                self.logger.exception(f"Force termination method {method_name} failed for PID {pid}")

        # If all methods failed, log comprehensive error
        self.logger.error(f"All Windows force termination methods failed for {service_name} (PID {pid})")

    async def _force_terminate_unix_process(self, pid: int, service_name: str) -> None:
        """Force terminate Unix process with comprehensive fallback methods."""
        termination_methods = [
            ("process_group_sigkill", self._unix_kill_process_group),
            ("individual_sigkill", self._unix_kill_individual_process),
            ("kill_command", self._unix_kill_via_command),
        ]

        for method_name, method_func in termination_methods:
            try:
                self.logger.debug(f"Attempting Unix force termination via {method_name} for PID {pid}")
                success = await method_func(pid, service_name)
                if success:
                    self.logger.warning(f"Successfully force terminated {service_name} (PID {pid}) via {method_name}")
                    return
                self.logger.debug(f"Force termination method {method_name} was not successful for PID {pid}")
            except (OSError, ProcessLookupError, ValueError) as e:
                self.logger.warning(f"Force termination method {method_name} failed for PID {pid}: {e}")

        # If all methods failed
        self.logger.error(f"All Unix force termination methods failed for {service_name} (PID {pid})")

    async def _unix_kill_process_group(self, pid: int, _service_name: str) -> bool:
        """Attempt to kill Unix process via process group."""
        try:
            os.killpg(pid, signal.SIGKILL)
            await asyncio.sleep(constants.FINAL_CLEANUP_DELAY)  # Give time for signal to take effect
            return not self.is_process_running(pid)
        except OSError as e:
            if e.errno == ESRCH_ERRNO:  # No such process
                self.logger.debug(f"Process group {pid} does not exist")
            else:
                self.logger.debug(f"Process group kill failed for {pid}: {e}")
            return False

    async def _unix_kill_individual_process(self, pid: int, _service_name: str) -> bool:
        """Attempt to kill Unix process individually."""
        try:
            os.kill(pid, signal.SIGKILL)
            await asyncio.sleep(constants.FINAL_CLEANUP_DELAY)  # Give time for signal to take effect
            return not self.is_process_running(pid)
        except ProcessLookupError:
            self.logger.debug(f"Process {pid} already gone during individual kill")
            return True
        except OSError as e:
            self.logger.debug(f"Individual process kill failed for {pid}: {e}")
            return False

    async def _unix_kill_via_command(self, pid: int, _service_name: str) -> bool:
        """Attempt to kill Unix process via kill command."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "kill",
                "-KILL",
                str(pid),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _stdout, _stderr = await asyncio.wait_for(proc.communicate(), timeout=5)

            await asyncio.sleep(constants.FINAL_CLEANUP_DELAY)  # Give time for signal to take effect
            return not self.is_process_running(pid)

        except (TimeoutError, OSError) as e:
            self.logger.debug(f"Kill command failed for {pid}: {e}")
            return False

    async def _verify_force_termination(self, pid: int, service_name: str) -> None:
        """Verify that force termination was successful."""
        verification_attempts = 3
        verification_delay = 0.8

        for attempt in range(verification_attempts):
            await asyncio.sleep(verification_delay)

            if not self.is_process_running(pid):
                self.logger.info(f"Force termination verified successful for {service_name} (PID {pid})")
                return
            self.logger.warning(
                f"Force termination verification attempt {attempt + 1}/{verification_attempts} "
                f"failed - process {pid} still running",
            )

        # Final verification failed
        self.logger.error(
            f"Force termination verification FAILED for {service_name} (PID {pid}). "
            f"Process is extremely stubborn and may require manual intervention. "
            f"Consider using system tools to investigate this process.",
        )

    async def stop_all_services(self) -> list[str]:
        """Stop all tracked services.

        Returns:
            List of service names that were stopped successfully

        """
        services = await self.get_all_services()
        if not services:
            self.logger.info("No services to stop")
            await self.cleanup_state()
            return []

        stopped_services = []

        for service_name in services:
            if await self.stop_service(service_name):
                stopped_services.append(service_name)
            else:
                self.logger.error(f"Failed to stop {service_name}")

        if stopped_services:
            self.logger.info(f"Stopped services: {stopped_services}")

        # Clean up state file if all services were stopped successfully
        if len(stopped_services) == len(services):
            await self.cleanup_state()

        return stopped_services
