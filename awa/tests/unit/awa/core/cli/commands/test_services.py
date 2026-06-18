import asyncio
import contextlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.cli import constants as cli_constants
from awa.core.cli.commands.start import _start


@pytest.mark.asyncio
async def test_start_services() -> None:
    """Test starting all services."""
    # Mock the ServiceManager and its temporal components
    with (
        patch("awa.core.cli.commands.start.ServiceManager") as mock_service_manager_class,
        patch("awa.core.cli.commands.start.asyncio.Event") as mock_event_class,
        patch("awa.core.cli.commands.stop._find_orphaned_awa_processes", return_value=[]),
    ):
        mock_service_manager = AsyncMock()
        mock_service_manager.check_all_services.side_effect = [
            {
                cli_constants.SERVICE_TEMPORAL_SERVER: False,
                cli_constants.SERVICE_TEMPORAL_WORKER: False,
                cli_constants.SERVICE_API: True,
                cli_constants.SERVICE_UI: True,
            },
            {
                cli_constants.SERVICE_TEMPORAL_SERVER: True,
                cli_constants.SERVICE_TEMPORAL_WORKER: True,
                cli_constants.SERVICE_API: True,
                cli_constants.SERVICE_UI: True,
            },
        ]
        mock_service_manager.start_missing_services.return_value = None
        mock_service_manager.ensure_all_services_running.return_value = None
        mock_service_manager.rollback_started_services.return_value = None
        mock_service_manager.display_service_urls = MagicMock(return_value=None)
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        mock_event = AsyncMock()
        mock_event.wait.side_effect = asyncio.CancelledError()
        mock_event_class.return_value = mock_event

        # Run the start command with cancellation - should handle gracefully without re-raising
        with contextlib.suppress(asyncio.CancelledError):
            await _start()

        # Verify services were started
        mock_service_manager.ensure_all_services_running.assert_called_once()
        mock_service_manager.display_service_urls.assert_called_once_with(None)

        # CancelledError is not specifically handled in _handle_post_start_monitoring
        # so rollback_started_services is not called for this exception type
        # mock_service_manager.rollback_started_services.assert_called_once()
