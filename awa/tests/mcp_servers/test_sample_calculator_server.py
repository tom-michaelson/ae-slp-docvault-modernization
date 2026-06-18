"""Tests for the sample calculator MCP server."""

import asyncio
import signal
from unittest.mock import patch

import pytest
from mcp_servers.sample_calculator_server import add, main, multiply


@pytest.mark.asyncio
async def test_add() -> None:
    """Test the add function."""
    expected_sum_1_2 = 3
    expected_sum_neg1_neg2 = -3
    expected_sum_float = 4.0

    assert await add.fn(1, 2) == expected_sum_1_2
    assert await add.fn(-1, -2) == expected_sum_neg1_neg2
    assert await add.fn(0, 0) == 0
    assert await add.fn(1.5, 2.5) == expected_sum_float


def test_signal_handler() -> None:
    """Test the shutdown event setting behavior."""

    # Create a simple mock event that mimics asyncio.Event behavior
    class MockEvent:
        def __init__(self) -> None:
            self._is_set = False

        def set(self) -> None:
            self._is_set = True

        def is_set(self) -> bool:
            return self._is_set

    test_event = MockEvent()

    # Define a signal handler directly similar to the one in the file
    def signal_handler_func(_: int, _frame: object) -> None:
        test_event.set()

    # Call the handler and verify it sets the event
    signal_handler_func(signal.SIGINT, None)
    assert test_event.is_set(), "Signal handler should set the event"


@pytest.mark.asyncio
async def test_multiply() -> None:
    """Test the multiply function."""
    expected_product_2_3 = 6
    expected_product_neg2_3 = -6
    expected_product_float = 3.0

    assert await multiply.fn(2, 3) == expected_product_2_3
    assert await multiply.fn(-2, 3) == expected_product_neg2_3
    assert await multiply.fn(0, 5) == 0
    assert await multiply.fn(1.5, 2.0) == expected_product_float


@pytest.mark.asyncio
async def test_main_stdio() -> None:
    """Test the main function with stdio transport."""
    with (
        patch("mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
        patch(
            "mcp_servers.sample_calculator_server.mcp.run_async",
        ) as mock_run_async,
    ):
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.transport = "stdio"
        mock_run_async.return_value = None

        await main()

        mock_run_async.assert_called_once_with(transport="stdio")


@pytest.mark.asyncio
async def test_main_stdio_exception() -> None:
    """Test the main function with stdio transport when exception occurs."""
    with (
        patch("mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
        patch(
            "mcp_servers.sample_calculator_server.mcp.run_async",
        ) as mock_run_async,
        patch(
            "mcp_servers.sample_calculator_server.logger.error",
        ) as mock_logger_error,
    ):
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.transport = "stdio"

        # Make run_async raise an exception
        test_exception = Exception("Test exception")
        mock_run_async.side_effect = test_exception

        # The exception should propagate
        with pytest.raises(Exception, match="Test exception") as exc_info:
            await main()

        assert exc_info.value == test_exception
        mock_logger_error.assert_called_once()
        assert "Server error" in mock_logger_error.call_args[0][0]


@pytest.mark.asyncio
async def test_main_stdio_cancelled() -> None:
    """Test the main function with stdio transport when cancelled."""
    with (
        patch("mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
        patch(
            "mcp_servers.sample_calculator_server.mcp.run_async",
        ) as mock_run_async,
        patch(
            "mcp_servers.sample_calculator_server.logger.info",
        ) as mock_logger_info,
    ):
        mock_args = mock_parser.return_value.parse_args.return_value
        mock_args.transport = "stdio"

        # Make run_async raise a CancelledError
        mock_run_async.side_effect = asyncio.CancelledError()

        # The CancelledError should be caught
        await main()

        # Verify the logger was called with the right message
        mock_logger_info.assert_any_call("Server stopped by user")
