# Functional spec — App Workspace Sidebar & Search Navigation

**Key:** `app-workspace-sidebar-search-nav`
**URL:** `/` (persistent layout component — rendered on every authenticated route)
**Legacy source:** `frontend/src/components/Sidebar.jsx` + `frontend/src/components/SearchBar.jsx`
**Integration host:** `frontend/src/App.jsx`

---

## Purpose

The Sidebar provides the primary workspace navigation, letting the authenticated user switch between the four top-level sections of the application (All Documents, Upload, Search, Tags). The SearchBar, rendered above the document list, allows the user to execute a server-side full-text search against the document store. Together these two components define how users orient themselves and find content within the workspace.

---

## Functional behavior

### Section navigation (Sidebar onClick)

1. The Sidebar component receives `activeSection` (string) and `onNavigate` (function) as props from `App.jsx`.
2. It renders a fixed list of four section items: `documents`, `upload`, `search`, `tags`, each with an emoji label.
3. When the user clicks a section item, the inline `onClick` handler calls `onNavigate(section.id)` — guarded by `onNavigate && onNavigate(section.id)` to avoid crashing when the prop is absent.
4. `App.handleNavigate` (App.jsx:58) receives the section ID and calls `this.setState({ activeSection: section })`.
5. The updated `activeSection` flows back down to Sidebar as a prop, applying `navItemActiveStyle` to the selected item.
6. **Note:** The current App.jsx `render()` does not gate content panel rendering on `activeSection`; `DocumentGrid` always renders regardless of which section is active. Section switching is purely cosmetic in the legacy implementation.

### Search form submission (SearchBar onSubmit)

1. The SearchBar component renders a `<form>` with a controlled text input and a "Search" submit button.
2. `SearchBar.handleSubmit` (SearchBar.jsx:31) is bound to the form's `onSubmit` event.
3. On submit, if `query.trim()` is empty the handler does nothing (no API call, no state change).
4. Otherwise it calls `onSearch(query.trim())`, which is bound to `App.handleSearch` (App.jsx:70).
5. `App.handleSearch` calls `this.documentGridRef?.handleSearch(query)` via an imperative React ref. If `documentGridRef` is null (e.g., DocumentGrid not yet mounted), the call is silently dropped.
6. `DocumentGrid.handleSearch` (DocumentGrid.jsx:566) sets its local `loading: true`, then calls `searchDocuments(query)` from `utils/api.js`.
7. `searchDocuments` issues `GET /api/search?q={encodeURIComponent(query)}` with a `Bearer` token header read from `localStorage.docvault_token`.
8. On the backend, `SearchOrchestrator.search` normalizes the query (trim + lowercase), checks `IndexManager.isIndexAvailable()` (always `false`), and delegates to `FallbackSearchProvider.search`.
9. `FallbackSearchProvider` executes `SELECT * FROM documents_v2 WHERE name ILIKE $1 ORDER BY uploaded_at DESC` with pattern `%{normalizedQuery}%`.
10. The API returns `{ results: [...], query: string, total: number }`. DocumentGrid stores the results array in local state, replacing the previously loaded documents list.
11. On error, DocumentGrid sets `error` state and displays a retry button.

### Client-side filter (DocumentGrid internal input — distinct from SearchBar)

