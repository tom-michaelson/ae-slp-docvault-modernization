#!/usr/bin/env python3
"""Script to generate CLI reference documentation from Typer CLI definitions."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path to allow importing AWA modules
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def _check_process_result(returncode: int, stderr: bytes) -> None:
    """Check subprocess result and raise error if command failed."""
    if returncode != 0:
        raise RuntimeError(f"Command failed with return code {returncode}: {stderr.decode()}")


async def generate_cli_docs() -> None:
    """Generate CLI documentation using Typer's built-in documentation generator."""
    # Define paths relative to script location
    script_dir = Path(__file__).parent
    docs_path = script_dir / "../docs/reference/cli.md"
    docs_path = docs_path.resolve()

    print("Generating CLI reference documentation...")
    print(f"Output file: {docs_path}")

    try:
        # Run Typer's documentation generation command using async subprocess
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "typer",
            "awa.core.cli",
            "utils",
            "docs",
            "--name",
            "awa",
            "--title",
            "AWA CLI Reference",
            cwd=project_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        _check_process_result(process.returncode, stderr)

        # Get the generated documentation
        generated_docs = stdout.decode()

        # Filter out debug logs and ANSI color codes - keep only the actual markdown content
        lines = generated_docs.split("\n")
        filtered_lines = []
        found_header = False

        for line in lines:
            # Skip debug log lines (they contain timestamps and log formatting)
            if "DEBUG" in line and ("AWA" in line or "Initializing" in line or "Registering" in line):
                continue
            # Skip ANSI color code lines
            if line.startswith("\x1b[") or "[32m" in line or "[34m" in line or "[36m" in line:
                continue
            # Start collecting lines once we hit the markdown header
            if line.startswith("# ") and not found_header:
                found_header = True

            if found_header:
                filtered_lines.append(line)

        cleaned_docs = "\n".join(filtered_lines).strip()

        # Add a header note about auto-generation
        header = """<!-- This file is auto-generated. Do not edit manually. -->
<!-- Run 'make docs-prep' or 'python scripts/generate_cli_docs.py' to regenerate. -->

"""

        # Write the documentation to the file
        with docs_path.open("w", encoding="utf-8") as f:
            f.write(header + cleaned_docs + "\n")

        print("Successfully generated CLI reference documentation!")
        print(f"  Generated {len(generated_docs.splitlines())} lines of documentation")

    except RuntimeError as e:
        print(f"Error generating CLI documentation: {e}")
        raise
    except (OSError, FileNotFoundError) as e:
        print(f"Error writing CLI documentation: {e}")
        raise


async def main() -> None:
    """Handle command line arguments and generate CLI docs."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Generate CLI reference documentation from Typer CLI definitions",
    )
    parser.add_argument(
        "--error-on-fail",
        action="store_true",
        help="Exit with error code 1 if operation fails (default: exit with code 0)",
    )
    args = parser.parse_args()

    try:
        await generate_cli_docs()
    except (RuntimeError, OSError, FileNotFoundError) as e:
        print(f"Failed to generate CLI documentation: {e}")
        if args.error_on_fail:
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
