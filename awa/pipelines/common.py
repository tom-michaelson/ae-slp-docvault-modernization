"""Common utilities for Dagger pipelines."""

import os

import dagger


def setup_baseline(
    client: dagger.Client,
    src: dagger.Directory,
    python_version: str = "3.12",
) -> dagger.Container:
    """Set up a base container with baseline dependencies.

    Args:
        client: Dagger client instance
        src: Source directory to mount
        python_version: Python version to use (default: "3.12")

    Returns:
        Container with baseline dependencies installed

    """
    container = (
        client.container()
        .from_(f"python:{python_version}")
        .with_env_variable("DAGGER_NO_NAG", "1")
        .with_env_variable("BITBUCKET_USERNAME", os.getenv("BITBUCKET_USERNAME", ""))
        .with_env_variable("BITBUCKET_PASSWORD", os.getenv("BITBUCKET_PASSWORD", ""))
        .with_exec(["apt-get", "update"])
        .with_exec(["apt-get", "install", "-y", "make", "curl", "ca-certificates", "gnupg", "git"])
        .with_mounted_directory("/project", src)
        .with_workdir("/project")
        .with_exec(
            [
                "pip",
                "install",
                "uv",
            ],
        )
    )

    return container


def setup_node(container: dagger.Container) -> dagger.Container:
    """Add Node.js and pnpm to an existing container.

    Args:
        container: Container to add Node.js to

    Returns:
        Container with Node.js and pnpm installed

    """
    container = (
        container
        # Install Node.js 22.x
        .with_exec(["curl", "-fsSL", "https://deb.nodesource.com/setup_22.x", "-o", "nodesource_setup.sh"])
        .with_exec(["bash", "nodesource_setup.sh"])
        .with_exec(["apt-get", "install", "-y", "nodejs"])
        .with_exec(["npm", "install", "-g", "pnpm"])
    )

    return container


def setup_temporal(container: dagger.Container) -> dagger.Container:
    """Add Temporal CLI to an existing container.

    Args:
        container: Container to add Temporal CLI to

    Returns:
        Container with Temporal CLI installed

    """
    container = (
        container
        # Install Temporal CLI
        .with_exec(["sh", "-c", "curl -sSf https://temporal.download/cli.sh | sh"]).with_exec(
            ["cp", "/root/.temporalio/bin/temporal", "/usr/local/bin/"],
        )
    )

    return container


def setup_base_dependencies(
    client: dagger.Client,
    src: dagger.Directory,
    python_version: str = "3.12",
) -> dagger.Container:
    """Set up a base container with all common dependencies.

    This is a convenience function that combines baseline, node, and temporal setup.

    Args:
        client: Dagger client instance
        src: Source directory to mount
        python_version: Python version to use (default: "3.12")

    Returns:
        Container with all dependencies installed

    """
    container = setup_baseline(client, src, python_version)
    container = setup_node(container)
    container = setup_temporal(container)

    return container
