# Functional spec — Select Document

**Key:** `document-grid-document-select`
**URL:** N/A — client-side state change only; no route change on selection
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 589–593, 865–905, 907–934) + `frontend/src/components/PreviewPanel.jsx`

---

## Purpose

Allows the user to choose a document from the grid or list view in order to inspect it in the preview panel. Clicking any document card or row immediately highlights it and opens `PreviewPanel` beside the grid — the primary document-inspection workflow in the application.

---

## Functional behavior

### handleDocumentClick(doc)

Triggered by `onClick` on any document card (`renderCard`, line 873) or list row (`renderListRow`, line 915).

1. Calls `this.setState({ selectedDocument: doc })` on `DocumentGrid` — updates local selection state.
2. The clicked card re-renders with `styles.cardSelected` (grid view) or `styles.listRowSelected` (list view): border becomes `2px solid #0f3460`, background becomes `#f0f4ff`. Any previously selected document reverts to the default style automatically.
3. Calls `this.props.onDocumentSelect(doc)` — delegates to `App.handleDocumentSelect`.

### App.handleDocumentSelect(doc)

1. Calls `this.setState({ selectedDocument: doc, showPreview: true })`.
2. `showPreview: true` causes `<PreviewPanel document={selectedDocument} onClose={...} />` to be mounted in the render output.

### PreviewPanel render (triggered by mount/prop change)

1. Receives the `document` object (already fully populated from `DocumentGrid`'s document list — no metadata fetch).
2. Displays document name (header), MIME type, and file size from `document.file_type` and `document.file_size`.
3. Constructs `previewUrl = GET /api/documents/{id}/preview` via `getPreviewUrl(document.id)`.
4. **If `document.file_type === 'application/pdf'`:** renders `<Document file={previewUrl}>` (react-pdf), which triggers a browser fetch of the preview URL. Shows loading state while PDF loads; shows page count on success; shows error message on failure.
5. **If `document.file_type` starts with `image/`:** renders `<img src={previewUrl}>`. Browser fetches the URL; no loading state.
6. **Otherwise:** renders static text "Preview not available for this file type."
7. A **✕ Close** button calls `App.handleClosePreview()`, which sets `{ selectedDocument: null, showPreview: false }` and unmounts `PreviewPanel`. `DocumentGrid.state.selectedDocument` is **not** reset by the close action — the card/row retains its selected style until the user clicks another document or the grid re-renders.

---

## Acceptance criteria

```gherkin
Scenario: Selecting a document card highlights it and opens the preview panel
  Given the document grid is showing at least one document in grid view
  When the user clicks a document card
  Then the card border changes to 2px solid #0f3460 and background to #f0f4ff
  And PreviewPanel appears beside the grid showing the document name and file type
  And no route change occurs in the browser URL bar

Scenario: Selecting a document row in list view highlights it and opens the preview panel
  Given the document grid is showing at least one document in list view
  When the user clicks a document row
  Then the row border changes to 2px solid #0f3460 and background to #f0f4ff
  And PreviewPanel appears beside the grid showing the document name and file type

Scenario: Selecting a second document replaces the previous selection
  Given a document is already selected (highlighted)
  When the user clicks a different document
  Then the previously highlighted card/row reverts to default style
  And the newly clicked card/row receives the selected style
  And PreviewPanel updates to show the new document

Scenario: Selecting a PDF document triggers a preview fetch
  Given the user clicks a document whose file_type is "application/pdf"
  Then PreviewPanel renders the react-pdf <Document> component
  And the browser fetches GET /api/documents/{id}/preview
  And a page count is shown once loading completes

Scenario: Selecting an image document triggers an image preview
  Given the user clicks a document whose file_type starts with "image/"
  Then PreviewPanel renders an <img> with src pointing to GET /api/documents/{id}/preview

Scenario: Selecting a non-previewable document shows a static message
  Given the user clicks a document whose file_type is not PDF or image
  Then PreviewPanel shows "Preview not available for this file type."
  And no HTTP request is made to /api/documents/{id}/preview

Scenario: Closing the preview panel unmounts PreviewPanel but preserves card highlight
  Given a document is selected and PreviewPanel is visible
  When the user clicks the "✕ Close" button in PreviewPanel
  Then PreviewPanel is unmounted from the DOM
  And showPreview in App state becomes false
  And the document card/row in DocumentGrid retains its selected highlight style
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Document card (grid view) | clickable `<div>`, `onClick` → `handleDocumentClick` | `DocumentGrid.jsx:870–904` |
| Document row (list view) | clickable `<div>`, `onClick` → `handleDocumentClick` | `DocumentGrid.jsx:911–933` |
| Selected-card style | CSS-in-JS state toggle (`cardSelected`) — blue border + blue-tint bg | `DocumentGrid.jsx:125–133` |
| Selected-row style | CSS-in-JS state toggle (`listRowSelected`) — blue border + blue-tint bg | `DocumentGrid.jsx:177–185` |
| File icon (card/row) | text emoji from `getFileIcon(doc.file_type)` | `DocumentGrid.jsx:877, 917` |
| Document name (card) | `<h3>` with `getFileIcon` prefix, text-overflow ellipsis | `DocumentGrid.jsx:876–879` |
| File type label (card/row) | `<p>` / `<div>` via `getFileTypeLabel(doc.file_type)` | `DocumentGrid.jsx:887, 921` |
| Upload date (card/row) | `<p>` / `<div>` via `formatDate(doc.uploaded_at)` | `DocumentGrid.jsx:888, 921` |
| Tag chips (card) | `<span>` loop over `doc.tags`; shows "No tags" if empty | `DocumentGrid.jsx:892–902` |
| Tag count (list row) | inline text `· N tags` if `doc.tags.length > 0` | `DocumentGrid.jsx:922` |
| Preview link badge (card) | `<span>Preview</span>` — shown only when `isPreviewable(doc.file_type)` | `DocumentGrid.jsx:889–891` |
| PreviewPanel — header | `<span>` showing `document.name` + **✕ Close** button | `PreviewPanel.jsx:99–103` |
| PreviewPanel — metadata | `<p>` for `document.file_type`; conditional `<p>` for `file_size` (formatFileSize) | `PreviewPanel.jsx:105–108` |
| PreviewPanel — PDF viewer | `<Document>` + `<Page>` (react-pdf), page counter | `PreviewPanel.jsx:110–127` |
| PreviewPanel — image viewer | `<img src={previewUrl}>` | `PreviewPanel.jsx:129–133` |
| PreviewPanel — no-preview message | static `<p>` "Preview not available for this file type." | `PreviewPanel.jsx:135–137` |
| PreviewPanel — empty state | `<div>` "Select a document to preview" — shown when `document` prop is null | `PreviewPanel.jsx:85–91` |

---

## Out of scope

| Feature | Reason |
|---|---|
| Tag editor (🏷️ button on card/row) | Separate feature; its `onClick` calls `handleOpenTagEditor(e, doc)` with `e.stopPropagation()` to prevent document selection from firing simultaneously — `document-grid-document-list` or a dedicated tag-editor feature key covers it |
| View mode toggle (grid ↔ list) | Covered by `document-grid-view-toggle` |
| Document list loading and filtering | Covered by `document-grid-document-list` and `document-grid-filter-*` features |
