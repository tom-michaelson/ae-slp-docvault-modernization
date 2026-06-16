---
model: opus
---

# Analyze Page Components

Decompose a page into its UI features and the API endpoints they call. Writes a
single `page-analysis.json` that `/develop.generate-page-plan` consumes.

**This command maps a page to its component tree for the angular-java target stack.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `page_key` | Page folder key (must exist under `docs/entry-points/ui-pages/`) |
| `docs_dir` | Absolute path to the docs root (typically `.../new-modernization-sdlc/docs`) |
| `legacy_dir` | Absolute path to the legacy source tree (for reference reads) |
| `output_path` | Absolute path to write `page-analysis.json` |

Example invocation:

```
/develop.analyze-page-components page_key=homepage-catalog-list \
  docs_dir=/.../docs legacy_dir=/.../legacy/eShopOnWeb \
  output_path=/.../docs/entry-points/ui-pages/homepage-catalog-list/page-analysis.json
```

**IMPORTANT:** The `page_key` must match an existing folder under
`{docs_dir}/entry-points/ui-pages/`. All outputs are written inside that folder.

## Input sources

### Discover outputs

1. Page inventory (the Discover workflow populates this per page):
   - `{docs_dir}/entry-points/ui-pages/{page-key}/inventory.json`
2. Per UI feature (for each feature the page references):
   - `{docs_dir}/entry-points/ui-features/{feature-key}/metadata.json`
   - `{docs_dir}/entry-points/ui-features/{feature-key}/api-usage.json`
   - `{docs_dir}/entry-points/ui-features/{feature-key}/functional-spec.md`
3. Per API endpoint:
   - `{docs_dir}/entry-points/api-endpoints/{api-key}/metadata.json`
   - `{docs_dir}/entry-points/api-endpoints/{api-key}/functional-spec.md`

## Item types

This stack produces only two types:

| Type | Meaning |
| --- | --- |
| `ui-feature` | Angular page, panel, form, grid, action |
| `api-endpoint` | Spring Boot REST endpoint |

If the Discover inventory includes items of other types (triggers, batch jobs),
**skip them with a warning**. They're out of scope for angular-java.

## Process

### Step 1 — load the page inventory

Read `{docs_dir}/entry-points/ui-pages/{page-key}/inventory.json`. Expect an
array of UI features that belong to the page.

### Step 2 — expand UI features

For every UI feature key in the inventory:

1. Read `{docs_dir}/entry-points/ui-features/{feature-key}/metadata.json` to
   pick up `name` and any other display attributes.
2. Read `{docs_dir}/entry-points/ui-features/{feature-key}/api-usage.json` to
   find API dependencies. The file is a list of `InventoryItem` objects — use
   each item's `key` as the dependency edge.
3. Resolve `functionalSpecPath` (see below).

### Step 3 — expand API endpoints

For every distinct API key surfaced in step 2:

1. Read `{docs_dir}/entry-points/api-endpoints/{api-key}/metadata.json`.
2. Resolve `functionalSpecPath` to
   `{docs_dir}/entry-points/api-endpoints/{api-key}/functional-spec.md`.
3. Record `usedBy` (list of UI feature keys that call this API).

### Step 4 — detect implementation status

For every component, check the parent directory of its resolved
`functionalSpecPath` for a `.IMPLEMENTED` marker file:

- `.IMPLEMENTED` exists → `status: "completed"`
- Otherwise → `status: "not-started"`

### Step 5 — write `page-analysis.json`

Write to `{output_path}` in the format below.

## Output format

```json
{
  "pageKey": "homepage-catalog-list",
  "domain": "catalog",
  "generatedAt": "2026-04-24T10:00:00Z",
  "summary": {
    "totalUiFeatures": 1,
    "totalApiEndpoints": 1
  },
  "uiFeatures": [
    {
      "key": "homepage-catalog-list",
      "type": "ui-feature",
      "name": "Homepage catalog list",
      "functionalSpecPath": "/abs/.../docs/entry-points/ui-features/homepage-catalog-list/functional-spec.md",
      "dependencies": ["list-catalog-items"],
      "status": "not-started"
    }
  ],
  "apiEndpoints": [
    {
      "key": "list-catalog-items",
      "type": "api-endpoint",
      "name": "List catalog items (paginated, filterable)",
      "functionalSpecPath": "/abs/.../docs/entry-points/api-endpoints/list-catalog-items/functional-spec.md",
      "dependencies": [],
      "usedBy": ["homepage-catalog-list"],
      "status": "not-started"
    }
  ]
}
```

## Resolving `functionalSpecPath`

Must be absolute. Resolution order:

1. Construct the canonical path:
   - UI feature: `{docs_dir}/entry-points/ui-features/{key}/functional-spec.md`
   - API endpoint: `{docs_dir}/entry-points/api-endpoints/{key}/functional-spec.md`
2. Verify the file exists (Read/Glob).
3. If missing, glob `{docs_dir}/entry-points/ui-features/*{key}*/functional-spec.md`
   (or the `api-endpoints` variant); pick the single match, or prefer the folder
   whose name ends with `-{key}`.
4. If still missing, set to `"NOT_FOUND"` and emit a warning with the candidates
   that were tried. The downstream `generate-page-plan` validation will surface
   this.

## Success criteria

- [ ] Page inventory read successfully.
- [ ] Every UI feature in the inventory is in `uiFeatures`.
- [ ] Every API referenced in any `api-usage.json` is in `apiEndpoints` exactly once.
- [ ] Every component has a non-empty `functionalSpecPath` (or `"NOT_FOUND"` with a warning).
- [ ] Components with a `.IMPLEMENTED` marker show `status: "completed"`.
- [ ] `{output_path}` parses as JSON and matches the shape above.

## Error handling

**Page folder missing:**
- Error: `Page folder not found at {docs_dir}/entry-points/ui-pages/{page-key}/`.
- Suggest re-running the discover workflow.

**`inventory.json` missing or empty:**
- Error; suggest running the discover workflow first.

**Unsupported type in inventory:**
- Log a warning, skip the item, continue.

**Missing `api-usage.json` for a feature:**
- Treat as "no API dependencies" and emit a warning.
