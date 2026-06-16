# Analyze API Endpoint

You are tasked with producing a detailed analysis of a single API entry point from the DocVault Express.js/Node.js legacy application. The output feeds a modernization effort targeting **ASP.NET Core 9.0 Web API + Angular 19 SPA** — every artifact must contain enough technical and business detail for a .NET developer to implement the equivalent `[ApiController]` endpoint without consulting the original source.

This is a **discover-phase** command. It reads the legacy DocVault source and writes structured artifacts to `docs/entry-points/api-endpoints/{key}/`.

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<endpoint-key>  legacy_dir=<abs-path>  location=<rel-path>  output_dir=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | Logical name for this endpoint (e.g., `list-documents`) |
| `legacy_dir` | Absolute path to the DocVault legacy source root (e.g., `.../legacy/ae-slp-docvault`) |
| `location` | Path to the entry point file, **relative to `legacy_dir`** (e.g., `backend/src/routes/documents.js`) |
| `output_dir` | Absolute path to the output folder — create it if needed, overwrite files if present |

**Examples:**

```
key=list-documents
legacy_dir=/abs/path/legacy/ae-slp-docvault
location=backend/src/routes/documents.js
output_dir=/abs/path/docs/entry-points/api-endpoints/list-documents
```

```
key=search-documents
legacy_dir=/abs/path/legacy/ae-slp-docvault
location=backend/src/services/SearchOrchestrator.js
output_dir=/abs/path/docs/entry-points/api-endpoints/search-documents
```

```
key=login-user
legacy_dir=/abs/path/legacy/ae-slp-docvault
location=backend/src/routes/auth.js
output_dir=/abs/path/docs/entry-points/api-endpoints/login-user
```

---

## Entry Point Types

Two distinct patterns exist in DocVault. Detect the type from `location`:

| Pattern | Location clue | Description |
|---|---|---|
| **Express Route Handler** | `backend/src/routes/` | Inline `router.get/post/put/delete()` handler function. Already a REST endpoint. JWT auth enforced by middleware in `backend/src/index.js`. |
| **Express Service** | `backend/src/services/` | Module with exported class/functions called from route handlers. Not yet directly HTTP-exposed. Will become an ASP.NET Core `[ApiController]`. |

---

## Output

Four files, written to `{output_dir}/`:

```
{output_dir}/
├── metadata.json
├── functional-spec.md
├── call-tree.json
└── database-dependencies.json
```

---

### `metadata.json` — filled-in example (Express Route Handler)

```json
{
  "key": "list-documents",
  "name": "List documents",
  "type": "api-endpoint",
  "domain": "documents",
  "legacyEntryPoint": "backend/src/routes/documents.js#GET /",
  "legacyLocation": "backend/src/routes/documents.js:10",
  "targetRestContract": {
    "method": "GET",
    "path": "/api/documents",
    "queryParams": [],
    "responseModel": "DocumentListResponse",
    "auth": "jwt",
    "notes": "Express route already HTTP-exposed. Target .NET endpoint keeps same route. Returns all documents ordered by uploaded_at DESC. No pagination in legacy — consider adding in target."
  },
  "usedByUiFeatures": ["document-list-page"]
}
```

### `metadata.json` — filled-in example (Express Service)

```json
{
  "key": "search-documents",
  "name": "Search documents",
  "type": "api-endpoint",
  "domain": "search",
  "legacyEntryPoint": "backend/src/services/SearchOrchestrator.js#SearchOrchestrator.search",
  "legacyLocation": "backend/src/services/SearchOrchestrator.js:1",
  "legacyRouteHandler": "backend/src/routes/search.js#GET /",
  "targetRestContract": {
    "method": "GET",
    "path": "/api/search",
    "queryParams": [
      {"name": "q", "type": "string", "optional": false}
    ],
    "responseModel": "SearchResponse",
    "auth": "jwt",
    "notes": "Service is invoked from the GET /api/search route. The .NET target exposes this as a single [HttpGet] action. Falls back to FallbackSearchProvider when primary index is unavailable."
  },
  "usedByUiFeatures": ["document-search"],
  "notes": [
    "SearchOrchestrator delegates to IndexManager first; falls back to FallbackSearchProvider on error.",
    "The legacy fallback performs a raw SQL ILIKE query against documents_v2."
  ]
}
```

