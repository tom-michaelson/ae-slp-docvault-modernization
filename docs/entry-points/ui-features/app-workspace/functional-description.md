# Functional Description: Main Application Workspace

> **Entry Point**: `app-workspace`
> **Location**: `frontend/src/App.jsx`
> **Type**: UI / Page
> **Domain**: documents
> **Legacy URL**: `/`

## Executive Summary

The Main Application Workspace is the root React component (`App.jsx`) that owns the entire DocVault user experience within a single-page application. It acts as an authentication gate — when `AuthContext.isAuthenticated` is `false` it renders only `LoginForm`; when `true` it renders the full workspace shell comprising a top header bar (`Header`), a left sidebar (`Sidebar`), a search bar (`SearchBar`), a document grid/list panel (`DocumentGrid`), and an optional right-side preview panel (`PreviewPanel`). The URL permanently stays at `/` regardless of which section or document the user navigates to.

`AppWithAuth` (the exported default) wraps `App` in a Redux `<Provider>` and an `<AuthProvider>`. On mount, `AuthProvider.componentDidMount` issues `GET /api/health`; if the backend returns `{ skipAuth: true }` (activated by the `DEV_SKIP_AUTH` environment variable), the app auto-authenticates as `dev@docvault.local` and bypasses the login form. In production (without `DEV_SKIP_AUTH`), all login attempts crash unconditionally due to **FR-007**: after a successful `POST /api/auth/login`, the code immediately calls `POST /api/auth/refresh`, but the backend returns `{ session: {...} }` instead of `{ token: '...' }`, causing `response.data.token.split('.')` to throw a `TypeError`. The catch block stores the error and leaves `isAuthenticated = false`. Effective authentication is impossible without the bypass.

Once authenticated, the workspace mounts `DocumentGrid` which immediately loads all documents via `GET /api/documents`. The `App` component coordinates search (delegated to `DocumentGrid` via an imperative `ref`), document selection (stores `selectedDocument` in `App.state` and mounts `PreviewPanel`), navigation (updates `activeSection` in `App.state` — no actual routing), preview close, and file upload (handled entirely within `DocumentGrid`). Tag editing is managed by an inline modal within `DocumentGrid`. The Redux store installed at the root (`store.js`) is wired but entirely dormant — all state lives in React `this.state` across the component tree.

---

## User Inputs

### Form Fields

| Field Name | JS Type | Source | Required | Notes |
|---|---|---|---|---|
| `LoginForm.state.email` | `string` | `<input type="email">` controlled state | yes | Sent as `email` in `POST /api/auth/login` body |
| `LoginForm.state.password` | `string` | `<input type="password">` controlled state | yes | Sent as `password` in `POST /api/auth/login` body |
| `SearchBar.query` (local state) | `string` | `<input type="text">` controlled state in `SearchBar` | no | Trimmed before use; empty string restores full document list |
| `DocumentGrid.filters.searchQuery` | `string` | `<input placeholder="Filter...">` controlled state | no | Client-side in-memory filter — does NOT issue an API call |
| `DocumentGrid.filters.fileType` | `string` | `<select>` controlled state; values: `''`, `'application/pdf'`, `'image/jpeg'`, `'image/png'` | no | Client-side in-memory filter |
| `DocumentGrid.tagEditorInput` | `string` | `<input placeholder="Add a tag...">` inside modal; `maxLength={50}` | no | Single pending tag entry; committed by clicking "Add" or pressing Enter |
| File via upload drop zone | `File` | `<input type="file" accept=".pdf,.jpg,.jpeg,.png">` (hidden) or drag-and-drop `dataTransfer.files[0]` | no | Only first file is used when multiple files are dropped |

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
|---|---|---|---|
| Sign in | `<button type="submit">Sign In</button>` (`LoginForm.jsx:112`) | `LoginForm.handleSubmit` → `AuthContext.login` → `POST /api/auth/login` then `POST /api/auth/refresh` | Form submit |
| Navigate to Documents | `<span>Documents</span>` (`Header.jsx:37`) or `<li>📁 All Documents</li>` (`Sidebar.jsx:35`) | `App.handleNavigate('documents')` → `App.setState({ activeSection: 'documents' })` | Click |
| Navigate to Upload | `<span>Upload</span>` (`Header.jsx:40`) or `<li>⬆️ Upload</li>` (`Sidebar.jsx:36`) | `App.handleNavigate('upload')` → `App.setState({ activeSection: 'upload' })` | Click |
| Navigate to Search | `<span>Search</span>` (`Header.jsx:43`) or `<li>🔍 Search</li>` (`Sidebar.jsx:37`) | `App.handleNavigate('search')` → `App.setState({ activeSection: 'search' })` | Click |
| Navigate to Tags | `<li>🏷️ Tags</li>` (`Sidebar.jsx:38`) | `App.handleNavigate('tags')` → `App.setState({ activeSection: 'tags' })` | Click |
| Search documents | `<button>Search</button>` (`SearchBar.jsx:47`) | `SearchBar.handleSubmit` → `props.onSearch(query)` → `App.handleSearch` → `DocumentGrid.handleSearch` → `GET /api/search?q={query}` | Form submit |
| Select document (grid) | Document card (`DocumentGrid.jsx:865`) | `DocumentGrid.handleDocumentClick(doc)` → `props.onDocumentSelect(doc)` → `App.handleDocumentSelect` | Click |
| Select document (list) | Document list row (`DocumentGrid.jsx:907`) | `DocumentGrid.handleDocumentClick(doc)` → `props.onDocumentSelect(doc)` → `App.handleDocumentSelect` | Click |
| Close preview panel | `<button>✕ Close</button>` (`PreviewPanel.jsx:101`) | `props.onClose` → `App.handleClosePreview` → `App.setState({ selectedDocument: null, showPreview: false })` | Click |
| Upload file (drop zone) | Upload drop zone (`DocumentGrid.jsx:782`) | `DocumentGrid.handleDrop` → `DocumentGrid.uploadFile(file)` → `POST /api/upload` | Drag-and-drop |
| Upload file (file picker) | Hidden file input (`DocumentGrid.jsx:791`) | `DocumentGrid.handleFileInputChange` → `DocumentGrid.uploadFile(file)` → `POST /api/upload` | Change |
| Open tag editor | `<button>🏷️</button>` on card (`DocumentGrid.jsx:879`) or list row (`DocumentGrid.jsx:925`) | `DocumentGrid.handleOpenTagEditor(e, doc)` → opens tag modal overlay | Click (propagation stopped) |
| Add tag in editor | `<button>Add</button>` (`DocumentGrid.jsx:831`) | `DocumentGrid.handleAddTag` | Click or Enter key |
| Remove tag chip | `<span>×</span>` per tag (`DocumentGrid.jsx:836`) | `DocumentGrid.handleRemoveTag(tag)` | Click |
| Save tags | `<button>Save</button>` (`DocumentGrid.jsx:852`) | `DocumentGrid.handleSaveTags` → `PUT /api/documents/{id}/tags` | Click |
| Cancel tag edit | `<button>Cancel</button>` (`DocumentGrid.jsx:849`) or click modal backdrop | `DocumentGrid.handleCloseTagEditor` | Click |
| Toggle grid/list view | View toggle button (`DocumentGrid.jsx:996`) | `DocumentGrid.handleViewToggle` → `App.setState({ viewMode })` | Click |
| Refresh document list | `<button>↻ Refresh</button>` (`DocumentGrid.jsx:1003`) | `DocumentGrid.handleRefresh` → `DocumentGrid.loadDocuments` → `GET /api/documents` | Click |
| Retry failed load | `<button>Retry</button>` in error container | `DocumentGrid.handleRefresh` → `DocumentGrid.loadDocuments` | Click |

