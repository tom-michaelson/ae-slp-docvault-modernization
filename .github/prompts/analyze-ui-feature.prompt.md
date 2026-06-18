# Analyze UI Feature

You are tasked with producing a detailed analysis of a single UI feature from the legacy React/Node.js application. The output feeds a modernization effort targeting **Angular 19 + .NET** — every artifact you write must contain enough technical detail for a .NET/Angular developer to re-implement the feature in that stack without consulting the original source.

This is a **discover-phase** command. It reads the legacy React/Node.js source and writes structured artifacts to `docs/entry-points/ui-features/{feature_key}/`.

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
feature_key=<key>  inventory_path=<abs-path>  source_root=<abs-path>
```

| Argument | Description |
|---|---|
| `feature_key` | The `key` value from the inventory entry (e.g., `basket-view-page`) |
| `inventory_path` | Absolute path to the `inventory.json` file that contains this feature |
| `source_root` | Absolute path to the React/Node.js source root (e.g., `.../target_repo/source`) |

**Examples:**

```
feature_key=document-list-page
inventory_path=/abs/path/docs/entry-points/ui-pages/documents/inventory.json
source_root=/abs/path/target_repo/source
```

```
feature_key=document-upload-panel
inventory_path=/abs/path/docs/entry-points/ui-pages/documents/inventory.json
source_root=/abs/path/target_repo/source
```

```
feature_key=document-detail-view
inventory_path=/abs/path/docs/entry-points/ui-pages/document-detail/inventory.json
source_root=/abs/path/target_repo/source
```

---

## Output

All files are written to:

```
docs/entry-points/ui-features/{feature_key}/
├── metadata.json
├── functional-spec.md
├── call-tree.json
└── database-dependencies.json
```

### `metadata.json` — filled-in example

```json
{
  "key": "document-list-page",
  "name": "Document list page",
  "type": "ui-feature",
  "elementType": "ui-page",
  "uri": "/documents",
  "location": "src/pages/DocumentList.tsx",
  "logic": "src/hooks/useDocuments.ts",
  "domain": "documents",
  "notes": [
    "Fetches documents on mount via useDocuments hook; re-fetches when filter state changes.",
    "Authenticated users see only their own documents; admins see all.",
    "Pagination state is managed in component state and reflected in the API query string."
  ]
}
```

### `functional-spec.md` — filled-in example

```markdown
# Functional spec — Document list page

**Key:** `document-list-page`
**URL:** `GET /documents`
**Legacy source:** `src/pages/DocumentList.tsx` + `src/hooks/useDocuments.ts`

## Purpose

Displays a paginated, filterable list of documents the authenticated user has access to,
and provides entry points for uploading new documents and viewing document details.

## Functional behavior

### On Mount — load documents

1. Calls `useDocuments({ page: 1, filter: '' })` hook on component mount.
2. Hook calls `documentService.getDocuments(params)` which issues `GET /api/documents?page=1`.
3. Renders document rows into the list table; shows loading spinner while fetching.

### On Filter Change — search/filter

1. User types in search input; debounced `handleFilterChange` fires after 300 ms.
2. Calls `documentService.getDocuments({ filter, page: 1 })`.
3. Replaces list content with filtered results.

## Acceptance criteria (Gherkin)

\`\`\`
Scenario: Authenticated user sees their document list on load
  Given the user is authenticated
  When they navigate to "/documents"
  Then the document list loads and displays their documents
  And the total count is shown in the header

Scenario: Empty state when no documents exist
  Given the user has no documents
  When they navigate to "/documents"
  Then the empty-state message "No documents found." is displayed

Scenario: Unauthenticated user is redirected to login
  Given the user is not authenticated
  When they navigate to "/documents"
  Then they are redirected to "/login"
\`\`\`

## UI elements

| Element | Kind | Source ref |
| --- | --- | --- |
| Page title | text | `DocumentList.tsx:12` |
| Search/filter input | input[text] | `DocumentList.tsx:34` |
| Document rows | loop over `documents` | `DocumentList.tsx:55-70` |
| Upload button | link to `/documents/upload` | `DocumentList.tsx:22` |
| Pagination controls | component `<Pagination>` | `DocumentList.tsx:80` |
| Empty-state message | conditional text | `DocumentList.tsx:50` |
| Loading spinner | conditional component | `DocumentList.tsx:45` |
```

