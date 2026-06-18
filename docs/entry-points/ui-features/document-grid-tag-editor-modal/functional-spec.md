# Functional spec — Document Grid – Tag Editor Modal

**Key:** `document-grid-tag-editor-modal`
**URL:** *(client-side modal; no route change)* — triggered from any document card or list row inside `DocumentGrid`
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 812–863, handlers 619–683)
**API endpoint called:** `PUT /api/documents/:id/tags`

---

## Purpose

Lets the user view and edit the tags attached to a single document without navigating away from the document grid. The modal opens as a full-viewport overlay above the grid, presents the current tag list, accepts additions and removals, then persists the result with a single API call. On success the grid card updates immediately with the new tag set.

---

## Functional behavior

### handleOpenTagEditor — open modal

1. Triggered by clicking the 🏷️ `actionButton` on a document card (`renderCard`, line 880) or a list row (`renderListRow`, line 925).
2. `e.stopPropagation()` prevents the card's own click handler from selecting the document simultaneously.
3. Sets component state: `tagEditorVisible = true`, `tagEditorDocId = doc.id`, `tagEditorTags = [...doc.tags]` (or `[]` if `doc.tags` is falsy), `tagEditorInput = ''`.
4. `renderTagEditor()` (line 812) detects `tagEditorVisible === true` and renders the overlay.

### handleTagInputChange — type a tag

1. Triggered on every keystroke in the text input.
2. Updates `tagEditorInput` in state.

### handleTagKeyPress — submit tag via keyboard

1. Triggered on any key press in the text input.
2. If `e.key === 'Enter'`, calls `e.preventDefault()` then delegates to `handleAddTag`.

### handleAddTag — add a tag chip

1. Trims `tagEditorInput`.
2. Guards: trimmed value must be non-empty, must not already exist in `tagEditorTags` (case-sensitive duplicate check), and `tagEditorTags.length` must be < 10.
3. Appends the new tag to `tagEditorTags`; clears `tagEditorInput`.
4. No API call is made at this point — the tag list is buffered locally until Save.

### handleRemoveTag — remove a tag chip

1. Triggered by clicking the `×` span inside a tag chip.
2. Filters `tagEditorTags`, removing the matching value.
3. No API call — change is buffered locally.

### handleSaveTags — persist the tag list

1. Sets `tagSaving = true` (disables the Save button and changes its label to "Saving…").
2. Calls `updateTags(tagEditorDocId, tagEditorTags)` → `PUT /api/documents/:id/tags` with body `{ tags: string[] }`.
3. **Success path:** patches the `documents` array in state (`map` over `id`), sets `tagSaving = false`, sets `tagEditorVisible = false`. The grid re-renders with the updated tag chips immediately; no full document re-fetch.
4. **Error path:** `tagSaving` is reset to `false`; the modal remains open. The error is written to `console.error` only — **no user-facing error message is shown**.

### handleCloseTagEditor — dismiss without saving

1. Triggered by clicking the Cancel button or by clicking the backdrop overlay (`tagEditorOverlay`).
2. Resets `tagEditorVisible`, `tagEditorDocId`, `tagEditorTags`, `tagEditorInput` to their initial values; any unsaved additions/removals are discarded.

---

## Acceptance criteria