### URL / Route Parameters

| Parameter | Source | Optional | Default | Notes |
|---|---|---|---|---|
| (none) | — | — | — | The SPA has no client-side routing. The URL permanently stays at `/`. All section changes are reflected only in `App.state.activeSection`. |

### Browser / Session Inputs

| Source | Data | Purpose |
|---|---|---|
| `localStorage['docvault_token']` | JWT string | Read back on page reload — but `AuthProvider` does not read it on mount; `checkAuthBypass()` replaces it. No token restoration logic exists. |
| `localStorage['docvault_refresh_token']` | Refresh token string | Stored by the login flow but never read back except to pass to `POST /api/auth/refresh` during the same login session. |
| `process.env.REACT_APP_API_URL` | Base URL string | If set, overrides the default `http://localhost:3001/api` API base URL used by all `axios` calls. |

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
|---|---|---|---|
| Login form | Full-screen centered card with email, password fields and "Sign In" button | `AuthContext.isAuthenticated === false` | `App.jsx:80–81`; `LoginForm.jsx` |
| Login error message | Red text below the form; shows `LoginForm.state.error` and/or `AuthContext.error` | Error state after failed login | `LoginForm.jsx:116–119` |
| Header bar | Dark bar with "📄 DocVault" title and "Documents / Upload / Search" nav links | `isAuthenticated === true` | `App.jsx:86`; `Header.jsx` |
| Sidebar | Left column (200 px) listing 4 navigation items; active item highlighted in blue | `isAuthenticated === true` | `App.jsx:88–91`; `Sidebar.jsx` |
| Search bar | Text input + Search button in a light grey strip below the header | `isAuthenticated === true` | `App.jsx:93–95`; `SearchBar.jsx` |
| Document grid header | "Documents" title, document count/loading text, filter input, file-type dropdown, view toggle, refresh button | Always shown in workspace | `DocumentGrid.jsx:969–1007` |
| Upload drop zone | Dashed-border area showing upload instructions (or progress state) | Always shown above the document list | `DocumentGrid.jsx:778–809` |
| Loading indicator | "Loading documents..." centred text | `DocumentGrid.state.loading === true` | `DocumentGrid.jsx:1015–1020` |
| Error container | Red-bordered box with error message + Retry button | `DocumentGrid.state.error !== null` | `DocumentGrid.jsx:946–956`, `1012–1013` |
| Empty state | "📂 No documents found" + "Upload a document to get started" | `!loading && !error && displayDocs.length === 0` | `DocumentGrid.jsx:936–943`, `1023` |
| Document grid (grid mode) | CSS grid of document cards; each card shows file icon, name, file type label, upload date, optional "Preview" link, tag chips | `viewMode === 'grid'` and documents present | `DocumentGrid.jsx:865–904`, `1025–1031` |
| Document grid (list mode) | Vertical list of rows; each row shows file icon, name, type·date·tag-count metadata, 🏷️ button | `viewMode === 'list'` and documents present | `DocumentGrid.jsx:907–933`, `1025–1031` |
| Selected card highlight | Blue border and light blue background on the selected card/row | `DocumentGrid.state.selectedDocument.id === doc.id` | `DocumentGrid.jsx:867`, `909` |
| Tag chips (read-only) | Coloured pill badges, one per tag | `doc.tags && doc.tags.length > 0` | `DocumentGrid.jsx:892–898` |
| "No tags" hint | Italic grey text | `!doc.tags \|\| doc.tags.length === 0` | `DocumentGrid.jsx:900–901` |
| Tag editor modal | Full-screen overlay with modal: tag input, "Add" button, removable tag chips, Cancel/Save buttons | `DocumentGrid.state.tagEditorVisible === true` | `DocumentGrid.jsx:812–863`, `1033–1034` |
| Status bar | Small text row at bottom: current view/sort/filter summary + "X of Y documents" count | Always shown in workspace | `DocumentGrid.jsx:1037–1043` |
| Preview panel | Right-column panel showing selected document name, type, size, and content (react-pdf viewer or `<img>` or "Preview not available") | `App.state.showPreview === true` | `App.jsx:101–106`; `PreviewPanel.jsx` |
| PDF page indicator | "Page N of M" text below PDF viewer | PDF loaded successfully | `PreviewPanel.jsx:121–125` |

### Navigation / Routing

