"""Aggregate per-feature api-usage.json files into a domain-level API inventory."""

from pathlib import Path

from pydantic import TypeAdapter
from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.inventory_item import InventoryItem
from cookbook.recipes.workflows.discover.models.ui_inventory_item import UiInventoryItem
from sdk_dist.python.awa.client import awa_activity


@workflow.defn(name="awa-discover-gather-api-inventory-from-ui-features")
class GatherApiInventoryFromUiFeaturesWorkflow:
    """Read each feature's ``api-usage.json`` and produce a de-duplicated API inventory.

    ``api-usage.json`` is written per-feature by ``/analyze-ui-feature``. This workflow
    just unions the lists and persists them to
    ``docs/entry-points/api-endpoints/inventory.{domain}.json``.
    """

    @workflow.run
    async def run(
        self,
        ui_inventory: list[UiInventoryItem],
        docs_dir: str,
        domain: str,
    ) -> list[InventoryItem]:
        seen: dict[str, InventoryItem] = {}
        adapter = TypeAdapter(list[InventoryItem])

        for feature in ui_inventory:
            usage_path = (
                Path(docs_dir) / "entry-points" / "ui-features" / feature.key / "api-usage.json"
            )
            raw = await awa_activity.read_file(str(usage_path), "")
            if not raw:
                continue
            for endpoint in adapter.validate_json(raw):
                seen.setdefault(endpoint.key, endpoint)

        api_inventory = sorted(seen.values(), key=lambda i: i.key)
        output_path = Path(docs_dir) / "entry-points" / "api-endpoints" / f"inventory.{domain}.json"
        await utils.write_inventory(output_path, api_inventory)

        workflow.logger.info(f"Collected {len(api_inventory)} unique API endpoints for '{domain}'.")
        return api_inventory
