from __future__ import annotations

import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from temporalio import activity

from awa.core.activities.agent_modes.create_agent import create_agent
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration as BaseAgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_base import CommandResult
from awa.sdk.models.agent_modes.streaming_task_response_model import StreamingTaskResponseModel
from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel

# TODO RH: Refactor all of these to use the temporal.activity.logger instead
# logger = get_logger(LoggerComponent.ACTIVITY)

if TYPE_CHECKING:
    from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
    from awa.sdk.models.agent_modes.agent_mode_base import AgentModeBase
else:
    # Alias at runtime to make the linter happy
    AgentConfiguration = BaseAgentConfiguration


@activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT)
async def execute_agent_activity(agent_config: AgentConfiguration) -> TaskResponseModel:
    """Execute an agent with the provided configuration.

    This activity is completely isolated from any worktree or environment setup concerns.
    It simply executes the agent using the provided configuration, including any
    working_directory that has been pre-configured by calling workflows/activities.

    Args:
        agent_config: Complete agent configuration including working directory

    Returns:
        TaskResponseModel with execution results

    """
    activity.logger.info(f"🔥 EXECUTE_AGENT_ACTIVITY: Starting with config: {agent_config}")
    activity.logger.info(f"Executing task {agent_config}")

    agent_mode: AgentModeBase | None = None
    session_id: str = ""  # Initialize session_id to avoid UnboundLocalError in finally block

    try:
        activity.logger.info(
            f"🔥 AGENT ACTIVITY: About to create agent with provider={agent_config.provider}, mode={agent_config.mode}",
        )
        agent_mode = create_agent(
            provider=agent_config.provider,
            mode=agent_config.mode,
        )
        activity.logger.info(f"🔥 AGENT ACTIVITY: Created agent: {type(agent_mode).__name__}")

        # Use session_id from config if provided, otherwise use workflow ID
        # Fall back to generated ID if workflow info is not available
        if agent_config.session_id:
            session_id = agent_config.session_id
            activity.logger.info(f"🔥 AGENT ACTIVITY: Using session_id from config: {session_id}")
        else:
            try:
                workflow_info = activity.info()
                session_id = workflow_info.workflow_id
                activity.logger.info(f"🔥 AGENT ACTIVITY: Using workflow_id as session_id: {session_id}")
            except (AttributeError, RuntimeError):
                session_id = f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4()!s}"
                activity.logger.info(f"🔥 AGENT ACTIVITY: Generated session_id: {session_id}")

        message: str = f"Initializing agent '{agent_config.provider}' in '{agent_config.mode}' mode..."
        activity.logger.info(message)

        output_content: str | None = None

        output_content = await _initialize_and_run(
            agent_config=agent_config,
            agent_mode=agent_mode,
            session_id=session_id,
        )

        if not output_content:
            output_content = "No output content"

        return TaskResponseModel(
            status="completed",
            output=output_content,
            reason=(
                f"🔥 AGENT DEBUG: Used {type(agent_mode).__name__} "
                f"for provider={agent_config.provider}, mode={agent_config.mode}"
            ),
        )
    except Exception as e:  # noqa: BLE001
        message = f"Agent action failed: {e}"
        activity.logger.exception(message)
        return TaskResponseModel(status="failed", reason=message, exception=str(e))
    finally:
        if agent_mode and session_id:
            await _cleanup(agent_config, agent_mode, session_id)


@activity.defn(name=sdk_constants.ACTIVITY_EXECUTE_AGENT_STREAMING)
async def execute_agent_activity_streaming(agent_config: AgentConfiguration) -> StreamingTaskResponseModel:
    """Execute an agent with the provided configuration and enable streaming output.

    This activity mirrors execute_agent_activity() but routes to the agent's stream_output() method
    to provide real-time streaming of agent execution progress. It maintains the same isolation
    from worktree and environment setup concerns.

    Args:
        agent_config: Complete agent configuration including working directory

    Returns:
        StreamingTaskResponseModel with execution results and session_id for frontend connection

    """
    activity.logger.info(f"🚀 STREAMING ACTIVITY STARTED: {agent_config}")

    agent_mode: AgentModeBase | None = None
    session_id: str | None = None
    try:
        agent_mode = create_agent(
            provider=agent_config.provider,
            mode=agent_config.mode,
        )

        session_id = agent_config.stream_session_id or f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4()!s}"

        message: str = f"Initializing agent '{agent_config.provider}' in '{agent_config.mode}' mode..."
        activity.logger.info(message)

        output_content: str | None = None

        output_content = await _initialize_and_run_streaming(
            agent_config=agent_config,
            agent_mode=agent_mode,
            session_id=session_id,
        )

        if not output_content:
            output_content = "No output content"

        activity.logger.info(f"✅ STREAMING ACTIVITY COMPLETED: output={len(output_content or '')} chars")
        return StreamingTaskResponseModel(status="completed", output=output_content, session_id=session_id)
    except Exception as e:  # noqa: BLE001
        message = f"Agent streaming action failed: {e}"
        activity.logger.exception(message)
        return StreamingTaskResponseModel(
            status="failed",
            reason=message,
            exception=str(e),
            session_id=session_id or "",
        )
    finally:
        if agent_mode and session_id:
            await _cleanup(agent_config, agent_mode, session_id)


