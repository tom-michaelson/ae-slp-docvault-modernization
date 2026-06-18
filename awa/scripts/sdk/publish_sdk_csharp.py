#!/usr/bin/env python3
"""Script to publish AWA SDK NuGet package to AWS CodeArtifact.

This script automates the process of publishing a pre-built NuGet package
to AWS CodeArtifact, supporting both AWS profiles and environment credentials.
It assumes the package has already been built by package_sdk_csharp.py.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for importing the helper
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.sdk.aws_auth_helper import configure_aws_environment

# Constants
MIN_PARTS_FOR_SOURCE_NAME = 2


def run_command(cmd: list[str], env: dict | None = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env or os.environ.copy(),
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, f"Command failed: {e.stderr.strip()}"


def check_prerequisites() -> bool:
    """Check if required tools are installed."""
    print("Checking prerequisites...")

    # Check if dotnet is installed
    success, output = run_command(["dotnet", "--version"])
    if not success:
        print("❌ dotnet CLI is not installed")
        return False
    print(f"✅ dotnet CLI version: {output}")

    # Check if AWS CLI is installed
    success, output = run_command(["aws", "--version"])
    if not success:
        print("❌ AWS CLI is not installed")
        return False
    print(f"✅ AWS CLI version: {output.split()[0]}")

    return True


def is_codeartifact_tool_installed() -> bool:
    """Check if CodeArtifact credential provider is installed."""
    success, _ = run_command(["dotnet", "tool", "list", "-g"])
    if not success:
        return False

    success, output = run_command(["dotnet", "tool", "list", "-g"])
    return "aws.codeartifact.nuget.credentialprovider" in output.lower()


def install_codeartifact_tools() -> bool:
    """Install CodeArtifact credential provider tools."""
    print("Setting up CodeArtifact credential provider...")

    # Check if already installed
    if is_codeartifact_tool_installed():
        print("✅ CodeArtifact credential provider already installed")
    else:
        print("Installing CodeArtifact credential provider...")
        success, output = run_command(
            [
                "dotnet",
                "tool",
                "install",
                "-g",
                "AWS.CodeArtifact.NuGet.CredentialProvider",
            ],
        )
        if not success:
            print(f"❌ Failed to install CodeArtifact credential provider: {output}")
            return False
        print("✅ CodeArtifact credential provider installed")

    # Install credential provider
    print("Installing CodeArtifact credentials...")
    success, output = run_command(["dotnet", "codeartifact-creds", "install"])
    if not success:
        # This might fail if already installed, which is okay
        if "already installed" not in output.lower():
            print(f"⚠️  CodeArtifact credentials install warning: {output}")
        else:
            print("✅ CodeArtifact credentials already installed")
    else:
        print("✅ CodeArtifact credentials installed")

    return True


def configure_codeartifact_profile(aws_profile: str | None) -> bool:
    """Configure CodeArtifact credential provider with AWS profile."""
    if not aws_profile:
        print("✅ Skipping profile configuration (using environment credentials)")
        return True

    print(f"Configuring CodeArtifact credential provider with profile: {aws_profile}")
    success, output = run_command(
        [
            "dotnet",
            "codeartifact-creds",
            "configure",
            "set",
            "profile",
            aws_profile,
        ],
    )
    if not success:
        print(f"❌ Failed to configure profile: {output}")
        return False

    print("✅ CodeArtifact credential provider configured")
    return True


def setup_environment(aws_profile: str | None) -> dict:
    """Set up environment variables for AWS authentication.

    This is a wrapper around the shared helper for backward compatibility.
    """
    return configure_aws_environment(aws_profile)


def login_to_codeartifact(
    domain: str,
    domain_owner: str,
    repository: str,
    env: dict,
) -> bool:
    """Log in to AWS CodeArtifact."""
    print(f"Logging in to CodeArtifact domain: {domain}, repository: {repository}")

    cmd = [
        "aws",
        "codeartifact",
        "login",
        "--tool",
        "dotnet",
        "--domain",
        domain,
        "--domain-owner",
        domain_owner,
        "--repository",
        repository,
    ]

    success, output = run_command(cmd, env)
    if not success:
        print(f"❌ Failed to log in to CodeArtifact: {output}")
        return False

    print("✅ Successfully logged in to CodeArtifact")
    return True


def get_package_version_from_file(package_dir: Path, package_name: str) -> str | None:
    """Extract version from the packaged .nupkg file name."""
    print(f"Looking for package files in: {package_dir}")

    # Find all .nupkg files matching the package name
    package_files = list(package_dir.glob(f"{package_name}.*.nupkg"))
    if not package_files:
        print(f"❌ No package files found matching {package_name}.*.nupkg")
        return None

    # Extract versions from all package files and find the highest version
    versions = []
    for package_file in package_files:
        filename = package_file.stem  # Remove .nupkg extension
        if filename.startswith(f"{package_name}."):
            version_str = filename[len(f"{package_name}.") :]
            versions.append((version_str, package_file))

    if not versions:
        print("❌ Could not extract version from any filename")
        return None

    # Sort versions to get the highest one (using semantic version sorting)
    # Maximum number of version parts (major.minor.patch.build)
    max_version_parts = 4

    def version_key(version_tuple: tuple[str, str]) -> list[int]:
        version_str = version_tuple[0]
        try:
            # Split version into parts and convert to integers for proper sorting
            parts = [int(x) for x in version_str.split(".")]
            # Pad with zeros to ensure consistent comparison
            while len(parts) < max_version_parts:
                parts.append(0)
            return parts
        except ValueError:
            # If version parsing fails, fall back to string sorting
            return [0, 0, 0, 0]

    # Sort by version and take the highest one
    sorted_versions = sorted(versions, key=version_key, reverse=True)
    latest_version, _latest_file = sorted_versions[0]

    print(f"✅ Found {len(versions)} package versions, using latest: {latest_version}")
    if len(versions) > 1:
        print(f"   Available versions: {[v[0] for v in sorted_versions]}")

    return latest_version


def check_version_exists(
    package_name: str,
    version: str,
    domain: str,
    repository: str,
    domain_owner: str,
    env: dict,
) -> bool:
    """Check if a specific version of a package exists in CodeArtifact."""
    print(f"Checking if {package_name} v{version} exists in CodeArtifact...")

    cmd = [
        "aws",
        "codeartifact",
        "describe-package-version",
        "--domain",
        domain,
        "--domain-owner",
        domain_owner,
        "--repository",
        repository,
        "--package",
        package_name,
        "--format",
        "nuget",
        "--package-version",
        version,
    ]

    success, output = run_command(cmd, env)
    if not success:
        if "ResourceNotFoundException" in output:
            print(f"✅ Version {version} does not exist (ready to publish)")
            return False
        print(f"❌ Failed to check package version: {output}")
        return False

    print(f"⚠️  Version {version} already exists in CodeArtifact")
    return True


def find_package_file(package_dir: Path, package_name: str, version: str | None = None) -> Path | None:
    """Find the .nupkg file in the package directory."""
    pattern = f"{package_name}.{version}.nupkg" if version else f"{package_name}.*.nupkg"

    package_files = list(package_dir.glob(pattern))
    if not package_files:
        print(f"❌ No package files found matching {pattern} in {package_dir}")
        return None

    # If multiple files found, take the most recent
    if len(package_files) > 1:
        package_file = max(package_files, key=lambda p: p.stat().st_mtime)
        print(f"⚠️  Multiple package files found, using most recent: {package_file.name}")
    else:
        package_file = package_files[0]

    print(f"✅ Found package file: {package_file}")
    return package_file


def get_nuget_source_name(domain: str, repository: str) -> str | None:
    """Get the NuGet source name for CodeArtifact."""
    print("Getting NuGet source name...")

    success, output = run_command(["dotnet", "nuget", "list", "source"])
    if not success:
        print(f"❌ Failed to list NuGet sources: {output}")
        return None

    # Look for the CodeArtifact source
    expected_source = f"{domain}/{repository}"
    for line in output.split("\n"):
        if expected_source in line:
            # Extract source name (first part before the URL)
            parts = line.strip().split()
            if len(parts) >= MIN_PARTS_FOR_SOURCE_NAME:
                source_name = parts[1]  # Usually the source name is after the number
                print(f"✅ Found NuGet source: {source_name}")
                return source_name

    print(f"❌ Could not find NuGet source for {expected_source}")
    return None


def publish_package(package_path: Path, source_name: str) -> bool:
    """Publish the NuGet package to CodeArtifact."""
    if not package_path.exists():
        print(f"❌ Package file not found: {package_path}")
        return False

    print(f"Publishing package: {package_path}")
    print(f"To source: {source_name}")

    cmd = [
        "dotnet",
        "nuget",
        "push",
        str(package_path),
        "--source",
        source_name,
    ]

    success, output = run_command(cmd)
    if not success:
        print(f"❌ Failed to publish package: {output}")
        return False

    print("✅ Successfully published package to CodeArtifact")
    return True


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Publish pre-built AWA SDK NuGet package to AWS CodeArtifact",
    )
    parser.add_argument(
        "--aws-profile",
        help="AWS profile name to use for authentication",
    )
    parser.add_argument(
        "--domain",
        default="slalom-all",
        help="CodeArtifact domain name (default: slalom-all)",
    )
    parser.add_argument(
        "--domain-owner",
        default="825505919920",
        help="CodeArtifact domain owner account ID (default: 825505919920)",
    )
    parser.add_argument(
        "--repository",
        default="slalom-nuget",
        help="CodeArtifact repository name (default: slalom-nuget)",
    )
    parser.add_argument(
        "--package-name",
        default="Awa.Client",
        help="Name of the NuGet package (default: Awa.Client)",
    )
    parser.add_argument(
        "--package-path",
        default=str(Path(__file__).resolve().parents[2] / "sdk_dist" / "csharp" / "Awa.Client" / "bin" / "Release"),
        help="Directory containing the pre-built NuGet package files",
    )
    parser.add_argument(
        "--version",
        help="Specific version to publish (if not provided, detects from package file)",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip CodeArtifact credential provider installation and configuration",
    )
    parser.add_argument(
        "--skip-duplicate-check",
        action="store_true",
        help="Skip checking if version already exists in CodeArtifact",
    )
    return parser


def setup_codeartifact_tools(skip_setup: bool, aws_profile: str | None) -> None:
    """Set up CodeArtifact tools if not skipped."""
    if not skip_setup:
        if not install_codeartifact_tools():
            sys.exit(1)
        if not configure_codeartifact_profile(aws_profile):
            sys.exit(1)
    else:
        print("✅ Skipping CodeArtifact setup (--skip-setup specified)")


def determine_version(
    version_override: str | None,
    package_dir: Path,
    package_name: str,
) -> str:
    """Determine the version to use for the package."""
    if version_override:
        print(f"✅ Using provided version: {version_override}")
        return version_override

    # Extract version from package file
    version = get_package_version_from_file(package_dir, package_name)
    if not version:
        print("❌ Could not determine package version")
        sys.exit(1)

    return version


def publish_prebuilt_package(
    args: argparse.Namespace,
    version: str,
    env: dict,
) -> None:
    """Publish the pre-built NuGet package to CodeArtifact."""
    # Check if this version already exists to avoid duplicate publishes
    if not args.skip_duplicate_check:
        if check_version_exists(
            args.package_name,
            version,
            args.domain,
            args.repository,
            args.domain_owner,
            env,
        ):
            print(f"✅ Version {version} already exists in CodeArtifact. Skipping publish.")
            return
    else:
        print("⚠️  Skipping duplicate version check")

    # Find the package file
    package_dir = Path(args.package_path)
    package_file = find_package_file(package_dir, args.package_name, version)
    if not package_file:
        print(f"❌ Cannot find package file for {args.package_name} v{version}")
        sys.exit(1)

    # Login to CodeArtifact
    if not login_to_codeartifact(args.domain, args.domain_owner, args.repository, env):
        sys.exit(1)

    # Get NuGet source name
    source_name = get_nuget_source_name(args.domain, args.repository)
    if not source_name:
        sys.exit(1)

    # Publish package
    if not publish_package(package_file, source_name):
        sys.exit(1)

    print(f"🎉 Package {args.package_name} v{version} published successfully!")


def main() -> None:
    """Run the main publishing workflow."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Set up CodeArtifact tools
    setup_codeartifact_tools(args.skip_setup, args.aws_profile)

    # Set up environment
    env = setup_environment(args.aws_profile)

    # Determine version from the pre-built package
    package_dir = Path(args.package_path)
    if not package_dir.exists():
        print(f"❌ Package directory not found: {package_dir}")
        print("Please ensure the package has been built using package_sdk_csharp.py first")
        sys.exit(1)

    version = determine_version(
        args.version,
        package_dir,
        args.package_name,
    )

    # Publish the pre-built package
    publish_prebuilt_package(args, version, env)


if __name__ == "__main__":
    main()
