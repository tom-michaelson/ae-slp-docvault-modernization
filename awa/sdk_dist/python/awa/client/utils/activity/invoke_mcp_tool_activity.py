from datetime import timedelta
from typing import TYPE_CHECKING, Any

from temporalio import workflow

if TYPE_CHECKING:
    from temporalio.common import RetryPolicy

from awa.client import constants


async def invoke_mcp_tool_activity(
    mcp_config: dict[str, Any],
    tool_name: str,
    parameters: dict[str, Any],
    timeout_seconds: int | None = None,
    retry_policy: "RetryPolicy | None" = None,
) -> Any:  # noqa: ANN401
    """Invoke a Model Context Protocol (MCP) tool.

    Args:
        mcp_config: Configuration dictionary for the MCP server.
        tool_name: Name of the MCP tool to invoke.
        parameters: Parameters to pass to the MCP tool.
        timeout_seconds: Optional timeout in seconds for the tool invocation.
            Defaults to agent timeout if not specified.
        retry_policy: Optional Temporal retry policy for handling failures.
            Defaults to None.

    Returns:
        Any: The result returned by the MCP tool.

    """
    return await workflow.execute_activity(
        constants.ACTIVITY_INVOKE_MCP_TOOL,
        args=[mcp_config, tool_name, parameters],
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=timeout_seconds or constants.AGENT_TIMEOUT_SECONDS),
        retry_policy=retry_policy,
    )
