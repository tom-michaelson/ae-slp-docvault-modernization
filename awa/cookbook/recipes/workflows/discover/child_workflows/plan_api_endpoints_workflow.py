"""Produce functional-spec + technical-plan artifacts per API endpoint."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.inventory_item import InventoryItem


@workflow.defn(name="awa-discover-plan-api-endpoints")
class PlanApiEndpointsWorkflow:
    """Call ``/plan-api-endpoint`` for each analyzed API endpoint.

    ``target_stack`` is forwarded to the slash command so project-specific templates
    (React/Blazor/Spring/etc.) can decide how to shape the technical plan.
    """

    @workflow.run
    async def run(
        self,
        api_inventory: list[InventoryItem],
        docs_dir: str,
        working_dir: str,
        max_concurrency: int,
        target_stack: str | None = None,
        agent_provider: str = "claude",
    ) -> None:
        if not api_inventory:
            return

        stack_arg = f" target_stack={target_stack}" if target_stack else ""
        coros = [
            lambda item=item: utils.run_slash_command(
                slash_command=(
                    f"/plan-api-endpoint key={item.key}{stack_arg} "
                    f"endpoint_dir={Path(docs_dir) / 'entry-points' / 'api-endpoints' / item.key}"
                ),
                name=f"PlanApiEndpoint_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
            )
            for item in api_inventory
        ]

        workflow.set_current_details(f"Planning API endpoints. {len(coros)} total.")
        await utils.run_with_controlled_concurrency(
            coroutine_funcs=coros,
            max_concurrency=max_concurrency,
            on_complete_callback=lambda completed, total, _: workflow.set_current_details(
                f"Planning API endpoints. {completed} of {total} completed.",
            ),
        )
