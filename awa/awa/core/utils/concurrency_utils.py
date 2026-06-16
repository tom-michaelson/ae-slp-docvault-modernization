import asyncio
from collections.abc import Callable
from typing import Any

from temporalio import workflow


class ConcurrencyUtils:
    @staticmethod
    async def run_with_controlled_concurrency(
        coroutine_funcs: list[Callable],
        max_concurrency: int,
    ) -> list[Any]:
        """Run a list of coroutine functions with controlled concurrency.

        This function ensures that at most `max_concurrency` coroutines are running
        simultaneously, but always maintains the maximum number of running tasks
        (when one completes, the next one starts immediately).

        Args:
            coroutine_funcs: List of coroutine functions to execute
            max_concurrency: Maximum number of coroutines to run simultaneously

        Returns:
            List of results in the same order as the input coroutine_funcs

        """
        if not coroutine_funcs:
            return []

        # Limit concurrency to the number of available tasks
        actual_concurrency = min(int(max_concurrency), len(coroutine_funcs))

        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(actual_concurrency)

        async def run_with_semaphore(index: int, coro_func: Callable) -> tuple[int, Any]:
            async with semaphore:
                result = await coro_func()
                return index, result

        # Create all tasks
        tasks = [asyncio.create_task(run_with_semaphore(i, coro_func)) for i, coro_func in enumerate(coroutine_funcs)]

        # Wait for all tasks to complete and collect results
        results = [None] * len(coroutine_funcs)
        for completed_task in workflow.as_completed(tasks):
            index, result = await completed_task
            results[index] = result

        return results
