# Functional spec — Document List

**Key:** `document-grid-document-list`
**URL:** `/` (panel within the Document Grid component)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (panel: lines 1025–1031; card render: lines 865–905; list-row render: lines 907–933)

## Purpose

Displays the set of documents that remain after the user's active filter and sort settings are applied. The panel is the primary read surface of the application: authenticated users see their stored documents as either card tiles (grid mode) or compact rows (list mode), and can open any document for preview by clicking it.

## Functional behavior

### componentDidMount — initial data load

1. Calls `this.loadDocuments()`.
2. `loadDocuments()` sets `state.loading = true` and `state.error = null`.
3. Calls `fetchDocuments()` → `GET /api/documents`.
4. On success: sets `state.documents = response.data.documents` (array) and `state.loading = false`.
5. On error: sets `state.error = err.response?.data?.error || 'Failed to load documents'` and `state.loading = false`.

### handleSearch(query) — search-driven data load

1. Called when the controls-bar search input emits a non-empty query.
2. If `query.trim()` is empty, falls back to `loadDocuments()` (restores full list).
3. Otherwise, sets `state.loading = true` and calls `searchDocuments(query)` → `GET /api/search?q={query}`.
4. On success: replaces `state.documents` with `response.data.results` (search result array).
5. On error: sets `state.error = err.response?.data?.error || 'Search failed'`.
6. Server-side search uses `ILIKE '%{query}%'` on `name` only; tag matching is client-side.

### render() — panel state machine (lines 1025–1031)

`render()` computes `displayDocs` by applying `filterDocuments(documents, filters)` then `sortDocuments(result, sortBy)` to `state.documents`. The panel renders one of four mutually exclusive states:

1. **Loading:** `state.loading === true` → renders "Loading documents..." text inside a centered container.
2. **Error:** `state.loading === false && state.error !== null` → renders `renderError()`: error message text + "Retry" button that calls `loadDocuments()`.
3. **Empty:** `!loading && !error && displayDocs.length === 0` → renders `renderEmpty()`: 📂 icon, "No documents found" heading, "Upload a document to get started" hint.
4. **Populated:** `!loading && !error && displayDocs.length > 0` → renders a `<div>` with `styles.grid` or `styles.list` layout; maps `displayDocs` through `renderCard(doc)` (grid mode) or `renderListRow(doc)` (list mode).

### renderCard(doc) — grid mode card (lines 865–905)

1. Applies `styles.cardSelected` if `state.selectedDocument?.id === doc.id`, else `styles.card`.
2. Header row: file icon emoji via `getFileIcon(doc.file_type)` + truncated `doc.name` (h3); 🏷️ tag-edit button (opens tag editor modal via `handleOpenTagEditor`).
3. Type line: `getFileTypeLabel(doc.file_type)` — human-readable string (e.g. "PDF Document").
4. Date line: `formatDate(doc.uploaded_at)` — formatted upload timestamp.
5. Preview link: `<span>Preview</span>` rendered only when `isPreviewable(doc.file_type)` is true (PDF, JPEG, PNG). Clicking the card (not specifically the span) triggers `handleDocumentClick` which opens the PreviewPanel.
6. Tags: if `doc.tags && doc.tags.length > 0`, renders tag pills; otherwise renders "No tags" in italic.

### renderListRow(doc) — list mode row (lines 907–933)

1. Applies `styles.listRowSelected` if selected, else `styles.listRow`.
2. Left: file icon emoji.
3. Center info block: `doc.name` (bold); meta line = `{typeLabel} · {formattedDate}` with ` · {N} tags` appended when tags are present.
4. Right: 🏷️ tag-edit button.

### Client-side filter and sort

`filterDocuments(documents, filters)` (line 485):
- `filters.fileType`: exact match on `doc.file_type`; empty string = no filter.
- `filters.searchQuery`: case-insensitive substring match on `doc.name` OR any element of `doc.tags`; empty string = no filter.

`sortDocuments(docs, sortBy)` (line 468):
- `'date'` (default): descending by `uploaded_at`.
- `'name'`: ascending by `name` via `localeCompare`.
- `'type'`: ascending by `file_type` via `localeCompare`.

## Acceptance criteria

