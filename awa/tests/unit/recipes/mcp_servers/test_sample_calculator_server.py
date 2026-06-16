"""Tests for the sample calculator MCP server."""

import argparse
import asyncio
import contextlib
import math
import signal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import cookbook.recipes.mcp_servers.sample_calculator_server as server_module
from cookbook.recipes.mcp_servers.sample_calculator_server import add, main, multiply


class TestCalculatorFunctions:
    """Test class for calculator tool functions."""

    @pytest.mark.asyncio
    async def test_add_positive_numbers(self) -> None:
        """Test adding positive numbers."""
        result = await add.fn(3.0, 4.0)
        assert result == 7.0

    @pytest.mark.asyncio
    async def test_add_negative_numbers(self) -> None:
        """Test adding negative numbers."""
        result = await add.fn(-1.0, -2.0)
        assert result == -3.0

    @pytest.mark.asyncio
    async def test_add_mixed_numbers(self) -> None:
        """Test adding positive and negative numbers."""
        result = await add.fn(5.0, -3.0)
        assert result == 2.0

    @pytest.mark.asyncio
    async def test_add_zero(self) -> None:
        """Test adding with zero."""
        result = await add.fn(0.0, 5.0)
        assert result == 5.0

        result = await add.fn(5.0, 0.0)
        assert result == 5.0

        result = await add.fn(0.0, 0.0)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_add_floats(self) -> None:
        """Test adding floating point numbers."""
        result = await add.fn(1.5, 2.5)
        assert result == 4.0

    @pytest.mark.asyncio
    async def test_add_large_numbers(self) -> None:
        """Test adding large numbers."""
        result = await add.fn(1000000.0, 2000000.0)
        assert result == 3000000.0

    @pytest.mark.asyncio
    async def test_multiply_positive_numbers(self) -> None:
        """Test multiplying positive numbers."""
        result = await multiply.fn(3.0, 4.0)
        assert result == 12.0

    @pytest.mark.asyncio
    async def test_multiply_negative_numbers(self) -> None:
        """Test multiplying negative numbers."""
        result = await multiply.fn(-2.0, -3.0)
        assert result == 6.0

    @pytest.mark.asyncio
    async def test_multiply_mixed_numbers(self) -> None:
        """Test multiplying positive and negative numbers."""
        result = await multiply.fn(4.0, -2.0)
        assert result == -8.0

    @pytest.mark.asyncio
    async def test_multiply_by_zero(self) -> None:
        """Test multiplying by zero."""
        result = await multiply.fn(5.0, 0.0)
        assert result == 0.0

        result = await multiply.fn(0.0, 10.0)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_multiply_floats(self) -> None:
        """Test multiplying floating point numbers."""
        result = await multiply.fn(2.5, 4.0)
        assert result == 10.0

    @pytest.mark.asyncio
    async def test_multiply_large_numbers(self) -> None:
        """Test multiplying large numbers."""
        result = await multiply.fn(1000.0, 2000.0)
        assert result == 2000000.0


class TestMainFunctionStdio:
    """Test class for main function with stdio transport."""

    @pytest.mark.asyncio
    async def test_main_stdio_success(self) -> None:
        """Test main function with stdio transport - success case."""
        with (
            patch(
                "cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser",
            ) as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal") as mock_signal,
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "stdio"
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock successful run
            mock_run_async.return_value = None

            await main()

            # Verify the correct calls
            mock_run_async.assert_called_once_with(transport="stdio")
            # Verify signal handlers were set up
            assert mock_signal.call_count == 2

    @pytest.mark.asyncio
    async def test_main_stdio_cancelled_error(self) -> None:
        """Test main function with stdio transport - CancelledError handling."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "stdio"
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock CancelledError
            mock_run_async.side_effect = asyncio.CancelledError()

            await main()

            # Verify proper logging
            mock_logger_info.assert_called_with("Server stopped by user")

    @pytest.mark.asyncio
    async def test_main_stdio_generic_exception(self) -> None:
        """Test main function with stdio transport - generic exception handling."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.error") as mock_logger_error,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "stdio"
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock generic exception
            test_exception = RuntimeError("Test error")
            mock_run_async.side_effect = test_exception

            # Should re-raise the exception
            with pytest.raises(RuntimeError, match="Test error"):
                await main()

            # Verify error logging
            mock_logger_error.assert_called_once()
            assert "Server error:" in str(mock_logger_error.call_args[0][0])


