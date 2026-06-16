#!/usr/bin/env python3
"""Build UI and documentation assets for AWA packaging."""

import asyncio
import shutil
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from awa.core.logger.logger import init_logging  # noqa: E402
from awa.core.utils.command_utils import CommandUtils  # noqa: E402


async def run_command_awa(command: str, description: str, shell: bool = True) -> None:
    """Run a shell command using AWA's command utilities.

    Args:
        command: Shell command to execute
        description: Description of what the command does
        shell: Whether to run the command in a shell (default True)

    """
    print(f"📦 {description}...")
    try:
        await CommandUtils.run_command_async(command=command, shell=shell)
        print(f"✅ {description} completed successfully")
    except (CommandUtils.CommandError, RuntimeError) as e:
        print(f"❌ {description} failed: {e}")
        sys.exit(1)


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists.

    Args:
        path: Directory path to create

    """
    path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Created directory: {path}")


def copy_assets(source: Path, destination: Path, asset_type: str) -> None:
    """Copy built assets to packaging directory.

    Args:
        source: Source directory with built assets
        destination: Destination directory in awa/static/
        asset_type: Type of assets being copied (for logging)

    """
    if not source.exists():
        print(f"⚠️  Source directory not found: {source}")
        return

    # Remove existing assets if they exist
    if destination.exists():
        shutil.rmtree(destination)
        print(f"🗑️  Removed existing {asset_type} assets")

    shutil.copytree(source, destination, dirs_exist_ok=True)
    print(f"📋 Copied {asset_type} assets: {source} → {destination}")


async def main() -> None:
    """Build UI and documentation assets for AWA packaging."""
    print("🚀 Building AWA UI and Documentation Assets")
    print("=" * 50)

    # Initialize AWA environment setup (like main CLI does)
    init_logging()

    # Verify we're running from correct directory
    current_dir = Path.cwd()
    if not (current_dir / "awa").exists():
        print("❌ Error: Must run from AWA project root directory")
        sys.exit(1)

    # Step 0: Ensure dependencies are installed (both root and ui)
    await run_command_awa(
        "pnpm install",
        "Installing root JavaScript dependencies",
    )

    # Step 0b: Ensure UI dependencies are properly flattened for packaging
    await run_command_awa(
        "cd ui && pnpm install --shamefully-hoist --force",
        "Installing UI dependencies with hoisting for packaging",
    )

    # Step 1: Run prerequisite scripts using AWA command utilities
    await run_command_awa(
        "pnpm run copy-cookbook-docs",
        "Copying cookbook documentation",
    )

    await run_command_awa(
        "uv run scripts/generate-cli-docs.py",
        "Generating CLI documentation",
    )

    # Step 2: Build documentation using AWA command utilities
    await run_command_awa(
        "pnpm run docs:build",
        "Building VitePress documentation",
    )

    # Step 3: Build UI using AWA command utilities
    await run_command_awa(
        "pnpm run ui:build",
        "Building Astro UI",
    )

    # Step 4: Prepare static assets directory
    static_dir = current_dir / "awa" / "static"
    ensure_directory(static_dir)

    # Step 5: Copy built assets
    # VitePress builds to ui/public/docs (see docs/.vitepress/config.mts outDir)
    docs_source = current_dir / "ui" / "public" / "docs"
    docs_dest = static_dir / "docs"
    copy_assets(docs_source, docs_dest, "documentation")

    # Copy built UI application and its runtime dependencies
    ui_dist_source = current_dir / "ui" / "dist"
    ui_dest = static_dir / "ui"
    copy_assets(ui_dist_source, ui_dest, "built UI application")

    # Copy node_modules needed for server runtime
    ui_node_modules_source = current_dir / "ui" / "node_modules"
    ui_node_modules_dest = static_dir / "ui" / "node_modules"
    copy_assets(ui_node_modules_source, ui_node_modules_dest, "UI runtime dependencies")

    # Copy package.json for module resolution
    ui_package_json_source = current_dir / "ui" / "package.json"
    ui_package_json_dest = static_dir / "ui" / "package.json"
    if ui_package_json_source.exists():
        shutil.copy2(ui_package_json_source, ui_package_json_dest)
        print(f"📋 Copied package.json: {ui_package_json_source} → {ui_package_json_dest}")

    print("=" * 50)
    print("✅ AWA UI and documentation assets built successfully!")
    print(f"📁 Assets packaged in: {static_dir}")


if __name__ == "__main__":
    asyncio.run(main())
