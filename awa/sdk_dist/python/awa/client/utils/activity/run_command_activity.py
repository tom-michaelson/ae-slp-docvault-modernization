from datetime import timedelta

from temporalio import workflow

from awa.client import constants
from awa.client.models.command_result import CommandInput, CommandResult


async def run_command_activity(command_input: CommandInput) -> CommandResult:
    """Run a command and return the result.

    Args:
        command_input: The command input containing command and working directory.

    Returns:
        CommandResult with success status and output.

    """
    result = await workflow.execute_activity(
        constants.ACTIVITY_RUN_COMMAND,
        arg=command_input,
        task_queue=constants.AWA_DEFAULT_TASK_QUEUE,
        start_to_close_timeout=timedelta(seconds=300),  # 5 minutes for commands
    )
    return CommandResult.model_validate(result)
