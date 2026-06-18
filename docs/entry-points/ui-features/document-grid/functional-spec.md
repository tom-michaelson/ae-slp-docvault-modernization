# Functional spec — Document Grid

**Key:** `document-grid`
**URL:** `/` (rendered as a panel inside the authenticated App Workspace; no dedicated route)
**Legacy source:** `frontend/src/components/DocumentGrid.jsx`

---

## Purpose

The Document Grid is the primary browsing surface of the DocVault application. It presents the user's uploaded documents as either card tiles (grid mode) or compact rows (list mode), lets the user filter and sort without additional server round-trips, and provides inline access to file upload (drag-and-drop or click-to-browse) and per-document tag editing. It is the only panel rendered for the Documents, Tags, and Upload sections of the sidebar — view changes are cosmetic rather than route-driven.

---

## Functional behavior

### componentDidMount — initial document load

1. Sets `state.loading = true`, `state.error = null`.
2. Calls `fetchDocuments()` → `GET /api/documents`.
3. Backend executes `SELECT * FROM documents_v2 ORDER BY uploaded_at DESC`; returns `{ documents: [...] }`.
4. On success: stores array in `state.documents`, sets `state.loading = false`.
5. On failure: stores error message string in `state.error`, sets `state.loading = false`.

### handleRefresh — manual reload

1. Triggered by clicking the **↻ Refresh** button.
2. Delegates to `loadDocuments()` — identical flow to the initial load.

### handleSearch — keyword search (delegated from SearchBar via ref)

1. Called by the parent App component via `documentGridRef.current.handleSearch(query)`.
2. If `query.trim()` is empty: calls `loadDocuments()` to restore the full list.
3. If non-empty: sets `state.loading = true`, calls `searchDocuments(query)` → `GET /api/search?q={query}`.
4. Backend delegates to `SearchOrchestrator.search(query)` which queries `documents_v2`.
5. On success: replaces `state.documents` with `response.data.results`.
6. On failure: stores error string in `state.error`.

### handleFilterChange / handleSortChange — client-side filter + sort (no API call)

1. Triggered by the text filter input (`onChange`) or file-type `<select>` (`onChange`).
2. Updates `state.filters.searchQuery` or `state.filters.fileType` (or `state.sortBy`).
3. During `render()`, `filterDocuments(documents, filters)` applies both filters:
   - `fileType`: exact MIME-type match.
   - `searchQuery`: case-insensitive substring match against `doc.name` and each element of `doc.tags`.
4. `sortDocuments(displayDocs, sortBy)` then sorts the filtered result:
   - `'date'` (default): descending by `uploaded_at`.
   - `'name'`: `localeCompare` ascending.
   - `'type'`: `file_type` `localeCompare` ascending.
5. No network call — operates entirely on `state.documents`.

### handleViewToggle — grid ↔ list toggle

1. Triggered by the view-toggle button (shows `☰` in grid mode, `⊞` in list mode).
2. Flips `state.viewMode` between `'grid'` and `'list'`.
3. Grid mode uses CSS Grid with `repeat(auto-fill, minmax(280px, 1fr))`.
4. List mode uses a flex column of horizontal rows.

### handleDocumentClick — document selection

1. Triggered by clicking any card or list row.
2. Sets `state.selectedDocument` to the clicked document object (highlights it visually).
3. If `props.onDocumentSelect` is provided, calls it with the document — the parent App uses this to open the PreviewPanel.

### uploadFile — file upload (drag-and-drop or file picker)

1. Entry points: `handleDrop(e)` (drag-and-drop) or `handleFileInputChange(e)` (hidden `<input type="file">`).
2. Both extract the first `File` object and call `uploadFile(file)`.
3. Sets `state.uploadProgress = 'uploading'`, `state.uploadError = null`.
4. Builds a `FormData` with fields `file` (the binary) and `name` (the filename).
5. Calls `uploadDocument(formData)` → `POST /api/upload` (Content-Type: multipart/form-data).
6. Backend: multer saves file to `config.uploadDir` as `{uuid}{ext}`; inserts row into `documents`; trigger copies to `documents_v2` (omitting `tags`).
7. On success: sets `state.uploadProgress = 'done'`; calls `loadDocuments()` to refresh list; resets `uploadProgress` to `null` after 2 seconds.
8. On failure: sets `state.uploadError` with server error string or `'Upload failed'`.
9. Accepted MIME types (enforced by backend multer and frontend `<input accept>`): `application/pdf`, `image/jpeg`, `image/png`.

### handleOpenTagEditor / handleAddTag / handleRemoveTag / handleSaveTags — inline tag editor

