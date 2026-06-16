"""Test configuration for AWA Cookbook."""

import asyncio
import sys
from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import ActivityEnvironment, WorkflowEnvironment


def pytest_addoption(parser: Any) -> None:  # noqa: ANN401
    """Add command line options for pytest."""
    parser.addoption(
        "--workflow-environment",
        default="local",
        help="Which workflow environment to use ('local', 'time-skipping', or target to existing server)",
    )


@pytest.fixture(scope="session")
def event_loop() -> Any:  # noqa: ANN401
    """Create event loop for testing."""
    # See https://github.com/pytest-dev/pytest-asyncio/issues/68
    # See https://github.com/pytest-dev/pytest-asyncio/issues/257
    # Also need ProactorEventLoop on older versions of Python with Windows so
    # that asyncio subprocess works properly
    if sys.version_info < (3, 8) and sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def activity_env() -> ActivityEnvironment:
    """Provide activity environment for testing."""
    return ActivityEnvironment()


@pytest_asyncio.fixture(scope="session")
async def workflow_env(request: Any) -> AsyncGenerator[WorkflowEnvironment, None]:  # noqa: ANN401
    """Provide workflow environment for testing."""
    env_type = request.config.getoption("--workflow-environment")
    if env_type == "local":
        env = await WorkflowEnvironment.start_local(
            dev_server_extra_args=[
                "--dynamic-config-value",
                "frontend.enableExecuteMultiOperation=true",
            ],
            data_converter=pydantic_data_converter,
        )
    elif env_type == "time-skipping":
        env = await WorkflowEnvironment.start_time_skipping()
    else:
        client = await Client.connect(
            env_type,
            data_converter=pydantic_data_converter,
        )
        env = WorkflowEnvironment.from_client(client)
    yield env
    await env.shutdown()


@pytest_asyncio.fixture
async def workflow_client(workflow_env: WorkflowEnvironment) -> Client:
    """Provide Temporal workflow client for testing."""
    return workflow_env.client
