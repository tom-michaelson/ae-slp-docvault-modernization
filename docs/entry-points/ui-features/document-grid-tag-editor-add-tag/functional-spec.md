# Functional spec — Add Tag Button

**Key:** `document-grid-tag-editor-add-tag`
**URL:** *(client-side only — no HTTP endpoint)*
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 642–663, 822–833)
**Parent feature:** `document-grid-tag-editor-modal`

---

## Purpose

The Add Tag button appends the user's typed text to the pending tag list inside the tag editor modal.
It is purely a client-side action: the tag is held in component state (`tagEditorTags`) and is not persisted to the server until the user later clicks Save.
This keeps the editing session transactional — the user may add or remove multiple tags before committing.

---

## Functional behavior

### handleAddTag — click on "Add" button

Triggered by `onClick` on the Add button (line 831).

1. Reads `tagEditorInput` and `tagEditorTags` from component state.
2. Computes `newTag = tagEditorInput.trim()`.
3. Evaluates three guards in a single `if` condition:
   - `newTag` is truthy (non-empty after trim).
   - `tagEditorTags` does not already include `newTag` (duplicate check, case-sensitive).
   - `tagEditorTags.length < 10` (maximum 10 tags per document).
4. **If all guards pass:** calls `setState({ tagEditorTags: [...tagEditorTags, newTag], tagEditorInput: '' })` — appends the tag and clears the input field.
5. **If any guard fails:** no state change — the action is a silent no-op (no error message shown to the user).

### handleTagKeyPress — Enter key in tag input

Triggered by `onKeyPress` on the tag text input (line 826).

1. Checks `e.key === 'Enter'`.
2. If true: calls `e.preventDefault()` to suppress form submission, then delegates to `handleAddTag()`.
3. Identical validation logic applies; this is purely a keyboard shortcut for the Add button.

---

## Acceptance criteria

```gherkin
Scenario: Happy path — valid new tag added
  Given the tag editor modal is open
  And tagEditorInput is "invoice"
  And tagEditorTags is ["contract"]
  When the user clicks the Add button
  Then tagEditorTags becomes ["contract", "invoice"]
  And tagEditorInput is cleared to ""

Scenario: Enter key behaves identically to Add button
  Given the tag editor modal is open
  And tagEditorInput is "invoice"
  When the user presses the Enter key in the tag input
  Then tagEditorTags gains "invoice"
  And tagEditorInput is cleared

Scenario: Duplicate tag is silently rejected
  Given tagEditorTags is ["contract"]
  And tagEditorInput is "contract"
  When the user clicks the Add button
  Then tagEditorTags remains ["contract"]
  And tagEditorInput is NOT cleared

Scenario: Whitespace-only input is silently rejected
  Given tagEditorInput is "   "
  When the user clicks the Add button
  Then tagEditorTags is unchanged
  And tagEditorInput is NOT cleared

Scenario: Tag limit of 10 is enforced
  Given tagEditorTags already contains 10 tags
  And tagEditorInput is "eleventh"
  When the user clicks the Add button
  Then tagEditorTags still contains exactly 10 tags
  And no error message is displayed

Scenario: Tags are case-sensitive for duplicate check
  Given tagEditorTags is ["Invoice"]
  And tagEditorInput is "invoice"
  When the user clicks the Add button
  Then tagEditorTags becomes ["Invoice", "invoice"]
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Tag text input | `<input type="text">`, `value={tagEditorInput}`, `onChange=handleTagInputChange`, `onKeyPress=handleTagKeyPress`, `maxLength={50}` | DocumentGrid.jsx:822–829 |
| Add button | `<button onClick={handleAddTag}>Add</button>` | DocumentGrid.jsx:831–833 |
| Tag chip list | loop over `tagEditorTags`; each chip is a `<span>` displaying the tag text | DocumentGrid.jsx:836–846 |
| Remove (×) span | `<span onClick={() => handleRemoveTag(tag)}>×</span>` inside each chip | DocumentGrid.jsx:840–844 |

---

## Out of scope

| Feature | Reason |
|---|---|
| **Save button / PUT /api/documents/{id}/tags** | Belongs to `document-grid-edit-tags`; the Add button itself makes no API call. |
| **Cancel button / modal close** | Belongs to `document-grid-tag-editor-modal`. |
| **🏷️ button that opens the modal** | Belongs to `document-grid-edit-tags` (handleOpenTagEditor). |
| **Tag editor in standalone TagEditor.jsx** | A separate component (`tag-editor-standalone-add-tag`); shares the same logic pattern but is a different inventory entry. |