async def _initialize_and_run(
    agent_config: AgentConfiguration,
    agent_mode: AgentModeBase,
    session_id: str,
) -> str | None:
    """Initialize the agent and execute the agent command, handling MCP and caching.

    Args:
        agent_config: The agent configuration.
        agent_mode: The agent mode instance.
        session_id: The session ID for the agent execution.

    Returns:
        tuple[Optional[str], Optional[str]]: The output content and command session ID.

    Raises:
        ValueError: If agent initialization or command execution fails.

    """
    init_result: CommandResult = await _initialize(
        agent_config=agent_config,
        agent_mode=agent_mode,
        session_id=session_id,
    )
    activity.logger.info(f"Agent initialized: {init_result.result}")

    if not init_result.status:
        raise ValueError(f"Agent initialization failed: {init_result.result}")

    mcp_tools: list[str] | None = None
    if agent_config.mcp and agent_mode.supports_mcp():
        activity.logger.info("Configuring MCP...")
        mcp_tools = await _configure_mcp(agent_config, agent_mode)
        activity.logger.info("MCP configured...")

    activity.logger.info("Executing agent command...")
    command_result: CommandResult = await _run_command(
        agent_config=agent_config,
        agent_mode=agent_mode,
        session_id=session_id,
        mcp_tools=mcp_tools,
    )
    activity.logger.info(f"Agent command completed: {command_result.result}")

    if not command_result.status:
        activity.logger.error(
            f"Agent Action failed for task: {command_result.result}",
        )
        raise ValueError(f"Agent command failed: {command_result.result}")

    output_content: str | None = command_result.content or command_result.result

    return output_content


async def _initialize_and_run_streaming(
    agent_config: AgentConfiguration,
    agent_mode: AgentModeBase,
    session_id: str,
) -> str | None:
    """Initialize the agent and stream the agent output, handling MCP and caching.

    Args:
        agent_config: The agent configuration.
        agent_mode: The agent mode instance.
        session_id: The session ID for the agent execution.

    Returns:
        str | None: The output content from streaming.

    Raises:
        ValueError: If agent initialization fails.

    """
    init_result: CommandResult = await _initialize(
        agent_config=agent_config,
        agent_mode=agent_mode,
        session_id=session_id,
    )
    activity.logger.info(f"Agent initialized: {init_result.result}")

    if not init_result.status:
        raise ValueError(f"Agent initialization failed: {init_result.result}")

    mcp_tools: list[str] | None = None
    if agent_config.mcp and agent_mode.supports_mcp():
        activity.logger.info("Configuring MCP...")
        mcp_tools = await _configure_mcp(agent_config, agent_mode)
        activity.logger.info("MCP configured...")

    activity.logger.info("Streaming agent output...")
    command_result: CommandResult = await agent_mode.stream_output(
        prompt=agent_config.prompt,
        command_path=agent_config.command_file_path,
        working_dir=agent_config.working_directory,
        mcp_tools=mcp_tools,
        session_id=session_id,
        parent_session_id=agent_config.parent_session_id,
    )
    activity.logger.info(f"Agent streaming completed: {command_result.result}")

    if not command_result.status:
        activity.logger.error(
            f"Agent streaming failed for task: {command_result.result}",
        )
        raise ValueError(f"Agent streaming failed: {command_result.result}")

    output_content: str | None = command_result.content or command_result.result

    return output_content


async def _initialize(
    agent_config: AgentConfiguration,
    agent_mode: AgentModeBase,
    session_id: str,
) -> CommandResult:
    init_file: str = agent_mode.get_init_file_name()
    init_command: str = agent_mode.get_init_command()

    if not agent_config.initialize:
        return CommandResult(status=True, result="Skipping agent initialization", session_id=session_id)

    # Lets check if the init file exists and skip initialization if it does
    if init_file and agent_config.working_directory:
        init_file_path = Path(agent_config.working_directory) / init_file
        if init_file_path.exists():
            return CommandResult(status=True, result="Skipping agent initialization", session_id=session_id)

    if init_file and init_command:
        return await agent_mode.initialize(
            command=init_command,
            working_dir=agent_config.working_directory,
            session_id=session_id,
        )

    return CommandResult(
        status=True,
        result="No initialization file found, skipping initialization",
        session_id=session_id,
    )


async def _run_command(
    agent_config: AgentConfiguration,
    agent_mode: AgentModeBase,
    session_id: str,
    mcp_tools: list[str] | None = None,
) -> CommandResult:
    command_result: CommandResult = CommandResult(status=False, result="No content")

    if not agent_config.command_file_path and agent_config.prompt:
        activity.logger.info(f"🔥 AGENT ACTIVITY: About to call execute_prompt on {type(agent_mode).__name__}")
        command_result = await agent_mode.execute_prompt(
            prompt=agent_config.prompt,
            session_id=session_id,
            working_dir=agent_config.working_directory,
            mcp_tools=mcp_tools,
            stream_enabled=agent_config.stream_enabled,
        )
        activity.logger.info(f"🔥 AGENT ACTIVITY: execute_prompt completed with status: {command_result.status}")
    elif agent_config.command_file_path:
        command_result = await agent_mode.execute_command(
            command=agent_config.command_file_path,
            session_id=session_id,
            working_dir=agent_config.working_directory,
            mcp_tools=mcp_tools,
            stream_enabled=agent_config.stream_enabled,
        )
    else:
        command_result.result = "No command file path or prompt provided"

    return command_result


async def _configure_mcp(
    agent_config: AgentConfiguration,
    agent_mode: AgentModeBase,
) -> list[str] | None:
    if not agent_config.mcp or not agent_config.working_directory or not agent_config.mcp.mcp_json:
        return None

    mcp_tools: list[str] | None = await agent_mode.configure_mcp(
        working_dir=agent_config.working_directory,
        mcp_json=agent_config.mcp.mcp_json,
        mcp_allowed_tools=agent_config.mcp.allowed,
    )

    return mcp_tools


async def _cleanup(
    agent_config: AgentConfiguration,
    agent_mode: AgentModeBase,
    session_id: str,
) -> None:
    await agent_mode.get_log_files(working_dir=agent_config.working_directory, session_id=session_id)
    await agent_mode.cleanup(session_id)
