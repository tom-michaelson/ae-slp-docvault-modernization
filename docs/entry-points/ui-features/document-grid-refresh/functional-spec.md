# Functional spec — Refresh Documents Button

**Key:** `document-grid-refresh`
**URL:** `GET /api/documents` (triggered on button click; no route change)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx:1003-1005` (button), `DocumentGrid.jsx:550-564` (loadDocuments), `DocumentGrid.jsx:612-614` (handleRefresh)

## Purpose

Lets the user manually reload the full document list from the server, discarding any
stale in-memory state. This is the only way (besides page load) to pick up documents
uploaded from another session or tab, since the grid does not poll. The same code path
is reused as the automatic post-error Retry action.

## Functional behavior

### handleRefresh — primary click handler (line 612)

1. User clicks the "↻ Refresh" button in the controls bar.
2. `handleRefresh()` calls `loadDocuments()` with no arguments.

### loadDocuments — data fetch (line 550)

1. Sets `state.loading = true` and `state.error = null` (clears any previous error).
2. Calls `fetchDocuments()` from `utils/api.js` — issues `GET /api/documents` with Bearer token from `localStorage['docvault_token']` if present.
3. Backend auth middleware checks for JWT, session, or API key; returns HTTP 401 if none match (and `DEV_SKIP_AUTH` is not `true`).
4. On HTTP 200: backend returns `{ documents: [...] }` from `SELECT * FROM documents_v2 ORDER BY uploaded_at DESC`.
5. Sets `state.documents = response.data.documents || []` and `state.loading = false`.
6. Client-side `filterDocuments()` and `sortDocuments()` re-run on the new array inside `render()`.
7. On HTTP error: sets `state.error = err.response?.data?.error || 'Failed to load documents'` and `state.loading = false`.

### Retry button (alternate entry point, line 951)

1. Rendered only when `state.error` is non-null (inside `renderError()`).
2. `onClick` fires `handleRefresh()` — identical execution path to the primary button.
3. On success: `state.error` is cleared and documents are displayed normally.

## Acceptance criteria

```gherkin
Scenario: Successful refresh replaces document list
  Given the document grid is showing a stale list of 3 documents
  And the server has 5 documents in documents_v2
  When the user clicks "↻ Refresh"
  Then the grid shows a loading indicator ("Loading documents...")
  And after the response the grid shows all 5 documents
  And the status bar reads "5 of 5 documents"

Scenario: Refresh clears active error state
  Given the document grid is showing an error "Failed to load documents"
  And the server is now healthy with 2 documents
  When the user clicks "↻ Refresh"
  Then the error panel is replaced by a loading indicator
  And after the response the grid shows the 2 documents

Scenario: Refresh when server returns 401 Unauthorized
  Given the user's JWT token has expired
  When the user clicks "↻ Refresh"
  Then the loading indicator appears briefly
  And the error panel appears with message "Authentication required" (or similar server error text)
  And a Retry button is displayed

Scenario: Retry button is functionally equivalent to Refresh
  Given the document grid is in error state
  When the user clicks the "Retry" button in the error panel
  Then loadDocuments() is called with the same logic as the Refresh button
  And on success the error is cleared and documents are shown

Scenario: Empty vault after refresh
  Given the documents_v2 table has no rows
  When the user clicks "↻ Refresh"
  Then after the response the grid shows the empty state:
       "📂 No documents found — Upload a document to get started"
  And the status bar reads "0 of 0 documents"

Scenario: Refresh while already loading (double-click)
  Given loadDocuments() is in-flight after the first click
  When the user clicks "↻ Refresh" again
  Then a second loadDocuments() call is issued (no debounce or guard in legacy code)
  And whichever response arrives last wins (last-write-wins race condition)
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Refresh button | `<button onClick={this.handleRefresh}>↻ Refresh</button>` | `DocumentGrid.jsx:1003-1005` |
| Loading indicator | Conditional `<div>` with "Loading documents..." text; shown when `state.loading === true` | `DocumentGrid.jsx:1016-1020` |
| Document count subtitle | `<p>` under header title; shows `N document(s)` or "Loading..." | `DocumentGrid.jsx:974-976` |
| Document grid | CSS grid of card tiles; re-renders after refresh with `displayDocs` | `DocumentGrid.jsx:1025-1031` |
| Document list | CSS flex column of list rows; alternate view mode | `DocumentGrid.jsx:1025-1031` |
| Empty state | `<div>` with 📂 icon and hint text; shown when `!loading && !error && displayDocs.length === 0` | `DocumentGrid.jsx:1023`, `DocumentGrid.jsx:936-944` |
| Error panel | `<div>` with error text; shown when `state.error` is non-null | `DocumentGrid.jsx:1012-1013`, `DocumentGrid.jsx:946-956` |
| Retry button | `<button onClick={this.handleRefresh}>Retry</button>` inside error panel | `DocumentGrid.jsx:951` |
| Status bar | Footer bar showing view mode, sort, filter, and document counts; updates after refresh | `DocumentGrid.jsx:1037-1043` |

## Out of scope

| Feature | Key | Notes |
|---|---|---|
| Text filter input | `document-grid-filter-text` | Filtering is purely client-side against already-loaded documents; no HTTP call |
| File type filter | `document-grid-filter-type` | Same — client-side only |
| Grid/list view toggle | `document-grid-view-toggle` | Pure UI state; no HTTP call |
| Upload area | `document-grid-upload-area` | Calls `POST /api/upload`; also invokes `loadDocuments()` on success, but the upload action itself is a separate feature |
| Tag editor modal | `document-grid-tag-editor-modal` | Calls `PUT /api/documents/{id}/tags`; separate feature |
