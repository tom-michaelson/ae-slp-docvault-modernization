"""Generic develop workflow.

Three phases on a single timeline (no patterns, no PR creation):

    0. Branch setup.
    1. Page planning (analyze + generate-plan + validate), one pass per page,
       bounded concurrency.
    2. Implementation — per page, per batch, per item. Each batch ends with
       verification + git push of the batch branch. The human opens the PR.
"""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.develop.child_workflows.analyze_page_components_workflow import (
    AnalyzePageComponentsWorkflow,
)
from cookbook.recipes.workflows.develop.child_workflows.generate_page_plan_workflow import (
    GeneratePagePlanWorkflow,
)
from cookbook.recipes.workflows.develop.child_workflows.implement_item_workflow import (
    ImplementItemWorkflow,
)
from cookbook.recipes.workflows.develop.child_workflows.verify_workflow import VerifyWorkflow
from cookbook.recipes.workflows.develop.models.page_plan import E2EBatch, PagePlan, PlanItem
from cookbook.recipes.workflows.develop.models.page_result import BatchResult, ItemResult, PageResult
from cookbook.recipes.workflows.develop.models.workflow_input import DevelopWorkflowInput

_TYPE_PRIORITY: dict[str, int] = {"api-endpoint": 1, "ui-feature": 2}