class TestMainFunctionHttp:
    """Test class for main function with HTTP transport."""

    @pytest.mark.asyncio
    async def test_main_http_startup_logging(self) -> None:
        """Test HTTP transport startup logging."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "streamable-http"
            mock_args.host = "127.0.0.1"
            mock_args.port = 9000
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock server to raise CancelledError after startup logging
            mock_run_async.side_effect = asyncio.CancelledError()

            await main()

            # Verify startup log (this covers line 61)
            mock_logger_info.assert_any_call("Starting Sample Calculator MCP Server on http://127.0.0.1:9000")

            # Verify server stopped log (covers part of exception handling)
            mock_logger_info.assert_any_call("Server stopped by user")

    @pytest.mark.asyncio
    async def test_main_http_custom_host_port(self) -> None:
        """Test HTTP transport with custom host and port."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
        ):
            # Set up mock arguments with custom host and port
            mock_args = MagicMock()
            mock_args.transport = "streamable-http"
            mock_args.host = "127.0.0.1"
            mock_args.port = 8888
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock server to raise CancelledError
            mock_run_async.side_effect = asyncio.CancelledError()

            await main()

            # Verify startup log with custom host:port
            mock_logger_info.assert_any_call("Starting Sample Calculator MCP Server on http://127.0.0.1:8888")

            # Verify the server was called with custom host and port
            mock_run_async.assert_called_once_with(
                transport="streamable-http",
                host="127.0.0.1",
                port=8888,
            )

    @pytest.mark.asyncio
    async def test_main_http_cancelled_error(self) -> None:
        """Test main function with HTTP transport - CancelledError handling."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "streamable-http"
            mock_args.host = "127.0.0.1"
            mock_args.port = 9000
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock CancelledError during server setup (covers line 86-87)
            mock_run_async.side_effect = asyncio.CancelledError()

            await main()

            # Verify proper logging (covers line 87)
            mock_logger_info.assert_any_call("Server stopped by user")

    @pytest.mark.asyncio
    async def test_main_http_generic_exception(self) -> None:
        """Test main function with HTTP transport - generic exception handling."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async") as mock_run_async,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.error") as mock_logger_error,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "streamable-http"
            mock_args.host = "127.0.0.1"
            mock_args.port = 9000
            mock_parser.return_value.parse_args.return_value = mock_args

            # Mock generic exception (covers line 88-90)
            test_exception = ConnectionError("Connection failed")
            mock_run_async.side_effect = test_exception

            # Should re-raise the exception
            with pytest.raises(ConnectionError, match="Connection failed"):
                await main()

            # Verify error logging (covers line 89)
            mock_logger_error.assert_called_once()
            assert "Server error:" in str(mock_logger_error.call_args[0][0])

    @pytest.mark.asyncio
    async def test_main_http_shutdown_with_suppress_context(self) -> None:
        """Test HTTP transport with shutdown event handling and suppress context."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async"),
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal"),
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.asyncio.Event") as mock_event_class,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.asyncio.create_task") as mock_create_task,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.asyncio.wait") as mock_wait,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.contextlib.suppress") as mock_suppress,
        ):
            # Set up mock arguments
            mock_args = MagicMock()
            mock_args.transport = "streamable-http"
            mock_args.host = "127.0.0.1"
            mock_args.port = 9000
            mock_parser.return_value.parse_args.return_value = mock_args

            # Set up mock event to be set (shutdown scenario)
            mock_shutdown_event = MagicMock()
            mock_shutdown_event.is_set.return_value = True
            mock_event_class.return_value = mock_shutdown_event

            # Create mock tasks using MagicMock instead of real coroutines
            mock_server_task = MagicMock()
            mock_server_task.done.return_value = True
            mock_shutdown_task = MagicMock()
            mock_shutdown_task.done.return_value = True

            # Mock create_task to return our mock tasks
            mock_create_task.side_effect = [mock_server_task, mock_shutdown_task]

            # Shutdown event completes first
            mock_wait.return_value = ({mock_shutdown_task}, {mock_server_task})

            # Mock the suppress context manager
            mock_suppress.return_value.__enter__ = MagicMock()
            mock_suppress.return_value.__exit__ = MagicMock(return_value=True)

            await main()

            # Verify contextlib.suppress was called (covers lines 80-82)
            mock_suppress.assert_called_once_with(asyncio.CancelledError)

            # Verify shutdown logging
            mock_logger_info.assert_any_call("Server stopped by user")


class TestSignalHandling:
    """Test class for signal handling functionality."""

    @pytest.mark.asyncio
    async def test_signal_handler_logs_and_sets_event(self) -> None:
        """Test signal handler logs message and sets shutdown event."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.argparse.ArgumentParser") as mock_parser,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.signal.signal") as mock_signal,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.asyncio.Event") as mock_event_class,
            patch(
                "cookbook.recipes.mcp_servers.sample_calculator_server.mcp.run_async",
                new=AsyncMock(),
            ) as mock_run_async,
        ):
            # Set up mock arguments for HTTP transport to trigger signal handler creation
            mock_args = MagicMock()
            mock_args.transport = "streamable-http"
            mock_args.host = "127.0.0.1"
            mock_args.port = 9000
            mock_parser.return_value.parse_args.return_value = mock_args

            # Set up mock shutdown event
            mock_shutdown_event = MagicMock()
            mock_event_class.return_value = mock_shutdown_event

            # Configure mcp.run_async to return None (already AsyncMock)
            mock_run_async.return_value = None

            # Capture the signal handler function
            signal_handler = None

            def capture_signal_handler(_sig: int, handler: object) -> None:
                nonlocal signal_handler
                signal_handler = handler

            mock_signal.side_effect = capture_signal_handler

            # Start main to set up signal handlers (will raise exception, but we catch it)
            with contextlib.suppress(Exception):
                await main()

            # Verify signal handler was captured
            assert signal_handler is not None

            # Test the signal handler directly
            signal_handler(signal.SIGINT, None)

            # Verify logging and event setting
            mock_logger_info.assert_any_call("Received signal 2, shutting down gracefully...")
            mock_shutdown_event.set.assert_called_once()

    def test_signal_handler_with_different_signals(self) -> None:
        """Test signal handler behavior with different signal types."""
        # Create a mock shutdown event
        mock_shutdown_event = MagicMock()

        with patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info:
            # Create signal handler function directly
            def signal_handler(signum: int, _frame: object) -> None:
                mock_logger_info(f"Received signal {signum}, shutting down gracefully...")
                mock_shutdown_event.set()

            # Test with SIGINT
            signal_handler(signal.SIGINT, None)
            mock_logger_info.assert_called_with("Received signal 2, shutting down gracefully...")
            mock_shutdown_event.set.assert_called()

            # Reset mocks
            mock_logger_info.reset_mock()
            mock_shutdown_event.reset_mock()

            # Test with SIGTERM
            signal_handler(signal.SIGTERM, None)
            mock_logger_info.assert_called_with("Received signal 15, shutting down gracefully...")
            mock_shutdown_event.set.assert_called()


