from pathlib import Path

import git
from git.exc import GitCommandError, InvalidGitRepositoryError
from temporalio import activity

from awa.core.utils.file_system_utils import FileSystemUtils
from awa.core.utils.git_utils import (
    commit_with_git_config_handling,
    get_git_author_info,
    merge_with_git_config_handling,
)
from awa.sdk import constants as sdk_constants
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration
from awa.sdk.models.agent_modes.agent_mode_enum import AgentModeEnum
from awa.sdk.models.agent_modes.isolated_agent_models import (
    IsolatedAgentEnvironmentInfo,
    IsolatedAgentEnvironmentResult,
)


async def _validate_source_directory(
    source_directory: str,
    require_write_permissions: bool = True,
) -> IsolatedAgentEnvironmentResult | None:
    """Validate source directory exists, is a directory, and has required permissions.

    Args:
        source_directory: Path to the source directory to validate
        require_write_permissions: Whether to check write permissions (default: True)

    Returns:
        IsolatedAgentEnvironmentResult with error if validation fails, None if validation passes

    """
    activity.logger.info(f"Validating source directory: {source_directory}")

    # Validate that source path exists using FileSystemUtils
    fs = FileSystemUtils.get_filesystem(source_directory)
    if not fs.exists(source_directory):
        return IsolatedAgentEnvironmentResult(
            success=False,
            message=f"Source directory path does not exist: {source_directory}",
        )

    # Check if path is a directory
    if not fs.isdir(source_directory):
        return IsolatedAgentEnvironmentResult(
            success=False,
            message=f"Source directory path is not a directory: {source_directory}",
        )

    # Check read and write permissions
    activity.logger.info(f"Checking read and write permissions for {source_directory}")

    has_read_permission = await FileSystemUtils.check_read_permission_async(source_directory)
    if not has_read_permission:
        return IsolatedAgentEnvironmentResult(
            success=False,
            message=f"Source directory path does not have read permissions: {source_directory}",
        )

    if require_write_permissions:
        has_write_permission = await FileSystemUtils.check_write_permission_async(source_directory)
        if not has_write_permission:
            return IsolatedAgentEnvironmentResult(
                success=False,
                message=f"Source directory path does not have write permissions: {source_directory}",
            )

    activity.logger.info(f"Permissions validated for {source_directory}")
    return None


@activity.defn(name=sdk_constants.ACTIVITY_SETUP_ISOLATED_AGENT)
async def setup_isolated_agent_activity(
    source_directory: str,
    source_branch: str | None,
    agent_config: AgentConfiguration,
    output_directory: str = "awa-agent-output",
) -> tuple[IsolatedAgentEnvironmentResult, AgentConfiguration | None]:
    """Set up isolated environment and return a fully configured agent config.

    For ACT mode: Creates a git worktree for isolated execution, using a temporary directory as the worktree directory.
    For ANALYZE mode: Creates a temporary directory copy for isolated execution.

    Args:
        source_directory: Path to the source directory (Git repo or regular directory)
        source_branch: Branch name to checkout, if using ACT mode
        agent_config: Agent configuration to run in the isolated environment
        output_directory: Directory name for agent outputs in analyze mode

    Returns:
        Tuple of (IsolatedAgentEnvironmentResult, AgentConfiguration or None):
        - IsolatedAgentEnvironmentResult with success status and environment information
        - AgentConfiguration configured for isolated execution (None if setup failed)

    """
    activity.logger.info(f"Setting up isolated agent environment from {source_directory}")

    if agent_config.mode == AgentModeEnum.ACT:
        # Use git worktree for ACT mode - source_branch is required
        if not source_branch:
            error_msg = "source_branch is required for ACT mode"
            activity.logger.error(error_msg)
            return IsolatedAgentEnvironmentResult(success=False, message=error_msg), None

        return await setup_isolated_agent_git_activity(
            source_directory,
            source_branch,
            agent_config,
        )
    if agent_config.mode == AgentModeEnum.ANALYZE:
        # Use temporary directory for ANALYZE mode
        return await setup_isolated_agent_temp_activity(
            source_directory,
            source_branch,
            agent_config,
            output_directory,
        )
    if agent_config.mode == AgentModeEnum.UNKNOWN:
        error_msg = f"Agent mode is UNKNOWN: {agent_config.mode}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg), None

    error_msg = f"Unsupported agent mode: {agent_config.mode}"
    activity.logger.error(error_msg)
    return IsolatedAgentEnvironmentResult(success=False, message=error_msg), None


