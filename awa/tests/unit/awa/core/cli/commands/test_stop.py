"""Unit tests for the stop CLI command."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer.testing

from awa.core.cli.commands.stop import _stop, app
from awa.core.cli.state_manager import StateManager  # noqa: F401
from awa.core.models.cli.service_state import ServiceInfo, ServiceState


class TestStopCommand:
    """Test cases for stop CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = typer.testing.CliRunner()

    @patch("awa.core.cli.commands.stop.asyncio.run")
    @patch("awa.core.cli.commands.stop.init_logging")
    def test_stop_command(
        self,
        mock_init_logging: MagicMock,
        mock_asyncio_run: MagicMock,
    ) -> None:
        """Test the stop command execution."""
        # Arrange
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        # Act
        result = self.runner.invoke(app, ["stop"])

        # Assert
        assert result.exit_code == 0
        mock_init_logging.assert_called_once_with()
        mock_asyncio_run.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_async_no_services(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test _stop async function when no services are running."""
    # Arrange
    mock_state_manager = MagicMock()
    mock_state_manager.load_state = AsyncMock(return_value=None)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop()

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # No stop_service calls since no services exist


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_async_empty_services(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test _stop async function when state exists but no services are tracked."""
    # Arrange
    mock_state_manager = MagicMock()
    empty_state = ServiceState(timestamp=datetime.now(UTC), services={})
    mock_state_manager.load_state = AsyncMock(return_value=empty_state)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop()

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # No stop_service calls since no services exist


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_async_with_services(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test _stop async function when services need to be stopped."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "temporal_server": ServiceInfo(pid=1234, port=7233, started_at=now),
            "api": ServiceInfo(pid=5678, port=8000, started_at=now),
            "ui": ServiceInfo(pid=9012, port=4321, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    # Simulate service removal after first stop attempt - return None during verification
    service_lookup_calls = 0

    def mock_get_service_info(name: str) -> ServiceInfo | None:
        nonlocal service_lookup_calls
        service_lookup_calls += 1
        # Return service info on first call (before stop), None on subsequent calls (after stop)
        if service_lookup_calls % 2 == 1:  # Odd calls (before stop)
            return service_state.services.get(name)
        # Even calls (verification after stop)
        return None

    mock_state_manager.get_service_info = AsyncMock(side_effect=mock_get_service_info)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"temporal_server": True, "api": True, "ui": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=False)
    mock_state_manager.is_service_running = AsyncMock(return_value=False)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(
        return_value={
            "temporal_server": True,
            "api": True,
            "ui": True,
        },
    )
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop()

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should call stop_service_with_verification for each service (exactly once each since verification passes)
    assert mock_state_manager.stop_service_with_verification.call_count == 3
    called_services = [call[0][0] for call in mock_state_manager.stop_service_with_verification.call_args_list]
    assert set(called_services) == {"temporal_server", "api", "ui"}


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_async_no_services_stopped(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test _stop async function when services are tracked but none were actually stopped."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "temporal_server": ServiceInfo(pid=1234, port=7233, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    mock_state_manager.get_service_info = AsyncMock(side_effect=lambda name: service_state.services.get(name))
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=False)  # Service stop failed
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=False)
    mock_state_manager.check_all_services = AsyncMock(return_value={"temporal_server": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=True)  # Still running
    mock_state_manager.is_service_running = AsyncMock(return_value=True)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager - service is unhealthy since PID exists but health check fails
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"temporal_server": False})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop()

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should retry 3 times due to failure, so expect 3 calls
    assert mock_state_manager.stop_service_with_verification_aggressive.call_count == 3
    # All calls should be for the same service
    for call_args in mock_state_manager.stop_service_with_verification_aggressive.call_args_list:
        assert call_args[0][0] == "temporal_server"


