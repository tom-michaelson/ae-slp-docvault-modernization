"""Generic discover workflow.

Seven-phase pipeline modeled on the Williams NWP discover workflow, stripped of
legacy-stack specifics so any project can plug in its own slash-command
implementations:

    1. Inventory UI features.
    2. Analyze UI features (call trees, API usage, screenshots).
    3. Gather API inventory from the analyzed UI features.
    4. Analyze API endpoints.
    5. Describe entry points (functional descriptions).
    6. Plan API endpoints (functional spec + technical plan).
    7. Plan UI features (functional spec + technical plan).
"""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from cookbook.recipes.workflows.discover.child_workflows.analyze_api_endpoints_workflow import (
    AnalyzeApiEndpointsWorkflow,
)
from cookbook.recipes.workflows.discover.child_workflows.analyze_ui_features_workflow import (
    AnalyzeUiFeaturesWorkflow,
)
from cookbook.recipes.workflows.discover.child_workflows.describe_entry_points_workflow import (
    DescribeEntryPointsWorkflow,
)
from cookbook.recipes.workflows.discover.child_workflows.gather_api_inventory_from_ui_features_workflow import (
    GatherApiInventoryFromUiFeaturesWorkflow,
)
from cookbook.recipes.workflows.discover.child_workflows.inventory_ui_features_workflow import (
    InventoryUiFeaturesWorkflow,
)
from cookbook.recipes.workflows.discover.child_workflows.plan_api_endpoints_workflow import (
    PlanApiEndpointsWorkflow,
)
from cookbook.recipes.workflows.discover.child_workflows.plan_ui_features_workflow import (
    PlanUiFeaturesWorkflow,
)
from cookbook.recipes.workflows.discover.models.workflow_input import DiscoverWorkflowInput


@recipe_exposed(
    "Inventory, analyze, describe, and plan UI features + API endpoints for a legacy codebase.",
)
@workflow.defn(name="awa-discover")
class DiscoverWorkflow:
    @workflow.run
    async def run(self, workflow_input: DiscoverWorkflowInput | None = None) -> str:
        if workflow_input is None:
            workflow_input = DiscoverWorkflowInput()

        project_root_dir = str(
            Path(
                workflow_input.project_root_dir
                or "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc",
            ).expanduser(),
        )
        legacy_dir = _resolve_under_root(
            workflow_input.target_dir or "legacy/eShopOnWeb",
            project_root_dir,
        )
        app_url = workflow_input.app_url or "http://localhost:5106"
        domain = "all"
        target_stack = workflow_input.target_stack
        max_concurrency = workflow_input.max_concurrency
        docs_dir = str(
            Path(
                workflow_input.docs_dir
                or "/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/docs",
            ).expanduser(),
        )
        agent_provider = workflow_input.agent_provider

        workflow.set_current_details(
            f"Discovering {legacy_dir} (domain={domain}, target_stack={target_stack or 'unset'}).",
        )

        # All phases cwd into project_root_dir so slash commands under
        # .claude/commands/ at the repo root resolve uniformly. Phases 1/2/4 receive
        # legacy_dir as an extra arg so their slash commands can read the legacy source.

        # Phase 1: Inventory UI features
        ui_inventory = await workflow.execute_child_workflow(
            workflow=InventoryUiFeaturesWorkflow,
            args=[docs_dir, project_root_dir, legacy_dir, domain, agent_provider],
        )
        if not ui_inventory:
            return f"No UI features found in {legacy_dir} for domain '{domain}'."

        # Phase 2: Analyze UI features (call trees, api-usage, screenshots)
        ui_inventory = await workflow.execute_child_workflow(
            workflow=AnalyzeUiFeaturesWorkflow,
            args=[
                ui_inventory,
                docs_dir,
                project_root_dir,
                legacy_dir,
                app_url,
                max_concurrency,
                agent_provider,
            ],
        )

        # Phase 3: Gather API inventory from UI features (no agent calls, pure JSON merge)
        api_inventory = await workflow.execute_child_workflow(
            workflow=GatherApiInventoryFromUiFeaturesWorkflow,
            args=[ui_inventory, docs_dir, domain],
        )

        # Phase 4: Analyze API endpoints
        api_inventory = await workflow.execute_child_workflow(
            workflow=AnalyzeApiEndpointsWorkflow,
            args=[api_inventory, docs_dir, project_root_dir, legacy_dir, max_concurrency, agent_provider],
        )

        # Phase 5: Describe entry points
        await workflow.execute_child_workflow(
            workflow=DescribeEntryPointsWorkflow,
            args=[ui_inventory, api_inventory, docs_dir, project_root_dir, max_concurrency, agent_provider],
        )

        # Phase 6: Plan API endpoints
        await workflow.execute_child_workflow(
            workflow=PlanApiEndpointsWorkflow,
            args=[api_inventory, docs_dir, project_root_dir, max_concurrency, target_stack, agent_provider],
        )

        # Phase 7: Plan UI features
        await workflow.execute_child_workflow(
            workflow=PlanUiFeaturesWorkflow,
            args=[ui_inventory, docs_dir, project_root_dir, max_concurrency, target_stack, agent_provider],
        )

        return (
            f"Discovery + planning complete. "
            f"UI features: {len(ui_inventory)}, API endpoints: {len(api_inventory)}. "
            f"Outputs under {docs_dir}/entry-points/."
        )


def _resolve_under_root(value: str, project_root_dir: str) -> str:
    """Expand ``~``; anchor relative paths to ``project_root_dir``; return absolute str."""
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = Path(project_root_dir) / p
    return str(p)
