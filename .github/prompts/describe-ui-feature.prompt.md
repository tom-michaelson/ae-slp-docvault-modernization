# Describe UI Feature

Produce a detailed technical narrative (`functional-description.md`) for a React/Node.js UI feature. This document describes **how the legacy feature works** — field names from source code, handler logic, service calls, visual states, and workflows — in enough detail for a Business Analyst to extract formal business requirements without reading the original TypeScript/JavaScript source.

This is a **discover-phase** command. It reads the artifacts already written by `analyze-ui-feature` plus the actual source files, and enriches them into a structured developer-facing description.

**Pipeline position:**
```
analyze-ui-feature  →  functional-spec.md, call-tree.json, metadata.json
take-screenshot     →  screenshots/
describe-ui-feature →  functional-description.md          ← this command
create-functional-spec-ui  →  functional-spec.md (enriched)
```

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<feature-key>  feature_dir=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | The feature key (e.g., `basket-view-page`) |
| `feature_dir` | Absolute path to the feature folder (e.g., `.../docs/entry-points/ui-features/basket-view-page`) |

Source files are resolved from `./source/{location}` relative to cwd (`target_repo/`), using the `location` field in `{feature_dir}/metadata.json`.

**Examples:**

```
key=basket-view-page
feature_dir=/abs/path/docs/entry-points/ui-features/basket-view-page
```

```
key=homepage-catalog-list
feature_dir=/abs/path/docs/entry-points/ui-features/homepage-catalog-list
```

---

## Idempotency

- If `{feature_dir}/functional-description.md` already exists → **stop immediately**. The analysis is complete.
- If `{feature_dir}/functional-description.in-progress.md` exists → a previous run crashed. **Overwrite it** and re-run the full analysis.
- Otherwise → proceed with full analysis.

---

## Inputs Read by This Command

From `{feature_dir}/`:

| File | What to extract |
|---|---|
| `metadata.json` | `key`, `name`, `elementType`, `uri`, `location`, `logic`, `domain`, `notes` |
| `functional-spec.md` | Purpose, Gherkin scenarios, business rules, inputs/outputs tables already written |
| `call-tree.json` | Handler entry points, service calls, DB operations |
| `database-dependencies.json` | Tables, columns, operations |
| `screenshots/*.png` | Visual reference of the legacy UI (if present) |

From `./source/` (cwd-relative):

| Resolved from | What to read |
|---|---|
| `./source/{location}` | The React component `.tsx` / `.jsx` file |
| `./source/{logic}` | The companion hook `.ts` or service file (if `logic` field present in metadata) |
| Child components referenced in JSX | `./source/src/components/*.tsx` or adjacent component files |
| Services in `call-tree.json` | `./source/{file}` for each service/hook implementation node |

---

## Output

```
{feature_dir}/functional-description.md
```

Written incrementally via:
1. Create `{feature_dir}/functional-description.in-progress.md` at Phase 1
2. Write each section as it is completed
3. Rename to `functional-description.md` at Phase 5 (final step)

---

## Output Template