# Tests for --services option functionality
@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_specific_services(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop command with specific services."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "temporal_server": ServiceInfo(pid=1234, port=7233, started_at=now),
            "temporal_worker": ServiceInfo(pid=5678, port=0, started_at=now),
            "api": ServiceInfo(pid=9012, port=8000, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    # Simulate successful service removal after first call
    service_lookup_calls = 0

    def mock_get_service_info(name: str) -> ServiceInfo | None:
        nonlocal service_lookup_calls
        service_lookup_calls += 1
        if service_lookup_calls % 2 == 1:  # Odd calls (before stop)
            return service_state.services.get(name)
        # Even calls (verification after stop)
        return None

    mock_state_manager.get_service_info = AsyncMock(side_effect=mock_get_service_info)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True, "temporal_server": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=False)
    mock_state_manager.is_service_running = AsyncMock(return_value=False)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(
        return_value={
            "api": True,
            "temporal_server": True,
        },
    )
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api,temporal_server")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should stop only specified services (each called once since verification succeeds)
    assert mock_state_manager.stop_service_with_verification.call_count == 2
    called_services = [call[0][0] for call in mock_state_manager.stop_service_with_verification.call_args_list]
    assert set(called_services) == {"api", "temporal_server"}


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_single_service(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop command with single service."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "temporal_server": ServiceInfo(pid=1234, port=7233, started_at=now),
            "api": ServiceInfo(pid=9012, port=8000, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    # Simulate successful service removal after first call
    service_lookup_calls = 0

    def mock_get_service_info(name: str) -> ServiceInfo | None:
        nonlocal service_lookup_calls
        service_lookup_calls += 1
        if service_lookup_calls % 2 == 1:  # Odd calls (before stop)
            return service_state.services.get(name)
        # Even calls (verification after stop)
        return None

    mock_state_manager.get_service_info = AsyncMock(side_effect=mock_get_service_info)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=False)
    mock_state_manager.is_service_running = AsyncMock(return_value=False)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should stop only the specified service (once since verification succeeds)
    mock_state_manager.stop_service_with_verification.assert_called_once_with("api")


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_services_not_in_state(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop command when requested services are not in state."""
    # Arrange
    mock_state_manager = MagicMock()
    empty_state = ServiceState(timestamp=datetime.now(UTC), services={})
    mock_state_manager.load_state = AsyncMock(return_value=empty_state)
    mock_state_manager.get_service_info = AsyncMock(return_value=None)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=False)
    mock_state_manager.is_service_running = AsyncMock(return_value=False)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api,ui")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should not call stop_service_with_verification since services not in state
    mock_state_manager.stop_service_with_verification.assert_not_called()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_mixed_services_some_in_state(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop command with mix of services in and not in state."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "api": ServiceInfo(pid=9012, port=8000, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    # Simulate successful service removal after first call
    service_lookup_calls = 0

    def mock_get_service_info(name: str) -> ServiceInfo | None:
        nonlocal service_lookup_calls
        service_lookup_calls += 1
        if service_lookup_calls % 2 == 1:  # Odd calls (before stop)
            return service_state.services.get(name)
        # Even calls (verification after stop)
        return None

    mock_state_manager.get_service_info = AsyncMock(side_effect=mock_get_service_info)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=False)
    mock_state_manager.is_service_running = AsyncMock(return_value=False)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api,ui,temporal_server")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should stop only services that are in state
    mock_state_manager.stop_service_with_verification.assert_called_once_with("api")


@pytest.mark.asyncio
async def test_stop_invalid_service_raises_error() -> None:
    """Test that invalid service name raises typer.Exit."""
    with pytest.raises(typer.Exit):
        await _stop(services="invalid_service")


@pytest.mark.asyncio
async def test_stop_empty_service_string_raises_error() -> None:
    """Test that empty service string raises typer.Exit."""
    with pytest.raises(typer.Exit):
        await _stop(services="")


@pytest.mark.asyncio
async def test_stop_whitespace_only_service_string_raises_error() -> None:
    """Test that whitespace-only service string raises typer.Exit."""
    with pytest.raises(typer.Exit):
        await _stop(services="   ")


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_duplicate_services_handled(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test that duplicate services in the list are handled correctly."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "api": ServiceInfo(pid=9012, port=8000, started_at=now),
            "ui": ServiceInfo(pid=1234, port=4321, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    # Simulate successful service removal after first call
    service_lookup_calls = 0

    def mock_get_service_info(name: str) -> ServiceInfo | None:
        nonlocal service_lookup_calls
        service_lookup_calls += 1
        if service_lookup_calls % 2 == 1:  # Odd calls (before stop)
            return service_state.services.get(name)
        # Even calls (verification after stop)
        return None

    mock_state_manager.get_service_info = AsyncMock(side_effect=mock_get_service_info)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True, "ui": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager.is_process_running = MagicMock(return_value=False)
    mock_state_manager.is_service_running = AsyncMock(return_value=False)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"api": True, "ui": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api,ui,api")  # api is duplicated

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should stop each service only once despite duplicates
    assert mock_state_manager.stop_service_with_verification.call_count == 2
    called_services = [call[0][0] for call in mock_state_manager.stop_service_with_verification.call_args_list]
    assert set(called_services) == {"api", "ui"}


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_async_services_not_running(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test _stop async function when requested services are not running."""
    # Arrange
    mock_state_manager = MagicMock()
    service_state = ServiceState(
        timestamp=datetime.now(UTC),
        services={
            "temporal_server": ServiceInfo(pid=1234, port=7233, started_at=datetime.now(UTC)),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"temporal_server": True})
    mock_state_manager.cleanup_state = AsyncMock()
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"temporal_server": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act - request services that aren't running
    await _stop(services="api,ui")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should not call stop_service_with_verification since services aren't running
    mock_state_manager.stop_service_with_verification.assert_not_called()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_with_verification_partial_success(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop operation where service stops but verification is incomplete."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "api": ServiceInfo(pid=1234, port=8001, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)

    # Mock service info lookup - service exists initially, then gets removed
    call_count = 0

    def mock_get_service_info(name: str) -> ServiceInfo | None:
        nonlocal call_count
        call_count += 1
        if call_count == 1:  # Before stop
            return service_state.services.get(name)
        # After stop - service removed but verification incomplete
        return None

    mock_state_manager.get_service_info = AsyncMock(side_effect=mock_get_service_info)
    mock_state_manager.stop_service_with_verification = AsyncMock(return_value=True)
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_state_manager.cleanup_state = AsyncMock()
    # Mock process still running (partial success)
    mock_state_manager.is_process_running = MagicMock(return_value=True)
    mock_state_manager.is_service_running = AsyncMock(return_value=True)
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    mock_state_manager.stop_service_with_verification.assert_called_once()


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_with_timeout_error(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop operation that times out."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "api": ServiceInfo(pid=1234, port=8001, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    mock_state_manager.get_service_info = AsyncMock(side_effect=lambda name: service_state.services.get(name))
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_state_manager.cleanup_state = AsyncMock()

    # Mock stop operation to raise TimeoutError
    mock_state_manager.stop_service_with_verification = AsyncMock(side_effect=TimeoutError("Operation timed out"))
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act
    await _stop(services="api")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    # Should call stop multiple times due to retry logic (3 attempts)
    assert mock_state_manager.stop_service_with_verification.call_count == 3


@pytest.mark.asyncio
@patch("awa.core.cli.commands.stop.StateManager")
@patch("awa.core.cli.commands.stop.ServiceManager.create")
async def test_stop_operation_general_exception(
    mock_service_manager_create: AsyncMock,
    mock_state_manager_class: MagicMock,
) -> None:
    """Test stop operation that encounters a general exception."""
    # Arrange
    mock_state_manager = MagicMock()
    now = datetime.now(UTC)
    service_state = ServiceState(
        timestamp=now,
        services={
            "api": ServiceInfo(pid=1234, port=8001, started_at=now),
        },
    )
    mock_state_manager.load_state = AsyncMock(return_value=service_state)
    mock_state_manager.get_service_info = AsyncMock(side_effect=lambda name: service_state.services.get(name))
    mock_state_manager.stop_service_with_verification_aggressive = AsyncMock(return_value=True)
    mock_state_manager.check_all_services = AsyncMock(return_value={"api": True})

    # Mock cleanup_state for emergency cleanup
    mock_state_manager.cleanup_state = AsyncMock()

    # Mock stop operation to raise a general exception
    mock_state_manager.stop_service_with_verification = AsyncMock(side_effect=Exception("Unexpected error"))
    mock_state_manager_class.return_value = mock_state_manager

    # Mock ServiceManager
    mock_service_manager = MagicMock()
    mock_service_manager.check_all_services = AsyncMock(return_value={"api": True})
    mock_service_manager_create.return_value = mock_service_manager

    # Act & Assert - Should raise exception on first attempt
    with pytest.raises(Exception, match="Unexpected error"):
        await _stop(services="api")

    # Assert
    mock_state_manager.load_state.assert_called_once()
    mock_state_manager.stop_service_with_verification.assert_called_once()