@activity.defn(name=sdk_constants.ACTIVITY_SETUP_ISOLATED_AGENT_GIT)
async def setup_isolated_agent_git_activity(
    source_directory: str,
    source_branch: str,
    agent_config: AgentConfiguration,
) -> tuple[IsolatedAgentEnvironmentResult, AgentConfiguration | None]:
    """Set up a git worktree and return a fully configured agent config for ACT mode execution.

    This activity encapsulates all git worktree setup logic and returns an agent config
    that is ready to execute without any knowledge of the worktree context.
    This function is specifically for ACT mode and creates a git worktree for isolated execution.

    Args:
        source_directory: Path to the source git repository
        source_branch: Branch name to checkout in the worktree
        agent_config: Original agent configuration to be adapted for worktree execution

    Returns:
        Tuple of (IsolatedAgentEnvironmentResult, AgentConfiguration or None):
        - IsolatedAgentEnvironmentResult with success status and worktree information
        - AgentConfiguration configured for isolated execution (None if setup failed)

    """
    activity.logger.info(f"Setting up git worktree from {source_directory} on branch {source_branch}")

    # First setup the worktree
    worktree_result = await setup_worktree_activity(source_directory, source_branch)

    if not worktree_result.success or not worktree_result.environment_info:
        activity.logger.error(f"Failed to setup worktree: {worktree_result.message}")
        return worktree_result, None

    # Create isolated agent config with worktree as working directory
    isolated_agent_config = agent_config.model_copy()
    isolated_agent_config.working_directory = worktree_result.environment_info.environment_path

    activity.logger.info(f"Git worktree environment ready at {worktree_result.environment_info.environment_path}")

    return worktree_result, isolated_agent_config


@activity.defn(name=sdk_constants.ACTIVITY_SETUP_ISOLATED_AGENT_TEMP)
async def setup_isolated_agent_temp_activity(
    source_directory: str,
    source_branch: str | None,
    agent_config: AgentConfiguration,
    output_directory: str = "awa-agent-output",
) -> tuple[IsolatedAgentEnvironmentResult, AgentConfiguration | None]:
    """Set up a temporary directory copy and return a fully configured agent config for isolated execution.

    This activity creates a temporary directory, copies the source directory into it,
    and returns an agent config that is ready to execute without any knowledge of the
    temporary directory context. This is used for ANALYZE mode.

    Args:
        source_directory: Path to the source directory (can be Git repo or regular directory)
        source_branch: Branch name (optional, not used for temporary directory setup)
        agent_config: Original agent configuration to be adapted for temporary directory execution
        output_directory: Directory name for agent outputs in analyze mode

    Returns:
        Tuple of (IsolatedAgentEnvironmentResult, AgentConfiguration or None):
        - IsolatedAgentEnvironmentResult with success status and temporary directory information
        - AgentConfiguration configured for isolated execution (None if setup failed)

    """
    activity.logger.info(f"Setting up temporary directory from {source_directory}")

    try:
        # Validate source directory
        validation_result = await _validate_source_directory(source_directory, require_write_permissions=True)
        if validation_result:
            return validation_result, None

        # Create temporary directory
        temp_dir_path = await FileSystemUtils.create_temp_directory_async(
            prefix="awa_analyze_",
            suffix=f"_{activity.info().workflow_id}",
        )

        activity.logger.info(f"Created temporary directory: {temp_dir_path}")
        source_fs = FileSystemUtils.get_filesystem(source_directory)

        # Copy all items except the output directory to prevent copying previous workflow outputs
        source_items = source_fs.listdir(source_directory)

        # Extract item names, handling both dict and string formats from listdir
        def get_item_name(item: dict | str) -> str:
            return Path(item["name"]).name if isinstance(item, dict) else item

        item_names = [get_item_name(item) for item in source_items if get_item_name(item) != output_directory]

        # Copy each item (files and directories are handled automatically by copy methods)
        for item_name in item_names:
            source_item_path = Path(source_directory) / item_name
            dest_item_path = Path(temp_dir_path) / item_name

            if source_fs.isdir(str(source_item_path)):
                await FileSystemUtils.copy_directory_async(str(source_item_path), str(dest_item_path))
            else:
                await FileSystemUtils.copy_file_async(str(source_item_path), str(dest_item_path))

        # Create output directory for analyze mode
        output_dir_path = Path(temp_dir_path) / output_directory
        activity.logger.info(f"Creating {output_directory} directory: {output_dir_path}")

        try:
            output_fs = FileSystemUtils.get_filesystem(str(output_dir_path))
            output_fs.makedirs(str(output_dir_path), exist_ok=True)
            activity.logger.info(f"Successfully created {output_directory} directory: {output_dir_path}")

        except (OSError, ValueError) as e:
            error_msg = f"Failed to create {output_directory} directory: {e}"
            activity.logger.error(error_msg)
            return IsolatedAgentEnvironmentResult(success=False, message=error_msg), None

        # Create IsolatedAgentEnvironmentInfo for temporary directory
        environment_info = IsolatedAgentEnvironmentInfo(
            environment_path=temp_dir_path,
            source_directory_path=source_directory,
            source_branch=source_branch,
        )

        # Create isolated agent config with temporary directory as working directory
        isolated_agent_config = agent_config.model_copy()
        isolated_agent_config.working_directory = temp_dir_path

        activity.logger.info(f"Temporary directory environment ready at {temp_dir_path}")

        return IsolatedAgentEnvironmentResult(
            success=True,
            message=f"Temporary directory created successfully at {temp_dir_path}",
            environment_info=environment_info,
        ), isolated_agent_config

    except (OSError, ValueError) as e:
        error_msg = f"Failed to create temporary directory: {e}"
        activity.logger.exception(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg), None


