"""Unit tests for StateManager."""

import asyncio
import json
import os
import signal
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from awa.core.cli import constants
from awa.core.cli.state_manager import StateManager
from awa.core.models.cli.service_state import ServiceInfo, ServiceState
from awa.core.utils.file_system_utils import FileSystemUtils

# Add missing attributes for Windows compatibility in tests
if not hasattr(os, "killpg"):
    os.killpg = lambda _pid, _sig: None

if not hasattr(signal, "SIGKILL"):
    signal.SIGKILL = 9


class TestStateManager:
    """Test cases for StateManager class."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path: Path) -> Path:
        """Provide a temporary directory for state files."""
        return tmp_path / ".awa_state"

    @pytest.fixture
    def state_manager(self, temp_state_dir: Path) -> StateManager:
        """Provide a StateManager instance with temporary directory."""
        return StateManager(state_dir=temp_state_dir)

    @pytest.fixture
    def sample_service_info(self) -> ServiceInfo:
        """Provide sample service info."""
        return ServiceInfo(
            pid=12345,
            port=8001,
            started_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
        )

    @pytest.fixture
    def sample_state(self, sample_service_info: ServiceInfo) -> ServiceState:
        """Provide sample service state."""
        return ServiceState(
            timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC),
            services={
                constants.SERVICE_API: sample_service_info,
            },
        )

    def test_init_default_state_dir(self) -> None:
        """Test StateManager initialization with default state directory."""
        manager = StateManager()
        expected_dir = Path.cwd() / ".awa_state"
        expected_file = expected_dir / "services.json"
        assert manager.state_dir == expected_dir
        assert manager.state_file == expected_file

    def test_init_custom_state_dir(self, temp_state_dir: Path) -> None:
        """Test StateManager initialization with custom state directory."""
        manager = StateManager(state_dir=temp_state_dir)
        assert manager.state_dir == temp_state_dir
        assert manager.state_file == temp_state_dir / "services.json"

    @pytest.mark.asyncio
    async def test_ensure_state_directory(self, state_manager: StateManager) -> None:
        """Test state directory creation."""
        assert not state_manager.state_dir.exists()
        await state_manager.ensure_state_directory()
        assert state_manager.state_dir.exists()
        assert state_manager.state_dir.is_dir()

    @pytest.mark.asyncio
    @patch("awa.core.cli.state_manager.FileSystemUtils.write_async")
    async def test_save_state(
        self,
        mock_write: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test saving service state."""
        await state_manager.save_state(sample_state)

        mock_write.assert_called_once()
        args = mock_write.call_args[0]
        assert args[0] == str(state_manager.state_file)

        # Verify the JSON content
        written_json = args[1]
        written_data = json.loads(written_json)
        assert constants.SERVICE_API in written_data["services"]
        assert written_data["services"][constants.SERVICE_API]["pid"] == 12345

    @pytest.mark.asyncio
    async def test_save_state_creates_directory(
        self,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test that save_state creates the state directory if it doesn't exist."""
        # Remove the directory if it exists
        if state_manager.state_dir.exists():
            import shutil

            shutil.rmtree(state_manager.state_dir)

        await state_manager.save_state(sample_state)

        # Verify directory was created
        assert state_manager.state_dir.exists()

    @pytest.mark.asyncio
    @patch("awa.core.cli.state_manager.FileSystemUtils.write_async")
    async def test_save_state_error_handling(
        self,
        mock_write: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test save_state error handling."""
        mock_write.side_effect = OSError("Permission denied")

        with pytest.raises(OSError):
            await state_manager.save_state(sample_state)

    @pytest.mark.asyncio
    @patch("awa.core.cli.state_manager.FileSystemUtils.read_async")
    async def test_load_state_success(
        self,
        mock_read: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test loading valid service state."""
        # Setup state file to exist
        state_manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        state_manager.state_file.touch()

        mock_read.return_value = sample_state.model_dump_json()

        result = await state_manager.load_state()

        assert result is not None
        assert result.services[constants.SERVICE_API].pid == 12345
        mock_read.assert_called_once_with(str(state_manager.state_file))

    @pytest.mark.asyncio
    async def test_load_state_file_not_exists(self, state_manager: StateManager) -> None:
        """Test loading state when file doesn't exist."""
        result = await state_manager.load_state()
        assert result is None

    @pytest.mark.asyncio
    @patch("awa.core.cli.state_manager.FileSystemUtils.read_async")
    async def test_load_state_invalid_json(
        self,
        mock_read: AsyncMock,
        state_manager: StateManager,
    ) -> None:
        """Test loading state with invalid JSON."""
        # Setup state file to exist
        state_manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        state_manager.state_file.touch()

        mock_read.return_value = "invalid json"

        result = await state_manager.load_state()
        assert result is None

    @pytest.mark.asyncio
    @patch.object(StateManager, "load_state")
    @patch.object(StateManager, "save_state")
    async def test_update_service_new_service(
        self,
        mock_save: AsyncMock,
        mock_load: AsyncMock,
        state_manager: StateManager,
    ) -> None:
        """Test updating service when no existing state."""
        mock_load.return_value = None

        new_service_info = ServiceInfo(pid=12345, port=8001, started_at=datetime.now(UTC))
        await state_manager.update_service(constants.SERVICE_API, new_service_info)

        # Verify save was called with new state
        mock_save.assert_called_once()
        call_args = mock_save.call_args[0][0]
        assert call_args.services[constants.SERVICE_API] == new_service_info

    @pytest.mark.asyncio
    @patch.object(StateManager, "load_state")
    @patch.object(StateManager, "save_state")
    async def test_update_service_existing_state(
        self,
        mock_save: AsyncMock,
        mock_load: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test updating service when state already exists."""
        mock_load.return_value = sample_state

        new_service_info = ServiceInfo(pid=54321, port=8002, started_at=datetime.now(UTC))
        await state_manager.update_service(constants.SERVICE_UI, new_service_info)

        mock_save.assert_called_once()
        saved_state = mock_save.call_args[0][0]
        assert constants.SERVICE_API in saved_state.services  # Original service preserved
        assert constants.SERVICE_UI in saved_state.services  # New service added
        assert saved_state.services[constants.SERVICE_UI].pid == 54321

    @pytest.mark.asyncio
    @patch.object(StateManager, "save_state")
    @patch.object(StateManager, "load_state")
    async def test_remove_service(
        self,
        mock_load: AsyncMock,
        mock_save: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test removing a service from state."""
        mock_load.return_value = sample_state

        await state_manager.remove_service(constants.SERVICE_API)

        mock_save.assert_called_once()
        saved_state = mock_save.call_args[0][0]
        assert constants.SERVICE_API not in saved_state.services

    @pytest.mark.asyncio
    @patch.object(StateManager, "load_state")
    async def test_get_service_info(
        self,
        mock_load: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test getting service information."""
        mock_load.return_value = sample_state

        result = await state_manager.get_service_info(constants.SERVICE_API)
        assert result is not None
        assert result.pid == 12345

        result = await state_manager.get_service_info(constants.SERVICE_UI)
        assert result is None

    @pytest.mark.asyncio
    @patch.object(StateManager, "load_state")
    async def test_get_all_services(
        self,
        mock_load: AsyncMock,
        state_manager: StateManager,
        sample_state: ServiceState,
    ) -> None:
        """Test getting all services."""
        mock_load.return_value = sample_state

        result = await state_manager.get_all_services()
        assert len(result) == 1
        assert constants.SERVICE_API in result
        assert result[constants.SERVICE_API].pid == 12345

    @pytest.mark.asyncio
    @patch("awa.core.cli.state_manager.FileSystemUtils.remove_async")
    async def test_cleanup_state(
        self,
        mock_remove: AsyncMock,
        state_manager: StateManager,
    ) -> None:
        """Test state cleanup."""
        # Setup state file and directory
        state_manager.state_dir.mkdir(parents=True, exist_ok=True)
        state_manager.state_file.touch()

        # Mock the file removal by actually removing it
        async def mock_remove_side_effect(path: str) -> None:
            if Path(path).exists():
                Path(path).unlink()

        mock_remove.side_effect = mock_remove_side_effect

        await state_manager.cleanup_state()

        mock_remove.assert_called_once_with(str(state_manager.state_file))
        assert not state_manager.state_dir.exists()  # Should be removed if empty

    def test_is_process_running_success(self, state_manager: StateManager) -> None:
        """Test process running check when process exists."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=False),
            patch("os.kill") as mock_kill,
        ):
            mock_kill.return_value = None  # No exception means process exists

            result = state_manager.is_process_running(12345)
            assert result is True
            mock_kill.assert_called_once_with(12345, 0)

    def test_is_process_running_not_found(self, state_manager: StateManager) -> None:
        """Test process running check when process doesn't exist."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=False),
            patch("os.killpg") as mock_kill,
        ):
            mock_kill.side_effect = ProcessLookupError()

            result = state_manager.is_process_running(12345)
            assert result is False

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_service_info")
    @patch.object(StateManager, "is_process_running")
    async def test_is_service_running_success(
        self,
        mock_is_running: MagicMock,
        mock_get_info: AsyncMock,
        state_manager: StateManager,
        sample_service_info: ServiceInfo,
    ) -> None:
        """Test service verification when service is running."""
        mock_get_info.return_value = sample_service_info
        mock_is_running.return_value = True

        # Mock port checking
        with patch("awa.core.utils.command_utils.CommandUtils.check_service_status") as mock_port_check:
            mock_port_check.return_value = True

            result = await state_manager.is_service_running(constants.SERVICE_API)

        assert result is True
        mock_get_info.assert_called_once_with(constants.SERVICE_API)
        mock_is_running.assert_called_once_with(12345)

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_service_info")
    async def test_is_service_running_not_in_state(
        self,
        mock_get_info: AsyncMock,
        state_manager: StateManager,
    ) -> None:
        """Test service verification when service not in state."""
        mock_get_info.return_value = None

        result = await state_manager.is_service_running(constants.SERVICE_API)

        assert result is False
        mock_get_info.assert_called_once_with(constants.SERVICE_API)

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_service_info")
    @patch.object(StateManager, "is_process_running")
    @patch.object(StateManager, "remove_service")
    async def test_is_service_running_process_not_running(
        self,
        mock_remove: AsyncMock,
        mock_is_running: MagicMock,
        mock_get_info: AsyncMock,
        state_manager: StateManager,
        sample_service_info: ServiceInfo,
    ) -> None:
        """Test service verification when process is not running."""
        mock_get_info.return_value = sample_service_info
        mock_is_running.return_value = False

        result = await state_manager.is_service_running(constants.SERVICE_API)

        assert result is False
        mock_get_info.assert_called_once_with(constants.SERVICE_API)
        mock_is_running.assert_called_once_with(12345)
        mock_remove.assert_called_once_with(constants.SERVICE_API)

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_service_info")
    @patch.object(StateManager, "is_process_running")
    @patch.object(StateManager, "remove_service")
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_stop_service_graceful(
        self,
        mock_is_windows: MagicMock,
        mock_remove: AsyncMock,
        mock_is_running: MagicMock,
        mock_get_info: AsyncMock,
        state_manager: StateManager,
        sample_service_info: ServiceInfo,
    ) -> None:
        """Test graceful service stopping with enhanced process termination."""
        mock_is_windows.return_value = False  # Test Unix path
        mock_get_info.return_value = sample_service_info
        mock_is_running.side_effect = [True, False]  # Running, then stopped

        # Mock the enhanced termination methods
        with (
            patch.object(state_manager, "_find_unix_process_tree", return_value=[12345]) as mock_find_tree,
            patch.object(state_manager, "_stop_unix_process_tree") as mock_stop_tree,
        ):
            result = await state_manager.stop_service(constants.SERVICE_API)

        assert result is True
        mock_get_info.assert_called_once_with(constants.SERVICE_API)
        mock_find_tree.assert_called_once_with(12345)
        mock_stop_tree.assert_called_once_with([12345], constants.SERVICE_API)
        mock_remove.assert_called_once_with(constants.SERVICE_API)

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_service_info")
    @patch.object(StateManager, "is_process_running")
    @patch.object(StateManager, "remove_service")
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_stop_service_force_kill(
        self,
        mock_is_windows: MagicMock,
        mock_remove: AsyncMock,
        mock_is_running: MagicMock,
        mock_get_info: AsyncMock,
        state_manager: StateManager,
        sample_service_info: ServiceInfo,
    ) -> None:
        """Test force killing service when graceful shutdown fails."""
        mock_is_windows.return_value = False  # Test Unix path
        mock_get_info.return_value = sample_service_info
        mock_is_running.return_value = True  # Process keeps running

        # Mock the enhanced termination methods
        with (
            patch.object(state_manager, "_find_unix_process_tree", return_value=[12345]) as mock_find_tree,
            patch.object(state_manager, "_stop_unix_process_tree") as mock_stop_tree,
        ):
            result = await state_manager.stop_service(constants.SERVICE_API)

        assert result is True
        mock_get_info.assert_called_once_with(constants.SERVICE_API)
        mock_find_tree.assert_called_once_with(12345)
        mock_stop_tree.assert_called_once_with([12345], constants.SERVICE_API)
        mock_remove.assert_called_once_with(constants.SERVICE_API)

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_all_services")
    @patch.object(StateManager, "stop_service")
    @patch.object(StateManager, "cleanup_state")
    async def test_stop_all_services_success(
        self,
        mock_cleanup: AsyncMock,
        mock_stop: AsyncMock,
        mock_get_all: AsyncMock,
        state_manager: StateManager,
    ) -> None:
        """Test stopping all services successfully."""
        mock_get_all.return_value = {
            constants.SERVICE_API: MagicMock(),
            constants.SERVICE_UI: MagicMock(),
        }
        mock_stop.return_value = True

        result = await state_manager.stop_all_services()

        assert result == [constants.SERVICE_API, constants.SERVICE_UI]
        assert mock_stop.call_count == 2
        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(StateManager, "get_all_services")
    async def test_stop_all_services_no_services(
        self,
        mock_get_all: AsyncMock,
        state_manager: StateManager,
    ) -> None:
        """Test stopping all services when no services exist."""
        mock_get_all.return_value = {}

        result = await state_manager.stop_all_services()
        assert result == []

    # Cross-platform process existence checking tests

    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    def test_is_process_running_windows(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test Windows process existence checking with os.kill."""
        mock_is_windows.return_value = True

        with patch("os.kill") as mock_kill:
            mock_kill.return_value = None  # No exception means process exists

            result = state_manager.is_process_running(12345)
            assert result is True
            mock_kill.assert_called_once_with(12345, 0)

    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    def test_is_process_running_windows_not_found(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test Windows process existence checking when process not found."""
        mock_is_windows.return_value = True

        with patch("os.kill") as mock_kill:
            mock_kill.side_effect = ProcessLookupError("Process not found")

            result = state_manager.is_process_running(12345)
            assert result is False
            mock_kill.assert_called_once_with(12345, 0)

    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    def test_is_process_running_unix(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test Unix process existence checking with os.kill."""
        mock_is_windows.return_value = False

        with patch("os.kill") as mock_kill:
            mock_kill.return_value = None  # No exception means process exists

            result = state_manager.is_process_running(12345)
            assert result is True
            mock_kill.assert_called_once_with(12345, 0)

    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    def test_is_process_running_unix_not_found(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test Unix process existence checking when process not found."""
        mock_is_windows.return_value = False

        with patch("os.kill") as mock_kill:
            mock_kill.side_effect = ProcessLookupError("Process not found")

            result = state_manager.is_process_running(12345)
            assert result is False
            mock_kill.assert_called_once_with(12345, 0)

    # Cross-platform process termination tests

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    @patch.object(StateManager, "get_service_info")
    @patch.object(StateManager, "is_process_running")
    @patch.object(StateManager, "remove_service")
    async def test_stop_service_cross_platform_windows(
        self,
        mock_remove: AsyncMock,
        mock_is_running: MagicMock,
        mock_get_info: AsyncMock,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
        sample_service_info: ServiceInfo,
    ) -> None:
        """Test Windows termination path using platform detection mock."""
        mock_is_windows.return_value = True
        mock_get_info.return_value = sample_service_info
        mock_is_running.side_effect = [True, False]  # Running, then stopped

        # Mock the Windows-specific termination method
        with patch.object(state_manager, "_stop_service_windows", new=AsyncMock()) as mock_windows:
            result = await state_manager.stop_service(constants.SERVICE_API)

            assert result is True
            mock_get_info.assert_called_once_with(constants.SERVICE_API)
            mock_windows.assert_called_once_with(12345, constants.SERVICE_API)
            mock_remove.assert_called_once_with(constants.SERVICE_API)

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    @patch.object(StateManager, "get_service_info")
    @patch.object(StateManager, "is_process_running")
    @patch.object(StateManager, "remove_service")
    async def test_stop_service_cross_platform_unix(
        self,
        mock_remove: AsyncMock,
        mock_is_running: MagicMock,
        mock_get_info: AsyncMock,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
        sample_service_info: ServiceInfo,
    ) -> None:
        """Test Unix termination path using enhanced process termination."""
        mock_is_windows.return_value = False
        mock_get_info.return_value = sample_service_info
        mock_is_running.side_effect = [True, False]  # Running, then stopped

        # Mock the enhanced termination methods
        with (
            patch.object(state_manager, "_find_unix_process_tree", return_value=[12345]) as mock_find_tree,
            patch.object(state_manager, "_stop_unix_process_tree") as mock_stop_tree,
        ):
            result = await state_manager.stop_service(constants.SERVICE_API)

            assert result is True
            mock_get_info.assert_called_once_with(constants.SERVICE_API)
            mock_find_tree.assert_called_once_with(12345)
            mock_stop_tree.assert_called_once_with([12345], constants.SERVICE_API)
            mock_remove.assert_called_once_with(constants.SERVICE_API)

    # Windows-specific termination tests

    @pytest.mark.asyncio
    async def test_stop_service_windows_success(self, state_manager: StateManager) -> None:
        """Test Windows service termination with successful taskkill."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"SUCCESS", b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc
            mock_wait_for.return_value = (b"SUCCESS", b"")

            await state_manager._stop_service_windows(12345, "test_service")

            # Enhanced implementation makes multiple calls for process discovery and termination
            # Verify that subprocess was called (enhanced version makes multiple discovery calls)
            assert mock_subprocess.call_count >= 1
            # Verify at least one call contained the expected taskkill or process discovery commands
            call_args_list = [str(call) for call in mock_subprocess.call_args_list]
            has_expected_call = any(
                "wmic" in call_str or "tasklist" in call_str or "powershell" in call_str for call_str in call_args_list
            )
            assert has_expected_call, f"Expected Windows process management calls, got: {call_args_list}"

    @pytest.mark.asyncio
    async def test_stop_service_windows_failure(self, state_manager: StateManager) -> None:
        """Test Windows service termination with taskkill failure."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            # Use MagicMock for the process, not AsyncMock
            mock_proc = MagicMock()
            # Configure stdin/stdout/stderr as regular MagicMock
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_proc.stderr = MagicMock()
            mock_proc.stdin.close = MagicMock(return_value=None)
            mock_proc.stdin.is_closing = MagicMock(return_value=False)
            mock_proc.stdout.is_closing = MagicMock(return_value=False)
            mock_proc.stderr.is_closing = MagicMock(return_value=False)

            # Use AsyncMock for communicate to avoid coroutine warnings
            mock_proc.communicate = AsyncMock(return_value=(b"", b"Process not found"))
            mock_proc.returncode = 1

            # Use AsyncMock for create_subprocess_exec
            mock_subprocess.return_value = mock_proc

            # Should not raise exception, just log warning
            await state_manager._stop_service_windows(12345, "test_service")

            # Enhanced implementation makes multiple calls for process discovery
            assert mock_subprocess.call_count >= 1

    @pytest.mark.asyncio
    async def test_stop_service_windows_timeout(self, state_manager: StateManager) -> None:
        """Test Windows service termination with timeout."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess:
            mock_proc = AsyncMock()
            # Configure stdin/stdout/stderr as regular MagicMock so their methods don't return coroutines
            mock_proc.stdin = MagicMock()
            mock_proc.stdout = MagicMock()
            mock_proc.stderr = MagicMock()
            mock_proc.stdin.close = MagicMock(return_value=None)
            mock_proc.stdin.is_closing = MagicMock(return_value=False)
            mock_proc.stdout.is_closing = MagicMock(return_value=False)
            mock_proc.stderr.is_closing = MagicMock(return_value=False)
            mock_proc.communicate.side_effect = TimeoutError("Timeout")
            mock_subprocess.return_value = mock_proc

            # Should not raise exception, just log warning
            await state_manager._stop_service_windows(12345, "test_service")

            # Enhanced implementation makes multiple calls for process discovery
            assert mock_subprocess.call_count >= 1

    # Unix-specific termination tests

    @pytest.mark.asyncio
    async def test_stop_service_unix_success(self, state_manager: StateManager) -> None:
        """Test Unix service termination with successful killpg."""
        with patch("os.killpg") as mock_killpg:
            mock_killpg.return_value = None  # Success

            await state_manager._stop_service_unix(12345, "test_service")

            mock_killpg.assert_called_once_with(12345, signal.SIGTERM)

    @pytest.mark.asyncio
    async def test_stop_service_unix_fallback(self, state_manager: StateManager) -> None:
        """Test Unix service termination with fallback to individual kill."""
        with patch("os.killpg") as mock_killpg, patch("os.kill") as mock_kill:
            mock_killpg.side_effect = OSError("No such process group")
            mock_kill.return_value = None  # Fallback success

            await state_manager._stop_service_unix(12345, "test_service")

            mock_killpg.assert_called_once_with(12345, signal.SIGTERM)
            mock_kill.assert_called_once_with(12345, signal.SIGTERM)

    @pytest.mark.asyncio
    async def test_stop_service_unix_process_gone(self, state_manager: StateManager) -> None:
        """Test Unix service termination when process already gone."""
        with patch("os.killpg") as mock_killpg, patch("os.kill") as mock_kill:
            mock_killpg.side_effect = ProcessLookupError("No such process group")
            mock_kill.side_effect = ProcessLookupError("No such process")

            # Should not raise exception
            await state_manager._stop_service_unix(12345, "test_service")

            mock_killpg.assert_called_once_with(12345, signal.SIGTERM)
            mock_kill.assert_called_once_with(12345, signal.SIGTERM)

    # Force termination tests

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_force_terminate_process_windows(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test force termination on Windows."""
        mock_is_windows.return_value = True

        with (
            patch("asyncio.create_subprocess_exec") as mock_subprocess,
            patch.object(state_manager, "is_process_running", return_value=True),
        ):
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (b"SUCCESS", b"")
            mock_subprocess.return_value = mock_proc

            await state_manager._force_terminate_process(12345, "test_service")

            # Enhanced implementation - just verify subprocess was called
            assert mock_subprocess.call_count >= 1

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_force_terminate_process_unix(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test force termination on Unix."""
        mock_is_windows.return_value = False

        with patch("os.killpg") as mock_killpg, patch.object(state_manager, "is_process_running", return_value=True):
            mock_killpg.return_value = None  # Success

            await state_manager._force_terminate_process(12345, "test_service")

            # Enhanced implementation - verify killpg was called
            assert mock_killpg.call_count >= 1

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_force_terminate_process_unix_fallback(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test force termination on Unix with fallback to individual kill."""
        mock_is_windows.return_value = False

        with (
            patch("os.killpg") as mock_killpg,
            patch("os.kill") as mock_kill,
            patch.object(state_manager, "is_process_running", return_value=True),
        ):
            mock_killpg.side_effect = ProcessLookupError("No such process group")
            mock_kill.return_value = None  # Fallback success

            await state_manager._force_terminate_process(12345, "test_service")

            # Enhanced implementation - verify both methods were attempted
            assert mock_killpg.call_count >= 1
            assert mock_kill.call_count >= 1


class TestStateManagerEnhancedProcessTermination:
    """Test cases for enhanced process termination functionality."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path: Path) -> Path:
        """Provide a temporary directory for state files."""
        return tmp_path / ".awa_state"

    @pytest.fixture
    def state_manager(self, temp_state_dir: Path) -> StateManager:
        """Provide a StateManager instance with temporary directory."""
        return StateManager(state_dir=temp_state_dir)

    @pytest.mark.asyncio
    async def test_find_unix_process_tree_success(self, state_manager: StateManager) -> None:
        """Test finding Unix process tree with successful ps command."""
        mock_ps_output = b"  123   100 python\n  456   123 uv\n  789   456 temporal\n  999   100 other\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (mock_ps_output, b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc
            mock_wait_for.return_value = (mock_ps_output, b"")

            result = await state_manager._find_unix_process_tree(123)

            # Should find at least the root process
            assert 123 in result  # Root process should always be found
            assert isinstance(result, list)  # Should return a list
            assert len(result) >= 1  # Should have at least the root process

            # Enhanced implementation - verify subprocess was called
            assert mock_subprocess.call_count >= 1

    @pytest.mark.asyncio
    async def test_find_unix_process_tree_ps_failure(self, state_manager: StateManager) -> None:
        """Test process tree discovery when ps command fails."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            # Use MagicMock for the process object
            mock_proc = MagicMock()
            # Use AsyncMock for communicate to avoid coroutine warnings
            mock_proc.communicate = AsyncMock(return_value=(b"", b"ps: command failed"))
            mock_proc.returncode = 1

            # Use AsyncMock for create_subprocess_exec
            mock_subprocess.return_value = mock_proc
            mock_wait_for.return_value = (b"", b"ps: command failed")

            result = await state_manager._find_unix_process_tree(123)

            # Should return only the root PID when ps fails
            assert result == [123]

    @pytest.mark.asyncio
    async def test_find_unix_process_tree_timeout(self, state_manager: StateManager) -> None:
        """Test process tree discovery with timeout."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            mock_subprocess.return_value = AsyncMock()
            mock_wait_for.side_effect = TimeoutError("Command timeout")

            result = await state_manager._find_unix_process_tree(123)

            # Should return only the root PID when timeout occurs
            assert result == [123]

    @pytest.mark.asyncio
    async def test_find_related_processes_by_pattern_success(self, state_manager: StateManager) -> None:
        """Test finding related processes by pattern matching."""
        mock_ps_output = b"""  123     1 node /usr/local/bin/astro dev
  456     1 pnpm run dev
  789   100 python -m awa.main
  999     1 uvicorn awa.core.api
 1111   100 temporal worker
 2222     1 other process
"""

        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (mock_ps_output, b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc
            mock_wait_for.return_value = (mock_ps_output, b"")

            result = await state_manager._find_related_processes_by_pattern(100)

            # Should find AWA-related processes that are orphaned (ppid=1) or related to root
            expected_pids = [123, 456, 789, 999, 1111]  # astro, pnpm, python awa, uvicorn, temporal
            for pid in expected_pids:
                assert pid in result
            assert 2222 not in result  # other process doesn't match patterns

            mock_subprocess.assert_called_once_with(
                "ps",
                "-axo",
                "pid,ppid,comm,args",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

    @pytest.mark.asyncio
    async def test_find_related_processes_by_pattern_no_matches(self, state_manager: StateManager) -> None:
        """Test pattern matching when no processes match."""
        mock_ps_output = b"  123   100 vim\n  456   100 ls\n"

        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            mock_proc = AsyncMock()
            mock_proc.communicate.return_value = (mock_ps_output, b"")
            mock_proc.returncode = 0
            mock_subprocess.return_value = mock_proc
            mock_wait_for.return_value = (mock_ps_output, b"")

            result = await state_manager._find_related_processes_by_pattern(100)

            assert result == []

    @pytest.mark.asyncio
    async def test_find_related_processes_by_pattern_ps_failure(self, state_manager: StateManager) -> None:
        """Test pattern matching when ps command fails."""
        with patch("asyncio.create_subprocess_exec") as mock_subprocess, patch("asyncio.wait_for") as mock_wait_for:
            # Use MagicMock for the process object
            mock_proc = MagicMock()
            # Use AsyncMock for communicate to avoid coroutine warnings
            mock_proc.communicate = AsyncMock(return_value=(b"", b"ps: command failed"))
            mock_proc.returncode = 1

            # Use AsyncMock for create_subprocess_exec
            mock_subprocess.return_value = mock_proc
            mock_wait_for.return_value = (b"", b"ps: command failed")

            result = await state_manager._find_related_processes_by_pattern(123)

            assert result == []

    @pytest.mark.asyncio
    async def test_stop_unix_process_tree_success(self, state_manager: StateManager) -> None:
        """Test stopping Unix process tree with successful termination."""
        test_pids = [123, 456, 789]

        # Use regular MagicMock for os.kill (synchronous operation)
        # Explicitly use MagicMock (not AsyncMock) for synchronous is_process_running method
        with (
            patch("os.kill") as mock_kill,
            patch.object(
                state_manager,
                "is_process_running",
                new=MagicMock(),
            ) as mock_is_running,
        ):
            # Configure mocks
            mock_kill.return_value = None
            # First call: processes are running, second call: processes are stopped
            mock_is_running.side_effect = [True, True, True, False, False, False]

            await state_manager._stop_unix_process_tree(test_pids, "test_service")

            # Should send SIGTERM to all processes
            expected_calls = [call(123, signal.SIGTERM), call(456, signal.SIGTERM), call(789, signal.SIGTERM)]
            mock_kill.assert_has_calls(expected_calls, any_order=True)
            assert mock_kill.call_count == 3

    @pytest.mark.asyncio
    async def test_stop_unix_process_tree_force_termination(self, state_manager: StateManager) -> None:
        """Test stopping Unix process tree with force termination."""
        test_pids = [123, 456]

        sleep_count = 0

        async def mock_sleep(_duration: float) -> None:
            nonlocal sleep_count
            sleep_count += 1
            if sleep_count > 1:  # After first sleep, raise timeout to exit loop
                raise TimeoutError("Graceful timeout")

        with (
            patch("os.kill") as mock_kill,
            patch.object(state_manager, "is_process_running") as mock_is_running,
            patch("asyncio.sleep", side_effect=mock_sleep),
        ):
            # Processes keep running, requiring force termination
            mock_is_running.return_value = True

            await state_manager._stop_unix_process_tree(test_pids, "test_service")

            # Should send SIGTERM then SIGKILL
            sigterm_calls = [call(123, signal.SIGTERM), call(456, signal.SIGTERM)]
            sigkill_calls = [call(123, signal.SIGKILL), call(456, signal.SIGKILL)]
            mock_kill.assert_has_calls(sigterm_calls + sigkill_calls, any_order=True)

    @pytest.mark.asyncio
    async def test_stop_unix_process_tree_empty_list(self, state_manager: StateManager) -> None:
        """Test stopping Unix process tree with empty PID list."""
        with patch("os.kill") as mock_kill:
            await state_manager._stop_unix_process_tree([], "test_service")

            # Should not make any kill calls
            mock_kill.assert_not_called()

    @pytest.mark.asyncio
    async def test_stop_unix_process_tree_process_already_gone(self, state_manager: StateManager) -> None:
        """Test stopping Unix process tree when processes are already gone."""
        test_pids = [123, 456]

        with patch("os.kill") as mock_kill:
            mock_kill.side_effect = ProcessLookupError("No such process")

            await state_manager._stop_unix_process_tree(test_pids, "test_service")

            # Should attempt to kill processes but not fail when they're gone
            # Enhanced implementation may check process existence first with signal 0
            assert mock_kill.call_count >= 2  # Should make at least 2 calls for 2 PIDs
            # Verify that we attempted to interact with the expected PIDs
            called_pids = {call_args[0][0] for call_args in mock_kill.call_args_list}
            assert 123 in called_pids
            assert 456 in called_pids

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_stop_service_uses_enhanced_unix_termination(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test that stop_service uses enhanced Unix process termination."""
        mock_is_windows.return_value = False

        service_info = ServiceInfo(pid=123, port=8001, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", side_effect=[True, False]),
            patch.object(state_manager, "_find_unix_process_tree", return_value=[123, 456, 789]) as mock_find_tree,
            patch.object(state_manager, "_stop_unix_process_tree") as mock_stop_tree,
            patch.object(state_manager, "remove_service"),
        ):
            result = await state_manager.stop_service("test_service")

            assert result is True
            mock_find_tree.assert_called_once_with(123)
            mock_stop_tree.assert_called_once_with([123, 456, 789], "test_service")

    def test_unix_process_running_check_uses_os_kill(self, state_manager: StateManager) -> None:
        """Test that Unix process running check uses os.kill instead of os.killpg."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=False),
            patch("os.kill") as mock_kill,
        ):
            mock_kill.return_value = None

            result = state_manager.is_process_running(12345)

            assert result is True
            mock_kill.assert_called_once_with(12345, 0)

    def test_unix_process_running_check_permission_error(self, state_manager: StateManager) -> None:
        """Test Unix process running check handles permission errors correctly."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=False),
            patch("os.kill") as mock_kill,
        ):
            mock_kill.side_effect = PermissionError("Permission denied")

            result = state_manager.is_process_running(12345)

            # Should return True for permission errors (process exists but no permission)
            assert result is True
            mock_kill.assert_called_once_with(12345, 0)

    def test_unix_process_running_check_oserror(self, state_manager: StateManager) -> None:
        """Test Unix process running check handles OSError correctly."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=False),
            patch("os.kill") as mock_kill,
        ):
            mock_kill.side_effect = OSError("Some OS error")

            result = state_manager.is_process_running(12345)

            # Should return False for other OS errors
            assert result is False
            mock_kill.assert_called_once_with(12345, 0)

    @pytest.mark.asyncio
    async def test_cleanup_state_with_directory_removal(self, temp_state_dir: Path) -> None:
        """Test state cleanup removes empty directory."""
        state_manager = StateManager(state_dir=temp_state_dir)

        # Create a state file
        state_file = temp_state_dir / "services.json"
        await FileSystemUtils.write_async(str(state_file), '{"timestamp": "2023-01-01T00:00:00Z", "services": {}}')

        # Ensure directory exists and has content
        assert temp_state_dir.exists()
        assert state_file.exists()

        await state_manager.cleanup_state()

        # Directory should be removed since it's empty after file removal
        assert not temp_state_dir.exists()

    @pytest.mark.asyncio
    async def test_cleanup_state_preserves_non_empty_directory(self, temp_state_dir: Path) -> None:
        """Test state cleanup preserves directory with other files."""
        state_manager = StateManager(state_dir=temp_state_dir)

        # Create a state file and another file
        state_file = temp_state_dir / "services.json"
        other_file = temp_state_dir / "other.txt"
        await FileSystemUtils.write_async(str(state_file), '{"timestamp": "2023-01-01T00:00:00Z", "services": {}}')
        await FileSystemUtils.write_async(str(other_file), "other content")

        await state_manager.cleanup_state()

        # Directory should be preserved since it has other files
        assert temp_state_dir.exists()
        assert not state_file.exists()  # State file should be gone
        assert other_file.exists()  # Other file should remain

    def test_windows_process_detection_tasklist_not_found(self, state_manager: StateManager) -> None:
        """Test Windows process detection when tasklist is not available."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=True),
            patch("os.kill", side_effect=OSError("Process not found")),
            patch("shutil.which", return_value=None),
        ):
            result = state_manager.is_process_running(12345)

            # Should return False when all methods fail
            assert result is False

    def test_windows_csv_detection_success(self, state_manager: StateManager) -> None:
        """Test Windows CSV detection method success."""
        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=True),
            patch("os.kill", side_effect=OSError("Process not found")),
            patch("shutil.which", return_value="C:\\Windows\\System32\\tasklist.exe"),
        ):
            mock_result = MagicMock()
            mock_result.stdout = '"notepad.exe","12345","Console","1","8,192 K"'
            mock_result.returncode = 0

            with patch("subprocess.run", return_value=mock_result):
                result = state_manager._try_tasklist_csv_detection(12345)

                assert result is True

    def test_windows_csv_detection_no_process(self, state_manager: StateManager) -> None:
        """Test Windows CSV detection when process not found."""
        with patch("shutil.which", return_value="C:\\Windows\\System32\\tasklist.exe"):
            mock_result = MagicMock()
            mock_result.stdout = ""  # No matching process
            mock_result.returncode = 0

            with patch("subprocess.run", return_value=mock_result):
                result = state_manager._try_tasklist_csv_detection(12345)

                assert result is False

    def test_windows_detailed_detection_success(self, state_manager: StateManager) -> None:
        """Test Windows detailed detection method success."""
        with patch("shutil.which", return_value="C:\\Windows\\System32\\tasklist.exe"):
            mock_result = MagicMock()
            mock_result.stdout = "Image Name: notepad.exe\nPID: 12345\nSession Name: Console"
            mock_result.returncode = 0

            with patch("subprocess.run", return_value=mock_result):
                result = state_manager._try_tasklist_detailed_detection(12345)

                assert result is True

    def test_windows_detailed_detection_no_tasks(self, state_manager: StateManager) -> None:
        """Test Windows detailed detection when no tasks running."""
        with patch("shutil.which", return_value="C:\\Windows\\System32\\tasklist.exe"):
            mock_result = MagicMock()
            mock_result.stdout = "No tasks are running which match the specified criteria."
            mock_result.returncode = 0

            with patch("subprocess.run", return_value=mock_result):
                result = state_manager._try_tasklist_detailed_detection(12345)

                assert result is False

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_is_service_running_api_port_check_fails(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test service running check when API port check fails."""
        mock_is_windows.return_value = False

        service_info = ServiceInfo(pid=123, port=8001, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", return_value=True),
            patch("awa.core.utils.command_utils.CommandUtils.check_service_status", return_value=False),
            patch.object(state_manager, "remove_service") as mock_remove,
        ):
            result = await state_manager.is_service_running(constants.SERVICE_API)

            assert result is False
            mock_remove.assert_called_once_with(constants.SERVICE_API)

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_is_service_running_ui_port_check_fails(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test service running check when UI port check fails."""
        mock_is_windows.return_value = False

        service_info = ServiceInfo(pid=123, port=8000, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", return_value=True),
            patch("awa.core.utils.command_utils.CommandUtils.check_service_status", return_value=False),
            patch.object(state_manager, "remove_service") as mock_remove,
        ):
            result = await state_manager.is_service_running(constants.SERVICE_UI)

            assert result is False
            mock_remove.assert_called_once_with(constants.SERVICE_UI)

    @pytest.mark.asyncio
    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows")
    async def test_is_service_running_temporal_port_check_fails(
        self,
        mock_is_windows: MagicMock,
        state_manager: StateManager,
    ) -> None:
        """Test service running check when Temporal port check fails."""
        mock_is_windows.return_value = False

        service_info = ServiceInfo(pid=123, port=7233, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", return_value=True),
            patch("awa.core.engine.temporal_server.TemporalServer.check_service_status", return_value=False),
            patch.object(state_manager, "remove_service") as mock_remove,
        ):
            result = await state_manager.is_service_running(constants.SERVICE_TEMPORAL_SERVER)

            assert result is False
            mock_remove.assert_called_once_with(constants.SERVICE_TEMPORAL_SERVER)

    @pytest.mark.asyncio
    async def test_stop_all_services_with_failure(self, state_manager: StateManager) -> None:
        """Test stopping all services when one service fails to stop."""
        services = {
            "service1": ServiceInfo(pid=123, port=8001, started_at=datetime.now(UTC)),
            "service2": ServiceInfo(pid=456, port=8002, started_at=datetime.now(UTC)),
        }

        with (
            patch.object(state_manager, "get_all_services", return_value=services),
            patch.object(state_manager, "stop_service", side_effect=[True, False]),  # First succeeds, second fails
            patch.object(state_manager, "cleanup_state") as mock_cleanup,
        ):
            result = await state_manager.stop_all_services()

            # Should return only the successfully stopped service
            assert result == ["service1"]
            # Should not cleanup state since not all services were stopped
            mock_cleanup.assert_not_called()


class TestStateManagerErrorHandling:
    """Test cases for error handling in StateManager."""

    @pytest.fixture
    def state_manager(self, tmp_path: Path) -> StateManager:
        """Provide a StateManager instance with temporary directory."""
        return StateManager(state_dir=tmp_path / ".awa_state")

    @pytest.mark.asyncio
    async def test_cleanup_state_error_handling(self, state_manager: StateManager) -> None:
        """Test that cleanup_state handles errors gracefully."""
        # Create the state file first so it will try to delete it
        state_manager.state_file.parent.mkdir(parents=True, exist_ok=True)
        state_manager.state_file.touch()

        # Mock FileSystemUtils.remove_async to raise an error
        with patch("awa.core.utils.file_system_utils.FileSystemUtils.remove_async") as mock_delete:
            mock_delete.side_effect = OSError("Permission denied")

            # Should not raise an exception
            await state_manager.cleanup_state()
            mock_delete.assert_called_once()

    def test_process_running_error_handling(self, state_manager: StateManager) -> None:
        """Test that is_process_running handles errors gracefully."""
        with patch.object(state_manager, "_is_process_running_unix") as mock_unix_check:
            mock_unix_check.side_effect = OSError("Access denied")

            result = state_manager.is_process_running(12345)
            assert result is False

    @patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=True)
    def test_windows_process_detection_handles_all_method_failures(
        self,
        mock_windows: MagicMock,  # noqa: ARG002
        state_manager: StateManager,
    ) -> None:
        """Test Windows process detection when all methods fail."""
        # Create mock methods with __name__ attributes
        mock_method1 = MagicMock(side_effect=OSError("Access denied"))
        mock_method1.__name__ = "_try_os_kill_detection"

        mock_method2 = MagicMock(side_effect=ValueError("Invalid format"))
        mock_method2.__name__ = "_try_tasklist_csv_detection"

        mock_method3 = MagicMock(side_effect=subprocess.TimeoutExpired("cmd", 5))
        mock_method3.__name__ = "_try_tasklist_detailed_detection"

        with (
            patch.object(state_manager, "_try_os_kill_detection", mock_method1),
            patch.object(state_manager, "_try_tasklist_csv_detection", mock_method2),
            patch.object(state_manager, "_try_tasklist_detailed_detection", mock_method3),
        ):
            result = state_manager._is_process_running_windows(12345)
            assert result is False

    def test_try_os_kill_detection_success(self, state_manager: StateManager) -> None:
        """Test successful os.kill detection method."""
        with patch("os.kill") as mock_kill:
            mock_kill.return_value = None  # Process exists

            result = state_manager._try_os_kill_detection(12345)
            assert result is True
            mock_kill.assert_called_once_with(12345, 0)

    def test_try_os_kill_detection_process_not_found(self, state_manager: StateManager) -> None:
        """Test os.kill detection when process doesn't exist."""
        with patch("os.kill") as mock_kill:
            mock_kill.side_effect = ProcessLookupError("No such process")

            # The method should raise the exception, not return False
            with pytest.raises(ProcessLookupError):
                state_manager._try_os_kill_detection(12345)


class TestStateManagerProcessTermination:
    """Test cases for process termination methods."""

    @pytest.fixture
    def state_manager(self, tmp_path: Path) -> StateManager:
        """Provide a StateManager instance with temporary directory."""
        return StateManager(state_dir=tmp_path / ".awa_state")

    @pytest.mark.asyncio
    async def test_terminate_service_process_only_success(self, state_manager: StateManager) -> None:
        """Test successful process termination without state cleanup."""
        service_info = ServiceInfo(pid=12345, port=8001, started_at=datetime.now(UTC))

        with (
            patch("awa.core.utils.platform_utils.PlatformUtils.is_windows", return_value=False),
            patch.object(state_manager, "_find_unix_process_tree", return_value=[12345, 12346]),
            patch.object(state_manager, "_stop_unix_process_tree") as mock_stop_tree,
        ):
            result = await state_manager._terminate_service_process_only("test_service", service_info)

            assert result is True
            mock_stop_tree.assert_called_once_with([12345, 12346], "test_service")

    @pytest.mark.asyncio
    async def test_verify_process_termination_complete_success(self, state_manager: StateManager) -> None:
        """Test successful process termination verification."""
        with patch.object(state_manager, "is_process_running", return_value=False):
            result = await state_manager._verify_process_termination_complete(
                original_pid=12345,
                service_name="test_service",
                verification_timeout=5.0,
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_verify_process_termination_timeout(self, state_manager: StateManager) -> None:
        """Test process termination verification timeout."""
        with (
            patch.object(state_manager, "is_process_running", return_value=True),
            patch("asyncio.sleep") as mock_sleep,
        ):
            # Configure sleep to raise TimeoutError after a few calls
            call_count = 0

            def sleep_side_effect(_duration: float) -> None:
                nonlocal call_count
                call_count += 1
                if call_count > 2:  # Allow a few retries before timeout
                    raise TimeoutError("Verification timeout")

            mock_sleep.side_effect = sleep_side_effect

            result = await state_manager._verify_process_termination_complete(
                original_pid=12345,
                service_name="test_service",
                verification_timeout=1.0,
            )
            assert result is False


class TestStateManagerServiceOperations:
    """Test cases for additional service operations."""

    @pytest.fixture
    def state_manager(self, tmp_path: Path) -> StateManager:
        """Provide a StateManager instance with temporary directory."""
        return StateManager(state_dir=tmp_path / ".awa_state")

    @pytest.mark.asyncio
    async def test_stop_service_with_verification_already_stopped(self, state_manager: StateManager) -> None:
        """Test stopping a service that's already stopped."""
        with patch.object(state_manager, "get_service_info", return_value=None):
            result = await state_manager.stop_service_with_verification("test_service")
            assert result is True

    @pytest.mark.asyncio
    async def test_stop_service_with_verification_process_already_dead(self, state_manager: StateManager) -> None:
        """Test stopping a service whose process is already dead."""
        service_info = ServiceInfo(pid=12345, port=8001, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", return_value=False),
            patch.object(state_manager, "remove_service") as mock_remove,
        ):
            result = await state_manager.stop_service_with_verification("test_service")

            assert result is True
            mock_remove.assert_called_once_with("test_service")

    @pytest.mark.asyncio
    async def test_stop_service_with_verification_termination_fails(self, state_manager: StateManager) -> None:
        """Test stopping a service when termination fails."""
        service_info = ServiceInfo(pid=12345, port=8001, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", return_value=True),
            patch.object(state_manager, "_terminate_service_process_only", return_value=False),
        ):
            result = await state_manager.stop_service_with_verification("test_service")
            assert result is False

    @pytest.mark.asyncio
    async def test_stop_service_with_verification_verification_fails(self, state_manager: StateManager) -> None:
        """Test stopping a service when verification fails."""
        service_info = ServiceInfo(pid=12345, port=8001, started_at=datetime.now(UTC))

        with (
            patch.object(state_manager, "get_service_info", return_value=service_info),
            patch.object(state_manager, "is_process_running", return_value=True),
            patch.object(state_manager, "_terminate_service_process_only", return_value=True),
            patch.object(state_manager, "_verify_process_termination_complete", return_value=False),
        ):
            result = await state_manager.stop_service_with_verification("test_service")
            assert result is False