---

### `functional-spec.md` — filled-in example

```markdown
# Functional spec — List documents

**Key:** `list-documents`
**Legacy:** `backend/src/routes/documents.js#GET /` — `GET /api/documents`
**Target REST:** `GET /api/documents`

## Purpose

Return all documents stored in DocVault, ordered by upload date descending.
The Angular document-list page calls this on every load.

## Inputs

| Name | Type | Optional | Default | Notes |
| --- | --- | --- | --- | --- |
| _(none)_ | — | — | — | No query parameters in legacy implementation. |

## Outputs

\`\`\`json
{
  "documents": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Q3 Report.pdf",
      "file_type": "application/pdf",
      "file_path": "/uploads/a1b2c3d4.pdf",
      "tags": ["finance", "quarterly"],
      "uploaded_at": "2024-11-01T12:34:56.000Z",
      "uploaded_by": "admin@docvault.local"
    }
  ]
}
\`\`\`

## Acceptance criteria

\`\`\`
Scenario: Documents exist
  Given 5 documents are in documents_v2
  When GET /api/documents
  Then response.documents.length == 5
  And documents are ordered by uploaded_at DESC

Scenario: No documents exist
  Given documents_v2 is empty
  When GET /api/documents
  Then response.documents.length == 0

Scenario: Unauthenticated request
  Given no JWT token is provided
  When GET /api/documents
  Then response status is 401
\`\`\`

## Business rules

- Results are always sorted by `uploaded_at DESC` — most recently uploaded first.
- All rows from `documents_v2` are returned; no pagination in legacy.
- The `tags` column is a PostgreSQL `TEXT[]` array; return as a JSON array of strings.

## Non-functional

- Read-only; no writes.
- JWT authentication required (enforced by global middleware in `backend/src/index.js`).
- Called on every document list page load.
```

---

### `call-tree.json` — Express Route Handler shape

```json
{
  "entryPoint": {
    "method": "backend/src/routes/documents.js#GET /",
    "file": "backend/src/routes/documents.js",
    "line": 10,
    "signature": "async (req, res) => void"
  },
  "calls": [
    {
      "method": "pool.query",
      "db": {"table": "documents_v2", "op": "select"},
      "notes": "Selects all rows ordered by uploaded_at DESC. No filtering or pagination."
    }
  ]
}
```

### `call-tree.json` — Express Service shape (route delegates to service)

When the legacy entry point is a service module called from a route handler, represent the route as a wrapper around the service:

```json
{
  "legacyRouteHandler": {
    "method": "backend/src/routes/search.js#GET /",
    "file": "backend/src/routes/search.js",
    "line": 8,
    "signature": "async (req, res) => void"
  },
  "entryPoint": {
    "method": "SearchOrchestrator.search",
    "file": "backend/src/services/SearchOrchestrator.js",
    "line": 1,
    "signature": "async search(query: string): Promise<object[]>"
  },
  "calls": [
    {
      "method": "IndexManager.search",
      "file": "backend/src/services/IndexManager.js",
      "notes": "Primary search path. Falls back to FallbackSearchProvider on error."
    },
    {
      "method": "FallbackSearchProvider.search",
      "file": "backend/src/services/FallbackSearchProvider.js",
      "notes": "Only invoked when IndexManager throws. Performs raw SQL ILIKE query."
    },
    {
      "method": "pool.query",
      "db": {"table": "documents_v2", "op": "select"},
      "notes": "FallbackSearchProvider queries documents_v2 with ILIKE on name and tags."
    }
  ]
}
```

### `database-dependencies.json` — filled-in example

```json
[
  {
    "type": "table",
    "name": "documents_v2",
    "key": "documents-v2",
    "operations": ["select"],
    "columns": ["id", "name", "file_type", "file_path", "tags", "uploaded_at", "uploaded_by"],
    "locations": [
      "backend/src/routes/documents.js"
    ],
    "notes": [
      "All columns selected. No filtering applied — full table scan ordered by uploaded_at DESC.",
      "tags column is a PostgreSQL TEXT[] array; returned as a JSON array of strings."
    ]
  }
]
```

---

