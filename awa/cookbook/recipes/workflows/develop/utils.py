"""Utility helpers for the generic develop workflow.

Mirrors the discover workflow's ``utils.py`` approach: a small set of thin
wrappers around the AWA SDK that are safe to call from inside a Temporal
workflow. Git helpers are added for the develop pipeline's branch stacking.
"""

import asyncio
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter
from temporalio import workflow
from temporalio.exceptions import ApplicationError

from sdk_dist.python.awa.client import awa_activity, awa_workflow
from sdk_dist.python.awa.client.models.agent_modes.agent_configuration import AgentConfiguration, McpServer
from sdk_dist.python.awa.client.models.agent_modes.task_response_model import TaskResponseModel
from sdk_dist.python.awa.client.models.command_result import CommandInput, CommandResult

TModel = TypeVar("TModel", bound=BaseModel)


# ---------------------------------------------------------------------------
# Slash command execution
# ---------------------------------------------------------------------------


async def run_slash_command(
    slash_command: str,
    name: str,
    working_dir: str,
    agent_provider: str = "claude",
    mcp: McpServer | None = None,
    timeout_seconds: int = 60 * 30,
) -> str:
    """Execute a slash command via an agent with ``working_dir`` as cwd."""
    # Route stream events under the TOP-LEVEL workflow id so every child's
    # output shows up in the same streaming tab. Walk `workflow.info().parent`
    # up to the root; fall back to the current workflow id if we're already at
    # the top.
    info = workflow.info()
    root_workflow_id = info.workflow_id
    parent = info.parent
    while parent is not None:
        root_workflow_id = parent.workflow_id
        parent = getattr(parent, "parent", None)

    agent_config = AgentConfiguration(
        provider=agent_provider,
        mode="act",
        prompt=slash_command,
        working_directory=str(Path(working_dir)),
        initialize=False,
        stream_enabled=True,
        timeout_seconds=timeout_seconds,
        mcp=mcp,
        # Parent id groups all per-invocation sessions under the top-level
        # workflow so they all appear in one place. stream_session_id is left
        # to auto-gen per ExecuteAgent workflow — that id is what the UI looks
        # up when you click an entry, so overriding it breaks the UI.
        parent_session_id=root_workflow_id,
    )

    # The UI's AgentDetailView extracts the workflow id from the session id via
    # regex `\d{8}_\d{6}_\d+_[a-f0-9]+`. Embedding the top-level workflow id in
    # the session name makes that regex match so clicking a session resolves.
    result: TaskResponseModel = await awa_workflow.execute_agent(
        name=f"{name}-{root_workflow_id}",
        agent_config=agent_config,
    )
    if result.status != "completed":
        # Surface everything the agent told us so the failure is diagnosable.
        output_tail = (result.output or "")[-2000:]
        raise ApplicationError(
            (
                f"Agent failed to complete slash command.\n"
                f"  slash_command: {slash_command}\n"
                f"  working_dir:   {working_dir}\n"
                f"  status:        {result.status!r}\n"
                f"  reason:        {result.reason!r}\n"
                f"  exception:     {result.exception!r}\n"
                f"  output (tail): {output_tail!r}"
            ),
            non_retryable=False,
        )
    return result.output or ""


async def run_with_controlled_concurrency(
    coroutine_funcs: list[Callable],
    max_concurrency: int,
    on_complete_callback: Callable[[int, int, Any], None] | None = None,
) -> list[Any]:
    """Run coroutine factories with a concurrency ceiling, preserving input order."""
    if not coroutine_funcs:
        return []

    actual_concurrency = min(int(max_concurrency), len(coroutine_funcs))
    semaphore = asyncio.Semaphore(actual_concurrency)

    async def run_with_semaphore(index: int, coro_func: Callable) -> tuple[int, Any]:
        async with semaphore:
            result = await coro_func()
            return index, result

    tasks = [
        asyncio.create_task(run_with_semaphore(i, coro_func))
        for i, coro_func in enumerate(coroutine_funcs)
    ]

    results: list[Any] = [None] * len(coroutine_funcs)
    completed_count = 0
    total_count = len(coroutine_funcs)

    for completed_task in asyncio.as_completed(tasks):
        index, result = await completed_task
        results[index] = result
        completed_count += 1
        if on_complete_callback:
            try:
                on_complete_callback(completed_count, total_count, result)
            except Exception as e:  # noqa: BLE001
                workflow.logger.warning(f"Status callback failed: {e}", exc_info=True)

    return results


# ---------------------------------------------------------------------------
# File / JSON helpers
# ---------------------------------------------------------------------------


async def file_exists_non_empty(path: str | Path) -> bool:
    """True if the file exists and is non-empty."""
    content = await awa_activity.read_file(str(path), "")
    return bool(content)


async def write_json(path: str | Path, obj: Any) -> None:
    await awa_activity.write_file(str(path), json.dumps(obj, indent=2))


async def read_json(path: str | Path, default: Any | None = None) -> Any:
    raw = await awa_activity.read_file(str(path), "")
    if not raw:
        return default
    return json.loads(raw)


