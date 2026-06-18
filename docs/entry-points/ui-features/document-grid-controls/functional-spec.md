# Functional spec — Document grid header controls

**Key:** `document-grid-controls`
**URL:** N/A — panel rendered inside `DocumentGrid`; no dedicated route
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` lines 971-1007 (render controls block)

---

## Purpose

The header controls bar sits at the top of the `DocumentGrid` component and gives users four tools to manage how the document list is displayed: a text filter box, a file-type dropdown, a grid/list view toggle, and a Refresh button. It does not navigate away; all interactions update local component state or re-fetch the document list in place.

---

## Functional behavior

### handleFilterChange — text search filter

1. Fires on `onChange` of the text `<input>` at line 984.
2. Calls `this.handleFilterChange({ searchQuery: e.target.value })`.
3. `handleFilterChange` (line 600) merges the partial update into `this.state.filters` via `setState`.
4. On next render, `filterDocuments(documents, filters)` (line 485) is called with the updated `filters.searchQuery`.
5. `filterDocuments` performs a client-side case-insensitive substring match against `doc.name` and each element of `doc.tags`.
6. **No API call is made.** The full document list stays in `this.state.documents`.

### handleFilterChange — file-type filter

1. Fires on `onChange` of the `<select>` at line 986.
2. Calls `this.handleFilterChange({ fileType: e.target.value })`.
3. `handleFilterChange` merges `fileType` into `this.state.filters`.
4. On next render, `filterDocuments` filters by exact match on `doc.file_type`.
5. Empty string `""` (the "All Types" option) disables the file-type filter.
6. **No API call is made.**

### handleViewToggle — grid/list toggle

1. Fires on `onClick` of the toggle button at line 998.
2. Calls `this.handleViewToggle()` (line 606), which flips `this.state.viewMode` between `'grid'` and `'list'`.
3. The button label and title change to reflect the current mode (`'grid'` → shows `☰` / "Switch to list"; `'list'` → shows `⊞` / "Switch to grid").
4. The document list section at line 1026 re-renders using the appropriate `styles.grid` or `styles.list` layout.
5. **No API call is made.**

### handleRefresh — reload documents

1. Fires on `onClick` of the Refresh button at line 1003.
2. Calls `this.handleRefresh()` (line 612), which delegates to `this.loadDocuments()`.
3. `loadDocuments()` (line 550) sets `loading: true, error: null`, then `await fetchDocuments()`.
4. `fetchDocuments` (line 34, `utils/api.js`) sends `GET /api/documents` with the JWT Bearer token from `localStorage('docvault_token')`.
5. The Express route (`backend/src/routes/documents.js:10`) executes `SELECT * FROM documents_v2 ORDER BY uploaded_at DESC` and returns `{ documents: rows }`.
6. On success: `this.state.documents` is replaced with `response.data.documents`; `loading` is set to `false`.
7. On failure: `this.state.error` is set to `err.response?.data?.error || 'Failed to load documents'`; `loading` is set to `false`.
8. The document count in the subtitle (`<p>` at line 974) reflects the post-filter count from `displayDocs.length`, updated after the new state is set.

---

## Acceptance criteria

```gherkin
Scenario: Text search filters documents client-side
  Given the document list is loaded and contains documents named "Budget 2024" and "Project Plan"
  When the user types "budget" in the Filter input
  Then only "Budget 2024" is shown in the grid
  And no API call is made
  And the subtitle shows "1 document"

Scenario: Text search matches on tags as well as name
  Given a document named "Untitled" with tags ["budget", "q4"]
  When the user types "q4" in the Filter input
  Then "Untitled" is shown (tag match)

Scenario: File-type filter shows only selected type
  Given documents of types application/pdf and image/jpeg are loaded
  When the user selects "PDF" from the file-type dropdown
  Then only PDF documents are shown
  And no API call is made

Scenario: Selecting "All Types" removes the file-type filter
  Given the file-type filter is set to "PDF"
  When the user selects "All Types"
  Then all documents are shown again

