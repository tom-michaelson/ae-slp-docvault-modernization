# Generic Discover Workflow (`awa-discover`)

A framework-agnostic port of the Williams NWP discover workflow. Given a legacy
code directory, it runs seven sequential phases and writes all artifacts under
`{docs_dir}/entry-points/` — by default
`/Users/evan.scharfer/projects/Slalom/new-modernization-sdlc/docs`, kept separate
from the legacy codebase.

## Phases

| # | Phase | Child workflow | Slash command(s) invoked |
| - | ----- | -------------- | ------------------------ |
| 1 | Inventory UI features | `InventoryUiFeaturesWorkflow` | `/inventory-ui-features` |
| 2 | Analyze UI features | `AnalyzeUiFeaturesWorkflow` | `/analyze-ui-feature`, `/take-screenshot-for-ui-feature` |
| 3 | Gather API inventory from UI | `GatherApiInventoryFromUiFeaturesWorkflow` | *(none — unions per-feature `api-usage.json`)* |
| 4 | Analyze API endpoints | `AnalyzeApiEndpointsWorkflow` | `/analyze-api-endpoint` |
| 5 | Describe entry points | `DescribeEntryPointsWorkflow` | `/describe-ui-feature`, `/describe-api-endpoint` |
| 6 | Plan API endpoints | `PlanApiEndpointsWorkflow` | `/plan-api-endpoint` |
| 7 | Plan UI features | `PlanUiFeaturesWorkflow` | `/plan-ui-feature` |

Phases 2 and 4+ run per-item with bounded concurrency (`max_concurrency`, default 5).
Screenshots within phase 2 run **serially** because Playwright MCP is unhappy
with concurrent browser sessions.

## Inputs

```python
class DiscoverWorkflowInput:
    target_dir: str | None = None        # LEGACY code dir; defaults to "../eShopOnWeb"
    target_repo_dir: str | None = None   # modernization target (Java) dir; defaults to .../target_repo
    app_url: str | None = None           # defaults to "http://localhost:5106" (eShopOnWeb docker compose)
    domain: str | None = None            # defaults to "all"
    target_stack: str | None = None      # e.g. "spring-boot" — forwarded to planning slash commands only
    docs_dir: str | None = None          # defaults to .../new-modernization-sdlc/docs
    max_concurrency: int = 5
```

### Agent working directory

All 7 phases cwd into `target_repo_dir` so every slash command resolves from the
single `target_repo/.claude/commands/` tree. Phases 1, 2, and 4 additionally
receive a `legacy_dir=…` argument in the slash command itself so the command
implementation can read the legacy source via absolute paths.

Discovery (phases 1–5) is target-stack-agnostic. `target_stack` is only consumed
by the planning slash commands (phases 6–7).

## Output layout

```
{docs_dir}/entry-points/
├── ui-features/
│   ├── inventory.{domain}.json
│   └── {feature-key}/
│       ├── metadata.json
│       ├── call-tree.json
│       ├── api-usage.json
│       ├── functional-description.md
│       ├── functional-spec.md
│       ├── technical-plan.md
│       └── screenshots/
│           ├── SCREENSHOTS_COMPLETE
│           └── *.png
└── api-endpoints/
    ├── inventory.{domain}.json
    └── {endpoint-key}/
        ├── metadata.json
        ├── call-tree.json
        ├── functional-description.md
        ├── functional-spec.md
        └── technical-plan.md
```

## Running

With the sibling `../eShopOnWeb` clone up on `docker-compose`:

```bash
uv run python -m awa workflow start awa-discover --input '{}'
```

Override for a different legacy app / target stack:

```bash
uv run python -m awa workflow start awa-discover \
  --input '{"target_dir": "../my-legacy-app", "app_url": "http://localhost:8080", "domain": "billing", "target_stack": "react"}'
```

## Slash command contracts

Each slash command is expected to write its output files itself; the workflow
only provides paths and passes-through the agent's stdout. All commands receive
the legacy code as their working directory.

| Slash command | Inputs | Writes |
| --- | --- | --- |
| `/inventory-ui-features` | `legacy_dir=… domain=… output_path=…` | `inventory.{domain}.json` as `list[UiInventoryItem]` |
| `/analyze-ui-feature` | `key=… legacy_dir=… location=… output_dir=…` | `{output_dir}/metadata.json`, `call-tree.json`, `api-usage.json` (`list[InventoryItem]`) |
| `/take-screenshot-for-ui-feature` | `key=… legacy_dir=… (file=…\|url=…) output_dir=… marker_path=…` | PNGs + `SCREENSHOTS_COMPLETE` marker |
| `/analyze-api-endpoint` | `key=… legacy_dir=… location=… output_dir=…` | `{output_dir}/metadata.json`, `call-tree.json` |
| `/describe-ui-feature` | `key=… feature_dir=…` | `{feature_dir}/functional-description.md` |
| `/describe-api-endpoint` | `key=… endpoint_dir=…` | `{endpoint_dir}/functional-description.md` |
| `/plan-ui-feature` | `key=… [target_stack=…] feature_dir=…` | `{feature_dir}/functional-spec.md`, `technical-plan.md` |
| `/plan-api-endpoint` | `key=… [target_stack=…] endpoint_dir=…` | `{endpoint_dir}/functional-spec.md`, `technical-plan.md` |