| Trigger | Destination | Condition |
|---|---|---|
| Click nav link / sidebar item | `App.state.activeSection` updated; no URL change | Always (no routing engine) |
| Successful upload | `DocumentGrid.loadDocuments()` called; grid refreshes in place | Upload succeeds |
| Tag save success | Modal closes; card/row tag chips updated in place | `PUT /api/documents/{id}/tags` succeeds |
| Document click | `PreviewPanel` mounted in right column | `App.state.showPreview = true` |
| Close preview | `PreviewPanel` unmounted | User clicks "✕ Close" |

### State Changes

| State | Change | Trigger | Notes |
|---|---|---|---|
| `localStorage['docvault_token']` | Written | Successful `POST /api/auth/login` | Also overwritten if `POST /api/auth/refresh` were to succeed (currently crashes before this line) |
| `localStorage['docvault_refresh_token']` | Written | Successful `POST /api/auth/login` | |
| `localStorage['docvault_token']` | Removed | `AuthContext.logout()` | No UI button currently calls logout |
| `localStorage['docvault_refresh_token']` | Removed | `AuthContext.logout()` | |
| `AuthContext.state.isAuthenticated` | Set to `true` | `GET /api/health` returns `skipAuth: true` | Auth bypass path only |
| `AuthContext.state.isAuthenticated` | Set to `false`, `error` set | Login crash (FR-007) catch block | |
| `App.state.activeSection` | Updated | Any nav link / sidebar click | Does not affect rendered content (no conditional routing) |
| `App.state.selectedDocument` / `showPreview` | Set to `doc` / `true` | Document click | Mounts `PreviewPanel` |
| `App.state.selectedDocument` / `showPreview` | Set to `null` / `false` | "✕ Close" button | Unmounts `PreviewPanel` |
| `DocumentGrid.state.documents` | Replaced with API result | `loadDocuments()` or `handleSearch()` | |
| `DocumentGrid.state.documents[i].tags` | Updated in-place | `handleSaveTags()` success | Optimistic local update after `PUT /api/documents/{id}/tags` |
| `DocumentGrid.state.uploadProgress` | `null` → `'uploading'` → `'done'` → `null` (after 2 s) | File upload | Drives drop-zone label copy |
| `documents` table (DB) | INSERT | `POST /api/upload` | Trigger `trg_sync_to_v2` propagates row to `documents_v2` (tags column NULL) |
| `documents_v2` table (DB) | INSERT | Trigger `trg_sync_to_v2` after upload | tags column always NULL on insert |
| `documents_v2.tags` (DB) | UPDATE | `PUT /api/documents/{id}/tags` | Only direct write path that sets non-null tags |

---

## API Dependencies

### Service Calls

| API Function | Endpoint | When Called | Data In | Data Out |
|---|---|---|---|---|
| `axios.get` (`AuthContext.jsx:38`) | `GET /api/health` | App mount (every page load) | — | `{ skipAuth: boolean }` |
| `axios.post` (`AuthContext.jsx:55`) | `POST /api/auth/login` | `LoginForm` submit | `{ email, password }` | `{ token, refreshToken }` |
| `axios.post` (`AuthContext.jsx:68`) | `POST /api/auth/refresh` | Immediately after login success | `{ refreshToken }` | `{ session: {...} }` — **crashes** (FR-007) |
| `fetchDocuments` (`api.js:34`) | `GET /api/documents` | `DocumentGrid.componentDidMount`; after upload; manual Refresh | — | `{ documents: [...] }` |
| `searchDocuments` (`api.js:42`) | `GET /api/search?q={query}` | `DocumentGrid.handleSearch(query)` when query non-empty | `q` (URL param) | `{ results: [...] }` |
| `uploadDocument` (`api.js:36`) | `POST /api/upload` | File drop / file picker | `FormData { file, name }` | (success/error) |
| `updateTags` (`api.js:40`) | `PUT /api/documents/{id}/tags` | `DocumentGrid.handleSaveTags` | `{ tags: string[] }` | (success/error) |
| `getPreviewUrl` (`api.js:43`) | `GET /api/documents/{id}/preview` | `PreviewPanel.render` (used as URL, not as fetch) | `id` (path param) | Raw file binary with Content-Type header |

### Call Sequences

**App mount — auth bypass check:**
1. `AppWithAuth` renders Redux `<Provider>` → `<AuthProvider>` → `<App>`
2. `AuthProvider.componentDidMount` → `checkAuthBypass()`
3. `GET /api/health` — if `skipAuth: true`: set `isAuthenticated=true`, synthetic user `{ email: 'dev@docvault.local', role: 'admin' }`; if `skipAuth: false` or error: do nothing → user sees `LoginForm`

**Login (normal credentials):**
1. User submits `LoginForm`
2. `LoginForm.handleSubmit` → `this.context.login(email, password)`
3. `AuthProvider.login`: `POST /api/auth/login` with `{ email, password }`
4. On HTTP 200: store `token` + `refreshToken` in `localStorage`
5. Immediately: `POST /api/auth/refresh` with `{ refreshToken }`
6. **CRASH**: `response.data.token.split('.')` → `TypeError` (FR-007)
7. Catch: set `AuthProvider.state.error`, `isAuthenticated=false`; re-throw
8. `LoginForm.handleSubmit` catch: set `LoginForm.state.error`; display error message

**Document list load (`DocumentGrid.loadDocuments`):**
1. `DocumentGrid.componentDidMount` → `loadDocuments()`
2. Set `loading=true`
3. `GET /api/documents` — on success: `documents = response.data.documents`, `loading=false`
4. On failure: `error='Failed to load documents'`, `loading=false` (Retry button shown)

**Search (`App.handleSearch` → `DocumentGrid.handleSearch`):**
1. `SearchBar.handleSubmit` → `props.onSearch(query.trim())`
2. `App.handleSearch(query)` → `this.documentGridRef?.handleSearch(query)` (imperative ref)
3. If `query.trim()` is empty: `DocumentGrid.handleSearch` calls `loadDocuments()` to restore full list
4. Otherwise: `GET /api/search?q={encodedQuery}` → replace `DocumentGrid.state.documents` with `response.data.results`
5. On failure: `DocumentGrid.state.error = 'Search failed'`