Scenario: View toggle switches layout
  Given the view mode is "grid"
  When the user clicks the view-toggle button
  Then the layout switches to list view
  And the button label changes to "⊞" with title "Switch to grid"

Scenario: Refresh reloads documents from API
  Given the document list is showing stale data
  When the user clicks the Refresh button
  Then GET /api/documents is called
  And the document list is replaced with the fresh response
  And the subtitle count updates

Scenario: Refresh shows error when API fails
  Given the GET /api/documents endpoint returns a 500 error
  When the user clicks the Refresh button
  Then the error state is shown with the message from the response (or "Failed to load documents")
  And a Retry button is displayed

Scenario: Empty document list shows empty state
  Given GET /api/documents returns an empty array
  When the component renders
  Then the empty-state block "No documents found" is displayed
  And the subtitle shows "0 documents"

Scenario: Authentication token attached to refresh request
  Given a JWT is stored in localStorage key "docvault_token"
  When the user clicks Refresh
  Then the GET /api/documents request includes "Authorization: Bearer <token>"

Scenario: No token — request sent without Authorization header
  Given localStorage does not contain "docvault_token"
  When the user clicks Refresh
  Then GET /api/documents is called without an Authorization header
  And if the server returns 401, a console warning is logged but no redirect occurs
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| "Documents" heading | text `<h2>` | `DocumentGrid.jsx:973` |
| Document count subtitle | dynamic text `<p>` — shows "Loading..." or "{n} document(s)" | `DocumentGrid.jsx:974-976` |
| Filter text input | `<input type="text">` — client-side filter on name + tags | `DocumentGrid.jsx:979-985` |
| File-type dropdown | `<select>` — options: All Types, PDF, JPEG, PNG | `DocumentGrid.jsx:986-995` |
| View-mode toggle button | toggle `<button>` — icon/label changes per mode | `DocumentGrid.jsx:996-1002` |
| Refresh button | `<button>` — triggers GET /api/documents | `DocumentGrid.jsx:1003-1005` |

---

## Out of scope

The following features rendered within the same `DocumentGrid` component are **not** part of this feature key:

- **Document card grid / list rows** (`renderCard`, `renderListRow`) — belongs to `document-grid-view`
- **Upload drop zone** (`renderUploadArea`) — belongs to `document-upload`
- **Tag editor modal** (`renderTagEditor`) — belongs to `document-tag-editor`
- **Status bar** (lines 1037-1043) — belongs to `document-grid-status-bar`
- **Error / loading / empty states** (`renderError`, `renderEmpty`) — shared rendering helpers used by multiple features

---

## Implementation notes for Angular 19 + Spring Boot

1. **Client-side filtering:** The Angular component should hold the full document list in a signal or BehaviorSubject and derive the filtered/sorted view via `computed()` or a pipe. No HTTP call on filter change.
2. **Search input vs. search API:** The legacy component defines a `handleSearch` method (line 566) that calls `GET /api/search?q=` but it is **never wired to the filter input** — the input only updates `filters.searchQuery` for client-side matching. The Angular implementation should preserve this behavior unless the product decision is to switch to server-side search.
3. **View mode persistence:** Consider persisting `viewMode` in `localStorage` or a user-preference service so it survives navigation.
4. **Token storage:** The legacy app stores the JWT in `localStorage('docvault_token')`. The Spring Boot equivalent should use `HttpOnly` cookies or an `HttpInterceptor` pattern rather than raw `localStorage` access inside the API layer.
5. **documents_v2 vs documents:** The backend `GET /api/documents` reads from `documents_v2`, NOT the `documents` table. Uploads write to `documents` and a DB trigger copies rows to `documents_v2` — deliberately omitting `tags` during the copy (migration 003). The Spring Boot endpoint should read from the canonical table (consolidation of `documents` / `documents_v2` is a known tech-debt item).
