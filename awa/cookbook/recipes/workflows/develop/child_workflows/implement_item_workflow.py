"""Per-item 9-step implementation pipeline.

Each step writes a predictable artifact so re-runs can skip already-completed
work. The final ``.IMPLEMENTED`` marker short-circuits the whole pipeline on
resume.
"""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.develop.models.page_plan import PlanItem
from cookbook.recipes.workflows.develop.models.page_result import ItemResult
from sdk_dist.python.awa.client import awa_activity

_MAX_REVIEW_ATTEMPTS = 5
_MAX_AC_ATTEMPTS = 5


@workflow.defn(name="awa-develop-implement-item")
class ImplementItemWorkflow:
    @workflow.run
    async def run(
        self,
        item: PlanItem,
        page_key: str,
        domain: str,
        docs_dir: str,
        project_root_dir: str,
        target_repo_dir: str,
        legacy_dir: str,
        target_stack: str,
        agent_provider: str = "claude",
    ) -> ItemResult:
        entry_point_folder = _entry_point_folder(docs_dir, item)
        implemented_marker = Path(entry_point_folder) / ".IMPLEMENTED"

        if await utils.file_exists_non_empty(implemented_marker):
            workflow.logger.info(f"Item {item.key} already implemented; skipping.")
            return ItemResult(key=item.key, type=item.type, status="skipped", attempts=0)

        core = (
            f"item_key={item.key} item_type={item.type} "
            f"entry_point_folder_path={entry_point_folder} "
            f"target_repo_dir={target_repo_dir} legacy_dir={legacy_dir} "
            f"target_stack={target_stack}"
        )

        # Step 1: research
        await self._step_if_missing(
            path=Path(entry_point_folder) / "research.md",
            slash=f"/research-item {core}",
            name=f"Research_{item.key}",
            working_dir=project_root_dir,
            agent_provider=agent_provider,
        )

        # Step 2: entity relationships (soft — log and continue on failure)
        try:
            await self._step_if_missing(
                path=Path(entry_point_folder) / "relationship-discovery.json",
                slash=(
                    f"/discover-entity-relationships {core} "
                    f"page_key={page_key} domain={domain}"
                ),
                name=f"EntityRel_{item.key}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )
        except Exception as e:  # noqa: BLE001
            workflow.logger.warning(
                f"Entity relationship discovery failed for {item.key}: {e}. Continuing.",
            )

        # Step 3: type-specific plan
        await self._step_if_missing(
            path=Path(entry_point_folder) / "implementation-plan.md",
            slash=f"/{_type_cmd(item.type, 'plan')} {core}",
            name=f"Plan_{item.key}",
            working_dir=project_root_dir,
            agent_provider=agent_provider,
        )

        # Step 4: plan review
        await self._step_if_missing(
            path=Path(entry_point_folder) / "plan-review.md",
            slash=f"/{_type_cmd(item.type, 'review-plan')} {core}",
            name=f"ReviewPlan_{item.key}",
            working_dir=project_root_dir,
            agent_provider=agent_provider,
        )

        # Step 5: task list
        await self._step_if_missing(
            path=Path(entry_point_folder) / "task-list.md",
            slash=f"/{_type_cmd(item.type, 'create-task-list')} {core}",
            name=f"TaskList_{item.key}",
            working_dir=project_root_dir,
            agent_provider=agent_provider,
        )

        # Step 6: implement + review loop
        impl_attempts = await self._implement_review_loop(
            item=item,
            core=core,
            entry_point_folder=entry_point_folder,
            project_root_dir=project_root_dir,
            agent_provider=agent_provider,
        )

        # Step 7: validate vs functional spec
        functional_spec = Path(entry_point_folder) / "functional-spec.md"
        if await utils.file_exists_non_empty(functional_spec):
            ac_validated = await self._ac_validation_loop(
                item=item,
                core=core,
                entry_point_folder=entry_point_folder,
                project_root_dir=project_root_dir,
                agent_provider=agent_provider,
            )
            if not ac_validated:
                return ItemResult(
                    key=item.key,
                    type=item.type,
                    status="failed",
                    attempts=impl_attempts,
                    notes="AC validation failed after max attempts.",
                )
        else:
            workflow.logger.info(f"No functional-spec.md for {item.key}; skipping AC validation.")

        # Step 8: unit tests (non-blocking)
        await self._step_if_missing(
            path=Path(entry_point_folder) / "test-tracking.json",
            slash=f"/{_type_cmd(item.type, 'generate-unit-tests')} {core}",
            name=f"UnitTests_{item.key}",
            working_dir=project_root_dir,
            agent_provider=agent_provider,
        )

        # Step 9: .IMPLEMENTED marker
        await awa_activity.write_file(
            str(implemented_marker),
            f'{{"key": "{item.key}", "type": "{item.type}"}}',
        )

        return ItemResult(
            key=item.key,
            type=item.type,
            status="implemented",
            attempts=impl_attempts,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    async def _step_if_missing(
        *,
        path: Path,
        slash: str,
        name: str,
        working_dir: str,
        agent_provider: str,
    ) -> None:
        if await utils.file_exists_non_empty(path):
            return
        await utils.run_slash_command(
            slash_command=slash,
            name=name,
            working_dir=working_dir,
            agent_provider=agent_provider,
        )

    @staticmethod
    async def _implement_review_loop(
        *,
        item: PlanItem,
        core: str,
        entry_point_folder: str,
        project_root_dir: str,
        agent_provider: str,
    ) -> int:
        review_path = Path(entry_point_folder) / "implementation-review-result.json"
        if await utils.is_validated(review_path):
            return 0

        feedback = ""
        for attempt in range(1, _MAX_REVIEW_ATTEMPTS + 1):
            impl_cmd = _type_cmd(item.type, "implement")
            review_cmd = _type_cmd(item.type, "review")
            feedback_arg = f" prior_feedback={feedback!r}" if feedback else ""

            await utils.run_slash_command(
                slash_command=f"/{impl_cmd} {core}{feedback_arg}",
                name=f"Implement_{item.key}_attempt{attempt}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )
            await utils.run_slash_command(
                slash_command=f"/{review_cmd} {core}",
                name=f"Review_{item.key}_attempt{attempt}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )

            data = await utils.read_json(review_path, default=None)
            if isinstance(data, dict) and data.get("validated"):
                return attempt
            feedback = (data or {}).get("feedback", "") if isinstance(data, dict) else ""

        return _MAX_REVIEW_ATTEMPTS

    @staticmethod
    async def _ac_validation_loop(
        *,
        item: PlanItem,
        core: str,
        entry_point_folder: str,
        project_root_dir: str,
        agent_provider: str,
    ) -> bool:
        result_path = Path(entry_point_folder) / "ac-validation-result.json"
        if await utils.is_validated(result_path):
            return True

        feedback = ""
        for attempt in range(1, _MAX_AC_ATTEMPTS + 1):
            feedback_arg = f" prior_feedback={feedback!r}" if feedback else ""
            await utils.run_slash_command(
                slash_command=f"/validate-code-against-functional-spec {core}{feedback_arg}",
                name=f"ACValidate_{item.key}_attempt{attempt}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )

            data = await utils.read_json(result_path, default=None)
            if isinstance(data, dict) and data.get("validated"):
                return True
            feedback = (data or {}).get("feedback", "") if isinstance(data, dict) else ""

            # Fix pass before re-validating.
            impl_cmd = _type_cmd(item.type, "implement")
            await utils.run_slash_command(
                slash_command=f"/{impl_cmd} {core} prior_feedback={feedback!r}",
                name=f"ACFix_{item.key}_attempt{attempt}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )

        return False


def _entry_point_folder(docs_dir: str, item: PlanItem) -> str:
    subdir = "ui-features" if item.type == "ui-feature" else "api-endpoints"
    return str(Path(docs_dir) / "entry-points" / subdir / item.key)


def _type_cmd(item_type: str, action: str) -> str:
    ui = item_type == "ui-feature"
    return {
        "plan": "plan-ui-feature" if ui else "plan-api-endpoint",
        "review-plan": "review-plan-ui" if ui else "review-plan-api",
        "create-task-list": "create-task-list-ui" if ui else "create-task-list-api",
        "implement": "implement-ui" if ui else "implement",
        "review": "review-ui-implementation" if ui else "review-implementation",
        "generate-unit-tests": "generate-ui-unit-tests" if ui else "generate-api-unit-tests",
    }[action]