**Document selection and preview:**
1. `DocumentGrid.handleDocumentClick(doc)` → `DocumentGrid.setState({ selectedDocument: doc })`
2. → `props.onDocumentSelect(doc)` → `App.handleDocumentSelect(doc)`
3. `App.setState({ selectedDocument: doc, showPreview: true })` → `PreviewPanel` mounts
4. `PreviewPanel.render` calls `getPreviewUrl(document.id)` → constructs URL `{API_BASE_URL}/documents/{id}/preview`
5. If PDF: `react-pdf <Document file={previewUrl}>` issues fetch to preview URL
6. If image: `<img src={previewUrl}>` fetches image

**File upload:**
1. Drop or file input change → `DocumentGrid.uploadFile(file)`
2. Set `uploadProgress='uploading'`
3. Build `FormData { file, name: file.name }` → `POST /api/upload`
4. Backend inserts into `documents` table; trigger copies to `documents_v2` (tags = NULL)
5. On success: `uploadProgress='done'`; call `loadDocuments()`; after 2 s set `uploadProgress=null`
6. On failure: `uploadProgress=null`, `uploadError=response.data.error || 'Upload failed'`

**Tag editing:**
1. `DocumentGrid.handleOpenTagEditor(e, doc)` → set `tagEditorVisible=true`, `tagEditorTags=[...doc.tags]`
2. User adds/removes tags in modal; each add: `handleAddTag` (max 10 tags, max 50 chars, no duplicates)
3. User clicks "Save" → `handleSaveTags`: `PUT /api/documents/{id}/tags` with `{ tags: [...] }`
4. On success: update `DocumentGrid.state.documents[i].tags` in-place; close modal
5. On failure: `tagSaving=false`; modal stays open (no error message shown to user)

**Close preview:**
1. `PreviewPanel` calls `props.onClose()`
2. `App.handleClosePreview` → `App.setState({ selectedDocument: null, showPreview: false })`
3. `PreviewPanel` unmounted

---

## State Management

### Component State Fields

| Property | Component | Type | Used In | Notes |
|---|---|---|---|---|
| `isAuthenticated` | `AuthProvider` | `boolean` | Controls login gate in `App.render` | Set `true` only by auth bypass; login always crashes |
| `user` | `AuthProvider` | `{ email, role } \| null` | Available in context but not read by any component in current code | |
| `token` | `AuthProvider` | `string \| null` | Stored in context but not attached to `axios` request headers | No `Authorization` header is sent to any API call |
| `loading` | `AuthProvider` | `boolean` | Disables Sign In button during login attempt | |
| `error` | `AuthProvider` | `string \| null` | Displayed in `LoginForm` below the button | |
| `email` / `password` | `LoginForm` | `string` | Controlled form inputs | |
| `activeSection` | `App` | `string` | Passed to `Sidebar` for highlight; no conditional rendering effect | Initial value: `'documents'` |
| `selectedDocument` | `App` | document object \| `null` | Passed to `PreviewPanel` | |
| `showPreview` | `App` | `boolean` | Conditionally renders `PreviewPanel` | |
| `query` | `SearchBar` | `string` | Controlled search input | Functional component `useState` hook |
| `documents` | `DocumentGrid` | `object[]` | Document list rendered | Replaced wholesale by both load and search |
| `loading` | `DocumentGrid` | `boolean` | Shows loading indicator, disables display | |
| `error` | `DocumentGrid` | `string \| null` | Shows error container + Retry | |
| `selectedDocument` | `DocumentGrid` | object \| `null` | Card/row highlight; separate from `App.state.selectedDocument` | Two separate selection states exist (potential sync issue) |
| `viewMode` | `DocumentGrid` | `'grid' \| 'list'` | Renders grid or list layout | |
| `sortBy` | `DocumentGrid` | `'date' \| 'name' \| 'type'` | Applied by `sortDocuments()` helper | Default: `'date'` |
| `filters.fileType` | `DocumentGrid` | `string` | Client-side type filter | |
| `filters.searchQuery` | `DocumentGrid` | `string` | Client-side name/tag text filter | |
| `tagEditorVisible` | `DocumentGrid` | `boolean` | Shows/hides tag editor modal | |
| `tagEditorDocId` | `DocumentGrid` | `string \| null` | ID of document being edited | |
| `tagEditorTags` | `DocumentGrid` | `string[]` | Working copy of tags in editor | |
| `tagEditorInput` | `DocumentGrid` | `string` | Pending tag text input | |
| `tagSaving` | `DocumentGrid` | `boolean` | Disables Save button during PUT | |
| `isDragging` | `DocumentGrid` | `boolean` | Switches drop zone to active style | |
| `uploadProgress` | `DocumentGrid` | `null \| 'uploading' \| 'done'` | Drop zone label copy | |
| `uploadError` | `DocumentGrid` | `string \| null` | Error text below drop zone | |
| `batchSelected` / `batchMode` | `DocumentGrid` | `[] / false` | **Never mutated** — abandoned feature | |
| `numPages` / `pageNumber` | `PreviewPanel` | `number \| null` / `number` | PDF page tracking | `pageNumber` is always 1 — no pagination UI exists |

### LocalStorage State

| Key | Read in | Written in | Cleared in | Purpose |
|---|---|---|---|---|
| `docvault_token` | Not read on mount (no restore logic) | `AuthProvider.login` on successful `POST /api/auth/login` | `AuthProvider.logout` | JWT — also not attached to API request headers |
| `docvault_refresh_token` | Not read on mount | `AuthProvider.login` on successful `POST /api/auth/login` | `AuthProvider.logout` | Refresh token — used only within same login transaction |

---

## Component Details

### Root Component: `AppWithAuth`

**File**: `frontend/src/App.jsx` (lines 116–126)

Stateless wrapper. Renders Redux `<Provider store={store}>` → `<AuthProvider>` → `<App>`. The Redux store is a dead dependency (see Analysis Notes).

### Page Component: `App`

**File**: `frontend/src/App.jsx` (lines 46–113)

**Static context**: `AuthContext`

**State**: `activeSection`, `selectedDocument`, `showPreview`

**Handlers**:
- `handleNavigate(section)` — updates `activeSection`
- `handleDocumentSelect(doc)` — sets `selectedDocument`, `showPreview=true`
- `handleClosePreview()` — clears `selectedDocument`, `showPreview=false`
- `handleSearch(query)` — delegates to `this.documentGridRef?.handleSearch(query)` via imperative ref