```gherkin
Scenario: Full document list loads and displays in grid mode
  Given the user is authenticated
  And GET /api/documents returns [{ id, name, file_type, tags, uploaded_at }, ...]
  When the Document Grid component mounts
  Then each document appears as a card tile
  And each card shows the file icon, name, type label, upload date, and tag pills

Scenario: Empty document vault shows empty state
  Given GET /api/documents returns an empty array
  When the Document Grid component mounts
  Then the panel shows the 📂 icon
  And the text "No documents found" is visible
  And the hint "Upload a document to get started" is visible

Scenario: Loading state is shown while fetch is in flight
  Given the Document Grid has just mounted
  When GET /api/documents has not yet responded
  Then the panel shows "Loading documents..."
  And no document cards are rendered

Scenario: API error shows error state with Retry button
  Given GET /api/documents returns HTTP 500
  When the Document Grid component mounts
  Then an error message is displayed
  And a "Retry" button is visible
  And clicking Retry calls GET /api/documents again

Scenario: User switches from grid to list view
  Given documents are loaded and displayed in grid mode
  When the user clicks the view-toggle button
  Then documents re-render as compact list rows
  And each row shows the file icon, name, and type+date+tag-count meta line

Scenario: Client-side file type filter narrows the list
  Given documents include PDF and JPEG files
  When the user selects "PDF" from the type filter dropdown
  Then only documents with file_type="application/pdf" appear
  And the document count subtitle updates to reflect the filtered count

Scenario: Client-side text filter matches on name and tags
  Given documents include one named "Invoice Q3" with tag "finance"
  When the user types "fin" in the filter input
  Then the "Invoice Q3" document appears in the list
  And documents without "fin" in name or tags are hidden

Scenario: Search query replaces document list with server results
  Given the user types "contract" in the search input
  When GET /api/search?q=contract returns two results
  Then the document list shows exactly those two results
  And the document count subtitle reflects 2 documents

Scenario: Clearing search query restores full document list
  Given a search for "contract" is active showing 2 results
  When the user clears the search input
  Then GET /api/documents is called
  And the full document list is restored

Scenario: Document with null tags shows "No tags" in grid mode
  Given a document has tags=null (uploaded via trigger, not directly)
  When it is rendered in grid mode
  Then the card shows "No tags" in italic instead of tag pills
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Loading text ("Loading documents...") | conditional text | `DocumentGrid.jsx:1016-1020` |
| Error message text | conditional text | `DocumentGrid.jsx:948-950` |
| Retry button | conditional button | `DocumentGrid.jsx:951-953` |
| Empty-state 📂 icon | conditional emoji/span | `DocumentGrid.jsx:939` |
| Empty-state "No documents found" | conditional text | `DocumentGrid.jsx:940` |
| Empty-state hint text | conditional text | `DocumentGrid.jsx:941` |
| Grid/list container `<div>` | layout container | `DocumentGrid.jsx:1026` |
| Document card (grid mode) | loop (`displayDocs.map`) | `DocumentGrid.jsx:865-905` |
| Card file icon + name (h3) | text + emoji | `DocumentGrid.jsx:876-884` |
| Card 🏷️ tag-edit button | button | `DocumentGrid.jsx:879-885` |
| Card file type label | text | `DocumentGrid.jsx:887` |
| Card upload date | text | `DocumentGrid.jsx:888` |
| Card "Preview" span | conditional span | `DocumentGrid.jsx:889-891` |
| Card tag pills | loop (conditional) | `DocumentGrid.jsx:892-900` |
| Card "No tags" text | conditional text | `DocumentGrid.jsx:901` |
| Document list row (list mode) | loop (`displayDocs.map`) | `DocumentGrid.jsx:907-933` |
| List row file icon | emoji/span | `DocumentGrid.jsx:917` |
| List row document name | text | `DocumentGrid.jsx:919` |
| List row meta line (type · date · tags) | text | `DocumentGrid.jsx:920-923` |
| List row 🏷️ tag-edit button | button | `DocumentGrid.jsx:925-931` |
| Status bar | text | `DocumentGrid.jsx:1037-1043` |

## Out of scope

- **Controls bar** (text filter input, type filter dropdown, sort control, view-toggle button, Refresh button): feature key `document-grid-controls`.
- **Upload area** (drag-and-drop + click-to-upload panel above the list): feature keys `document-grid-upload-area`, `document-grid-upload-drop`, `document-grid-upload-click`.
- **Tag editor modal** (inline modal opened by the 🏷️ button): feature key `document-grid-tag-editor-modal`.
- **Document selection → PreviewPanel**: the onClick on each card/row is feature key `document-grid-document-select`; the PreviewPanel itself is a separate component.