```markdown
# Functional Description: {name}

> **Entry Point**: {key}
> **Location**: {location}
> **Type**: UI / {Page | Panel | Form}
> **Domain**: {domain}
> **Legacy URL**: {uri}

## Executive Summary

[2–3 paragraphs covering:
1. What task this page enables for the user
2. The main handlers/operations and how they interact
3. Any non-obvious aspects (anonymous vs auth, cookie tracking, lazy creation, etc.)]

## User Inputs

### Form Fields

[Table of all input fields the user can interact with. Use TypeScript property names from
controlled inputs, `useState`, `useFormik`, or React Hook Form — these are the authoritative
field names for the downstream create-functional-spec-ui command.]

| Field Name | TS Type | Source | Required | Notes |
| --- | --- | --- | --- | --- |
| `documentId` | string | controlled input / `useState` | yes | Document to act on |
| `quantity` | number | form state / `useFormik` or React Hook Form | yes | Min 0 |

### User Interactions

[Buttons, links, and form submits. Reference the handler or route they invoke.]

| Interaction | Element | Handler / Target | Trigger |
| --- | --- | --- | --- |
| Upload document | `<button type="submit">Upload</button>` | `handleUploadSubmit` | Form submit |
| View details | `<Link to="/documents/:id">` | `/documents/:id` | Navigation |
| Delete document | `<button onClick={handleDelete}>` | `handleDelete` via `documentService.delete` | Click handler |

### URL / Route Parameters

[Query string params and route segments that reach this page.]

| Parameter | Source | Optional | Default | Notes |
| --- | --- | --- | --- | --- |
| `page` | Query string (`useSearchParams`) | yes | 1 | 1-indexed page number |
| `filter` | Query string | yes | '' | Text search filter |

### Browser / Session Inputs

[Cookie reads, localStorage/sessionStorage, React auth context consumed on load.]

| Source | Data | Purpose |
| --- | --- | --- |
| localStorage / sessionStorage | Auth token | Session persistence |
| React auth context (`useAuth`) | User identity | Authenticated user identity |

---

## Outputs

### Rendered Content

[What the page renders for the user. Include loops, conditionals, and partials.
Reference the source file and line numbers.]

| Content Area | Description | Condition | Source ref |
| --- | --- | --- | --- |
| Empty state message | "No documents found." + Upload link | `documents.length === 0` | `DocumentList.tsx:50` |
| Documents table | Rows for each document (title, date, status, actions) | Documents loaded | `DocumentList.tsx:55–70` |
| Loading spinner | Spinner component while fetching | `isLoading === true` | `DocumentList.tsx:45` |
| Pagination controls | Page nav buttons | `totalPages > 1` | `DocumentList.tsx:80` |
| Upload button | Link to `/documents/upload` | Always | `DocumentList.tsx:22` |

### Navigation / Routing

[Redirects and links with business conditions.]

| Trigger | Destination | Condition |
| --- | --- | --- |
| Submit with null documentId | `/documents` (stay on page with error) | `documentId == null` |
| Upload success | `/documents` (redirect back to list) | Upload complete |
| Detail link | `/documents/:id` | User clicks row |

### State Changes

[localStorage writes, React context updates, and side effects triggered by this page.]

| State | Change | Trigger | Notes |
| --- | --- | --- | --- |
| Auth token | Stored in localStorage on login | Login action | JWT expiry managed by auth service |
| `Documents` row | Inserted | handleUploadSubmit, on successful upload | Created via documentService.uploadDocument |

---

## API Dependencies

[Service methods called by this feature. Use names from call-tree.json.
"When called" = which handler calls it.]

### Service Calls

| Service Method | When Called | Data In | Data Out |
| --- | --- | --- | --- |
| `documentService.getDocuments` | On mount, on filter change | `{ page, filter }` | `{ documents, total }` |
| `documentService.uploadDocument` | handleUploadSubmit | `FormData` | `Document` |
| `documentService.deleteDocument` | handleDelete | `documentId` | (void, removes document) |

### Call Sequences

**On Mount:**
1. `useEffect` fires; call `documentService.getDocuments({ page, filter })`
2. Set `isLoading = true` before fetch; set `isLoading = false` after response
3. Populate `documents` state with response data; set `totalPages`

**On Submit (handleUploadSubmit):**
1. Receive `FormData` from upload form
2. If `documentId == null` → display validation error, stay on page
3. Call `documentService.uploadDocument(formData)` → returns created `Document`
4. On success: navigate to `/documents` (list page)

**On Filter Change (handleFilterChange):**
1. Update `filter` state with new value
2. Reset `page` to 1
3. Re-call `documentService.getDocuments({ page: 1, filter })` → refresh `documents` list

---

## State Management

[For React components: component state variables, props, custom hooks, and auth/session state.]

### Component State / Props

| State Variable | Type | Used In | Notes |
| --- | --- | --- | --- |
| `documents` | `Document[]` | render loop | Populated by useDocuments hook on mount |
| `filter` | `string` | filter input, API call | Controlled input; triggers re-fetch on change |
| `isLoading` | `boolean` | loading spinner | Set true before fetch, false after |

### Auth / Session State

| Name | Read in | Written in | Purpose |
| --- | --- | --- | --- |
| Auth token (localStorage) | On mount (useAuth hook) | Login action | Identifies authenticated user |
| `currentUser` (React context) | Component render | Auth context provider | Drives user-specific data filtering |

---

## Component Details

### Component: `DocumentList`

**File**: `src/pages/DocumentList.tsx`

**Hooks used**: `useDocuments`, `useAuth`, `useNavigate`

**Event handlers**:
- `handleFilterChange(value)` — updates filter state; triggers re-fetch
- `handlePageChange(page)` — updates page state; triggers re-fetch
- `handleDelete(documentId)` — calls documentService.deleteDocument; refreshes list

**Child components**:
- `<DocumentRow>` — renders a single document row
- `<Pagination>` — page navigation controls
- `<EmptyState>` — shown when documents array is empty

### Component Template: `DocumentList.tsx`

**Key JSX sections**:
- Loading spinner (`isLoading && <Spinner />`)
- Empty-state block (`documents.length === 0 && <EmptyState />`)
- Documents table (`documents.map(doc => <DocumentRow key={doc.id} doc={doc} />)`)
- Pagination controls (`<Pagination page={page} total={totalPages} onChange={handlePageChange} />`)
- Upload button (link to `/documents/upload`)

### Child Components Included

| Component | Location | What it renders |
| --- | --- | --- |
| `<DocumentRow>` | `src/components/DocumentRow.tsx` | Document row with title, date, status, action buttons |
| `<Pagination>` | `src/components/Pagination.tsx` | Page navigation bar |
| `<EmptyState>` | `src/components/EmptyState.tsx` | Empty state message and upload CTA |

---

## Workflows

### Workflow 1: Browse Documents (On Mount)

**Use case**: User opens the document list to review available documents.

**Preconditions**: Authenticated user navigates to `/documents`.

**Steps**:

1. **Resolve user identity**
   - Code: `useAuth()` hook
   - Reads auth token from localStorage; sets `currentUser` in React context

2. **Fetch document list**
   - `useEffect` calls `documentService.getDocuments({ page: 1, filter: '' })`
   - `isLoading` set to `true` before fetch; set to `false` after response
   - Populates `documents` state; sets `totalPages`

3. **Render page**
   - If `isLoading`: show `<Spinner />`
   - If `documents.length === 0`: show `<EmptyState />` with Upload link
   - If documents present: render documents table with rows, pagination, and Upload button

**Success outcome**: Page renders with current document list (or empty-state message).

---

### Workflow 2: Upload Document (handleUploadSubmit)

**Use case**: User uploads a new document via the upload form.

**Preconditions**: User navigates to `/documents/upload` and submits the form.

**Steps**:

1. **Validate input**
   - If `documentId == null`: display validation error; stay on page

2. **Submit upload**
   - Call `documentService.uploadDocument(formData)` → returns created `Document`
   - `isLoading` set to `true` during upload

3. **Navigate on success**
   - On success: `useNavigate()` navigates to `/documents`
   - Document list re-fetches on mount showing newly uploaded document

**Success outcome**: Document uploaded; user redirected to list page with new document visible.

---

### Workflow 3: Delete Document (handleDelete)

**Use case**: User deletes a document by clicking the delete action button.

**Preconditions**: User is authenticated; document exists in the list.

**Steps**:

1. **Invoke delete**
   - `handleDelete(documentId)` calls `documentService.deleteDocument(documentId)`

2. **Refresh list**
   - On success: re-call `documentService.getDocuments({ page, filter })` to refresh `documents` state
   - If deleted item was last on current page: decrement `page` and re-fetch

**Success outcome**: Document removed from list; page re-renders with updated document set.

---

### Workflow 4: Filter by Keyword (handleFilterChange)

**Use case**: User types a keyword to narrow the document list.

**Preconditions**: User is on `/documents` page.

**Steps**:

1. **Update filter state**
   - `handleFilterChange(value)` updates `filter` state; resets `page` to 1

2. **Re-fetch documents**
   - `useEffect` dependency on `filter` triggers `documentService.getDocuments({ page: 1, filter })`
   - `isLoading` set to `true` during fetch

3. **Render filtered results**
   - If no matches: show `<EmptyState />`
   - If matches: render filtered documents table

**Success outcome**: Document list filtered to keyword matches; pagination resets to page 1.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
| --- | --- | --- |
| Initial page load | `<Spinner />` component | Shown while `isLoading === true`; hidden after data arrives |
| Upload in progress | Button disabled + spinner | Prevents double-submit during upload |

### Error States

| Error | Display | Recovery |
| --- | --- | --- |
| `documentId` null on submit | Inline validation error | User corrects and resubmits |
| API fetch failure | Error message banner | User retries or refreshes page |
| Delete failure | Toast notification | User retries delete action |

### Empty States

| Context | Message | Actions available |
| --- | --- | --- |
| No documents in list | "No documents found." | Upload button → `/documents/upload` |
| Filter returns no results | "No documents match your search." | Clear filter link |

### Success States

| Action | Feedback | Next state |
| --- | --- | --- |
| Upload document | Redirect to `/documents` | List re-renders with new document included |
| Delete document | List refreshes | Deleted document no longer visible |

---

## Use Cases

### UC-1: Browse documents

**User story**: As a user, I want to see all documents in the vault so I can find and manage my files.

**Workflow**: Workflow 1 (Browse Documents)

### UC-2: Upload a document

**User story**: As a user, I want to upload a new document so it is stored in the vault for later access.

**Workflow**: Workflow 2 (Upload Document)

### UC-3: Delete a document

**User story**: As a user, I want to delete a document so it is removed from the vault.

**Workflow**: Workflow 3 (Delete Document)

### UC-4: Filter by keyword

**User story**: As a user, I want to search documents by keyword so I can quickly find the file I need.

**Workflow**: Workflow 4 (Filter by Keyword)

---

## Security Considerations

### Authentication

- **Required**: Yes — authenticated users only. Auth token read from localStorage via `useAuth` hook.
- **Unauthenticated access**: React Router guard redirects to `/login` if no valid token found.
- **Token expiry**: Managed by auth service; expired tokens should trigger re-login redirect.

### Data Integrity

- **Critical**: Document metadata (owner, permissions) is validated server-side on upload. The POSTed `FormData` is not trusted for ownership — the .NET API derives owner from the authenticated JWT claim. This must be preserved in the Angular target.

### CSRF

- React SPA communicates via REST API calls with JWT Bearer tokens. Standard CSRF cookie patterns do not apply, but the .NET API must validate the `Authorization` header on all mutating endpoints.

---

## Accessibility Considerations

- Filter input uses a controlled `<input>` with `onChange` debounced — screen readers receive live-region updates if implemented.
- Empty-state and loading-spinner elements should carry appropriate `aria-live` or `role="status"` attributes.
- Upload and delete buttons should have descriptive `aria-label` attributes so screen readers can distinguish actions per document row.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
| --- | --- | --- |
| `Documents` API endpoint | Document list, metadata | Loading error banner shown; empty state displayed |
| Auth service (localStorage token) | User identity | Unauthenticated redirect to `/login` |
| `documentService.uploadDocument` | Upload result + new document | Error banner; user stays on upload form |

### Downstream

| System | What this page affects | How |
| --- | --- | --- |
| `/documents/upload` | User proceeds to upload | Link / button (navigation) |
| `/documents/:id` | User views document detail | React Router `<Link>` (navigation) |

---

## Analysis Notes

- Filter input triggers a re-fetch on every change (potentially debounced). The Angular target should implement debounce (e.g., 300 ms) to avoid excessive API calls.
- `handleDelete` refreshes the entire document list after deletion. The Angular target may optimistically remove the row from local state before the API confirms, then roll back on error.
- Auth token expiry handling: if the token expires mid-session, the API returns 401. The React app may not handle this gracefully — the Angular target should implement a global HTTP interceptor for 401 responses.
- `documentService.uploadDocument` uses `FormData` (multipart). The .NET API must accept `multipart/form-data`. Flag content-type handling for the API implementation team.
```

