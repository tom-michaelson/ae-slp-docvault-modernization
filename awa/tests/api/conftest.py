"""Shared fixtures for API tests."""

import logging
import os
import random
import time
from collections.abc import Generator

import httpx
import pytest

from awa.core.models.config.env_config import EnvConfig

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Get the API base URL from environment or config."""
    # Allow override via environment variable
    if "AWA_TEST_API_URL" in os.environ:
        return os.environ["AWA_TEST_API_URL"]

    # Use current environment configuration
    env_config = EnvConfig.get_env_config()
    return f"http://{env_config.awa_api_host}:{env_config.awa_api_port}"


@pytest.fixture(scope="session")
def api_client(api_base_url: str) -> Generator[httpx.Client, None, None]:
    """Create HTTP client for API testing against real environment."""
    with httpx.Client(
        base_url=api_base_url,
        timeout=30.0,
        follow_redirects=True,
    ) as client:
        yield client


@pytest.fixture(scope="session")
def api_health_check(api_client: httpx.Client, api_base_url: str) -> None:
    """Verify API is accessible before running tests."""
    try:
        response = api_client.get("/api/v1/health")
        if response.status_code not in [200, 503]:  # 503 if services are down but API is up
            pytest.skip(f"API not accessible at {api_base_url} - got status {response.status_code}")
    except (httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException) as e:
        pytest.skip(f"API not accessible at {api_base_url}: {e}")


@pytest.fixture(autouse=True)
def api_test_delay() -> None:
    """Add configurable delay between API tests to prevent overwhelming the server.

    Environment variables:
    - AWA_TEST_DELAY: Delay in seconds between tests (default: 0.1)
        - Set to "0" or "0.0" for no delay
        - Set to "random" for random delays between 0.1-1.0 seconds
        - Set to specific float value for fixed delay
    - AWA_TEST_DELAY_VERBOSE: Set to "1" to enable verbose logging

    The delay helps prevent API server overload when running many tests concurrently.
    """
    delay_config = os.environ.get("AWA_TEST_DELAY", "0.1")
    verbose = os.environ.get("AWA_TEST_DELAY_VERBOSE", "0") == "1"

    if delay_config in {"0.0", "0"}:
        # No delay - return immediately for fast execution
        return

    delay = 0.1  # Default delay

    if delay_config == "random":
        # Random delay between 0.1-1.0 seconds
        # Note: Using random for test delays is acceptable (not cryptographic)
        delay = random.uniform(0.1, 1.0)  # noqa: S311
    else:
        try:
            delay = float(delay_config)
        except ValueError:
            # Invalid value - default to no delay
            if verbose:
                logger.warning(f"Invalid AWA_TEST_DELAY value '{delay_config}', using no delay")
            return

    # Add delay with test counting for monitoring
    if hasattr(api_test_delay, "_test_count"):
        api_test_delay._test_count += 1
        if verbose:
            logger.info(f"Test delay: {delay:.2f}s (test #{api_test_delay._test_count})")
        time.sleep(delay)
    else:
        api_test_delay._test_count = 1
        if verbose:
            logger.info(f"Starting API tests with {delay:.2f}s delay between tests")


@pytest.fixture
def api_test_timing() -> Generator[object, None, None]:
    """Track API test execution timing for performance analysis.

    This fixture can be used to measure test execution time and generate
    performance reports for API endpoint testing.
    """

    class TimingContext:
        def __init__(self) -> None:
            self.start_time: float | None = None
            self.end_time: float | None = None
            self.duration: float | None = None

        def __enter__(self) -> "TimingContext":
            self.start_time = time.time()
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: object,
        ) -> None:
            self.end_time = time.time()
            if self.start_time is not None:
                self.duration = self.end_time - self.start_time

    return TimingContext()
