# Functional spec — Standalone Tag Editor

**Key:** `tag-editor-standalone`
**URL:** N/A — panel component; no standalone route. Embedded by a parent and receives `documentId` as a prop.
**Legacy source:** `frontend/src/components/TagEditor.jsx`

## Purpose

Provides an inline widget for viewing, adding, and removing tags on a single document, then persisting the full tag list with a single Save action. It is the extraction-ready counterpart to the ad-hoc tag editor duplicated inside `DocumentGrid.jsx`; both call the same `PUT /api/documents/{id}/tags` API.

## Functional behavior

### handleAdd — add a tag to the local list

1. Reads `newTag` state, trims whitespace.
2. Rejects the tag if any of the following is true: trimmed value is empty, the value already exists in `tags` (case-sensitive exact match), or `tags.length >= 10`.
3. On acceptance: appends the trimmed value to `tags` state and resets `newTag` to `''`.
4. No API call is made; the change exists only in component state until **handleSave** is invoked.

### handleRemove — remove a tag from the local list

1. Accepts `tagToRemove` (a string from the rendered tag list).
2. Filters `tags` state to exclude the matching string; updates state.
3. No API call; change is local until **handleSave** is invoked.

### handleKeyPress — Enter-key shortcut for add

1. Fires on every `keypress` event in the tag text input.
2. If `e.key === 'Enter'`: calls `e.preventDefault()` (suppresses any parent form submit), then delegates to `handleAdd`.

### handleSave — persist tags to the server

1. Sets `saving = true`, disabling the Save button and showing label "Saving…".
2. Calls `updateTags(documentId, tags)` → `PUT /api/documents/{documentId}/tags` with JSON body `{ tags: string[] }`.
   - Auth: Bearer token read from `localStorage.getItem('docvault_token')` via axios request interceptor.
3. On success: calls the `onTagsUpdated(tags)` prop callback if provided (allows parent to sync its own state).
4. On error: logs to `console.error`; no user-visible error message is rendered.
5. Sets `saving = false` in the `finally` block regardless of outcome.

## Acceptance criteria

```gherkin
Scenario: Add a new unique tag
  Given the tag editor is rendered with documentId="doc-1" and initialTags=["foo"]
  When the user types "bar" in the tag input and clicks Add
  Then the tag "bar" appears in the tag list
  And the "Save Tags" button is still enabled (no API call yet)

Scenario: Duplicate tag is rejected
  Given the tag editor is rendered with initialTags=["foo"]
  When the user types "foo" and clicks Add
  Then the tag list remains ["foo"]
  And no duplicate is appended

Scenario: Maximum 10 tags enforced client-side
  Given the tag list already contains 10 tags
  When the user types "extra" and clicks Add
  Then the tag list is unchanged
  And no 11th tag is appended

Scenario: Enter key triggers add
  Given the tag input contains "baz"
  When the user presses the Enter key
  Then "baz" is added to the tag list (same outcome as clicking Add)

Scenario: Remove a tag
  Given the tag list contains ["alpha", "beta"]
  When the user clicks × next to "alpha"
  Then the tag list becomes ["beta"]

Scenario: Save persists tags to the server
  Given the tag list is ["alpha", "beta"] and documentId="doc-1"
  When the user clicks "Save Tags"
  Then a PUT /api/documents/doc-1/tags request is sent with body { "tags": ["alpha", "beta"] }
  And the Save button shows "Saving…" and is disabled while the request is in-flight
  And after the response the button returns to "Save Tags" and is enabled
  And the onTagsUpdated callback is called with ["alpha", "beta"]

Scenario: Save with expired or missing token
  Given localStorage does not contain "docvault_token"
  When the user clicks "Save Tags"
  Then the PUT request is sent without an Authorization header
  And the server returns 401
  And the error is logged to console
  And the Save button re-enables (no crash, no user-visible error message)

Scenario: Document not found on save
  Given documentId refers to a document that no longer exists
  When the user clicks "Save Tags"
  Then the server returns 404
  And the error is logged to console
  And the tag list in the component is unchanged
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Tag text input | `<input type="text">`, controlled, `maxLength=50`, Enter triggers handleAdd | `TagEditor.jsx:104-112` |
| Add button | `<button onClick={handleAdd}>` | `TagEditor.jsx:113-115` |
| Tag chip list | Loop over `tags` state, one `<span>` per tag | `TagEditor.jsx:118-125` |
| Tag chip label | text — displays the tag string value | `TagEditor.jsx:120` |
| Tag chip remove button | `<span onClick={() => handleRemove(tag)}>×</span>` | `TagEditor.jsx:121-123` |
| Save Tags button | `<button onClick={handleSave}>`, disabled while `saving === true` | `TagEditor.jsx:127-129` |

## Out of scope

- `DocumentGrid.jsx:812-860` contains a visually and functionally identical tag editor rendered as a modal overlay (`renderTagEditor()`). That implementation is a separate feature keyed `document-grid-tag-editor-modal` and is **not** part of this component's spec.
- The `GET /api/documents/{id}/tags` endpoint (`backend/src/routes/tags.js:38-53`) is not called by `TagEditor.jsx` — initial tags are passed in via the `initialTags` prop.
