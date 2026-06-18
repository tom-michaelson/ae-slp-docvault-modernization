#!/usr/bin/env python3
"""Package and publish the latest SDK version for Python and C#.

This script orchestrates the complete packaging and publishing workflow:
1. Gets the current SDK version from version files
2. Packages both Python and C# SDKs with that version
3. Publishes both SDKs to AWS CodeArtifact

It runs the individual packaging and publishing scripts for each language.
"""

import argparse
import subprocess
import sys


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and report its status."""
    print(f"\n{'=' * 60}")
    print(f"🚀 {description}")
    print(f"{'=' * 60}")
    print(f"Running: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def get_sdk_version() -> str | None:
    """Get the current SDK version using the get_sdk_version script."""
    print("\n📌 Getting current SDK version...")

    try:
        result = subprocess.run(
            ["uv", "run", "scripts/get_sdk_version.py"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
        if version:
            print(f"✅ Current SDK version: {version}")
            return version
        print("❌ No version output from get_sdk_version.py")
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get SDK version: {e.stderr}")
        return None


def package_python(version: str) -> bool:
    """Package the Python SDK."""
    cmd = [
        "uv",
        "run",
        "scripts/sdk/package_sdk_python.py",
        "--version",
        version,
    ]
    return run_command(cmd, "Packaging Python SDK")


def package_csharp(version: str) -> bool:
    """Package the C# SDK."""
    cmd = [
        "uv",
        "run",
        "scripts/sdk/package_sdk_csharp.py",
        "--version",
        version,
    ]
    return run_command(cmd, "Packaging C# SDK")


def publish_python(aws_profile: str | None, skip_duplicate_check: bool) -> bool:
    """Publish the Python SDK to CodeArtifact."""
    cmd = ["uv", "run", "scripts/sdk/publish_sdk_python.py"]

    if aws_profile:
        cmd.extend(["--aws-profile", aws_profile])

    if skip_duplicate_check:
        cmd.append("--skip-duplicate-check")

    return run_command(cmd, "Publishing Python SDK to CodeArtifact")


def publish_csharp(aws_profile: str | None, skip_duplicate_check: bool) -> bool:
    """Publish the C# SDK to CodeArtifact."""
    cmd = ["uv", "run", "scripts/sdk/publish_sdk_csharp.py"]

    if aws_profile:
        cmd.extend(["--aws-profile", aws_profile])

    if skip_duplicate_check:
        cmd.append("--skip-duplicate-check")

    return run_command(cmd, "Publishing C# SDK to CodeArtifact")


def main() -> None:  # noqa: PLR0915
    """Execute package and publish workflow for SDK."""
    parser = argparse.ArgumentParser(
        description="Package and publish the latest SDK version for Python and C#",
    )
    parser.add_argument(
        "--aws-profile",
        help="AWS profile name to use for CodeArtifact authentication",
    )
    parser.add_argument(
        "--skip-packaging",
        action="store_true",
        help="Skip packaging steps (assume packages are already built)",
    )
    parser.add_argument(
        "--skip-publishing",
        action="store_true",
        help="Skip publishing steps (only package the SDKs)",
    )
    parser.add_argument(
        "--skip-duplicate-check",
        action="store_true",
        help="Skip checking if package versions already exist in CodeArtifact",
    )
    parser.add_argument(
        "--python-only",
        action="store_true",
        help="Only package and publish Python SDK",
    )
    parser.add_argument(
        "--csharp-only",
        action="store_true",
        help="Only package and publish C# SDK",
    )
    parser.add_argument(
        "--version",
        help="Override the SDK version (if not provided, uses latest from version files)",
    )

    args = parser.parse_args()

    # Validate mutually exclusive options
    if args.python_only and args.csharp_only:
        print("❌ Cannot specify both --python-only and --csharp-only")
        sys.exit(1)

    # Get the SDK version
    if args.version:
        version = args.version
        print(f"📌 Using provided version: {version}")
    else:
        version = get_sdk_version()
        if not version:
            print("❌ Could not determine SDK version")
            print("   Run 'uv run -m awa.main run --workflow awa-generate-sdk' to generate SDKs first")
            sys.exit(1)

    # Track overall success
    all_successful = True

    # Determine which SDKs to process
    process_python = not args.csharp_only
    process_csharp = not args.python_only

    # Package SDKs
    if not args.skip_packaging:
        print(f"\n{'#' * 60}")
        print(f"# PACKAGING PHASE - Version {version}")
        print(f"{'#' * 60}")

        if process_python and not package_python(version):
            all_successful = False
            if not args.skip_publishing:
                print("⚠️  Python packaging failed, skipping Python publishing")
                process_python = False

        if process_csharp and not package_csharp(version):
            all_successful = False
            if not args.skip_publishing:
                print("⚠️  C# packaging failed, skipping C# publishing")
                process_csharp = False
    else:
        print("\n⏭️  Skipping packaging phase (--skip-packaging)")

    # Publish SDKs
    if not args.skip_publishing:
        print(f"\n{'#' * 60}")
        print(f"# PUBLISHING PHASE - Version {version}")
        print(f"{'#' * 60}")

        if process_python and not publish_python(args.aws_profile, args.skip_duplicate_check):
            all_successful = False

        if process_csharp and not publish_csharp(args.aws_profile, args.skip_duplicate_check):
            all_successful = False
    else:
        print("\n⏭️  Skipping publishing phase (--skip-publishing)")

    # Final summary
    print(f"\n{'=' * 60}")
    print("📊 SUMMARY")
    print(f"{'=' * 60}")

    if all_successful:
        print(f"🎉 Successfully completed all operations for SDK version {version}")

        if not args.skip_packaging:
            if process_python:
                print("   ✅ Python SDK packaged")
            if process_csharp:
                print("   ✅ C# SDK packaged")

        if not args.skip_publishing:
            if process_python:
                print("   ✅ Python SDK published to CodeArtifact")
            if process_csharp:
                print("   ✅ C# SDK published to CodeArtifact")
    else:
        print("⚠️  Some operations failed. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
