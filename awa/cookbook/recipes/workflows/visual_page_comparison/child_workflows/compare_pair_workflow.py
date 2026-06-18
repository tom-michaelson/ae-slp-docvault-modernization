"""Phase 5 fan-out unit: /visual-comparison.compare-pair for one screenshot."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.visual_page_comparison.models.visual_page_comparison import (
    ComparisonResult,
    ComparisonStatus,
)


@workflow.defn(name="awa-visual-page-comparison-compare-pair")
class ComparePairWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        screenshot_name: str,
        docs_dir: str,
        project_root_dir: str,
        agent_provider: str = "claude",
    ) -> ComparisonResult:
        analysis_path = (
            Path(docs_dir)
            / "entry-points"
            / "ui-pages"
            / page_key
            / "visual-comparison"
            / "analysis"
            / f"{screenshot_name}.json"
        )

        if not await utils.file_exists_non_empty(analysis_path):
            await utils.run_slash_command(
                slash_command=f"/visual-comparison.compare-pair {page_key} {screenshot_name}",
                name=f"ComparePair_{page_key}_{screenshot_name}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )

        result = await utils.read_model(analysis_path, ComparisonResult)
        if result is None:
            return ComparisonResult(
                screenshot_name=screenshot_name,
                status=ComparisonStatus.ERROR,
                error="comparison-output-missing",
                summary=f"No analysis JSON written at {analysis_path}",
            )
        return result