---

## Discovery Process

### Phase 0: Idempotency Check and Work Unit Type Detection

1. Check: does `{feature_dir}/functional-description.md` exist?
   - Yes → **stop**. Print "functional-description.md already exists for {key} — skipping."
   - No → continue.
2. Read `{feature_dir}/metadata.json`. Extract `elementType`:
   - `"ui-page"` → **Page** analysis focus (overall structure, all handlers, navigation)
   - `"ui-panel"` → **Panel** analysis focus (data display, selection, parent relationship)
   - `"ui-action"` → **Form/Modal** analysis focus (form fields, validation, submission)
3. Note the source file paths: `./source/{location}` and `./source/{logic}` (if present).

---

### Phase 1: Read Artifacts and Create In-Progress File

1. Read `{feature_dir}/metadata.json` — extract all fields.
2. Read `{feature_dir}/functional-spec.md` — note Gherkin scenarios, business rules, inputs/outputs already written. This becomes your baseline; the description must not contradict it.
3. Read `{feature_dir}/call-tree.json` — note all handler entry points, service methods called, DB ops.
4. Read `{feature_dir}/database-dependencies.json` — note all tables and operations.
5. Check `{feature_dir}/screenshots/` — list any `.png` files present.
6. **Write `{feature_dir}/functional-description.in-progress.md`** with the template header:
   ```
   # Functional Description: {name}
   > **Entry Point**: {key}
   > **Location**: {location}
   > **Type**: UI / {Page | Panel | Form}
   > **Domain**: {domain}
   > **Legacy URL**: {uri}
   ```

