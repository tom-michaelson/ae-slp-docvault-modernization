import asyncio
import os
import time
import uuid

from pydantic import BaseModel
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter

from awa.core import constants
from awa.core.logger.logger import LoggerComponent, get_logger

logger = get_logger(LoggerComponent.WORKER)


async def connect_to_temporal() -> Client:
    """Connect to Temporal services using the same configuration pattern as the main AWA application."""
    temporal_host = os.environ.get("TEMPORAL_SERVER_HOST", "localhost")
    temporal_port = os.environ.get("TEMPORAL_SERVER_PORT", "7233")
    temporal_address = f"{temporal_host}:{temporal_port}"

    logger.info(f"Connecting to Temporal at: {temporal_address}")
    return await Client.connect(temporal_address, data_converter=pydantic_data_converter)


async def wait_for_temporal_services() -> None:
    """Wait for Temporal services to be ready before proceeding with tests."""
    max_wait_time = 120  # Increased wait time for CI environments
    check_interval = 3  # Slightly longer intervals for CI
    start_time = time.time()

    logger.info("Waiting for Temporal services to be ready...")

    while time.time() - start_time < max_wait_time:
        try:
            # Try to connect and verify services are actually ready
            client = await connect_to_temporal()

            # Verify the connection is working by attempting to list workflows
            # This will fail if the server isn't fully ready
            workflows = client.list_workflows()
            # Convert the first few results to verify the server is responding
            workflow_list = []
            async for wf in workflows:
                workflow_list.append(wf)
                if len(workflow_list) >= 1:  # Just need to verify we can get a response
                    break

            # Additional verification: ensure we can actually execute a simple health check
            await asyncio.sleep(0.5)  # Brief pause to ensure stability

            # If we get here, services are truly ready
            logger.info("Temporal services are ready and responsive!")
            return

        except (ConnectionError, OSError, TimeoutError) as e:
            # Handle both expected connection errors and any Temporal-specific errors
            # Log more specific error information
            error_msg = str(e)
            if "tcp connect error" in error_msg:
                logger.debug("Temporal server not yet available (connection refused)")
            elif "connection" in error_msg.lower():
                logger.debug(f"Connection issue: {error_msg}")
            else:
                logger.debug(f"Service check failed with: {error_msg}")

            elapsed = time.time() - start_time
            logger.debug(f"Waiting for services... ({elapsed:.1f}s elapsed)")
            await asyncio.sleep(check_interval)

    elapsed = time.time() - start_time
    raise TimeoutError(f"Temporal services did not become ready within {max_wait_time} seconds (waited {elapsed:.1f}s)")


async def temporal_client() -> Client:
    """Create a Temporal client that connects to the running server."""
    # Add retry logic for connection
    max_retries = 5  # Reduced since we have wait_for_temporal_services
    retry_delay = 2.0

    for attempt in range(max_retries):
        try:
            # Try to connect and verify services are actually ready
            client = await connect_to_temporal()

            # Test the connection by checking if server is reachable
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}. Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
            else:
                raise ConnectionError(f"Failed to connect to Temporal server after {max_retries} attempts") from e

    # This should never be reached due to the raise above, but satisfies the type checker
    raise ConnectionError("Failed to connect to Temporal server")


async def temporal_workflow_id() -> str:
    return f"test-file-transform-{uuid.uuid4().hex[:8]}-{int(time.time())}"


async def execute_workflow(workflow_name: str, workflow_input: BaseModel) -> str:
    """Execute a workflow using the existing Temporal services."""
    # Wait for services to be ready first
    await wait_for_temporal_services()

    # Connect to the already running Temporal server
    client = await temporal_client()
    logger.info(f"Temporal client details: {client.__dict__ if hasattr(client, '__dict__') else str(client)}")

    workflow_id = await temporal_workflow_id()
    logger.info(f"Starting workflow {workflow_name} with ID: {workflow_id}")

    # Execute the workflow with retry logic for CI stability
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await client.execute_workflow(
                workflow_name,
                workflow_input,
                id=f"{workflow_id}-attempt-{attempt + 1}",
                task_queue=constants.TASK_QUEUE,
            )
            logger.info(f"Workflow {workflow_id} completed successfully: {result}")
            return result
        except Exception as e:
            if "tcp connect error" in str(e) and attempt < max_retries - 1:
                logger.warning(f"Workflow execution attempt {attempt + 1} failed with tcp error, retrying...")
                await asyncio.sleep(2)  # Brief pause before retry
                # Reconnect client for next attempt
                client = await temporal_client()
            else:
                raise

    raise RuntimeError(f"Workflow execution failed after {max_retries} attempts")