### `call-tree.json` — filled-in example

```json
{
  "handlers": [
    {
      "entryPoint": {
        "method": "DocumentList.useEffect[onMount]",
        "file": "src/pages/DocumentList.tsx",
        "line": 28
      },
      "calls": [
        {
          "method": "useDocuments",
          "file": "src/hooks/useDocuments.ts",
          "line": 12,
          "calls": [
            {
              "method": "documentService.getDocuments",
              "file": "src/services/documentService.ts",
              "line": 8,
              "calls": [
                {
                  "method": "apiClient.get",
                  "file": "src/api/apiClient.ts",
                  "line": 15,
                  "db": {"table": "Documents", "op": "select"}
                }
              ]
            }
          ]
        }
      ]
    },
    {
      "entryPoint": {
        "method": "DocumentList.handleFilterChange",
        "file": "src/pages/DocumentList.tsx",
        "line": 42
      },
      "calls": [
        {
          "method": "documentService.getDocuments",
          "file": "src/services/documentService.ts",
          "line": 8,
          "calls": [
            {
              "method": "apiClient.get",
              "file": "src/api/apiClient.ts",
              "line": 15,
              "db": {"table": "Documents", "op": "select"}
            }
          ]
        }
      ]
    }
  ]
}
```

For components with a single interaction (no POST), use `"entryPoint"` + `"calls"` at the top level (no `"handlers"` array):

```json
{
  "entryPoint": {
    "method": "DocumentDetail.useEffect[onMount]",
    "file": "src/pages/DocumentDetail.tsx",
    "line": 18
  },
  "calls": [...]
}
```

### `database-dependencies.json` — filled-in example

```json
[
  {
    "type": "table",
    "name": "Documents",
    "key": "documents",
    "operations": ["select"],
    "columns": ["id", "title", "ownerId", "createdAt", "updatedAt", "status"],
    "locations": [
      "src/db/migrations/20230101_create_documents.js",
      "src/models/Document.js",
      "src/services/documentService.ts"
    ],
    "notes": [
      "Queried by ownerId for regular users; no ownerId filter for admin role.",
      "Supports full-text search on title via the filter query parameter."
    ]
  }
]
```

---

## Field Rules

### metadata.json

| Field | Rule |
|---|---|
| `key` | Copied verbatim from the matching inventory entry |
| `name` | Copied verbatim from the inventory entry |
| `type` | Always `"ui-feature"` |
| `elementType` | Copied from inventory entry (`ui-page`, `ui-panel`, etc.) |
| `uri` | The HTTP path. For React page components derive from React Router `<Route path>` or file-based routing convention. |
| `location` | Relative to `source_root`. The primary `.tsx` or `.jsx` component file for the feature. |
| `logic` | The custom hook (`.ts`) or service file that contains the data-fetching and business logic, if separate from the component file. Omit if logic is co-located in the component. |
| `domain` | Copied from inventory entry |
| `notes` | 2–4 factual strings that would not be obvious from the file name alone. Focus on non-obvious behaviors (cookie handling, dual-path POST handlers, anonymous vs authenticated routing, etc.) |

### functional-spec.md