---

### Phase 2: Read Source Files

**For React Page Component:**
1. Read `./source/{location}` — the `.tsx`/`.jsx` component file. Extract `useEffect` hooks, event handlers, imported services/hooks, JSX structure.
2. If `logic` field present in metadata, read `./source/{logic}` — the companion hook file.
3. For each child component rendered in JSX, read that component file from `src/components/` (1 level deep).
4. Note every form `onSubmit`, button `onClick`, input `onChange`, and `<Link to="...">` / `useNavigate` call.

**For React Feature Component:**
1. Read `./source/{location}` — extract props interface, local state, imported hooks and services.
2. Identify callback props (`on*`) that delegate to parent component.
3. Follow child component imports one level deep.

**For React Container Component:**
1. Read `./source/{location}` — identify Redux `useSelector`/`useDispatch` or Context `useContext` calls.
2. Read the relevant Redux slice or context file.
3. Identify data-fetching hooks (`useQuery`, `useMutation` or similar).

---

### Phase 3: Screenshot Analysis (if screenshots present)

For each `.png` in `{feature_dir}/screenshots/`:

1. View the screenshot image.
2. Document:
   - **Screen state shown** (empty, loaded, form open, error, etc.)
   - **Content areas visible** (panels, forms, tables, empty states)
   - **Field labels** as displayed (note: these may differ from TypeScript property names — use TS names in Form Fields table, note display label discrepancies here)
   - **Buttons and actions visible**
   - **Required field indicators** (highlighted inputs)
