# Functional spec — Workspace Search Bar

**Key:** `app-workspace-search-bar`
**URL:** `/app` (authenticated workspace — rendered inside `App.jsx`; no dedicated route)
**Legacy source:** `frontend/src/components/SearchBar.jsx`

---

## Purpose

The search bar allows authenticated users to filter the document grid by typing a name query and submitting it. It is always visible at the top of the main content column when the user is logged in, providing immediate access to document retrieval across the workspace.

---

## Functional behavior

### handleSubmit — user submits a search query

1. User types into the text input; `query` state is updated on every keystroke via `setQuery`.
2. User presses Enter or clicks the **Search** button, triggering `handleSubmit`.
3. `handleSubmit` calls `e.preventDefault()` to suppress native form navigation.
4. If `query.trim()` is empty or whitespace-only, the handler returns early — no callback is fired, no visual feedback is shown.
5. Otherwise, `props.onSearch(query.trim())` is called with the trimmed string.
6. `App.handleSearch` receives the query and imperatively calls `this.documentGridRef.handleSearch(query)`.
7. `DocumentGrid.handleSearch` sets `loading: true` and calls `searchDocuments(query)` (`GET /api/search?q={encodedQuery}`).
8. On success, `DocumentGrid` replaces its `documents` state with `response.data.results` and clears `loading`.
9. On failure, `DocumentGrid` stores the error message and clears `loading`.

### handleSubmit — user submits an empty query (reset path)

1. If `DocumentGrid.handleSearch` receives an empty/whitespace string, it calls `this.loadDocuments()` instead of `searchDocuments`.
2. `loadDocuments` issues `GET /api/documents` and repopulates the full document list.
3. This path is **not reachable through SearchBar** because SearchBar guards with `query.trim()` before calling `onSearch`; however, `DocumentGrid.handleSearch` is also callable via the imperative ref from other entry points.

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user searches by document name — results returned
  Given the user is logged in and the workspace is visible
  When they type "budget" into the search input and click Search
  Then GET /api/search?q=budget is called
  And the document grid renders only documents whose name contains "budget" (case-insensitive)
  And loading state is shown while the request is in flight

Scenario: Authenticated user searches by document name — no results
  Given the user is logged in
  When they type "zzznomatch" into the search input and submit
  Then GET /api/search?q=zzznomatch is called
  And the document grid renders an empty state (zero documents)

Scenario: User submits an empty or whitespace-only query
  Given the user is logged in
  When they submit the search form with an empty input
  Then no API call is made
  And the document grid is unchanged

Scenario: User clears the search input and resubmits
  Given the user has previously searched and the grid shows filtered results
  When they clear the input and submit (empty string)
  Then SearchBar does not call onSearch (empty guard fires)
  And the document grid remains in its current state
  Note: the full-document reload path in DocumentGrid is unreachable from SearchBar alone

Scenario: Search API returns an error
  Given the server returns HTTP 500 for GET /api/search
  When the user submits a valid query
  Then DocumentGrid sets error state to "Search failed"
  And the document grid displays the error message
  And loading is cleared

Scenario: Unauthenticated access
  Given the user is not logged in
  When the app renders
  Then App.jsx renders <LoginForm /> instead of the workspace
  And SearchBar is never mounted
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Search form container | `<form onSubmit>` | `SearchBar.jsx:39` |
| Query text input | `<input type="text">` controlled by `useState('')` | `SearchBar.jsx:40-46` |
| Submit button | `<button type="submit">` labelled "Search" | `SearchBar.jsx:47-49` |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| Document grid results rendering (grid/list view, sorting, file-type filter) | `app-document-grid` |
| Client-side `filterDocuments()` filter (fileType + searchQuery in DocumentGrid local state) | `app-document-grid` |
| Redux `searchReducer` / `filtersReducer` state (populated by DocumentGrid's internal filter controls, not by this SearchBar) | `app-document-grid` |
| Preview panel opened on document click | `app-document-preview-panel` |
| Header navigation and sidebar | `app-header`, `app-sidebar` |
