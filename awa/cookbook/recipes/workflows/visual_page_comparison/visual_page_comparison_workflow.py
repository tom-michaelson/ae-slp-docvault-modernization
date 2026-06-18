"""Visual page comparison workflow.

Compares the legacy and new applications page-by-page using six functional
heuristics. Adapted from the Williams page-level comparison workflow with
all the Passage-specific bits removed (no login, no menu tree, no Spring
Boot start, no PR creation).

Phases:

    1. Validate prerequisites (curl both URLs, write ui-validation-result.json)
    2. Create capture plan (read inventory + feature specs → page-capture-plan.json)
    3. Capture legacy + new screenshots in parallel (Playwright MCP, headless 1440x900)
    4. Compare each pair via the 6 heuristics (fan-out under maxConcurrency)
    5. Generate visual-comparison-report.md
"""

from pathlib import Path

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.visual_page_comparison.child_workflows.capture_screenshots_workflow import (
    CaptureScreenshotsWorkflow,
)
from cookbook.recipes.workflows.visual_page_comparison.child_workflows.compare_pair_workflow import (
    ComparePairWorkflow,
)
from cookbook.recipes.workflows.visual_page_comparison.child_workflows.create_page_plan_workflow import (
    CreatePagePlanWorkflow,
)
from cookbook.recipes.workflows.visual_page_comparison.child_workflows.generate_report_workflow import (
    GenerateReportWorkflow,
)
from cookbook.recipes.workflows.visual_page_comparison.child_workflows.validate_prerequisites_workflow import (
    ValidatePrerequisitesWorkflow,
)
from cookbook.recipes.workflows.visual_page_comparison.models.visual_page_comparison import (
    CapturePlan,
    CaptureSide,
    ComparisonResult,
    VisualPageComparisonInput,
    VisualPageComparisonOutput,
)

_DEFAULT_LEGACY_URL = "http://localhost:5106"
_DEFAULT_NEW_URL = "http://localhost:4200"
_DEFAULT_PROJECT_ROOT = "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc"
_DEFAULT_DOCS_DIR = "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/docs"


@recipe_exposed(
    "Visually compare the legacy app (5106) and the new Angular app (4200) for one page.",
)
@workflow.defn(name="awa-visual-page-comparison")
class VisualPageComparisonWorkflow:
    @workflow.run
    async def run(self, workflow_input: VisualPageComparisonInput) -> VisualPageComparisonOutput:
        page_key = workflow_input.pageKey
        legacy_url = workflow_input.legacyUrl or _DEFAULT_LEGACY_URL
        new_url = workflow_input.newUrl or _DEFAULT_NEW_URL
        project_root_dir = str(Path(workflow_input.project_root_dir or _DEFAULT_PROJECT_ROOT).expanduser())
        docs_dir = str(Path(workflow_input.docs_dir or _DEFAULT_DOCS_DIR).expanduser())
        agent_provider = workflow_input.agent_provider or "claude"
        max_concurrency = workflow_input.max_concurrency

        workflow.set_current_details(
            f"awa-visual-page-comparison: page={page_key}, legacy={legacy_url}, new={new_url}",
        )

        # ------------------------------------------------------------------
        # Phase 1: validate prerequisites
        # ------------------------------------------------------------------
        validation = await workflow.execute_child_workflow(
            workflow=ValidatePrerequisitesWorkflow,
            args=[page_key, legacy_url, new_url, docs_dir, project_root_dir, agent_provider],
            static_summary=f"validate:{page_key}",
        )
        if not validation.get("legacyHealthy") or not validation.get("newHealthy"):
            raise ApplicationError(
                (
                    f"Prerequisites failed: legacyHealthy={validation.get('legacyHealthy')}, "
                    f"newHealthy={validation.get('newHealthy')}. "
                    f"Start the legacy stack (docker compose up at legacy/eShopOnWeb) and the "
                    f"Angular dev server (ng serve --port 4200) before retrying."
                ),
                non_retryable=True,
            )

        # ------------------------------------------------------------------
        # Phase 2: create capture plan
        # ------------------------------------------------------------------
        plan: CapturePlan = await workflow.execute_child_workflow(
            workflow=CreatePagePlanWorkflow,
            args=[page_key, docs_dir, project_root_dir, agent_provider],
            static_summary=f"plan:{page_key}",
        )
        if not plan.screenshots:
            raise ApplicationError(
                f"Capture plan for '{page_key}' contains no screenshots; nothing to compare.",
                non_retryable=True,
            )

        # ------------------------------------------------------------------
        # Phase 3 & 4: capture legacy then new (serial — see below)
        # ------------------------------------------------------------------
        # Serial, not parallel. Even with `--isolated` profiles per agent, two
        # concurrent captures both invoke the SAME Playwright MCP process and
        # have raced on browser state in practice. Serial keeps this
        # deterministic and only adds ~1 capture's worth of wall-clock time.
        for side in (CaptureSide.LEGACY, CaptureSide.NEW):
            await workflow.execute_child_workflow(
                workflow=CaptureScreenshotsWorkflow,
                args=[page_key, side, docs_dir, project_root_dir, agent_provider],
                static_summary=f"capture:{side.value}:{page_key}",
            )

        # ------------------------------------------------------------------
        # Phase 5: compare every pair (fan-out under max_concurrency)
        # ------------------------------------------------------------------
        compare_coros = [
            lambda name=entry.name: workflow.execute_child_workflow(
                workflow=ComparePairWorkflow,
                args=[page_key, name, docs_dir, project_root_dir, agent_provider],
                static_summary=f"compare:{page_key}:{name}",
            )
            for entry in plan.screenshots
        ]
        results: list[ComparisonResult] = await utils.run_with_controlled_concurrency(
            coroutine_funcs=compare_coros,
            max_concurrency=max_concurrency,
        )

        # ------------------------------------------------------------------
        # Phase 6: render markdown report
        # ------------------------------------------------------------------
        return await workflow.execute_child_workflow(
            workflow=GenerateReportWorkflow,
            args=[page_key, legacy_url, new_url, docs_dir, results],
            static_summary=f"report:{page_key}",
        )
