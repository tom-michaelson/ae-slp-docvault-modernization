"""Phase 2: /visual-comparison.create-page-plan — produce page-capture-plan.json."""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.workflows.develop import utils
from cookbook.recipes.workflows.visual_page_comparison.models.visual_page_comparison import (
    CapturePlan,
)


@workflow.defn(name="awa-visual-page-comparison-create-page-plan")
class CreatePagePlanWorkflow:
    @workflow.run
    async def run(
        self,
        page_key: str,
        docs_dir: str,
        project_root_dir: str,
        agent_provider: str = "claude",
    ) -> CapturePlan:
        output_path = (
            Path(docs_dir)
            / "entry-points"
            / "ui-pages"
            / page_key
            / "visual-comparison"
            / "page-capture-plan.json"
        )

        if not await utils.file_exists_non_empty(output_path):
            await utils.run_slash_command(
                slash_command=f"/visual-comparison.create-page-plan {page_key}",
                name=f"CreatePagePlan_{page_key}",
                working_dir=project_root_dir,
                agent_provider=agent_provider,
            )

        plan = await utils.read_model(output_path, CapturePlan)
        if plan is None:
            from temporalio.exceptions import ApplicationError

            raise ApplicationError(
                f"create-page-plan did not produce a valid CapturePlan at {output_path}",
                non_retryable=True,
            )
        return plan
