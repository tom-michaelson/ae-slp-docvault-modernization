# Functional spec — Application workspace shell

**Key:** `app-workspace`
**URL:** `GET /` (single-page application — URL never changes during use)
**Legacy source:** `frontend/src/App.jsx`

---

## Purpose

The application workspace shell is the top-level React component that owns the entire DocVault user experience. It enforces the authentication gate (showing `LoginForm` before the user is authenticated, the full workspace after), lays out the persistent chrome (header navigation bar, sidebar), and coordinates document browsing, search, upload, and preview within a fixed viewport layout. Every user-visible interaction routes through this component or one of its direct children.

---

## Functional behavior

### Initial mount — auth bypass check

1. `AppWithAuth` renders a Redux `<Provider>` wrapping an `<AuthProvider>` wrapping `<App>`.
2. `AuthProvider.componentDidMount` calls `checkAuthBypass()`.
3. `checkAuthBypass` issues `GET /api/health`.
4. If `response.data.skipAuth === true` (backend started with `DEV_SKIP_AUTH=true`), `AuthProvider` sets `isAuthenticated=true` and `user={ email: 'dev@docvault.local', role: 'admin' }` — the login form is skipped entirely.
5. If the health check fails or returns `skipAuth: false`, the user must authenticate via the login form.

---

### Login — `LoginForm.handleSubmit` → `AuthProvider.login`

1. User fills in email and password fields and submits the form.
2. `LoginForm.handleSubmit` calls `this.context.login(email, password)`.
3. `AuthProvider.login` issues `POST /api/auth/login` with `{ email, password }`.
4. On success (HTTP 200), the backend returns `{ token, refreshToken }`. Both are stored in `localStorage` under `'docvault_token'` and `'docvault_refresh_token'`.
5. `AuthProvider.login` immediately issues `POST /api/auth/refresh` with `{ refreshToken }`.
6. **CRASH (FR-007):** The backend `/refresh` endpoint returns `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }`. The next line in `AuthProvider` calls `response.data.token.split('.')` — since `response.data.token` is `undefined`, this throws a `TypeError`. The catch block sets `error` state and sets `isAuthenticated=false`. Login always fails for real credentials.
7. On credential failure (HTTP 401 from `/login`), `AuthProvider` sets `error='Invalid credentials'` and the LoginForm displays it.

---

### Navigation — `App.handleNavigate`

1. Header nav links ("Documents", "Upload", "Search") and Sidebar list items call `onNavigate(sectionId)`.
2. `App.handleNavigate` calls `this.setState({ activeSection: sectionId })`.
3. `Sidebar` re-renders with the newly active section highlighted.
4. There is no route change — the URL stays at `/`. The sections `'upload'` and `'search'` and `'tags'` update `activeSection` but the `App.render()` always renders the same `DocumentGrid` regardless of `activeSection` (the section value is passed down but `DocumentGrid` does not conditionally render based on it). Navigation is cosmetic-only in the current implementation.

---

### Document list load — `DocumentGrid.componentDidMount`

1. On mount, `DocumentGrid.loadDocuments()` is called.
2. Sets `loading=true`, issues `GET /api/documents`.
3. On success, sets `documents=response.data.documents`, `loading=false`.
4. On failure, sets `error='Failed to load documents'`, `loading=false` (Retry button visible).

---

### Search — `App.handleSearch` → `DocumentGrid.handleSearch`

1. User types a query in `SearchBar` and submits the form.
2. `SearchBar.handleSubmit` calls `props.onSearch(query.trim())`.
3. `App.handleSearch` delegates to `this.documentGridRef?.handleSearch(query)` via an imperative ref.
4. If `query` is empty, `DocumentGrid.handleSearch` calls `loadDocuments()` to restore the full list.
5. Otherwise issues `GET /api/search?q={encodedQuery}`.
6. On success, replaces `DocumentGrid.state.documents` with `response.data.results`.
7. On failure, sets `error='Search failed'`.

`DocumentGrid` also provides a local "Filter..." text input and a file-type dropdown that filter `DocumentGrid.state.documents` in memory (client-side) without an API call.

---

### Document selection and preview — `App.handleDocumentSelect`

