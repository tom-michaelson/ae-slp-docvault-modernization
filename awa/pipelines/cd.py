import argparse
import asyncio
import os
import sys
from pathlib import Path

import dagger


def get_docker_socket_path() -> str:
    """Detect the correct Docker socket path for different Docker setups."""
    # Common Docker socket paths to check
    socket_paths = [
        "/var/run/docker.sock",  # Standard Docker
        str(Path.home() / ".colima/default/docker.sock"),  # Colima
        str(Path.home() / ".docker/run/docker.sock"),  # Docker Desktop (some configs)
        "/run/user/1000/docker.sock",  # Rootless Docker
    ]

    for path in socket_paths:
        if Path(path).exists():
            return path

    # Default to standard path if none found
    return "/var/run/docker.sock"


def setup_container(client: dagger.Client, src: dagger.Directory) -> dagger.Container:
    """Create and configure the base container with all system dependencies."""
    return (
        client.container()
        .from_("python:3.12-slim")
        .with_env_variable("DAGGER_NO_NAG", "1")
        # Combined system setup - install all dependencies in single layer
        .with_exec(
            [
                "sh",
                "-c",
                "set -eux && "
                # Update and install base packages
                "apt-get update && "
                "apt-get install -y --no-install-recommends "
                "make curl ca-certificates gnupg git lsb-release unzip build-essential && "
                # Install AWS CLI
                "curl -fsSL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip && "
                "unzip -q awscliv2.zip && "
                "./aws/install && "
                "rm -rf awscliv2.zip aws/ && "
                # Setup Docker repository and install Docker
                "install -m 0755 -d /etc/apt/keyrings && "
                "curl -fsSL https://download.docker.com/linux/debian/gpg | "
                "gpg --dearmor -o /etc/apt/keyrings/docker.gpg && "
                "chmod a+r /etc/apt/keyrings/docker.gpg && "
                'echo "deb [arch=$(dpkg --print-architecture) '
                "signed-by=/etc/apt/keyrings/docker.gpg] "
                'https://download.docker.com/linux/debian $(lsb_release -cs) stable" | '
                "tee /etc/apt/sources.list.d/docker.list > /dev/null && "
                "apt-get update && "
                "apt-get install -y --no-install-recommends "
                "docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin && "
                # Install Node.js 22.x
                "curl -fsSL https://deb.nodesource.com/setup_22.x -o nodesource_setup.sh && "
                "bash nodesource_setup.sh && "
                "apt-get install -y --no-install-recommends nodejs && "
                "corepack enable && "
                "corepack prepare pnpm@latest --activate && "
                "rm -f nodesource_setup.sh && "
                # Install Temporal CLI
                "curl -sSf https://temporal.download/cli.sh | sh && "
                "cp /root/.temporalio/bin/temporal /usr/local/bin/ && "
                # Install uv
                "pip install --no-cache-dir uv && "
                # Clean up caches and temporary files
                "apt-get clean && "
                "rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* /root/.cache",
            ],
        )
        .with_mounted_directory("/project", src)
        .with_workdir("/project")
        # Mount Docker socket for Docker-in-Docker (auto-detect correct path)
        .with_unix_socket("/var/run/docker.sock", client.host().unix_socket(get_docker_socket_path()))
    )


def setup_environment(container: dagger.Container, env_config: dict) -> dagger.Container:
    """Configure environment variables and project setup."""
    # Configure environment variables
    container = (
        container.with_env_variable("AWS_REGION", env_config["aws_region"])
        .with_env_variable("AWS_ROLE_ARN", env_config["aws_role_arn"])
        .with_env_variable("AWS_WEB_IDENTITY_TOKEN_FILE", env_config["aws_web_identity_token_file"])
        .with_env_variable("BITBUCKET_STEP_OIDC_TOKEN", env_config["bitbucket_oidc_token"])
        .with_env_variable("PNPM_CI", "true")
    )

    # Build the setup command based on mode
    setup_commands = ["set -eux"]

    # Clean existing node_modules to prevent conflicts
    setup_commands.append("rm -rf node_modules || true")
    setup_commands.append("rm -rf ui/node_modules || true")

    # Ensure pnpm is available (refresh corepack)
    setup_commands.append("corepack enable && corepack use pnpm@latest")

    # Always install project dependencies
    setup_commands.append("make install")

    # Execute the combined setup
    container = container.with_exec(["sh", "-c", " && ".join(setup_commands)])

    return container


