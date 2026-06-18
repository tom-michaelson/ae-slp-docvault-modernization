# Functional spec — Add Tag Button

**Key:** `tag-editor-standalone-add-tag`
**URL:** n/a — client-side state action; no HTTP request is made
**Legacy source:** `frontend/src/components/TagEditor.jsx` (lines 70–75, 94–98, 113–115)
**Parent component:** `TagEditor` (`frontend/src/components/TagEditor.jsx:65`)

## Purpose

The Add Tag Button allows a user to stage a new tag string into the in-memory tag list of the standalone `TagEditor` component. The action is purely client-side: it validates and appends the typed value to local React state without contacting the API. Tags are not persisted until the user separately clicks the **Save Tags** button (see `tag-editor-standalone-save-tags`).

## Functional behavior

### handleAdd — add a tag to local state

Triggered by:
1. Clicking the **Add** button (`TagEditor.jsx:113`).
2. Pressing **Enter** while focused in the tag text input (`TagEditor.jsx:94–98` via `handleKeyPress`).

Steps:
1. Read `newTag` state and trim whitespace → local variable `tag`.
2. Validate all three conditions must be true simultaneously:
   - `tag` is non-empty (truthy after trim).
   - `tag` is not already present in `tags` state (`!tags.includes(tag)`).
   - Current tag count is below the maximum: `tags.length < 10`.
3. If validation passes:
   a. Call `setTags([...tags, tag])` — appends the new tag to the end of the list.
   b. Call `setNewTag('')` — clears the text input.
4. If any validation condition fails: the function exits silently; the input value is **not** cleared and no feedback is shown to the user.

### handleKeyPress — Enter-key shortcut

1. Fires on every `keypress` event in the tag input (`TagEditor.jsx:94`).
2. Checks `e.key === 'Enter'`; if true, calls `e.preventDefault()` then delegates to `handleAdd()`.
3. No other keys produce any action.

## Acceptance criteria

```gherkin
Scenario: Add a valid tag via button click
  Given the TagEditor has fewer than 10 tags
  And the tag input contains "  invoice  " (with surrounding spaces)
  When the user clicks the Add button
  Then the tag "invoice" appears in the tag list
  And the tag input is cleared

Scenario: Add a valid tag via Enter key
  Given the TagEditor has fewer than 10 tags
  And the tag input contains "contract"
  When the user presses the Enter key while the input is focused
  Then the tag "contract" appears in the tag list
  And the tag input is cleared

Scenario: Silently ignore a duplicate tag
  Given the tag list already contains "invoice"
  And the tag input contains "invoice"
  When the user clicks the Add button
  Then the tag list is unchanged
  And the tag input is not cleared

Scenario: Silently ignore an empty input
  Given the tag input contains "   " (whitespace only)
  When the user clicks the Add button
  Then the tag list is unchanged
  And the tag input is not cleared

Scenario: Silently ignore add when tag limit is reached
  Given the tag list already contains 10 tags
  And the tag input contains "newTag"
  When the user clicks the Add button
  Then the tag list remains at 10 tags
  And the tag input is not cleared

Scenario: No API call is made when adding a tag
  Given the TagEditor is mounted with documentId "abc-123"
  When the user clicks the Add button with a valid new tag
  Then no PUT /api/documents/abc-123/tags request is issued
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Tag text input | `<input type="text">`, controlled, `maxLength={50}`, placeholder "Add a tag...", `onKeyPress` → `handleKeyPress` | `TagEditor.jsx:104–111` |
| **Add** button | `<button onClick={handleAdd}>` | `TagEditor.jsx:113–115` |
| Tag chip list | loop over `tags` state; each chip renders tag text + remove `×` | `TagEditor.jsx:118–125` |
| Tag chip remove `×` | `<span onClick={() => handleRemove(tag)}>` per chip | `TagEditor.jsx:121–123` |

## Out of scope

| Feature | Reason |
|---|---|
| `tag-editor-standalone-save-tags` | The **Save Tags** button (line 127) is a separate feature key; it owns the `updateTags()` API call and `onTagsUpdated` callback. |
| `document-grid-tag-editor-add-tag` | The `DocumentGrid` class component contains its own inline tag-editor modal with equivalent logic (`handleAddTag`, `tagEditorTags` state). That is a distinct code path under the `document-grid-*` feature family. |
