from temporalio import activity

from awa.core.utils.command_utils import CommandUtils
from awa.sdk import constants as sdk_constants
from awa.sdk.models.command_result import CommandInput, CommandResult


@activity.defn(name=sdk_constants.ACTIVITY_RUN_COMMAND)
async def run_command_activity(command_input: CommandInput) -> CommandResult:
    """Execute a command in a specified working directory and return result.

    Args:
        command_input: CommandInput containing command and optional working directory

    Returns:
        CommandResult containing exit_code, output, and success status

    """
    success, output = await CommandUtils.run_command_async(
        command_input.command,
        command_input.working_dir,
    )
    exit_code = 0 if success else 1
    return CommandResult(exit_code=exit_code, output=output)
