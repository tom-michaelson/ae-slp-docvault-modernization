from datetime import timedelta
from typing import Any

from temporalio import workflow

from awa.sdk import constants


async def resolve_template_activity(
    template_str: str,
    variables: dict[str, Any] | None = None,
) -> str:
    """Resolve a template string by substituting variables.

    Args:
        template_str: The template string containing variable placeholders.
        variables: Optional dictionary of variables to substitute in the template.
            Defaults to None.

    Returns:
        str: The resolved template string with variables substituted.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_RESOLVE_TEMPLATE,
        args=[template_str, variables],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=constants.FILE_IO_TIMEOUT_SECONDS),
    )
