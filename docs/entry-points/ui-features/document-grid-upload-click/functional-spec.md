# Functional spec — Click to Select File

**Key:** `document-grid-upload-click`
**URL:** `POST /api/upload` (action initiated from the root `/` workspace page)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 717–744, 778–809)

---

## Purpose

Lets an authenticated user pick a file from their local file system by clicking the upload drop zone,
then uploads it to the server. The uploaded document immediately appears in the document grid.
This is one of two upload entry points in the same zone — the other being drag-and-drop (`document-grid-upload-drop`).

---

## Functional behavior

### handleFileInputClick — open file picker

1. User clicks anywhere on the upload area `<div>` (line 789, `onClick={this.handleFileInputClick}`).
2. `handleFileInputClick` (line 717) calls `this.fileInputRef.current?.click()`.
3. The browser opens the native OS file-picker dialog.
4. The hidden `<input type="file" accept=".pdf,.jpg,.jpeg,.png">` mediates the dialog — no UI change yet.

### handleFileInputChange → uploadFile — transmit file

1. User selects a file; `onChange` fires `handleFileInputChange` (line 721).
2. Extracts `e.target.files[0]`; if empty, returns early (no upload).
3. Resets the hidden input value (`fileInputRef.current.value = ''`) after extracting the file so the same file can be re-selected later.
4. Calls `uploadFile(file)` (line 728):
   a. Sets state `uploadProgress = 'uploading'`, `uploadError = null` — upload area shows "Uploading…".
   b. Builds `FormData` with two fields: `file` (binary) and `name` (`file.name`).
   c. Calls `uploadDocument(formData)` → `axios.post('/api/upload', formData, { 'Content-Type': 'multipart/form-data' })`.
5. **On success (HTTP 201):**
   a. Sets `uploadProgress = 'done'` — upload area shows "✅ Upload complete!".
   b. Calls `loadDocuments()` → `GET /api/documents` to refresh the document list.
   c. After 2 000 ms, clears `uploadProgress` to null — upload area returns to idle state.
6. **On error (non-2xx or network failure):**
   a. Sets `uploadProgress = null`, `uploadError = err.response?.data?.error || 'Upload failed'`.
   b. Upload area shows the error message in red beneath the hint text.

### Backend: POST /api/upload

1. Auth middleware runs first: API key → JWT → session (any one must succeed; 401 if all fail and DEV_SKIP_AUTH is not set).
2. Multer `fileFilter` validates MIME type (`application/pdf`, `image/jpeg`, `image/png` only); rejects others with "Invalid file type".
3. Multer saves file to `config.uploadDir` as `{uuid}{original-extension}`.
4. Handler reads `req.body.name` (falls back to `req.file.originalname`) and `req.user?.email`.
5. Executes: `INSERT INTO documents (name, file_type, file_path, tags, uploaded_by) VALUES (...) RETURNING *`.
6. `tags` is null (frontend does not send tags on click-upload).
7. DB trigger `trg_sync_to_v2` fires immediately: copies row to `documents_v2` **without** `tags`.
8. Returns HTTP 201 with the full `documents` row as JSON.

---

## Acceptance criteria

```gherkin
Scenario: Happy path — authenticated user clicks and uploads a valid PDF
  Given the user is authenticated (JWT, session, or API key)
  And the user is on the workspace page (/)
  When the user clicks the upload area
  And selects a PDF file from the file picker
  Then the upload area shows "Uploading..."
  And a POST /api/upload request is sent with multipart/form-data fields: file and name
  And the server returns HTTP 201 with the new document row
  And the upload area shows "✅ Upload complete!" for 2 seconds
  And the document list refreshes (GET /api/documents is called)
  And the new document appears in the grid

Scenario: Invalid file type rejected by the browser accept filter
  Given the user clicks the upload area
  When the OS file picker opens
  Then only files matching .pdf, .jpg, .jpeg, .png are selectable
  Note: this is enforced by the accept attribute on the hidden input — not a hard block on all OSes

Scenario: Invalid MIME type rejected by backend
  Given a user submits a file with MIME type not in [application/pdf, image/jpeg, image/png]
  When POST /api/upload is received
  Then the server returns HTTP 400 with error "Invalid file type. Only PDF, JPEG, and PNG are allowed."
  And the upload area shows "Invalid file type. Only PDF, JPEG, and PNG are allowed."

Scenario: Unauthenticated upload attempt
  Given the user has no JWT token, no session, and no API key
  When they click the upload area and select a file
  Then POST /api/upload returns HTTP 401 with { "error": "Authentication required" }
  And the upload area shows "Upload failed"

Scenario: Network or server error during upload
  Given the user selects a valid file
  And the server returns HTTP 500 or the network is unavailable
  Then the upload area shows "Upload failed" (or the server error message if provided)
  And uploadProgress is cleared to null
  And the document list is not refreshed

Scenario: User cancels the file picker without selecting a file
  Given the user clicks the upload area
  When the OS file picker opens and the user dismisses it without selecting a file
  Then no upload is initiated
  And the upload area remains in idle state

Scenario: Same file re-selected after successful upload
  Given a file was just successfully uploaded
  When the user clicks the upload area again and picks the same file
  Then a new upload is initiated (hidden input value was reset to '' after first upload)
  And a second document row is created in the database
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Upload area `<div>` | click target / drag-and-drop zone (dashed border) | `DocumentGrid.jsx:782–809` |
| Hidden file `<input type="file">` | `accept=".pdf,.jpg,.jpeg,.png"`, `style={{ display: 'none' }}` | `DocumentGrid.jsx:791–797` |
| Upload icon | `<span>⬆️</span>` | `DocumentGrid.jsx:798` |
| Upload text | conditional text: "Uploading…" / "✅ Upload complete!" / "Drop files here or click to upload" | `DocumentGrid.jsx:799–805` |
| Upload hint | `<span>PDF, JPEG, PNG</span>` | `DocumentGrid.jsx:806` |
| Upload error message | `<p style={{ color: 'red' }}>{uploadError}</p>`, shown only when `uploadError` is non-null | `DocumentGrid.jsx:807` |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| Drag-and-drop upload (onDrop handler) on the same zone | `document-grid-upload-drop` |
| Document list refresh after upload (GET /api/documents) | `document-grid-document-list` |
| Upload area active/idle visual styling (`isDragging` state) | `document-grid-upload-area` |