1. User clicks a document card or list row in `DocumentGrid`.
2. `DocumentGrid.handleDocumentClick` calls `props.onDocumentSelect(doc)`.
3. `App.handleDocumentSelect` sets `selectedDocument=doc`, `showPreview=true`.
4. `PreviewPanel` renders in the right column with the selected document.
5. `PreviewPanel.render` calls `getPreviewUrl(document.id)` → constructs URL `{API_BASE_URL}/documents/{id}/preview`.
6. If `file_type === 'application/pdf'`, renders a `react-pdf` `<Document>` component pointing at the preview URL. PDF page count is tracked in `PreviewPanel.state.numPages`.
7. If `file_type` starts with `'image/'`, renders an `<img>` pointing at the preview URL.
8. Otherwise renders "Preview not available for this file type."
9. File size display calls `formatFileSize` imported from `DocumentGrid.jsx` (anti-pattern: utility exported from a god component).

---

### Close preview — `App.handleClosePreview`

1. User clicks the "✕ Close" button in `PreviewPanel`.
2. `PreviewPanel` calls `props.onClose()`.
3. `App.handleClosePreview` sets `selectedDocument=null`, `showPreview=false`.
4. `PreviewPanel` is unmounted.

---

### Upload — `DocumentGrid.uploadFile`

1. User drops a file onto the upload drop zone or clicks it and selects a file via the hidden `<input type="file">`.
2. Accepted types: `application/pdf`, `image/jpeg`, `image/png`.
3. `DocumentGrid.uploadFile(file)` builds a `FormData` with fields `file` and `name` (original filename).
4. Issues `POST /api/upload` with `Content-Type: multipart/form-data`.
5. Backend inserts into `documents` table. The trigger `trg_sync_to_v2` copies the row to `documents_v2` but **omits tags** — any tags in the formData body are silently dropped (FR-008).
6. On success, `DocumentGrid` reloads the document list.
7. `uploadProgress` transitions: `null` → `'uploading'` → `'done'` (shown in drop zone label) → `null` (after 2 s timeout).

---

### Tag editing — `DocumentGrid.handleSaveTags`

1. User clicks the 🏷️ button on a document card or list row.
2. `DocumentGrid.handleOpenTagEditor` opens a modal overlay with the current tags pre-populated.
3. User adds tags (text input + "Add" button or Enter key); each tag is limited to 50 characters; maximum 10 tags per document.
4. User clicks "Save".
5. `DocumentGrid.handleSaveTags` issues `PUT /api/documents/{id}/tags` with `{ tags: [...] }`.
6. On success, updates the document in `DocumentGrid.state.documents` in-place.
7. Closes the modal overlay.

---

### Logout — `AuthProvider.logout`

1. Called from `AuthProvider.logout()` (wired to any UI element that invokes it via context — no logout button exists in the current layout).
2. Clears `user`, `token`, `isAuthenticated` from `AuthProvider` state.
3. Removes `'docvault_token'` and `'docvault_refresh_token'` from `localStorage`.

---

## Acceptance criteria

