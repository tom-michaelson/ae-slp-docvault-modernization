import asyncio
import contextlib
import signal
import subprocess
from pathlib import Path

from temporalio.client import Client

from awa.core import constants
from awa.core.logger.logger import LoggerComponent, get_logger, get_subprocess_logger
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.command_utils import CommandUtils
from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.platform_utils import PlatformUtils


class TemporalServer:
    """Manages the Temporal server process with enhanced stability for detach mode."""

    def __init__(self) -> None:
        self.server_started_event = asyncio.Event()
        self.logger = get_logger(LoggerComponent.CLI)
        self.subprocess_logger = get_subprocess_logger("temporal-server")
        self.config = ConfigLoader.get_config()
        self._server_task: asyncio.Task | None = None
        self._temporal_proc = None
        self.server_process = None
        self.should_stop = False
        self.output_tasks = []
        self.env_config = EnvConfig.get_env_config()
        self.logger.debug(
            f"Loaded config. \n-----[CONFIG]-----\n{self.config.model_dump_json(indent=2)}\n-----[/CONFIG]-----\n",
        )

    async def _temporal_server(self) -> None:
        self.logger.info("Starting Temporal Server...")
        gen = CommandUtils.stream_command_async(
            f"temporal server start-dev --ui-port {EnvConfig.get_env_config().temporal_ui_port} "
            f"--port {EnvConfig.get_env_config().temporal_server_port} "
            f"--metrics-port {EnvConfig.get_env_config().temporal_metrics_port} "
            f"--db-filename {constants.TEMPORAL_DB_FILENAME}",
        )
        proc = await gen.__anext__()  # Get proc handle
        self._temporal_proc = proc
        try:
            async for line in gen:
                self.logger.info(f"[Temporal] {line}")
                if not self.server_started_event.is_set():
                    self.server_started_event.set()
        except asyncio.CancelledError:
            self.logger.info("Temporal server task cancelled, terminating process...")
            proc.terminate()
            await proc.wait()
            raise
        finally:
            self._temporal_proc = None

    async def check_service_status(self) -> bool:
        """Check if the Temporal server is running.

        Returns:
            bool: True if the server is running, False otherwise

        """
        try:
            await Client.connect(
                f"{EnvConfig.get_env_config().temporal_server_host}:{EnvConfig.get_env_config().temporal_server_port}",
                namespace=EnvConfig.get_env_config().temporal_namespace,
            )
            if not self.server_started_event.is_set():
                self.server_started_event.set()
        except (OSError, ConnectionRefusedError, RuntimeError):
            return False
        return True

    async def start_server(self) -> None:
        """Start the Temporal server service."""
        if not await self.check_service_status() and (not self._server_task or self._server_task.done()):
            self._server_task = asyncio.create_task(self._temporal_server())
            # Wait for server to be ready
            await self.server_started_event.wait()
        await self._ensure_namespace_retention()

    async def stop_server(self) -> None:
        """Stop the Temporal server service."""
        self.logger.info("Stopping server")
        if self._server_task and not self._server_task.done():
            self._server_task.cancel()
            self.logger.info("Server task cancelled")
            with contextlib.suppress(asyncio.CancelledError):
                await self._server_task
            self.server_started_event.clear()
            self.logger.info("Server stopped")

    async def start_temporal_server(self) -> None:
        """Start the Temporal server service."""
        try:
            if not await self.check_service_status():
                await self.start_server()
        except Exception:
            # If anything fails, try to clean up
            await self.stop_temporal_server()
            raise

    async def stop_temporal_server(self) -> None:
        """Stop the Temporal server service."""
        try:
            await self.stop_server()
            self.logger.info("Temporal server shutdown complete")
        except Exception:
            self.logger.exception("Error stopping server")
            # Continue with cleanup even if there's an error
            self.server_started_event.clear()
            if self._server_task:
                self._server_task.cancel()

    async def run_with_retries(self, max_retries: int = 3) -> None:
        """Run the server with retry logic, similar to worker."""
        retry_count = 0

        while retry_count < max_retries:
            try:
                await self.start()

                # Wait for server to be ready
                if await self._wait_for_server_ready():
                    self.logger.info("Temporal server is ready")
                    # Keep running until stopped
                    await self.wait()
                    break
                raise RuntimeError("Server failed to become ready")  # noqa: TRY301

            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    self.logger.warning(
                        f"Server start attempt {retry_count} failed: {e}. Retrying ({retry_count}/{max_retries})...",
                    )
                    await asyncio.sleep(2**retry_count)  # Exponential backoff
                else:
                    self.logger.exception("Failed to start server after %d attempts", max_retries)
                    raise

    async def start(self, detach: bool = False) -> int:
        """Start the Temporal server with proper I/O handling."""
        # Build the temporal server command
        cmd = [
            "temporal",
            "server",
            "start-dev",
            "--db-filename",
            str(Path.cwd() / "temporal.db"),
            "--ip",
            self.env_config.temporal_server_host,
            "--port",
            str(self.env_config.temporal_server_port),
            "--ui-port",
            str(self.env_config.temporal_ui_port),
            "--log-level",
            "warn",
        ]

        try:
            # Configure subprocess based on detach mode
            if detach:
                # In detach mode, redirect to prevent pipe issues
                stdout_target = asyncio.subprocess.DEVNULL
                stderr_target = asyncio.subprocess.DEVNULL
                stdin_target = asyncio.subprocess.DEVNULL
            else:
                # Normal mode - capture output
                stdout_target = asyncio.subprocess.PIPE
                stderr_target = asyncio.subprocess.PIPE
                stdin_target = asyncio.subprocess.DEVNULL

            # Platform-specific process creation
            if PlatformUtils.is_windows():
                creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if detach else 0
                self.server_process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=stdout_target,
                    stderr=stderr_target,
                    stdin=stdin_target,
                    creationflags=creation_flags,
                )
            else:
                self.server_process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=stdout_target,
                    stderr=stderr_target,
                    stdin=stdin_target,
                    start_new_session=detach,
                    preexec_fn=None if not detach else self._ignore_signals,
                )

            self.logger.info(f"Temporal server started with PID: {self.server_process.pid}")

            # Only consume output in non-detach mode
            if not detach and self.server_process.stdout:
                task = asyncio.create_task(self._consume_output(self.server_process.stdout, "stdout"))
                self.output_tasks.append(task)
            if not detach and self.server_process.stderr:
                task = asyncio.create_task(self._consume_output(self.server_process.stderr, "stderr"))
                self.output_tasks.append(task)

            # Add monitoring with restart capability
            if detach:
                task = asyncio.create_task(self._monitor_server_health())
                self.output_tasks.append(task)

            return self.server_process.pid

        except Exception:
            self.logger.exception("Failed to start Temporal server")
            raise

    def _ignore_signals(self) -> None:
        """Ignore signals in child process to prevent signal propagation issues."""
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        signal.signal(signal.SIGTERM, signal.SIG_IGN)

    async def _consume_output(self, stream: asyncio.StreamReader, stream_name: str) -> None:
        """Consume output from the server to prevent pipe blocking."""
        if not stream:
            return

        try:
            while True:
                line = await stream.readline()
                if not line:
                    break
                # Use subprocess logger for consistent formatting
                self.subprocess_logger.info(line.decode().rstrip())
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Error reading {stream_name}: {e}")

    async def _wait_for_server_ready(self) -> bool:
        """Wait for the server to be ready."""
        try:
            async with asyncio.timeout(30):
                while True:
                    if await CommandUtils.check_service_status(
                        self.env_config.temporal_server_host,
                        self.env_config.temporal_server_port,
                    ):
                        await self._ensure_namespace_retention()
                        return True
                    await asyncio.sleep(1)
        except TimeoutError:
            return False

    async def _ensure_namespace_retention(self) -> None:
        """Set the namespace retention so completed workflow history isn't pruned daily.

        Temporal's `start-dev` creates the default namespace with a 24-hour retention,
        which means completed runs disappear from the UI a day after they finish even
        though `temporal.db` is preserved. This bumps it to a longer period so history
        only goes away when the user explicitly runs `make clean`.
        """
        namespace = self.env_config.temporal_namespace
        retention = f"{constants.TEMPORAL_NAMESPACE_RETENTION_DAYS}d"
        address = f"{self.env_config.temporal_server_host}:{self.env_config.temporal_server_port}"
        try:
            proc = await asyncio.create_subprocess_exec(
                "temporal", "operator", "namespace", "update",
                "--namespace", namespace,
                "--retention", retention,
                "--address", address,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
        except FileNotFoundError:
            self.logger.warning(
                "`temporal` CLI not on PATH; skipping namespace retention update. "
                "Workflow history will follow Temporal's default retention.",
            )
            return
        if proc.returncode != 0:
            self.logger.warning(
                f"Failed to set retention on namespace '{namespace}' to {retention}: "
                f"{stderr.decode().strip()}",
            )
        else:
            self.logger.info(f"Namespace '{namespace}' retention set to {retention}")

    async def _monitor_server_health(self) -> None:
        """Monitor the server process and handle restarts if needed in detach mode."""
        max_restarts = 3
        restart_count = 0

        while not self.should_stop and restart_count < max_restarts:
            if self.server_process:
                return_code = await self.server_process.wait()

                if not self.should_stop and return_code != 0:
                    self.logger.error(f"Temporal server exited unexpectedly with code: {return_code}")
                    restart_count += 1

                    if restart_count < max_restarts:
                        self.logger.info(f"Attempting restart ({restart_count}/{max_restarts})...")
                        await asyncio.sleep(2**restart_count)  # Exponential backoff
                        await self.start(detach=True)
                    else:
                        self.logger.error("Max restart attempts reached, giving up")
                        break

    async def stop(self) -> None:
        """Stop the Temporal server gracefully."""
        self.should_stop = True

        # Cancel output consumption tasks
        for task in self.output_tasks:
            task.cancel()

        if self.server_process:
            try:
                self.server_process.terminate()
                await asyncio.wait_for(self.server_process.wait(), timeout=5.0)
            except TimeoutError:
                self.logger.warning("Temporal server did not stop gracefully, forcing kill")
                self.server_process.kill()
                await self.server_process.wait()

            self.logger.info("Temporal server stopped")

    async def wait(self) -> int | None:
        """Wait for the server process to complete."""
        if self.server_process:
            return await self.server_process.wait()
        return None