**Render**:
- If `!isAuthenticated`: returns `<LoginForm />`
- If `isAuthenticated`: returns layout with `<Header>`, `<Sidebar>`, `<SearchBar>`, `<DocumentGrid ref>`, and conditional `<PreviewPanel>`

### Auth Component: `AuthProvider`

**File**: `frontend/src/context/AuthContext.jsx`

**Manages**: `isAuthenticated`, `user`, `token`, `loading`, `error`

**Key methods**: `checkAuthBypass()` (on mount), `login(email, password)`, `logout()`

**Crash point (FR-007)**: `AuthContext.jsx:75` — `refreshResponse.data.token.split('.')`

### View Component: `DocumentGrid`

**File**: `frontend/src/components/DocumentGrid.jsx` (~1050 lines)

**Injected via props**: `onDocumentSelect` callback from `App`

**Key state groups**: documents/loading/error, view/sort/filters, tag editor, upload progress, batch (dead)

**Exported utility** (anti-pattern): `formatFileSize(bytes)` — imported by `PreviewPanel.jsx` and `DocumentCard.jsx`

**Sub-renders**: `renderUploadArea()`, `renderTagEditor()`, `renderCard(doc)`, `renderListRow(doc)`, `renderEmpty()`, `renderError()`

### View Component: `LoginForm`

**File**: `frontend/src/components/LoginForm.jsx`

**Static context**: `AuthContext` (reads `loading`, `error`; calls `login`)

**State**: `email`, `password`, `error` (local, separate from `AuthContext.error`)

### View Component: `PreviewPanel`

**File**: `frontend/src/components/PreviewPanel.jsx`

**Props**: `document` (object), `onClose` (callback)

**State**: `numPages`, `pageNumber` (always 1), `loading`, `error`

**External dependency**: `formatFileSize` imported from `DocumentGrid.jsx` (anti-pattern cross-component utility coupling)

**PDF rendering**: `react-pdf` `<Document>` + `<Page pageNumber={1} width={400}>` — no page navigation UI despite tracking `numPages`

### Sub-components (stateless presentational)

| Component | File | Props consumed | Purpose |
|---|---|---|---|
| `Header` | `components/Header.jsx` | `onNavigate` | Top nav bar with title and 3 nav links |
| `Sidebar` | `components/Sidebar.jsx` | `activeSection`, `onNavigate` | Left sidebar with 4 section items; active item highlighted |
| `SearchBar` | `components/SearchBar.jsx` | `onSearch` | Search form; trims query before calling `onSearch` |

---

## Workflows

### Workflow 1: App Mount — Auth Bypass Check

**Use case**: Every page load; determines whether to show login form or workspace.

**Entry point**: `AuthProvider.componentDidMount` → `checkAuthBypass()`

**Steps**:

1. **Issue health check**
   - `GET /api/health`
   - If `response.data.skipAuth === true`: set `isAuthenticated=true`, `user={ email: 'dev@docvault.local', role: 'admin' }` → workspace renders
   - If `skipAuth: false`, health check fails, or backend unreachable: silently ignore → `isAuthenticated` remains `false` → `LoginForm` renders

**Success outcome**: If `DEV_SKIP_AUTH=true` on backend, full workspace renders immediately without any user interaction.

**Failure outcome**: `LoginForm` renders; login is effectively impossible (FR-007).

---

### Workflow 2: Login Attempt (Always Fails — FR-007)

**Use case**: User tries to authenticate with email and password.

**Entry point**: `LoginForm.handleSubmit` → `AuthContext.login(email, password)`

**Steps**:

1. **Validate inputs** — `required` HTML attribute on both inputs; browser-native validation only.

2. **Submit credentials**
   - `AuthProvider.login` sets `loading=true`, `error=null`
   - `POST /api/auth/login` with `{ email, password }`
   - On HTTP 401: catch block sets `error='Invalid credentials'` (or backend message), `loading=false`, re-throw → `LoginForm` shows error

3. **Store initial tokens** (if HTTP 200)
   - `localStorage.setItem('docvault_token', token)`
   - `localStorage.setItem('docvault_refresh_token', refreshToken)`

4. **Attempt token refresh — CRASH**
   - `POST /api/auth/refresh` with `{ refreshToken }`
   - Backend returns `{ session: { userId, email, createdAt } }` (not `{ token, refreshToken }`)
   - `AuthContext.jsx:75`: `refreshResponse.data.token.split('.')` → `TypeError: Cannot read properties of undefined (reading 'split')`
   - Catch: `error = err.message` (`"Cannot read properties..."`) or the TypeError message, `loading=false`, `isAuthenticated=false`, re-throw

5. **Display error**
   - `LoginForm.handleSubmit` catch: `LoginForm.state.error = err.message || 'Login failed. The app has crashed — check the console.'`
   - Both `LoginForm.state.error` and `AuthContext.error` may display below the form

**Success outcome**: None. Login is always blocked by the crash. Only `DEV_SKIP_AUTH` allows access.

---

### Workflow 3: Navigation

**Use case**: User clicks a header nav link or sidebar item.

**Entry point**: `App.handleNavigate(section)`

**Steps**:

1. `App.setState({ activeSection: section })` — one of `'documents'`, `'upload'`, `'search'`, `'tags'`
2. `Sidebar` re-renders: selected item gets `navItemActiveStyle` (blue background + white text)
3. **No other effect** — `DocumentGrid` always renders; no section-conditional content exists in `App.render`

**Success outcome**: Sidebar highlight changes. URL remains `/`. Document grid is unaffected.

---

### Workflow 4: Document List Load

**Use case**: Initial workspace mount; also triggered by manual Refresh and after upload.

**Entry point**: `DocumentGrid.componentDidMount` → `loadDocuments()`

**Steps**:

1. Set `loading=true`, `error=null`
2. `GET /api/documents` → queries `documents_v2` ordered by `uploaded_at DESC`
3. **On success**: `documents = response.data.documents || []`, `loading=false`
4. **On failure**: `error = response.data.error || 'Failed to load documents'`, `loading=false`; Retry button appears

