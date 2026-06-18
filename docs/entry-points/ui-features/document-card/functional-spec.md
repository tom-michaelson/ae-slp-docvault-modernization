# Functional spec — Document Card

**Key:** `document-card`
**URL:** N/A — presentational component; no route. Rendered as a child inside any document-list context.
**Legacy source:** `frontend/src/components/DocumentCard.jsx`

## Purpose

Renders a single document as a clickable card, surfacing its name, MIME/file type, upload date, and tag chips. It acts as the visual unit of a document list and fires a selection callback when clicked, enabling the parent to open the preview panel.

## Functional behavior

### Render

1. Destructures `{ name, file_type, tags, uploaded_at }` from the `document` prop.
2. Renders a styled `<div>` with a click handler. The `onClick` guard (`onClick && onClick(document)`) means the card is safe to render without a callback prop — the click is a no-op.
3. Renders `name` inside an `<h3>` (title).
4. Renders `file_type` in a `<p>` prefixed with "Type:".
5. Renders `formatDate(uploaded_at)` in a `<p>` prefixed with "Uploaded:".
   - `formatDate` is from `../utils/formatDate`; returns `'Unknown date'` for falsy input, `'Invalid date'` for unparsable input, otherwise `'en-US'` locale string with year/short-month/day/hour:minute.
6. If `tags` is a non-empty array, renders a `<div>` of `<span>` chips, one per tag (keyed by array index).
7. If `tags` is absent or empty, renders an italic `<p>No tags</p>` instead.

### onClick interaction

1. Wrapping `<div>` has `onClick={() => onClick && onClick(document)}`.
2. Passes the full `document` object back to the caller — no transformation.
3. Cursor is set to `pointer` via inline style to signal clickability.

## Acceptance criteria

```gherkin
Scenario: Card renders document fields
  Given a document object { name: "Report.pdf", file_type: "application/pdf", tags: ["finance"], uploaded_at: "2024-03-15T10:30:00Z" }
  When DocumentCard renders with this document
  Then the card shows "Report.pdf" as the title
  And shows "Type: application/pdf"
  And shows "Uploaded: Mar 15, 2024, 10:30 AM"
  And shows a tag chip labelled "finance"

Scenario: Card shows "No tags" when tags array is empty
  Given a document object with tags: []
  When DocumentCard renders
  Then an italic "No tags" paragraph is displayed
  And no tag chip container is rendered

Scenario: Card shows "No tags" when tags prop is absent
  Given a document object with no tags field
  When DocumentCard renders
  Then an italic "No tags" paragraph is displayed

Scenario: Click fires onClick with full document object
  Given an onClick callback spy
  When the user clicks the card
  Then onClick is called once with the document object as its sole argument

Scenario: Card renders without crashing when onClick prop is omitted
  Given no onClick prop is provided
  When the user clicks the card
  Then no error is thrown and the card remains visible

Scenario: formatDate handles missing uploaded_at
  Given a document object with uploaded_at: null
  When DocumentCard renders
  Then "Uploaded: Unknown date" is displayed
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Card container `<div>` | click target (fires `onClick(document)`) | `DocumentCard.jsx:49` |
| Document name `<h3>` | text | `DocumentCard.jsx:50` |
| File type `<p>` | text ("Type: {file_type}") | `DocumentCard.jsx:51` |
| Upload date `<p>` | text ("Uploaded: {formatDate(uploaded_at)}") | `DocumentCard.jsx:52` |
| Tag chips container `<div>` | conditional (`tags && tags.length > 0`) | `DocumentCard.jsx:53-58` |
| Tag chip `<span>` | loop over `tags` array | `DocumentCard.jsx:55-57` |
| No-tags message `<p>` | conditional text, italic (`!tags \|\| tags.length === 0`) | `DocumentCard.jsx:60-62` |

## Out of scope

- **DocumentGrid inline card rendering** (`renderCard()` in `DocumentGrid.jsx:~880-930`): the grid renders its own inline card markup independently of this component; that inline variant belongs to `document-grid-document-list`.
- **PreviewPanel**: opened by the parent (`App.jsx`) in response to the `onDocumentSelect` callback — outside this component's responsibility.
- **formatFileSize utility** (`DocumentGrid.jsx:21`): imported but unused in this component. In the Angular 19 target, do not introduce a dependency on the equivalent of DocumentGrid for this utility; move it to a shared `FormatUtils` service.
