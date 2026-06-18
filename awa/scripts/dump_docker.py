#!/usr/bin/env python3
"""Docker Container File Structure Dumper.

This script dumps the entire file structure of a Docker container to stdout.
Usage: python dump-docker.py <container_name>
"""

import argparse
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO


def run_docker_command(container_name: str, command: list[str]) -> str:
    """Run a command inside the Docker container and return the output."""
    try:
        result = subprocess.run(
            ["docker", "exec", container_name, *command],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        sys.stderr.write(f"Error running command in container '{container_name}': {e}\n")
        sys.stderr.write(f"Command: {' '.join(['docker', 'exec', container_name, *command])}\n")
        if e.stderr:
            sys.stderr.write(f"Error output: {e.stderr}\n")
        sys.exit(1)
    except FileNotFoundError:
        sys.stderr.write("Error: docker command not found. Please ensure Docker is installed and in PATH.\n")
        sys.exit(1)


def check_container_exists(container_name: str) -> bool:
    """Check if the Docker container exists and is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return container_name in result.stdout.strip().split("\n")
    except subprocess.CalledProcessError:
        return False


def _write_directory_structure(f: TextIO, container_name: str) -> int:
    """Write directory structure to file and return directory count."""
    find_command = ["find", "/app", "-type", "d"]

    try:
        result = subprocess.run(
            ["docker", "exec", container_name, *find_command],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )

        dirs = result.stdout.strip().split("\n") if result.stdout.strip() else []
        dirs = [d for d in dirs if d]  # Remove empty lines
        dirs.sort()

        if dirs:
            f.writelines(directory + "\n" for directory in dirs)
            f.write(f"\nTotal directories found: {len(dirs)}\n")
            return len(dirs)
        f.write("No directories found (or all directories are in excluded paths)\n")
        return 0
    except OSError as e:
        f.write(f"Error getting directory listing: {e}\n")
        sys.stderr.write(f"Error getting directory listing: {e}\n")
        sys.exit(1)


def _write_tree_structure(f: TextIO, container_name: str, dirs: list[str]) -> None:
    """Write tree-like directory structure to file."""
    f.write("\n=== Tree-like Directory View ===\n")
    f.write("-" * 60 + "\n")

    try:
        tree_output = run_docker_command(
            container_name,
            ["sh", "-c", "which tree >/dev/null 2>&1 && tree -d -a /app || echo 'tree command not available'"],
        )
        if "tree command not available" not in tree_output:
            f.write(tree_output)
        elif dirs:
            f.write("Directory tree (indented view):\n")
            for directory in dirs:
                depth = directory.replace("/app", "").count("/") if directory != "/app" else 0
                indent = "  " * depth
                dir_name = directory.split("/")[-1] or "app"
                f.write(f"{indent}{dir_name}/\n")
    except OSError as e:
        f.write(f"Error getting tree structure: {e}\n")
        sys.stderr.write(f"Error getting tree structure: {e}\n")


def dump_file_structure(container_name: str, exclude_common_dirs: bool = True) -> None:  # noqa: ARG001
    """Dump the directory structure of the Docker container."""
    # Check if container exists and is running
    if not check_container_exists(container_name):
        sys.stderr.write(f"Error: Container '{container_name}' not found or not running.\n")
        sys.stderr.write("Available running containers:\n")
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "table {{.Names}}\t{{.Image}}\t{{.Status}}"],
                check=False,
                capture_output=True,
                text=True,
            )
            sys.stderr.write(result.stdout)
        except subprocess.CalledProcessError:
            pass
        sys.exit(1)

    sys.stdout.write(f"=== Docker Container Directory Structure: {container_name} (/app only) ===\n")
    sys.stdout.write("\n")

    # Create output file path
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    temp_dir = Path(tempfile.gettempdir())
    output_file = temp_dir / f"docker-dump-{container_name}-{timestamp}.txt"

    try:
        with output_file.open("w") as f:
            f.write(f"=== Docker Container Directory Structure: {container_name} (/app only) ===\n\n")

            # Get the directory listing
            f.write("Directory structure (/app only):\n")
            f.write("-" * 60 + "\n")

            _write_directory_structure(f, container_name)

            # Create dirs list for tree structure
            result = subprocess.run(
                ["docker", "exec", container_name, "find", "/app", "-type", "d"],
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            dirs = result.stdout.strip().split("\n") if result.stdout.strip() else []
            dirs = [d for d in dirs if d]
            dirs.sort()

            _write_tree_structure(f, container_name, dirs)

        # Print summary to console
        file_size = output_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        with output_file.open() as f:
            line_count = sum(1 for _ in f)

        sys.stdout.write("✅ Docker container analysis complete!\n")
        sys.stdout.write(f"📁 Container: {container_name}\n")
        sys.stdout.write(f"📄 Output saved to: {output_file}\n")
        sys.stdout.write(f"📊 File size: {file_size_mb:.1f} MB ({file_size:,} bytes)\n")
        sys.stdout.write(f"📝 Total lines: {line_count:,}\n")
        sys.stdout.write(f"\n🔗 View the file with: cat {output_file}\n")
        sys.stdout.write(f"🔍 Search specific paths: grep '/app/ui' {output_file}\n")

    except OSError as e:
        sys.stderr.write(f"Error writing output file: {e}\n")
        sys.exit(1)


def main() -> None:
    """Parse arguments and dump container structure."""
    parser = argparse.ArgumentParser(
        description="Dump the entire file structure of a Docker container to stdout",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dump-docker.py my-container
  python dump-docker.py awa-ui
  python dump-docker.py --include-system my-container
        """,
    )

    parser.add_argument(
        "container_name",
        help="Name of the Docker container to inspect",
    )

    parser.add_argument(
        "--include-system",
        action="store_true",
        help="Include system directories (/proc, /sys, /dev, etc.) in the output",
    )

    args = parser.parse_args()

    try:
        dump_file_structure(args.container_name, exclude_common_dirs=not args.include_system)
    except KeyboardInterrupt:
        sys.stderr.write("\nOperation cancelled by user.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
