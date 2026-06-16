# Generic Develop Workflow (`awa-develop`)

Takes the outputs of [`awa-discover`](../discover/README.md) and implements them
into the Angular + Spring Boot target repo. Single workflow, three phases, no
patterns and no automatic PR creation.

## Phases

| # | Phase | Applies to | Outputs |
| - | ----- | ---------- | ------- |
| 0 | Branch setup | Workflow start | `feature/{domain}-develop-{suffix}` |
| 1 | Page planning | Per page (bounded concurrent) | `page-analysis.json`, `page-plan.json`, `page-plan.md`, `.VALIDATED` marker |
| 2 | Implementation | Per page → per batch → per item | Source + tests under `target_repo/source`; batch branches pushed |

Phase 2 per item runs a 9-step pipeline driven by the slash commands documented
in [`target_repo/.claude/commands/SPEC.md`](../../../../../target_repo/.claude/commands/SPEC.md):

1. `/research-item`
2. `/discover-entity-relationships`
3. `/plan-{api-endpoint,ui-feature}`
4. `/review-plan-{api,ui}`
5. `/create-task-list-{api,ui}`
6. `/implement{,-ui}` + `/review-{,-ui-}implementation` — retry loop, max 5
7. `/validate-code-against-functional-spec` — retry loop, max 5
8. `/generate-{api,ui}-unit-tests`
9. Write `.IMPLEMENTED` marker

After every item in a batch is implemented, the batch runs verification
(`./gradlew clean build` + `./gradlew test`). Failures loop with
`/fix-build-errors` or `/fix-test-failures`, up to 5 attempts. Pass or fail, the
batch branch is committed + pushed so the human can inspect it and open the PR.

## Inputs

```python
class DevelopWorkflowInput:
    pages: list[str]                 # page keys from Discover
    domain: str | None = None        # defaults to "all"
    target_stack: str | None = None  # defaults to "angular-java"
    target_repo_dir: str | None = None  # defaults to .../target_repo
    docs_dir: str | None = None      # defaults to .../docs
    legacy_dir: str | None = None    # defaults to "../eShopOnWeb"
    starting_branch: str | None = None  # defaults to "main"
    max_concurrency: int = 5
```

## Idempotency

Every stage short-circuits when its artifact already exists:

| Stage | Marker |
| --- | --- |
| Branch setup | `ensure_on_branch` (git is the state) |
| Analyze components | `page-analysis.json` |
| Generate page plan | `page-plan.json` |
| Validate plan | `page-plan.VALIDATED` |
| Batch start / resume | In-progress plan file + `git show-ref` on branch |
| Research | `research.md` |
| Entity relationships | `relationship-discovery.json` |
| Plan | `implementation-plan.md` |
| Plan review | `plan-review.md` |
| Task list | `task-list.md` |
| Implement + review | `implementation-review-result.json` with `validated:true` |
| AC validation | `ac-validation-result.json` with `validated:true` |
| Unit tests | `test-tracking.json` |
| Item done | `.IMPLEMENTED` |
| Batch verify | `.VERIFIED` |
| Batch push | git remote ref |

## Branch strategy

```
main
  └─ feature/{domain}-develop-{suffix}
       ├─ feature/{domain}-{page1}-progress     (state only, no PR)
       │    ├─ feature/{domain}-{page1}-batch1  (pushed — open PR by hand)
       │    └─ feature/{domain}-{page1}-batch2  (pushed — open PR by hand)
       └─ feature/{domain}-{page2}-progress
            └─ feature/{domain}-{page2}-batch1  (pushed)
```

Each batch branch targets the previous batch branch in the stack (or the
develop branch for batch 1), matching the stacked-PR pattern — but the PR
itself is opened manually.

## Running

```bash
uv run python -m awa workflow start awa-develop --input '{
  "pages": ["0001-catalog-list-page"],
  "domain": "catalog"
}'
```

## Files

```
awa/cookbook/recipes/workflows/develop/
├── __init__.py
├── README.md
├── develop_workflow.py
├── utils.py
├── models/
│   ├── workflow_input.py
│   ├── page_plan.py
│   └── page_result.py
└── child_workflows/
    ├── analyze_page_components_workflow.py
    ├── generate_page_plan_workflow.py
    ├── implement_item_workflow.py
    └── verify_workflow.py
```