## Field Rules

### metadata.json

| Field | Rule |
|---|---|
| `key` | Copied verbatim from the `key` arg |
| `name` | Human-readable name for the operation. Derive from the route path and method: `GET /` in documents.js → `"List documents"` |
| `type` | Always `"api-endpoint"` |
| `domain` | Derive from the route file name or service name: `documents.js` → `"documents"`, `SearchOrchestrator.js` → `"search"`, `auth.js` → `"auth"` |
| `legacyEntryPoint` | `"{file}#{HTTP_VERB} {path}"` for route handlers (e.g., `backend/src/routes/documents.js#GET /`); `"{file}#{ClassName}.{method}"` for services (e.g., `backend/src/services/SearchOrchestrator.js#SearchOrchestrator.search`) |
| `legacyLocation` | `{file-relative-to-legacy_dir}:{line}` of the handler or method definition |
| `legacyRouteHandler` | **Express Services only.** `"{file}#{HTTP_VERB} {path}"` of the route handler that calls this service. Omit for Express Route Handlers. |
| `targetRestContract.method` | HTTP verb: extract from `router.get/post/put/delete` (Route Handler) or derive from service method verb (get/list→GET, add/create/upload→POST, set/update→PUT, delete/remove→DELETE) |
| `targetRestContract.path` | REST path. For Route Handlers: extract from the `app.use()` mount in `index.js` + the `router.*()` sub-path. For services: derive a RESTful resource path. |
| `targetRestContract.queryParams` | Array of `{name, type, default?, optional}` objects. Present only for GET endpoints. |
| `targetRestContract.requestModel` | Object describing the request body fields. Present only for POST/PUT endpoints. |
| `targetRestContract.responseModel` | Name of the response shape (e.g., `"DocumentListResponse"`) |
| `targetRestContract.auth` | `"jwt"` if the route is under `/api` (all `/api` routes require JWT via global middleware, except `/api/auth/*`); `"none"` for auth endpoints themselves |
| `targetRestContract.notes` | 1–2 sentences about how the legacy implementation maps to the .NET target — especially where the mapping is non-obvious |
| `usedByUiFeatures` | Array of `feature_key` strings for UI features that call this endpoint. Derive by searching `docs/entry-points/ui-features/*/call-tree.json`. Leave as `[]` if none found. |
| `notes` | Array of factual strings about non-obvious behavior: fallback logic, guard clauses, side effects, known bugs to not carry over. Omit if empty. |

### functional-spec.md

| Section | Rule |
|---|---|
| **Purpose** | 2–3 sentences: what operation this performs and which Angular component calls it |
| **Inputs** | Table: Name, Type, Optional, Default, Notes. For GET: query params. For POST/PUT: request body fields and `multipart/form-data` fields if applicable. For path params: include them with "path" in Notes. |
| **Outputs** | Filled-in JSON example of the response body. Include only the fields this endpoint actually returns — not the full table row shape if the endpoint projects a subset. |
| **Acceptance criteria** | Gherkin `Scenario:` blocks. At minimum: happy path, empty/not-found case, and any guard clause that returns an error (missing required param, invalid file type, etc.). |
| **Business rules** | Numbered list of non-obvious rules: defaults, ordering, guard clauses, idempotency semantics, file type restrictions. |
| **Non-functional** | Read-only vs mutating, auth required, expected call frequency, any notable performance concerns (e.g., full-table scan, no pagination). |

### call-tree.json

| Field | Rule |
|---|---|
| `entryPoint.method` | `"{file}#{HTTP_VERB} {path}"` for route handlers; `"{ClassName}.{method}"` for services |
| `entryPoint.signature` | Full JS/Node function signature including return type if determinable (e.g., `async (req, res) => void`, `async search(query: string): Promise<object[]>`) |
| `entryPoint.file` | Relative to `legacy_dir` |
| `entryPoint.line` | Line where the handler function or method is defined |
| `legacyRouteHandler` | Present only for Express Services. Same fields as `entryPoint` but refers to the route handler that invokes the service. |
| `db` | Object `{"table": "Name", "op": "select|insert|update|delete|count"}`. Use an array when a single call does multiple ops. |
| `notes` | Only for non-obvious conditional logic (e.g., "Only when IndexManager throws") |
| Tracing depth | Follow until you reach a `db` node or an external leaf (file system, external HTTP, email). Do not trace into `pg` pool internals. |

