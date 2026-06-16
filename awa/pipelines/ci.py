import argparse
import asyncio
import os
import sys

import dagger


def build_service_test_script(
    services: str,
    test_command: str,
    message: str = "Starting services and running tests",
) -> str:
    """Build a bash script for starting services, running tests, and stopping services.

    Args:
        services: Comma-separated list of services to start (e.g., "temporal_server,temporal_worker,api")
        test_command: Command to run tests (e.g., "uv run -m pytest -v tests/workflow/tests")
        message: Message to display at the start (default: "Starting services and running tests")

    Returns:
        Bash script as a string

    """
    return f"""
            set -e
            echo "--- {message} ---"

            # Start services in development mode (production mode is slower due to extra build step)
            uv run -m awa.main start --detach --ui-mode dev --services {services}

            # Wait for services to be ready with health checks
            echo "Waiting for services to be ready..."
            WAIT_TIME=0
            MAX_WAIT=120
            while [ $WAIT_TIME -lt $MAX_WAIT ]; do
                if uv run -m awa.main status -s {services} --quiet; then
                    echo "Services are ready!"
                    break
                fi
                echo "Services not ready yet, waiting... ($WAIT_TIME/$MAX_WAIT seconds)"
                sleep 2
                WAIT_TIME=$((WAIT_TIME + 2))
            done

            # Final check - abort if services still not ready
            if [ $WAIT_TIME -ge $MAX_WAIT ]; then
                echo "Services failed to start within $MAX_WAIT seconds. Aborting tests."
                exit 1
            fi

            # Run tests
            {test_command}

            echo "Tests completed successfully. Container will handle service cleanup."
            """


async def run_unit_tests(python: dagger.Container) -> None:
    """Run unit tests."""
    # Some unit tests check for pnpm availability, so we need to install Node.js
    # This is a workaround until the tests are fixed to properly mock shutil.which
    python = (
        python.with_exec(["apt-get", "install", "-y", "gnupg"])
        .with_exec(["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", "nodesource_setup.sh"])
        .with_exec(["bash", "nodesource_setup.sh"])
        .with_exec(["apt-get", "install", "-y", "nodejs"])
        .with_exec(["npm", "install", "-g", "pnpm"])
    )

    tests = await python.with_exec(["make", "test"]).exit_code()
    if tests != 0:
        sys.exit(tests)


