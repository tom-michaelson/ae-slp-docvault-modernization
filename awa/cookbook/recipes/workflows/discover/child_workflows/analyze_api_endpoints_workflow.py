"""Analyze each API endpoint: extract call tree and persist metadata."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.inventory_item import InventoryItem


@workflow.defn(name="awa-discover-analyze-api-endpoints")
class AnalyzeApiEndpointsWorkflow:
    """For each API endpoint, invoke ``/analyze-api-endpoint`` with bounded concurrency."""

    @workflow.run
    async def run(
        self,
        api_inventory: list[InventoryItem],
        docs_dir: str,
        working_dir: str,
        legacy_dir: str,
        max_concurrency: int,
        agent_provider: str = "claude",
    ) -> list[InventoryItem]:
        if not api_inventory:
            return api_inventory

        workflow.set_current_details(f"Analyzing API Endpoints. {len(api_inventory)} total.")

        coros = [
            lambda item=item: utils.run_slash_command(
                slash_command=(
                    f"/analyze-api-endpoint key={item.key} legacy_dir={legacy_dir} "
                    f"location={item.location} "
                    f"output_dir={Path(docs_dir) / 'entry-points' / 'api-endpoints' / item.key}"
                ),
                name=f"AnalyzeApiEndpoint_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
            )
            for item in api_inventory
        ]
        await utils.run_with_controlled_concurrency(
            coroutine_funcs=coros,
            max_concurrency=max_concurrency,
            on_complete_callback=lambda completed, total, _: workflow.set_current_details(
                f"Analyzing API Endpoints. {completed} of {total} completed.",
            ),
        )

        return api_inventory
