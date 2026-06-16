"""UI command implementation."""

import asyncio
import os
from pathlib import Path
from typing import Annotated

import typer

import awa
from awa.core.cli import constants as cli_constants
from awa.core.logger.logger import LoggerComponent, get_logger, init_logging
from awa.core.models.cli.ui_mode import UIMode
from awa.core.models.config.env_config import EnvConfig
from awa.core.utils.cli_utils import is_packaged_mode
from awa.core.utils.command_utils import CommandUtils

app = typer.Typer()
init_logging()
ui_logger = get_logger(LoggerComponent.UI)


@app.command(name="ui")
def ui(
    mode: Annotated[
        UIMode | None,
        typer.Option("--ui", "-u", help="UI mode to use"),
    ] = UIMode.DEV,
) -> None:
    """Run the AWA UI in the specified mode."""
    init_logging()
    asyncio.run(ui_async(mode=mode))


async def ui_async(mode: UIMode = UIMode.DEV) -> None:
    if not mode or mode == UIMode.NONE:
        ui_logger.info("Not running UI.")
        return

    # Check for package mode and exit early
    if is_packaged_mode():
        ui_logger.warning(cli_constants.UI_PACKAGE_MODE_WARNING)
        return

    # Development mode: dynamic building
    await build_and_serve_dynamic(mode)


async def check_nodejs_available() -> bool:
    """Check if Node.js is available on the system."""
    try:
        await CommandUtils.run_command_async("node --version")
        return True
    except Exception:  # noqa: BLE001
        return False


async def serve_static_assets(_mode: UIMode) -> None:
    """Serve pre-built UI using Node.js server."""
    static_dir = Path(awa.__file__).parent / "static"
    ui_dist_dir = static_dir / "ui"

    if not ui_dist_dir.exists():
        ui_logger.error(f"UI build directory not found: {ui_dist_dir}")
        ui_logger.error("Package may not have been built with UI assets.")
        return

    # Basic validation for required components
    required_paths = [
        ui_dist_dir / "server" / "entry.mjs",
        ui_dist_dir / "node_modules",
        ui_dist_dir / "package.json",
    ]

    for path in required_paths:
        if not path.exists():
            ui_logger.error(f"Required UI component not found: {path}")
            ui_logger.error("Package may not have been built correctly with all dependencies.")
            return

    # Check for Node.js availability
    if not await check_nodejs_available():
        ui_logger.error("Node.js is required to run the UI server but was not found.")
        ui_logger.error("Please install Node.js and ensure it's available in your PATH.")
        return

    # Set environment variables
    env = os.environ.copy()
    env["AWA_UI_HOST"] = EnvConfig.get_env_config().awa_ui_host
    env["AWA_UI_PORT"] = str(EnvConfig.get_env_config().awa_ui_port)
    env["AWA_API_HOST"] = EnvConfig.get_env_config().awa_api_host
    env["AWA_API_PORT"] = str(EnvConfig.get_env_config().awa_api_port)
    env["TEMPORAL_UI_HOST"] = EnvConfig.get_env_config().temporal_ui_host
    env["TEMPORAL_UI_PORT"] = str(EnvConfig.get_env_config().temporal_ui_port)

    # Run the built Node.js server directly
    command = "node server/entry.mjs"

    ui_logger.info(f"Starting UI server from: {ui_dist_dir}")
    ui_logger.info(f"UI available at: http://{env['AWA_UI_HOST']}:{env['AWA_UI_PORT']}")

    async for output in CommandUtils.stream_command_async(command, env=env, working_dir=str(ui_dist_dir)):
        if hasattr(output, "pid"):
            ui_logger.info(f"UI server started with PID: {output.pid}")
            continue
        if output:
            ui_logger.info(f"[UI] {output}")


async def build_and_serve_dynamic(mode: UIMode) -> None:
    """Build and serve UI dynamically (existing development logic)."""
    ui_logger.info("Building docs for UI...")
    await CommandUtils.run_command_async(command="pnpm run copy-cookbook-docs")
    await CommandUtils.run_command_async(command="uv run scripts/generate_cli_docs.py")
    await CommandUtils.run_command_async(command="pnpm run docs:build")

    # Set environment variables for Astro
    env = os.environ.copy()
    env["AWA_UI_HOST"] = EnvConfig.get_env_config().awa_ui_host
    env["AWA_UI_PORT"] = str(EnvConfig.get_env_config().awa_ui_port)
    env["AWA_API_HOST"] = EnvConfig.get_env_config().awa_api_host
    env["AWA_API_PORT"] = str(EnvConfig.get_env_config().awa_api_port)
    env["TEMPORAL_UI_HOST"] = EnvConfig.get_env_config().temporal_ui_host
    env["TEMPORAL_UI_PORT"] = str(EnvConfig.get_env_config().temporal_ui_port)

    ui_command = None
    if mode == UIMode.DEV:
        ui_command = "pnpm run ui:dev"
    elif mode == UIMode.PROD:
        ui_logger.info("Building UI...")
        await CommandUtils.run_command_async(command="pnpm run ui:build")
        ui_command = "pnpm run ui:preview"

    if ui_command:
        ui_logger.info(f"Starting UI server with command: {ui_command}")

        async for output in CommandUtils.stream_command_async(ui_command, env=env):
            if hasattr(output, "pid"):
                ui_logger.info(f"UI server started with PID: {output.pid}")
                continue
            if output:
                ui_logger.info(output.rstrip())

    ui_logger.info(f"UI started in '{mode}' mode.")
