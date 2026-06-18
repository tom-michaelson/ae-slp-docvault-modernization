---
model: opus
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --from-stdin
            --log
            --file-pattern "*page-plan.md"
            --contains '# Page Plan'
            --contains '## Overview'
            --contains '## Component Summary'
            --contains '## Implementation Order'
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*page-plan.md"
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*page-plan.md"
            --contains '# Page Plan'
            --contains '## Overview'
            --contains '## Component Summary'
            --contains '## Implementation Order'
---

# Generate Page Plan

Generate the complete page plan from component analysis files.

**This command creates the page plan (JSON and markdown) from page component trees.**

## Input Parameters

You will receive:
- **domain**: The domain to generate the plan for
- **pages**: Comma-separated list of page folder names (e.g., `2046-ba-request,2047-company-maintenance`). These are the existing folders under `docs/entry-points/ui-pages/` created by the Discover workflow.

Example invocation:
```
/develop.generate-page-plan domain: company pages: 2046-ba-request,2047-company-maintenance
```

**IMPORTANT:** Each page in the list must match an existing folder in `docs/entry-points/ui-pages/`. All outputs will be written to the corresponding existing folder.

## Input Sources

For each page in the list:
- `docs/entry-points/ui-pages/{page-key}/page-analysis.json` - Component tree from `/develop.analyze-page-components` (must exist in the page folder)

The page-analysis files contain:
- UI features for the page
- API endpoints used by the page
- Batch jobs related to the page
- Database triggers related to the page
- Dependencies between components

## Implementation Ordering

### Priority Order (Type-Based)

Components are ordered by type priority:

1. **Database Triggers (Priority 1)** - Fire on database events, must exist first
2. **API Endpoints (Priority 2)** - Backend before frontend
3. **Batch Jobs (Priority 3)** - Depend on APIs
4. **UI Features (Priority 4)** - Depend on APIs, implement last

### Dependency Resolution

Within each type:
1. Topological sort ensuring dependencies come before dependents
2. Alphabetical order when no dependency relationship exists
3. Related items grouped together

### Batching Strategy

**Two-Level Batch Hierarchy:**

1. **E2E Batches** - One per layer per page. Each becomes one branch and one PR.
2. **Items** - Individual components within the batch, ordered by dependency.

**E2E Batch Rules:**
- One batch per component type layer (triggers, APIs, batch jobs, UI features)
- All items of the same type within a page belong to one E2E batch
- Dependencies between layers are handled by batch ordering (layer 1 before layer 2)

## Output Files

**Note:** Output files go into each page's folder. When processing multiple pages, create files in each page folder.

### 1. JSON: `docs/entry-points/ui-pages/{page-key}/page-plan.json`

```json
{
  "domain": "company",
  "pages": ["2046-ba-request"],
  "generatedAt": "2024-01-15T12:00:00Z",
  "readyForImplementation": true,
  "status": "not-started",
  "blockingReasons": [],
  "startingBranch": "main",
  "summary": {
    "totalItems": 16,
    "totalE2eBatches": 4,
    "byType": {
      "triggers": 2,
      "apiEndpoints": 8,
      "batchJobs": 1,
      "uiFeatures": 5
    }
  },
  "items": [
    {
      "sequence": 1,
      "componentKey": "ba-request-audit-trigger",
      "componentType": "trigger",
      "pageKey": "2046-ba-request",
      "functionalSpecPath": "docs/entry-points/database-triggers/ba-request-audit-trigger/functional-spec.md",
      "dependencies": [],
      "e2eBatchId": "e2e-2046-ba-request-triggers",
      "status": "not-started"
    }
  ],
  "e2eBatches": [
    {
      "batchId": "e2e-2046-ba-request-triggers",
      "name": "Layer 1: Database Triggers",
      "pageKey": "2046-ba-request",
      "componentKeys": ["ba-request-audit-trigger"],
      "status": "not-started"
    },
    {
      "batchId": "e2e-2046-ba-request-apis",
      "name": "Layer 2: API Endpoints",
      "pageKey": "2046-ba-request",
      "componentKeys": ["get-ba-requests", "get-ba-request-by-id"],
      "status": "not-started"
    },
    {
      "batchId": "e2e-2046-ba-request-batch-jobs",
      "name": "Layer 3: Batch Jobs",
      "pageKey": "2046-ba-request",
      "componentKeys": ["ba-request-sync-job"],
      "status": "not-started"
    },
    {
      "batchId": "e2e-2046-ba-request-ui",
      "name": "Layer 4: UI Features",
      "pageKey": "2046-ba-request",
      "componentKeys": ["infrastructure-company-ba-request-grid"],
      "status": "not-started"
    }
  ]
}
```

### 2. Markdown: `docs/entry-points/ui-pages/{page-key}/page-plan.md`