3. Cross-reference with source analysis:
   - Does the screenshot show content that the source analysis found? ✓
   - Does the source analysis describe content not visible in the screenshot? (different state)
   - Are there display labels that look different from TypeScript property names? Flag in Analysis Notes.

---

### Phase 4: Write All Sections

Write each section to `functional-description.in-progress.md` as it is completed — do not wait until all sections are drafted before writing.

**For Page work units** (elementType = `ui-page`):
- Emphasize: all event handlers, full workflows for each handler, rendered content table, navigation/routing
- Include: URL/route parameters, auth/session inputs
- State Management: component state variables, auth/session state
- Component Details: React component class, child components, hooks and services used
- Visual States: loading state, error paths, redirect outcomes

**For Panel work units** (elementType = `ui-panel`):
- Emphasize: data display (columns/fields with TypeScript names), selection behavior, relationship to parent page
- De-emphasize: form fields (unless panel has inline editing)

**For Form/Modal work units** (elementType = `ui-action`):
- Emphasize: Form Fields table (every field with TypeScript name, type, required, validation), submission workflow, validation rules
- De-emphasize: page structure

**Section order** (follow the output template above):
1. Executive Summary
2. User Inputs (Form Fields → User Interactions → URL/Route Parameters → Browser/Session Inputs)
3. Outputs (Rendered Content → Navigation/Routing → State Changes)
4. API Dependencies (Service Calls → Call Sequences)
5. State Management (Component State/Props → Auth/Session State)
6. Component Details (React Component → Component Template → Child Components)
7. Workflows (one H3 per handler — write in full before moving to next)
8. Visual States (Loading → Error → Empty → Success)
9. Use Cases
10. Security Considerations
11. Accessibility Considerations
12. Integration Points
13. Analysis Notes

---

### Phase 5: Finalise

1. Review: all sections written, all Gherkin scenarios from `functional-spec.md` are reflected somewhere in the workflows or use cases.
2. Review: all component state variables and controlled input fields appear in the Form Fields / Component State tables with their TypeScript property names.
3. Review: all service methods from `call-tree.json` appear in the API Dependencies section.
4. Rename: `functional-description.in-progress.md` → `functional-description.md`

---

## Implementation Workflow

### Step 1: Parse Parameters
Read `key` and `feature_dir` from `{{PROMPT}}`.

### Step 2: Idempotency Check
If `{feature_dir}/functional-description.md` exists → stop.

### Step 3: Read All Artifacts
Read `metadata.json`, `functional-spec.md`, `call-tree.json`, `database-dependencies.json` from `feature_dir`. List screenshots if any.

### Step 4: Detect Work Unit Type
Use `elementType` from `metadata.json`.

### Step 5: Write In-Progress File
Create `{feature_dir}/functional-description.in-progress.md` with the header block.

### Step 6: Read Source Files
Read view template + companion hook from `./source/{location}` + `./source/{logic}`. Read referenced child components and service implementations.

### Step 7: Analyse Screenshots
If screenshots present, view and document each one.

### Step 8: Write All Sections
Write sections 1–13 of the output template incrementally.

