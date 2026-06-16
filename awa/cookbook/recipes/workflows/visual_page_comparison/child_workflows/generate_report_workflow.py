"""Phase 6: render visual-comparison-report.md from per-pair analysis JSONs.

Pure Python — no agent. Reads every ``analysis/<name>.json`` and writes a
markdown summary plus the aggregate counts the parent workflow returns.
"""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.visual_page_comparison.models.visual_page_comparison import (
    ComparisonResult,
    ComparisonStatus,
    VisualPageComparisonOutput,
)
from sdk_dist.python.awa.client import awa_activity


def _aggregate_status(results: list[ComparisonResult]) -> ComparisonStatus:
    if any(r.status == ComparisonStatus.FAIL for r in results):
        return ComparisonStatus.FAIL
    if any(r.status == ComparisonStatus.ERROR for r in results):
        return ComparisonStatus.FAIL
    if any(r.status == ComparisonStatus.WARN for r in results):
        return ComparisonStatus.WARN
    return ComparisonStatus.PASS


def _render_markdown(
    page_key: str,
    overall: ComparisonStatus,
    results: list[ComparisonResult],
    legacy_url: str,
    new_url: str,
) -> str:
    lines: list[str] = []
    lines.append(f"# Visual Comparison Report — `{page_key}`")
    lines.append("")
    lines.append(f"- **Legacy URL:** {legacy_url}")
    lines.append(f"- **New URL:** {new_url}")
    lines.append(f"- **Overall:** **{overall.value}**")
    lines.append("")

    counts = {s: sum(1 for r in results if r.status == s) for s in ComparisonStatus}
    lines.append(
        f"PASS: {counts[ComparisonStatus.PASS]} | "
        f"WARN: {counts[ComparisonStatus.WARN]} | "
        f"FAIL: {counts[ComparisonStatus.FAIL]} | "
        f"ERROR: {counts[ComparisonStatus.ERROR]}",
    )
    lines.append("")

    lines.append("## Screenshots")
    lines.append("")
    lines.append("| Screenshot | Status | Summary |")
    lines.append("|---|---|---|")
    for r in results:
        summary = (r.summary or r.error or "").replace("|", r"\|").replace("\n", " ")
        lines.append(f"| `{r.screenshot_name}` | {r.status.value} | {summary} |")
    lines.append("")

    return "\n".join(lines)


@workflow.defn(name="awa-visual-page-comparison-generate-report")
class GenerateReportWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        legacy_url: str,
        new_url: str,
        docs_dir: str,
        results: list[ComparisonResult],
    ) -> VisualPageComparisonOutput:
        overall = _aggregate_status(results)
        markdown = _render_markdown(page_key, overall, results, legacy_url, new_url)

        report_path = (
            Path(docs_dir)
            / "entry-points"
            / "ui-pages"
            / page_key
            / "visual-comparison"
            / "visual-comparison-report.md"
        )
        await awa_activity.write_file(str(report_path), markdown)

        return VisualPageComparisonOutput(
            pageKey=page_key,
            overall_status=overall,
            pass_count=sum(1 for r in results if r.status == ComparisonStatus.PASS),
            warn_count=sum(1 for r in results if r.status == ComparisonStatus.WARN),
            fail_count=sum(1 for r in results if r.status == ComparisonStatus.FAIL),
            error_count=sum(1 for r in results if r.status == ComparisonStatus.ERROR),
            report_path=str(report_path),
        )