@activity.defn(name=sdk_constants.ACTIVITY_SETUP_WORKTREE)
async def setup_worktree_activity(
    source_directory: str,
    source_branch: str,
) -> IsolatedAgentEnvironmentResult:
    """Create a git worktree for isolated agent execution.

    Always creates a temporary branch for the worktree to avoid conflicts,
    regardless of whether the source branch exists or is checked out elsewhere.

    Args:
        source_directory: Path to the source git repository
        source_branch: Branch name to eventually merge back to

    Returns:
        IsolatedAgentEnvironmentResult with success status and worktree information

    """
    activity.logger.info(f"Setting up worktree from {source_directory} for branch {source_branch}")

    try:
        # Validate source directory
        validation_result = await _validate_source_directory(source_directory, require_write_permissions=True)
        if validation_result:
            return validation_result

        # This will raise InvalidGitRepositoryError if the path is not a git repository
        repo = git.Repo(source_directory)
        if repo.bare:
            return IsolatedAgentEnvironmentResult(
                success=False,
                message=f"Source repository is bare: {source_directory}",
            )

        # Generate worktree name
        worktree_name = f"isolated_agent_{activity.info().workflow_id}"

        # Create temporary directory for worktree
        temp_base_dir = await FileSystemUtils.create_temp_directory_async(
            prefix="awa_worktree_",
            suffix=f"_{worktree_name}",
        )
        worktree_path = Path(temp_base_dir)

        # Always create a temporary branch for the worktree to avoid conflicts
        temp_branch = f"awa-worktree-{worktree_name}"

        # Determine what to branch from
        if source_branch in [head.name for head in repo.heads]:
            # Branch exists, create temp branch from it
            activity.logger.info(f"Creating temporary branch '{temp_branch}' from existing branch '{source_branch}'")
            branch_from = source_branch
        else:
            # Branch doesn't exist, create temp branch from current HEAD
            activity.logger.info(
                f"Branch '{source_branch}' doesn't exist, creating temporary branch '{temp_branch}' from HEAD",
            )
            branch_from = "HEAD"

        # Create the worktree with temporary branch
        activity.logger.info(f"Creating worktree at {worktree_path} using temporary branch {temp_branch}")
        repo.git.worktree("add", "-b", temp_branch, str(worktree_path), branch_from)

        environment_info = IsolatedAgentEnvironmentInfo(
            environment_path=str(worktree_path),
            source_directory_path=source_directory,
            source_branch=source_branch,  # Original branch to merge back to
        )

        activity.logger.info(f"Successfully created worktree: {worktree_path} on temporary branch {temp_branch}")
        return IsolatedAgentEnvironmentResult(
            success=True,
            message=f"Worktree created successfully at {worktree_path} on branch {temp_branch}",
            environment_info=environment_info,
        )

    except InvalidGitRepositoryError:
        error_msg = f"Source path is not a valid git repository: {source_directory}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
    except GitCommandError as e:
        error_msg = f"Git command failed: {e}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
    except (OSError, ValueError) as e:
        error_msg = f"Failed to create worktree: {e}"
        activity.logger.exception(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)


