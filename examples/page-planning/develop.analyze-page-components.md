# Analyze Page Components

Analyze a page and identify all its components (UI features, APIs, batch jobs, triggers).

**This command builds the complete component tree for a page from Discover workflow outputs.**

## Input Parameters

You will receive:
- **page_key**: The page folder name (e.g., `2046-ba-request`). This is the existing folder under `docs/entry-points/ui-pages/` created by the Discover workflow.
- **domain**: The domain this page belongs to

Example invocation:
```
/develop.analyze-page-components page_key: 2046-ba-request domain: company
```

**IMPORTANT:** The `page_key` must match an existing folder in `docs/entry-points/ui-pages/`. All outputs will be written to this same folder.

## Input Sources

### Primary Sources (from Discover workflow)

1. **Page UI Features Inventory** (read from existing page folder):
   - `docs/entry-points/ui-pages/{page-key}/inventory.json` - List of all UI features for this page (created by Discover)

2. **Per-Feature Analysis** (for each UI feature in this page):
   - `docs/entry-points/ui-features/{menuItemId}-{feature-key}/api-usage.json` - APIs used by this feature
   - `docs/entry-points/ui-features/{menuItemId}-{feature-key}/functional-spec.md` - Feature's functional spec
   - `docs/entry-points/ui-features/{menuItemId}-{feature-key}/metadata.json` - Feature metadata
   - **Note:** `{menuItemId}` is the numeric page ID from the inventory item's `menuItemId` field (e.g., `2087`). The folder name is `{menuItemId}-{feature-key}` (e.g., `2087-infrastructure-company-company-contact-grid`).

3. **API Analysis** (for each API identified):
   - `docs/entry-points/api-endpoints/{api-key}/functional-spec.md` - API's functional spec
   - `docs/entry-points/api-endpoints/{api-key}/database-dependencies.json` - Includes triggers

4. **Batch Jobs**:
   - `docs/entry-points/quartz-batch-jobs/inventory.{domain}.json` - Batch jobs for domain

5. **Database Triggers**:
   - `docs/entry-points/database-triggers/inventory.{domain}.json` - Triggers for domain

## Analysis Steps

### Step 1: Find UI Features for This Page

1. Verify the page folder exists: `docs/entry-points/ui-pages/{page-key}/`
2. Read `docs/entry-points/ui-pages/{page-key}/inventory.json` (this file already exists from Discover)
3. This inventory contains all UI features for this page:
   - The main page itself
   - All sub-features (tabs, grids, forms, modals, menu actions, etc.)

### Step 2: Identify API Dependencies

For each UI feature found:
1. Read `docs/entry-points/ui-features/{menuItemId}-{feature-key}/api-usage.json` (where `menuItemId` comes from the inventory item)
2. Extract `apiDependencies` array
3. For each API dependency:
   - First, try to find the API endpoint folder at `docs/entry-points/api-endpoints/{apiKey}/`
   - If not found, apply **API Key Resolution** (see below)
4. Collect unique, resolved API keys

#### API Key Resolution (Fallback for Mismatched Keys)

If an API key from `api-usage.json` doesn't match any folder in `docs/entry-points/api-endpoints/`:

1. **Check for TBD/auto prefix mismatch:**
   - If key starts with `TBD-`, try replacing with `auto-` (e.g., `TBD-spring-gridservices-load` → `auto-gridservices-load`)
   - Strip the `spring-` part if present (e.g., `TBD-spring-gridservices-load` → `auto-gridservices-load`)

2. **Match by service and method:**
   - Extract the service name and method from the key (e.g., `gridservices` and `load`)
   - Search for folders matching pattern `*-{service}-{method}` or `auto-{service}-{method}`

3. **Update the API key in output:**
   - Use the **resolved key** (the actual folder name) in the output JSON
   - This ensures `functionalSpecPath` points to existing files

### Step 3: Identify Batch Jobs

1. Read `docs/entry-points/quartz-batch-jobs/inventory.{domain}.json` (if exists)
2. Match batch jobs that:
   - Explicitly reference this page's entities
   - Share database tables with this page's APIs
   - Have naming conventions matching the page

### Step 4: Identify Triggers

For each API identified:
1. Read `docs/entry-points/api-endpoints/{api-key}/database-dependencies.json`
2. Extract `triggers` array if present
3. Also check `docs/entry-points/database-triggers/inventory.{domain}.json` for domain-wide triggers

### Step 5: Build Component Tree

Create the component tree with proper dependencies:

