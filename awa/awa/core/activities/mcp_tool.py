import asyncio
import subprocess
import sys
from typing import Any

from fastmcp import Client
from fastmcp.client.transports import SSETransport
from temporalio import activity

from awa.core.logger.logger import LoggerComponent, get_logger
from awa.sdk import constants as sdk_constants

logger = get_logger(LoggerComponent.ACTIVITY)


async def _diagnose_mcp_server_startup(mcp_config: dict[str, Any]) -> None:
    """Diagnose MCP server startup issues."""
    if not isinstance(mcp_config, dict) or "mcpServers" not in mcp_config:
        return

    for server_name, server_config in mcp_config["mcpServers"].items():
        command = server_config.get("command")
        args = server_config.get("args", [])
        env = server_config.get("env", {})

        if command == "npx":
            logger.info(f"Diagnosing {server_name} server startup...")

            # Test if npx is available
            try:
                # Using subprocess here is necessary for environment validation in diagnostic context
                result = subprocess.run(  # noqa: ASYNC221, S603
                    [sys.executable, "-c", "import shutil; print(shutil.which('npx') or '')"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"npx found at: {result.stdout.strip()}")
                else:
                    logger.error("npx not found in PATH")
                    return
            except (subprocess.TimeoutExpired, OSError):
                logger.exception("Failed to check npx availability")
                return

            # Test if the package can be downloaded
            if args:
                package = args[-1] if args[-1] != "-y" else args[-2]
                logger.info(f"Testing package availability: {package}")
                try:
                    # Use absolute path to npx if found, safer than relying on PATH
                    npx_path = result.stdout.strip() if result.stdout.strip() else "npx"
                    test_cmd = [npx_path, "-y", package, "--help"]
                    # Package testing requires subprocess for validation in diagnostic context
                    pkg_result = subprocess.run(  # noqa: ASYNC221, S603
                        test_cmd,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        env={**subprocess.os.environ, **env},
                        check=False,
                    )
                    if pkg_result.returncode == 0:
                        logger.info(f"Package {package} downloaded and executed successfully")
                    else:
                        logger.error(f"Package {package} failed: {pkg_result.stderr}")
                except subprocess.TimeoutExpired:
                    logger.warning(f"Package {package} test timed out - may still work")
                except (OSError, subprocess.SubprocessError):
                    logger.exception(f"Failed to test package {package}")


@activity.defn(name=sdk_constants.ACTIVITY_INVOKE_MCP_TOOL)
async def invoke_mcp_tool(
    mcp_config: dict[str, Any] | str,
    tool_name: str,
    parameters: dict[str, Any],
) -> Any:  # noqa: ANN401
    """Temporal Activity that invokes an MCP tool programmatically using MCPConfig.

    Args:
        mcp_config: MCP configuration dictionary containing server definitions.
                   Format: {
                       "mcpServers": {
                           "server_name": {
                               "url": "http://127.0.0.1:9000/mcp",
                               "transport": "streamable-http",
                               "env": {"EXAMPLE_ENV_VAR": "example_value"},
                           }
                       }
                   }
        tool_name: The name of the MCP tool to invoke (can include server prefix if multiple servers)
        parameters: Dictionary of parameters to pass to the tool

    Returns:
        The result of the MCP tool invocation

    """
    # Run diagnostics on first connection failure
    if isinstance(mcp_config, dict):
        logger.debug(f"MCP config servers: {list(mcp_config.get('mcpServers', {}).keys())}")
        # Always run diagnostics first to validate environment
        logger.debug("Running MCP server environment diagnostics...")
        await _diagnose_mcp_server_startup(mcp_config)

    client: Client | None = None
    if isinstance(mcp_config, str):
        transport = SSETransport(url=mcp_config)
        client = Client(transport)
    else:
        client = Client(mcp_config)

    max_retries = 2  # Reduced retries for faster failure in pipeline
    for attempt in range(max_retries):
        try:
            logger.info(f"Starting MCP client connection (attempt {attempt + 1}/{max_retries})...")
            async with client:
                logger.info(f"MCP client connected! Calling tool {tool_name} with parameters {parameters}")
                logger.debug(f"MCP config: {mcp_config}")
                result = await client.call_tool(tool_name, parameters)
                logger.debug(f"Result: {result}")
                return result
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            logger.exception(f"Attempt {attempt + 1} failed with {error_type}: {error_msg}")

            if attempt == max_retries - 1:
                logger.exception(f"All {max_retries} attempts failed for MCP tool {tool_name}")
                # Return error as a result instead of raising
                # This allows agents to see the error and self-correct
                final_error_msg = (
                    f"MCP tool '{tool_name}' failed after {max_retries} attempts. Last error: {error_type}: {error_msg}"
                )
                return {"error": final_error_msg, "tool": tool_name, "parameters": parameters}

            # Shorter wait time for faster pipeline execution
            wait_time = 1
            logger.info(f"Retrying in {wait_time} second(s)...")
            await asyncio.sleep(wait_time)

    # This should never be reached due to the return in the loop, but satisfies linter
    error_msg = f"Failed to execute MCP tool {tool_name} after {max_retries} attempts"
    return {"error": error_msg, "tool": tool_name, "parameters": parameters}