@activity.defn(name=sdk_constants.ACTIVITY_MERGE_WORKTREE_CHANGES)
async def merge_worktree_changes_activity(
    worktree_info: IsolatedAgentEnvironmentInfo,
    agent_config: AgentConfiguration,
) -> IsolatedAgentEnvironmentResult:
    """Merge changes from worktree back to the original source branch (for ACT mode).

    Args:
        worktree_info: Information about the worktree containing changes
        agent_config: Agent configuration containing provider information for commit attribution

    Returns:
        IsolatedAgentEnvironmentResult with success status

    """
    workflow_id = activity.info().workflow_id
    activity.logger.info(f"Merging changes from worktree: {workflow_id}")

    try:
        # Check if this is ACT mode - temporary directories (ANALYZE mode) don't need merging
        if agent_config.mode == AgentModeEnum.ANALYZE:
            activity.logger.info("ANALYZE mode - no changes to merge")
            return IsolatedAgentEnvironmentResult(
                success=True,
                message="No changes to merge (ANALYZE mode)",
            )

        # Check if source_branch is available (required for merging)
        if not worktree_info.source_branch:
            error_msg = "source_branch is required for merging changes"
            activity.logger.error(error_msg)
            return IsolatedAgentEnvironmentResult(success=False, message=error_msg)

        # Get the source repository
        source_repo = git.Repo(worktree_info.source_directory_path)
        worktree_repo = git.Repo(worktree_info.environment_path)

        # Check if there are any changes to commit in the worktree
        if not worktree_repo.is_dirty() and not worktree_repo.untracked_files:
            activity.logger.info("No changes detected in worktree")
            return IsolatedAgentEnvironmentResult(
                success=True,
                message="No changes to merge",
            )

        # Stage all changes in the worktree
        worktree_repo.git.add(A=True)

        # Get git author information once for both commit and merge
        git_info = await get_git_author_info(agent_config)

        # Create commit message
        commit_message = (
            f"AWA Agent ({agent_config.provider.title()}) changes from workflow: {activity.info().workflow_id}"
        )

        # Commit changes in the worktree using helper function
        worktree_commit = commit_with_git_config_handling(
            worktree_repo,
            commit_message,
            git_info,
        )

        activity.logger.info(f"Committed changes in worktree: {worktree_commit.hexsha[:8]}")

        # Merge back to the original source branch
        target_branch = worktree_info.source_branch

        workflow_id = activity.info().workflow_id
        worktree_name = f"isolated_agent_{workflow_id}"
        temp_branch = f"awa-worktree-{worktree_name}"

        activity.logger.info(
            f"Merging changes from temporary branch '{temp_branch}' back to '{target_branch}'",
        )

        # Ensure the target branch exists
        if target_branch not in [head.name for head in source_repo.heads]:
            # Create the target branch if it doesn't exist
            activity.logger.info(f"Creating target branch '{target_branch}' from current HEAD")
            source_repo.create_head(target_branch)

        # Switch to target branch in source repo and merge
        source_repo.heads[target_branch].checkout()
        merge_with_git_config_handling(source_repo, worktree_commit.hexsha, git_info)

        activity.logger.info(f"Successfully merged changes to {target_branch}")
        return IsolatedAgentEnvironmentResult(
            success=True,
            message=f"Changes merged successfully to {target_branch}",
        )

    except InvalidGitRepositoryError:
        error_msg = f"Repository is not valid during merge: {worktree_info.source_directory_path}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
    except GitCommandError as e:
        error_msg = f"Git merge failed: {e}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
    except (OSError, ValueError) as e:
        error_msg = f"Failed to merge worktree changes: {e}"
        activity.logger.exception(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)


