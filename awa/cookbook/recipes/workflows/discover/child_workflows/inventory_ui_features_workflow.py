"""Inventory UI features from the legacy codebase."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.ui_inventory_item import UiInventoryItem


@workflow.defn(name="awa-discover-inventory-ui-features")
class InventoryUiFeaturesWorkflow:
    """Scan ``target_dir`` and emit ``inventory.{domain}.json`` under ``ui-features``.

    The actual scanning logic lives in the ``/inventory-ui-features`` slash command so
    each project can bring its own heuristics without touching the workflow.
    """

    @workflow.run
    async def run(
        self,
        docs_dir: str,
        working_dir: str,
        legacy_dir: str,
        domain: str,
        agent_provider: str = "claude",
    ) -> list[UiInventoryItem]:
        inventory_path = Path(docs_dir) / "entry-points" / "ui-features" / f"inventory.{domain}.json"

        items = await utils.read_inventory(inventory_path, UiInventoryItem)
        if items:
            workflow.logger.info(f"UI feature inventory already present ({len(items)} items).")
            return items

        workflow.set_current_details(f"Inventorying UI features into {inventory_path}.")
        await utils.run_slash_command(
            slash_command=(
                f"/inventory-ui-features legacy_dir={legacy_dir} domain={domain} "
                f"output_path={inventory_path}"
            ),
            name=f"InventoryUiFeatures_{domain}",
            target_dir=working_dir,
            agent_provider=agent_provider,
        )

        items = await utils.read_inventory(inventory_path, UiInventoryItem)
        workflow.logger.info(f"Inventory produced {len(items)} UI features for domain '{domain}'.")
        return items
