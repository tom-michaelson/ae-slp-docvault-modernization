"""Unit tests for status command."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer

from awa.core.cli.commands.status import _status


class TestStatusCommand:
    """Test cases for status CLI command."""

    @pytest.fixture
    def mock_service_manager(self) -> MagicMock:
        """Create a mock service manager."""
        manager = MagicMock()
        manager.check_all_services = AsyncMock()
        return manager

    @pytest.mark.asyncio
    async def test_status_all_services_running(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test status command when all services are running."""
        # Mock all services as running
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": True,
            "temporal_worker": True,
            "api": True,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            await _status(services=None)

        # Verify all services were checked
        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_some_services_stopped(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test status command when some services are stopped."""
        # Mock some services as stopped
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": False,
            "temporal_worker": False,
            "api": True,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            # Expect the command to exit with code 1 when services are stopped
            with pytest.raises(typer.Exit) as exc_info:
                await _status(services=None)
            assert exc_info.value.exit_code == 1

        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_specific_services_all_running(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test status command with specific services all running."""
        # Mock all services status
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": True,
            "temporal_worker": True,
            "api": True,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            await _status(services="api,ui")

        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_specific_services_some_stopped(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test status command with specific services some stopped."""
        # Mock all services status
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": True,
            "temporal_worker": True,
            "api": False,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            # Expect the command to exit with code 1 when some requested services are stopped
            with pytest.raises(typer.Exit) as exc_info:
                await _status(services="api,ui")
            assert exc_info.value.exit_code == 1

        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_single_service_running(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test status command with single service running."""
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": True,
            "temporal_worker": True,
            "api": True,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            await _status(services="api")

        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_single_service_stopped(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test status command with single service stopped."""
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": True,
            "temporal_worker": True,
            "api": False,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            # Expect the command to exit with code 1 when the requested service is stopped
            with pytest.raises(typer.Exit) as exc_info:
                await _status(services="api")
            assert exc_info.value.exit_code == 1

        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_calls_service_manager_correctly(
        self,
        mock_service_manager: MagicMock,
    ) -> None:
        """Test that status command calls service manager with correct parameters."""
        mock_service_manager.check_all_services.return_value = {
            "temporal_server": True,
            "temporal_worker": True,
            "api": True,
            "ui": True,
        }

        with patch("awa.core.cli.commands.status.ServiceManager.create", return_value=mock_service_manager):
            await _status(services=None)

        mock_service_manager.check_all_services.assert_called_once()

    @pytest.mark.asyncio
    async def test_status_invalid_service_raises_error(self) -> None:
        """Test that invalid service name raises typer.Exit."""
        with pytest.raises(typer.Exit):
            await _status(services="invalid_service")

    @pytest.mark.asyncio
    async def test_status_empty_service_string_raises_error(self) -> None:
        """Test that empty service string raises typer.Exit."""
        with pytest.raises(typer.Exit):
            await _status(services="")

    @pytest.mark.asyncio
    async def test_status_whitespace_only_service_string_raises_error(self) -> None:
        """Test that whitespace-only service string raises typer.Exit."""
        with pytest.raises(typer.Exit):
            await _status(services="   ")
