# Functional spec — Document Preview Panel

**Key:** `app-workspace-preview-panel`
**URL:** Inline panel within the workspace (no dedicated route). Preview asset loaded via `GET /api/documents/{id}/preview`.
**Legacy source:** `frontend/src/components/PreviewPanel.jsx`

---

## Purpose

The Document Preview Panel displays the content of a selected document directly within the workspace without navigating away. It allows authenticated users to inspect a document's rendered content (PDF or image) and key metadata (name, MIME type, file size) before deciding to take further action. It is the primary in-app content viewer.

---

## Functional behavior

### render — empty state

1. When `document` prop is `null` or `undefined`, renders a centred placeholder message: "Select a document to preview".
2. No network requests are made in this state.

### render — document selected (PDF)

1. Receives `document` object (`{id, name, file_type, file_size}`) and `onClose` callback from parent `App`.
2. Constructs preview URL by calling `getPreviewUrl(document.id)` → `${API_BASE_URL}/documents/${id}/preview`.
3. Checks `document.file_type === 'application/pdf'` to enter PDF branch.
4. Renders react-pdf `<Document file={previewUrl}>` which initiates `GET /api/documents/{id}/preview`.
5. While loading: shows "Loading PDF..." paragraph.
6. On success (`onDocumentLoadSuccess`): sets `numPages` in state, clears `loading`, renders `<Page pageNumber={1} width={400} />` and page-count label "Page 1 of N".
7. On error (`onDocumentLoadError`): sets `error` string in state, renders red "Error: {message}" paragraph.
8. Header always shows document name and "✕ Close" button.
9. Metadata rows show `file_type`; `file_size` row is shown only when `document.file_size` is truthy (formatted via `formatFileSize()`).

### render — document selected (image)

1. Checks `document.file_type?.startsWith('image/')`.
2. Constructs preview URL via `getPreviewUrl(document.id)`.
3. Renders `<img src={previewUrl} alt={document.name} />` constrained to `maxWidth: 100%` / `maxHeight: 500px`.
4. No loading state — browser handles image fetch natively.
5. Header and metadata rows identical to PDF branch.

### render — document selected (unsupported type)

1. Neither PDF nor image condition is met.
2. Renders metadata rows then falls through to: "Preview not available for this file type."

### onClose (delegated to parent)

1. User clicks "✕ Close" button.
2. `onClose` prop callback fires → `App.handleClosePreview()`.
3. Parent sets `selectedDocument = null`, `showPreview = false` → `PreviewPanel` is unmounted.

---

## Acceptance criteria

```gherkin
Scenario: Empty state when no document is selected
  Given the workspace is loaded
  And no document has been selected
  Then the preview panel shows "Select a document to preview"
  And no network requests are made to the preview API

Scenario: PDF document renders with page count
  Given the user selects a document with file_type "application/pdf"
  When the preview panel mounts
  Then the panel header shows the document name
  And a GET request is made to /api/documents/{id}/preview
  And "Loading PDF..." is displayed while the request is pending
  When the PDF loads successfully with 5 pages
  Then "Loading PDF..." disappears
  And page 1 of the PDF is rendered at width 400px
  And the label "Page 1 of 5" is displayed

Scenario: PDF fails to load
  Given the user selects a document with file_type "application/pdf"
  When the preview panel mounts
  And the GET /api/documents/{id}/preview request fails
  Then a red error message is displayed: "Error: {error message}"
  And "Loading PDF..." disappears

Scenario: Image document renders inline
  Given the user selects a document with file_type "image/png"
  When the preview panel mounts
  Then the panel header shows the document name
  And an <img> is rendered with src pointing to /api/documents/{id}/preview
  And no "Loading..." text is shown

Scenario: Unsupported file type shows fallback
  Given the user selects a document with file_type "text/csv"
  When the preview panel mounts
  Then the panel shows "Preview not available for this file type."
  And no network request is made to the preview API

Scenario: File size metadata is hidden when absent
  Given the user selects a document with file_size null
  Then the "Size:" metadata row is not rendered

Scenario: Closing the panel dismisses it
  Given the preview panel is visible with a selected document
  When the user clicks "✕ Close"
  Then App.handleClosePreview() is called
  And showPreview is set to false
  And the preview panel is unmounted from the DOM

Scenario: Backend document not found
  Given the user selects a document whose id no longer exists in the database
  When GET /api/documents/{id}/preview is called
  Then the server responds with 404
  And the PDF branch shows "Error: {network/404 message}" in red
  And the image branch renders a broken-image placeholder (browser default)
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Empty-state message "Select a document to preview" | conditional text (`!document`) | `PreviewPanel.jsx:86-90` |
| Panel header (`<div>`) | layout container | `PreviewPanel.jsx:99-104` |
| Document name label | text (`document.name`) | `PreviewPanel.jsx:100` |
| "✕ Close" button | button (`onClick={onClose}`) | `PreviewPanel.jsx:101-103` |
| File type metadata row | text (`document.file_type`) | `PreviewPanel.jsx:105` |
| File size metadata row | conditional text (`document.file_size && formatFileSize(...)`) | `PreviewPanel.jsx:106-108` |
| "Loading PDF..." paragraph | conditional text (`isPdf && loading`) | `PreviewPanel.jsx:112` |
| PDF error paragraph | conditional red text (`isPdf && error`) | `PreviewPanel.jsx:113` |
| react-pdf `<Document>` | PDF viewer component (`file={previewUrl}`) | `PreviewPanel.jsx:114-118` |
| react-pdf `<Page pageNumber={1} width={400}>` | PDF page renderer | `PreviewPanel.jsx:119` |
| Page count label "Page X of N" | conditional text (`numPages`) | `PreviewPanel.jsx:121-125` |
| `<img>` image preview | image (`src={previewUrl}`) | `PreviewPanel.jsx:131` |
| Unsupported-type fallback message | conditional text (`!isPdf && !isImage`) | `PreviewPanel.jsx:135-137` |

---

## Out of scope

| Feature | Owner key |
|---|---|
| Selecting a document (clicking a document card in the grid) | `document-grid-document-select` |
| "✕ Close" parent-side state management (`showPreview = false`) | `app-workspace-preview-panel-close` |
| Site header and sidebar navigation | `app-workspace-header`, `app-workspace-sidebar` |
| PDF.js worker CDN loading | external / infrastructure concern |
