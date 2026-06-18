"""Pydantic models for the visual-page-comparison workflow.

Input/output models, plus the on-disk shapes the slash commands read and
write (``page-capture-plan.json`` and the per-screenshot analysis JSONs).

Field names mirror the JSON keys the slash commands emit (camelCase),
which is why N815 is suppressed module-wide.
"""
# ruff: noqa: N815, S105

from enum import StrEnum

from pydantic import BaseModel, Field
from pydantic.json_schema import SkipJsonSchema


class CaptureSide(StrEnum):
    LEGACY = "legacy"
    NEW = "new"


class ScreenshotCategory(StrEnum):
    BASELINE = "baseline"
    FLOW = "flow"


class ComparisonStatus(StrEnum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    ERROR = "ERROR"


# ---------------------------------------------------------------------------
# Capture plan (written by /visual-comparison.create-page-plan)
# ---------------------------------------------------------------------------


class ScreenshotEntry(BaseModel):
    name: str
    category: ScreenshotCategory
    description: str
    navigationHint: str | SkipJsonSchema[None] = Field(default=None)
    expectedElements: list[str] = Field(default_factory=list)


class CapturePlan(BaseModel):
    pageKey: str
    pageSummary: str
    legacyPath: str
    newPath: str
    screenshots: list[ScreenshotEntry]


# ---------------------------------------------------------------------------
# Per-screenshot analysis (written by /visual-comparison.compare-pair)
# ---------------------------------------------------------------------------


class ComparisonResult(BaseModel):
    """Loose model for the per-screenshot analysis JSON.

    The slash command writes a richer structure with all 6 heuristic blocks;
    we only deserialize the top-level fields the workflow needs to aggregate
    the report.
    """

    screenshot_name: str
    status: ComparisonStatus
    summary: str | SkipJsonSchema[None] = Field(default=None)
    error: str | SkipJsonSchema[None] = Field(default=None)


# ---------------------------------------------------------------------------
# Workflow input/output
# ---------------------------------------------------------------------------


class VisualPageComparisonInput(BaseModel):
    """Input for the page-level visual comparison workflow."""

    pageKey: str = Field(
        ...,
        description="Page key — folder name under docs/entry-points/ui-pages/. e.g. 'basket', 'home'.",
    )
    legacyUrl: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Legacy app base URL. Defaults to http://localhost:5106.",
    )
    newUrl: str | SkipJsonSchema[None] = Field(
        default=None,
        description="New Angular app base URL. Defaults to http://localhost:4200.",
    )
    docs_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Docs directory. Defaults to .../new-modernization-sdlc/docs.",
    )
    project_root_dir: str | SkipJsonSchema[None] = Field(
        default=None,
        description=(
            "Project root where .claude/commands/ lives; used as the agent cwd. "
            "Defaults to /Users/evan.scharfer/projects/Slalom/new-modernization-sdlc."
        ),
    )
    agent_provider: str | SkipJsonSchema[None] = Field(
        default=None,
        description="Agent provider. Defaults to 'claude'.",
    )
    max_concurrency: int = Field(
        default=5,
        description="Maximum number of concurrent comparisons in the fan-out phase.",
    )


class VisualPageComparisonOutput(BaseModel):
    pageKey: str
    overall_status: ComparisonStatus
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0
    error_count: int = 0
    report_path: str
