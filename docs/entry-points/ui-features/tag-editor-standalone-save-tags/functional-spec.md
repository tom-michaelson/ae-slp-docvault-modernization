# Functional spec — Tag Editor — Save Tags

**Key:** `tag-editor-standalone-save-tags`
**URL:** `PUT /api/documents/:id/tags` (component-level interaction; no dedicated page route)
**Legacy source:** `frontend/src/components/TagEditor.jsx`

## Purpose

The `TagEditor` component lets an authenticated user manage the tag list attached to a
single document: they add and remove tags locally, then persist the final list with a
single "Save Tags" action. It is consumed as an embedded widget on any page that displays
document detail.

## Functional behavior

### handleAdd — add a tag to the local list

1. Reads `newTag` state, trims whitespace.
2. Validates: skip if trimmed value is empty, already in `tags` array, or `tags.length >= 10`.
3. Appends the new tag to `tags` state; clears `newTag` to empty string.
4. No API call — change is local until `handleSave`.

### handleRemove — remove a tag from the local list

1. Receives `tagToRemove` string.
2. Filters it out of `tags` state.
3. No API call — change is local until `handleSave`.

### handleKeyPress — Enter-key shortcut for add

1. Fires on every keypress in the tag input.
2. If `e.key === 'Enter'`: calls `e.preventDefault()` then delegates to `handleAdd`.
3. All other keys are ignored.

### handleSave — persist tag list to backend

1. Sets `saving = true` (disables Save button, changes label to "Saving…").
2. Calls `updateTags(documentId, tags)` → `PUT /api/documents/{documentId}/tags` with body `{ tags }`.
3. The axios instance attaches `Authorization: Bearer <token>` from `localStorage['docvault_token']` via a request interceptor.
4. On success: calls the `onTagsUpdated(tags)` prop callback if provided (allows parent component to refresh its own state).
5. On error: logs to `console.error('Failed to save tags:', err)`; no user-visible error message is shown.
6. In all cases (finally): sets `saving = false`.

**Backend behavior** (`backend/src/routes/tags.js`):
- Validates `tags` is an array; returns 400 if not.
- Filters out non-string / blank entries; returns 400 if more than 10 valid tags remain.
- Executes `UPDATE documents_v2 SET tags = $1 WHERE id = $2 RETURNING id, tags`.
- Returns 404 `{ error: 'Document not found' }` if no row matched.
- Returns 200 `{ id, tags }` on success.

## Acceptance criteria

```gherkin
Scenario: User adds a new tag and saves
  Given the TagEditor is rendered with documentId "abc-123" and initialTags ["legal"]
  When the user types "finance" in the tag input and clicks Add
  And clicks Save Tags
  Then PUT /api/documents/abc-123/tags is called with body { tags: ["legal", "finance"] }
  And onTagsUpdated is called with ["legal", "finance"]
  And the Save Tags button re-enables after the call completes

Scenario: User adds a tag via Enter key
  Given the TagEditor is rendered with an empty tag list
  When the user types "urgent" in the tag input and presses Enter
  Then "urgent" appears as a tag chip in the list
  And the input field is cleared

Scenario: Duplicate tag is silently ignored
  Given the TagEditor already contains tag "legal"
  When the user types "legal" and clicks Add
  Then the tag list still contains exactly one "legal" entry
  And no error message is shown

Scenario: Tag cap prevents adding an eleventh tag
  Given the TagEditor already contains 10 tags
  When the user types a new tag name and clicks Add
  Then the tag list remains at 10 items
  And no API call is made

Scenario: User removes a tag and saves
  Given the TagEditor contains tags ["legal", "finance"]
  When the user clicks × next to "finance"
  And clicks Save Tags
  Then PUT /api/documents/:id/tags is called with body { tags: ["legal"] }

Scenario: Save button is disabled while request is in flight
  Given the user clicks Save Tags
  Then the button label changes to "Saving..." and the button becomes disabled
  And the button re-enables once the PUT request resolves

Scenario: Document not found returns 404
  Given the documentId does not exist in documents_v2
  When the user clicks Save Tags
  Then the backend returns HTTP 404 with { error: "Document not found" }
  And the frontend logs "Failed to save tags:" to console.error
  And no user-visible error message is displayed

Scenario: Unauthenticated request is rejected
  Given no valid token exists in localStorage['docvault_token']
  When the user clicks Save Tags
  Then the backend returns HTTP 401
  And the axios response interceptor logs "Unauthorized — token may be expired"
  And saving resets to false
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Tag text input | `<input type="text">`, maxLength=50, placeholder "Add a tag..." | `TagEditor.jsx:104–112` |
| Add button | `<button onClick={handleAdd}>` | `TagEditor.jsx:113–115` |
| Tag chip list | loop over `tags` state array | `TagEditor.jsx:118–125` |
| Tag chip label | inline text per tag | `TagEditor.jsx:119` |
| Remove (×) button | `<span onClick={() => handleRemove(tag)}>` per chip | `TagEditor.jsx:121–123` |
| Save Tags button | `<button onClick={handleSave}>`, disabled while `saving===true` | `TagEditor.jsx:127–129` |
| Saving… label | conditional text inside Save button when `saving===true` | `TagEditor.jsx:129` |

## Out of scope

- The parent page/component that renders `<TagEditor>` — mounting, routing, and how `documentId` + `initialTags` are sourced belong to the containing page's feature spec.
- `onTagsUpdated` callback behavior in the parent — the callback contract is a prop; its implementation is owned by the caller.
- `GET /api/documents/:id/tags` — the `fetchTags` utility exists in `api.js` but `TagEditor` itself never calls it; tag fetching is the parent's responsibility via `initialTags`.