### database-dependencies.json

Identical rules to `analyze-ui-feature`:

| Field | Rule |
|---|---|
| `key` | Lowercase kebab-case of `name` |
| `operations` | Only ops actually performed by this endpoint. Order: select before mutate. |
| `columns` | Only columns read or written. Check the SQL query strings in the route/service files. |
| `locations` | Files where the table is accessed: route files, service files. |
| `notes` | 1–2 sentences on *how* this endpoint uses the table. |

---

## Exclusion Criteria

Do NOT include in `database-dependencies.json`:
- Tables accessed only by middleware or other routes that happen to share a service
- PostgreSQL system tables or migration tracking tables

Do NOT add call tree nodes for:
- `pg` pool internals (`pool.connect`, `client.release`)
- Express middleware internals (`next()`, `res.status()`, `res.json()`)
- `multer` internals for file storage (note multer usage in the entry point metadata but don't trace into it)

Do NOT set `legacyRouteHandler` for Express Route Handlers — those inline handlers are already the HTTP layer.

---

## Discovery Process

### Phase 1: Detect Entry Point Type and Read the File

1. Check `location`:
   - Contains `backend/src/routes/` → **Express Route Handler**
   - Contains `backend/src/services/` → **Express Service**
2. Read `{legacy_dir}/{location}`.
3. **Express Route Handler:** Locate the `router.get/post/put/delete()` call matching the `key`. Extract the HTTP verb and sub-path. Cross-reference `backend/src/index.js` to determine the full mount path (e.g., `app.use('/api/documents', documentRoutes)` + `router.get('/')` = `GET /api/documents`).
4. **Express Service:** Identify the specific exported class/function this `key` refers to. Search `backend/src/routes/` for route handlers that `require()` and call this service — that becomes `legacyRouteHandler`.

**For Express Route Handlers — read companion middleware:**
- `backend/src/middleware/jwtAuth.js` — confirm auth enforcement
- `backend/src/middleware/apiKeyAuth.js` and `backend/src/middleware/sessionAuth.js` if referenced

**For Express Services — read caller route:**
- Read the route file that imports and calls this service
- Note what the route does before/after calling the service (validation, response shaping)

**Derive `targetRestContract`:**
- Express Route Handler: extract HTTP verb from `router.*()` + full path from `index.js` mount + sub-path
- Express Service: derive RESTful path using these rules:
  - Resource = entity the service operates on (documents, search, uploads)
  - `getX(id)` → `GET /api/{resources}/{id}`
  - `listX()` → `GET /api/{resources}`
  - `searchX(query)` → `GET /api/{resources}?q={query}`
  - `addX(...)` / `uploadX(...)` → `POST /api/{resources}`
  - `updateX(id, ...)` → `PUT /api/{resources}/{id}`
  - `deleteX(id)` → `DELETE /api/{resources}/{id}`

---

### Phase 2: Trace the Call Tree

Starting from the entry point (route handler function or service method):

1. List every function/method called directly.
2. For each service call (`require('../services/...')`), read the service file.
3. For each `pool.query()` call, record the table name (from the SQL string) and op (SELECT/INSERT/UPDATE/DELETE).
4. For each service method call within a service, read that service's file if not already read.
5. For file system operations (`fs.existsSync`, `res.sendFile`), note them as external leaves — do not trace into Node.js `fs` internals.
6. Continue 3 levels deep, stopping at `db` nodes or external leaves.
7. Note any guard clauses (`if (!req.file)`, `if (!q || !q.trim())`) that produce error responses.

---

### Phase 3: Identify Database Dependencies

From the call tree:

1. Collect every distinct table name across all `pool.query()` calls (parse from the SQL strings).
2. For each table:
   a. Collect all SQL operation types (SELECT/INSERT/UPDATE/DELETE) → `operations` array.
   b. Parse the SQL column list or `*` to determine which columns are read or written → `columns`. For `SELECT *`, inspect the response shape to list columns actually used.
   c. Collect all file paths where the table is queried → `locations`.
   d. Write 1–2 factual sentences on how this endpoint uses the table → `notes`.

---

### Phase 4: Determine `usedByUiFeatures`

Search existing `docs/entry-points/ui-features/*/call-tree.json` files. For each, check whether the `legacyEntryPoint` service method name appears anywhere in the call tree nodes. If yes, add that feature's `key` to the `usedByUiFeatures` array.

If `docs/entry-points/ui-features/` doesn't exist yet or contains no files, leave the array empty.

---

### Phase 5: Compose All Output Files

**Write `metadata.json`** — construct from discovery above. Write immediately (create `output_dir` if needed), overwrite if present.

**Write `call-tree.json`** — overwrite if present.

**Write `database-dependencies.json`** — overwrite if present.

**Write `functional-spec.md`:**
- Purpose: 2–3 sentences from inline comments in the route/service file or inferred from the route path and method name.
- Inputs table: derive from `req.query`, `req.body`, `req.params`, and `req.file` (multer). Note which are required vs optional (based on guard clauses in the handler).
- Outputs: produce a filled-in JSON example, not a schema. Use realistic-looking placeholder values matching the actual `res.json()` shape.
- Acceptance criteria: minimum one scenario per significant branch (happy path, empty/no-result, guard-clause failure, auth rejection).
- Business rules: non-obvious rules only — ordering, file type restrictions, fallback behavior, known bugs to not carry over (document explicitly as "do NOT carry over to .NET target").
- Non-functional: whether read-only, auth required (all `/api/*` routes except `/api/auth/*` require JWT), call frequency.

---

## Implementation Workflow

### Step 1: Parse Parameters
Extract `key`, `legacy_dir`, `location`, `output_dir` from `{{PROMPT}}`.

### Step 2: Detect Entry Point Type
Check `location` prefix: `backend/src/routes/` → Express Route Handler; `backend/src/services/` → Express Service.

### Step 3: Read Source Files
- For Express Route Handlers: read route `.js` file + `backend/src/index.js` for mount path.
- For Express Services: read service file + route caller file.

### Step 4: Derive `targetRestContract`
Extract (Express Route Handler) or derive (Express Service) the HTTP method, full path (mount + sub-path), params, response model, and auth requirement.

### Step 5: Write metadata.json
Write to `{output_dir}/metadata.json` — create folder if needed, overwrite if present.

### Step 6: Trace Call Tree
Follow handler → services → repositories → DB, 3 levels max.

### Step 7: Write call-tree.json
Write to `{output_dir}/call-tree.json` — overwrite if present.

### Step 8: Identify DB Dependencies
Collect tables from call tree; enrich with columns and locations.

### Step 9: Write database-dependencies.json
Write to `{output_dir}/database-dependencies.json` — overwrite if present.

### Step 10: Determine usedByUiFeatures
Search `docs/entry-points/ui-features/*/call-tree.json` for the service method name.

### Step 11: Write functional-spec.md
Write to `{output_dir}/functional-spec.md` — overwrite if present.

### Step 12: Report Summary
```
Key:              {key}
Entry point type: {Express Route Handler | Express Service}
HTTP contract:    {METHOD} {path}
DB tables:        {list}
Gherkin blocks:   {count}
usedByUiFeatures: {list or "[]"}
Files written:    metadata.json, call-tree.json, database-dependencies.json, functional-spec.md
```

---

## Worked Examples

### Example 1: Express Route Handler — `GET /api/documents`

**Input:**
```
key=list-documents
legacy_dir=/path/legacy/ae-slp-docvault
location=backend/src/routes/documents.js
output_dir=/path/docs/entry-points/api-endpoints/list-documents
```

**Entry point type:** Express Route Handler (`backend/src/routes/`)

**Files read:**
- `backend/src/routes/documents.js`
- `backend/src/index.js` (to confirm mount path: `app.use('/api/documents', documentRoutes)`)
- `backend/src/db/migrations/002-create-documents-v2.sql` (to confirm column names)

**targetRestContract:** `GET /api/documents` (mount `/api/documents` + sub-path `/`)

**Auth:** `"jwt"` (all `/api/*` routes gated by global JWT middleware in `index.js`, except `/api/auth/*`)

**DB tables:** `documents_v2` (select)

**Gherkin blocks:** 3 (documents exist, no documents, unauthenticated)

**Notable business rule to capture:** Query uses `SELECT *` — the .NET target should project only needed columns explicitly.

---

### Example 2: Express Service — `SearchOrchestrator.search`

**Input:**
```
key=search-documents
legacy_dir=/path/legacy/ae-slp-docvault
location=backend/src/services/SearchOrchestrator.js
output_dir=/path/docs/entry-points/api-endpoints/search-documents
```

**Entry point type:** Express Service (`backend/src/services/`)

**Files read:**
- `backend/src/services/SearchOrchestrator.js`
- `backend/src/services/IndexManager.js`
- `backend/src/services/FallbackSearchProvider.js`
- `backend/src/routes/search.js` (legacyRouteHandler caller)

**targetRestContract derived:**
- Verb: `search` → `GET`
- Resource: documents/search → `GET /api/search?q={query}`
- `q` is required (guard clause returns 400 if missing)

**legacyRouteHandler:** `backend/src/routes/search.js#GET /`

**DB tables:** `documents_v2` (select via FallbackSearchProvider only)

**Gherkin blocks:** 4 (results found, no results, missing q param, index unavailable falls back)

---

### Example 3: Express Route Handler — `POST /api/auth/login`

**Input:**
```
key=login-user
legacy_dir=/path/legacy/ae-slp-docvault
location=backend/src/routes/auth.js
output_dir=/path/docs/entry-points/api-endpoints/login-user
```

**Entry point type:** Express Route Handler (`backend/src/routes/`)

**targetRestContract:** `POST /api/auth/login` (mount `/api/auth` + sub-path `/login`)

**Auth:** `"none"` — this endpoint IS the auth endpoint. It accepts credentials and returns `{ token, refreshToken }`. All other `/api/*` endpoints then require that JWT.

**Files read:** `backend/src/routes/auth.js` + `backend/src/middleware/jwtAuth.js`

**DB tables:** None — credentials are hardcoded; no user table in legacy.

**Non-functional note:** Credentials are hardcoded (`admin@docvault.local` / `docvault123`). The .NET target must implement proper user management with a database-backed user store. Do NOT carry over the hardcoded credentials.

---

## Important Notes

1. **Two entry point types, two discovery paths.** The `location` prefix determines everything — apply only the matching discovery path. Do not confuse an inline route handler (Express Route Handler) with a service module (Express Service).

2. **`targetRestContract` is the deliverable for the .NET developer.** This is what the ASP.NET Core developer implements as a `[ApiController]`. Make it precise: exact HTTP verb, full resource path, every query param or request body field, the response model name. Vague contracts cause rework.

3. **Express Services need a derived REST path.** When `location` points to a service file, you must design the REST path yourself using the resource-oriented rules in Phase 1. The .NET developer has no other reference for the target route.

4. **Auth is global middleware, not per-route.** All routes under `/api` (except `/api/auth/*`) require JWT. You do not need to find per-route auth annotations — check `backend/src/index.js` for the middleware setup and default to `"jwt"` for all non-auth endpoints.

5. **Hardcoded credentials are a legacy artifact.** The `auth.js` route hardcodes `admin@docvault.local` / `docvault123`. Flag this explicitly in the notes with "do NOT carry over to .NET target — implement proper user store."

6. **Known bugs in legacy.** The `/api/auth/refresh` route returns a session-shaped response instead of a JWT-shaped response (bug FR-007). When analyzing affected endpoints, document the bug explicitly and specify the correct behavior for the .NET target.

7. **`documents` vs `documents_v2`.** The upload route writes to `documents` (the old table); a PostgreSQL trigger copies to `documents_v2`. Read endpoints use `documents_v2`. Document this split accurately in `database-dependencies.json`.

8. **`usedByUiFeatures` may be empty.** If `docs/entry-points/ui-features/` doesn't exist yet, write `"usedByUiFeatures": []` — the workflow will populate it in a later pass.

9. **Idempotency.** All four output files overwrite cleanly on each run. Re-running with the same inputs must produce identical output.

10. **`legacyLocation` line number.** Always include the line number of the handler or method definition. If you cannot determine it precisely, omit the `:N` suffix rather than guessing.
