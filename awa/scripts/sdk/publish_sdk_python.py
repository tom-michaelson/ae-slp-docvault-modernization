#!/usr/bin/env python3
"""Script to publish AWA Python SDK package to AWS CodeArtifact.

This script publishes a pre-built Python package to AWS CodeArtifact.
The package should already be built using package_sdk_python.py.
Supports both AWS profiles and environment credentials.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Add parent directory to path for importing the helper
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scripts.sdk.aws_auth_helper import configure_aws_environment, get_auth_method_description

# Constants
MIN_PARTS_FOR_SOURCE_NAME = 2


def run_command(cmd: list[str], env: dict | None = None, cwd: Path | None = None) -> tuple[bool, str]:
    """Run a shell command and return success status and output."""
    # Print the command being run for debugging
    print(f"🔍 Running command: {' '.join(cmd)}")
    if cwd:
        print(f"   Working directory: {cwd}")

    # Show relevant environment variables for AWS commands
    if cmd[0] == "aws":
        effective_env = env or os.environ.copy()
        auth_desc = get_auth_method_description(effective_env)
        if auth_desc != "No AWS authentication configured":
            print(f"   {auth_desc}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            env=env or os.environ.copy(),
            cwd=cwd,
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, f"Command failed: {e.stderr.strip()}"


def check_prerequisites() -> bool:
    """Check if required tools are installed."""
    print("Checking prerequisites...")

    # Check if AWS CLI is installed
    success, output = run_command(["aws", "--version"])
    if not success:
        print("❌ AWS CLI is not installed")
        return False
    print(f"✅ AWS CLI version: {output.split()[0]}")

    # Check if uv is installed (needed for publish command)
    success, output = run_command(["uv", "--version"])
    if not success:
        print("❌ uv is not installed")
        return False
    print(f"✅ uv version: {output}")

    return True


def get_codeartifact_token(
    domain: str,
    domain_owner: str,
    env: dict,
) -> str | None:
    """Get authorization token from AWS CodeArtifact."""
    print("Getting CodeArtifact authorization token...")

    cmd = [
        "aws",
        "codeartifact",
        "get-authorization-token",
        "--domain",
        domain,
        "--domain-owner",
        domain_owner,
        "--query",
        "authorizationToken",
        "--output",
        "text",
    ]

    success, output = run_command(cmd, env)
    if not success:
        print(f"❌ Failed to get CodeArtifact token: {output}")
        return None

    token = output.strip()
    # Check if we got a valid token (AWS CLI returns "None" as string if no token)
    none_string = "None"
    if token and token != none_string:
        print("✅ CodeArtifact authorization token obtained")
        return token
    print("❌ Invalid or empty CodeArtifact token")
    return None


def setup_environment(aws_profile: str | None) -> dict:
    """Set up environment variables for AWS authentication.

    This is a wrapper around the shared helper for backward compatibility.
    """
    return configure_aws_environment(aws_profile)


def get_codeartifact_repository_url(
    domain: str,
    domain_owner: str,
    repository: str,
    env: dict,
) -> str | None:
    """Get the repository URL for AWS CodeArtifact."""
    print(f"Getting CodeArtifact repository URL for domain: {domain}, repository: {repository}")

    cmd = [
        "aws",
        "codeartifact",
        "get-repository-endpoint",
        "--domain",
        domain,
        "--domain-owner",
        domain_owner,
        "--repository",
        repository,
        "--format",
        "pypi",
    ]

    success, output = run_command(cmd, env)
    if not success:
        print(f"❌ Failed to get repository URL: {output}")
        return None

    try:
        result = json.loads(output)
        repository_endpoint = result.get("repositoryEndpoint")
        # For publishing, use the base repository endpoint without /simple/
        # The /simple/ suffix is only needed for package index/fetching, not publishing
        if repository_endpoint and not repository_endpoint.endswith("/"):
            repository_url = f"{repository_endpoint}/"
        else:
            repository_url = repository_endpoint
        print(f"✅ Repository URL: {repository_url}")
        return repository_url
    except (json.JSONDecodeError, KeyError) as e:
        print(f"❌ Failed to parse repository URL response: {e}")
        return None


def get_package_version(package_path: Path) -> str | None:
    """Extract version from pyproject.toml file."""
    pyproject_path = package_path / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"❌ pyproject.toml not found: {pyproject_path}")
        return None

    try:
        content = pyproject_path.read_text()
        match = re.search(r'version\s*=\s*"([^"]*)"', content)
        if match:
            version = match.group(1)
            print(f"✅ Found package version: {version}")
            return version
        print("❌ Could not find version in pyproject.toml")
        return None
    except OSError as e:
        print(f"❌ Failed to read pyproject.toml: {e}")
        return None


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
        "pypi",
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


def publish_package(
    package_path: Path,
    repository_url: str,
    package_name: str,
    version: str,
    token: str,
    env: dict,
) -> bool:
    """Publish the pre-built Python package to CodeArtifact using uv."""
    if not package_path.exists():
        print(f"❌ Package directory not found: {package_path}")
        return False

    print(f"Publishing package: {package_name} v{version}")
    print(f"To repository: {repository_url}")

    # Find the built package files
    dist_dir = package_path / "dist"
    if not dist_dir.exists():
        print(f"❌ Dist directory not found: {dist_dir}")
        print("   Please ensure the package is built using package_sdk_python.py first")
        return False

    # Look for wheel and tar.gz files (both hyphen and underscore variations)
    wheel_files = list(dist_dir.glob("*.whl"))
    tar_files = list(dist_dir.glob("*.tar.gz"))

    # Filter to only files containing the version
    wheel_files = [f for f in wheel_files if version in f.name]
    tar_files = [f for f in tar_files if version in f.name]

    if not wheel_files and not tar_files:
        print(f"❌ No package files found for version {version} in {dist_dir}")
        print(f"   Available files: {list(dist_dir.glob('*'))}")
        print("   Please ensure the package is built with the correct version")
        return False

    print(f"   Found {len(wheel_files)} wheel file(s) and {len(tar_files)} source distribution(s)")

    # Set up environment with CodeArtifact credentials
    publish_env = env.copy()
    publish_env["UV_PUBLISH_USERNAME"] = "aws"
    publish_env["UV_PUBLISH_PASSWORD"] = token

    # Print authentication info (without exposing token)
    token_preview_length = 4
    print("\n📦 Publishing with authentication:")
    print("   Username: aws")
    print(f"   Token: {'*' * 10}...{token[-token_preview_length:] if len(token) > token_preview_length else '****'}")
    print(f"   Repository URL: {repository_url}")

    # Publish using uv
    cmd = [
        "uv",
        "publish",
        "--publish-url",
        repository_url,
    ]

    # Add all found package files (use relative paths from package directory)
    package_files = wheel_files + tar_files
    cmd.extend(str(package_file.relative_to(package_path)) for package_file in package_files)

    # Print the files being published
    print(f"\n📦 Publishing {len(package_files)} file(s):")
    for pf in package_files:
        print(f"   - {pf.name}")
    print()

    success, output = run_command(cmd, publish_env, cwd=package_path)
    if not success:
        print(f"❌ Failed to publish package: {output}")
        # Check for common issues and provide helpful error messages
        if "404" in output:
            print("   This may indicate that the CodeArtifact repository doesn't exist")
            print("   or you don't have permissions to publish to it.")
        elif "401" in output or "403" in output:
            print("   This indicates an authentication or authorization issue.")
            print("   Please check your AWS credentials and CodeArtifact permissions.")
        elif "409" in output or "already exists" in output.lower():
            print(f"   Version {version} may already exist in the repository")
        return False

    print("✅ Successfully published package to CodeArtifact")
    return True


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="Publish pre-built AWA Python SDK package to AWS CodeArtifact",
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
        default="slalom-pypi",
        help="CodeArtifact repository name (default: slalom-pypi)",
    )
    parser.add_argument(
        "--package-name",
        default="awa-client",
        help="Name of the Python package (default: awa-client)",
    )
    parser.add_argument(
        "--package-path",
        default=str(Path(__file__).resolve().parents[2] / "sdk_dist" / "python"),
        help="Path to the Python package directory (default: sdk_dist/python)",
    )
    parser.add_argument(
        "--version",
        help="Specific version to publish (if not provided, detects from package file)",
    )
    parser.add_argument(
        "--skip-token",
        action="store_true",
        help="Skip CodeArtifact token generation (use existing authentication)",
    )
    parser.add_argument(
        "--skip-duplicate-check",
        action="store_true",
        help="Skip checking if package version already exists",
    )
    return parser


def get_codeartifact_auth_token(
    domain: str,
    domain_owner: str,
    env: dict,
    skip_token: bool,
) -> str | None:
    """Get CodeArtifact authentication token if not skipped."""
    if skip_token:
        print("✅ Skipping CodeArtifact token generation (--skip-token specified)")
        return os.environ.get("UV_PUBLISH_PASSWORD") or os.environ.get("AWS_CODEARTIFACT_TOKEN")
    return get_codeartifact_token(domain, domain_owner, env)


def determine_version(
    version_override: str | None,
    package_path: Path,
) -> str:
    """Determine the version to use for the package."""
    if version_override:
        print(f"✅ Using provided version: {version_override}")
        return version_override

    # Extract version from package file
    version = get_package_version(package_path)
    if not version:
        print("❌ Could not determine package version")
        sys.exit(1)

    return version


def publish_to_codeartifact(
    args: argparse.Namespace,
    env: dict,
) -> None:
    """Publish the pre-built Python package to CodeArtifact."""
    package_path = Path(args.package_path)

    # Determine version to use
    version = determine_version(args.version, package_path)

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

    # Get CodeArtifact repository URL
    repository_url = get_codeartifact_repository_url(
        args.domain,
        args.domain_owner,
        args.repository,
        env,
    )
    if not repository_url:
        sys.exit(1)

    # Get CodeArtifact authentication token
    auth_token = get_codeartifact_auth_token(
        args.domain,
        args.domain_owner,
        env,
        args.skip_token,
    )
    if not auth_token:
        print("❌ Failed to get CodeArtifact authentication token")
        sys.exit(1)

    # Publish package
    if not publish_package(package_path, repository_url, args.package_name, version, auth_token, env):
        sys.exit(1)

    print(f"🎉 Package {args.package_name} v{version} published successfully!")


def main() -> None:
    """Run the main publishing workflow."""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Set up environment
    env = setup_environment(args.aws_profile)

    # Publish the pre-built package
    publish_to_codeartifact(args, env)


if __name__ == "__main__":
    main()