### Step 9: Rename to Final
`mv {feature_dir}/functional-description.in-progress.md {feature_dir}/functional-description.md`

### Step 10: Report Summary
```
Key:           {key}
Work unit type: {Page | Panel | Form}
Handlers:      {list, e.g. On Mount, handleUploadSubmit, handleDelete, handleFilterChange}
Form fields:   {count of controlled input / state fields documented}
Workflows:     {count}
Use cases:     {count}
Screenshots:   {count analysed, or "none"}
Output:        {feature_dir}/functional-description.md
```

---

## Worked Examples

### Example 1: Page with multiple handlers — `document-list-page`

**Input:**
```
key=document-list-page
feature_dir=/path/docs/entry-points/ui-features/document-list-page
```

**Artifacts read:** `metadata.json` (elementType=ui-page), `functional-spec.md`, `call-tree.json` (4 handlers), `database-dependencies.json` (Documents, Users), `screenshots/document-list-empty.png`

**Source files read:** `./source/src/pages/DocumentList.tsx`, `./source/src/hooks/useDocuments.ts`, `./source/src/services/documentService.ts`, `./source/src/components/DocumentRow.tsx`

**Form fields documented:** `filter` (controlled input / useState), `documentId` (from delete handler)

**Workflows:** 4 (Browse Documents, Upload Document, Delete Document, Filter by Keyword)

**Key Analysis Notes:**
- Filter triggers re-fetch on every change — debounce recommended in Angular target
- Auth token read from localStorage; expired tokens return 401 — Angular HTTP interceptor needed
- Upload uses `FormData` multipart — .NET API must accept `multipart/form-data`

---

### Example 2: Read-only page with filter — `document-search-panel`

**Input:**
```
key=document-search-panel
feature_dir=/path/docs/entry-points/ui-features/document-search-panel
```

**Artifacts read:** `metadata.json` (elementType=ui-panel), `functional-spec.md`, `call-tree.json` (1 handler: On Mount), `database-dependencies.json` (Documents, Tags), `screenshots/document-search.png`

**Source files read:** `./source/src/components/DocumentSearchPanel.tsx`, `./source/src/hooks/useDocumentSearch.ts`, `./source/src/components/TagFilter.tsx`

**Form fields documented:** No form submission — `searchTerm` and `selectedTag` bind from query string (`useSearchParams`)

**URL/Route Parameters:** `searchTerm` (string?), `tag` (string?), `page` (number?, default 1)

**Workflows:** 1 (Load and filter documents)

**Key Analysis Notes:**
- Filter is applied via query string update — Angular target should use `Router.navigate` with `queryParams`.
- `<TagFilter>` child component emits `onTagChange` callback — included in rendered content but is a separate component concern.
- `documentService.getDocuments` composes absolute document URLs — Angular target must replicate URL composition logic.

---

## Important Notes

1. **Write incrementally.** Write each section to `functional-description.in-progress.md` as you complete it. Do not draft the entire document in memory and write once at the end — long analyses can be interrupted.

2. **Field names from TypeScript source, not display labels.** The `create-functional-spec-ui` command uses field names from this document as authoritative. Always use TypeScript state variable names (`documents`, `filter`, `documentId`) not display labels ("Document List", "Search", "Document ID") in the Form Fields table.

3. **Do not contradict `functional-spec.md`.** The Gherkin and business rules already written there are correct. Do not change their meaning — deepen them.

4. **Child components are in scope for rendered content.** A `<DocumentRow doc={doc} />` renders document rows that may contain delete/view actions. Include the child component's content in the Rendered Content table but note it is "via `<DocumentRow>` component" and mark downstream effects (the delete API call) as part of that component's concern.

5. **Auth token handling is security-relevant.** Always document localStorage reads and auth context usage explicitly in Browser/Session Inputs, State Changes, and Security Considerations. The .NET target needs this detail to implement equivalent authentication.

6. **One workflow per event handler.** Every significant `useEffect`, `onSubmit`, `onClick`, and filter change handler gets its own named Workflow section. Include the full step-by-step logic including branches and navigation.

7. **Analysis Notes is the place for technical debt and migration flags.** Anything that would surprise a .NET/Angular developer implementing the equivalent endpoint belongs here: missing debounce, optimistic UI patterns, auth expiry handling, multipart form handling.

8. **Source path resolution.** Source files are at `./source/{location}` relative to cwd. If a service file listed in `call-tree.json` has path `src/services/documentService.ts`, read it from `./source/src/services/documentService.ts`.
