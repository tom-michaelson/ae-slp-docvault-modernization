# Functional spec — Drag-and-Drop Upload

**Key:** `document-grid-upload-drop`
**URL:** `POST /api/upload` (multipart/form-data; triggered by native browser drag-and-drop onto the upload zone)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 688–715, 728–745, 778–810)

---

## Purpose

Allows authenticated users to upload a document (PDF, JPEG, or PNG) by dragging it from the OS file system
and dropping it onto the upload zone rendered inside `DocumentGrid`. On success the document list
refreshes automatically and the user sees a brief "✅ Upload complete!" confirmation.

---

## Functional behavior

### handleDragEnter — drag enters zone

1. Calls `e.preventDefault()` and `e.stopPropagation()` to allow the browser to accept the drag.
2. Sets `isDragging: true`, switching the drop zone style from `styles.uploadArea` (dashed grey border,
   `#fafafa` background) to `styles.uploadAreaActive` (dashed `#0f3460` border, `#f0f4ff` background).

### handleDragLeave — drag leaves zone

1. Calls `e.preventDefault()` and `e.stopPropagation()`.
2. Sets `isDragging: false`, restoring the default drop zone appearance.

### handleDragOver — drag hovers over zone

1. Calls `e.preventDefault()` and `e.stopPropagation()` only.
2. No state changes. Required so the browser treats the zone as a valid drop target.

### handleDrop — file dropped

1. Calls `e.preventDefault()` and `e.stopPropagation()` to prevent the browser from navigating to the file.
2. Sets `isDragging: false`.
3. Reads `e.dataTransfer.files`. If `files.length === 0`, returns immediately.
4. Takes only `files[0]` — subsequent files in a multi-file drop are silently ignored.
5. Calls `this.uploadFile(file)`.

### uploadFile — shared upload execution

1. Sets `uploadProgress: 'uploading'` and clears `uploadError`.
2. Constructs a `FormData` with two fields:
   - `file`: the `File` object
   - `name`: `file.name` (original filename from the OS)
3. Calls `uploadDocument(formData)` from `frontend/src/utils/api.js`, which posts `multipart/form-data`
   to `POST /api/upload`.
4. **On success:**
   - Sets `uploadProgress: 'done'`.
   - Calls `this.loadDocuments()` (GET /api/documents) to refresh the document grid.
   - After 2000 ms, clears `uploadProgress` back to `null`.
5. **On failure:**
   - Sets `uploadProgress: null`.
   - Sets `uploadError` to `err.response?.data?.error` or the fallback string `'Upload failed'`.
   - The error message is rendered inline in the drop zone in red 12 px text.

### POST /api/upload — backend handler (Node.js / Express)

1. Multer middleware intercepts the request. Allowed MIME types: `application/pdf`, `image/jpeg`, `image/png`.
   Any other type causes Multer to reject with `'Invalid file type. Only PDF, JPEG, and PNG are allowed.'`.
2. File is stored on disk at `config.uploadDir` (default `./uploads`) with a UUID-based filename preserving
   the original extension.
3. Inserts one row into `documents`:
   - `name`: `req.body.name` (from FormData) or falls back to `req.file.originalname`
   - `file_type`: Multer-detected `mimetype`
   - `file_path`: `/uploads/{uuid}{ext}`
   - `tags`: `null` (drag-drop upload sends no tags)
   - `uploaded_by`: `req.user?.email` if a JWT user is attached to the request, otherwise `null`
4. PostgreSQL trigger `trg_sync_to_v2` fires after the INSERT and copies the row to `documents_v2`,
   intentionally omitting the `tags` column (schema bug; see migration 003-create-trigger.sql).
5. Returns HTTP 201 with the newly inserted `documents` row as JSON.

---

## Acceptance criteria

```gherkin
Scenario: User drops a single PDF onto the upload zone
  Given the user is on the document grid page
  And the upload zone shows "Drop files here or click to upload"
  When the user drags a PDF file over the upload zone
  Then the zone border turns blue (#0f3460) and the background turns light blue
  When the user drops the PDF
  Then the zone shows "Uploading..."
  And a POST multipart/form-data request is sent to /api/upload
  When the upload succeeds
  Then the zone shows "✅ Upload complete!"
  And the document list is refreshed to include the new document
  And after 2 seconds the upload zone returns to "Drop files here or click to upload"

Scenario: User drops multiple files — only first is processed
  Given the user is on the document grid page
  When the user drops three PDF files onto the upload zone simultaneously
  Then only the first file in e.dataTransfer.files is uploaded
  And the remaining two files are silently ignored

Scenario: User drops a file with a disallowed type
  Given the user is on the document grid page
  When the user drops a .docx file onto the upload zone
  Then the backend returns HTTP 400 or 500
  And the upload zone displays the server error message in red
  And uploadProgress is reset to null

Scenario: Empty drop (no files in dataTransfer)
  Given the user drags a non-file item (e.g., a browser tab link) onto the upload zone
  When the user releases over the drop zone
  Then handleDrop returns immediately without calling uploadFile
  And no request is sent to /api/upload
  And the upload zone returns to its default state

Scenario: Upload fails due to network error
  Given the backend is unreachable
  When the user drops a valid PDF onto the upload zone
  Then the upload zone displays "Upload failed" in red
  And uploadProgress is set to null
  And the document list is not refreshed

Scenario: Drag enters then leaves without dropping
  Given the user is on the document grid page
  When the user drags a file over the upload zone
  Then the zone activates (isDragging = true)
  When the user moves the file away without dropping
  Then the zone returns to default style (isDragging = false)
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Drop zone container div | interactive container; receives all four drag events and onClick | `DocumentGrid.jsx:782–809` |
| Hidden file input | `<input type="file">` accepting `.pdf,.jpg,.jpeg,.png`; triggered via `fileInputRef.current.click()` on zone click | `DocumentGrid.jsx:791–797` |
| Upload icon | decorative text `⬆️` | `DocumentGrid.jsx:798` |
| Upload text | conditional text: "Uploading…" / "✅ Upload complete!" / "Drop files here or click to upload" based on `uploadProgress` | `DocumentGrid.jsx:799–805` |
| Format hint | static text "PDF, JPEG, PNG" | `DocumentGrid.jsx:806` |
| Error message | conditionally rendered red `<p>` showing `uploadError` when non-null | `DocumentGrid.jsx:807` |
| Active drag style | `styles.uploadAreaActive` — blue dashed border + `#f0f4ff` background applied when `isDragging === true` | `DocumentGrid.jsx:784` |

---

## Out of scope

- **Click-to-browse upload** (`handleFileInputClick` / `handleFileInputChange`, lines 717–726): shares the
  same `uploadFile` method as the drop handler but is triggered by a click on the zone rather than a drop
  event. Covered under feature key `document-grid-upload-click`.
- **UploadButton component** (`frontend/src/components/UploadButton.jsx`): a separate functional component
  that duplicates the click-upload pattern. Covered under feature key `upload-button`.
- **Document list rendering**: the grid/list of document cards rendered after upload completes belongs to
  the `document-grid` feature key.
- **documents_v2 trigger bug**: the `trg_sync_to_v2` trigger copies new uploads to `documents_v2` without
  the `tags` column. This is a known schema defect, not behavior owned by this UI feature.
