"""Git utility functions for handling git operations with config management."""

import git
from git import Actor
from pydantic import BaseModel
from temporalio import activity

from awa.core.utils.file_system_utils import FileSystemUtils
from awa.sdk.models.agent_modes.agent_configuration import AgentConfiguration


class GitAuthorInfo(BaseModel):
    """Git author/committer information for operations."""

    model_config = {"arbitrary_types_allowed": True}

    has_existing_config: bool
    agent_name: str
    agent_email: str
    actor: Actor | None


async def get_git_author_info(agent_config: AgentConfiguration) -> GitAuthorInfo:
    """Get git author information based on config availability.

    Args:
        agent_config: Agent configuration containing provider information

    Returns:
        GitAuthorInfo with config status and author details

    """
    has_git_config = await FileSystemUtils.check_git_config_async()
    agent_name = f"AWA Agent: {agent_config.provider}"
    agent_email = f"awa-agent-{agent_config.provider.lower()}@example.com"

    if has_git_config:
        return GitAuthorInfo(
            has_existing_config=True,
            agent_name=agent_name,
            agent_email=agent_email,
            actor=None,
        )
    return GitAuthorInfo(
        has_existing_config=False,
        agent_name=agent_name,
        agent_email=agent_email,
        actor=Actor(agent_name, agent_email),
    )


def commit_with_git_config_handling(
    repo: git.Repo,
    message: str,
    git_info: GitAuthorInfo,
) -> git.Commit:
    """Create a commit with appropriate git config handling.

    Args:
        repo: Git repository to commit in
        message: Commit message
        git_info: Pre-computed git author information

    Returns:
        The created commit object

    """
    if git_info.has_existing_config:
        activity.logger.info("Using existing git configuration for commit")
        return repo.index.commit(message)
    activity.logger.info(f"No git configuration found, using agent as author: {git_info.agent_name}")
    return repo.index.commit(
        message,
        author=git_info.actor,
        committer=git_info.actor,
    )


def merge_with_git_config_handling(
    repo: git.Repo,
    commit_hexsha: str,
    git_info: GitAuthorInfo,
) -> None:
    """Perform a merge with appropriate git config handling.

    Args:
        repo: Git repository to merge in
        commit_hexsha: Commit hash to merge
        git_info: Pre-computed git author information

    """
    if git_info.has_existing_config:
        activity.logger.info("Using existing git configuration for merge")
        repo.git.merge(commit_hexsha, no_ff=True)
    else:
        activity.logger.info(f"No git configuration found, using agent for merge: {git_info.agent_name}")
        # Use custom environment for merge to specify author/committer
        with repo.git.custom_environment(
            GIT_AUTHOR_NAME=git_info.agent_name,
            GIT_AUTHOR_EMAIL=git_info.agent_email,
            GIT_COMMITTER_NAME=git_info.agent_name,
            GIT_COMMITTER_EMAIL=git_info.agent_email,
        ):
            repo.git.merge(commit_hexsha, no_ff=True)
