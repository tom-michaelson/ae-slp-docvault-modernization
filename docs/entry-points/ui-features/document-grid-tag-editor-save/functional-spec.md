# Functional spec — Document Grid Tag Editor — Save Tags

**Key:** `document-grid-tag-editor-save`
**URL:** `PUT /api/documents/:id/tags` (API endpoint triggered by the Save button)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 666–683, 812–863)
**Backend source:** `backend/src/routes/tags.js`

---

## Purpose

Allows the user to persist a modified tag set for a document. The tag editor modal
accumulates additions and removals in local component state; clicking Save commits
that in-memory list to the server in a single full-replacement PUT. On success the
card or list row immediately reflects the new tags without a page reload.

---

## Functional behavior

### handleSaveTags (Save button click)

1. Reads `tagEditorDocId` and `tagEditorTags` from component state.
2. Sets `tagSaving = true` — disables the Save button and shows "Saving..." label.
3. Calls `updateTags(tagEditorDocId, tagEditorTags)` from `frontend/src/utils/api.js`.
   - Axios issues `PUT /api/documents/:id/tags` with body `{ tags: string[] }`.
   - The request interceptor attaches `Authorization: Bearer <token>` from
     `localStorage.docvault_token` if present.
4. **On success (2xx):**
   - Updates `this.state.documents[]` in-place: maps over the array and replaces
     the document whose `id` matches `tagEditorDocId` with `{ ...d, tags: tagEditorTags }`.
   - Sets `tagSaving = false` and `tagEditorVisible = false` (closes modal).
5. **On failure (network error or non-2xx):**
   - Logs to `console.error` only — **no error is surfaced to the user**.
   - Sets `tagSaving = false`; `tagEditorVisible` remains `true` so the user can retry.

### Backend route — PUT /api/documents/:id/tags

1. Auth middleware chain (index.js lines 49–76) requires at least one of:
   API key, JWT (`Authorization: Bearer`), or express-session. Bypassed if
   `DEV_SKIP_AUTH=true`.
2. Validates `req.body.tags` is an array; returns `400` if not.
3. Filters tags to non-empty strings (`validTags`).
4. Rejects with `400` if `validTags.length > 10`.
5. Executes `UPDATE documents_v2 SET tags = $1 WHERE id = $2 RETURNING id, tags`.
6. Returns `404` if no row matched the UUID.
7. Returns `{ id, tags }` (the persisted values) on success.

---

## Acceptance criteria

```gherkin
Scenario: Happy path — save a non-empty tag list
  Given the tag editor modal is open for document with id "doc-uuid-1"
  And the tag list contains ["invoice", "2024", "finance"]
  When the user clicks Save
  Then PUT /api/documents/doc-uuid-1/tags is called with body { "tags": ["invoice","2024","finance"] }
  And the Save button shows "Saving..." and is disabled during the request
  And on 200 response the modal closes
  And the document card for "doc-uuid-1" displays tags "invoice", "2024", "finance" without a page reload

Scenario: Save clears all tags (empty list)
  Given the tag editor modal is open for document with id "doc-uuid-2"
  And the user has removed all tags so the list is empty
  When the user clicks Save
  Then PUT /api/documents/doc-uuid-2/tags is called with body { "tags": [] }
  And on 200 response the document card shows no tags

Scenario: API returns 404 (document not found)
  Given the tag editor modal is open for document "doc-uuid-ghost"
  And the document has been deleted server-side
  When the user clicks Save
  Then PUT /api/documents/doc-uuid-ghost/tags returns 404
  And the Save button re-enables (tagSaving = false)
  And the modal stays open
  And no error message is displayed to the user

Scenario: Network failure during save
  Given the tag editor modal is open
  When the user clicks Save and the network request fails
  Then the Save button re-enables
  And the modal remains open with the current tag list intact
  And an error is logged to the browser console only

Scenario: Unauthenticated request (401)
  Given DEV_SKIP_AUTH is false
  And no valid JWT, session, or API key exists
  When the user clicks Save
  Then PUT /api/documents/:id/tags returns 401
  And the client-side catch handler fires (same as network failure: modal stays open, no UI error shown)

Scenario: Tag count limit enforced on server
  Given the client-side guard allows max 10 tags (handleAddTag line 645)
  And the server also rejects if validTags.length > 10
  When a PUT request is crafted with 11 tags (bypassing the UI)
  Then the server responds 400 { "error": "Maximum 10 tags per document" }
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Tag editor overlay (backdrop) | `<div>` fixed fullscreen, click closes modal | `DocumentGrid.jsx:818` |
| Tag editor modal container | `<div>` — stops click propagation to backdrop | `DocumentGrid.jsx:819` |
| "Edit Tags" modal title | text | `DocumentGrid.jsx:820` |
| Tag text input | `<input type="text">` maxLength=50, Enter triggers add | `DocumentGrid.jsx:822–829` |
| Add button | `<button>` — calls `handleAddTag` | `DocumentGrid.jsx:831–833` |
| Current tag list | loop over `tagEditorTags[]` rendering removable chip spans | `DocumentGrid.jsx:836–846` |
| Remove (×) per tag | `<span>` click — calls `handleRemoveTag(tag)` | `DocumentGrid.jsx:839–844` |
| Cancel button | `<button>` — calls `handleCloseTagEditor` (discards changes) | `DocumentGrid.jsx:849–851` |
| **Save button** | `<button>` — calls `handleSaveTags`; disabled when `tagSaving=true`; label "Saving…" during request | `DocumentGrid.jsx:852–858` |

---

## Out of scope

| Feature | Feature key |
|---|---|
| Opening the tag editor (🏷️ button on card / list row) | `document-grid-tag-editor-open` |
| Adding / removing tags within the open modal before saving | `document-grid-tag-editor-edit` |
| Document card rendering and selection | `document-grid-card` |
| Document list row rendering | `document-grid-list-row` |
| GET /api/documents/:id/tags (read tags endpoint) | — |
