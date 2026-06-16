import asyncio
import contextlib
import logging
import os
import shlex
import socket
import subprocess
import sys
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.utils.platform_utils import PlatformUtils

SUBPROCESS_EXEC_LIMIT = 1024 * 1024  # 65536 is default

init_logging()
logger = get_logger(LoggerComponent.CLI)


class CommandUtils:
    @staticmethod
    def set_event_loop_policy() -> None:
        if sys.platform != "win32":
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

    @staticmethod
    @contextlib.asynccontextmanager
    async def safe_subprocess_exec(*args: str, **kwargs: object) -> AsyncGenerator[asyncio.subprocess.Process, None]:
        """Context manager for subprocess creation with automatic cleanup.

        Automatically sets stdin to DEVNULL if not specified and ensures
        proper subprocess cleanup to prevent transport warnings.
        """
        # Set default stdin to DEVNULL if not specified
        if "stdin" not in kwargs:
            kwargs["stdin"] = asyncio.subprocess.DEVNULL

        proc = None
        try:
            proc = await asyncio.create_subprocess_exec(*args, **kwargs)
            yield proc
        finally:
            if proc is not None and proc.returncode is None:
                # Ensure subprocess is properly cleaned up
                try:
                    proc.terminate()
                    await asyncio.wait_for(proc.wait(), timeout=2.0)
                except (TimeoutError, ProcessLookupError, OSError):
                    try:
                        proc.kill()
                        await proc.wait()
                    except (ProcessLookupError, OSError):
                        pass  # Process already terminated

    @staticmethod
    def _should_use_shell() -> bool:
        """Determine if shell should be used for command execution."""
        return sys.platform == "win32"

    @staticmethod
    async def run_command_async(
        command: str,
        working_dir: str | None = None,
        env: dict | None = None,
        shell: bool = False,
    ) -> tuple[bool, str]:
        CommandUtils.set_event_loop_policy()
        use_shell = CommandUtils._should_use_shell()
        process_env = env if env is not None else os.environ.copy()

        if use_shell or shell:
            # On Windows, use shell=True for better PATH resolution
            proc = await asyncio.create_subprocess_shell(
                command,
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=process_env,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *shlex.split(command),
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir,
                env=process_env,
            )
        stdout, stderr = await proc.communicate()
        return CommandUtils._process_output(proc.returncode or 0, stdout, stderr)

    @staticmethod
    async def stream_command_async(
        command: str,
        working_dir: str | None = None,
        env: dict[str, str] | None = None,
        shell: bool = False,
        detach: bool = False,
    ) -> AsyncGenerator[str | Any, None]:
        """Run a command asynchronously and yield output lines.

        Args:
            command: The command to run.
            working_dir: The working directory to run the command in.
            env: Environment variables to set for the command.
            shell: Whether to run the command in a shell (default False).
            detach: Whether to run the process in detached (daemon) mode.

        Yields:
            Output lines or process handles.

        """
        CommandUtils.set_event_loop_policy()
        use_shell = CommandUtils._should_use_shell()
        process_env = env if env is not None else os.environ.copy()

        # Create subprocess based on platform and mode
        proc = await CommandUtils._create_subprocess(
            command,
            working_dir,
            process_env,
            shell,
            use_shell,
            detach,
        )

        # Log process creation details
        logger.debug(f"Created subprocess PID {proc.pid} for command: {command[:50]}...")
        CommandUtils._log_subprocess_info(proc)

        # Yield the process handle first
        yield proc

        # Handle output streaming based on detach mode and platform
        async for line in CommandUtils._handle_output_streaming(proc, detach):
            yield line

    @staticmethod
    async def _create_subprocess(
        command: str,
        working_dir: str | None,
        process_env: dict,
        shell: bool,
        use_shell: bool,
        detach: bool,
    ) -> asyncio.subprocess.Process:
        """Create subprocess with appropriate configuration for platform and detach mode."""
        if detach:
            return await CommandUtils._create_detached_subprocess(
                command,
                working_dir,
                process_env,
                shell,
                use_shell,
            )
        return await CommandUtils._create_normal_subprocess(
            command,
            working_dir,
            process_env,
            shell,
            use_shell,
        )

    @staticmethod
    async def _create_detached_subprocess(
        command: str,
        working_dir: str | None,
        process_env: dict,
        shell: bool,
        use_shell: bool,
    ) -> asyncio.subprocess.Process:
        """Create detached subprocess with platform-specific settings."""
        if PlatformUtils.is_windows():
            return await CommandUtils._create_windows_detached_subprocess(
                command,
                working_dir,
                process_env,
                shell,
                use_shell,
            )
        return await CommandUtils._create_unix_detached_subprocess(
            command,
            working_dir,
            process_env,
            shell,
            use_shell,
        )

    @staticmethod
    async def _create_windows_detached_subprocess(
        command: str,
        working_dir: str | None,
        process_env: dict,
        shell: bool,
        use_shell: bool,
    ) -> asyncio.subprocess.Process:
        """Create Windows detached subprocess with DEVNULL streams."""
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP

        if shell or use_shell:
            return await asyncio.create_subprocess_shell(
                command,
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=working_dir,
                env=process_env,
                creationflags=creation_flags,
            )
        return await asyncio.create_subprocess_exec(
            *shlex.split(command),
            limit=SUBPROCESS_EXEC_LIMIT,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            stdin=asyncio.subprocess.DEVNULL,
            cwd=working_dir,
            env=process_env,
            creationflags=creation_flags,
        )

    @staticmethod
    async def _create_unix_detached_subprocess(
        command: str,
        working_dir: str | None,
        process_env: dict,
        shell: bool,
        use_shell: bool,
    ) -> asyncio.subprocess.Process:
        """Create Unix detached subprocess with PIPE streams for startup validation."""
        if shell or use_shell:
            return await asyncio.create_subprocess_shell(
                command,
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=working_dir,
                env=process_env,
                start_new_session=True,
            )
        return await asyncio.create_subprocess_exec(
            *shlex.split(command),
            limit=SUBPROCESS_EXEC_LIMIT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL,
            cwd=working_dir,
            env=process_env,
            start_new_session=True,
        )

    @staticmethod
    async def _create_normal_subprocess(
        command: str,
        working_dir: str | None,
        process_env: dict,
        shell: bool,
        use_shell: bool,
    ) -> asyncio.subprocess.Process:
        """Create normal (non-detached) subprocess."""
        if shell or use_shell:
            if PlatformUtils.is_windows():
                return await asyncio.create_subprocess_shell(
                    command,
                    limit=SUBPROCESS_EXEC_LIMIT,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    stdin=asyncio.subprocess.DEVNULL,
                    cwd=working_dir,
                    env=process_env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                )
            return await asyncio.create_subprocess_shell(
                command,
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=working_dir,
                env=process_env,
            )
        if PlatformUtils.is_windows():
            return await asyncio.create_subprocess_exec(
                *shlex.split(command),
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=working_dir,
                env=process_env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        return await asyncio.create_subprocess_exec(
            *shlex.split(command),
            limit=SUBPROCESS_EXEC_LIMIT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            stdin=asyncio.subprocess.DEVNULL,
            cwd=working_dir,
            env=process_env,
            start_new_session=True,
        )

    @staticmethod
    def _log_subprocess_info(proc: asyncio.subprocess.Process) -> None:
        """Log subprocess information if available."""
        try:
            if hasattr(proc, "get_extra_info"):
                extra_info = proc.get_extra_info("subprocess")
                if extra_info:
                    logger.debug("Extra subprocess info available")
        except (AttributeError, ValueError) as e:
            logger.debug(f"Subprocess info access encountered issues: {e}")

    @staticmethod
    async def _handle_output_streaming(proc: asyncio.subprocess.Process, detach: bool) -> AsyncGenerator[str, None]:
        """Handle output streaming based on detach mode and platform."""
        if detach:
            if PlatformUtils.is_windows():
                logger.debug(f"Process {proc.pid} started in detached mode with DEVNULL streams - no cleanup needed")
                return
            logger.debug(f"Process {proc.pid} started in detached mode - will consume initial output")

        # Stream output line by line
        if proc.stdout:
            async for line in CommandUtils._read_output_lines(proc.stdout):
                yield line

    @staticmethod
    async def _read_output_lines(stdout: asyncio.StreamReader) -> AsyncGenerator[str, None]:
        """Read output lines from stdout stream."""
        while True:
            try:
                line = await stdout.readline()
                if not line:
                    break
                yield line.decode("utf-8")
            except ValueError as e:
                error_msg = str(e).lower()
                if "closed" in error_msg or "operation on closed" in error_msg:
                    logger.debug(f"Process pipe closed during termination: {e}")
                    break
                else:
                    # Unexpected ValueError - preserve original behavior
                    logger.warning(f"Error in reading proc stdout: {e}")
                    # Continue reading instead of breaking to match current behavior

    @staticmethod
    def run_command(command: str, working_dir: str | None = None) -> tuple[bool, str]:
        CommandUtils.set_event_loop_policy()
        use_shell = CommandUtils._should_use_shell()

        if use_shell:
            # On Windows, use shell=True for better PATH resolution
            with subprocess.Popen(  # noqa: S602
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=os.environ.copy(),
            ) as proc:
                stdout, stderr = proc.communicate()
                return CommandUtils._process_output(proc.returncode, stdout, stderr)
        else:
            args = shlex.split(command)
            with subprocess.Popen(  # noqa: S603
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=working_dir,
                env=os.environ.copy(),
            ) as proc:
                stdout, stderr = proc.communicate()
                return CommandUtils._process_output(proc.returncode, stdout, stderr)

    @staticmethod
    def _process_output(returncode: int, stdout: bytes, stderr: bytes) -> tuple[bool, str]:
        output = []
        if stdout:
            output.append(stdout.decode("utf-8", errors="replace"))
        if stderr:
            output.append(stderr.decode("utf-8", errors="replace"))

        return returncode == 0, "\n".join(output).strip()

    @staticmethod
    async def check_service_status(host: str, port: int) -> bool:
        """Check if a service is running by attempting to connect to its port with HTTP.

        Args:
            host: The host to check
            port: The port to check

        Returns:
            bool: True if the service is running, False otherwise

        """
        try:
            # Temporarily disable httpx and related debug logging to avoid verbose output
            loggers_to_quiet = [
                "httpx",
                "httpcore",
                "httpcore.connection",
                "httpcore.http11",
                "httpcore.proxy",
            ]
            original_levels = {}
            for logger_name in loggers_to_quiet:
                logger_obj = logging.getLogger(logger_name)
                original_levels[logger_name] = logger_obj.level
                logger_obj.setLevel(logging.WARNING)

            try:
                url = f"http://{host}:{port}"
                timeout = httpx.Timeout(2.0)

                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url)
                    # Accept any HTTP response (even 404) as proof the service is running
                    return response.status_code is not None
            finally:
                # Restore original logging levels
                for logger_name, original_level in original_levels.items():
                    logging.getLogger(logger_name).setLevel(original_level)
        except (
            ConnectionError,
            TimeoutError,
            ValueError,
            httpx.ConnectError,
            httpx.TimeoutException,
            httpx.RemoteProtocolError,
            OSError,
        ) as e:
            # If HTTP fails, fall back to socket check
            logger.debug(f"HTTP health check failed: {e}")
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex((host, port))
                    return result == 0
            except OSError:
                return False
