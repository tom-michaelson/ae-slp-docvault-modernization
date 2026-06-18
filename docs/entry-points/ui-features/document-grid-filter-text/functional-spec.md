# Functional spec — Text Filter Input

**Key:** `document-grid-filter-text`
**URL:** N/A — client-side action within the Document Grid view; no route change
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 979–985, handler at line 600, filter logic at line 485)

---

## Purpose

The text filter input lets the user narrow the visible document list in real time by typing a query string. It operates entirely on the already-loaded `documents` array held in component state, performing a case-insensitive substring search against each document's filename and its associated tags. No network request is issued when the user types.

---

## Functional behavior

### onChange — text filter

1. User types into `<input type="text" placeholder="Filter..." />` at line 979.
2. `onChange` fires with `e.target.value` and calls `this.handleFilterChange({ searchQuery: e.target.value })` (line 984).
3. `handleFilterChange` (line 600) merges `{ searchQuery }` into `state.filters` via functional `setState`:
   ```js
   filters: { ...prevState.filters, ...filterUpdate }
   ```
4. React schedules a synchronous re-render.
5. During `render()` (line 965), `filterDocuments(documents, filters)` is called:
   - If `filters.searchQuery` is non-empty, each document `d` is kept only if:
     - `d.name.toLowerCase().includes(query)`, **OR**
     - `d.tags && d.tags.some(t => t.toLowerCase().includes(query))`
   - If `filters.searchQuery` is empty string (user cleared the box), the name/tag predicate is skipped and all documents pass.
6. The filtered array is passed to `sortDocuments` and then rendered as cards or list rows.
7. The status bar at line 1042 displays `{displayDocs.length} of {documents.length} documents`.

**No API call is made.** The document list is not re-fetched; only the in-memory array is re-filtered.

### Interaction with fileType filter

The text filter composes with the `fileType` dropdown (`state.filters.fileType`). `filterDocuments` applies the file-type predicate first, then the text predicate. Clearing the text box restores documents that match the active `fileType` filter (if any).

---

## Acceptance criteria

```gherkin
Scenario: Text filter narrows list by document name
  Given the document list is loaded with documents ["invoice.pdf", "photo.jpg", "report.pdf"]
  When the user types "invoice" in the Filter input
  Then only "invoice.pdf" is shown
  And the status bar reads "1 of 3 documents"

Scenario: Text filter matches tags case-insensitively
  Given a document "untitled.pdf" has tags ["Budget", "Finance"]
  When the user types "budget" in the Filter input
  Then "untitled.pdf" is shown in the result list

Scenario: Text filter is case-insensitive on document name
  Given a document named "Annual Report.pdf" exists
  When the user types "annual report" in the Filter input
  Then "Annual Report.pdf" is shown in the result list

Scenario: Clearing the filter restores the full list
  Given the user has typed "invoice" and the list shows 1 document
  When the user clears the Filter input
  Then all documents matching any active fileType filter are shown again

Scenario: Text filter with no matches shows empty state
  Given the document list contains ["invoice.pdf", "photo.jpg"]
  When the user types "zzznomatch" in the Filter input
  Then the empty state ("No documents found") is displayed
  And the status bar reads "0 of 2 documents"

Scenario: Text filter composes with file-type filter
  Given documents ["invoice.pdf" (PDF), "photo.jpg" (JPEG), "scan.pdf" (PDF)]
  And the fileType filter is set to "PDF"
  When the user types "invoice" in the Filter input
  Then only "invoice.pdf" is shown
  And "scan.pdf" is not shown (does not match name/tag query)
  And "photo.jpg" is not shown (excluded by fileType filter)

Scenario: Filter state is not persisted across navigation
  Given the user has typed "invoice" in the Filter input
  When the user navigates away and returns to the Document Grid
  Then the Filter input is empty
  And all documents are shown
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Filter text input | `<input type="text">`, controlled, `value={filters.searchQuery}` | `DocumentGrid.jsx:979-985` |
| Filter input placeholder | static text `"Filter..."` | `DocumentGrid.jsx:981` |
| Status bar document count | text: `{displayDocs.length} of {documents.length} documents` | `DocumentGrid.jsx:1042` |
| Empty state panel | conditional block rendered when `displayDocs.length === 0` and not loading/error | `DocumentGrid.jsx:1023` |
| Active filter indicator in status bar | conditional text ` · Filter: {filters.fileType}` (fileType filter, not text filter) | `DocumentGrid.jsx:1040` |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| File-type dropdown filter (`filters.fileType`) | `document-grid-filter-filetype` |
| View toggle (grid/list) | `document-grid-view-toggle` |
| Refresh button | `document-grid-refresh` |
| Full-text server-side search (calls `searchDocuments` API) | `app-workspace-search-bar` |
| Document card/list row rendering | `document-grid-card`, `document-grid-list-row` |
