# Functional spec — Document Grid — Filter by Type

**Key:** `document-grid-filter-type`
**URL:** `/` (rendered as a control inside `DocumentGrid`, which is the main application view)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx:986-995`

---

## Purpose

The file-type filter dropdown lets users narrow the document list to a single MIME type (PDF, JPEG, or PNG) with one interaction. It operates entirely on the client-side document cache — no server round-trip is made when the value changes. It is one of two simultaneous filters; the other is a free-text search (`filters.searchQuery`) evaluated in the same `filterDocuments()` pass.

---

## Functional behavior

### onChange — apply type filter

1. User selects an option in the `<select>` at `DocumentGrid.jsx:986`.
2. The synthetic event fires `this.handleFilterChange({ fileType: e.target.value })` (`DocumentGrid.jsx:989`).
3. `handleFilterChange` (`DocumentGrid.jsx:600`) calls `this.setState(prevState => ({ filters: { ...prevState.filters, fileType } }))`, merging the new value without disturbing `searchQuery`.
4. React schedules a re-render of `DocumentGrid`.
5. `render()` (`DocumentGrid.jsx:961`) destructures `state.filters` and calls `filterDocuments(documents, filters)` (`DocumentGrid.jsx:965`).
6. `filterDocuments` (`DocumentGrid.jsx:485–499`):
   - If `filters.fileType` is non-empty, retains only documents where `d.file_type === filters.fileType` (exact MIME string match).
   - If `filters.fileType` is `""` (the "All Types" option), skips the type predicate — all documents pass.
   - In the same pass, if `filters.searchQuery` is non-empty, further filters by checking whether `d.name.toLowerCase()` or any `d.tags` entry contains the query string.
7. The filtered array is then sorted by `sortDocuments()` and rendered in the current `viewMode` (grid or list).
8. The status bar (`DocumentGrid.jsx:1040`) shows `· Filter: <mimeType>` when a non-empty type filter is active.

### Initial data load (precondition for filter)

On `componentDidMount`, `loadDocuments()` (`DocumentGrid.jsx:543`) calls `fetchDocuments()` (`api.js:34`), which issues `GET /api/documents`. The Node.js backend executes `SELECT * FROM documents_v2 ORDER BY uploaded_at DESC` and returns `{ documents: [...] }`. This full list is stored in `state.documents` and is never re-fetched when the filter changes.

---

## Acceptance criteria

```gherkin
Scenario: Default state shows all documents
  Given the document grid has loaded with documents of mixed types
  When no type filter is selected (value is "")
  Then all documents are displayed regardless of file_type
  And the status bar shows no "Filter:" label

Scenario: Selecting "PDF" hides non-PDF documents
  Given the document grid contains 3 PDF and 2 JPEG documents
  When the user selects "PDF" from the type filter dropdown
  Then only the 3 PDF documents are visible
  And the status bar shows "· Filter: application/pdf"
  And no API call is made

Scenario: Selecting "All Types" after a filter restores full list
  Given the user has filtered to "PDF" (2 documents shown, 3 hidden)
  When the user selects "All Types" (value "")
  Then all 5 documents are visible again
  And the status bar Filter label disappears

Scenario: Type filter and text search are applied simultaneously
  Given the document grid contains documents:
    | name         | file_type        |
    | report.pdf   | application/pdf  |
    | photo.jpg    | image/jpeg       |
    | scan.pdf     | application/pdf  |
  When the user selects "PDF" and types "report" in the search box
  Then only "report.pdf" is displayed

Scenario: Filtering when no documents match shows empty state
  Given the document grid contains only JPEG documents
  When the user selects "PDF" from the type filter
  Then zero document cards are rendered
  And the empty-state element is shown ("No documents found")
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Type filter `<select>` | form select (controlled) | `DocumentGrid.jsx:986-995` |
| "All Types" option | `<option value="">` | `DocumentGrid.jsx:991` |
| "PDF" option | `<option value="application/pdf">` | `DocumentGrid.jsx:992` |
| "JPEG" option | `<option value="image/jpeg">` | `DocumentGrid.jsx:993` |
| "PNG" option | `<option value="image/png">` | `DocumentGrid.jsx:994` |
| Status bar filter label | conditional text `· Filter: {fileType}` | `DocumentGrid.jsx:1040` |
| Document count display | text `{displayDocs.length} of {documents.length} documents` | `DocumentGrid.jsx:1042` |

---

## Out of scope

| Feature | Reason |
|---|---|
| Free-text search input | Separate control (`filters.searchQuery`); own feature key `document-grid-filter-search`. |
| Document grid card / list row rendering | Separate rendering concern (`renderCard`, `renderListRow`). |
| View mode toggle (grid ↔ list) | Separate control in the same header bar; own feature key `document-grid-view-toggle`. |
| Refresh button | Triggers `loadDocuments()`; own feature key `document-grid-refresh`. |
| Upload drop zone | Separate drag-and-drop area; own feature key `document-grid-upload`. |
| Tag editor modal | Separate inline feature; own feature key `document-grid-tag-editor`. |