| Section | Rule |
|---|---|
| **Purpose** | 2–3 sentences: what the user does here, why it matters in the shopping flow |
| **Functional behavior** | One sub-section per user interaction or data-fetch lifecycle event (e.g., `### On Mount`, `### On Submit`, `### On Filter Change`). Numbered steps. Reference real function/hook names. |
| **Acceptance criteria** | Gherkin `Scenario:` blocks. Minimum one per handler. Cover the happy path + at least one edge case (empty state, validation failure, auth gate). |
| **UI elements** | A table with columns: Element, Kind (text/link/img/form/loop/partial), Source ref (`.tsx:N` or `.jsx:N`). List every visible element that has user-facing behaviour. Omit purely structural wrapper divs. |
| **Out of scope** | Optional section. Use it when adjacent features (e.g., site header basket count) are visible in the same template but belong to a different feature key. |

### call-tree.json

| Field | Rule |
|---|---|
| `method` | Module-path + function name (e.g., `services/documentService.getDocuments`) |
| `file` | Relative to `source_root` |
| `line` | Integer. Use the line where the method is defined (not the call site). Omit if line cannot be determined. |
| `db` | Object `{"table": "TableName", "op": "select\|insert\|update\|delete\|select count"}`. Use an array when a single call performs multiple ops. |
| `notes` | Optional string — only for non-obvious conditional logic (e.g., "Only when no basket exists"). |
| `reads` / `writes` | Optional arrays for cookie or session access. Document HTTP context side effects that won't be obvious from the method signature. |

Trace calls until you reach either:
- A `db` node (repository call hitting a table), or
- A leaf method with no further calls into application code (utility/external service)

### database-dependencies.json

| Field | Rule |
|---|---|
| `key` | Lowercase kebab-case version of `name` (e.g., `"BasketItems"` → `"basket-items"`) |
| `operations` | Array subset of `["select", "insert", "update", "delete", "select count"]`. Order: select before mutate. |
| `columns` | Columns actually read or written by this feature. Not all columns in the table — only those touched. |
| `locations` | Files where this table is accessed: migration defining it, specification/repository accessing it, entity class. |
| `notes` | 1–2 sentences per entry. Focus on *how* this feature uses the table (e.g., "Rows deleted lazily via Basket.RemoveEmptyItems when quantity reaches zero"). |

---

## Exclusion Criteria

Do NOT add entries to `database-dependencies.json` for:
- Tables used by shared auth middleware or global layout components unless the feature itself queries them
- Tables touched only by other unrelated features referenced from this page

Do NOT add nodes to `call-tree.json` for:
- ORM internals (e.g., Prisma `$connect`, Sequelize `sync`, Mongoose middleware)
- Module resolution / dependency injection container internals
- React rendering internals (`setState`, `render`, `reconciler`)

Do NOT list UI elements in `functional-spec.md` for:
- Shared layout/shell components (`AppShell`, `NavBar`, `Footer`, global `<Header>`)
- Structural wrapper divs with no user-facing behaviour
- SEO `<meta>` tags

---

## Discovery Process

### Phase 1: Locate the Feature in Inventory

1. Read `inventory_path` — it is a JSON array of inventory entries.
2. Find the entry whose `"key"` matches `feature_key`. If not found, stop and report the error.
3. Extract: `name`, `elementType`, `location`, `uri`, `domain`, `notes` from the entry.
4. Determine the **page type** from `location`:
   - Path under `src/pages/` or `src/views/` with `.tsx`/`.jsx` extension → **React Page Component** (maps directly to a route)
   - Path under `src/components/` or `src/features/` with `.tsx`/`.jsx` extension → **React Feature Component** (significant sub-component, not a full page)
   - Component that imports from Redux (`useSelector`, `useDispatch`), Context API, or a data-fetching hook as its primary data source → **React Container Component**

**Output:** Populated `metadata.json` — write this file immediately before continuing.

---

### Phase 2: Read Source Files

#### React Page Component (`*.tsx` / `*.jsx` mapped to a route)

1. Read `{source_root}/{location}` — the React component file.
2. If a companion hook file (`use*.ts`) exists (referenced in `logic` field), read it too.
3. Identify all `useEffect` calls, event handlers (`handle*`, `on*`), and state declarations (`useState`, `useReducer`).
4. Identify all imported service modules and the functions called on them.
5. For each child component imported and rendered in JSX, read that component file from `src/components/` or adjacent folder (1 level deep).
6. Note every form `onSubmit`, button `onClick`, input `onChange`, and link `href`/`to` prop.

