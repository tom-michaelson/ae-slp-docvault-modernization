# Functional spec — Preview Panel Close

**Key:** `app-workspace-preview-panel-close`
**URL:** N/A — workspace panel action (no dedicated route; the workspace lives at `/`)
**Legacy source:** `frontend/src/components/PreviewPanel.jsx` (button at line 101) + `frontend/src/App.jsx` (handler at line 66)

---

## Purpose

Allows the user to dismiss the document preview panel and return to the unobstructed full-width document grid. The action is triggered by the "✕ Close" button rendered in the PreviewPanel header whenever a document is actively selected for preview.

---

## Functional behavior

### onClick (Close button)

1. User clicks the "✕ Close" `<button>` rendered at `PreviewPanel.jsx:101`.
2. The button's `onClick` directly invokes the `onClose` prop (no intermediate handler inside `PreviewPanel`).
3. `App.handleClosePreview()` is called (`App.jsx:66–68`).
4. `App.setState` is called with `{ selectedDocument: null, showPreview: false }`.
5. React schedules a synchronous re-render of `App`.
6. The conditional `{showPreview && <PreviewPanel document={selectedDocument} onClose={...} />}` (`App.jsx:101–106`) evaluates to `false`.
7. `PreviewPanel` is unmounted from the DOM; any in-progress PDF load via `react-pdf` / pdf.js is abandoned and internal page state (`numPages`, `pageNumber`, `loading`, `error`) is discarded.
8. `DocumentGrid` reclaims the full content area width (flex layout, `contentStyle`).

---

## Acceptance criteria

```gherkin
Scenario: Close button dismisses the preview panel
  Given a document is selected and PreviewPanel is visible
  When the user clicks the "✕ Close" button
  Then PreviewPanel is removed from the DOM
  And DocumentGrid occupies the full content area width
  And App.state.selectedDocument is null
  And App.state.showPreview is false

Scenario: Close during PDF loading discards load state
  Given a PDF document is selected and the PDF is still loading
  When the user clicks "✕ Close" before the PDF finishes loading
  Then PreviewPanel is unmounted
  And no "Loading PDF…" indicator remains visible
  And no error state is left in the UI

Scenario: Re-opening preview after close restores clean state
  Given the user has previously closed the preview panel
  When the user selects a different document in DocumentGrid
  Then PreviewPanel mounts fresh with pageNumber=1, loading=true, error=null
  And the newly selected document's name appears in the panel header

Scenario: Close button is not rendered when no document is selected
  Given no document is selected (App.state.showPreview is false)
  Then PreviewPanel is not present in the DOM
  And the close button is not reachable by the user
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Panel header container | layout div | `PreviewPanel.jsx:99` |
| Document name title | text (`<span>`) | `PreviewPanel.jsx:100` |
| "✕ Close" button | button, `onClick={onClose}` | `PreviewPanel.jsx:101–103` |
| File type metadata line | text (`<p>`) | `PreviewPanel.jsx:105` |
| File size metadata line | text (`<p>`), conditionally rendered when `document.file_size` is truthy | `PreviewPanel.jsx:106–108` |
| PDF viewer block | conditional block (`isPdf`): loading indicator, error message, `<Document>/<Page>`, page count | `PreviewPanel.jsx:110–127` |
| Image viewer block | conditional block (`isImage`): `<img>` tag | `PreviewPanel.jsx:129–133` |
| "Preview not available" fallback | text (`<p>`), rendered when neither PDF nor image | `PreviewPanel.jsx:135–137` |
| Empty-state message | text, rendered when `document` prop is null | `PreviewPanel.jsx:86–90` |

---

## Out of scope

| Feature | Key | Notes |
|---|---|---|
| Opening / selecting a document to preview | `app-workspace-document-select` | `handleDocumentSelect` in App.jsx sets `selectedDocument` and `showPreview=true`; that action is a separate feature. |
| PDF pagination (page forward/back) | `app-workspace-preview-panel-pdf-paginate` | `numPages`/`pageNumber` state and any page-navigation controls belong to a separate feature key. |
| Document grid layout and document cards | `app-workspace-document-grid` | `DocumentGrid` is a sibling component; its behavior is unaffected by PreviewPanel close beyond reclaiming the flex width. |
| `formatFileSize` utility imported from DocumentGrid | N/A (anti-pattern) | PreviewPanel imports `formatFileSize` from `DocumentGrid.jsx` (god component). The Angular replacement must import this from a standalone utility; do not couple the preview component to the document grid module. |
