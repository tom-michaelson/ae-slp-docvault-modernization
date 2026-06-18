from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from temporalio import exceptions, workflow

from awa.core.constants import DEFAULT_ACTIVITY_TIMEOUT_SECONDS
from awa.sdk import constants as sdk_constants

if TYPE_CHECKING:
    from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration

with workflow.unsafe.imports_passed_through():
    from awa.core.activities.agent import execute_agent_activity
    from awa.core.activities.isolated_agent_environment import (
        cleanup_isolated_environment_activity,
        copy_analyze_outputs_activity,
        merge_worktree_changes_activity,
        setup_isolated_agent_activity,
    )
    from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
    from awa.sdk.models.agent_modes.isolated_agent_models import (
        IsolatedAgentEnvironmentInfo,
        IsolatedAgentParams,
    )
    from awa.sdk.models.agent_modes.task_response_model import TaskResponseModel


@workflow.defn(name=sdk_constants.WORKFLOW_ISOLATED_AGENT)
class IsolatedAgentChildWorkflow:
    """Workflow for executing agents in isolated environments.

    This workflow implements complete separation of concerns:
    1. Environment setup is fully encapsulated in setup activities
    2. Agent execution is completely unaware of environment context
    3. Cleanup and output handling are managed by dedicated activities

    For ACT mode: Uses git worktree for isolated execution and merges changes back
    For ANALYZE mode: Uses temporary directory copy for isolated execution and copies outputs back

    The agent receives a pre-configured environment and executes normally,
    with no knowledge that it's working in an isolated environment.
    """

    async def _handle_agent_outputs(
        self,
        agent_result: TaskResponseModel,
        params: IsolatedAgentParams,
        environment_info: IsolatedAgentEnvironmentInfo,
    ) -> TaskResponseModel:
        """Handle agent outputs for ACT and ANALYZE modes."""
        if agent_result.status != "completed":
            return agent_result

        if params.agent_config.mode == AgentModeEnum.ACT:
            workflow.logger.info("Agent mode is ACT - merging changes back to source branch")
            merge_result = await workflow.execute_activity(
                merge_worktree_changes_activity,
                args=[environment_info, params.agent_config],
                start_to_close_timeout=timedelta(seconds=DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            if not merge_result.success:
                workflow.logger.warning(f"Failed to merge changes: {merge_result.message}")
                agent_result.reason = f"Agent completed but merge failed: {merge_result.message}"
        elif params.agent_config.mode == AgentModeEnum.ANALYZE:
            workflow.logger.info("Agent mode is ANALYZE - copying outputs to source directory")
            copy_result = await workflow.execute_activity(
                copy_analyze_outputs_activity,
                args=[environment_info, params.output_directory],
                start_to_close_timeout=timedelta(seconds=DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            if not copy_result.success:
                workflow.logger.warning(f"Failed to copy analyze outputs: {copy_result.message}")
                agent_result.reason = f"Agent completed but output copy failed: {copy_result.message}"
            else:
                workflow.logger.info(f"Successfully copied analyze outputs: {copy_result.message}")
        else:
            workflow.logger.warning(f"Unsupported agent mode: {params.agent_config.mode}")
            agent_result.reason = f"Unsupported agent mode: {params.agent_config.mode}"

        return agent_result

    async def _cleanup_isolated_environment(
        self,
        environment_info: IsolatedAgentEnvironmentInfo | None,
        agent_config: AgentConfiguration,
    ) -> None:
        """Clean up the isolated environment (git worktree or temporary directory)."""
        if not environment_info:
            return

        workflow.logger.info("Cleaning up isolated environment...")
        try:
            cleanup_result = await workflow.execute_activity(
                cleanup_isolated_environment_activity,
                args=[environment_info, agent_config],
                start_to_close_timeout=timedelta(seconds=DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            if cleanup_result.success:
                workflow.logger.info("Environment cleanup completed successfully")
            else:
                workflow.logger.error(f"Environment cleanup failed: {cleanup_result.message}")

        except (OSError, ValueError) as cleanup_error:
            workflow.logger.exception(f"Error during environment cleanup: {cleanup_error}")

    @workflow.run
    async def run(self, params: IsolatedAgentParams) -> TaskResponseModel:
        """Execute an agent in an isolated environment.

        Args:
            params: Parameters containing source directory, agent config, and options

        Returns:
            TaskResponseModel with the agent execution result

        """
        workflow.logger.info(f"Starting isolated agent workflow for directory: {params.source_directory}")
        workflow.logger.info(f"Agent provider: {params.agent_config.provider}, mode: {params.agent_config.mode}")

        environment_info: IsolatedAgentEnvironmentInfo | None = None

        try:
            # Step 1: Setup Isolated Agent Environment
            workflow.logger.info("Setting up isolated agent environment...")
            environment_result, isolated_agent_config = await workflow.execute_activity(
                setup_isolated_agent_activity,
                args=[
                    params.source_directory,
                    params.source_branch,
                    params.agent_config,
                    params.output_directory,
                ],
                start_to_close_timeout=timedelta(seconds=60),
            )

            if not environment_result.success or not environment_result.environment_info or not isolated_agent_config:
                error_msg = f"Failed to setup isolated environment: {environment_result.message}"
                workflow.logger.error(error_msg)
                raise exceptions.ApplicationError(error_msg, non_retryable=True)

            environment_info = environment_result.environment_info
            if environment_info is not None:
                workflow.logger.info(f"Isolated environment ready: {environment_info.environment_path}")

            # Step 2: Execute Agent (Completely Isolated from Environment Knowledge)
            workflow.logger.info("Executing agent in isolated environment...")

            agent_result = await workflow.execute_activity(
                execute_agent_activity,
                args=[isolated_agent_config],
                start_to_close_timeout=timedelta(minutes=params.agent_execution_timeout_minutes),
            )
            if isinstance(agent_result, dict):
                agent_result = TaskResponseModel(**agent_result)

            workflow.logger.info(f"Agent execution completed with status: {agent_result.status}")

            # Step 3: Handle outputs based on agent mode
            if environment_info is not None:
                agent_result = await self._handle_agent_outputs(agent_result, params, environment_info)

            # Check if agent execution failed and raise exception to mark workflow as failed
            if agent_result.status == "failed":
                error_message = agent_result.reason or agent_result.exception or "Agent execution failed"
                workflow.logger.error(f"Agent execution failed: {error_message}")
                raise exceptions.ApplicationError(error_message, non_retryable=True)

            return agent_result

        finally:
            # Step 4: Cleanup Environment (always execute)
            await self._cleanup_isolated_environment(environment_info, params.agent_config)
            workflow.logger.info("Isolated agent workflow completed")