#### React Feature Component (`*.tsx` / `*.jsx` as a sub-component)

1. Read `{source_root}/{location}` — the React component file.
2. Identify `props` interface/type — note any callback props (`on*`) that delegate actions to a parent.
3. Identify `useEffect` hooks, local state, and any directly imported services or hooks.
4. Follow child component imports one level deep.

#### React Container Component (uses Redux / Context / data hooks)

1. Read `{source_root}/{location}` — the container component file.
2. Identify `useSelector` / `useDispatch` calls or `useContext` — note the slice/context name.
3. Read the relevant Redux slice or context file to understand dispatch actions and selectors.
4. Identify `useQuery` / `useMutation` (React Query) or similar data-fetching hooks.
5. Identify `[Authorize]`-equivalent route guard usage (e.g., `<ProtectedRoute>`, `useAuth` hook, redirect in `useEffect`).

---

### Phase 3: Trace the Call Tree

For each handler method identified in Phase 2:

1. List every service method or hook called directly from the handler.
2. For each service method, read the service implementation file (search `src/services/` and `src/api/`).
3. For each ORM/API client call, record the model or endpoint and the DB table it targets.
4. Follow nested service/hook calls up to 3 levels deep, stopping at a `db` node or a leaf.
5. Record cookie and session reads/writes encountered along the way.

**Finding files:** Service implementations live in `src/services/` or `src/api/`. Hook implementations live in `src/hooks/`. ORM model/entity classes live in `src/models/` or `src/db/models/`.

**DB table determination:** The service function name or ORM model name usually implies the table (e.g., `documentService.getDocuments` + `Document` model → `Documents` table). Confirm by checking the model definition or schema file.

**Call tree JSON template per handler:**

```json
{
  "entryPoint": {
    "method": "{ComponentName}.{handlerOrLifecycle}",
    "file": "{location relative to source_root}",
    "line": {line number}
  },
  "calls": [
    {
      "method": "{hookName or serviceName}.{functionName}",
      "file": "{hook or service file}",
      "line": {line},
      "calls": [
        {
          "method": "{apiClient or ORM method}",
          "file": "{api client or model file}",
          "line": {line},
          "db": {"table": "{TableName}", "op": "{op}"}
        }
      ]
    }
  ]
}
```

For pages with multiple handlers, wrap all handler objects in a `"handlers"` array.

---

### Phase 4: Identify Database Dependencies

From the completed call tree:

1. Collect every distinct `db.table` value across all handlers.
2. For each table:
   a. Collect all distinct `op` values from its nodes → `operations` array.
   b. Find the entity class for this table in `src/models/` or `src/db/models/` — extract the property names that are read or mutated by this feature → `columns` array.
   c. Collect all file paths where this table appears in the call tree → `locations` array. Add the migration file defining the table schema if you can identify it from `src/db/migrations/`.
   d. Write 1–2 factual sentences about *how* this feature uses the table → `notes` array.

**DB dependency JSON template:**

```json
{
  "type": "table",
  "name": "{PascalCase table name}",
  "key": "{kebab-case table name}",
  "operations": ["{op1}", "{op2}"],
  "columns": ["{Col1}", "{Col2}"],
  "locations": ["{file1}", "{file2}"],
  "notes": ["{factual note about usage}"]
}
```

---

### Phase 5: Compose the Functional Spec

Using the source you have read, produce `functional-spec.md` with the following sections:

**Header block:**
```
# Functional spec — {name}

**Key:** `{feature_key}`
**URL:** `{uri}` (list all HTTP methods if more than one handler)
**Legacy source:** `{location}` + `{codeBehind if present}`
```

**Purpose:** 2–3 sentences describing the user goal served by this page.

