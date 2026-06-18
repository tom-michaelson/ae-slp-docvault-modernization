---
model: opus
---

# Generate Page Plan

Produce the implementation plan for a single page: typed items ordered by
dependency, grouped into E2E batches. One batch becomes one stacked branch that
the `awa-develop` workflow commits and pushes (PR is opened by a human).

**This command creates `page-plan.{page-key}.json` and `page-plan.{page-key}.md`
in the page's folder.**

## Input parameters

Expected when invoked:

| Arg | Purpose |
| --- | --- |
| `page_key` | Page folder key (must exist under `docs/entry-points/ui-pages/`) |
| `domain` | Domain label used in the plan metadata |
| `legacy_dir` | Absolute path to the legacy code directory (for reference reads) |
| `page_analysis_path` | Absolute path to the upstream `page-analysis.json` |
| `output_json_path` | Absolute path to write `page-plan.json` |
| `output_md_path` | Absolute path to write `page-plan.md` |
| `target_stack` *(optional)* | Defaults to `angular-java` |

Example invocation:

```
/develop.generate-page-plan page_key=homepage-catalog-list domain=catalog \
  legacy_dir=/.../legacy/eShopOnWeb \
  page_analysis_path=/.../docs/entry-points/ui-pages/homepage-catalog-list/page-analysis.json \
  output_json_path=/.../docs/entry-points/ui-pages/homepage-catalog-list/page-plan.json \
  output_md_path=/.../docs/entry-points/ui-pages/homepage-catalog-list/page-plan.md
```

## Input sources

- `{page_analysis_path}` — component tree from `/develop.analyze-page-components`.
  Contains the page's UI features, API endpoints, and dependencies.
- Entry-point folders referenced by the analysis:
  - UI features: `docs/entry-points/ui-features/{key}/{metadata.json,functional-spec.md}`
  - API endpoints: `docs/entry-points/api-endpoints/{key}/{metadata.json,functional-spec.md}`

If any `functional-spec.md` referenced by the plan is missing the plan MUST
still be written, but the workflow's inline validation will flag it.

## Item types

Our target stack is **Angular + Spring Boot** only. Two item types:

| Priority | Type | Rationale |
| --- | --- | --- |
| 1 | `api-endpoint` | Backend first — UI features depend on endpoints |
| 2 | `ui-feature` | Implement after the APIs they call |

(No `trigger` / `batch-job` types — out of scope for this workflow.)

## Dependency resolution

Within each priority tier:

1. Topological sort so dependencies come before dependents.
2. Alphabetical order on `key` when no dependency relationship exists.
3. Cycles broken at the least-critical edge; log the break.

Cross-tier dependencies (a `ui-feature` depending on an `api-endpoint`) are
enforced by tier ordering — Layer 1 completes before Layer 2 starts.

## Batching strategy

One **E2E batch per tier per page** (so up to 2 batches per page):

| `batchId` | Name | Contains |
| --- | --- | --- |
| `e2e-{page_key}-apis` | "Layer 1: API Endpoints" | All `api-endpoint` items for the page |
| `e2e-{page_key}-ui` | "Layer 2: UI Features" | All `ui-feature` items for the page |

Omit a batch if the tier has zero items.

## Output files

### 1. JSON — `{output_json_path}`

Must match the `PagePlan` pydantic model the workflow reads. Items are nested
inside their batch (no separate top-level `items` array).

```json
{
  "pageKey": "homepage-catalog-list",
  "domain": "catalog",
  "batches": [
    {
      "batchId": "e2e-homepage-catalog-list-apis",
      "name": "Layer 1: API Endpoints",
      "items": [
        {
          "key": "list-catalog-items",
          "type": "api-endpoint",
          "functionalSpecPath": "/abs/.../docs/entry-points/api-endpoints/list-catalog-items/functional-spec.md",
          "dependencies": []
        }
      ],
      "branchName": null,
      "pushed": false,
      "completed": false
    },
    {
      "batchId": "e2e-homepage-catalog-list-ui",
      "name": "Layer 2: UI Features",
      "items": [
        {
          "key": "homepage-catalog-list",
          "type": "ui-feature",
          "functionalSpecPath": "/abs/.../docs/entry-points/ui-features/homepage-catalog-list/functional-spec.md",
          "dependencies": ["list-catalog-items"]
        }
      ],
      "branchName": null,
      "pushed": false,
      "completed": false
    }
  ]
}
```