**Success outcome**: Document grid renders one card (grid mode) or row (list mode) per document.

**Failure outcome**: Error container shown with Retry button.

---

### Workflow 5: Search

**Use case**: User types a query and clicks Search.

**Entry point**: `SearchBar.handleSubmit` → `App.handleSearch` → `DocumentGrid.handleSearch`

**Steps**:

1. `SearchBar.handleSubmit` only calls `onSearch` if `query.trim()` is truthy (empty search is swallowed by `SearchBar`)
2. `App.handleSearch(query)` → `this.documentGridRef?.handleSearch(query)` — delegates via imperative `ref` (anti-pattern)
3. `DocumentGrid.handleSearch(query)`:
   - If `query.trim()` is empty: call `loadDocuments()` to restore full list
   - Otherwise: set `loading=true`; `GET /api/search?q={encodedQuery}` → queries `documents_v2` (full-text or ILIKE)
4. **On success**: `documents = response.data.results || []`, `loading=false`
5. **On failure**: `error = 'Search failed'`, `loading=false`

**Note on in-memory filters**: The "Filter..." text input and file-type dropdown in `DocumentGrid` apply client-side filtering on top of `state.documents` — they do not issue API calls. These filters operate independently of the `SearchBar` query.

**Success outcome**: Document grid replaced with search results.

---

### Workflow 6: Document Selection and Preview

**Use case**: User clicks a document card or list row to preview it.

**Entry point**: `DocumentGrid.handleDocumentClick(doc)`

**Steps**:

1. `DocumentGrid.setState({ selectedDocument: doc })` — applies highlight style to clicked card/row
2. `props.onDocumentSelect(doc)` → `App.handleDocumentSelect(doc)` → `App.setState({ selectedDocument: doc, showPreview: true })`
3. `PreviewPanel` mounts in right column
4. `PreviewPanel.render`:
   - `previewUrl = getPreviewUrl(document.id)` → `{API_BASE_URL}/documents/{id}/preview`
   - If `file_type === 'application/pdf'`: render `react-pdf <Document file={previewUrl}>` → loads PDF from URL; `onDocumentLoadSuccess` sets `numPages`; renders page 1 at width 400 px
   - If `file_type.startsWith('image/')`: render `<img src={previewUrl} alt={document.name}>`
   - Otherwise: "Preview not available for this file type."
5. File size displayed using `formatFileSize(document.file_size)` imported from `DocumentGrid.jsx`

**Success outcome**: Preview panel shows document metadata and content.

---

### Workflow 7: Close Preview

**Use case**: User closes the preview panel.

**Entry point**: `PreviewPanel` `<button onClick={onClose}>✕ Close</button>`

**Steps**:

1. `props.onClose()` → `App.handleClosePreview()`
2. `App.setState({ selectedDocument: null, showPreview: false })`
3. `PreviewPanel` unmounts

**Note**: `DocumentGrid.state.selectedDocument` is NOT cleared — the card/row remains highlighted after preview is closed.

---

### Workflow 8: File Upload

**Use case**: User drops a file onto the drop zone or uses the file picker.

**Entry point**: `DocumentGrid.handleDrop(e)` or `DocumentGrid.handleFileInputChange(e)` → `uploadFile(file)`

**Steps**:

1. Set `uploadProgress='uploading'`, `uploadError=null`
2. Build `FormData`: `formData.append('file', file)`, `formData.append('name', file.name)`
3. `POST /api/upload` with multipart form data
4. Backend accepts only `application/pdf`, `image/jpeg`, `image/png`; returns HTTP 400 for other types
5. Backend inserts row into `documents` table; trigger `trg_sync_to_v2` copies row to `documents_v2` with `tags = NULL` (FR-008 — tags are lost on insert)
6. **On success**: set `uploadProgress='done'`; call `loadDocuments()` to refresh grid; after 2 s setTimeout: `uploadProgress=null`
7. **On failure**: set `uploadProgress=null`, `uploadError=response.data.error || 'Upload failed'`; drop zone shows error text

**File picker reset**: `this.fileInputRef.current.value = ''` after upload to allow re-selection of same file.

**Success outcome**: New document appears in the grid. Tags are always `null` until explicitly added via tag editor.

---

### Workflow 9: Tag Editing

**Use case**: User edits the tags on a document.

**Entry point**: `DocumentGrid.handleOpenTagEditor(e, doc)` (click on 🏷️ button)

**Steps**:

1. `e.stopPropagation()` — prevents click from propagating to document card (avoids triggering selection)
2. Set `tagEditorVisible=true`, `tagEditorDocId=doc.id`, `tagEditorTags=[...doc.tags]`, `tagEditorInput=''`
3. Tag editor modal renders over the workspace:
   - User types in text input (max 50 chars); clicks "Add" or presses Enter → `handleAddTag` appends tag if: not empty, not duplicate, and `tagEditorTags.length < 10`
   - User clicks × on a chip → `handleRemoveTag(tag)` removes it
4. User clicks "Save" → `handleSaveTags`:
   - Set `tagSaving=true`
   - `PUT /api/documents/{id}/tags` with `{ tags: tagEditorTags }`
   - **On success**: update `state.documents[i].tags = tagEditorTags` in-place; set `tagSaving=false`, `tagEditorVisible=false`
   - **On failure**: `console.error` only; `tagSaving=false`; modal stays open — no user-visible error
5. User clicks "Cancel" or modal backdrop → `handleCloseTagEditor`: discard changes, close modal

**Success outcome**: Document card/row shows updated tag chips. Tags are written to `documents_v2.tags`.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
|---|---|---|
| Document list loading | "Loading documents..." centred text (`DocumentGrid.jsx:1016–1020`) | Shows during initial load, search, and refresh |
| Sign In button during login | Button text changes to "Signing in..." and becomes `disabled` | Driven by `AuthContext.loading` |
| Tag save in progress | "Save" button changes to "Saving..." and becomes `disabled` | Driven by `DocumentGrid.state.tagSaving` |
| Upload in progress | Drop zone label shows "Uploading..." | Driven by `uploadProgress === 'uploading'` |
| PDF loading in preview | "Loading PDF..." text above viewer | Driven by `PreviewPanel.state.loading` |