@activity.defn(name=sdk_constants.ACTIVITY_COPY_ANALYZE_OUTPUTS)
async def copy_analyze_outputs_activity(
    environment_info: IsolatedAgentEnvironmentInfo,
    output_directory: str = "awa-agent-output",
) -> IsolatedAgentEnvironmentResult:
    """Copy analyze mode outputs from worktree/temp directory to the original directory.

    This activity copies any files generated by the agent during analyze mode
    from the output directory in the worktree/temp directory to the output directory
    in the original directory. Creates a subdirectory using the workflow ID to avoid
    overwriting files from successive runs.

    Args:
        environment_info: Information about the worktree/temp directory containing outputs
        output_directory: Directory name for agent outputs in analyze mode

    Returns:
        IsolatedAgentEnvironmentResult with success status

    """
    workflow_id = activity.info().workflow_id
    activity.logger.info(f"Copying analyze outputs from: {workflow_id}")

    try:
        environment_output_path = Path(environment_info.environment_path) / output_directory
        source_output_path = Path(environment_info.source_directory_path) / output_directory

        # Create subdirectory using workflow ID to avoid overwriting successive runs
        workflow_output_path = source_output_path / workflow_id

        # Check if the output directory exists in the isolated environment
        environment_fs = FileSystemUtils.get_filesystem(str(environment_output_path))
        if not environment_fs.exists(str(environment_output_path)):
            activity.logger.info(f"No {output_directory} directory found in working directory - no outputs to copy")
            return IsolatedAgentEnvironmentResult(
                success=True,
                message=f"No outputs to copy - {output_directory} directory not found in working directory",
            )

        # Check if the output directory is empty
        try:
            environment_contents = environment_fs.listdir(str(environment_output_path))
            if not environment_contents:
                activity.logger.info(f"{output_directory} directory in working directory is empty - no outputs to copy")
                return IsolatedAgentEnvironmentResult(
                    success=True,
                    message=f"No outputs to copy - {output_directory} directory in working directory is empty",
                )
        except (OSError, ValueError) as e:
            activity.logger.warning(f"Failed to list working directory output contents: {e}")
            # Continue with copy attempt in case the directory exists but listing failed

        # Ensure the output directory exists in the source directory
        source_fs = FileSystemUtils.get_filesystem(str(workflow_output_path.parent))
        if not source_fs.exists(str(workflow_output_path.parent)):
            activity.logger.info(f"Creating {output_directory} directory in source: {workflow_output_path.parent}")
            source_fs.makedirs(str(workflow_output_path.parent), exist_ok=True)

        # Copy all contents from isolated environment output directory to source output directory with workflow ID
        activity.logger.info(f"Copying outputs from {environment_output_path} to {workflow_output_path}")
        await FileSystemUtils.copy_directory_async(
            str(environment_output_path),
            str(workflow_output_path),
        )

        activity.logger.info(f"Successfully copied analyze outputs to {workflow_output_path}")
        return IsolatedAgentEnvironmentResult(
            success=True,
            message=f"Analyze outputs copied successfully to {workflow_output_path}",
        )

    except (OSError, ValueError) as e:
        error_msg = f"Failed to copy analyze outputs: {e}"
        activity.logger.exception(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)


@activity.defn(name=sdk_constants.ACTIVITY_CLEANUP_ISOLATED_AGENT)
async def cleanup_isolated_environment_activity(
    environment_info: IsolatedAgentEnvironmentInfo,
    agent_config: AgentConfiguration,
) -> IsolatedAgentEnvironmentResult:
    """Clean up an isolated agent environment (git worktree or temporary directory).

    For ACT mode: Removes the worktree from git tracking, deletes the temporary branch,
    and removes the temporary directory.
    For ANALYZE mode: Removes the temporary directory.

    Args:
        environment_info: Information about the environment to clean up
        agent_config: Agent configuration to determine cleanup type

    Returns:
        IsolatedAgentEnvironmentResult with success status

    """
    workflow_id = activity.info().workflow_id
    activity.logger.info(f"Cleaning up isolated environment: {workflow_id}")

    # Handle temporary directory cleanup for ANALYZE mode
    if agent_config.mode == AgentModeEnum.ANALYZE:
        return await cleanup_temp_directory_activity(environment_info)

    # Handle git worktree cleanup for ACT mode
    if agent_config.mode == AgentModeEnum.ACT:
        return await cleanup_git_worktree_activity(environment_info, workflow_id)

    # Handle UNKNOWN mode - treat as temporary directory cleanup for safety
    if agent_config.mode == AgentModeEnum.UNKNOWN:
        activity.logger.warning("Agent mode is UNKNOWN during cleanup - treating as temporary directory cleanup")
        return await cleanup_temp_directory_activity(environment_info)

    error_msg = f"Unsupported agent mode during cleanup: {agent_config.mode}"
    activity.logger.error(error_msg)
    return IsolatedAgentEnvironmentResult(success=False, message=error_msg)