```markdown
# Page Plan - {domain}

Generated: {ISO 8601 timestamp}

## Overview

| Metric | Value |
|--------|-------|
| Domain | {domain} |
| Total Pages | {count} |
| Total Components | {count} |
| Total E2E Batches | {count} |
| Status | **READY** |

## Component Summary

| Type | Count |
|------|-------|
| Triggers | {count} |
| API Endpoints | {count} |
| Batch Jobs | {count} |
| UI Features | {count} |

---

## E2E Batch Structure

### Page: {page_key}

| E2E Batch | Layer | Items |
|-----------|-------|-------|
| e2e-2046-ba-request-triggers | Layer 1: Database Triggers | ba-request-audit-trigger |
| e2e-2046-ba-request-apis | Layer 2: API Endpoints | get-ba-requests, get-ba-request-by-id |
| e2e-2046-ba-request-ui | Layer 4: UI Features | infrastructure-company-ba-request-grid |

---

## Implementation Order

### Layer 1: Database Triggers (e2e-2046-ba-request-triggers)

| Seq | Component | Page | Dependencies |
|-----|-----------|------|--------------|
| 1 | ba-request-audit-trigger | 2046-ba-request | - |

### Layer 2: API Endpoints (e2e-2046-ba-request-apis)

| Seq | Component | Page | Dependencies |
|-----|-----------|------|--------------|
| 2 | get-ba-requests | 2046-ba-request | - |
| 3 | get-ba-request-by-id | 2046-ba-request | - |

---

## Next Steps

1. Run the Implementation Workflow to generate code
2. Review PRs in batch order
3. Merge batches sequentially
```

## Algorithm

```
1. For each page:
   a. Load docs/entry-points/ui-pages/{page-key}/page-analysis.json
   b. Extract all components for this page
   c. Create E2E batch for this page: "e2e-{page-key}"
   d. Assign priority: triggers=1, apis=2, batch=3, ui=4
   e. Topological sort within each priority level
   f. Assign sequence numbers 1 to N
   g. Create one E2E batch per layer (triggers, APIs, batch jobs, UI features)
   h. Assign e2eBatchId to each item matching its layer's E2E batch
   i. Write page-plan.json to docs/entry-points/ui-pages/{page-key}/
   j. Write page-plan.md to docs/entry-points/ui-pages/{page-key}/
2. If processing multiple pages, repeat for each page
```

## E2E Batch ID Convention

For each layer within a page, create an E2E batch with:
- `batchId`: `"e2e-{page-key}-{layer}"` where layer is one of: `triggers`, `apis`, `batch-jobs`, `ui` (e.g., `"e2e-2046-ba-request-apis"`)
- `name`: Human-readable layer name (e.g., `"Layer 2: API Endpoints"`)
- `pageKey`: The page folder name (e.g., `"2046-ba-request"`)
- `componentKeys`: Array of all component keys in this layer
- `status`: `"not-started"` initially (or `"completed"` if all components have `.implemented` markers)

Only create E2E batches for layers that have components. If a page has no batch jobs, omit the batch-jobs E2E batch.

## Item Fields

Each item must include:
- `sequence`: Global sequence number
- `componentKey`: Entry point key
- `componentType`: Type (api-endpoint, ui-feature, batch-job, trigger)
- `pageKey`: Page identifier
- `functionalSpecPath`: Path to functional spec
- `dependencies`: Array of dependent component keys
- `e2eBatchId`: E2E batch ID for this item's layer
- `status`: `"not-started"` initially (or `"completed"` if component has `.implemented` marker)

## Success Criteria

- [ ] All page-analysis files found and loaded from `docs/entry-points/ui-pages/{page-key}/`
- [ ] Components merged and deduplicated
- [ ] Dependencies resolved correctly
- [ ] Topological sort successful
- [ ] Sequence numbers assigned
- [ ] E2E batches created (one per layer per page, only for layers with components)
- [ ] Items include e2eBatchId referencing their layer's E2E batch
- [ ] Component statuses from page-analysis.json preserved in item statuses
- [ ] For each page: `docs/entry-points/ui-pages/{page-key}/page-plan.json` written
- [ ] For each page: `docs/entry-points/ui-pages/{page-key}/page-plan.md` written

## Error Handling

**Page folder doesn't exist:**
- Report error: "Page folder not found at `docs/entry-points/ui-pages/{page-key}/`"
- Suggest checking the page key against existing folders: `ls docs/entry-points/ui-pages/`

**Missing page-analysis.json file:**
- Report which page is missing the analysis file
- Suggest running `/develop.analyze-page-components` first for that page

**Unmet dependency:**
- Report component and missing dependency
- Continue with best-effort ordering

**Cycle detected:**
- Report the cycle
- Break at least critical point
- Continue with ordering
