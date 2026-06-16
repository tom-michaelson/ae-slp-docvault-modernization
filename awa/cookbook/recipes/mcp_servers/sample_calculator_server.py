"""Sample Calculator MCP Server for testing MCP tool integration."""

import argparse
import asyncio
import contextlib
import signal
import sys

from fastmcp import FastMCP
from loguru import logger

mcp = FastMCP("SampleCalculatorServer")


@mcp.tool
async def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b


@mcp.tool
async def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run Sample Calculator MCP Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=9000, help="Port to bind to (default: 9000)")
    parser.add_argument(
        "--transport",
        default="streamable-http",
        choices=["stdio", "streamable-http"],
        help="Transport to use (default: streamable-http)",
    )

    args = parser.parse_args()

    # Create a shutdown event for graceful termination
    shutdown_event = asyncio.Event()

    def signal_handler(signum: int, _frame: object) -> None:
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        shutdown_event.set()

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

    if args.transport == "stdio":
        try:
            await mcp.run_async(transport="stdio")
        except asyncio.CancelledError:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise
    else:
        logger.info(f"Starting Sample Calculator MCP Server on http://{args.host}:{args.port}")
        try:
            # Run the server until shutdown event is set
            server_task = asyncio.create_task(
                mcp.run_async(transport="streamable-http", host=args.host, port=args.port),
            )
            shutdown_task = asyncio.create_task(shutdown_event.wait())

            # Wait for either the server to complete or shutdown signal
            _, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED,
            )

            # Cancel any pending tasks
            for task in pending:
                task.cancel()

            if shutdown_event.is_set():
                with contextlib.suppress(asyncio.CancelledError):
                    await server_task
                logger.info("Server stopped by user")
            else:
                await server_task

        except asyncio.CancelledError:
            logger.info("Server stopped by user")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
