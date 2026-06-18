# Functional spec — Standalone Upload Button

**Key:** `upload-button`
**URL:** N/A — component has no route; embedded wherever the parent mounts it. Calls `POST /api/upload`.
**Legacy source:** `frontend/src/components/UploadButton.jsx`

---

## Purpose

Provides a self-contained, clickable upload control that lets an authenticated user
select a single file from their local filesystem and submit it to the DocVault backend.
The component is a standalone alternative to DocumentGrid's built-in upload area;
both share identical upload logic but live in separate files. On success, the component
notifies its parent via a callback prop so the document list can refresh without a
full page reload.

---

## Functional behavior

### handleClick — open file picker

1. User clicks the green "📤 Upload Document" button.
2. The button is disabled (`disabled={uploading}`) while an upload is in progress.
3. `handleClick` calls `fileInputRef.current?.click()` to programmatically open the
   native OS file-picker dialog.
4. No network activity occurs in this handler.

### handleFileChange — upload file

1. Fires when the user selects a file from the OS dialog (`onChange` on `<input type="file">`).
2. If `e.target.files[0]` is falsy (dialog cancelled), returns immediately — no state change.
3. Sets `uploading = true` and `status = 'Uploading...'`.
4. Constructs a `FormData` object with two fields:
   - `file` → the `File` object
   - `name` → `file.name` (the local filename)
   - **Note:** no `tags` field is appended; the backend defaults tags to `null`.
5. Calls `uploadDocument(formData)` from `utils/api.js`, which issues
   `POST /api/upload` with `Content-Type: multipart/form-data`.
   - The axios request interceptor reads `localStorage['docvault_token']` and attaches
     `Authorization: Bearer {token}` if present.
   - The backend multer middleware validates the MIME type is one of
     `application/pdf`, `image/jpeg`, `image/png`; rejects other types with HTTP 400.
   - On success the backend inserts a row into the `documents` table and returns the
     new record (HTTP 201) with fields: `id`, `name`, `file_type`, `file_path`,
     `tags`, `uploaded_at`, `uploaded_by`.
6. **On success:**
   - Sets `status = 'Uploaded: {response.data.name}'`.
   - If the `onUploadComplete` prop is provided, calls `onUploadComplete(response.data)`.
7. **On error:**
   - Sets `status = 'Upload failed: {err.response?.data?.error || err.message}'`.
8. **Finally (always):**
   - Sets `uploading = false`.
   - Resets `fileInputRef.current.value = ''` so the same file can be selected again.

---

## Acceptance criteria

```gherkin
Scenario: Successful upload of a PDF file
  Given the user is authenticated (JWT token in localStorage)
  And the user clicks "📤 Upload Document"
  When the OS file-picker opens and the user selects "report.pdf"
  Then the button becomes disabled and shows "Uploading..."
  And a POST /api/upload request is sent with multipart fields file and name
  And the Authorization: Bearer header is present on the request
  And when the server responds 201, the status text reads "Uploaded: report.pdf"
  And onUploadComplete is called with the returned document record
  And the button is re-enabled

Scenario: Upload of a disallowed file type
  Given the user is authenticated
  And the user selects a file with MIME type "text/plain" (e.g., "notes.txt")
  Then the server responds with HTTP 400 and { "error": "Invalid file type..." }
  And the status text reads "Upload failed: Invalid file type. Only PDF, JPEG, and PNG are allowed."
  And onUploadComplete is NOT called

Scenario: Upload attempted without authentication
  Given no JWT token is present in localStorage
  And the user selects a valid PDF file
  Then the POST /api/upload request carries no Authorization header
  And the server responds with HTTP 401 { "error": "Authentication required" }
  And the status text reads "Upload failed: Authentication required"
  And the button is re-enabled after the error

Scenario: Network error during upload
  Given the user is authenticated and selects a valid PDF
  And the network request fails with a connection timeout
  Then the status text reads "Upload failed: timeout of 10000ms exceeded"
  And uploading is set back to false

Scenario: User cancels the file picker dialog
  Given the user clicks "📤 Upload Document"
  And the OS file-picker opens
  When the user dismisses the dialog without selecting a file
  Then e.target.files[0] is undefined
  And the component state is unchanged (no status text, no network call)

Scenario: Same file re-uploaded after a successful upload
  Given a previous upload succeeded
  And the file input value was reset to '' in the finally block
  When the user clicks the button again and selects the same file
  Then the onChange event fires normally (input was reset, so the browser detects a change)
  And a new upload request is sent
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Outer container `<div>` | structural wrapper | `UploadButton.jsx:58` |
| Hidden `<input type="file">` | file input, accepts `.pdf,.jpg,.jpeg,.png`, not visible to user | `UploadButton.jsx:59-65` |
| "📤 Upload Document" / "Uploading..." button | `<button>`, disabled while uploading, triggers file picker on click | `UploadButton.jsx:66-68` |
| Status message `<p>` | conditional text block, shown when `status` is non-empty; displays success name or error string | `UploadButton.jsx:69` |

---

## Out of scope

- **DocumentGrid upload area** (`document-grid-upload-area`, `document-grid-upload-click`,
  `document-grid-upload-drop`): `DocumentGrid.jsx` contains duplicated upload state
  (lines 531 and 686) that performs the same POST /api/upload call, including drag-and-drop
  support. That logic belongs to those feature keys, not this one.
- **JWT acquisition / login flow**: the `docvault_token` token is written by the login
  feature (`login-form-submit`); this component only reads it via the axios interceptor.
- **Document list refresh**: the parent's behaviour after `onUploadComplete` fires is out of
  scope here (handled by `document-grid-refresh` or equivalent feature key).
- **documents_v2 trigger side-effect**: the DB trigger that copies inserted rows to
  `documents_v2` (omitting `tags`) is a backend concern; the Angular reimplementation
  should write directly to the canonical table and not rely on trigger replication.
