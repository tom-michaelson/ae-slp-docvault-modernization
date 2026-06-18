# Functional spec — Edit Tags Button

**Key:** `document-grid-edit-tags`
**URL:** `PUT /api/documents/{id}/tags` (triggered by user action, not a page route)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (button lines 879–885 card / 925–930 list row; modal render lines 812–863; handlers lines 619–683)

## Purpose

Lets a user add, remove, and persist tags on any document directly from the document grid, without navigating away from the page. The 🏷️ button appears on every document card (grid view) and every list row (list view); clicking it opens a modal dialog pre-populated with the document's current tags. Changes are saved with a single API call that replaces the tag set atomically.

## Functional behavior

### handleOpenTagEditor — open modal

1. User clicks the 🏷️ button on a document card or list row.
2. `e.stopPropagation()` is called to prevent the parent card/row `onClick` (document selection) from also firing.
3. State is set: `tagEditorVisible = true`, `tagEditorDocId = doc.id`, `tagEditorTags = [...doc.tags]` (shallow copy of current tags), `tagEditorInput = ''`.
4. `renderTagEditor()` returns the modal overlay; the document grid remains visible behind a semi-transparent backdrop.

### handleAddTag — add a tag

1. Triggered by clicking the **Add** button or pressing **Enter** in the tag input field.
2. The current value of `tagEditorInput` is trimmed.
3. The tag is rejected (silently, no error message) if it is empty, already present in `tagEditorTags`, or if `tagEditorTags` already has 10 entries.
4. Otherwise the tag is appended to `tagEditorTags` and `tagEditorInput` is cleared.

### handleRemoveTag — remove a tag

1. Triggered by clicking the **×** span next to any existing tag in the modal list.
2. The tag is filtered out of `tagEditorTags` by value match.

### handleSaveTags — persist tags to backend

1. Triggered by clicking the **Save** button.
2. `tagSaving` is set to `true`; the Save button is disabled and shows "Saving…".
3. `updateTags(tagEditorDocId, tagEditorTags)` is called, which issues `PUT /api/documents/{id}/tags` with body `{ tags: tagEditorTags }`. The JWT from `localStorage('docvault_token')` is attached as a Bearer token.
4. **Success path:** the `documents` array in local state is updated — the matching document's `tags` field is replaced with `tagEditorTags`. `tagSaving` is set to `false` and `tagEditorVisible` is set to `false` (modal closes).
5. **Error path:** `tagSaving` is set to `false` and the modal stays open. The error is logged to `console.error` only — no user-visible error message is displayed.

### handleCloseTagEditor — discard and close

1. Triggered by clicking the **Cancel** button or clicking anywhere on the semi-transparent backdrop overlay.
2. State is reset: `tagEditorVisible = false`, `tagEditorDocId = null`, `tagEditorTags = []`, `tagEditorInput = ''`.
3. Any unsaved tag changes are discarded.

## Acceptance criteria

```gherkin
Scenario: Open tag editor from card view
  Given documents are displayed in grid view
  And document "Report Q1" has tags ["finance", "q1"]
  When the user clicks the 🏷️ button on "Report Q1"
  Then the tag editor modal opens
  And the modal displays the tags "finance" and "q1"
  And the document card is not selected (card onClick was not triggered)

Scenario: Open tag editor from list view
  Given documents are displayed in list view
  When the user clicks the 🏷️ button on any document row
  Then the tag editor modal opens pre-populated with that document's current tags

Scenario: Add a tag via Add button
  Given the tag editor is open with tags ["finance"]
  When the user types "q1" in the tag input
  And clicks the Add button
  Then "q1" appears as a removable tag chip in the modal
  And the input field is cleared

Scenario: Add a tag via Enter key
  Given the tag editor is open
  When the user types "annual" in the tag input and presses Enter
  Then "annual" is added to the tag list
  And the input field is cleared

Scenario: Duplicate tag is silently rejected
  Given the tag editor already contains the tag "finance"
  When the user types "finance" and clicks Add
  Then no duplicate tag is added
  And no error message is shown

Scenario: Tag limit enforced client-side
  Given the tag editor already contains 10 tags
  When the user types a new tag and clicks Add
  Then the tag is not added
  And the count remains 10

Scenario: Remove a tag
  Given the tag editor contains tags ["finance", "q1"]
  When the user clicks × next to "finance"
  Then "finance" is removed from the tag list
  And "q1" remains

Scenario: Save tags successfully
  Given the tag editor contains tags ["finance", "q1"]
  When the user clicks Save
  Then PUT /api/documents/{id}/tags is called with body { "tags": ["finance", "q1"] }
  And the Save button shows "Saving…" and is disabled during the request
  And on success the modal closes
  And the document card/row in the grid now shows tags "finance" and "q1" without a page reload

Scenario: Save tags — API error
  Given the tag editor is open and the API returns a 500 error
  When the user clicks Save
  Then the modal stays open
  And the Save button is re-enabled
  And no user-visible error message is displayed (error is logged to console only)

Scenario: Cancel discards changes
  Given the tag editor is open and the user has added a new tag "draft"
  When the user clicks Cancel
  Then the modal closes
  And the document's tags are unchanged in the grid
  And no API call is made

Scenario: Close by clicking backdrop
  Given the tag editor modal is open
  When the user clicks the semi-transparent backdrop outside the modal
  Then the modal closes and changes are discarded
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| 🏷️ button (card view) | button, `onClick=(e) => handleOpenTagEditor(e, doc)` | `DocumentGrid.jsx:879-885` |
| 🏷️ button (list row view) | button, `onClick=(e) => handleOpenTagEditor(e, doc)` | `DocumentGrid.jsx:925-930` |
| Tag editor overlay / backdrop | fixed-position div, `onClick=handleCloseTagEditor` | `DocumentGrid.jsx:818` |
| Tag editor modal container | div, `onClick=e.stopPropagation()` (prevents backdrop close) | `DocumentGrid.jsx:819` |
| Modal title | text "Edit Tags" | `DocumentGrid.jsx:820` |
| Tag text input | `<input type="text">`, `value=tagEditorInput`, `maxLength=50`, `onKeyPress=handleTagKeyPress` | `DocumentGrid.jsx:823-830` |
| Add button | button, `onClick=handleAddTag` | `DocumentGrid.jsx:831-833` |
| Tag chip list | loop over `tagEditorTags` | `DocumentGrid.jsx:836-846` |
| Tag remove × | span, `onClick=() => handleRemoveTag(tag)` per chip | `DocumentGrid.jsx:840-844` |
| Cancel button | button, `onClick=handleCloseTagEditor` | `DocumentGrid.jsx:849-851` |
| Save button | button, `onClick=handleSaveTags`, disabled when `tagSaving=true` | `DocumentGrid.jsx:852-858` |
| Save button loading text | conditional text: "Saving…" vs "Save" | `DocumentGrid.jsx:857` |

## Out of scope

- The document card and list row rendering that hosts the 🏷️ button belongs to `document-grid-document-list`.
- The tag display (read-only pill chips on each card/row) belongs to `document-grid-document-list`.
- The search filter that matches on tag values belongs to `document-grid-filter-text`.