async def cleanup_git_worktree_activity(
    worktree_info: IsolatedAgentEnvironmentInfo,
    workflow_id: str,
) -> IsolatedAgentEnvironmentResult:
    """Clean up a git worktree specifically.

    Removes the worktree from git tracking, deletes the temporary branch,
    and removes the temporary directory.

    Args:
        worktree_info: Information about the worktree to clean up
        workflow_id: Workflow ID for logging and branch naming

    Returns:
        IsolatedAgentEnvironmentResult with success status

    """
    try:
        # Get the source repository
        repo = git.Repo(worktree_info.source_directory_path)

        worktree_path = Path(worktree_info.environment_path)
        worktree_fs = FileSystemUtils.get_filesystem(str(worktree_path))

        # Remove the worktree from git
        if worktree_fs.exists(str(worktree_path)):
            activity.logger.info(f"Removing worktree from git: {workflow_id}")
            repo.git.worktree("remove", str(worktree_path), "--force")

        # Clean up the temporary directory if it still exists
        if worktree_fs.exists(str(worktree_path)):
            activity.logger.info(f"Removing temporary worktree directory: {worktree_path}")
            await FileSystemUtils.remove_directory_async(str(worktree_path))

        # Always clean up the temporary branch
        try:
            worktree_name = f"isolated_agent_{workflow_id}"
            branch_name = f"awa-worktree-{worktree_name}"
            if branch_name in [head.name for head in repo.heads]:
                activity.logger.info(f"Removing temporary branch: {branch_name}")
                repo.delete_head(branch_name, force=True)
            else:
                activity.logger.info(f"Temporary branch {branch_name} not found, skipping deletion")
        except (GitCommandError, OSError, ValueError, AttributeError) as e:
            activity.logger.warning(f"Failed to cleanup temporary branch {branch_name}: {e}")
            # Don't fail the entire cleanup for branch deletion issues

        activity.logger.info(f"Successfully cleaned up worktree: {workflow_id}")
        return IsolatedAgentEnvironmentResult(
            success=True,
            message=f"Worktree {workflow_id} cleaned up successfully",
        )

    except InvalidGitRepositoryError:
        error_msg = f"Source repository is not valid during cleanup: {worktree_info.source_directory_path}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
    except GitCommandError as e:
        error_msg = f"Git command failed during cleanup: {e}"
        activity.logger.error(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
    except (OSError, ValueError) as e:
        error_msg = f"Failed to cleanup worktree: {e}"
        activity.logger.exception(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)


async def cleanup_temp_directory_activity(
    environment_info: IsolatedAgentEnvironmentInfo,
) -> IsolatedAgentEnvironmentResult:
    """Clean up a temporary directory.

    Removes the temporary directory and all its contents.

    Args:
        environment_info: Information about the temporary directory to clean up

    Returns:
        IsolatedAgentEnvironmentResult with success status

    """
    workflow_id = activity.info().workflow_id
    activity.logger.info(f"Cleaning up temporary directory: {workflow_id}")

    try:
        temp_path = Path(environment_info.environment_path)
        temp_fs = FileSystemUtils.get_filesystem(str(temp_path))

        # Remove the temporary directory if it exists
        if temp_fs.exists(str(temp_path)):
            activity.logger.info(f"Removing temporary directory: {temp_path}")
            await FileSystemUtils.remove_directory_async(str(temp_path))

        activity.logger.info(f"Successfully cleaned up temporary directory: {workflow_id}")
        return IsolatedAgentEnvironmentResult(
            success=True,
            message=f"Temporary directory {workflow_id} cleaned up successfully",
        )

    except (OSError, ValueError) as e:
        error_msg = f"Failed to cleanup temporary directory: {e}"
        activity.logger.exception(error_msg)
        return IsolatedAgentEnvironmentResult(success=False, message=error_msg)