@recipe_exposed(
    "Page-plan and implement Discover outputs into the Angular + Spring Boot target repo.",
)
@workflow.defn(name="awa-develop")
class DevelopWorkflow:
    @workflow.run
    async def run(self, workflow_input: DevelopWorkflowInput) -> str:
        if not workflow_input or not workflow_input.pages:
            return "No pages supplied; nothing to do."

        domain = "all"
        target_stack = workflow_input.target_stack or "angular-java"
        target_repo_dir = str(
            Path(
                workflow_input.target_repo_dir
                or "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/target_repo",
            ).expanduser(),
        )
        project_root_dir = str(
            Path(
                workflow_input.project_root_dir
                or "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc",
            ).expanduser(),
        )
        docs_dir = str(
            Path(
                workflow_input.docs_dir
                or "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/docs",
            ).expanduser(),
        )
        legacy_dir = _resolve_under_root(
            workflow_input.legacy_dir or "legacy/eShopOnWeb",
            project_root_dir,
        )
        # Default: stack on top of whatever branch the caller invoked us from,
        # NOT 'main'. Prevents Phase 0 from nuking untracked work on a feature
        # branch by checking out main first.
        starting_branch = workflow_input.starting_branch or await utils.get_current_branch(
            project_root_dir,
        )
        max_concurrency = workflow_input.max_concurrency
        agent_provider = "claude"

        # ------------------------------------------------------------------
        # Phase 0: branch setup
        # ------------------------------------------------------------------
        # Use run-id for a fresh suffix on every run. It's replay-safe (Temporal
        # supplies the same run_id on replay) but unique across runs, so we don't
        # reuse stale branches. Resumption of in-flight work relies on committed
        # .IMPLEMENTED markers on the starting branch, not on branch name reuse.
        suffix = workflow.info().run_id.replace("-", "")[:8]
        develop_branch = utils.develop_branch_name(domain, suffix)
        await utils.ensure_on_branch(project_root_dir, starting_branch, develop_branch)

        workflow.set_current_details(
            f"awa-develop on {develop_branch}; {len(workflow_input.pages)} pages.",
        )

        # ------------------------------------------------------------------
        # Phase 1: page planning (bounded concurrency across pages)
        # ------------------------------------------------------------------
        analyze_coros = [
            lambda page=page: workflow.execute_child_workflow(
                workflow=AnalyzePageComponentsWorkflow,
                args=[page, docs_dir, project_root_dir, legacy_dir, agent_provider],
                static_summary=f"analyze:{page}",
            )
            for page in workflow_input.pages
        ]
        analysis_paths = await utils.run_with_controlled_concurrency(
            coroutine_funcs=analyze_coros,
            max_concurrency=max_concurrency,
        )

        plan_coros = [
            lambda page=page, analysis=analysis: workflow.execute_child_workflow(
                workflow=GeneratePagePlanWorkflow,
                args=[
                    page,
                    domain,
                    docs_dir,
                    project_root_dir,
                    legacy_dir,
                    analysis,
                    agent_provider,
                ],
                static_summary=f"plan:{page}",
            )
            for page, analysis in zip(workflow_input.pages, analysis_paths, strict=True)
        ]
        plans: list[PagePlan] = await utils.run_with_controlled_concurrency(
            coroutine_funcs=plan_coros,
            max_concurrency=max_concurrency,
        )

        # ------------------------------------------------------------------
        # Phase 2: implementation (serial pages, serial batches, serial items)
        # ------------------------------------------------------------------
        page_results: list[PageResult] = []
        for plan in plans:
            result = await self._process_page(
                plan=plan,
                domain=domain,
                starting_branch=develop_branch,
                project_root_dir=project_root_dir,
                target_repo_dir=target_repo_dir,
                docs_dir=docs_dir,
                legacy_dir=legacy_dir,
                target_stack=target_stack,
                agent_provider=agent_provider,
            )
            page_results.append(result)

        total_items = sum(len(br.item_results) for pr in page_results for br in pr.batch_results)
        pushed = sum(1 for pr in page_results for br in pr.batch_results if br.pushed)
        return (
            f"awa-develop complete. {len(page_results)} page(s), "
            f"{total_items} item(s), {pushed} batch branch(es) pushed. "
            "Open PRs from the pushed branches when ready."
        )

    # ------------------------------------------------------------------
    # Per-page orchestration
    # ------------------------------------------------------------------

    async def _process_page(
        self,
        *,
        plan: PagePlan,
        domain: str,
        starting_branch: str,
        project_root_dir: str,
        target_repo_dir: str,
        docs_dir: str,
        legacy_dir: str,
        target_stack: str,
        agent_provider: str,
    ) -> PageResult:
        progress_branch = utils.progress_branch_name(domain, plan.page_key)
        await utils.ensure_on_branch(project_root_dir, starting_branch, progress_branch)

        in_progress_path = (
            Path(docs_dir)
            / "entry-points"
            / "ui-pages"
            / plan.page_key
            / f"page-plan.{domain}-{plan.page_key}.in-progress.json"
        )
        persisted = await utils.read_model(in_progress_path, PagePlan) or plan

        batch_results: list[BatchResult] = []
        parent_branch = starting_branch

        for idx, batch in enumerate(persisted.batches):
            expected_branch = utils.batch_branch_name(domain, plan.page_key, batch.batch_id)

            # Skip completed batches on resume.
            if batch.completed or (
                batch.pushed
                and batch.branch_name
                and await utils.branch_exists(project_root_dir, batch.branch_name)
            ):
                workflow.logger.info(
                    f"Skipping batch {batch.batch_id} (page={plan.page_key}) — already processed.",
                )
                parent_branch = batch.branch_name or expected_branch
                batch_results.append(
                    BatchResult(
                        batch_id=batch.batch_id,
                        branch=batch.branch_name,
                        pushed=batch.pushed,
                        verified=batch.completed,
                        item_results=[
                            ItemResult(key=i.key, type=i.type, status="skipped")
                            for i in batch.items
                        ],
                    ),
                )
                continue

            # Fresh / resumed batch branch.
            await utils.ensure_on_branch(project_root_dir, parent_branch, expected_branch)
            batch.branch_name = expected_branch
            await utils.write_model(in_progress_path, persisted)

            item_results = await self._run_batch(
                batch=batch,
                plan=plan,
                domain=domain,
                project_root_dir=project_root_dir,
                target_repo_dir=target_repo_dir,
                docs_dir=docs_dir,
                legacy_dir=legacy_dir,
                target_stack=target_stack,
                agent_provider=agent_provider,
            )

            # Batch verification (build + test with fix loops).
            verify_dir = str(
                Path(docs_dir)
                / "entry-points"
                / "ui-pages"
                / plan.page_key
                / "verify"
                / batch.batch_id,
            )
            verified: bool = await workflow.execute_child_workflow(
                workflow=VerifyWorkflow,
                args=[domain, batch.batch_id, project_root_dir, target_repo_dir, verify_dir, agent_provider],
                static_summary=f"verify:{plan.page_key}:{batch.batch_id}",
            )

            # Commit + push whatever we produced, even on verify failure, so the
            # human can inspect the branch.
            await utils.commit_paths(
                working_dir=project_root_dir,
                paths=[str(Path(target_repo_dir) / "source"), str(Path(docs_dir))],
                message=(
                    f"feat({domain}): {plan.page_key} batch {batch.batch_id} "
                    f"({'verified' if verified else 'unverified'})"
                ),
            )
            await utils.push_current_branch(project_root_dir, expected_branch)

            batch.pushed = True
            batch.completed = verified
            await utils.write_model(in_progress_path, persisted)

            batch_results.append(
                BatchResult(
                    batch_id=batch.batch_id,
                    branch=expected_branch,
                    pushed=True,
                    verified=verified,
                    item_results=item_results,
                ),
            )
            parent_branch = expected_branch

            # Return to progress branch before starting the next batch.
            await utils.ensure_on_branch(project_root_dir, parent_branch, progress_branch)

        all_implemented = all(
            ir.status in {"implemented", "skipped"}
            for br in batch_results
            for ir in br.item_results
        )
        return PageResult(
            page_key=plan.page_key,
            progress_branch=progress_branch,
            batch_results=batch_results,
            implementation_complete=all_implemented,
        )

    # ------------------------------------------------------------------
    # Per-batch orchestration (serial items, by type priority)
    # ------------------------------------------------------------------

    async def _run_batch(
        self,
        *,
        batch: E2EBatch,
        plan: PagePlan,
        domain: str,
        project_root_dir: str,
        target_repo_dir: str,
        docs_dir: str,
        legacy_dir: str,
        target_stack: str,
        agent_provider: str,
    ) -> list[ItemResult]:
        sorted_items = sorted(batch.items, key=_item_sort_key)
        results: list[ItemResult] = []
        for item in sorted_items:
            result: ItemResult = await workflow.execute_child_workflow(
                workflow=ImplementItemWorkflow,
                args=[
                    item,
                    plan.page_key,
                    domain,
                    docs_dir,
                    project_root_dir,
                    target_repo_dir,
                    legacy_dir,
                    target_stack,
                    agent_provider,
                ],
                static_summary=f"item:{item.key}",
            )
            results.append(result)
        return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _item_sort_key(item: PlanItem) -> tuple[int, str]:
    return _TYPE_PRIORITY.get(item.type, 99), item.key


def _resolve_under_root(value: str, project_root_dir: str) -> str:
    """Expand ``~``; anchor relative paths to ``project_root_dir``; return absolute str."""
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = Path(project_root_dir) / p
    return str(p)