async def read_model(path: str | Path, model: type[TModel]) -> TModel | None:
    raw = await awa_activity.read_file(str(path), "")
    if not raw:
        return None
    return TypeAdapter(model).validate_json(raw)


async def write_model(path: str | Path, item: BaseModel) -> None:
    await awa_activity.write_file(
        str(path),
        json.dumps(item.model_dump(mode="json", by_alias=True), indent=2),
    )


async def is_validated(result_path: str | Path) -> bool:
    """Check the ``{ "validated": bool }`` shape the review commands write."""
    data = await read_json(result_path, default=None)
    if not isinstance(data, dict):
        return False
    return bool(data.get("validated"))


# ---------------------------------------------------------------------------
# Git helpers (all operate via awa_activity.run_command)
# ---------------------------------------------------------------------------


async def _git(working_dir: str, command: str) -> CommandResult:
    return await awa_activity.run_command(
        CommandInput(command=command, working_dir=working_dir),
    )


async def get_current_branch(working_dir: str) -> str:
    result = await _git(working_dir, "git rev-parse --abbrev-ref HEAD")
    if not result.success:
        raise ApplicationError(
            f"Failed to read current branch: {result.output}",
            non_retryable=True,
        )
    return result.output.strip()


async def branch_exists(working_dir: str, branch_name: str) -> bool:
    result = await _git(
        working_dir,
        f"git show-ref --verify --quiet refs/heads/{branch_name}",
    )
    return result.success


async def has_uncommitted_changes(working_dir: str) -> bool:
    result = await _git(working_dir, "git status --porcelain")
    if not result.success:
        raise ApplicationError(
            f"Failed to check git status: {result.output}",
            non_retryable=True,
        )
    return bool(result.output.strip())


async def ensure_on_branch(
    working_dir: str,
    starting_branch: str,
    expected_branch: str,
) -> None:
    """Guarantee ``working_dir`` is checked out on ``expected_branch``.

    If the branch exists, switch to it. If it doesn't, checkout
    ``starting_branch`` first and create the new one from there. Refuses to
    switch if there are uncommitted changes.
    """
    current = await get_current_branch(working_dir)
    if current == expected_branch:
        return

    if await has_uncommitted_changes(working_dir):
        raise ApplicationError(
            f"Cannot switch to '{expected_branch}' from '{current}' with uncommitted changes.",
            non_retryable=True,
        )

    if await branch_exists(working_dir, expected_branch):
        result = await _git(working_dir, f"git checkout {expected_branch}")
        if not result.success:
            raise ApplicationError(
                f"Failed to checkout existing branch {expected_branch}: {result.output}",
                non_retryable=True,
            )
        return

    # Checkout starting branch, then create the expected branch from it.
    result = await _git(working_dir, f"git checkout {starting_branch}")
    if not result.success:
        raise ApplicationError(
            f"Failed to checkout starting branch {starting_branch}: {result.output}",
            non_retryable=True,
        )
    result = await _git(working_dir, f"git checkout -b {expected_branch}")
    if not result.success:
        raise ApplicationError(
            f"Failed to create branch {expected_branch}: {result.output}",
            non_retryable=True,
        )


async def commit_paths(working_dir: str, paths: list[str], message: str) -> bool:
    """Stage, commit, and return True if a commit was produced."""
    if not paths:
        return False

    quoted = " ".join(f"'{p}'" for p in paths)
    add = await _git(working_dir, f"git add -- {quoted}")
    if not add.success:
        raise ApplicationError(
            f"Failed to stage files: {add.output}",
            non_retryable=True,
        )

    status = await _git(working_dir, "git status --porcelain")
    if not status.output.strip():
        return False

    commit = await _git(working_dir, f"git commit -m {message!r}")
    if not commit.success:
        raise ApplicationError(
            f"Failed to commit: {commit.output}",
            non_retryable=True,
        )
    return True


async def push_current_branch(working_dir: str, branch: str) -> None:
    result = await _git(working_dir, f"git push -u origin {branch}")
    if not result.success:
        raise ApplicationError(
            f"Failed to push branch {branch}: {result.output}",
            non_retryable=True,
        )


# ---------------------------------------------------------------------------
# Branch-name helpers
# ---------------------------------------------------------------------------


def _sanitize(value: str) -> str:
    import re

    cleaned = re.sub(r"[^a-z0-9-]", "-", value.lower())
    return re.sub(r"-+", "-", cleaned).strip("-")


def progress_branch_name(domain: str, page_key: str) -> str:
    return f"feature/{_sanitize(domain)}-{_sanitize(page_key)}-progress"


def batch_branch_name(domain: str, page_key: str, batch_id: str) -> str:
    return f"feature/{_sanitize(domain)}-{_sanitize(page_key)}-{_sanitize(batch_id)}"


def develop_branch_name(domain: str, suffix: str) -> str:
    return f"feature/{_sanitize(domain)}-develop-{_sanitize(suffix)}"
