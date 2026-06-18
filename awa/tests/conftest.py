import asyncio
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import ActivityEnvironment, WorkflowEnvironment

from awa.core.models.config.env_config import EnvConfig

# Strategy: Only disable logging for workflow tests, not all tests
# We'll use markers to identify workflow tests and apply patches selectively


def mock_init_logging(*args: object, **kwargs: object) -> None:
    """No-op init_logging to prevent InterceptHandler installation."""


def mock_get_logger(component: Any, **kwargs: Any) -> Any:  # noqa: ANN401, ARG001
    """Mock logger that doesn't trigger any imports."""
    mock_logger = MagicMock()
    mock_logger.info = MagicMock()
    mock_logger.error = MagicMock()
    mock_logger.debug = MagicMock()
    mock_logger.warning = MagicMock()
    mock_logger.exception = MagicMock()
    return mock_logger


def mock_setup_workflow_logging(*args: object, **kwargs: object) -> None:
    """Mock workflow logging setup."""


def mock_get_subprocess_logger(*args: object, **kwargs: object) -> Any:  # noqa: ARG001, ANN401
    """Mock subprocess logger."""
    return MagicMock()


# Global patch only for init_logging to prevent InterceptHandler during workflows
_init_logging_patcher = patch("awa.core.logger.logger.init_logging", side_effect=mock_init_logging)
_init_logging_patcher.start()


def pytest_configure(config: Any) -> None:  # noqa: ANN401
    """Pytest hook called before test collection and execution."""
    # Ensure the patch is active during test collection


def pytest_unconfigure(config: Any) -> None:  # noqa: ANN401, ARG001
    """Pytest hook called after all tests are done."""
    import asyncio
    import warnings

    # Clean up the patches
    _init_logging_patcher.stop()

    # Suppress warnings and errors from libraries trying to log during cleanup
    # This includes litellm and openai.agents which try to log after loguru handlers are closed
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*was never awaited")

    # Give background tasks a moment to complete
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule cleanup for after current tasks
            loop.call_soon(lambda: None)
    except RuntimeError:
        # No event loop, that's fine
        pass

    # Remove all loguru handlers to prevent errors during final cleanup
    try:
        from loguru import logger

        logger.remove()
    except (ImportError, ValueError):
        # loguru might be mocked or already cleaned up
        pass


project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Add SDK distribution path for cookbook recipe tests
sdk_dist_path = project_root / "sdk_dist" / "python"
if str(sdk_dist_path) not in sys.path:
    sys.path.insert(0, str(sdk_dist_path))


def pytest_addoption(parser: Any) -> None:  # noqa: ANN401
    parser.addoption(
        "--workflow-environment",
        default="local",
        help="Which workflow environment to use ('local', 'time-skipping', or target to existing server)",
    )


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging() -> Any:  # noqa: ANN401
    """Configure logging for tests to prevent log file creation.

    This fixture automatically runs for all tests and prevents the creation
    of log files in the actual logs/ directory by disabling file logging
    during test execution.
    """

    def mock_setup_workflow_logging(workflow_id: str) -> None:
        # Set workflow context but don't create log files
        try:
            from awa.core.logger.intercept_handler import workflow_context

            workflow_context.set(workflow_id)
        except ImportError:
            # If intercept_handler can't be imported, skip
            pass

    # Patch the EnvConfig.get_env_config() object and workflow logging functions to disable file logging during tests
    # Also patch get_subprocess_logger to avoid wrapping sys.stdout in a TextIOWrapper,
    # which can interfere with pytest's stdout capturing.
    def mock_get_subprocess_logger(service_name: str) -> Any:  # noqa: ANN401
        import logging
        import sys

        logger_name = f"subprocess.{service_name.lower()}"
        subprocess_logger = logging.getLogger(logger_name)
        if not subprocess_logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter("%(message)s"))
            subprocess_logger.addHandler(handler)
            subprocess_logger.setLevel(logging.NOTSET)
            subprocess_logger.propagate = False
        return subprocess_logger

    with (
        patch.object(EnvConfig.get_env_config(), "log_file_enabled", new=False),
        patch.object(EnvConfig.get_env_config(), "log_enable_json", new=False),
        patch.object(EnvConfig.get_env_config(), "log_console_enabled", new=False),
        patch("awa.core.logger.logger.setup_workflow_logging", side_effect=mock_setup_workflow_logging),
        patch("awa.core.logger.logger.get_subprocess_logger", side_effect=mock_get_subprocess_logger),
    ):
        yield
        # Cleanup: Remove all loguru handlers before session ends to prevent
        # cleanup errors from libraries (litellm, openai.agents) trying to log
        try:
            from loguru import logger

            logger.remove()
        except (ImportError, ValueError):
            # Loguru might be mocked or already cleaned up
            pass


@pytest.fixture(autouse=True)
def isolate_workflow_tests(request: Any) -> Any:  # noqa: ANN401
    """Isolate workflow tests from logging infrastructure."""
    # Check if this is a workflow test by examining the test path or name
    test_file = str(request.fspath) if hasattr(request, "fspath") else ""

    is_workflow_test = "/workflows/" in test_file and test_file.endswith(".py")

    # Mock _log_subprocess_info to avoid AsyncMock coroutine warnings in all tests
    def mock_log_subprocess_info(*args: object, **kwargs: object) -> None:
        """No-op subprocess info logging."""

    if is_workflow_test:
        # For workflow tests, prevent any logger imports that could trigger sandbox violations
        # and also mock temporalio.workflow.logger which is used in workflows
        with (
            patch.dict(
                "sys.modules",
                {
                    "awa.core.logger.intercept_handler": MagicMock(),
                    "loguru": MagicMock(),
                },
            ),
            patch("awa.core.logger.logger.get_logger", side_effect=mock_get_logger),
            patch("awa.core.logger.logger.setup_workflow_logging", side_effect=mock_setup_workflow_logging),
            patch("awa.core.logger.logger.get_subprocess_logger", side_effect=mock_get_subprocess_logger),
            patch(
                "awa.core.utils.command_utils.CommandUtils._log_subprocess_info",
                side_effect=mock_log_subprocess_info,
            ),
            # Also patch temporalio's workflow logger to prevent it from trying to log during execution
            patch("temporalio.workflow.logger.info", MagicMock()),
            patch("temporalio.workflow.logger.error", MagicMock()),
            patch("temporalio.workflow.logger.debug", MagicMock()),
            patch("temporalio.workflow.logger.warning", MagicMock()),
        ):
            yield
    else:
        # For non-workflow tests, also mock _log_subprocess_info
        with patch(
            "awa.core.utils.command_utils.CommandUtils._log_subprocess_info",
            side_effect=mock_log_subprocess_info,
        ):
            yield


@pytest.fixture(scope="session")
def event_loop() -> Any:  # noqa: ANN401
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
    return ActivityEnvironment()


@pytest_asyncio.fixture(scope="session")
async def workflow_env(request: Any) -> AsyncGenerator[WorkflowEnvironment, None]:  # noqa: ANN401
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
    return workflow_env.client