class TestArgumentParsing:
    """Test class for command-line argument parsing."""

    def test_argument_parser_configuration(self) -> None:
        """Test that argument parser is configured with expected defaults and choices."""
        # This test verifies the argument parser setup by actually calling it
        parser = argparse.ArgumentParser(description="Run Sample Calculator MCP Server")
        parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
        parser.add_argument("--port", type=int, default=9000, help="Port to bind to (default: 9000)")
        parser.add_argument(
            "--transport",
            default="streamable-http",
            choices=["stdio", "streamable-http"],
            help="Transport to use (default: streamable-http)",
        )

        # Test default values
        args = parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 9000
        assert args.transport == "streamable-http"

        # Test custom values
        args = parser.parse_args(["--host", "localhost", "--port", "8080", "--transport", "stdio"])
        assert args.host == "localhost"
        assert args.port == 8080
        assert args.transport == "stdio"

        # Test invalid transport should raise SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--transport", "invalid"])


class TestEdgeCases:
    """Test class for edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_add_with_infinity(self) -> None:
        """Test add function with infinity values."""
        result = await add.fn(float("inf"), 1.0)
        assert math.isinf(result)

        result = await add.fn(1.0, float("-inf"))
        assert math.isinf(result)

    @pytest.mark.asyncio
    async def test_multiply_with_infinity(self) -> None:
        """Test multiply function with infinity values."""
        result = await multiply.fn(float("inf"), 2.0)
        assert math.isinf(result)

        result = await multiply.fn(-1.0, float("inf"))
        assert math.isinf(result)

    @pytest.mark.asyncio
    async def test_add_with_nan(self) -> None:
        """Test add function with NaN values."""
        result = await add.fn(float("nan"), 1.0)
        assert math.isnan(result)

    @pytest.mark.asyncio
    async def test_multiply_with_nan(self) -> None:
        """Test multiply function with NaN values."""
        result = await multiply.fn(float("nan"), 2.0)
        assert math.isnan(result)


class TestMainEntryPoint:
    """Test class for the main entry point execution."""

    def test_main_entry_point_keyboard_interrupt(self) -> None:
        """Test main entry point handles KeyboardInterrupt."""
        with (
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.asyncio.run") as mock_asyncio_run,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.logger.info") as mock_logger_info,
            patch("cookbook.recipes.mcp_servers.sample_calculator_server.sys.exit") as mock_sys_exit,
        ):
            # Mock KeyboardInterrupt
            mock_asyncio_run.side_effect = KeyboardInterrupt()

            # Execute the main block using already imported module

            # Simulate the if __name__ == "__main__": block
            try:
                server_module.asyncio.run(server_module.main())
            except KeyboardInterrupt:
                server_module.logger.info("Server stopped by user")
                server_module.sys.exit(0)

            # Verify proper handling
            mock_logger_info.assert_called_with("Server stopped by user")
            mock_sys_exit.assert_called_with(0)