```gherkin
Scenario: Open tag editor for a document with existing tags
  Given the document grid is loaded and a document has tags ["invoice", "2024"]
  When the user clicks the 🏷️ button on that document card
  Then the tag editor modal appears with chips "invoice" and "2024"
  And the text input is empty and focused

Scenario: Add a tag via the Add button
  Given the tag editor is open with tags ["invoice"]
  When the user types "contract" in the input and clicks Add
  Then a chip "contract" appears in the tag list
  And the input is cleared
  And no API call is made yet

Scenario: Add a tag via the Enter key
  Given the tag editor is open
  When the user types "urgent" in the input and presses Enter
  Then a chip "urgent" is added
  And the default form submission is suppressed

Scenario: Duplicate tag is rejected
  Given the tag editor is open with tags ["invoice"]
  When the user types "invoice" and clicks Add
  Then no duplicate chip is added
  And the tag list remains unchanged

Scenario: Tag limit of 10 is enforced
  Given the tag editor is open with 10 existing tags
  When the user types a new tag and clicks Add
  Then no chip is added (the limit guard silently blocks the operation)

Scenario: Remove a tag
  Given the tag editor is open with chips ["invoice", "urgent"]
  When the user clicks the × on "urgent"
  Then the "urgent" chip disappears from the list
  And no API call is made yet

Scenario: Save persists tags and closes modal
  Given the tag editor is open with tags ["invoice", "contract"]
  When the user clicks Save
  Then PUT /api/documents/:id/tags is called with body {"tags": ["invoice", "contract"]}
  And the Save button shows "Saving…" and is disabled during the request
  And on success the modal closes
  And the document card in the grid shows the updated tag chips without a page reload

Scenario: Save failure leaves modal open with no error shown to user
  Given the tag editor is open
  When the user clicks Save and the API returns a 500 error
  Then the modal remains open
  And the Save button re-enables
  And no error message is displayed to the user (error is console.error only)

Scenario: Cancel discards unsaved changes
  Given the tag editor is open and the user has added a chip "draft"
  When the user clicks Cancel
  Then the modal closes
  And "draft" does not appear on the document card
  And no API call is made

Scenario: Click-outside (backdrop) closes modal
  Given the tag editor modal is open
  When the user clicks anywhere outside the modal panel (on the dark overlay)
  Then the modal closes without saving

Scenario: Tag editor opens from list-view row
  Given the document grid is in list view
  When the user clicks the 🏷️ button on any list row
  Then the same tag editor modal opens for that document
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Backdrop overlay (`tagEditorOverlay`) | `div`, fixed-position full-viewport, closes modal on click | `DocumentGrid.jsx:818` |
| Modal panel (`tagEditorModal`) | `div`, 400 px wide, stops click propagation | `DocumentGrid.jsx:819` |
| "Edit Tags" title | text | `DocumentGrid.jsx:820` |
| Tag text input | `<input type="text">`, controlled, max 50 chars, Enter triggers add | `DocumentGrid.jsx:822–829` |
| Add button | `<button>`, calls `handleAddTag` | `DocumentGrid.jsx:831–833` |
| Tag chip list | loop over `tagEditorTags` | `DocumentGrid.jsx:836–846` |
| × remove span per chip | inline `<span>`, calls `handleRemoveTag(tag)` | `DocumentGrid.jsx:839–844` |
| Cancel button | `<button>`, calls `handleCloseTagEditor` | `DocumentGrid.jsx:849–851` |
| Save button | `<button>`, calls `handleSaveTags`; disabled + "Saving…" label while `tagSaving === true` | `DocumentGrid.jsx:852–858` |
| 🏷️ action button (card) | `<button>` on each grid card, opens modal | `DocumentGrid.jsx:879–885` |
| 🏷️ action button (list row) | `<button>` on each list row, opens modal | `DocumentGrid.jsx:925–931` |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| Standalone `TagEditor.jsx` functional component | `tag-editor-component` (unused in production; parallel implementation) |
| Document card rendering (title, date, file type, preview link) | `document-grid-card` |
| Document list row rendering | `document-grid-list-row` |
| Document grid data loading, search, and filter controls | `document-grid-main` |

---

## Migration notes for Spring Boot / Angular target

- **Angular:** Implement as a `MatDialog` or standalone `<app-tag-editor-dialog>` component receiving `documentId: string` and `initialTags: string[]` as `@Input()` or dialog data. Emit a `tagsUpdated: EventEmitter<string[]>` on save so the parent grid component can patch its local document list.
- **Spring Boot:** The existing `PUT /api/documents/{id}/tags` contract maps directly to a `@PutMapping("/documents/{id}/tags")` method accepting `TagUpdateRequest { List<String> tags }`. Enforce the max-10 and max-50-chars rules in a `@Valid` bean validation annotation rather than inline. Store as a PostgreSQL `TEXT[]` column or a JSON array column depending on chosen ORM strategy.
- **Error handling gap:** The legacy implementation silently swallows save errors (console.error only). The Angular reimplementation should surface a `MatSnackBar` or inline error message on save failure.
