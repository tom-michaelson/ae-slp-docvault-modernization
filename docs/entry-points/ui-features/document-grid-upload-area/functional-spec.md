# Functional spec — Document Upload Area

**Key:** `document-grid-upload-area`
**URL:** `POST /api/upload` (multipart/form-data)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` lines 778–809 (render), 688–745 (handlers)

---

## Purpose

Provides the primary file-ingestion surface for the document vault. Users can drag files onto the zone or click it to open a native file picker, after which the file is uploaded to the server and the document grid refreshes automatically. The zone is always visible above the document list, regardless of how many documents already exist.

---

## Functional behavior

### Drop-zone drag-and-drop

1. `handleDragEnter` sets `state.isDragging = true`; the zone re-renders with the highlighted `uploadAreaActive` style.
2. `handleDragOver` calls `e.preventDefault()` to allow the drop; no state change.
3. `handleDragLeave` sets `state.isDragging = false`; zone reverts to normal `uploadArea` style.
4. `handleDrop` prevents default browser behaviour, sets `isDragging = false`, reads `e.dataTransfer.files[0]`, and calls `uploadFile(file)`. Only the first file in the transfer is used; multi-file drops silently ignore files after the first.

### Click-to-browse

1. Clicking anywhere on the drop-zone div triggers `handleFileInputClick`, which calls `.click()` on `fileInputRef` — a hidden `<input type="file">`.
2. The hidden input's `accept` attribute restricts the picker to `.pdf,.jpg,.jpeg,.png`.
3. On file selection, `handleFileInputChange` reads `e.target.files[0]` and calls `uploadFile(file)`. After the call returns, the input's `value` is reset to `''` so the same file can be re-selected later.

### uploadFile (shared by both paths)

1. Sets `state.uploadProgress = 'uploading'` and `state.uploadError = null`.
2. Constructs a `FormData` with fields `file` (the `File` object) and `name` (`file.name`).
3. Calls `uploadDocument(formData)` → `POST /api/upload` with `Content-Type: multipart/form-data`.
4. On success:
   - Sets `state.uploadProgress = 'done'`.
   - Calls `loadDocuments()` to refresh the document grid via `GET /api/documents`.
   - After 2 000 ms clears `uploadProgress` back to `null`.
5. On error: sets `state.uploadProgress = null` and `state.uploadError` to `err.response.data.error` or `'Upload failed'`.

### Server-side (POST /api/upload)

1. multer `fileFilter` rejects MIME types other than `application/pdf`, `image/jpeg`, `image/png`; returns HTTP 400 `{ error: 'Invalid file type. Only PDF, JPEG, and PNG are allowed.' }`.
2. multer saves the file to `config.uploadDir` as `{uuid}{ext}`.
3. Executes `INSERT INTO documents (name, file_type, file_path, tags, uploaded_by) VALUES (...)`. `tags` is `null`; `uploaded_by` is `req.user.email` when a JWT is present, otherwise `null`.
4. The `trg_sync_to_v2` DB trigger fires and copies the new row to `documents_v2`, **omitting** the `tags` column.
5. Returns HTTP 201 with the full inserted row.

---

## Acceptance criteria

```gherkin
Scenario: Successful drag-and-drop upload
  Given the DocumentGrid is rendered
  And the drop zone is visible above the document list
  When the user drags a valid PDF file onto the zone
  Then isDragging becomes true and the zone highlights with uploadAreaActive style
  And when the file is dropped the zone reverts to normal style
  And the upload text changes to "Uploading..."
  And POST /api/upload is called with Content-Type: multipart/form-data
  And on 201 response the text changes to "✅ Upload complete!"
  And GET /api/documents is called to refresh the grid
  And after 2 seconds the upload text reverts to "Drop files here or click to upload"

Scenario: Successful click-to-browse upload
  Given the DocumentGrid is rendered
  When the user clicks anywhere on the drop zone
  Then the hidden file input receives a programmatic .click()
  When the user selects a JPEG file in the OS picker
  Then uploadFile is called with that file
  And after upload completes the hidden input value is reset to ""

Scenario: Only first file processed in multi-file drop
  Given the user drags three files onto the drop zone
  When handleDrop fires
  Then only e.dataTransfer.files[0] is passed to uploadFile
  And the remaining two files are silently ignored

Scenario: Upload error from server
  Given the server returns 500 { error: "Upload failed" }
  When uploadFile catches the error
  Then state.uploadProgress is set to null
  And state.uploadError is set to "Upload failed"
  And the error message is rendered in red below the upload hint

Scenario: Invalid file type rejected by server
  Given the user drops a .docx file onto the zone
  When POST /api/upload is called
  Then the server multer fileFilter rejects the file with HTTP 400
  And the error message "Invalid file type. Only PDF, JPEG, and PNG are allowed." is displayed inline

Scenario: Same file can be re-uploaded after first success
  Given a user has already uploaded "report.pdf"
  When they select "report.pdf" again via the file picker
  Then the hidden input value was reset to "" after the first upload
  And the onChange event fires again, allowing the re-upload to proceed
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Drop-zone container div | interactive container (drag target + click target) | `DocumentGrid.jsx:782-809` |
| Hidden file input | `<input type="file">` (hidden) | `DocumentGrid.jsx:791-797` |
| Upload icon | text (`⬆️`) | `DocumentGrid.jsx:798` |
| Upload status text | conditional text (idle / uploading / done) | `DocumentGrid.jsx:799-805` |
| Upload hint | static text ("PDF, JPEG, PNG") | `DocumentGrid.jsx:806` |
| Inline error message | conditional `<p>` in red (12 px) | `DocumentGrid.jsx:807` |

### Visual states of the drop-zone container

| State | Style applied | Trigger |
|---|---|---|
| Idle | `styles.uploadArea` (2 px dashed `#ccc`, background `#fafafa`) | Default |
| Dragging | `styles.uploadAreaActive` (2 px dashed `#0f3460`, background `#f0f4ff`) | `isDragging === true` |

---

## Out of scope

- **Document list refresh** (`document-grid-document-list`): `loadDocuments()` is called after a successful upload but the rendering of the list belongs to the parent `document-grid` feature.
- **UploadButton component** (`frontend/src/components/UploadButton.jsx`): A separate component that duplicates parts of this upload logic. The upload area inside `DocumentGrid` is a self-contained inline implementation.
- **documents_v2 trigger side-write**: The `trg_sync_to_v2` trigger is a DB-level concern. The Angular replacement should POST to `/api/upload` as documented; whether the server-side Spring implementation replicates or replaces this trigger is an API-implementation decision, not a UI concern.