async def run_workflow_tests(python: dagger.Container) -> None:
    """Run workflow tests with Temporal services."""
    # Install Temporal CLI and run workflow tests
    test_runner = (
        python.with_exec(["sh", "-c", "curl -sSf https://temporal.download/cli.sh | sh"])
        .with_exec(["cp", "/root/.temporalio/bin/temporal", "/usr/local/bin/"])
        .with_exec(["rm", "-f", "temporal.db"])
        # Generate BAML client before running tests
        .with_exec(["make", "baml"])
        .with_env_variable("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        .with_env_variable("TEMPORAL_SERVER_HOST", "0.0.0.0")  # noqa: S104
        .with_exec(
            [
                "sh",
                "-c",
                build_service_test_script(
                    services="temporal_server,temporal_worker,api",
                    test_command="uv run -m pytest -v tests/workflow/tests",
                ),
            ],
            insecure_root_capabilities=True,
        )
    )
    workflow_test = await test_runner.exit_code()
    if workflow_test != 0:
        sys.exit(workflow_test)


async def run_ui_tests(python: dagger.Container) -> None:
    """Run UI tests with AWA services."""
    # Install all dependencies and run UI tests
    test_runner = (
        python
        # Install Node.js and pnpm
        .with_exec(["apt-get", "install", "-y", "gnupg"])
        .with_exec(["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", "nodesource_setup.sh"])
        .with_exec(["bash", "nodesource_setup.sh"])
        .with_exec(["apt-get", "install", "-y", "nodejs"])
        .with_exec(["npm", "install", "-g", "pnpm"])
        # Install Temporal CLI since UI tests start temporal_server
        .with_exec(["sh", "-c", "curl -sSf https://temporal.download/cli.sh | sh"])
        .with_exec(["cp", "/root/.temporalio/bin/temporal", "/usr/local/bin/"])
        # Install Node.js packages
        .with_exec(["pnpm", "install"])
        # Install Playwright system dependencies
        .with_exec(
            [
                "apt-get",
                "install",
                "-y",
                "libnss3",
                "libnspr4",
                "libatk-bridge2.0-0",
                "libdrm2",
                "libxkbcommon0",
                "libxcomposite1",
                "libxdamage1",
                "libxrandr2",
                "libgbm1",
                "libxss1",
                "libasound2",
                "libatspi2.0-0",
                "libgtk-3-0",
                "libgdk-pixbuf-2.0-0",
            ],
        )
        .with_exec(["npx", "playwright", "install", "chromium"])
        .with_exec(["rm", "-f", "temporal.db"])
        .with_env_variable("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        .with_env_variable("TEMPORAL_SERVER_HOST", "0.0.0.0")  # noqa: S104
        .with_exec(
            [
                "sh",
                "-c",
                build_service_test_script(
                    services="temporal_server,temporal_worker,api,ui",
                    test_command="make test-ui",
                    message="Starting AWA services and running UI tests",
                ),
            ],
            insecure_root_capabilities=True,
        )
    )
    ui_tests = await test_runner.exit_code()
    if ui_tests != 0:
        sys.exit(ui_tests)


async def run_api_tests(python: dagger.Container) -> None:
    """Run API tests."""
    # Install Temporal CLI since API tests need the API service which depends on Temporal
    test_runner = (
        python.with_exec(["sh", "-c", "curl -sSf https://temporal.download/cli.sh | sh"])
        .with_exec(["cp", "/root/.temporalio/bin/temporal", "/usr/local/bin/"])
        .with_exec(["rm", "-f", "temporal.db"])
        .with_env_variable("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
        .with_env_variable("TEMPORAL_SERVER_HOST", "0.0.0.0")  # noqa: S104
        .with_exec(
            [
                "sh",
                "-c",
                build_service_test_script(
                    services="temporal_server,temporal_worker,api",
                    test_command="make test-api",
                    message="Starting services and running API tests",
                ),
            ],
            insecure_root_capabilities=True,
        )
    )
    api_tests = await test_runner.exit_code()
    if api_tests != 0:
        sys.exit(api_tests)


async def run_build_docs(python: dagger.Container) -> None:
    """Build documentation."""
    # Install all dependencies for docs build
    python = (
        python.with_exec(["apt-get", "install", "-y", "git", "gnupg"])
        .with_exec(["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", "nodesource_setup.sh"])
        .with_exec(["bash", "nodesource_setup.sh"])
        .with_exec(["apt-get", "install", "-y", "nodejs"])
        .with_exec(["npm", "install", "-g", "pnpm"])
        .with_exec(["uv", "sync"])
        .with_exec(["pnpm", "install"])
        .with_exec(["make", "docs-prep"])
    )

    # Build documentation
    docs_build = await python.with_exec(["pnpm", "run", "docs:build"]).exit_code()
    if docs_build != 0:
        sys.exit(docs_build)

    # List built docs for verification (non-fatal if directory doesn't exist)
    await python.with_exec(
        [
            "sh",
            "-c",
            "ls -la docs/.vitepress/dist/ || echo 'Directory not found (may be expected)'",
        ],
    ).stdout()


async def run_pre_commit_checks(python: dagger.Container) -> None:
    """Run pre-commit checks."""
    # Install all dependencies and run pre-commit checks
    python = (
        python
        # Install Git and Node.js
        .with_exec(["apt-get", "install", "-y", "git", "gnupg"])
        .with_exec(["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", "nodesource_setup.sh"])
        .with_exec(["bash", "nodesource_setup.sh"])
        .with_exec(["apt-get", "install", "-y", "nodejs"])
        .with_exec(["npm", "install", "-g", "pnpm"])
        # Install Node.js packages
        .with_exec(["pnpm", "install"])
        # Install pre-commit hooks
        .with_exec(["uv", "run", "pre-commit", "install"])
    )

    precommit_check = await python.with_exec(["uv", "run", "pre-commit", "run", "--all-files"]).exit_code()
    if precommit_check != 0:
        sys.exit(precommit_check)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "test_type",
        nargs="?",
        default="unit-tests",
        choices=["unit-tests", "workflow-tests", "ui-tests", "api-tests", "build-docs", "pre-commit-checks"],
        help="Type of tests to run (default: unit-tests)",
    )
    args = parser.parse_args()

    # Define Python/Node package installation requirements for each test type
    # System-level installations are now handled in the handler functions
    installation_requirements = {
        "unit-tests": [
            ["uv", "sync"],  # Python deps only
        ],
        "workflow-tests": [
            ["uv", "sync"],  # Python deps only
        ],
        "api-tests": [
            ["uv", "sync"],  # Python deps only
        ],
        "ui-tests": [
            ["uv", "sync"],  # Python deps
            # pnpm install is handled in run_ui_tests after Node.js is installed
        ],
        "build-docs": [
            # Don't use make install here since it requires Node.js which we install in the handler
            # The handler will install system deps first, then run Python/Node installations
        ],
        "pre-commit-checks": [
            ["uv", "sync"],  # Python deps
            # pnpm install and pre-commit install are handled in run_pre_commit_checks after Node.js is installed
        ],
    }

    async with dagger.Connection() as client:
        build_id = os.getenv("DAGGER_ENGINE_DOCKER_CONTAINER_NAME", "")
        src = client.host().directory(
            ".",
            exclude=[".venv", "__pycache__", ".mypy_cache", ".pytest_cache", "node_modules"],
        )

        # Minimal base container - only essentials needed by all test types
        python = (
            client.container()
            .from_("python:3.12")
            .with_label("dagger.io/engine.name", build_id)
            .with_exec(["echo", f"Using Dagger Build Id: {build_id}"])
            .with_env_variable("DAGGER_NO_NAG", "1")
            .with_exec(["apt-get", "update"])
            .with_exec(["apt-get", "install", "-y", "make", "curl", "ca-certificates"])
            .with_mounted_directory("/project", src)
            .with_workdir("/project")
            .with_exec(["pip", "install", "uv"])
        )

        # Install dependencies based on test type
        install_cmds = installation_requirements.get(args.test_type, [])
        for cmd in install_cmds:
            python = python.with_exec(cmd)

        # Dictionary dispatch for test types
        test_handlers = {
            "unit-tests": run_unit_tests,
            "workflow-tests": run_workflow_tests,
            "ui-tests": run_ui_tests,
            "api-tests": run_api_tests,
            "build-docs": run_build_docs,
            "pre-commit-checks": run_pre_commit_checks,
        }

        # Execute the selected test handler
        handler = test_handlers.get(args.test_type)
        if handler:
            await handler(python)
        else:
            sys.stderr.write(f"Error: Unknown test type: {args.test_type}\n")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