**Functional behavior:** One sub-section per user interaction or data-fetch lifecycle event (`### On Mount`, `### On Submit`, etc.). Numbered steps. Reference real function/hook names. If the handler redirects, name the destination. If it checks auth, describe that logic explicitly.

**Acceptance criteria:** Gherkin `Scenario:` blocks. Rules:
- At minimum: one happy path scenario per handler.
- Always include: the empty-state scenario if the page shows a list.
- Always include: the auth/redirect scenario if a route guard or `useAuth` redirect is present.
- Always include: the error/invalid-input scenario if the page accepts a POST.

**UI elements table:** Columns — Element | Kind | Source ref. Include:
- All form inputs and submit buttons
- All navigation links with specific destinations
- All loops rendering lists of items
- All conditionally rendered blocks (ternary expressions, `&&` short-circuit, or named boolean flags in JSX)
- All child components imported and rendered by name

**Out of scope** (optional): List features visible in the same template that belong to other feature keys (e.g., the site-wide header basket count, the shared navigation rail).

---

## Implementation Workflow

### Step 1: Parse Parameters
Read `feature_key`, `inventory_path`, `source_root` from `{{PROMPT}}`.

### Step 2: Locate Feature Entry
Read `inventory_path` (JSON array). Find entry matching `feature_key`. If missing, report error and stop.

### Step 3: Write metadata.json
Construct from the inventory entry. Write to `docs/entry-points/ui-features/{feature_key}/metadata.json` — create the folder if needed, overwrite if present.

### Step 4: Read Source Files
Based on page type detected from `location`:
- React Page Component → read `.tsx`/`.jsx` + companion hook (`use*.ts`) + imported child components (1 level)
- React Feature Component → read `.tsx`/`.jsx` + props interface + child components (1 level)
- React Container Component → read `.tsx`/`.jsx` + Redux slice or context + data-fetching hooks

### Step 5: Trace Call Tree
Follow handler methods → services → repositories → DB. Build the call tree structure in memory.

### Step 6: Write call-tree.json
Write to `docs/entry-points/ui-features/{feature_key}/call-tree.json` — overwrite if present.

### Step 7: Identify DB Dependencies
From the call tree, collect all tables, their operations, columns, and locations.

### Step 8: Write database-dependencies.json
Write to `docs/entry-points/ui-features/{feature_key}/database-dependencies.json` — overwrite if present.

### Step 9: Write functional-spec.md
Compose all sections (Purpose, Functional behavior, Gherkin, UI elements). Write to `docs/entry-points/ui-features/{feature_key}/functional-spec.md` — overwrite if present.

### Step 10: Report Summary
Output a brief summary:
```
Feature key:    {feature_key}
Page type:      {React Page Component | React Feature Component | React Container Component}
Handlers:       {list, e.g. useEffect[onMount], handleFilterChange, handleSubmit}
DB tables:      {list, e.g. Baskets, BasketItems, Catalog}
Gherkin blocks: {count}
UI elements:    {count}
Output folder:  docs/entry-points/ui-features/{feature_key}/
Files written:  metadata.json, call-tree.json, database-dependencies.json, functional-spec.md
```

---

## Worked Examples

### Example 1: React Page Component with multiple interactions — `document-list-page`

**Input:**
```
feature_key=document-list-page
inventory_path=/path/docs/entry-points/ui-pages/documents/inventory.json
source_root=/path/target_repo/source
```

**Files read:**
- `src/pages/DocumentList.tsx`
- `src/hooks/useDocuments.ts`
- `src/services/documentService.ts`
- `src/api/apiClient.ts`
- `src/models/Document.js`
- `src/components/Pagination.tsx`
- `src/components/DocumentRow.tsx`

**call-tree.json handlers:** `useEffect[onMount]`, `handleFilterChange`, `handlePageChange`
**database-dependencies.json tables:** `Documents` (select, select count)
**Gherkin scenarios:** 4 (authenticated load, empty state, filter search, unauthenticated redirect)
**UI elements:** 7 (page title, search input, document rows loop, upload button, pagination, empty-state message, loading spinner)