Rules:

- `pageKey` MUST equal the input `page_key`.
- `domain` MUST equal the input `domain`.
- `functionalSpecPath` MUST be absolute.
- `dependencies` lists other items' `key`s from the **same page plan** (items
  from other pages belong in their own plan and are resolved via batch stacking
  across pages at workflow level).
- `branchName`, `pushed`, `completed` are mutable state — always emit
  `null/false/false` here; the workflow owns them after this point.

### 2. Markdown — `{output_md_path}`

Human-readable twin of the JSON. Must contain these exact H1/H2 headings
(validators look for them):

```markdown
# Page Plan

Generated: {ISO 8601 timestamp}

## Overview

| Metric | Value |
|--------|-------|
| Page | {page_key} |
| Domain | {domain} |
| Target stack | {target_stack} |
| Total items | {count} |
| Total batches | {count} |

## Component Summary

| Type | Count |
|------|-------|
| API Endpoints | {count} |
| UI Features | {count} |

## Implementation Order

### Layer 1: API Endpoints ({batchId})

| Seq | Item | Dependencies |
|-----|------|--------------|
| 1 | list-catalog-items | — |

### Layer 2: UI Features ({batchId})

| Seq | Item | Dependencies |
|-----|------|--------------|
| 2 | homepage-catalog-list | list-catalog-items |

## Next Steps

Run `awa-develop` — it reads this plan, implements each item, commits the
batch branch, and pushes it. Open the PRs manually from the pushed branches.
```

## Algorithm

```
1. Load page_analysis_path as JSON.
2. Extract all items; classify each as "api-endpoint" or "ui-feature".
   - If an analysis item has an unsupported type (trigger/batch-job/etc), log a warning and skip it.
3. Validate that each item's functionalSpecPath exists on disk.
   - If missing, include the item anyway but flag in notes so downstream review catches it.
4. Assign priority: api-endpoint=1, ui-feature=2.
5. Within each priority tier, topologically sort by dependencies.
   - Tie-break alphabetically on key.
   - On cycle: break at the lexicographically-latest edge and log it.
6. Assign global `sequence` numbers 1..N in final order (for the markdown output only —
   the JSON doesn't require sequence; it orders by batch + item position).
7. Group items into E2E batches (one per tier). Skip empty tiers.
8. Write page-plan.json (matches PagePlan pydantic model — see above).
9. Write page-plan.md (matches the template above).
```

## Success criteria

- [ ] `page_analysis_path` loaded successfully.
- [ ] Every item classified as `api-endpoint` or `ui-feature` (others skipped with a warning).
- [ ] Dependencies topologically sorted, cycles broken.
- [ ] At least one E2E batch created.
- [ ] `{output_json_path}` exists, parses as JSON, matches the `PagePlan` shape.
- [ ] `{output_md_path}` exists and contains headings `# Page Plan`, `## Overview`, `## Component Summary`, `## Implementation Order`.

## Error handling

**`page_analysis_path` missing or empty:**
- Report the expected path.
- Suggest running `/develop.analyze-page-components page_key={page_key}` first.

**Unsupported item type (trigger / batch-job / other):**
- Log a warning: `"Item {key} has unsupported type {type}; skipping for angular-java stack"`.
- Continue — the plan still covers supported items.

**Missing `functional-spec.md` for an included item:**
- Include the item; record a note: `"functional-spec.md missing at {path}"`.
- The workflow's `ValidatePagePlan` step will raise on this.

**Cycle between items:**
- Log: `"Cycle detected: {a} -> {b} -> ... -> {a}. Breaking at edge {b}->{a}"`.
- Continue — the plan is still produced; downstream humans review.
