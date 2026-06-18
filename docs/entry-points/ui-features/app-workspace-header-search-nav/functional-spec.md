# Functional spec — App workspace header search navigation

**Key:** `app-workspace-header-search-nav`
**URL:** `/` (SPA — authenticated workspace; no discrete route for this feature)
**Legacy source:** `frontend/src/components/Header.jsx` · `frontend/src/components/SearchBar.jsx` · `frontend/src/App.jsx`

---

## Purpose

The Header component renders the application title and three navigation links (Documents, Upload, Search) at the top of the authenticated workspace. Clicking **Search** updates the active section in the Sidebar. A separate always-visible SearchBar accepts a text query and calls the backend search API, replacing the DocumentGrid contents with matching results.

---

## Functional behavior

### onClick — Header 'Search' link

1. User clicks the `<span>` at `Header.jsx:43`.
2. `onNavigate('search')` is called on the Header prop.
3. `App.handleNavigate('search')` sets `this.state.activeSection = 'search'`.
4. The Sidebar re-renders, highlighting the **🔍 Search** item.
5. **No other change occurs** — the SearchBar is always mounted and visible.

### onSubmit — SearchBar form

1. User types a query into the `<input>` (SearchBar.jsx) and presses Enter or clicks **Search**.
2. `SearchBar.handleSubmit` is called; if `query.trim()` is empty, submission is suppressed.
3. `onSearch(query.trim())` invokes `App.handleSearch(query)`.
4. `App.handleSearch` calls `this.documentGridRef.handleSearch(query)` via an imperative ref; if the ref is null, the call silently no-ops.
5. `DocumentGrid.handleSearch(query)`:
   - If `query` is empty/whitespace → calls `loadDocuments()` (resets to full list).
   - Otherwise → calls `searchDocuments(query)` (`GET /api/search?q={encodedQuery}`).
6. The axios request interceptor attaches `Authorization: Bearer {token}` from `localStorage.docvault_token`.
7. Backend route `GET /api/search` validates `q` is non-empty, then calls `SearchOrchestrator.search`.
8. `SearchOrchestrator` normalizes the query to lowercase, passes it to `IndexManager.search`.
9. `IndexManager.isIndexAvailable()` always returns `false` → delegates to `FallbackSearchProvider.search`.
10. `FallbackSearchProvider` executes `SELECT * FROM documents_v2 WHERE name ILIKE $1 ORDER BY uploaded_at DESC` with pattern `%{query}%`.
11. Each row is returned with `score: 1.0` added.
12. Backend responds `{ results: [...], query: string, total: number }`.
13. `DocumentGrid` sets `this.state.documents = response.data.results` and `loading: false`.
14. DocumentGrid re-renders showing only matching documents (or empty state if `results` is `[]`).

### On error (search API failure)

1. If the API call throws, `DocumentGrid.handleSearch` catches the error.
2. Sets `this.state.error = err.response?.data?.error || 'Search failed'`.
3. DocumentGrid renders an error banner with a Retry button that calls `handleRefresh()`.

---

## Acceptance criteria

```gherkin
Scenario: Clicking 'Search' nav highlights search section in sidebar
  Given the user is authenticated and the workspace is shown
  When they click the "Search" link in the header
  Then App.state.activeSection is set to "search"
  And the Sidebar item "🔍 Search" is styled with the active (highlighted) style

Scenario: Submitting a query returns matching documents
  Given the user is authenticated
  And there is at least one document named "invoice-2024.pdf" in documents_v2
  When the user types "invoice" in the SearchBar and submits
  Then GET /api/search?q=invoice is called with a Bearer token header
  And the DocumentGrid displays only documents whose name contains "invoice" (case-insensitive)

Scenario: Empty query submission is suppressed
  Given the user is authenticated
  When the user submits the SearchBar with an empty or whitespace-only query
  Then no API call is made
  And the DocumentGrid contents are unchanged

Scenario: Query with no matching documents shows empty state
  Given no documents in documents_v2 have a name matching "xyzzy"
  When the user searches for "xyzzy"
  Then GET /api/search?q=xyzzy returns { results: [], total: 0 }
  And the DocumentGrid renders the empty-state message

Scenario: Unauthenticated access is blocked at the app level
  Given the user is not authenticated (AuthContext.isAuthenticated = false)
  Then App.render() returns <LoginForm /> and the Header is not mounted
  And the SearchBar is not mounted
  And no search request can be initiated

Scenario: API error during search shows error banner
  Given the search API responds with HTTP 500
  When the user submits a query
  Then DocumentGrid.state.error is set to "Search failed"
  And an error banner is rendered with a Retry button
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| App title "📄 DocVault" | text (h1) | Header.jsx:35 |
| "Documents" nav link | `<span>` onClick → onNavigate('documents') | Header.jsx:37–39 |
| "Upload" nav link | `<span>` onClick → onNavigate('upload') | Header.jsx:40–42 |
| "Search" nav link | `<span>` onClick → onNavigate('search') | Header.jsx:43–45 |
| SearchBar container | `<form>` onSubmit → handleSubmit | SearchBar.jsx:39 |
| Search text input | `<input type="text">` controlled, placeholder "Search documents..." | SearchBar.jsx:40–45 |
| Search submit button | `<button type="submit">` label "Search" | SearchBar.jsx:47–49 |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| Sidebar navigation (mirrors Header links, adds Tags) | Sidebar component (separate feature) |
| DocumentGrid document listing and card rendering | `app-workspace-document-grid` |
| PreviewPanel (slide-in panel on document select) | `app-workspace-preview-panel` |
| LoginForm (shown when not authenticated) | `app-auth-login-form` |
| Tag editor modal inside DocumentGrid | `app-workspace-tag-editor` |
