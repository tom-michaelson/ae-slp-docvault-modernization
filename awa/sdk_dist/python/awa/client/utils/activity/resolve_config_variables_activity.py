from datetime import timedelta
from typing import Any

from temporalio import workflow

from awa.client import constants


async def resolve_config_variables_activity(config_object: Any) -> Any:  # noqa: ANN401
    """Resolve environment variables in configuration objects.

    Recursively expands environment variable placeholders in nested objects.
    Handles ${VAR_NAME} and $VAR patterns in strings within nested dicts/lists.
    Raises an error if any required environment variables are not found.

    Args:
        config_object: The configuration object to process. Can be a dict, list,
            string, or any other type.

    Returns:
        Any: The configuration object with environment variable placeholders expanded.

    Raises:
        ValueError: If required environment variables are not set.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_RESOLVE_CONFIG_VARIABLES,
        args=[config_object],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