### Error States

| Error | Display | Recovery |
|---|---|---|
| Login crash (FR-007) | Error message below Sign In button (TypeError message) | None — login is structurally broken |
| Invalid credentials (HTTP 401) | "Login failed. The app has crashed — check the console." or AuthContext error text | User can retry with different credentials |
| Document load failure | Red-bordered error container + "Retry" button (`DocumentGrid.jsx:946–956`) | Click Retry → calls `loadDocuments()` |
| Search failure | Error container shown (same as load failure) | Click Retry → calls `loadDocuments()` (restores full list, not search) |
| Upload failure | Red text below drop zone (`uploadError`) | User can retry by dropping/selecting again |
| Tag save failure | Silent — `console.error` only; modal stays open | User can retry by clicking Save again |
| PDF load failure in preview | "Error: {message}" in red above viewer (`PreviewPanel.jsx:113`) | No retry; user must close and reopen |
| Unsupported file type upload | Backend returns HTTP 400; `uploadError` shown | User must select a supported file type |

### Empty States

| Context | Message | Actions available |
|---|---|---|
| No documents in vault | "📂 No documents found" + "Upload a document to get started" (`DocumentGrid.jsx:936–943`) | Upload via drop zone above |
| No documents match filters | Same empty state (client-side filter reduces to zero results) | Clear filters |
| Preview panel with no document selected | "Select a document to preview" (centred grey text, `PreviewPanel.jsx:87–90`) | Click a document card/row |
| Tag editor with no tags | Empty tag list area; "Add a tag..." placeholder in input | Add tags |

### Success States

| Action | Feedback | Next state |
|---|---|---|
| Auth bypass | Workspace renders immediately (no message) | Full workspace visible |
| Upload complete | Drop zone shows "✅ Upload complete!" for 2 s | Document grid refreshes; drop zone resets |
| Tag save | Modal closes; tag chips update in-place | Updated tags visible on card/row |
| Document selection | Card/row highlighted (blue border); preview panel opens | Preview panel visible |

---

## Use Cases

### UC-1: Access workspace without credentials

**User story**: As a developer, I want the workspace to open automatically so I can test without managing credentials.

**Workflow**: Workflow 1 (App Mount — Auth Bypass Check) with `DEV_SKIP_AUTH=true`

---

### UC-2: Attempt login with credentials (always fails)

**User story**: As a user, I want to sign in with my email and password.

**Workflow**: Workflow 2 (Login Attempt)

**Known defect**: FR-007 — login always crashes before authentication is established.

---

### UC-3: Browse all documents

**User story**: As a user, I want to see all documents in the vault so I can find what I need.

**Workflow**: Workflow 4 (Document List Load)

---

### UC-4: Search for documents by name or content

**User story**: As a user, I want to search for documents by keyword so I can find specific files.

**Workflow**: Workflow 5 (Search)

---

### UC-5: Filter and sort documents locally

**User story**: As a user, I want to narrow the displayed documents by name or file type without leaving the page.

**Workflow**: No API call — in-memory `filterDocuments()` + `sortDocuments()` applied to `DocumentGrid.state.documents`

---

### UC-6: Preview a document

**User story**: As a user, I want to see a preview of a PDF or image so I can verify its contents without downloading.

**Workflow**: Workflow 6 (Document Selection and Preview)

---

### UC-7: Upload a new document

**User story**: As a user, I want to add a document to the vault so others can find and preview it.

**Workflow**: Workflow 8 (File Upload)

**Known defect**: FR-008 — uploaded tags are silently dropped; tags must be added separately after upload.

---

### UC-8: Tag a document

**User story**: As a user, I want to add metadata tags to a document so it can be categorised and found by tag.

**Workflow**: Workflow 9 (Tag Editing)

---

### UC-9: Switch between grid and list views

**User story**: As a user, I want to switch between a card grid and a compact list so I can choose my preferred layout.

**Workflow**: `DocumentGrid.handleViewToggle` → `viewMode` toggles between `'grid'` and `'list'`

---

### UC-10: Navigate sections (cosmetic)

**User story**: As a user, I want to navigate between Documents, Upload, Search, and Tags sections.

**Workflow**: Workflow 3 (Navigation)

**Known defect**: Navigation is cosmetic only — no conditional rendering exists for sections other than sidebar highlight.

---

## Security Considerations

### Authentication

- **Required**: Yes — the app renders `LoginForm` when `isAuthenticated === false`. However, the only working authentication path is the `DEV_SKIP_AUTH` bypass.
- **Token storage**: JWTs are stored in `localStorage` (not `httpOnly` cookies), making them vulnerable to XSS. The Angular target should consider `httpOnly` cookie storage.
- **Token not sent to API**: `AuthProvider` stores the token but never attaches it to `axios` as a default `Authorization` header. All API calls (`GET /api/documents`, `POST /api/upload`, etc.) are unauthenticated at the HTTP level in the current implementation. The backend likely does not validate JWT on these routes either.
- **Logout**: `AuthContext.logout` exists but no UI button invokes it. The user cannot log out from within the application.

### Input Validation

- Login fields: HTML `required` attribute only — no email format validation beyond browser-native.
- Tag input: `maxLength={50}` on the input element; backend enforces max 10 tags.
- Upload file type: accepted MIME types enforced by the backend multer filter (`application/pdf`, `image/jpeg`, `image/png`); the `<input accept=".pdf,.jpg,.jpeg,.png">` attribute provides a client-side hint only.

### CSRF

- No CSRF protection is present. The API uses `axios` with `Content-Type: application/json` or `multipart/form-data`. The Angular target should implement CSRF tokens if the backend enforces them.

### Price/Data Integrity

- No financial data in this application; equivalent concern is tag content — tags are user-supplied free text limited to 50 characters and 10 per document.

---

## Accessibility Considerations