```gherkin
Scenario: Dev bypass — workspace loads without login
  Given the backend is running with DEV_SKIP_AUTH=true
  When the app mounts and GET /api/health returns { skipAuth: true }
  Then AuthContext.isAuthenticated is set to true
  And the workspace shell renders (Header, Sidebar, SearchBar, DocumentGrid)
  And the LoginForm is not rendered

Scenario: Login attempt always crashes (FR-007)
  Given the backend is running without DEV_SKIP_AUTH
  And GET /api/health returns { skipAuth: false }
  When the user submits valid credentials in LoginForm
  Then POST /api/auth/login succeeds and returns { token, refreshToken }
  And POST /api/auth/refresh is called with the refreshToken
  And the backend returns { session: {...} } (not { token: "..." })
  Then AuthContext.login throws TypeError: Cannot read properties of undefined (reading 'split')
  And the LoginForm displays the error message
  And AuthContext.isAuthenticated remains false

Scenario: Login fails with wrong credentials
  Given the backend is running without DEV_SKIP_AUTH
  When the user submits an incorrect email or password
  Then POST /api/auth/login returns HTTP 401
  And the LoginForm displays "Login failed. The app has crashed — check the console."
  And AuthContext.isAuthenticated remains false

Scenario: Document list loads on workspace mount
  Given the user is authenticated
  When the workspace mounts
  Then GET /api/documents is called
  And DocumentGrid shows a loading indicator while the request is in flight
  And upon success the document grid renders one card per document

Scenario: Empty document vault
  Given the user is authenticated
  And GET /api/documents returns { documents: [] }
  Then DocumentGrid renders the empty state: "📂 No documents found" with hint "Upload a document to get started"

Scenario: Search returns matching documents
  Given the user is authenticated
  And the document list is loaded
  When the user types "invoice" in SearchBar and submits
  Then GET /api/search?q=invoice is called
  And DocumentGrid replaces its document list with the search results

Scenario: Empty search restores full list
  Given the user has previously searched
  When the user clears the search query and submits an empty string
  Then DocumentGrid calls loadDocuments() to restore the full list via GET /api/documents

Scenario: Document selection opens preview panel
  Given the workspace is loaded with at least one document
  When the user clicks a document card
  Then App.state.showPreview becomes true
  And PreviewPanel renders in the right column showing the document name and metadata
  And for PDF documents a react-pdf Document viewer is rendered via GET /api/documents/{id}/preview
  And for image documents an <img> is rendered via GET /api/documents/{id}/preview

Scenario: Closing preview hides panel
  Given a document is selected and PreviewPanel is visible
  When the user clicks "✕ Close"
  Then App.state.showPreview becomes false
  And PreviewPanel is unmounted

Scenario: File upload via drag-and-drop
  Given the workspace is loaded
  When the user drops a PDF file onto the upload drop zone
  Then POST /api/upload is called with the file
  And the drop zone label shows "Uploading..." then "✅ Upload complete!"
  And DocumentGrid reloads the document list after success
  And uploaded tags are NULL in documents_v2 (FR-008 — trigger omits tags column)

Scenario: File upload rejects unsupported types
  Given the workspace is loaded
  When the user selects a .docx file via the file picker
  Then the multer file filter on the backend returns 400 "Invalid file type"
  And DocumentGrid shows the upload error message

Scenario: Tag editing saves tags to documents_v2
  Given a document is displayed in DocumentGrid
  When the user clicks the 🏷️ button
  Then the tag editor modal opens showing the current tags
  When the user adds a new tag and clicks Save
  Then PUT /api/documents/{id}/tags is called with the updated tag array
  And the document card updates in-place with the new tags

Scenario: Tag limit enforced at 10
  Given the tag editor modal is open
  And the document already has 10 tags
  When the user tries to add an 11th tag
  Then the "Add" button does not add the tag (client-side guard: tagEditorTags.length < 10)

Scenario: Sidebar navigation is cosmetic only
  Given the workspace is loaded
  When the user clicks "Upload" in the Sidebar
  Then App.state.activeSection becomes 'upload'
  And the Sidebar highlights "⬆️ Upload"
  And the URL remains "/"
  And DocumentGrid continues to render (no conditional section routing exists)
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| DocVault title heading | text (always visible) | `Header.jsx:35` |
| "Documents" nav link | click → `onNavigate('documents')` | `Header.jsx:37` |
| "Upload" nav link | click → `onNavigate('upload')` | `Header.jsx:40` |
| "Search" nav link | click → `onNavigate('search')` | `Header.jsx:43` |
| Sidebar nav list | loop over 4 sections; active section highlighted | `Sidebar.jsx:44` |
| "📁 All Documents" sidebar item | click → `onNavigate('documents')` | `Sidebar.jsx:35` |
| "⬆️ Upload" sidebar item | click → `onNavigate('upload')` | `Sidebar.jsx:36` |
| "🔍 Search" sidebar item | click → `onNavigate('search')` | `Sidebar.jsx:37` |
| "🏷️ Tags" sidebar item | click → `onNavigate('tags')` | `Sidebar.jsx:38` |
| Search text input | text input, controlled | `SearchBar.jsx:40` |
| Search submit button | form submit → `onSearch(query)` | `SearchBar.jsx:47` |
| "Filter..." inline text input | controlled; filters DocumentGrid in-memory | `DocumentGrid.jsx:980` |
| File-type dropdown | `<select>`; values: All/PDF/JPEG/PNG | `DocumentGrid.jsx:986` |
| Grid/List view toggle button | click → `handleViewToggle` | `DocumentGrid.jsx:996` |
| Refresh button | click → `handleRefresh` → `loadDocuments()` | `DocumentGrid.jsx:1003` |
| Upload drop zone | drag-and-drop + click to browse; accepts PDF/JPEG/PNG | `DocumentGrid.jsx:782` |
| Hidden file input | `<input type="file" accept=".pdf,.jpg,.jpeg,.png">` | `DocumentGrid.jsx:791` |
| Document card (grid mode) | click → `handleDocumentClick`; shows name, type, date, tags | `DocumentGrid.jsx:865` |
| Document list row (list mode) | click → `handleDocumentClick`; shows icon, name, type, date, tag count | `DocumentGrid.jsx:907` |
| 🏷️ tag edit button (per card/row) | click → `handleOpenTagEditor(e, doc)` | `DocumentGrid.jsx:879`, `DocumentGrid.jsx:925` |
| "Preview" text link (previewable docs) | conditionally rendered when `isPreviewable(doc.file_type)` | `DocumentGrid.jsx:889` |
| Document tag chips | loop over `doc.tags`; read-only display | `DocumentGrid.jsx:893` |
| "No tags" hint | conditional text when `doc.tags` is empty | `DocumentGrid.jsx:901` |
| Empty-state icon + text | conditional; shown when list is empty and not loading | `DocumentGrid.jsx:936` |
| Loading indicator | conditional text; shown while API request in flight | `DocumentGrid.jsx:1016` |
| Error container + Retry button | conditional; shown on fetch failure | `DocumentGrid.jsx:946` |
| Status bar | text; shows view/sort/filter summary and document counts | `DocumentGrid.jsx:1037` |
| Tag editor modal overlay | fixed overlay; shown when `tagEditorVisible=true` | `DocumentGrid.jsx:818` |
| Tag input field | text input inside modal; max 50 chars | `DocumentGrid.jsx:822` |
| "Add" tag button | click or Enter → `handleAddTag` | `DocumentGrid.jsx:831` |
| Removable tag chip | click ×  → `handleRemoveTag` | `DocumentGrid.jsx:836` |
| Tag editor "Cancel" button | click → `handleCloseTagEditor` | `DocumentGrid.jsx:849` |
| Tag editor "Save" button | click → `handleSaveTags` → `PUT /api/documents/:id/tags` | `DocumentGrid.jsx:852` |
| Preview panel document title | text; `document.name` | `PreviewPanel.jsx:100` |
| "✕ Close" button | click → `onClose` → `App.handleClosePreview` | `PreviewPanel.jsx:101` |
| File type metadata | text; `document.file_type` | `PreviewPanel.jsx:105` |
| File size metadata | text; `formatFileSize(document.file_size)` (imported from DocumentGrid.jsx) | `PreviewPanel.jsx:107` |
| react-pdf Document viewer | conditional; shown when `file_type === 'application/pdf'` | `PreviewPanel.jsx:114` |
| PDF page indicator | text; "Page N of M" | `PreviewPanel.jsx:122` |
| Image preview | `<img>`; shown when `file_type` starts with `'image/'` | `PreviewPanel.jsx:131` |
| "Preview not available" message | text; shown for unsupported file types | `PreviewPanel.jsx:136` |
| Login email input | `<input type="email">`; required | `LoginForm.jsx:96` |
| Login password input | `<input type="password">`; required | `LoginForm.jsx:103` |
| "Sign In" submit button | form submit → `handleSubmit`; disabled during loading | `LoginForm.jsx:112` |
| Login error message | conditional text; shows AuthContext error | `LoginForm.jsx:116` |

---

## Out of scope

- **Redux store** (`frontend/src/store.js`): The Redux store is instantiated and wrapped around the app but none of the document, auth, or search state is actually managed through Redux actions in the current implementation — all state lives in React component `this.state`. The Redux store, its 12 reducers, and the custom middleware are dead weight. They are not part of the workspace's runtime behavior and do not need to be replicated in Angular.
- **`ActionCreatorFactory.js`**: Imported by `store.js` but the action creators it produces (`setDocuments`, `setUser`, `toggleSidebar`, `setSearchQuery`) are never dispatched by any component.
- **`lib/` directory** (`frontend/src/lib/`): `libFormatDate`, `humanFileSize`, `categorizeFile`, and `libGetDocuments` are imported by `DocumentGrid` but are dead imports — the component uses the `utils/` versions exclusively.
- **Batch selection feature**: `DocumentGrid.state.batchSelected` and `batchMode` fields exist but are never mutated; the UI for batch operations was commented out.