**Dependencies Rules:**
- UI features depend on the APIs they call
- APIs are independent (may have inter-API dependencies based on their call trees)
- Batch jobs depend on the APIs they use
- Triggers are independent (fire on database events)

### Step 6: Detect Implementation Status

For each component identified in steps 1-4, check whether it has already been implemented:

1. Determine the component's entry point folder path — use the **parent directory of the already-resolved `functionalSpecPath`** for that component. Do not re-derive the path; use the path resolved in the "Resolving `functionalSpecPath`" section.

2. Check if a `.implemented` marker file exists in that directory

3. If `.implemented` exists:
   - Set the component's `status` to `"completed"`
4. If `.implemented` does not exist:
   - Set the component's `status` to `"not-started"` (this is the default)

## Output Format

Write the component tree to `docs/entry-points/ui-pages/{page-key}/page-analysis.json`:

**Note:** The folder `docs/entry-points/ui-pages/{page-key}/` already exists from the Discover workflow. Write to this existing folder.

```json
{
  "pageKey": "2046-ba-request",
  "domain": "company",
  "generatedAt": "2024-01-15T10:00:00Z",
  "summary": {
    "totalUiFeatures": 5,
    "totalApiEndpoints": 8,
    "totalBatchJobs": 1,
    "totalTriggers": 2
  },
  "uiFeatures": [
    {
      "key": "infrastructure-company-ba-request",
      "type": "ui-feature",
      "name": "BA Request Page",
      "functionalSpecPath": "docs/entry-points/ui-features/2046-infrastructure-company-ba-request/functional-spec.md",
      "dependencies": [
        "get-ba-requests",
        "get-ba-request-by-id"
      ],
      "status": "not-started"
    },
    {
      "key": "infrastructure-company-ba-request-grid",
      "type": "ui-feature",
      "name": "BA Request Grid",
      "functionalSpecPath": "docs/entry-points/ui-features/2046-infrastructure-company-ba-request-grid/functional-spec.md",
      "dependencies": [
        "get-ba-requests",
        "update-ba-request"
      ],
      "status": "not-started"
    }
  ],
  "apiEndpoints": [
    {
      "key": "get-ba-requests",
      "type": "api-endpoint",
      "name": "Get BA Requests",
      "functionalSpecPath": "docs/entry-points/api-endpoints/get-ba-requests/functional-spec.md",
      "dependencies": [],
      "usedBy": ["infrastructure-company-ba-request", "infrastructure-company-ba-request-grid"],
      "status": "not-started"
    },
    {
      "key": "get-ba-request-by-id",
      "type": "api-endpoint",
      "name": "Get BA Request By ID",
      "functionalSpecPath": "docs/entry-points/api-endpoints/get-ba-request-by-id/functional-spec.md",
      "dependencies": [],
      "usedBy": ["infrastructure-company-ba-request"],
      "status": "not-started"
    },
    {
      "key": "update-ba-request",
      "type": "api-endpoint",
      "name": "Update BA Request",
      "functionalSpecPath": "docs/entry-points/api-endpoints/update-ba-request/functional-spec.md",
      "dependencies": ["get-ba-request-by-id"],
      "usedBy": ["infrastructure-company-ba-request-grid"],
      "status": "not-started"
    }
  ],
  "batchJobs": [
    {
      "key": "ba-request-sync-job",
      "type": "batch-job",
      "name": "BA Request Sync Batch Job",
      "functionalSpecPath": "docs/entry-points/quartz-batch-jobs/ba-request-sync-job/functional-spec.md",
      "dependencies": ["get-ba-requests", "update-ba-request"],
      "status": "not-started"
    }
  ],
  "triggers": [
    {
      "key": "ba-request-audit-trigger",
      "type": "trigger",
      "name": "BA Request Audit Trigger",
      "functionalSpecPath": "docs/entry-points/database-triggers/ba-request-audit-trigger/functional-spec.md",
      "dependencies": [],
      "status": "not-started"
    }
  ]
}
```

## Field Descriptions

| Field | Description |
|-------|-------------|
| `key` | Unique identifier for the component |
| `type` | One of: `ui-feature`, `api-endpoint`, `batch-job`, `trigger` |
| `name` | Human-readable name (from metadata or derived from key) |
| `functionalSpecPath` | Relative path to the functional spec from Discover |
| `dependencies` | Keys of other components this one depends on |
| `usedBy` | (APIs only) Keys of UI features that use this API |
| `status` | Implementation status: `"not-started"` or `"completed"` (from `.implemented` marker) |

## Resolving `functionalSpecPath`

