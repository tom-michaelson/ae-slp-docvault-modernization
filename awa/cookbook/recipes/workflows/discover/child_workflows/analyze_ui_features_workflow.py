"""Analyze UI features: extract call trees, record API usage, capture screenshots."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.discover import utils
from cookbook.recipes.workflows.discover.models.ui_inventory_item import UiInventoryItem
from sdk_dist.python.awa.client import awa_activity
from sdk_dist.python.awa.client.models.agent_modes.agent_configuration import McpServer

_PLAYWRIGHT_MCP = McpServer(
    mcp_json=(
        '{"mcpServers":{"playwright":{"command":"npx","args":["@playwright/mcp@latest",'
        '"--headless","--viewport-size=1920,1200"]}}}'
    ),
)


@workflow.defn(name="awa-discover-analyze-ui-features")
class AnalyzeUiFeaturesWorkflow:
    """Per UI feature, run call-tree extraction and capture a screenshot.

    Call-tree extraction runs with bounded concurrency (stateless Claude calls).
    Screenshots run serially because Playwright MCP dislikes parallel sessions.
    """

    @workflow.run
    async def run(
        self,
        ui_inventory: list[UiInventoryItem],
        docs_dir: str,
        working_dir: str,
        legacy_dir: str,
        app_url: str | None,
        max_concurrency: int,
        agent_provider: str = "claude",
        skip_screenshots: bool = False,
    ) -> list[UiInventoryItem]:
        if not ui_inventory:
            return ui_inventory

        workflow.set_current_details(f"Analyzing UI Features. {len(ui_inventory)} total.")

        analyze_coros = [
            lambda item=item: utils.run_slash_command(
                slash_command=(
                    f"/analyze-ui-feature key={item.key} legacy_dir={legacy_dir} "
                    f"location={item.location} "
                    f"output_dir={Path(docs_dir) / 'entry-points' / 'ui-features' / item.key}"
                ),
                name=f"AnalyzeUiFeature_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
            )
            for item in ui_inventory
        ]
        await utils.run_with_controlled_concurrency(
            coroutine_funcs=analyze_coros,
            max_concurrency=max_concurrency,
            on_complete_callback=lambda completed, total, _: workflow.set_current_details(
                f"Analyzing UI Features. {completed} of {total} completed.",
            ),
        )

        # Screenshots — serialized
        if skip_screenshots:
            return ui_inventory

        for idx, item in enumerate(ui_inventory):
            feature_dir = Path(docs_dir) / "entry-points" / "ui-features" / item.key
            marker_path = feature_dir / "screenshots" / "SCREENSHOTS_COMPLETE"
            if await awa_activity.read_file(str(marker_path), ""):
                continue

            target_hint = f"url={app_url}{item.uri}" if app_url and item.uri else f"file={item.location}"
            await utils.run_slash_command(
                slash_command=(
                    f"/take-screenshot-for-ui-feature key={item.key} legacy_dir={legacy_dir} "
                    f"{target_hint} "
                    f"output_dir={feature_dir / 'screenshots'} marker_path={marker_path}"
                ),
                name=f"TakeScreenshot_{item.key}",
                target_dir=working_dir,
                agent_provider=agent_provider,
                mcp=_PLAYWRIGHT_MCP,
            )
            workflow.set_current_details(
                f"Screenshotting UI Features. {idx + 1} of {len(ui_inventory)} completed.",
            )

        return ui_inventory