1. **Open:** clicking the 🏷️ button on any card or list row calls `handleOpenTagEditor(e, doc)`. Stops propagation to prevent document-selection. Copies `doc.tags` into `state.tagEditorTags`, sets `state.tagEditorVisible = true`.
2. **Add tag:** user types in the tag input and presses Enter or clicks **Add**. `handleAddTag()` trims input; adds if non-empty, not already present, and count < 10.
3. **Remove tag:** clicking `×` next to a tag calls `handleRemoveTag(tag)`.
4. **Save:** `handleSaveTags()` calls `updateTags(docId, tagEditorTags)` → `PUT /api/documents/{id}/tags` with body `{ tags: [...] }`.
5. Backend validates: tags must be an array; filters to non-empty strings; rejects if > 10 items; executes `UPDATE documents_v2 SET tags = $1 WHERE id = $2 RETURNING id, tags`.
6. On success: optimistically updates `state.documents` (maps array, replaces matching doc's tags in-place), closes modal.
7. On failure: logs error to console; keeps modal open with `state.tagSaving = false`.
8. **Cancel / overlay click:** calls `handleCloseTagEditor()`, discards local changes.

---

## Acceptance criteria

```gherkin
Scenario: Initial load displays all documents ordered by upload date
  Given the user is authenticated
  And documents_v2 contains 3 documents uploaded at different times
  When the Document Grid mounts
  Then GET /api/documents is called
  And the grid renders 3 document cards in descending uploaded_at order
  And the subtitle reads "3 documents"

Scenario: Empty state when no documents exist
  Given the user is authenticated
  And documents_v2 is empty
  When the Document Grid mounts
  Then the grid renders the empty-state panel
  And the empty-state shows "📂 No documents found"
  And the empty-state shows "Upload a document to get started"

Scenario: Error state when API call fails
  Given the user is authenticated
  And GET /api/documents returns a 500 error
  When the Document Grid mounts
  Then state.error is set to the server error message or "Failed to load documents"
  And the error panel is rendered with the message
  And a "Retry" button is visible

Scenario: Retry after error reloads documents
  Given the error state is displayed
  When the user clicks "Retry"
  Then loadDocuments() is called
  And the loading indicator appears
  And the error panel is replaced by the document list on success

Scenario: Client-side text filter narrows visible documents
  Given 5 documents are loaded ("invoice.pdf", "photo.jpg", "report.pdf", "budget.pdf", "photo2.png")
  When the user types "photo" in the filter input
  Then only "photo.jpg" and "photo2.png" are rendered
  And the subtitle reads "2 documents"
  And no API call is made

Scenario: Client-side file type filter
  Given 4 documents of mixed types are loaded
  When the user selects "PDF" from the type dropdown
  Then only documents with file_type "application/pdf" are rendered
  And no API call is made

Scenario: Text filter also matches tags
  Given a document named "report.pdf" has tags ["Q1", "finance"]
  When the user types "finance" in the filter input
  Then "report.pdf" is included in the filtered results

Scenario: View mode toggle switches between grid and list
  Given documents are displayed in grid mode
  When the user clicks the view-toggle button (shows "☰")
  Then viewMode becomes "list"
  And documents render as horizontal rows instead of cards
  And the button now shows "⊞"

Scenario: Successful file upload via drag-and-drop
  Given the user drags a PDF onto the upload area
  When the drop event fires
  Then uploadFile(file) is called
  And POST /api/upload is called with multipart/form-data
  And the upload area shows "Uploading..."
  And on success the area shows "✅ Upload complete!"
  And loadDocuments() is called to refresh the list

Scenario: Upload rejected for unsupported file type
  Given the user drops a .docx file onto the upload area
  When the backend multer filter rejects the file
  Then POST /api/upload returns a 400 error
  And state.uploadError is set to the server error message or "Upload failed"
  And the error message is displayed below the upload icon

Scenario: Tag editor opens with existing tags pre-populated
  Given a document has tags ["legal", "2024"]
  When the user clicks the 🏷️ button on that document card
  Then the tag editor modal opens
  And the tag list shows "legal" and "2024" as removable chips

Scenario: Adding a duplicate tag is a no-op
  Given the tag editor is open with tags ["legal"]
  When the user types "legal" and clicks Add
  Then the tag list still shows only one "legal" chip

Scenario: Tag limit enforced at 10 tags
  Given the tag editor already has 10 tags
  When the user attempts to add an 11th tag
  Then handleAddTag() does not add the tag (count check: tagEditorTags.length < 10)

Scenario: Successful tag save updates document in-place
  Given the tag editor is open and the user adds a new tag "urgent"
  When the user clicks Save
  Then PUT /api/documents/{id}/tags is called with the updated tags array
  And on success the document card immediately shows the new tag without a page reload
  And the tag editor modal closes

Scenario: Search delegates to GET /api/search
  Given the Document Grid is mounted
  When the parent calls documentGridRef.current.handleSearch("invoice")
  Then GET /api/search?q=invoice is called
  And state.documents is replaced with the search results
  And the subtitle reflects the new count

Scenario: Clearing search restores full document list
  Given a search for "invoice" is active showing 1 result
  When the parent calls documentGridRef.current.handleSearch("")
  Then loadDocuments() is called (GET /api/documents)
  And all documents are displayed again
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| "Documents" heading | text | `DocumentGrid.jsx:973` |
| Document count subtitle | text (dynamic) | `DocumentGrid.jsx:974-976` |
| Text filter input | `<input type="text" placeholder="Filter...">` | `DocumentGrid.jsx:979-985` |
| File type filter | `<select>` with options: All Types / PDF / JPEG / PNG | `DocumentGrid.jsx:986-995` |
| View-toggle button | button (grid↔list icon, active state styled) | `DocumentGrid.jsx:996-1002` |
| Refresh button | button (↻ Refresh) | `DocumentGrid.jsx:1003-1005` |
| Upload area | drag-and-drop zone + hidden `<input type="file" accept=".pdf,.jpg,.jpeg,.png">` | `DocumentGrid.jsx:778-809` |
| Upload progress text | conditional text: "Uploading..." / "✅ Upload complete!" | `DocumentGrid.jsx:799-804` |
| Upload error message | conditional `<p style=color:red>` | `DocumentGrid.jsx:807` |
| Loading indicator | conditional div "Loading documents..." | `DocumentGrid.jsx:1016-1020` |
| Empty-state panel | conditional div with 📂 icon + two text lines | `DocumentGrid.jsx:936-943` |
| Error panel + Retry button | conditional div with error text and retry button | `DocumentGrid.jsx:946-956` |
| Document card (grid mode) | loop over `displayDocs` — shows file icon, name, type label, date, preview link (if previewable), tags | `DocumentGrid.jsx:865-904` |
| Document list row (list mode) | loop over `displayDocs` — shows file icon, name, type+date meta, tag count, tag-edit button | `DocumentGrid.jsx:907-933` |
| Selected-card highlight | conditional style (border + background) on card/row when `selectedDocument.id === doc.id` | `DocumentGrid.jsx:866-868` |
| "Preview" link (card) | conditional `<span>` shown when `isPreviewable(doc.file_type)` is true | `DocumentGrid.jsx:889-891` |
| Tag chips on card | loop over `doc.tags` | `DocumentGrid.jsx:892-901` |
| "No tags" placeholder | conditional italic text when tags are empty | `DocumentGrid.jsx:901` |
| Edit tags button (card) | button with 🏷️ icon | `DocumentGrid.jsx:879-885` |
| Edit tags button (list row) | button with 🏷️ icon | `DocumentGrid.jsx:925-931` |
| Tag editor modal overlay | fixed-position overlay (z-index 1000), click-outside closes | `DocumentGrid.jsx:812-862` |
| Tag editor input | `<input type="text" maxLength=50 placeholder="Add a tag...">` | `DocumentGrid.jsx:822-829` |
| Tag editor Add button | button (adds tag to local list) | `DocumentGrid.jsx:831-833` |
| Tag editor tag chips | loop over `tagEditorTags` with × remove button | `DocumentGrid.jsx:836-846` |
| Tag editor Cancel button | button (discards changes, closes modal) | `DocumentGrid.jsx:849-851` |
| Tag editor Save button | button (disabled while saving; shows "Saving..." when `tagSaving` is true) | `DocumentGrid.jsx:852-858` |
| Status bar | bottom bar showing view mode, sort, active filter, and "N of M documents" count | `DocumentGrid.jsx:1037-1043` |

---

## Out of scope

- **PreviewPanel:** opened when `props.onDocumentSelect` is called with a previewable document. The "Preview" span in a card triggers selection, which the parent App translates into a PreviewPanel display (`app-workspace` feature key).
- **Sidebar navigation:** the sidebar's Documents / Upload / Tags items change `App.activeSection` state; the DocumentGrid itself has no awareness of this and renders identically for all three sections.
- **SearchBar:** the text input in the app header (separate component) calls `DocumentGrid.handleSearch()` via a React ref — the search bar UI is analysed under `app-workspace-header-search-nav`.
- **Auth guard:** the DocumentGrid is only mounted after `AuthContext.isAuthenticated` is true; the login redirect is handled by the parent App component (`login` feature key).
