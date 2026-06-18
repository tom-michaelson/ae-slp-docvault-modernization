"""Produce functional-spec + technical-plan artifacts per UI feature."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.ui_inventory_item import UiInventoryItem


@workflow.defn(name="awa-discover-plan-ui-features")
class PlanUiFeaturesWorkflow:
    """Call ``/plan-ui-feature`` for each analyzed UI feature."""

    @workflow.run
    async def run(
        self,
        ui_inventory: list[UiInventoryItem],
        docs_dir: str,
        working_dir: str,
        max_concurrency: int,
        target_stack: str | None = None,
        agent_provider: str = "claude",
    ) -> None:
        if not ui_inventory:
            return

        stack_arg = f" target_stack={target_stack}" if target_stack else ""
        coros = [
            lambda item=item: utils.run_slash_command(
                slash_command=(
                    f"/plan-ui-feature key={item.key}{stack_arg} "
                    f"feature_dir={Path(docs_dir) / 'entry-points' / 'ui-features' / item.key}"
                ),
                name=f"PlanUiFeature_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
            )
            for item in ui_inventory
        ]

        workflow.set_current_details(f"Planning UI features. {len(coros)} total.")
        await utils.run_with_controlled_concurrency(
            coroutine_funcs=coros,
            max_concurrency=max_concurrency,
            on_complete_callback=lambda completed, total, _: workflow.set_current_details(
                f"Planning UI features. {completed} of {total} completed.",
            ),
        )
