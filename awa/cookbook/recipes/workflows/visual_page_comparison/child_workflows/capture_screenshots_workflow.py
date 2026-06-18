"""Phases 3 & 4: /visual-comparison.capture-legacy and capture-new.

Configures the Playwright MCP for the agent and runs the appropriate capture
slash command. Uses a SCREENSHOTS_COMPLETE marker for idempotency on rerun.
"""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.visual_page_comparison.models.visual_page_comparison import (
    CaptureSide,
)
from sdk_dist.python.awa.client.models.agent_modes.agent_configuration import McpServer


def _playwright_mcp() -> McpServer:
    """Headless Playwright MCP configured for 1440x900 — matches comparison runs.

    ``--isolated`` gives each agent an ephemeral profile so legacy/new captures
    never collide on a shared Chrome ``user-data-dir`` lock when invoked
    concurrently from the parent workflow.
    """
    return McpServer(
        command="npx",
        args=[
            "@playwright/mcp@latest",
            "--headless",
            "--isolated",
            "--viewport-size=1440,900",
        ],
    )


@workflow.defn(name="awa-visual-page-comparison-capture-screenshots")
class CaptureScreenshotsWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        side: CaptureSide,
        docs_dir: str,
        project_root_dir: str,
        agent_provider: str = "claude",
    ) -> str:
        screenshots_dir = (
            Path(docs_dir)
            / "entry-points"
            / "ui-pages"
            / page_key
            / "visual-comparison"
            / side.value
        )
        marker = screenshots_dir / "SCREENSHOTS_COMPLETE"

        if await utils.file_exists_non_empty(marker):
            workflow.logger.info(
                f"{side.value} capture for {page_key} already complete — skipping.",
            )
            return str(screenshots_dir)

        slash_command = (
            f"/visual-comparison.capture-{side.value} {page_key}"
        )
        await utils.run_slash_command(
            slash_command=slash_command,
            name=f"CaptureScreenshots_{side.value}_{page_key}",
            working_dir=project_root_dir,
            agent_provider=agent_provider,
            mcp=_playwright_mcp(),
        )

        if not await utils.file_exists_non_empty(marker):
            from temporalio.exceptions import ApplicationError

            raise ApplicationError(
                (
                    f"capture-{side.value} did not produce SCREENSHOTS_COMPLETE at "
                    f"{marker}. The capture command failed validation; rerun after "
                    "deleting the partial output."
                ),
                non_retryable=False,
            )
        return str(screenshots_dir)