def run_pipeline_steps(container: dagger.Container, pipeline_config: dict) -> dagger.Container:
    """Execute the main pipeline steps: checks, build, and deploy."""
    is_local_mode = pipeline_config.get("is_local_mode", False)
    # Run pre-commit checks
    container = container.with_exec(["uv", "run", "pre-commit", "run", "--all-files"])

    # Build docs (commented out)
    # container = container.with_exec(["make", "docs-build"])

    # Handle .env file based on mode
    if is_local_mode:
        # Local mode: use existing .env file, but ensure HOME_DIR is set
        container = container.with_exec(
            [
                "sh",
                "-c",
                "if [ ! -f .env ]; then echo 'Error: .env file not found in local mode'; exit 1; fi && "
                "echo 'Using existing .env file:' && cat .env && "
                "echo 'Ensuring HOME_DIR is set in .env...' && "
                "if ! grep -q '^HOME_DIR=' .env; then echo 'HOME_DIR=$HOME' >> .env; fi && "
                "echo 'Updated .env file:' && cat .env",
            ],
        )
    else:
        # CD mode: create .env file from environment variables
        container = container.with_exec(
            [
                "sh",
                "-c",
                f"cat > .env << 'EOF'\n"
                f"PUBLIC_AUTH_MODE={pipeline_config['public_auth_mode']}\n"
                f"PUBLIC_DOCS_ONLY=true\n"
                f"PUBLIC_AUTH_TRUST_HOST=true\n"
                f"AUTH_COGNITO_CLIENT_ID={pipeline_config['auth_cognito_client_id']}\n"
                f"AUTH_COGNITO_CLIENT_SECRET={pipeline_config['auth_cognito_client_secret']}\n"
                f"AUTH_COGNITO_ISSUER={pipeline_config['auth_cognito_issuer']}\n"
                f"AUTH_SECRET={pipeline_config['auth_secret']}\n"
                f"HOME_DIR=$HOME\n"
                f"EOF\n"
                f"echo 'Created .env file from environment variables:' && cat .env",
            ],
        )

    # Create web-identity-token file for OIDC authentication (only for pipeline mode)
    if not is_local_mode and pipeline_config["bitbucket_oidc_token"]:
        container = container.with_exec(
            [
                "sh",
                "-c",
                (
                    f'echo -n "{pipeline_config["bitbucket_oidc_token"]}" > '
                    f"{pipeline_config['aws_web_identity_token_file']}"
                ),
            ],
        )
        container = container.with_exec(
            ["sh", "-c", f"echo 'Created web-identity-token file at {pipeline_config['aws_web_identity_token_file']}'"],
        )

    # Verify UI source structure before build
    container = container.with_exec(
        [
            "sh",
            "-c",
            "echo 'Verifying UI source structure:' && "
            "ls -la ui/ && "
            "echo 'UI src directory:' && "
            "ls -la ui/src/ && "
            "echo 'UI src/pages directory:' && "
            "ls -la ui/src/pages/ || echo 'WARNING: ui/src/pages not found'",
        ],
    )

    # Build Docker image
    container = container.with_exec(
        [
            "docker",
            "compose",
            "-f",
            "docker-compose.awa.yml",
            "build",
            "ui",
        ],
    )

    # Show built images
    container = container.with_exec(
        ["sh", "-c", "echo 'Built images:' && docker images --filter 'reference=project-ui'"],
    )

    if is_local_mode:
        # Local mode: just test the built image locally
        container = container.with_exec(
            [
                "sh",
                "-c",
                "echo '✅ Build completed successfully in local mode!' && "
                "echo 'Image built: project-ui:latest' && "
                "echo 'To run locally: docker run -p 8000:8000 project-ui:latest'",
            ],
        )
    else:
        # Pipeline mode: tag and push to ECR
        image_name = (
            f"{pipeline_config['ecr_registry']}/{pipeline_config['ecr_repository']}:{pipeline_config['ecr_image_tag']}"
        )
        image_name_latest = f"{pipeline_config['ecr_registry']}/{pipeline_config['ecr_repository']}:latest"

        container = container.with_exec(
            [
                "sh",
                "-c",
                f"set -eux && "
                # Verify AWS identity
                f"echo 'AWS Identity:' && aws sts get-caller-identity && "
                # Tag image for ECR
                f"docker tag project-ui:latest {image_name} && "
                # Login to ECR and push
                f"aws ecr get-login-password --region {pipeline_config['aws_region']} | "
                f"docker login --username AWS --password-stdin {pipeline_config['ecr_registry']} && "
                f"docker push {image_name} && "
                f"echo 'Successfully pushed {image_name}'",
                f"docker tag project-ui:latest {image_name_latest} && "
                f"docker push {image_name_latest} && "
                f"echo 'Successfully pushed {image_name_latest}'",
            ],
        )
        container = container.with_exec(
            [
                "sh",
                "-c",
                f"set -eux && "
                # Verify AWS identity
                f"echo 'AWS Identity:' && aws sts get-caller-identity && "
                # Tag image for ECR
                f"docker tag project-ui:latest {image_name_latest} && "
                # Login to ECR and push
                f"aws ecr get-login-password --region {pipeline_config['aws_region']} | "
                f"docker login --username AWS --password-stdin {pipeline_config['ecr_registry']} && "
                f"docker push {image_name_latest} && "
                f"echo 'Successfully pushed {image_name_latest}'",
            ],
        )

        # Push to the Slalom Common ECR registry
        common_image_name = (
            f"{pipeline_config['common_ecr_registry']}/"
            f"{pipeline_config['common_ecr_repository']}:"
            f"{pipeline_config['ecr_image_tag']}"
        )
        container = container.with_exec(
            [
                "sh",
                "-c",
                f"set -eux && "
                f"echo '=== PUSHING TO SECOND ECR REGISTRY ===' && "
                f"echo 'AWS Identity:' && aws sts get-caller-identity && "
                f"docker tag project-ui:latest {common_image_name} && "
                f"aws ecr get-login-password --region {pipeline_config['aws_region']} | "
                f"docker login --username AWS --password-stdin {pipeline_config['common_ecr_registry']} && "
                f"docker push {common_image_name} && "
                f"echo 'Successfully pushed {common_image_name}'",
            ],
        )
    return container