- No ARIA roles or labels on nav links (`<span onClick>`) — screen readers will not announce them as navigation elements. The Angular target should use `<nav>`, `<button>`, or `<a>` with `aria-label`.
- Search input has a `placeholder` but no `<label>` element — screen readers may not associate the label correctly.
- Tag chips in the editor have no ARIA roles — "Add" and "×" buttons lack descriptive labels.
- The tag editor modal has no `role="dialog"` or `aria-modal="true"` — focus is not trapped inside it.
- Document cards and list rows are `<div onClick>` rather than `<button>` or `<a>` elements — not keyboard-accessible.
- The PDF viewer (`react-pdf`) renders within a `<div>` — keyboard navigation of PDF pages is not available (no next/previous page UI).
- Upload drop zone is a `<div>` with no `role="button"` or keyboard trigger — cannot be activated by keyboard users.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
|---|---|---|
| `GET /api/health` | `{ skipAuth: boolean }` | If unreachable, auth bypass silently skipped; user sees login form (login still broken) |
| `GET /api/documents` | `{ documents: [] }` from `documents_v2` | Empty state shown; Retry button available |
| `GET /api/search?q=` | `{ results: [] }` from `documents_v2` | Error state in document grid |
| `POST /api/auth/login` | `{ token, refreshToken }` | HTTP 401 shown as error; HTTP 200 still crashes on next step |
| `POST /api/auth/refresh` | `{ session: {...} }` (bug: should be `{ token, refreshToken }`) | Always crashes (FR-007) |
| `POST /api/upload` | 200 on success / 400 on bad file type | Upload error shown in drop zone |
| `PUT /api/documents/{id}/tags` | 200 on success | Silent failure (no user message on error) |
| `GET /api/documents/{id}/preview` | Raw binary with Content-Type | PDF/image fails to render; "Error: ..." shown in preview panel |

### Downstream

| System | What this page affects | How |
|---|---|---|
| `documents` table | INSERT on upload | `POST /api/upload` |
| `documents_v2` table | INSERT (via trigger, tags=NULL); UPDATE tags | Trigger on `documents` INSERT; `PUT /api/documents/{id}/tags` |

---

## Analysis Notes

1. **FR-007 — Login always crashes**: The `POST /api/auth/refresh` step immediately follows a successful login and crashes unconditionally because the backend returns `{ session: {...} }` instead of `{ token: '...' }`. The Angular target must either: (a) fix the backend `/refresh` contract to return `{ token, refreshToken }`, or (b) remove the immediate re-refresh step from the login flow entirely. This is a **blocking defect** — the app is only usable with `DEV_SKIP_AUTH=true`.

2. **FR-008 — Upload silently drops tags**: The PostgreSQL trigger `trg_sync_to_v2` inserts a row into `documents_v2` with `tags = NULL`. Any tags passed in the upload `FormData` body are ignored at the trigger level. Tags must always be added in a separate `PUT /api/documents/{id}/tags` call after upload. The Angular upload flow must guide users to add tags post-upload, or the backend trigger must be fixed to propagate tags.

3. **Token not sent to API**: Despite storing a JWT in `localStorage`, no `axios` default header or interceptor attaches `Authorization: Bearer {token}` to API requests. All API calls are effectively unauthenticated. The Angular target should implement an `HttpInterceptor` that attaches the stored JWT.

4. **No token restoration on refresh**: `AuthProvider.componentDidMount` only calls `checkAuthBypass()` — it does not read `localStorage['docvault_token']` to restore an authenticated session. Every page load starts unauthenticated. The Angular target should implement token persistence + restoration on app init.

5. **Imperative ref anti-pattern**: `App` holds a `ref` to `DocumentGrid` and calls `this.documentGridRef?.handleSearch(query)` to trigger a search. This tightly couples parent and child. The Angular target should use a shared service or `@Input`/`@Output` event binding to communicate search queries.

6. **`formatFileSize` exported from god component**: `PreviewPanel.jsx` and `DocumentCard.jsx` import `formatFileSize` from `DocumentGrid.jsx`. This creates a compile-time dependency on the 1050-line god component for a 5-line utility. The Angular target should place this in a shared pipe or utility service.

7. **Redux store is dead weight**: The Redux `store.js` with 12 reducers and custom middleware is installed but no component dispatches any action. All state lives in React `this.state`. Do not replicate Redux in the Angular target — use Angular signals or services.

8. **`lib/` directory imports are dead**: `DocumentGrid.jsx` imports from `frontend/src/lib/` (`libFormatDate`, `humanFileSize`, `categorizeFile`, `libGetDocuments`) but uses only the `utils/` versions at runtime. These imports exist to demonstrate co-existence of duplicate utility directories and should not be replicated.

9. **Navigation is cosmetic only**: `activeSection` changes highlight the sidebar but have no effect on rendered content — `DocumentGrid` always renders. The Angular target should implement real routing with `RouterModule` and route-based component activation for `Documents`, `Upload`, `Search`, and `Tags` sections.

10. **Dual `selectedDocument` state**: `App.state.selectedDocument` and `DocumentGrid.state.selectedDocument` are set independently. When the preview panel is closed, `DocumentGrid.state.selectedDocument` is not cleared — the card remains highlighted after preview close. The Angular target should use a single source of truth for document selection.

11. **Batch selection is dead code**: `DocumentGrid.state.batchSelected` and `batchMode` exist and are initialized but never mutated. The commented-out handlers and styles confirm this was an abandoned feature. Do not replicate.

12. **`pageNumber` is always 1**: `PreviewPanel` tracks `numPages` and `pageNumber` in state but no previous/next page UI exists. The PDF viewer always renders page 1. The Angular target could implement page navigation if desired.

13. **`activeSection: 'tags'`** has no corresponding UI panel. The sidebar item navigates to a `'tags'` section that renders nothing different from the documents view.

14. **`SearchBar` swallows empty queries**: `SearchBar.handleSubmit` only calls `onSearch` if `query.trim()` is truthy. This means the user cannot clear a search by submitting an empty search bar — they must use the SearchBar's "empty query" path, which is never triggered since `handleSubmit` guards against it. However, `DocumentGrid.handleSearch` correctly handles empty string by calling `loadDocuments()` — it is just unreachable via `SearchBar`. The in-memory "Filter..." input box in `DocumentGrid` can be cleared to remove client-side filtering.
