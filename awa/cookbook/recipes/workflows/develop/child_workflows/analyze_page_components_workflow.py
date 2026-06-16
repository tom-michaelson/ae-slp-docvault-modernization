"""Phase 1a: /develop.analyze-page-components — one per page."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils


@workflow.defn(name="awa-develop-analyze-page-components")
class AnalyzePageComponentsWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        docs_dir: str,
        working_dir: str,
        legacy_dir: str,
        agent_provider: str = "claude",
    ) -> str:
        output_path = Path(docs_dir) / "entry-points" / "ui-pages" / page_key / "page-analysis.json"

        if await utils.file_exists_non_empty(output_path):
            workflow.logger.info(f"page-analysis for {page_key} already present; skipping.")
            return str(output_path)

        await utils.run_slash_command(
            slash_command=(
                f"/develop.analyze-page-components page_key={page_key} "
                f"docs_dir={docs_dir} legacy_dir={legacy_dir} output_path={output_path}"
            ),
            name=f"AnalyzePageComponents_{page_key}",
            working_dir=working_dir,
            agent_provider=agent_provider,
        )
        return str(output_path)