async def main() -> None:
    """Orchestrate the main CD pipeline."""
    parser = argparse.ArgumentParser(description="AWA CD Pipeline - Build and optionally push Docker images")
    parser.add_argument(
        "image_tag",
        nargs="?",
        default="latest",
        help="Tag for the Docker image (default: latest)",
    )
    parser.add_argument(
        "--cd",
        nargs="?",
        const=True,
        default=None,
        type=lambda x: x.lower() in ("true", "1", "yes", "on"),
        help="Run in CD pipeline mode with ECR push (default: auto-detect based on CI env)",
    )
    args = parser.parse_args()

    # Determine if we're running locally or in CI/CD
    # Default to local mode unless explicitly running in CI or --cd=true is passed
    default_local_mode = not bool(os.getenv("CI"))
    # If --cd is specified, invert the logic (--cd=true means NOT local mode)
    is_local_mode = not args.cd if args.cd is not None else default_local_mode

    ecr_registry = os.getenv("ECR_REGISTRY")
    ecr_repository = os.getenv("ECR_REPOSITORY")
    common_ecr_registry = os.getenv("COMMON_ECR_REGISTRY")
    common_ecr_repository = os.getenv("COMMON_ECR_REPOSITORY")
    ecr_image_tag = args.image_tag
    public_auth_mode = os.getenv("PUBLIC_AUTH_MODE", "cognito")
    auth_cognito_client_id = os.getenv("AUTH_COGNITO_CLIENT_ID", "")
    auth_cognito_client_secret = os.getenv("AUTH_COGNITO_CLIENT_SECRET", "")
    auth_cognito_issuer = os.getenv("AUTH_COGNITO_ISSUER", "")
    auth_secret = os.getenv("AUTH_SECRET", "default_secret_change_in_production")

    # AWS configuration for ECR (using OIDC) - matches Bitbucket Pipelines setup
    aws_region = os.getenv("AWS_REGION", "us-east-1")
    aws_role_arn = os.getenv("AWS_OIDC_ROLE_ARN", "")
    bitbucket_oidc_token = os.getenv("BITBUCKET_STEP_OIDC_TOKEN", "")
    aws_web_identity_token_file = "/project/web-identity-token"  # noqa: S105

    # Validate required variables only for non-local mode
    if not is_local_mode and not (ecr_registry and ecr_repository):
        raise ValueError("ECR_REGISTRY and ECR_REPOSITORY must be set for pipeline mode")

    # Set defaults for local mode
    if is_local_mode:
        ecr_registry = ecr_registry or "local.registry"
        ecr_repository = ecr_repository or "awa-ui"

    # Note: AWS_ROLE_ARN and AWS_WEB_IDENTITY_TOKEN_FILE will be provided by the CI/CD environment
    # for OIDC authentication. If not using OIDC, traditional AWS credentials can be used instead.

    env_config = {
        "aws_region": aws_region,
        "aws_role_arn": aws_role_arn,
        "aws_web_identity_token_file": aws_web_identity_token_file,
        "bitbucket_oidc_token": bitbucket_oidc_token,
        "is_local_mode": is_local_mode,
    }

    pipeline_config = {
        "ecr_registry": ecr_registry,
        "ecr_repository": ecr_repository,
        "common_ecr_registry": common_ecr_registry,
        "common_ecr_repository": common_ecr_repository,
        "ecr_image_tag": ecr_image_tag,
        "public_auth_mode": public_auth_mode,
        "auth_cognito_client_id": auth_cognito_client_id,
        "auth_cognito_client_secret": auth_cognito_client_secret,
        "auth_cognito_issuer": auth_cognito_issuer,
        "auth_secret": auth_secret,
        "aws_region": aws_region,
        "bitbucket_oidc_token": bitbucket_oidc_token,
        "aws_web_identity_token_file": aws_web_identity_token_file,
        "is_local_mode": is_local_mode,
    }

    async with dagger.Connection() as client:
        src = client.host().directory(
            ".",
            exclude=[".venv", "__pycache__", ".mypy_cache", ".pytest_cache"],
        )

        # Set up container with system dependencies
        python = setup_container(client, src)

        # Configure environment and project setup
        python = setup_environment(python, env_config)

        # Run the main pipeline steps
        python = run_pipeline_steps(python, pipeline_config)

        # Check final exit code for entire pipeline
        final_exit_code = await python.exit_code()
        if final_exit_code != 0:
            sys.exit(final_exit_code)


if __name__ == "__main__":
    asyncio.run(main())
