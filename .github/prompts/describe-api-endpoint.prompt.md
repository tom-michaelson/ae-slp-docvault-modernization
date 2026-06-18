# Describe API Endpoint

Produce a detailed technical narrative (`functional-description.md`) for a legacy React/Node.js API endpoint. This document describes **how the legacy endpoint works** — the REST contract, business logic, call sequence, database dependencies, and migration constraints — in enough detail for a .NET/Angular developer to implement the equivalent ASP.NET Core `[ApiController]` endpoint without reading the original TypeScript/JavaScript source.

This is a **discover-phase** command. It reads the artifacts already written by `analyze-api-endpoint` plus the actual source files, and enriches them into a structured developer-facing description.

**Pipeline position:**
```
analyze-api-endpoint  →  metadata.json, call-tree.json, database-dependencies.json, functional-spec.md
describe-api-endpoint →  functional-description.md    ← this command
```

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<endpoint-key>  endpoint_dir=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | The endpoint key (e.g., `list-documents-paged`) |
| `endpoint_dir` | Absolute path to the endpoint folder (e.g., `.../docs/entry-points/api-endpoints/list-documents-paged`) |

Source files are resolved from `./source/{legacyLocation}` relative to cwd (`target_repo/`), using the `legacyLocation` field in `{endpoint_dir}/metadata.json`.

**Examples:**

```
key=list-documents-paged
endpoint_dir=/abs/path/docs/entry-points/api-endpoints/list-documents-paged
```

```
key=upload-document
endpoint_dir=/abs/path/docs/entry-points/api-endpoints/upload-document
```

---

## Idempotency

- If `{endpoint_dir}/functional-description.md` already exists → **stop immediately**. The analysis is complete.
- If `{endpoint_dir}/functional-description.in-progress.md` exists → a previous run crashed. **Overwrite it** and re-run the full analysis.
- Otherwise → proceed with full analysis.

---

## Inputs Read by This Command

From `{endpoint_dir}/`:

| File | What to extract |
|---|---|
| `metadata.json` | `key`, `name`, `domain`, `legacyEntryPoint`, `legacyLocation`, `legacyWebHandler` (if present), `targetRestContract`, `usedByUiFeatures`, `notes` |
| `functional-spec.md` | Purpose, Inputs table, Outputs JSON example, Gherkin scenarios, business rules, non-functional notes |
| `call-tree.json` | Entry point method and signature, call chain nodes, DB operations |
| `database-dependencies.json` | Tables, columns, operations, file locations |

From `./source/` (cwd-relative):

| Resolved from | What to read |
|---|---|
| `./source/{legacyLocation}` | The route handler file (Express route) or service method file (in-process) |
| `./source/{call-tree.legacyWebHandler.file}` | The route handler that calls the service — **in-process only** |
| `./source/{call-tree.calls[].file}` | Service implementations, ORM model files, middleware listed in the call tree |

---

## Output

```
{endpoint_dir}/functional-description.md
```

Written incrementally via:
1. Create `{endpoint_dir}/functional-description.in-progress.md` at Phase 1
2. Write each section as it is completed
3. Rename to `functional-description.md` at Phase 4 (final step)

---

## Output Template

The template below uses `list-documents-paged` (Express Route Handler GET) as the filled-in example. For an in-process service, replace the Component Details section and adapt the Call Sequence and Migration Notes accordingly — see the In-process service note blocks throughout.

