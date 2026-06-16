"""Phase 1b+1c: /develop.generate-page-plan + inline validation."""

from pathlib import Path

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.develop.models.page_plan import PagePlan
from sdk_dist.python.awa.client import awa_activity


@workflow.defn(name="awa-develop-generate-page-plan")
class GeneratePagePlanWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        domain: str,
        docs_dir: str,
        working_dir: str,
        legacy_dir: str,
        page_analysis_path: str,
        agent_provider: str = "claude",
    ) -> PagePlan:
        plan_dir = Path(docs_dir) / "entry-points" / "ui-pages" / page_key
        plan_json = plan_dir / "page-plan.json"
        plan_md = plan_dir / "page-plan.md"
        validated_marker = plan_dir / "page-plan.VALIDATED"

        if not await utils.file_exists_non_empty(plan_json):
            await utils.run_slash_command(
                slash_command=(
                    f"/develop.generate-page-plan page_key={page_key} domain={domain} "
                    f"legacy_dir={legacy_dir} "
                    f"page_analysis_path={page_analysis_path} "
                    f"output_json_path={plan_json} output_md_path={plan_md}"
                ),
                name=f"GeneratePagePlan_{page_key}",
                working_dir=working_dir,
                agent_provider=agent_provider,
            )

        plan = await utils.read_model(plan_json, PagePlan)
        if plan is None:
            raise ApplicationError(
                f"Page plan was not produced at {plan_json}.",
                non_retryable=True,
            )

        if not await utils.file_exists_non_empty(validated_marker):
            self._validate(plan, page_key, domain)
            await self._check_functional_specs_exist(plan)
            await awa_activity.write_file(str(validated_marker), "ok")

        return plan

    @staticmethod
    def _validate(plan: PagePlan, expected_page_key: str, expected_domain: str) -> None:
        if plan.page_key != expected_page_key:
            raise ApplicationError(
                f"Plan page_key '{plan.page_key}' != expected '{expected_page_key}'.",
                non_retryable=True,
            )
        if plan.domain != expected_domain:
            raise ApplicationError(
                f"Plan domain '{plan.domain}' != expected '{expected_domain}'.",
                non_retryable=True,
            )
        if not plan.batches:
            raise ApplicationError("Page plan has no batches.", non_retryable=True)

        item_keys: set[str] = set()
        for batch in plan.batches:
            if not batch.items:
                raise ApplicationError(
                    f"Batch '{batch.batch_id}' has no items.",
                    non_retryable=True,
                )
            for item in batch.items:
                if item.key in item_keys:
                    raise ApplicationError(
                        f"Duplicate item key '{item.key}' in plan.",
                        non_retryable=True,
                    )
                item_keys.add(item.key)

        # Dependency references must resolve inside this plan.
        for batch in plan.batches:
            for item in batch.items:
                for dep in item.dependencies:
                    if dep not in item_keys:
                        raise ApplicationError(
                            f"Item '{item.key}' references unknown dependency '{dep}'.",
                            non_retryable=True,
                        )

    @staticmethod
    async def _check_functional_specs_exist(plan: PagePlan) -> None:
        for batch in plan.batches:
            for item in batch.items:
                if item.type == "ui-feature" and item.functional_spec_path:
                    if not await utils.file_exists_non_empty(item.functional_spec_path):
                        raise ApplicationError(
                            f"Item '{item.key}' references missing functional spec: "
                            f"{item.functional_spec_path}",
                            non_retryable=True,
                        )