---
### Example 2: React Feature Component — `document-upload-panel`

**Input:**
```
feature_key=document-upload-panel
inventory_path=/path/docs/entry-points/ui-pages/documents/inventory.json
source_root=/path/target_repo/source
```

**Files read:**
- `src/components/DocumentUploadPanel.tsx`
- `src/hooks/useUpload.ts`
- `src/services/documentService.ts`

**call-tree.json:** Single `handleUploadSubmit` handler tree calling `documentService.uploadDocument` → `apiClient.post` → `db: {table: "Documents", op: "insert"}`
**database-dependencies.json tables:** `Documents` (insert), `DocumentVersions` (insert)
**Gherkin scenarios:** 3 (successful upload, file-type validation failure, file-size limit exceeded)
**UI elements:** 5 (file drop zone, file type hint text, upload progress bar, submit button, error message)

**Note on child components:** `<FileDropZone>` renders the drag-and-drop target. It emits an `onFilesSelected` callback — this belongs to the `document-upload-panel` feature. Document the element row but note the component boundary.

---
### Example 3: React Container Component — `document-detail-view`

**Input:**
```
feature_key=document-detail-view
inventory_path=/path/docs/entry-points/ui-pages/document-detail/inventory.json
source_root=/path/target_repo/source
```

**Page type detection:** Component uses `useSelector` and `useDispatch` → React Container Component
**Files read:** `DocumentDetail.tsx`, Redux slice `documentSlice.ts`, `documentService.ts`, `useAuth.ts`
**call-tree.json:** `useEffect[onMount]` entry point dispatching `fetchDocumentById` thunk → service → `db: {table: "Documents", op: "select"}`
**Note:** Container components dispatch Redux thunks — trace the thunk action creator rather than a direct service call from the component.

---

## Important Notes

1. **Three component types, three discovery paths.** React Page Components, React Feature Components, and React Container Components each have distinct data-flow patterns. Detect the component type first (Phase 1) and apply only the matching discovery path in Phase 2.

2. **Trace depth: stop at DB, not at the service interface.** Follow calls through hooks and service modules until you reach an explicit `db` node or a leaf API call. Do not stop at the interface/type boundary — read the implementation.

3. **Multiple handlers = `"handlers"` array.** Use the flat (`"entryPoint"` + `"calls"`) shape only for single-interaction components. Use `"handlers": [...]` whenever there is more than one entry point (e.g., mount + submit + filter change).

4. **Columns = touched columns only.** Do not list all columns in the ORM model. Only list the columns actually read or written by this feature's handlers. Check ORM query `select`/`include` options and model mutation calls.

5. **Child components scope.** Read child components that are imported and rendered by the page and extract their UI elements into the `functional-spec.md` table. However, if a child component implements a feature with its own `feature_key`, mark it as out of scope rather than duplicating the analysis.

6. **Idempotency.** All four output files are overwritten cleanly on each run. A second run with the same inputs must produce identical output.

7. **Source refs use relative paths.** In the UI elements table, `Source ref` values are relative to `source_root` (e.g., `DocumentList.tsx:39`, not absolute paths).

8. **Gherkin covers edge cases that matter for .NET/Angular.** The Gherkin scenarios will be consumed by the .NET/Angular developer. Always cover: auth guard redirect, loading/empty-list state, form validation failure on submit, and optimistic UI or error rollback if present. These are the cases most likely to be missed when reimplementing.

9. **`dotnetEquivalent` is in inventory, not here.** This command does not add `dotnetEquivalent` to any output. That field lives in `inventory.json`. The .NET/Angular developer uses `call-tree.json` and `functional-spec.md` together to understand the mapping.

10. **No screenshots directory.** This command does not create a `screenshots/` folder. If screenshots already exist in the output folder, do not delete them.
