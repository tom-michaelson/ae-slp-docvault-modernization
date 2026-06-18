"""Generate human-readable functional descriptions for every analyzed entry point."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.inventory_item import InventoryItem
from cookbook.recipes.workflows.discover.models.ui_inventory_item import UiInventoryItem


@workflow.defn(name="awa-discover-describe-entry-points")
class DescribeEntryPointsWorkflow:
    """Write a ``functional-description.md`` for each UI feature and API endpoint.

    Delegates to two slash commands so the wording/format can differ by entry-point
    type: ``/describe-ui-feature`` and ``/describe-api-endpoint``.
    """

    @workflow.run
    async def run(
        self,
        ui_inventory: list[UiInventoryItem],
        api_inventory: list[InventoryItem],
        docs_dir: str,
        working_dir: str,
        max_concurrency: int,
        agent_provider: str = "claude",
    ) -> None:
        ui_coros = [
            lambda item=item: utils.run_slash_command(
                slash_command=(
                    f"/describe-ui-feature key={item.key} "
                    f"feature_dir={Path(docs_dir) / 'entry-points' / 'ui-features' / item.key}"
                ),
                name=f"DescribeUiFeature_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
            )
            for item in ui_inventory
        ]
        api_coros = [
            lambda item=item: utils.run_slash_command(
                slash_command=(
                    f"/describe-api-endpoint key={item.key} "
                    f"endpoint_dir={Path(docs_dir) / 'entry-points' / 'api-endpoints' / item.key}"
                ),
                name=f"DescribeApiEndpoint_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
            )
            for item in api_inventory
        ]

        total = len(ui_coros) + len(api_coros)
        workflow.set_current_details(f"Describing entry points. {total} total.")
        await utils.run_with_controlled_concurrency(
            coroutine_funcs=ui_coros + api_coros,
            max_concurrency=max_concurrency,
            on_complete_callback=lambda completed, t, _: workflow.set_current_details(
                f"Describing entry points. {completed} of {t} completed.",
            ),
        )
