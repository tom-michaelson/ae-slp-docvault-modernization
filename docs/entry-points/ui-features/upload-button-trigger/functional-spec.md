# Functional spec — Upload Document Button

**Key:** `upload-button-trigger`
**URL:** Triggers `POST /api/upload` (multipart/form-data)
**Legacy source:** `frontend/src/components/UploadButton.jsx`

## Purpose

Allows an authenticated user to upload a document (PDF, JPEG, or PNG) from their local filesystem into DocVault. The user clicks a single button to open the OS file picker; upon file selection the component immediately sends the file to the API with no additional confirmation step.

## Functional behavior

### handleClick — open file picker

1. User clicks the "📤 Upload Document" `<button>`.
2. If `uploading === true` the button's `disabled` attribute is set — the DOM ignores the click and this handler is never called.
3. `handleClick()` calls `fileInputRef.current?.click()`, which programmatically triggers the browser's native file picker dialog.
4. The file picker is filtered to `.pdf`, `.jpg`, `.jpeg`, `.png` via the `accept` attribute on the hidden input.

### handleFileChange — upload selected file

1. Fires when the user selects a file and the hidden `<input type="file">` fires its `onChange` event.
2. Reads `e.target.files[0]`; returns immediately (no-op) if the array is empty (user cancelled the dialog).
3. Sets `uploading = true` and `status = 'Uploading...'`.
4. Constructs a `FormData` with two fields: `file` (the binary `File` object) and `name` (the file's `.name` string).
5. Calls `uploadDocument(formData)` (`utils/api.js:36`), which issues `POST /api/upload` as `multipart/form-data`. The axios request interceptor attaches `Authorization: Bearer {token}` from `localStorage.getItem('docvault_token')`.
6. The backend (Express + multer) validates MIME type, writes the file to disk as `{uuid}{original-ext}`, and inserts a row into the `documents` table. A PostgreSQL trigger (`trg_sync_to_v2`) then fires and copies the row into `documents_v2` **without** the `tags` column.
7. On success (HTTP 201): sets `status = 'Uploaded: {response.data.name}'` and calls the `onUploadComplete(response.data)` callback prop with the full created document object.
8. On error: sets `status = 'Upload failed: {err.response?.data?.error || err.message}'`. Does **not** call `onUploadComplete`.
9. In `finally` (always): sets `uploading = false` and resets `fileInputRef.current.value = ''` so the same file path can be selected again on a subsequent click.

## Acceptance criteria

```gherkin
Scenario: User uploads a valid PDF
  Given the user is authenticated and localStorage contains 'docvault_token'
  When the user clicks "📤 Upload Document"
  And they select a .pdf file from the OS file picker
  Then the button shows "Uploading..." and is disabled
  And a POST /api/upload request is sent with Content-Type multipart/form-data
  And the Authorization: Bearer header is present
  And on HTTP 201 the status paragraph shows "Uploaded: {document.name}"
  And onUploadComplete is called with the returned document object
  And the button returns to enabled state with label "📤 Upload Document"

Scenario: User uploads an unsupported file type
  Given the user selects a .docx file
  Then the hidden input's accept attribute filters it from the file picker
  But if the browser allows selection anyway the server returns 500
  And the status paragraph shows "Upload failed: Invalid file type. Only PDF, JPEG, and PNG are allowed."
  And onUploadComplete is not called

Scenario: Upload fails due to server error or network timeout
  Given the server is unavailable or returns a 5xx response
  When the user selects a valid file
  Then status shows "Upload failed: {err.message}"
  And the button is re-enabled
  And onUploadComplete is not called

Scenario: Button is disabled while an upload is in progress
  Given an upload is currently in progress (uploading === true)
  When the user clicks "📤 Upload Document"
  Then the button is disabled and handleClick is not invoked
  And no duplicate POST /api/upload request is sent

Scenario: User cancels the file picker without selecting a file
  Given the user clicks "📤 Upload Document"
  When they close the OS file dialog without selecting a file
  Then handleFileChange fires with e.target.files length of 0
  And the function returns immediately
  And uploading remains false and status remains unchanged

Scenario: Unauthenticated user attempts upload
  Given localStorage has no 'docvault_token'
  When the user selects a valid file
  Then POST /api/upload returns HTTP 401 with body { "error": "Authentication required" }
  And status shows "Upload failed: Authentication required"
  And onUploadComplete is not called

Scenario: File input is reset after upload so same file can be re-uploaded
  Given a previous upload completed (success or failure)
  When the user selects the same file path again
  Then the onChange event fires again (fileInputRef.current.value was reset to '')
  And a new upload is initiated
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Hidden file input | `<input type="file" accept=".pdf,.jpg,.jpeg,.png" style="display:none">` | `UploadButton.jsx:59-65` |
| "📤 Upload Document" button | `<button onClick={handleClick} disabled={uploading}>` | `UploadButton.jsx:66-68` |
| Uploading label (inline button text) | Conditional text — `uploading ? 'Uploading...' : '📤 Upload Document'` | `UploadButton.jsx:67` |
| Status paragraph | `<p>` conditionally rendered when `status` is non-empty; shows success or error message | `UploadButton.jsx:69` |

## Out of scope

- **`document-grid-upload-area` / `document-grid-upload-click` / `document-grid-upload-drop`**: `DocumentGrid.jsx` (`handleFileInputChange`, `handleDrop`, `uploadFile`) contains a duplicate implementation of this upload flow for its drag-and-drop zone. The two codepaths call the same `uploadDocument` API but are entirely separate — changes to `UploadButton` do not affect the `DocumentGrid` upload behaviour.
- **`app-workspace-header-upload-nav`**: The "Upload" link in `Header.jsx` calls `onNavigate('upload')` to set `App.state.activeSection`; it does not trigger an upload or render `UploadButton` directly.