```markdown
# Functional Description: {name}

> **Entry Point**: {key}
> **Location**: {legacyLocation}
> **Type**: API / {Express Route Handler | Service Module}
> **Domain**: {domain}
> **Legacy method**: {legacyEntryPoint}
> **Web handler**: {legacyWebHandler}   ← include only for in-process services

## Executive Summary

[2–3 paragraphs covering:
1. What operation this endpoint performs and which Angular component or UI feature calls it
2. The key constraints: auth requirements, lazy creation, server-side lookups, validation guards
3. Anything non-obvious about the legacy implementation that the .NET/Angular developer must understand
   before implementing]

For example (list-documents-paged):
The `list-documents-paged` endpoint returns a paginated, optionally filtered page of documents from the document vault. It is called by the Angular documents page on initial load and on every filter or pagination interaction.

The endpoint performs two sequential database queries: a COUNT query to compute the total page count, then a paginated SELECT query for the current page. Each document's `fileUri` is rewritten from a relative storage path to an absolute URL before being returned.

Authentication is required via JWT Bearer token. The legacy implementation includes a deliberate 200ms artificial delay for demo purposes — this must NOT be carried over to the .NET target.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `/api/catalog-items` |
| Auth required | no |

### Query Parameters *(GET endpoints — omit section for POST/PUT)*

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `pageSize` | int | no | 10 | Items per page. When `0`, returns all matching items. |
| `pageIndex` | int | no | 0 | 0-indexed page number |
| `ownerId` | string | no | null | Filter by document owner (admin only) |
| `status` | string | no | null | Filter by document status (draft/published/archived) |

### Request Body *(POST/PUT endpoints — omit section for GET)*

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `title` | string | yes | Document title, max 255 chars |
| `file` | File (multipart) | yes | The document file binary |
| `tags` | string[] | no | Optional tag list |

> **File binary is never trusted from URL.** The legacy route handler validates the file via multer middleware before passing it to the service. The .NET target must replicate this server-side file validation.

### Success Response

```json
{
  "pageCount": 3,
  "documents": [
    {
      "id": "d1a2b3c4",
      "title": "Q1 Report",
      "fileUri": "https://host/files/documents/d1a2b3c4.pdf",
      "status": "published",
      "ownerId": "user-123",
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 401 | JWT required but absent or invalid | empty |
| 404 | Resource not found (in-process endpoints that look up by ID) | empty |
| 400 | Validation guard triggered (negative quantity, null ID, etc.) | ValidationProblem or empty |

---

## Business Logic

### Overview

[Narrative of what this endpoint does — written so a .NET/Angular developer can implement it without
reading the TypeScript/JavaScript source. Cover: what it queries or mutates, the key invariants that must hold,
and any branching behavior (empty result, lazy creation, redirect on error).]

list-documents-paged example:
The endpoint accepts optional `ownerId` and/or `status` filters. Both are optional; if omitted, all documents are included. Pagination is controlled by `pageSize` (items per page) and `pageIndex` (0-based). When `pageSize=0`, all matching documents are returned in a single page.

Two queries are issued: a COUNT to compute `pageCount`, then a paginated SELECT for the current page. `pageCount = ceil(totalDocuments / pageSize)`. Each returned document's `fileUri` is rewritten from a relative storage path to an absolute URL via `uriComposer.composeFileUri`.

### Validation Rules

| Field / Condition | Rule | Failure behavior |
| --- | --- | --- |
| `pageSize` | Integer ≥ 0 | Unvalidated in legacy (causes 500); .NET: return 400 |
| `pageIndex` | Integer ≥ 0 | Same as above |
| `documentId` | Not null/undefined (service) | Returns null in legacy; .NET: return 404 |

### Call Sequence

[Numbered walkthrough of what happens when a request arrives. Derived from `call-tree.json` and
source file reads — not just a list of method names, but what each call does and why.]

**list-documents-paged:**
1. Receive request: `pageSize`, `pageIndex`, optional `ownerId`, `status`
2. Build query object `{ where: { ownerId, status }, skip: pageSize * pageIndex, take: pageSize }`
3. `documentRepository.count(query)` → total matching documents → compute `pageCount`
4. `documentRepository.findMany(pagedQuery)` → materialize current page rows
5. For each document: `uriComposer.composeFileUri(doc.fileUri)` → rewrite to absolute URL
6. Map entity to DTO (only include fields in response contract)
7. Return `{ pageCount, documents }`

---

## Component Details

### Express Route Handler *(include for Express route handler type)*

**Router file**: `src/routes/documents.js` (or `.ts`)
**Handler function**: `listDocumentsPaged`

**Route registration:**
```javascript
router.get('/api/documents', authMiddleware, listDocumentsPaged);
```

**Query params parsed**: `pageSize` (number, default 10), `pageIndex` (number, default 0), `ownerId` (string?), `status` (string?)

**Response shape**: `{ pageCount: number, documents: DocumentDto[] }`

**Dependencies**: `documentRepository`, `uriComposer`, auth middleware

---

### In-process Service *(include for In-process Service type — replace Express Route Handler section above)*

**Service file**: `src/services/documentService.js`
**Method**: `uploadDocument(userId, file, metadata)`

**Called from web handler**: `POST /api/documents` route handler
**Web handler file**: `src/routes/documents.js`

**What the route handler does BEFORE calling the service:**
1. Validates `file` is present — returns 400 if missing
2. Validates `title` is not empty — returns 400 if blank
3. Resolves `userId` from JWT token (auth middleware populates `req.user`)
4. **Then** calls `documentService.uploadDocument(userId, file, metadata)`

**What the route handler does AFTER the service call:**
- Returns 201 with the created document DTO
- On error: returns 500 with error message

> **File binary is never trusted from URL.** The legacy route handler validates the file via multer middleware before passing it to the service. The .NET target must replicate this server-side file validation.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `documents` | SELECT, COUNT | `id`, `title`, `ownerId`, `fileUri`, `status`, `createdAt` | COUNT for pageCount; SELECT for current page with optional filters |
| `document_versions` | SELECT, INSERT | `id`, `documentId`, `version`, `fileUri` | INSERT on new upload; SELECT to get version history |
| `document_tags` | SELECT | `documentId`, `tag` | Joined when tags filter is applied |

---

## Security Considerations

### Authentication

- **Required**: no / yes — JWT Bearer via `[Authorize]` + `RequireAuthorization()` in `AddRoute()`
- **Mechanism**: *(if required)* JWT bearer token in `Authorization: Bearer {token}` header
- **Notes**: ...

### Price Integrity *(if applicable)*

File source is validated server-side. The legacy route handler uses multer middleware to validate the uploaded file before passing it to the service. **The .NET target must replicate this server-side file validation** — the endpoint must never trust a client-supplied file URI.

### Input Validation

[Describe what the endpoint validates (guard clauses, model state checks) and what it does NOT validate — so the .NET/Angular developer knows where to add validation that the legacy code lacks.]

---

## Performance Notes

| Concern | Detail | .NET target action |
| --- | --- | --- |
| Deliberate delay | `await sleep(200)` in handler | **Do NOT carry over** — artificial demo delay |
| Manual DTO mapping | Object spread or lodash `_.pick()` per result item | .NET: use AutoMapper (or manual mapping) or manual projection; ensure same fields are mapped |
| Two-query pagination | COUNT query + SELECT query are separate round-trips | .NET: EF Core skip/take; acceptable to keep two queries if simpler |
| Lazy document creation | `documentRepository.create` fires only when document doesn't exist | .NET: make the create idempotent (check before insert, or use upsert) |

---

## Migration Notes

| Aspect | Legacy behavior | .NET target requirement |
| --- | --- | --- |
| `fileUri` rewriting | `uriComposer.composeFileUri` converts relative storage path to absolute URL using app's base URL | .NET endpoint must compose the absolute URI; either store absolute URLs in DB or implement equivalent URI composition |
| `pageSize=0` semantics | When `pageSize=0`, all matching documents are returned (skip=0, take=all) | Preserve this behaviour or document it is intentionally changed |
| `await sleep(200)` | Artificial 200ms delay in handler | **Remove** — do not replicate in .NET target |
| File source | Caller validates file via middleware; service receives file as parameter | .NET endpoint must validate file server-side |
| JWT user identity | JWT from Authorization header resolves the `userId`; .NET target uses `[Authorize]` + `User.FindFirst(ClaimTypes.NameIdentifier)` | JWT from Authorization header resolves the `userId`; .NET target uses `[Authorize]` + `User.FindFirst(ClaimTypes.NameIdentifier)` |
| Document soft-delete | Legacy sets `status='deleted'` rather than hard-deleting | .NET must replicate soft-delete behavior |

---

## Analysis Notes

[Technical debt, edge cases, and anything that would surprise a .NET/Angular developer implementing this endpoint.]

- `pageCount` when `pageSize=0`: the legacy code computes `pageCount = 1` when all documents fit one "infinite" page. .NET target should decide whether to preserve this or return `pageCount = 0` for an empty result set when `pageSize=0`.
- Manual DTO mapping via object spread or `_.pick()`: the DTO may not include all entity fields. Read the response shape definition to confirm exactly which fields are projected — only those fields should appear in the .NET response DTO.
- Document file-size guard: the legacy multer middleware enforces a maximum file size. The .NET target should return HTTP 400 rather than propagating a 500.
- Document soft-delete: `status='deleted'` is set rather than hard-deleting. Note this for reference when the `delete-document` endpoint is described.
```

---

## Discovery Process

### Phase 0: Idempotency Check

1. Check if `{endpoint_dir}/functional-description.md` exists → **stop** if yes.
2. Check if `{endpoint_dir}/functional-description.in-progress.md` exists → overwrite it if yes and re-run the full analysis.

---

### Phase 1: Read Artifacts and Create In-Progress File

1. Read `{endpoint_dir}/metadata.json` — extract all fields.
2. **Detect entry point type:**
   - `legacyLocation` contains `src/routes/` or `src/api/` → **Express Route Handler**
   - `legacyLocation` contains `src/services/` or `src/controllers/` → **Service/Controller Module**
   - If `legacyWebHandler` field is present → **In-process service module**
3. Read `{endpoint_dir}/functional-spec.md` — note Purpose, Inputs table, Outputs JSON, Gherkin scenarios, business rules. These are your baseline; the description must not contradict them, only deepen them.
4. Read `{endpoint_dir}/call-tree.json` — note entry point method and signature, every call node, all `db` ops.
5. Read `{endpoint_dir}/database-dependencies.json` — note all tables, operations, columns.
6. **Write `{endpoint_dir}/functional-description.in-progress.md`** with the template header:
   ```
   # Functional Description: {name}
   > **Entry Point**: {key}
   > **Location**: {legacyLocation}
   > **Type**: API / {Express Route Handler | Service Module}
   > **Domain**: {domain}
   > **Legacy method**: {legacyEntryPoint}
   > **Web handler**: {legacyWebHandler}    ← only for in-process
   ```

---

### Phase 2: Read Source Files

**For Express Route Handler:**
1. Read `./source/{legacyLocation}` — extract:
   - Route registration: HTTP verb, exact path string, middleware applied (auth, multer, validation)
   - Handler function body: every step, each service called, guard clauses, return values
   - Imported dependencies (services, middleware, repositories)
2. Find and read companion request/response type files or JSDoc types referenced in the handler.
3. For each call in `call-tree.json` with a `file` field, read `./source/{file}`:
   - Repository files: confirm which entity properties are filtered/selected
   - Service method files: understand what domain mutations happen

**For Service/Controller Module:**
1. Read `./source/{legacyLocation}` — find the specific function matching `key`. Extract:
   - Function signature (parameters, return type)
   - Guard clauses and their conditions
   - Every repository call and what it does
   - Conditional branches (create-if-not-exists, increment-if-exists, etc.)
2. Read `./source/{call-tree.legacyWebHandler.file}` — find the route handler. Extract:
   - What it does BEFORE calling the service (validation, auth resolution, null guards)
   - What parameters it constructs for the service call
   - What it does AFTER the service call (status code, redirect, error handling)
3. For each ORM model file in `call-tree.json`, read `./source/{file}` — understand schema, constraints, and which columns are actually written.

---

### Phase 3: Write All Sections

Write each section to `functional-description.in-progress.md` as it is completed — do not batch.

**Section order:**
1. Executive Summary
2. REST Contract (HTTP Request → Query Params or Request Body → Success Response → Error Responses)
3. Business Logic (Overview → Validation Rules → Call Sequence)
4. Component Details (Express Route Handler section -or- In-process Service section based on type)
5. Database Dependencies
6. Security Considerations
7. Performance Notes
8. Migration Notes
9. Analysis Notes

**Express Route Handler emphasis:**
- REST Contract is the primary deliverable — fill every field from route registration and request/response types
- Call Sequence is a direct walkthrough of the handler function body
- Migration Notes covers: `await sleep(200)` removal, `fileUri` rewriting, DTO mapping

**In-process service emphasis:**
- Component Details must document BOTH the service method AND the route handler's pre/post-call logic
- Call Sequence should trace: route handler pre-call → service method → repository calls
- Migration Notes is especially important — the .NET target REST endpoint must replicate the route handler's pre-call logic (identity resolution, file validation) inside the handler, not just the service method logic

---

### Phase 4: Finalise

1. Review: all Gherkin scenarios from `functional-spec.md` are reflected somewhere in Business Logic.
2. Review: all tables from `database-dependencies.json` appear in the Database Dependencies table.
3. Review: `targetRestContract` fields from `metadata.json` are fully reflected in the REST Contract section.
4. Review: any `await sleep(200)`, DTO mapping usage, file-source concerns, or domain guard clauses are captured in Performance Notes, Migration Notes, or Analysis Notes.
5. Rename: `functional-description.in-progress.md` → `functional-description.md`

---

## Implementation Workflow

### Step 1: Parse Parameters
Read `key` and `endpoint_dir` from `{{PROMPT}}`.

### Step 2: Idempotency Check
If `{endpoint_dir}/functional-description.md` exists → stop immediately.

### Step 3: Read All Artifacts
Read `metadata.json`, `functional-spec.md`, `call-tree.json`, `database-dependencies.json` from `endpoint_dir`.

### Step 4: Detect Entry Point Type
From `legacyLocation` in `metadata.json`: `src/routes/` or `src/api/` → Express Route Handler; otherwise → Service/Controller Module.

### Step 5: Write In-Progress File
Create `{endpoint_dir}/functional-description.in-progress.md` with the header block.

### Step 6: Read Source Files
- Express Route Handler: route file + companion type files + repository and service files from call tree
- In-process: service method file + route handler caller file + ORM model files

### Step 7: Write All Sections
Write sections 1–9 incrementally to the in-progress file as each is completed.

### Step 8: Rename to Final
`mv {endpoint_dir}/functional-description.in-progress.md {endpoint_dir}/functional-description.md`

### Step 9: Report Summary
```
Key:              {key}
Entry point type: {Express Route Handler | Service/Controller Module}
HTTP contract:    {METHOD} {path}
Auth required:    {yes | no}
DB tables:        {list}
Source files read: {count}
Output:           {endpoint_dir}/functional-description.md
```

---

## Worked Examples

### Example 1: Express Route Handler GET — `list-documents-paged`

**Input:**
```
key=list-documents-paged
endpoint_dir=/path/docs/entry-points/api-endpoints/list-documents-paged
```

**Entry point type:** Express Route Handler (`legacyLocation` = `src/routes/documents.js`)

**Artifacts read:** `metadata.json` (Express route handler, domain=documents, no `legacyWebHandler`), `functional-spec.md` (4 Gherkin scenarios), `call-tree.json` (2 repository calls + uriComposer call), `database-dependencies.json` (documents: select + count)

**Source files read:** `src/routes/documents.js`, JSDoc type files for request/response shapes, `documentRepository.js`, `uriComposer.js`

**REST Contract:** `GET /api/documents` with 4 optional query params; JWT auth required

**Call Sequence:** COUNT query for `pageCount` → paginated SELECT → URI rewrite per document → DTO mapping → return response

**Key Migration Notes:**
- `await sleep(200)` in handler — **do NOT carry over to .NET**
- `fileUri` rewriting via `uriComposer` — implement equivalent in .NET
- `pageSize=0` → return all documents — preserve or explicitly change

**Key Analysis Notes:**
- Manual DTO mapping via object spread; read response shape to confirm which fields appear in response
- `pageCount` calculation when `pageSize=0` should be clarified in business rules

---

### Example 2: In-process service POST — `upload-document`

**Input:**
```
key=upload-document
endpoint_dir=/path/docs/entry-points/api-endpoints/upload-document
```

**Entry point type:** Service/Controller Module (`legacyLocation` = `src/services/documentService.js`, `legacyWebHandler` field present)

**Artifacts read:** `metadata.json` (in-process, domain=documents, `legacyWebHandler=POST /api/documents route handler`), `functional-spec.md`, `call-tree.json` (documents insert, document_versions insert), `database-dependencies.json`

**Source files read:** `documentService.js` (uploadDocument method), `src/routes/documents.js` (POST route handler), ORM model files for Document and DocumentVersion

**REST Contract:** `POST /api/documents` with multipart body `{title, file, tags}`; JWT auth required

**Component Details covers BOTH:**
- Service method: document creation, version insertion, repository calls
- Route handler pre-call: file presence check, title validation, JWT userId resolution

**Key Migration Notes:**
- File must be validated server-side in .NET — never from request URL
- JWT user identity: `req.user` from auth middleware becomes `User.FindFirst(ClaimTypes.NameIdentifier)` in .NET

**Key Analysis Notes:**
- Document file-size guard enforced by multer — .NET target should return HTTP 400 for oversized files
- Document soft-delete: `status='deleted'` is set rather than hard-deleting — note its existence

---

## Important Notes

1. **The REST Contract section is the .NET/Angular developer's primary reference.** Every field from `targetRestContract` in `metadata.json` must appear here, enriched with the detail from source reads. A vague REST Contract causes rework in the develop phase.

2. **In-process services: document the route handler's pre-call logic explicitly.** The service method alone is not the complete picture. The route handler performs meaningful work before calling it — file validation, identity resolution. The .NET REST endpoint must replicate that logic inside its handler. Capture it fully in Component Details and Migration Notes.

3. **Do not contradict `functional-spec.md`.** The Gherkin and business rules already written there are correct. The description deepens them — it does not change their meaning.

4. **Source path resolution.** All source files are at `./source/{path}` relative to cwd. If `call-tree.json` lists `src/services/documentService.js`, read it from `./source/src/services/documentService.js`.

5. **Migration Notes is the most important section for preventing .NET bugs.** Always check for and document:
   - `await sleep(200)` — **do NOT carry over**
   - File validation pattern — must happen server-side
   - Lazy creation — replicate the idempotency semantics
   - `fileUri` rewriting — implement equivalent in .NET
   - JWT user identity — understand auth middleware to `[Authorize]` + claims mapping

6. **Performance Notes is where DTO mapping usage is flagged.** .NET/Angular developers may not realise the legacy code is doing object-to-DTO mapping and that specific fields are projected. Note which fields the DTO includes.

7. **Write incrementally.** Write each section to the `.in-progress.md` file as you complete it. Do not draft the entire document in memory and write once at the end — long analyses can be interrupted.

8. **`legacyWebHandler` in metadata.json is the signal for in-process services.** Its `file` field (from `call-tree.json`) gives you the exact route handler file to read. Use it.
