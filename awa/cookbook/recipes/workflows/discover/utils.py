"""Utility helpers for the generic discover workflow."""

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

TModel = TypeVar("TModel", bound=BaseModel)


async def run_slash_command(
    slash_command: str,
    name: str,
    target_dir: str,
    agent_provider: str = "claude",
    mcp: McpServer | None = None,
    timeout_seconds: int = 60 * 30,
) -> str:
    """Execute a slash command using an agent against the legacy codebase.

    Mirrors the shape of the Williams-specific discover workflow helper, but kept minimal
    so this generic flow has no cross-package imports.
    """
    # Route stream events under the top-level workflow id so all children show
    # up in one streaming tab.
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
        working_directory=str(Path(target_dir)),
        initialize=False,
        stream_enabled=True,
        timeout_seconds=timeout_seconds,
        mcp=mcp,
        # Group under the top-level workflow id; leave stream_session_id to
        # auto-gen so per-invocation UI lookups resolve.
        parent_session_id=root_workflow_id,
    )

    # The UI's AgentDetailView extracts the top-level workflow id from the
    # session id via regex. Embedding it in the session name makes the regex
    # match so clicking a session in the UI resolves.
    result: TaskResponseModel = await awa_workflow.execute_agent(
        name=f"{name}-{root_workflow_id}",
        agent_config=agent_config,
    )
    if result.status != "completed":
        output_tail = (result.output or "")[-2000:]
        raise ApplicationError(
            (
                f"Agent failed to complete slash command.\n"
                f"  slash_command: {slash_command}\n"
                f"  working_dir:   {target_dir}\n"
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


async def read_inventory(path: str | Path, model: type[TModel]) -> list[TModel]:
    """Read a JSON array from disk and validate it as ``list[model]``.

    Returns ``[]`` if the file is missing or empty.
    """
    raw = await awa_activity.read_file(str(path), "")
    if not raw:
        return []
    return TypeAdapter(list[model]).validate_json(raw)


async def write_inventory(path: str | Path, items: list[BaseModel]) -> None:
    """Write a list of pydantic models as pretty JSON."""
    await awa_activity.write_file(
        str(path),
        json.dumps([item.model_dump(mode="json", by_alias=True) for item in items], indent=2),
    )