**CRITICAL: Every component MUST have a valid `functionalSpecPath`.** The downstream develop workflow uses this path to locate the entry point folder. A value of `"NOT_FOUND"` will cause the workflow to fail. Follow the resolution steps below carefully, including the glob fallback.

### Resolution Algorithm

For each component, resolve its `functionalSpecPath` using these steps **in order**:

**Step A — Construct the expected path:**

| Type | Path Pattern |
|------|-------------|
| UI feature | `docs/entry-points/ui-features/{menuItemId}-{feature-key}/functional-spec.md` |
| API endpoint | `docs/entry-points/api-endpoints/{api-key}/functional-spec.md` |
| Batch job | `docs/entry-points/quartz-batch-jobs/{batch-key}/functional-spec.md` |
| Trigger | `docs/entry-points/database-triggers/{trigger-key}/functional-spec.md` |

For **UI features**, the `menuItemId` comes from:
1. The item's `menuItemId` in the page's `inventory.json` (if not null)
2. If `menuItemId` is null (common for child components like panels, actions), **inherit from the page key** — extract the numeric prefix by splitting the page key on the first `-` (e.g., page key `2122-dor` → menuItemId `2122`)

**Step B — Verify the file exists:**

After constructing the path, **check that `functional-spec.md` actually exists** at that location using Glob or Read.

**Step C — Glob fallback if not found:**

If the constructed path does not exist:
1. Glob for `docs/entry-points/ui-features/*{feature-key}/functional-spec.md`
2. If exactly one match is found, use it
3. If multiple matches, pick the one whose folder starts with the expected menuItemId prefix
4. Apply this same glob fallback for API endpoints, batch jobs, and triggers if their constructed path doesn't exist

**Step D — Only set `"NOT_FOUND"` as last resort:**

If all resolution steps fail (constructed path missing AND glob finds nothing), set `functionalSpecPath` to `"NOT_FOUND"` and log a **warning** that includes the component key and the paths that were tried.

### Examples

- Feature key `nominations-scheduling-dor-main-panel` with `menuItemId: null` on page `2122-dor`:
  - Step A: `menuItemId` is null → inherit `2122` from page key → `docs/entry-points/ui-features/2122-nominations-scheduling-dor-main-panel/functional-spec.md`
  - Step B: Verify file exists → yes → done

- Feature key `infrastructure-company-company-contact-grid` with `menuItemId: 2087`:
  - Step A: `docs/entry-points/ui-features/2087-infrastructure-company-company-contact-grid/functional-spec.md`
  - Step B: Verify file exists → yes → done

## Handling Missing Data

**If an API key doesn't match any endpoint folder:**
1. Apply the API Key Resolution fallback (see Step 2)
2. If resolved, use the resolved key and its functional spec path
3. If still not found after resolution AND glob fallback fails, set `functionalSpecPath` to `"NOT_FOUND"` and log a warning

**If a functional spec doesn't exist at the resolved path:**
- Apply the glob fallback (Step C above)
- Only set `functionalSpecPath` to `"NOT_FOUND"` if glob also fails

**If api-usage.json doesn't exist:**
- Assume the UI feature has no API dependencies
- Log a warning

**If inventory files don't exist:**
- Return an empty array for that component type
- Log a warning

## Success Criteria

- [ ] Page folder exists: `docs/entry-points/ui-pages/{page-key}/`
- [ ] Page inventory file read successfully from `docs/entry-points/ui-pages/{page-key}/inventory.json`
- [ ] API dependencies extracted from api-usage.json files
- [ ] Batch jobs identified (if any)
- [ ] Triggers identified (if any)
- [ ] Dependencies mapped correctly
- [ ] Component tree JSON written to `docs/entry-points/ui-pages/{page-key}/page-analysis.json`
- [ ] Each component checked for `.implemented` marker file
- [ ] Components with `.implemented` marker have status `"completed"`
- [ ] Components without `.implemented` marker have status `"not-started"`

## Error Handling

**Page folder doesn't exist:**
- Report error: "Page folder not found at `docs/entry-points/ui-pages/{page-key}/`"
- Suggest running Discover workflow first
- List available page folders with: `ls docs/entry-points/ui-pages/`

**Missing inventory.json in page folder:**
- Report error and suggest running Discover workflow first

**Invalid page key:**
- Report that page folder doesn't exist
- List available page folders for the domain (filter by domain in folder names or check inventory.json files)

**Circular dependencies (if detected):**
- Report the cycle
- Break the cycle at the least critical point
