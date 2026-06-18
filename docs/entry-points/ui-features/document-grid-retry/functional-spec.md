# Functional spec — Retry on Error

**Key:** `document-grid-retry`
**URL:** N/A — no route change; clicking Retry triggers `GET /api/documents` in the background
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 946–956, 612–614, 550–564)

---

## Purpose

When the document list fails to load (network error, 5xx, timeout), a red error banner replaces the document grid. The Retry button lets the user re-trigger the full document fetch without reloading the page, clearing the error state immediately and showing a loading indicator while the request is in flight.

---

## Functional behavior

### onClick — retry document fetch

1. User clicks the **Retry** button rendered inside `renderError()` at `DocumentGrid.jsx:951`.
2. `handleRefresh()` (line 612) is invoked; it delegates unconditionally to `loadDocuments()` (line 550).
3. `loadDocuments()` calls `this.setState({ loading: true, error: null })` — the error banner disappears and the loading text appears instantly.
4. `fetchDocuments()` (`frontend/src/utils/api.js:37`) issues `GET /api/documents` via axios, attaching the `Bearer` token from `localStorage['docvault_token']` if present.
5. **Success path:** server returns `{ documents: [...] }`; component sets `state.documents` and `state.loading = false`. The grid re-renders with fresh data; any active client-side filters and sort are preserved in state and re-applied by `filterDocuments()` / `sortDocuments()` inside `render()`.
6. **Failure path:** catch block sets `state.error` to `err.response?.data?.error` or the fallback string `'Failed to load documents'`, and `state.loading = false`. The error banner reappears with the (potentially different) error message.

---

## Acceptance criteria

```gherkin
Scenario: Retry succeeds and documents are displayed
  Given the DocumentGrid is in error state with error "Failed to load documents"
  When the user clicks the Retry button
  Then state.loading is immediately set to true and state.error is cleared
  And a GET request is sent to /api/documents
  And on a 200 response the documents list is populated from response.data.documents
  And the error banner is no longer rendered
  And any previously active text/type filters are still applied to the refreshed list

Scenario: Retry fails again and error banner reappears
  Given the DocumentGrid is in error state
  When the user clicks Retry
  And the GET /api/documents request returns a 500 with body { "error": "Database unavailable" }
  Then state.error is set to "Database unavailable"
  And the error banner renders the message "Error: Database unavailable"
  And the Retry button remains visible

Scenario: Retry replaces a stale fallback error message with a new one
  Given the DocumentGrid shows error "Failed to load documents" (network timeout)
  When the user clicks Retry
  And the server responds with 500 { "error": "Server overloaded" }
  Then the error banner updates to "Error: Server overloaded"

Scenario: Retry is not visible when there is no error
  Given the DocumentGrid loaded successfully with documents
  Then the error container is not rendered
  And the Retry button is not present in the DOM
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Error container div | conditional block (`{error && this.renderError()}`) | `DocumentGrid.jsx:1013` |
| Error message paragraph | text — `"Error: {error}"` | `DocumentGrid.jsx:950` |
| **Retry button** | button — `onClick={this.handleRefresh}`, style `styles.errorRetry` (red background `#c62828`) | `DocumentGrid.jsx:951–953` |

---

## Out of scope

The following elements are visible on the same page render but belong to other feature keys:

| Feature | Key |
|---|---|
| Upload drop zone rendered above the error state | `document-grid-upload-area` |
| Grid/list header with Refresh (↻) button — a separate reload trigger | `document-grid-refresh` |
| Document card grid / list rows | `document-grid-document-list` |
| Filter text input and type select | `document-grid-filter-text` / `document-grid-filter-type` |
| View toggle (grid ↔ list) | `document-grid-view-toggle` |
| Tag editor modal | (part of `document-grid-document-list`) |