1. DocumentGrid renders its own `<input type="text" placeholder="Filter...">` in its header controls section (DocumentGrid.jsx:979–984).
2. Typing in this input calls `DocumentGrid.handleFilterChange({ searchQuery: value })` (DocumentGrid.jsx:600).
3. The module-level `filterDocuments(docs, filters)` function (DocumentGrid.jsx:485) applies a case-insensitive `includes()` check against `document.name` and `document.tags` on the already-loaded documents list.
4. No API call is made. This filter is reset whenever `loadDocuments()` or `handleSearch()` replaces the documents list.

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user sees four navigation items, first item active by default
  Given the user is authenticated
  When the workspace loads
  Then the Sidebar renders four items: "📁 All Documents", "⬆️ Upload", "🔍 Search", "🏷️ Tags"
  And the "📁 All Documents" item is styled with the active background (#0f3460)

Scenario: User switches section — sidebar highlights new item
  Given the workspace is loaded with activeSection = "documents"
  When the user clicks "🔍 Search" in the Sidebar
  Then App.handleNavigate is called with "search"
  And activeSection becomes "search"
  And the "🔍 Search" item is styled as active
  And the "📁 All Documents" item is styled as inactive

Scenario: onNavigate prop absent — no crash
  Given Sidebar is rendered without an onNavigate prop
  When the user clicks any nav item
  Then no error is thrown (guard: onNavigate && onNavigate(section.id))

Scenario: User submits a non-empty search query
  Given the SearchBar is visible and DocumentGrid is mounted
  When the user types "invoice" and submits the form
  Then GET /api/search?q=invoice is called with Authorization: Bearer {token}
  And DocumentGrid replaces its documents list with the API response results
  And the document count subtitle reflects the number of results returned

Scenario: User submits an empty or whitespace-only search query
  Given the SearchBar is visible
  When the user submits the form with an empty input
  Then no API call is made
  And the documents list is unchanged

Scenario: Search API returns an error
  Given GET /api/search?q=invoice returns HTTP 500
  When the user submits "invoice"
  Then DocumentGrid shows an error message "Search failed"
  And a Retry button is displayed

Scenario: Search query is empty string after trim (backend guard)
  Given the backend receives GET /api/search?q=%20
  When SearchOrchestrator.normalizeQuery returns null
  Then the backend responds with HTTP 400: {"error": "Query parameter 'q' is required"}

Scenario: Client-side filter narrows visible documents without an API call
  Given DocumentGrid has loaded 10 documents
  When the user types "report" in the Filter input inside DocumentGrid
  Then only documents whose name or tags contain "report" (case-insensitive) are displayed
  And no network request is made
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Sidebar container `<aside>` | structural panel, 200px width, dark navy (#16213e) | Sidebar.jsx:42 |
| Nav list `<ul>` | loop over 4 static section items | Sidebar.jsx:43–53 |
| Nav item `<li>` — "📁 All Documents" | clickable item, calls `onNavigate('documents')` | Sidebar.jsx:44–52 |
| Nav item `<li>` — "⬆️ Upload" | clickable item, calls `onNavigate('upload')` | Sidebar.jsx:44–52 |
| Nav item `<li>` — "🔍 Search" | clickable item, calls `onNavigate('search')` | Sidebar.jsx:44–52 |
| Nav item `<li>` — "🏷️ Tags" | clickable item, calls `onNavigate('tags')` | Sidebar.jsx:44–52 |
| Active item highlight | conditional style — `navItemActiveStyle` when `activeSection === section.id` | Sidebar.jsx:47 |
| SearchBar `<form>` | form with onSubmit handler | SearchBar.jsx:39 |
| Search text input | controlled input, `value=query`, `onChange` updates local state | SearchBar.jsx:40–46 |
| Search submit button | `<button type="submit">Search</button>` | SearchBar.jsx:47–49 |
| DocumentGrid internal Filter input | controlled input inside DocumentGrid header, client-side filter only | DocumentGrid.jsx:979–984 |
| File type filter `<select>` | dropdown: All Types / PDF / JPEG / PNG | DocumentGrid.jsx:986–995 |
| View toggle button (grid/list) | toggles `viewMode` between 'grid' and 'list' | DocumentGrid.jsx:996–1002 |
| Refresh button | calls `DocumentGrid.loadDocuments()` | DocumentGrid.jsx:1003–1005 |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| Document card rendering inside DocumentGrid | `app-workspace-document-grid` |
| Preview panel (PreviewPanel.jsx) | `app-workspace-document-preview` |
| Upload button / drag-and-drop upload area inside DocumentGrid | `app-workspace-document-upload` |
| Tag editor modal inside DocumentGrid | `app-workspace-tag-editor` |
| Header bar (Header.jsx) | `app-workspace-header` |
| Authentication / LoginForm | `auth-login` |

---

## Migration notes for Angular/Spring Boot target

- **Sidebar:** Implement as an Angular `<nav>` component bound to a `RouterModule` active route. Replace `onNavigate` + lifted state with Angular Router navigation (`router.navigate(['/section'])`). Active-item styling maps to `routerLinkActive`.
- **SearchBar:** Implement as a standalone Angular `ReactiveFormsModule` form. On submit, dispatch to a `DocumentSearchService` that calls `GET /api/search?q=`. Remove the imperative-ref anti-pattern; use an Observable or NgRx action instead.
- **Client-side filter:** Move to a pipe (`FilterDocumentsPipe`) or an NgRx selector that filters `documents$` stream. Keep it decoupled from server-side search.
- **Dual search paths:** The Angular implementation should expose a single search interface; the "internal Filter" inside the grid and the external SearchBar should be unified as one query input that decides whether to call the API or filter locally based on whether the full list is already in state.
- **`documents_v2` / tags bug:** The Spring Boot search endpoint should query the canonical `documents` table (not `documents_v2`) to avoid the missing-tags defect in the legacy sync trigger.
