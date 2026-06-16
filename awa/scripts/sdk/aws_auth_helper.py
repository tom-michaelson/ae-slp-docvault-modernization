"""Shared AWS authentication helper for SDK scripts.

This module provides consistent AWS credential configuration across all SDK publishing scripts.
Supports three authentication methods in order of precedence:
1. AWS Profile with mounted credentials
2. OIDC/Web Identity Token (used by Bitbucket pipelines)
3. Static AWS credentials (access key/secret key)
"""

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import dagger


def configure_aws_environment(aws_profile: str | None = None, verbose: bool = True) -> dict:
    """Set up environment variables for AWS authentication.

    Supports three authentication methods in order of precedence:
    1. AWS Profile with mounted credentials
    2. OIDC/Web Identity Token (used by Bitbucket pipelines)
    3. Static AWS credentials (access key/secret key)

    Args:
        aws_profile: Optional AWS profile name to use
        verbose: Whether to print status messages

    Returns:
        Dictionary of environment variables configured for AWS authentication

    Raises:
        SystemExit: If no valid authentication method is available

    """
    env = os.environ.copy()

    if aws_profile:
        env["AWS_PROFILE"] = aws_profile
        if verbose:
            print(f"✅ Using AWS profile: {aws_profile}")
    elif os.getenv("AWS_ROLE_ARN") and os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"):
        # Use OIDC/Web Identity Token authentication (used by Bitbucket pipelines)
        if verbose:
            print("✅ Using OIDC/Web Identity Token authentication")
        env["AWS_ROLE_ARN"] = os.getenv("AWS_ROLE_ARN", "")
        env["AWS_WEB_IDENTITY_TOKEN_FILE"] = os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE", "")

        # Also pass through the role session name if set
        if os.getenv("AWS_ROLE_SESSION_NAME"):
            env["AWS_ROLE_SESSION_NAME"] = os.getenv("AWS_ROLE_SESSION_NAME", "")
    elif "AWS_ACCESS_KEY_ID" in os.environ and "AWS_SECRET_ACCESS_KEY" in os.environ:
        if verbose:
            print("✅ Using AWS credentials from environment variables")
        env["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID", "")
        env["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        if os.getenv("AWS_SESSION_TOKEN"):
            env["AWS_SESSION_TOKEN"] = os.getenv("AWS_SESSION_TOKEN", "")
    else:
        if verbose:
            print("❌ No AWS authentication method available. Please provide one of:")
            print("   1. AWS profile name via --aws-profile")
            print("   2. OIDC credentials via AWS_ROLE_ARN and AWS_WEB_IDENTITY_TOKEN_FILE")
            print("   3. Static credentials via AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        sys.exit(1)

    return env


def get_auth_method_description(env: dict | None = None) -> str:
    """Get a description of the current AWS authentication method.

    Args:
        env: Environment dictionary to check, defaults to os.environ

    Returns:
        String describing the authentication method in use

    """
    if env is None:
        env = os.environ

    if "AWS_PROFILE" in env:
        return f"AWS_PROFILE: {env['AWS_PROFILE']}"
    if "AWS_ROLE_ARN" in env and "AWS_WEB_IDENTITY_TOKEN_FILE" in env:
        return "Using OIDC/Web Identity Token authentication"
    if "AWS_ACCESS_KEY_ID" in env:
        return "Using AWS credentials from environment"
    return "No AWS authentication configured"


def configure_aws_credentials_for_dagger(
    container: "dagger.Container",
    client: "dagger.Client",
    aws_profile: str | None = None,
) -> "dagger.Container":
    """Configure AWS credentials for a Dagger container.

    This is specifically for use with Dagger pipelines and includes file mounting logic.

    Args:
        container: The dagger container to configure
        client: The dagger client for accessing host resources
        aws_profile: Optional AWS profile name to use

    Returns:
        The container with AWS credentials configured

    """
    aws_profile = aws_profile or os.getenv("AWS_PROFILE")

    if aws_profile:
        container = container.with_env_variable("AWS_PROFILE", aws_profile)
        # Mount AWS credentials from host
        aws_creds_path = Path.home() / ".aws"
        if aws_creds_path.exists():
            aws_creds_dir = client.host().directory(str(aws_creds_path))
            container = container.with_mounted_directory("/root/.aws", aws_creds_dir)
    elif os.getenv("AWS_ROLE_ARN") and os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"):
        # Use OIDC/Web Identity Token authentication (used by Bitbucket pipelines)
        container = container.with_env_variable("AWS_ROLE_ARN", os.getenv("AWS_ROLE_ARN", ""))
        container = container.with_env_variable("AWS_WEB_IDENTITY_TOKEN_FILE", "/tmp/web-identity-token")  # noqa: S108

        # Mount the web identity token file
        token_file_path = os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE", "")
        if token_file_path and Path(token_file_path).exists():
            token_file = client.host().file(token_file_path)
            container = container.with_mounted_file("/tmp/web-identity-token", token_file)  # noqa: S108

        # Also pass through the role session name if set
        if os.getenv("AWS_ROLE_SESSION_NAME"):
            container = container.with_env_variable("AWS_ROLE_SESSION_NAME", os.getenv("AWS_ROLE_SESSION_NAME", ""))
    elif os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        # Use environment credentials
        container = container.with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", ""))
        container = container.with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
        if os.getenv("AWS_SESSION_TOKEN"):
            container = container.with_env_variable("AWS_SESSION_TOKEN", os.getenv("AWS_SESSION_TOKEN", ""))

    return container
