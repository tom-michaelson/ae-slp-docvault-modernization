# Pipeline Runner

The AWA Workflow Runner is a Dagger-based pipeline that provides a consistent, containerized environment for executing AWA workflows in CI/CD systems.

## Overview

The `awa_workflow_runner.py` script creates a complete AWA execution environment using Dagger containers, handling dependency installation, service startup, and workflow execution. This approach ensures reproducible builds and eliminates environment-specific issues.

## Why Dagger?

This pipeline runner leverages [Dagger](https://dagger.io/) as the container orchestration platform to provide significant advantages for both development and production environments:

**Local Development Benefits**

- Run the complete pipeline locally with `dagger run uv run pipelines/awa_workflow_runner.py`
- Same execution environment locally as in CI/CD - no surprises
- Faster debugging cycle - test changes without pushing to remote CI
- Immediate feedback on configuration or dependency issues

**Production Reliability**

- Consistent container environment eliminates deployment variations
- Automatic dependency resolution and service orchestration
- Built-in retry mechanisms and error handling
- Comprehensive logging for troubleshooting failures

**Cross-Platform Compatibility**

- Works on any system that can run Docker containers
- No CI platform vendor lock-in (GitHub Actions, GitLab CI, Jenkins, etc.)
- Easy migration between different deployment environments
- Portable across development team machines

**Performance Optimizations**

- Intelligent caching reduces subsequent run times
- Parallel service startup and dependency installation
- Resource-efficient container reuse
- Automatic cleanup of temporary resources

For more information about Dagger's capabilities, see the [official documentation](https://docs.dagger.io/).

## Architecture

```mermaid
graph TD
    A[GitHub Actions] --> B[AWS OIDC Authentication]
    B --> C[Dagger Container]
    C --> D[Python 3.12 Base Image]
    D --> E[Install Dependencies]
    E --> F[AWS CLI + CodeArtifact Auth]
    E --> G[UV Package Manager]
    E --> H[Node.js 22.x]
    E --> I[Temporal CLI]
    F --> J[Private SDK Access]
    G --> K[AWA Core Setup]
    H --> L[PNPM Package Manager]
    J --> K
    K --> M[Start AWA Services]
    L --> N[Start Recipes Worker]
    M --> O[Execute Workflow]
    N --> O
    O --> P[Workflow Results]
```

## Key Features

- **Containerized Execution** - Consistent Python 3.12 environment isolated from host system dependencies
- **AWS Integration** - OIDC authentication for secure access to CodeArtifact private packages
- **Dependency Management** - UV for fast Python package management with AWS CodeArtifact support
- **Service Orchestration** - Automatic Temporal server startup and AWA API service initialization
- **Flexible Configuration** - Support for local and remote repositories with configurable branch selection
- **Fast Failure Detection** - Early detection of authentication and dependency issues

## Usage

### Basic Command Line

```bash
# Execute with remote repositories using Dagger
dagger run uv run pipelines/awa_workflow_runner.py \
  --workflow github-pr-description \
  --input '{"owner":"slalombuild","repo":"agentic-workflow-accelerator-helper","pull_number":123}' \
  --cookbook-branch feature/github-pr-desc \
  --core-branch feature/github-pr-desc \
```

### With Local Development

```bash
# Use local repositories for development
dagger run uv run pipelines/awa_workflow_runner.py \
  --workflow github-pr-description \
  --input '{"owner":"slalombuild","repo":"agentic-workflow-accelerator-helper","pull_number":123}' \
  --local-cookbook-path "../agentic-workflow-accelerator-cookbook" \
  --local-awa-path "../agentic-workflow-accelerator" \
```

## Configuration Options

### Command Line Arguments

| Argument                | Description                                                                      | Default       | Required |
| ----------------------- | -------------------------------------------------------------------------------- | ------------- | -------- |
| `--workflow`            | AWA workflow name to execute                                                     | -             | ✅       |
| `--input`               | JSON input string for workflow                                                   | `""`          | ❌       |
| `--cookbook-branch`     | Cookbook repository branch                                                       | `main`        | ❌       |
| `--core-branch`         | Core AWA repository branch                                                       | `main`        | ❌       |
| `--local-cookbook-path` | Local cookbook directory path                                                    | -             | ❌       |
| `--local-awa-path`      | Local AWA core directory path                                                    | -             | ❌       |
| `--skip-validation`     | Skip JSON input validation                                                       | `false`       | ❌       |
| `--queue`               | Temporal queue name (must match the queue where workflow workers are registered) | `awa_default` | ❌       |

### Environment Variables

#### Required Variables

```bash
# GitHub integration
export GH_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxx"

# AI/LLM services
export OPENAI_API_KEY="sk-xxxxxxxxxxxx"

# AWA repository access (if using remote repos)
export BITBUCKET_USERNAME="your-username"
export BITBUCKET_PASSWORD="your-app-password"

# AWS CodeArtifact (CI/CD environments)
export AWS_ACCESS_KEY_ID="AKIA..."           # Set by OIDC
export AWS_SECRET_ACCESS_KEY="..."           # Set by OIDC
export AWS_SESSION_TOKEN="..."               # Set by OIDC
export AWS_DEFAULT_REGION="us-east-1"        # CodeArtifact region
```

#### GitHub Repository Variables

```bash
# Set as Repository Variable (not Secret) in GitHub Settings > Secrets and Variables > Actions > Variables
AWS_OIDC_ROLE_ARN="arn:aws:iam::YOUR_ACCOUNT_ID:role/your-github-actions-role"
```

#### Local Development Variables

```bash
# AWS Profile for local CodeArtifact access
export CODEARTIFACT_AWS_PROFILE="slalom-codeartifact"
```

#### Optional Configuration

```bash
# AWA service configuration
export AWA_API_BASE_URL="http://localhost:8001"
export TEMPORAL_SERVER_HOST="0.0.0.0"
```

## Service Orchestration & Execution

The pipeline automatically handles the complete service startup and workflow execution process:

**AWS Authentication & Setup:**

1. **Environment Detection** - Automatically detects CI vs local environment
2. **CodeArtifact Authentication** - Sets up access to private AWS CodeArtifact packages
3. **Credential Validation** - Verifies AWS access and CodeArtifact permissions
4. **Fast Failure** - Exits immediately if authentication or CodeArtifact access fails

**Service Startup:**

1. **AWA Core Services** - Starts Temporal server, worker, and API services in detached mode
2. **Recipes Worker** - Initializes cookbook recipes worker and registers workflows
3. **Health Checks** - Waits for services to be ready before proceeding
4. **Dependency Verification** - Confirms all private packages are accessible

**Workflow Execution:**

- Validates JSON input (unless `--skip-validation` is used)
- Executes the specified workflow on the designated queue
- Provides comprehensive logging throughout the process
- Real-time output streaming for immediate feedback

## Local Development

### Repository Mounting

For local development, the runner can mount local directories instead of cloning:

```python
# Mount local cookbook
if args.local_cookbook_path:
    cookbook_dir = client.host().directory(
        args.local_cookbook_path,
        exclude=[".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"]
    )
    python = python.with_mounted_directory("/local-cookbook", cookbook_dir)
```

### Development Workflow

1. **Make local changes** to cookbook or AWA core
2. **Run with local paths** to test changes immediately
3. **No repository cloning** - faster iteration cycles
4. **Consistent environment** - same container as CI

Example development command:

```bash
dagger run uv run pipelines/awa_workflow_runner.py \
  --workflow github-pr-description \
  --input '{"owner":"slalombuild","repo":"agentic-workflow-accelerator-helper","pull_number":123}' \
  --local-cookbook-path "../agentic-workflow-accelerator-cookbook" \
  --local-awa-path "../agentic-workflow-accelerator" \
  --skip-validation
```

## Error Handling and Logging

### Comprehensive Log Collection

```bash
# On workflow failure, dump all logs
echo "=== AWA CORE SERVICES LOG ==="
cat awa_services.log

echo "=== COOKBOOK RECIPES WORKER LOG ==="
cat recipes.log
```

### Comprehensive Logging

The pipeline provides detailed logging for debugging and monitoring:

- **AWA Core Services** logs are captured and displayed at completion
- **Recipes Worker** logs show workflow registration and execution details
- All logs are available for troubleshooting both successful runs and failures

## Troubleshooting

### Common Issues

**Service Startup Failures**

```bash
# Check if Temporal server started
temporal workflow list --limit 1

# Review service logs
cat awa_services.log
```

**Recipes Worker Issues**

```bash
# Check worker registration
grep "Worker started\|Connected to Temporal" recipes.log
```

**CodeArtifact Authentication Issues**

```bash
# Check AWS authentication (CI/CD)
aws sts get-caller-identity

# Test CodeArtifact access
aws codeartifact get-authorization-token --domain your-domain --domain-owner YOUR_CODEARTIFACT_ACCOUNT_ID

# Check for CodeArtifact errors in logs
grep -i "401 Unauthorized\|CodeArtifact\|Failed to fetch.*codeartifact" *.log

# Verify local AWS profile (local development)
aws configure list-profiles | grep your-codeartifact-profile
```

**General Authentication Problems**

````bash
# Verify GitHub credentials are set
echo $GH_PERSONAL_ACCESS_TOKEN

# Verify Bitbucket credentials (for remote repos)
echo $BITBUCKET_USERNAME

# Check for authentication errors in logs
grep -i "auth\|403\|401" *.log
```|**CodeArtifact Authentication Issues**

```bash
# Check AWS authentication (CI/CD)
aws sts get-caller-identity

# Test CodeArtifact access
aws codeartifact get-authorization-token --domain your-domain --domain-owner YOUR_CODEARTIFACT_ACCOUNT_ID

# Check for CodeArtifact errors in logs
grep -i "401 Unauthorized\|CodeArtifact\|Failed to fetch.*codeartifact" *.log

# Verify local AWS profile (local development)
aws configure list-profiles | grep your-codeartifact-profile
````

**General Authentication Problems**

````bash
# Verify GitHub credentials are set
echo $GH_PERSONAL_ACCESS_TOKEN

# Verify Bitbucket credentials (for remote repos)
echo $BITBUCKET_USERNAME

# Check for authentication errors in logs
grep -i "auth\|403\|401" *.log
```|**CodeArtifact Authentication Issues**

```bash
# Check AWS authentication (CI/CD)
aws sts get-caller-identity

# Test CodeArtifact access
aws codeartifact get-authorization-token --domain your-domain --domain-owner YOUR_CODEARTIFACT_ACCOUNT_ID

# Check for CodeArtifact errors in logs
grep -i "401 Unauthorized\|CodeArtifact\|Failed to fetch.*codeartifact" *.log

# Verify local AWS profile (local development)
aws configure list-profiles | grep your-codeartifact-profile
````

**General Authentication Problems**

```bash
# Verify GitHub credentials are set
echo $GH_PERSONAL_ACCESS_TOKEN

# Verify Bitbucket credentials (for remote repos)
echo $BITBUCKET_USERNAME

# Check for authentication errors in logs
grep -i "auth\|403\|401" *.log
```

### Performance Optimization

**Reduce container startup time:**

- Use `--local-cookbook-path` and `--local-awa-path` for development
- Implement Docker layer caching in CI systems
- Use smaller base images when possible

**Memory management:**

- Monitor container memory usage for large workflows
- Adjust Temporal worker configuration for memory-intensive tasks
- Use controlled concurrency in workflows

## Best Practices

### Security

- Store API keys as encrypted secrets
- Use minimal required permissions for tokens
- Regularly rotate authentication credentials

### Performance

- Use appropriate queue names for different environments
- Monitor workflow execution times and resource usage
- Implement timeout and retry policies

### Maintenance

- Keep base container images updated
- Monitor dependency versions for security updates
- Test pipeline changes in development environments first

The pipeline runner provides a robust, scalable foundation for executing AWA workflows in production environments while maintaining development flexibility and debugging capabilities.

## Complete Pipeline Runner Code

Here's the full `awa_workflow_runner.py` implementation used in production with AWS CodeArtifact integration:

```python
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import dagger

# Load environment variables from .env file if it exists
def load_env_file():
    env_path = Path('.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())


def is_ci_environment():
    """Detect if running in CI/CD environment"""
    return bool(os.getenv("GITHUB_ACTIONS") or os.getenv("CI"))


def detect_local_aws_profile():
    """Try to detect a suitable local AWS profile for CodeArtifact"""
    import subprocess
    try:
        # Get list of AWS profiles
        result = subprocess.run(
            ["aws", "configure", "list-profiles"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            profiles = result.stdout.strip().split('
')
            # Prefer slalom-codeartifact if it exists
            if 'slalom-codeartifact' in profiles:
                return 'slalom-codeartifact'
            # Otherwise use default
            if 'default' in profiles:
                return 'default'
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass
    # Fallback to slalom-codeartifact since user confirmed they have it
    return 'slalom-codeartifact'


def configure_aws_credentials_for_dagger(container, client):
    """Configure AWS credentials in Dagger container based on environment"""
    # Check if we're in CI with OIDC credentials
    if os.getenv("AWS_ROLE_ARN") and os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"):
        # Use OIDC/Web Identity Token authentication (used by GitHub Actions)
        container = container.with_env_variable("AWS_ROLE_ARN", os.getenv("AWS_ROLE_ARN", ""))
        container = container.with_env_variable("AWS_WEB_IDENTITY_TOKEN_FILE", "/tmp/web-identity-token")

        # Mount the web identity token file
        token_file_path = os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE", "")
        if token_file_path and Path(token_file_path).exists():
            token_file = client.host().file(token_file_path)
            container = container.with_mounted_file("/tmp/web-identity-token", token_file)

        # Also pass through the role session name if set
        if os.getenv("AWS_ROLE_SESSION_NAME"):
            container = container.with_env_variable("AWS_ROLE_SESSION_NAME", os.getenv("AWS_ROLE_SESSION_NAME", ""))
    elif os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"):
        # Use environment credentials (GitHub Actions OIDC sets these)
        container = container.with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", ""))
        container = container.with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
        if os.getenv("AWS_SESSION_TOKEN"):
            container = container.with_env_variable("AWS_SESSION_TOKEN", os.getenv("AWS_SESSION_TOKEN", ""))
    elif not is_ci_environment():
        # Local development - mount AWS credentials directory
        aws_profile = os.getenv("AWS_PROFILE") or detect_local_aws_profile()
        if aws_profile:
            container = container.with_env_variable("AWS_PROFILE", aws_profile)
        # Mount AWS credentials from host
        aws_creds_path = Path.home() / ".aws"
        if aws_creds_path.exists():
            aws_creds_dir = client.host().directory(str(aws_creds_path))
            container = container.with_mounted_directory("/root/.aws", aws_creds_dir)

    return container


def setup_local_aws_env(profile_name=None, debug=False):
    """Set up AWS environment variables for local testing"""
    if is_ci_environment():
        if debug:
            print("CI environment detected, using OIDC credentials")
        return

    if not profile_name:
        profile_name = detect_local_aws_profile()

    if not profile_name:
        if debug:
            print("WARNING: No AWS profile detected, CodeArtifact may not work")
        return

    if debug:
        print(f"Local environment detected, using AWS profile: {profile_name}")

    # Set the profile for the Dagger function to use
    os.environ["AWS_PROFILE"] = profile_name


async def main() -> None:
    import argparse

    # Load .env file if it exists
    load_env_file()

    # Set up local AWS environment if needed
    setup_local_aws_env(debug=True)  # Always debug during development

    parser = argparse.ArgumentParser(description="Generic AWA workflow runner using Dagger")
    parser.add_argument(
        "--workflow",
        type=str,
        required=True,
        help="AWA workflow name to execute (e.g., awa-hello-world, github-pr-description)",
    )
    parser.add_argument(
        "--input",
        type=str,
        required=False,
        default="",
        help="JSON input string for the workflow (optional)",
    )
    parser.add_argument(
        "--cookbook-branch",
        type=str,
        default="main",
        help="Cookbook branch to checkout (default: main)",
    )
    parser.add_argument(
        "--core-branch",
        type=str,
        default="main",
        help="Core AWA repository branch to checkout (default: main)",
    )
    parser.add_argument(
        "--local-cookbook-path",
        type=str,
        help="Local path to cookbook repository (if provided, will use this instead of cloning)",
    )
    parser.add_argument(
        "--local-awa-path",
        type=str,
        help="Local path to main AWA repository (if provided, will use this instead of cloning)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip input validation checks",
    )
    parser.add_argument(
        "--queue",
        type=str,
        default="awa_default",
        help="Temporal queue name (default: awa_default)",
    )
    parser.add_argument(
        "--local-aws-profile",
        type=str,
        help="Local AWS profile to use (for local testing, auto-detects if not specified)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging and enhanced output",
    )

    args = parser.parse_args()

    # Apply local AWS profile override if specified
    if args.local_aws_profile:
        setup_local_aws_env(args.local_aws_profile, args.debug)
    elif not is_ci_environment():
        # Auto-detect for local environment
        setup_local_aws_env(debug=args.debug)

    if args.debug:
        print(f"Environment: {'CI' if is_ci_environment() else 'Local'}")
        print(f"AWS Profile (CodeArtifact): {os.getenv('CODEARTIFACT_AWS_PROFILE', 'Not set')}")


    # Validate JSON input (only if provided)
    if not args.skip_validation and args.input:
        try:
            json.loads(args.input)
        except json.JSONDecodeError as e:
            sys.stderr.write(f"ERROR: Invalid JSON input: {e}")
            sys.exit(1)

    async with dagger.Connection() as client:
        # Add cache busting with timestamp
        cache_bust = str(int(time.time()))

        src = client.host().directory(
            ".",
            exclude=[".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"],
        )

        # Determine AWS setup based on environment
        is_local = not is_ci_environment()

        python = (
            client.container()
            .from_("python:3.12")
            .with_env_variable("DAGGER_NO_NAG", "1")
            .with_env_variable("CACHE_BUST", cache_bust)
            .with_env_variable("BITBUCKET_USERNAME", os.getenv("BITBUCKET_USERNAME", ""))
            .with_env_variable("BITBUCKET_PASSWORD", os.getenv("BITBUCKET_PASSWORD", ""))
            .with_env_variable("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            .with_env_variable("GH_PERSONAL_ACCESS_TOKEN", os.getenv("GH_PERSONAL_ACCESS_TOKEN", ""))
            # AWS credentials setup - different for local vs CI
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", ""))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
            .with_env_variable("AWS_SESSION_TOKEN", os.getenv("AWS_SESSION_TOKEN", ""))
            .with_env_variable("AWS_DEFAULT_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
            .with_env_variable("CODEARTIFACT_AWS_PROFILE", os.getenv("CODEARTIFACT_AWS_PROFILE", "default"))
            # Add debug flag
            .with_env_variable("AWA_RUNNER_DEBUG", "1" if args.debug else "0")

            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "make", "curl", "ca-certificates", "gnupg", "git", "unzip"])
            # Install AWS CLI v2 (architecture-aware)
            .with_exec([
                "sh", "-c",
                "arch=$(uname -m) && "
                'if [ "$arch" = "aarch64" ] || [ "$arch" = "arm64" ]; then '
                "  curl -sL https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip -o awscliv2.zip; "
                "else "
                "  curl -sL https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip; "
                "fi"
            ])
            .with_exec(["unzip", "-q", "awscliv2.zip"])
            .with_exec(["./aws/install"])
            .with_exec(["rm", "-rf", "awscliv2.zip", "aws"])
            # Install Node.js 22.x
            .with_exec(["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", "nodesource_setup.sh"])
            .with_exec(["bash", "nodesource_setup.sh"])
            .with_exec(["apt-get", "install", "-y", "nodejs"])
            .with_exec(["npm", "install", "-g", "pnpm"])
            # Install Temporal CLI
            .with_exec(["sh", "-c", "curl -sSf https://temporal.download/cli.sh | sh"])
            .with_exec(["cp", "/root/.temporalio/bin/temporal", "/usr/local/bin/"])
            .with_mounted_directory("/project", src)
            .with_workdir("/project")
        )

        # Install UV first
        python = python.with_exec(["pip", "install", "uv"])

        # Configure AWS credentials using the proven AWA method
        python = configure_aws_credentials_for_dagger(python, client)

        # Mount local directories if provided
        if args.local_cookbook_path:
            if not Path(args.local_cookbook_path).exists():
                raise ValueError(f"Local cookbook path does not exist: {args.local_cookbook_path}")
            cookbook_dir = client.host().directory(
                args.local_cookbook_path,
                exclude=[".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"],
            )
            python = python.with_mounted_directory("/local-cookbook", cookbook_dir)

        if args.local_awa_path:
            if not Path(args.local_awa_path).exists():
                raise ValueError(f"Local AWA path does not exist: {args.local_awa_path}")
            awa_dir = client.host().directory(
                args.local_awa_path,
                exclude=[".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"],
            )
            python = python.with_mounted_directory("/local-awa", awa_dir)

        # Get credentials for URL-based authentication (only needed if we're cloning)
        if not args.local_cookbook_path or not args.local_awa_path:
            bitbucket_username = os.getenv("BITBUCKET_USERNAME", "")
            bitbucket_password = os.getenv("BITBUCKET_PASSWORD", "")
            if not bitbucket_username or not bitbucket_password:
                raise ValueError("BITBUCKET_USERNAME and BITBUCKET_PASSWORD must be set")
            python = python.with_exec(["git", "config", "--global", "user.name", "CI"])
            python = python.with_exec(["git", "config", "--global", "user.email", "ci@slalom.com"])

        # Define cookbook directory name for consistency
        cookbook_dir_name = "agentic-workflow-accelerator-cookbook"

        # Either copy local cookbook or clone from repository
        if args.local_cookbook_path:
            # Copy the mounted local cookbook directory
            python = python.with_exec(
                ["sh", "-c", f"cp -r /local-cookbook {cookbook_dir_name}"],
            )
        else:
            # Clone cookbook repository with authentication
            clone_cmd = (
                f"git clone https://{bitbucket_username}:{bitbucket_password}@bitbucket.org/slalom-consulting/"
                f"agentic-workflow-accelerator-cookbook.git {cookbook_dir_name}"
            )
            python = python.with_exec(["sh", "-c", clone_cmd])

            # Checkout specific cookbook branch
            if args.cookbook_branch != "main":
                python = python.with_exec(["sh", "-c", f"cd {cookbook_dir_name} && git fetch --all && git reset --hard origin/{args.cookbook_branch}"])

        # Define main AWA directory name
        main_awa_dir_name = "agentic-workflow-accelerator"

        # Handle main AWA repository setup
        if args.local_awa_path:
            # Copy the mounted local AWA directory
            python = python.with_exec(
                ["sh", "-c", f"cp -r /local-awa {main_awa_dir_name}"],
            )
        else:
            # Clone main AWA repository with authentication
            main_awa_clone_cmd = (
                f"git clone https://{bitbucket_username}:{bitbucket_password}@bitbucket.org/slalom-consulting/"
                f"agentic-workflow-accelerator.git {main_awa_dir_name}"
            )
            python = python.with_exec(["sh", "-c", main_awa_clone_cmd])

            # Checkout specific core branch
            if args.core_branch != "main":
                python = python.with_exec(["sh", "-c", f"cd {main_awa_dir_name} && git fetch --all && git reset --hard origin/{args.core_branch}"])

        # Install AWA dependencies from the main AWA directory
        python = python.with_exec(["sh", "-c", f"cd {main_awa_dir_name} && cp config.dev.yaml config.yaml && make base-install"])

        # Log the parameters being used
        sys.stderr.write(f"Running AWA workflow: {args.workflow}\n")
        if args.input:
            sys.stderr.write(f"  Input: {args.input}\n")
        sys.stderr.write(f"  Queue: {args.queue}\n")
        if args.cookbook_branch != "main":
            sys.stderr.write(f"  Cookbook Branch: {args.cookbook_branch}\n")
        if args.core_branch != "main":
            sys.stderr.write(f"  Core Branch: {args.core_branch}\n")
        if args.local_cookbook_path:
            sys.stderr.write(f"  Local Cookbook: {args.local_cookbook_path}\n")
        if args.local_awa_path:
            sys.stderr.write(f"  Local AWA: {args.local_awa_path}\n")

        # Run the AWA workflow with comprehensive AWS authentication and logging
        workflow_runner = (
            python.with_exec(["rm", "-f", "temporal.db"])
            .with_env_variable("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
            .with_env_variable("GH_PERSONAL_ACCESS_TOKEN", os.getenv("GH_PERSONAL_ACCESS_TOKEN", ""))
            .with_env_variable("AWA_API_BASE_URL", os.getenv("AWA_API_BASE_URL", "http://localhost:8001"))
            .with_env_variable("TEMPORAL_SERVER_HOST", "0.0.0.0")  # noqa: S104
            .with_env_variable("AWA_LOG_LEVEL_ACTIVITY", "WARNING")  # Suppress DEBUG activity logs
            .with_env_variable("AWA_LOG_LEVEL_WORKFLOW", "INFO")  # Suppress DEBUG workflow logs
            .with_env_variable("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", ""))
            .with_env_variable("AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", ""))
            .with_env_variable("AWS_SESSION_TOKEN", os.getenv("AWS_SESSION_TOKEN", ""))
            .with_env_variable("AWS_DEFAULT_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
            .with_env_variable("CODEARTIFACT_AWS_PROFILE", os.getenv("CODEARTIFACT_AWS_PROFILE", ""))
            .with_exec([
                "bash",
                "-c",
                f"""
                set -e

                echo "=== AWS Configuration Check ==="
                echo "Region: $AWS_DEFAULT_REGION"

                # Test AWS CLI access
                echo "=== Testing AWS CLI ==="
                aws --version || echo "AWS CLI not available"

                # Test basic AWS authentication
                echo "Testing AWS authentication..."
                if aws sts get-caller-identity 2>&1; then
                    echo "✓ AWS authentication successful"
                    AWS_AUTH_OK=1
                else
                    echo "✗ AWS authentication failed"
                    AWS_AUTH_OK=0
                fi

                # Test CodeArtifact access if authentication worked
                if [ "${{AWS_AUTH_OK:-0}}" = "1" ]; then
                    echo "=== Testing CodeArtifact Access ==="
                    echo "Testing access to slalom-all domain..."

                    # First try with verbose error output (no profile needed in container)
                    if aws codeartifact get-authorization-token --domain your-domain --domain-owner YOUR_CODEARTIFACT_ACCOUNT_ID --query authorizationToken --output text 2>/tmp/codeartifact_error.log >/dev/null; then
                        echo "✓ CodeArtifact access successful"
                        CODEARTIFACT_OK=1
                    else
                        echo "✗ CodeArtifact access failed"
                        echo "Error details:"
                        cat /tmp/codeartifact_error.log
                        echo ""
                        echo "=== Debugging Information ==="
                        aws codeartifact list-domains --region us-east-1 --max-results 1 2>&1 || echo "Cannot list domains in us-east-1"
                        echo ""
                        echo "ERROR: CodeArtifact access is required but failed. Cannot proceed without private packages."
                        echo "Please check:"
                        echo "1. The role has CodeArtifact permissions"
                        echo "2. The domain 'your-domain' exists in account YOUR_CODEARTIFACT_ACCOUNT_ID"
                        echo "3. The domain is in the correct region"
                        echo "4. Cross-account permissions are properly configured"
                        exit 1
                    fi
                else
                    echo "ERROR: AWS authentication failed. Cannot proceed."
                    exit 1
                fi

                echo "=== Python Dependencies ==="
                uv lock
                uv add dagger-io

                # Start services (run from AWA directory)
                cd /project/{main_awa_dir_name}

                echo "=== Starting AWA Core Services ==="
                uv run -m awa.main start --detach --services temporal_server,temporal_worker,api > awa_services.log 2>&1 &
                AWA_SERVICES_PID=$$!
                sleep 2

                # Wait for temporal server to be ready
                for i in $(seq 1 30); do
                    if temporal workflow list --limit 1 >/dev/null 2>&1; then
                        break
                    fi
                    sleep 2
                done

                # Start recipes worker in detached mode
                cd /project/{cookbook_dir_name}/recipes
                echo "=== Starting Recipes Worker ==="

                # Set up CodeArtifact authentication for cookbook
                echo "=== Setting up CodeArtifact for recipes ==="
                CODEARTIFACT_TOKEN=$(aws codeartifact get-authorization-token --domain your-domain --domain-owner YOUR_CODEARTIFACT_ACCOUNT_ID --query authorizationToken --output text 2>&1)
                if [ $? -eq 0 ] && [ -n "$CODEARTIFACT_TOKEN" ]; then
                    echo "✓ CodeArtifact authentication configured"
                    export UV_INDEX_SLALOM_USERNAME="aws"
                    export UV_INDEX_SLALOM_PASSWORD="$CODEARTIFACT_TOKEN"
                    echo "✓ CodeArtifact authentication configured" > aws-auth-test.log
                else
                    echo "✗ CodeArtifact authentication failed: $CODEARTIFACT_TOKEN"
                    echo "FAILED: $CODEARTIFACT_TOKEN" > aws-auth-test.log
                    echo "ERROR: CodeArtifact authentication required for cookbook packages"
                    exit 1
                fi

                echo "=== Running make recipes ==="
                make recipes > recipes.log 2>&1 &
                RECIPES_PID=$$!
                sleep 3

                # Wait for recipes worker to be ready, but also check for authentication failures
                TIMEOUT=60
                ELAPSED=0
                while [ $ELAPSED -lt $TIMEOUT ]; do
                    # Check for successful worker startup
                    if grep -q -E "Worker started|Connected to Temporal|worker is running|Worker registered" recipes.log 2>/dev/null; then
                        echo "✓ Recipes worker started successfully"
                        break
                    fi

                    # Check for CodeArtifact authentication failures
                    if grep -q -E "HTTP status client error \(401 Unauthorized\)|Failed to fetch.*codeartifact.*401|Authentication failed" recipes.log 2>/dev/null; then
                        echo "✗ CRITICAL: CodeArtifact authentication failure detected in recipes worker"
                        echo "Error details from recipes.log:"
                        grep -E "HTTP status client error \(401 Unauthorized\)|Failed to fetch.*codeartifact|Authentication failed|Error 1" recipes.log 2>/dev/null || echo "(No specific error found)"
                        echo ""
                        echo "This indicates the cookbook cannot access private packages from CodeArtifact."
                        echo "The workflow cannot proceed without these dependencies."
                        exit 1
                    fi

                    # Check for any make errors that would prevent startup
                    if grep -q "make: \*\*\* \[.*\] Error" recipes.log 2>/dev/null; then
                        echo "✗ CRITICAL: Make command failed in recipes setup"
                        echo "Error details from recipes.log:"
                        grep "make: \*\*\*" recipes.log 2>/dev/null
                        echo "The recipes worker cannot start due to build/dependency failures."
                        exit 1
                    fi

                    sleep 1
                    ELAPSED=$((ELAPSED + 1))
                done

                # Final check - if we timed out, it's also a failure
                if [ $ELAPSED -ge $TIMEOUT ]; then
                    echo "✗ CRITICAL: Recipes worker failed to start within $TIMEOUT seconds"
                    echo "Final status check - recent logs:"
                    tail -10 recipes.log 2>/dev/null || echo "(No log available)"
                    exit 1
                fi

                # Give worker time to stabilize
                sleep 5

                # Run the specified AWA workflow (from AWA directory)
                cd /project/{main_awa_dir_name}

                # Check if input is actually provided (not empty string)
                INPUT_PROVIDED='{args.input}'

                # Return to AWA directory for workflow execution
                cd /project/{main_awa_dir_name}

                if [ -z "$INPUT_PROVIDED" ] || [ "$INPUT_PROVIDED" = "" ]; then
                    echo "=== Executing Workflow: {args.workflow} ==="
                    stdbuf -oL -eL uv run -m awa.main run --workflow {args.workflow} -q {args.queue} 2>&1 || {{
                        echo "ERROR: Workflow execution failed!"

                        echo ""
                        echo "=========================================="
                        echo "        FULL LOG DUMP (FAILURE)"
                        echo "=========================================="

                        echo ""
                        echo "=== AWA CORE SERVICES LOG ==="
                        echo "File: /project/{main_awa_dir_name}/awa_services.log"
                        echo "----------------------------------------"
                        if [ -f "/project/{main_awa_dir_name}/awa_services.log" ]; then
                            cat "/project/{main_awa_dir_name}/awa_services.log"
                        else
                            echo "(Log file not found)"
                        fi

                        echo ""
                        echo "=== COOKBOOK AWS AUTH TEST LOG ==="
                        echo "File: /project/{cookbook_dir_name}/recipes/aws-auth-test.log"
                        echo "----------------------------------------"
                        if [ -f "/project/{cookbook_dir_name}/recipes/aws-auth-test.log" ]; then
                            cat "/project/{cookbook_dir_name}/recipes/aws-auth-test.log"
                        else
                            echo "(Log file not found)"
                        fi

                        echo ""
                        echo "=== COOKBOOK RECIPES WORKER LOG ==="
                        echo "File: /project/{cookbook_dir_name}/recipes/recipes.log"
                        echo "----------------------------------------"
                        if [ -f "/project/{cookbook_dir_name}/recipes/recipes.log" ]; then
                            cat "/project/{cookbook_dir_name}/recipes/recipes.log"
                        else
                            echo "(Log file not found)"
                        fi

                        echo ""
                        echo "=========================================="
                        echo "       END OF LOG DUMP (FAILURE)"
                        echo "=========================================="

                        exit 1
                    }}
                else
                    echo "=== Executing Workflow: {args.workflow} with input ==="
                    stdbuf -oL -eL uv run -m awa.main run --workflow {args.workflow} -q {args.queue} --input "$INPUT_PROVIDED" 2>&1 || {{
                        echo "ERROR: Workflow execution failed!"

                        echo ""
                        echo "=========================================="
                        echo "        FULL LOG DUMP (FAILURE)"
                        echo "=========================================="

                        echo ""
                        echo "=== AWA CORE SERVICES LOG ==="
                        echo "File: /project/{main_awa_dir_name}/awa_services.log"
                        echo "----------------------------------------"
                        if [ -f "/project/{main_awa_dir_name}/awa_services.log" ]; then
                            cat "/project/{main_awa_dir_name}/awa_services.log"
                        else
                            echo "(Log file not found)"
                        fi

                        echo ""
                        echo "=== COOKBOOK AWS AUTH TEST LOG ==="
                        echo "File: /project/{cookbook_dir_name}/recipes/aws-auth-test.log"
                        echo "----------------------------------------"
                        if [ -f "/project/{cookbook_dir_name}/recipes/aws-auth-test.log" ]; then
                            cat "/project/{cookbook_dir_name}/recipes/aws-auth-test.log"
                        else
                            echo "(Log file not found)"
                        fi

                        echo ""
                        echo "=== COOKBOOK RECIPES WORKER LOG ==="
                        echo "File: /project/{cookbook_dir_name}/recipes/recipes.log"
                        echo "----------------------------------------"
                        if [ -f "/project/{cookbook_dir_name}/recipes/recipes.log" ]; then
                            cat "/project/{cookbook_dir_name}/recipes/recipes.log"
                        else
                            echo "(Log file not found)"
                        fi

                        echo ""
                        echo "=========================================="
                        echo "       END OF LOG DUMP (FAILURE)"
                        echo "=========================================="

                        exit 1
                    }}
                fi

                echo "Workflow completed successfully"

                echo ""
                echo "=========================================="
                echo "       RECIPES WORKER LOG"
                echo "=========================================="
                if [ -f "/project/{cookbook_dir_name}/recipes/recipes.log" ]; then
                    cat "/project/{cookbook_dir_name}/recipes/recipes.log"
                else
                    echo "(Recipes log file not found)"
                fi
                echo "========================================"
                """
            ],
            insecure_root_capabilities=True,
        )
        )

        # Get the exit code from the workflow run
        workflow_exit = await workflow_runner.exit_code()

        if workflow_exit != 0:
            sys.stderr.write(f"Workflow {args.workflow} failed with exit code {workflow_exit}\n")
            sys.exit(workflow_exit)
        else:
            sys.stderr.write(f"Workflow {args.workflow} completed successfully\n")


if __name__ == "__main__":
    asyncio.run(main())
```

This complete implementation shows all the production features including:

- **Environment setup** with Python 3.12, Node.js, and Temporal CLI
- **Flexible repository handling** (local vs remote)
- **Service orchestration** with proper startup sequencing
- **Comprehensive logging** for debugging failures
- **Error handling** with detailed log dumps on failure
- **Cache busting** for consistent builds
