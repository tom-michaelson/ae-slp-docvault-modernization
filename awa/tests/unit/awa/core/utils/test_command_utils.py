"""Unit tests for CommandUtils class."""

import asyncio
import os
import subprocess
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

from awa.core.utils.command_utils import SUBPROCESS_EXEC_LIMIT, CommandUtils
from tests.utils.platform_test_utils import get_platform_specific_subprocess_kwargs


class TestCommandUtils:
    """Test cases for CommandUtils class."""

    def test_set_event_loop_policy_non_windows(self) -> None:
        """Test set_event_loop_policy on non-Windows platforms."""
        with (
            patch.object(sys, "platform", "linux"),
            patch(
                "asyncio.set_event_loop_policy",
            ) as mock_set_policy,
            patch("asyncio.DefaultEventLoopPolicy") as mock_policy_class,
        ):
            mock_policy = Mock()
            mock_policy_class.return_value = mock_policy

            CommandUtils.set_event_loop_policy()

            mock_policy_class.assert_called_once()
            mock_set_policy.assert_called_once_with(mock_policy)

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_set_event_loop_policy_windows(self) -> None:
        """Test set_event_policy on Windows platform."""
        with patch.object(sys, "platform", "win32"), patch("asyncio.set_event_loop_policy") as mock_set_policy:
            CommandUtils.set_event_loop_policy()
            # Should not call set_event_loop_policy on Windows
            mock_set_policy.assert_not_called()

    def test_should_use_shell_windows(self) -> None:
        """Test _should_use_shell returns True on Windows."""
        with patch.object(sys, "platform", "win32"):
            result = CommandUtils._should_use_shell()
            assert result is True

    def test_should_use_shell_non_windows(self) -> None:
        """Test _should_use_shell returns False on non-Windows."""
        with patch.object(sys, "platform", "linux"):
            result = CommandUtils._should_use_shell()
            assert result is False

    @pytest.mark.asyncio
    async def test_run_command_async_shell_mode(self) -> None:
        """Test run_command_async with shell mode."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            # Setup mock process
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_create_shell.return_value = mock_proc

            # Act
            success, output = await CommandUtils.run_command_async("test command")

            # Assert
            assert success is True
            assert output == "output"
            mock_create_shell.assert_called_once_with(
                "test command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None,
                env=os.environ.copy(),
            )

    @pytest.mark.asyncio
    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    async def test_run_command_async_exec_mode(self) -> None:
        """Test run_command_async with exec mode."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_exec") as mock_create_exec,
            patch(
                "shlex.split",
                return_value=["test", "command"],
            ),
        ):
            # Setup mock process with properly awaitable communicate
            mock_proc = AsyncMock()

            # Explicitly define a proper awaitable communicate method
            communicate_mock = AsyncMock()
            communicate_mock.return_value = (b"output", b"")
            mock_proc.communicate = communicate_mock

            mock_proc.returncode = 0
            mock_create_exec.return_value = mock_proc

            # Act
            success, output = await CommandUtils.run_command_async("test command")

            # Assert
            assert success is True
            assert output == "output"
            mock_create_exec.assert_called_once_with(
                "test",
                "command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=None,
                env=os.environ.copy(),
            )

    @pytest.mark.asyncio
    async def test_run_command_async_with_working_dir_and_env(self) -> None:
        """Test run_command_async with working directory and environment."""
        custom_env = {"TEST_VAR": "test_value"}

        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_create_shell.return_value = mock_proc

            # Act
            await CommandUtils.run_command_async(
                "test command",
                working_dir="/test/dir",
                env=custom_env,
            )

            # Assert
            mock_create_shell.assert_called_once_with(
                "test command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/test/dir",
                env=custom_env,
            )

    @pytest.mark.asyncio
    async def test_run_command_async_force_shell(self) -> None:
        """Test run_command_async with shell=True parameter."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_create_shell.return_value = mock_proc

            # Act - force shell even though _should_use_shell returns False
            success, _output = await CommandUtils.run_command_async("test command", shell=True)  # noqa: S604

            # Assert
            assert success is True
            mock_create_shell.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_command_async_failure(self) -> None:
        """Test run_command_async with command failure."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"", b"error output")
            mock_proc.returncode = 1
            mock_create_shell.return_value = mock_proc

            # Act
            success, output = await CommandUtils.run_command_async("failing command")

            # Assert
            assert success is False
            assert "error output" in output

    @pytest.mark.asyncio
    async def test_stream_command_async_shell_mode(self) -> None:
        """Test stream_command_async with shell mode."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            # Setup mock process with proper awaitable behavior
            mock_proc = AsyncMock()

            # Create a properly awaitable mock_stdout
            mock_stdout = AsyncMock()

            # Create a counter to simulate reading lines sequentially
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                lines = [b"line 1\n", b"line 2\n", b""]
                if call_count < len(lines):
                    result = lines[call_count]
                    call_count += 1
                    return result
                return b""

            # Set up readline to use our custom async function
            mock_stdout.readline = mock_readline

            mock_proc.stdout = mock_stdout

            # Make wait properly awaitable with a specific return value
            async def mock_wait() -> int:
                return 0

            mock_proc.wait = mock_wait

            mock_create_shell.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command")
            proc = await anext(stream)
            lines = [line async for line in stream]

            # Assert
            assert proc == mock_proc
            assert lines == ["line 1\n", "line 2\n"]

            # Build expected kwargs with platform-specific parameters
            # Shell mode, non-detach (default)
            expected_kwargs = get_platform_specific_subprocess_kwargs(
                {
                    "limit": SUBPROCESS_EXEC_LIMIT,
                    "stdout": asyncio.subprocess.PIPE,
                    "stderr": asyncio.subprocess.STDOUT,
                    "stdin": asyncio.subprocess.DEVNULL,
                    "cwd": None,
                    "env": os.environ.copy(),
                },
                is_shell_mode=True,
                is_detach_mode=False,
            )

            mock_create_shell.assert_called_once_with(
                "test command",
                **expected_kwargs,
            )

    @pytest.mark.asyncio
    async def test_stream_command_async_exec_mode(self) -> None:
        """Test stream_command_async with exec mode."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_exec") as mock_create_exec,
            patch(
                "shlex.split",
                return_value=["test", "command"],
            ),
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Create a counter for readline calls
            call_count_exec = 0

            async def mock_readline_exec() -> bytes:
                nonlocal call_count_exec
                lines = [b"output\n", b""]
                if call_count_exec < len(lines):
                    result = lines[call_count_exec]
                    call_count_exec += 1
                    return result
                return b""

            mock_stdout.readline = mock_readline_exec
            mock_proc.stdout = mock_stdout

            # Make wait properly awaitable
            async def mock_wait_exec() -> None:
                return None

            mock_proc.wait = mock_wait_exec
            mock_create_exec.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command")
            proc = await anext(stream)
            lines = [line async for line in stream]

            # Assert
            assert proc == mock_proc
            assert lines == ["output\n"]

            # Build expected kwargs with platform-specific parameters
            # Exec mode, non-detach (default)
            expected_kwargs = get_platform_specific_subprocess_kwargs(
                {
                    "limit": SUBPROCESS_EXEC_LIMIT,
                    "stdout": asyncio.subprocess.PIPE,
                    "stderr": asyncio.subprocess.STDOUT,
                    "stdin": asyncio.subprocess.DEVNULL,
                    "cwd": None,
                    "env": os.environ.copy(),
                },
                is_shell_mode=False,
                is_detach_mode=False,
            )

            mock_create_exec.assert_called_once_with(
                "test",
                "command",
                **expected_kwargs,
            )

    @pytest.mark.asyncio
    async def test_stream_command_async_no_stdout(self) -> None:
        """Test stream_command_async when process has no stdout."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_proc.stdout = None  # No stdout

            # Make wait properly awaitable
            async def mock_wait_no_stdout() -> None:
                return None

            mock_proc.wait = mock_wait_no_stdout
            mock_create_shell.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command")
            proc = await anext(stream)
            lines = [line async for line in stream]

            # Assert
            assert proc == mock_proc
            assert not lines

            # Build expected kwargs with platform-specific parameters
            # Shell mode, non-detach (default)
            expected_kwargs = get_platform_specific_subprocess_kwargs(
                {
                    "limit": SUBPROCESS_EXEC_LIMIT,
                    "stdout": asyncio.subprocess.PIPE,
                    "stderr": asyncio.subprocess.STDOUT,
                    "stdin": asyncio.subprocess.DEVNULL,
                    "cwd": None,
                    "env": os.environ.copy(),
                },
                is_shell_mode=True,
                is_detach_mode=False,
            )

            mock_create_shell.assert_called_once_with(
                "test command",
                **expected_kwargs,
            )

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_run_command_shell_mode(self) -> None:
        """Test run_command with shell mode."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_proc = Mock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_popen.return_value.__enter__.return_value = mock_proc

            # Act
            success, output = CommandUtils.run_command("test command")

            # Assert
            assert success is True
            assert output == "output"
            mock_popen.assert_called_once()

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_run_command_exec_mode(self) -> None:
        """Test run_command with exec mode."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("subprocess.Popen") as mock_popen,
            patch(
                "shlex.split",
                return_value=["test", "command"],
            ),
        ):
            mock_proc = Mock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_popen.return_value.__enter__.return_value = mock_proc

            # Act
            success, output = CommandUtils.run_command("test command")

            # Assert
            assert success is True
            assert output == "output"
            mock_popen.assert_called_once()

    @pytest.mark.filterwarnings("ignore::RuntimeWarning")
    def test_run_command_with_working_dir(self) -> None:
        """Test run_command with working directory."""
        with (
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch.object(
                CommandUtils,
                "set_event_loop_policy",
            ),
            patch("subprocess.Popen") as mock_popen,
        ):
            mock_proc = Mock()
            mock_proc.communicate.return_value = (b"output", b"")
            mock_proc.returncode = 0
            mock_popen.return_value.__enter__.return_value = mock_proc

            # Act
            CommandUtils.run_command("test command", working_dir="/test/dir")

            # Assert
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args[1]
            assert call_args["cwd"] == "/test/dir"

    def test_process_output_success(self) -> None:
        """Test _process_output with success."""
        stdout = b"stdout output"
        stderr = b"stderr output"

        success, output = CommandUtils._process_output(0, stdout, stderr)

        assert success is True
        assert "stdout output" in output
        assert "stderr output" in output

    def test_process_output_failure(self) -> None:
        """Test _process_output with failure."""
        stdout = b"stdout output"
        stderr = b"stderr output"

        success, output = CommandUtils._process_output(1, stdout, stderr)

        assert success is False
        assert "stdout output" in output
        assert "stderr output" in output

    def test_process_output_empty(self) -> None:
        """Test _process_output with empty output."""
        success, output = CommandUtils._process_output(0, b"", b"")

        assert success is True
        assert output == ""

    @pytest.mark.asyncio
    async def test_check_service_status_http_success(self) -> None:
        """Test check_service_status with successful HTTP response."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await CommandUtils.check_service_status("localhost", 8080)
            assert result is True
            mock_client.get.assert_called_once_with("http://localhost:8080")

    @pytest.mark.asyncio
    async def test_check_service_status_http_not_found(self) -> None:
        """Test check_service_status with HTTP 404 response."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status_code = 404
            mock_client.get.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await CommandUtils.check_service_status("localhost", 8080)
            assert result is True  # 404 still indicates service is running

    @pytest.mark.asyncio
    async def test_check_service_status_socket_fallback_success(self) -> None:
        """Test check_service_status falls back to socket when HTTP fails."""
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("socket.socket") as mock_socket,
        ):
            # HTTP fails
            mock_client = AsyncMock()
            mock_client.get.side_effect = ConnectionError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Socket succeeds
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value.__enter__.return_value = mock_sock_instance

            result = await CommandUtils.check_service_status("localhost", 8080)
            assert result is True
            mock_sock_instance.connect_ex.assert_called_once_with(("localhost", 8080))

    @pytest.mark.asyncio
    async def test_check_service_status_socket_fallback_failure(self) -> None:
        """Test check_service_status socket fallback when connection fails."""
        with (
            patch("httpx.AsyncClient") as mock_client_class,
            patch("socket.socket") as mock_socket,
        ):
            # HTTP fails
            mock_client = AsyncMock()
            mock_client.get.side_effect = ConnectionError("Connection failed")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Socket fails
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 1
            mock_socket.return_value.__enter__.return_value = mock_sock_instance

            result = await CommandUtils.check_service_status("localhost", 8080)
            assert result is False
            mock_sock_instance.connect_ex.assert_called_once_with(("localhost", 8080))

    @pytest.mark.asyncio
    async def test_check_service_status_with_exception(self) -> None:
        """Test check_service_status handles exceptions."""
        with patch("socket.socket") as mock_socket:
            mock_socket.side_effect = OSError("Test error")

            result = await CommandUtils.check_service_status("localhost", 8080)
            assert result is False

    # Cross-platform process group creation tests

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    @patch("subprocess.CREATE_NEW_PROCESS_GROUP", 0x00000200, create=True)
    async def test_stream_command_async_detach_windows(
        self,
        mock_is_windows: Mock,
    ) -> None:
        """Test stream_command_async with detach=True on Windows."""
        mock_is_windows.return_value = True

        with (
            patch.object(CommandUtils, "set_event_loop_policy"),
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Mock readline to return no output and then stop
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                if call_count == 0:
                    call_count += 1
                    return b""
                return b""

            mock_stdout.readline = mock_readline
            mock_proc.stdout = mock_stdout
            mock_proc.wait = AsyncMock(return_value=0)
            mock_create_shell.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command", detach=True)
            proc = await anext(stream)
            _ = [line async for line in stream]  # Consume stream output

            # Assert
            assert proc == mock_proc
            mock_create_shell.assert_called_once_with(
                "test command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    @patch("subprocess.CREATE_NEW_PROCESS_GROUP", 0x00000200, create=True)
    async def test_stream_command_async_detach_windows_exec_mode(
        self,
        mock_is_windows: Mock,
    ) -> None:
        """Test stream_command_async with detach=True on Windows in exec mode."""
        mock_is_windows.return_value = True

        with (
            patch.object(CommandUtils, "set_event_loop_policy"),
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_create_exec,
            patch("shlex.split", return_value=["test", "command"]),
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Mock readline to return no output and then stop
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                if call_count == 0:
                    call_count += 1
                    return b""
                return b""

            mock_stdout.readline = mock_readline
            mock_proc.stdout = mock_stdout
            mock_proc.wait = AsyncMock(return_value=0)
            mock_create_exec.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command", detach=True)
            proc = await anext(stream)
            _ = [line async for line in stream]  # Consume stream output

            # Assert
            assert proc == mock_proc
            mock_create_exec.assert_called_once_with(
                "test",
                "command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_stream_command_async_detach_unix(
        self,
        mock_is_windows: Mock,
    ) -> None:
        """Test stream_command_async with detach=True on Unix."""
        mock_is_windows.return_value = False

        with (
            patch.object(CommandUtils, "set_event_loop_policy"),
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Mock readline to return no output and then stop
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                if call_count == 0:
                    call_count += 1
                    return b""
                return b""

            mock_stdout.readline = mock_readline
            mock_proc.stdout = mock_stdout
            mock_proc.wait = AsyncMock(return_value=0)
            mock_create_shell.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command", detach=True)
            proc = await anext(stream)
            _ = [line async for line in stream]  # Consume stream output

            # Assert
            assert proc == mock_proc
            mock_create_shell.assert_called_once_with(
                "test command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None,
                env=os.environ.copy(),
                start_new_session=True,
            )

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_stream_command_async_detach_unix_exec_mode(
        self,
        mock_is_windows: Mock,
    ) -> None:
        """Test stream_command_async with detach=True on Unix in exec mode."""
        mock_is_windows.return_value = False

        with (
            patch.object(CommandUtils, "set_event_loop_policy"),
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_create_exec,
            patch("shlex.split", return_value=["test", "command"]),
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Mock readline to return no output and then stop
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                if call_count == 0:
                    call_count += 1
                    return b""
                return b""

            mock_stdout.readline = mock_readline
            mock_proc.stdout = mock_stdout
            mock_proc.wait = AsyncMock(return_value=0)
            mock_create_exec.return_value = mock_proc

            # Act
            stream = CommandUtils.stream_command_async("test command", detach=True)
            proc = await anext(stream)
            _ = [line async for line in stream]  # Consume stream output

            # Assert
            assert proc == mock_proc
            mock_create_exec.assert_called_once_with(
                "test",
                "command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None,
                env=os.environ.copy(),
                start_new_session=True,
            )

    # Windows non-detach mode tests

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    @patch("subprocess.CREATE_NEW_PROCESS_GROUP", 0x00000200, create=True)
    async def test_stream_command_async_non_detach_windows_shell_mode(
        self,
        mock_is_windows: Mock,
    ) -> None:
        """Test stream_command_async with detach=False on Windows in shell mode."""
        mock_is_windows.return_value = True

        with (
            patch.object(CommandUtils, "set_event_loop_policy"),
            patch.object(CommandUtils, "_should_use_shell", return_value=True),
            patch("asyncio.create_subprocess_shell") as mock_create_shell,
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Mock readline to return some output and then stop
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                lines = [b"output\n", b""]
                if call_count < len(lines):
                    result = lines[call_count]
                    call_count += 1
                    return result
                return b""

            mock_stdout.readline = mock_readline
            mock_proc.stdout = mock_stdout
            mock_proc.wait = AsyncMock(return_value=0)
            mock_create_shell.return_value = mock_proc

            # Act - non-detach mode (default)
            stream = CommandUtils.stream_command_async("test command")
            proc = await anext(stream)
            lines = [line async for line in stream]

            # Assert
            assert proc == mock_proc
            assert lines == ["output\n"]
            mock_create_shell.assert_called_once_with(
                "test command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    @patch("subprocess.CREATE_NEW_PROCESS_GROUP", 0x00000200, create=True)
    async def test_stream_command_async_non_detach_windows_exec_mode(
        self,
        mock_is_windows: Mock,
    ) -> None:
        """Test stream_command_async with detach=False on Windows in exec mode."""
        mock_is_windows.return_value = True

        with (
            patch.object(CommandUtils, "set_event_loop_policy"),
            patch.object(CommandUtils, "_should_use_shell", return_value=False),
            patch("asyncio.create_subprocess_exec") as mock_create_exec,
            patch("shlex.split", return_value=["test", "command"]),
        ):
            mock_proc = AsyncMock()
            mock_stdout = AsyncMock()

            # Mock readline to return some output and then stop
            call_count = 0

            async def mock_readline() -> bytes:
                nonlocal call_count
                lines = [b"output\n", b""]
                if call_count < len(lines):
                    result = lines[call_count]
                    call_count += 1
                    return result
                return b""

            mock_stdout.readline = mock_readline
            mock_proc.stdout = mock_stdout
            mock_proc.wait = AsyncMock(return_value=0)
            mock_create_exec.return_value = mock_proc

            # Act - non-detach mode (default)
            stream = CommandUtils.stream_command_async("test command")
            proc = await anext(stream)
            lines = [line async for line in stream]

            # Assert
            assert proc == mock_proc
            assert lines == ["output\n"]
            mock_create_exec.assert_called_once_with(
                "test",
                "command",
                limit=SUBPROCESS_EXEC_LIMIT,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.DEVNULL,
                cwd=None,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
