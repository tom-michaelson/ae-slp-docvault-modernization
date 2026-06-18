# Functional spec — Search Submit Button

**Key:** `app-workspace-search-bar-submit`
**URL:** `GET /api/search?q={query}` (triggered from the workspace page)
**Legacy source:** `frontend/src/components/SearchBar.jsx` (button at line 47; handler at line 31)
**Parent feature:** `app-workspace-search-bar`

## Purpose

Submits the user's text query to the document search API and replaces the
DocumentGrid's current document list with the matching results. The button is
the primary mechanism for finding documents by name in the authenticated workspace.

## Functional behavior

### handleSubmit — form onSubmit

1. `e.preventDefault()` suppresses the default browser form submission.
2. Evaluates `query.trim()`: if blank, the function returns immediately — no API call, no visual change.
3. Calls `props.onSearch(query.trim())`, which is bound to `App.handleSearch` at the `<SearchBar>` call site (`App.jsx:94`).
4. `App.handleSearch` (App.jsx:70) immediately delegates to `this.documentGridRef?.handleSearch(query)` via an imperative React ref. If `documentGridRef` is `null`, the call is silently dropped.
5. `DocumentGrid.handleSearch` (DocumentGrid.jsx:566) sets local state `{loading: true, error: null}`.
6. Calls `searchDocuments(query)` from `utils/api.js`, which issues `GET /api/search?q={encodeURIComponent(query)}` via axios.
   - The axios request interceptor reads `localStorage.getItem('docvault_token')` and attaches it as `Authorization: Bearer {token}`.
7. On HTTP 200: DocumentGrid sets `documents` state to `response.data.results` and `loading: false`. The grid re-renders showing only matching documents.
8. On HTTP error: DocumentGrid sets `error` to `response?.data?.error ?? 'Search failed'` and `loading: false`. An error banner is shown in the grid.

### Backend: GET /api/search (routes/search.js:8)

1. Reads `req.query.q`; returns HTTP 400 `{ error: "Query parameter 'q' is required" }` if absent or blank.
2. Instantiates `SearchOrchestrator` and calls `orchestrator.search(q)`.
3. `SearchOrchestrator.normalizeQuery` trims and lowercases the query.
4. `SearchOrchestrator` delegates to `IndexManager.search`. Because `IndexManager.indexReady` is always `false`, this unconditionally calls `FallbackSearchProvider.search(normalizedQuery)`.
5. `FallbackSearchProvider` executes:
   ```sql
   SELECT * FROM documents_v2
   WHERE name ILIKE $1
   ORDER BY uploaded_at DESC
   ```
   with pattern `%{normalizedQuery}%`.
6. `SearchOrchestrator.rerank` maps each row to `{...row, score: 1.0}` (no-op ranking).
7. Route responds with `{ results: [...], query: q, total: results.length }`.

## Acceptance criteria

```gherkin
Scenario: Happy path — matching documents returned
  Given the user is authenticated (Bearer token in localStorage)
  And documents named "Budget Report" and "Annual Budget" exist in documents_v2
  When the user types "budget" in the search input and clicks "Search"
  Then GET /api/search?q=budget is issued with Authorization header
  And the DocumentGrid displays "Budget Report" and "Annual Budget"
  And the DocumentGrid does not display documents whose names do not match

Scenario: Empty query is a no-op
  Given the search input contains only whitespace
  When the user clicks "Search"
  Then no API call is made
  And the DocumentGrid is unchanged

Scenario: No results found
  Given no document in documents_v2 has a name matching "zzz_nonexistent"
  When the user searches for "zzz_nonexistent"
  Then GET /api/search?q=zzz_nonexistent returns { results: [], total: 0 }
  And the DocumentGrid renders its empty state

Scenario: Search API returns HTTP 500
  Given the database is unavailable
  When the user submits a non-empty search query
  Then the DocumentGrid shows the error banner with message "Search failed"
  And loading spinner is removed

Scenario: User presses Enter key instead of clicking "Search"
  Given the user has typed "invoice" in the search input
  When the user presses the Enter key
  Then handleSubmit fires (form onSubmit)
  And GET /api/search?q=invoice is issued identically to a button click

Scenario: Unauthenticated request (token expired)
  Given localStorage does not contain 'docvault_token'
  And the API returns HTTP 401
  Then the axios response interceptor logs "Unauthorized — token may be expired"
  And DocumentGrid shows an error banner (the 401 is re-thrown as a rejected promise)
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Search form container | `<form onSubmit={handleSubmit}>` | `SearchBar.jsx:39` |
| Query text input | `<input type="text">`, controlled via `useState('')` | `SearchBar.jsx:40–46` |
| **Search submit button** *(this feature)* | `<button type="submit">` labelled "Search" | `SearchBar.jsx:47–49` |

## Out of scope

- **Query text input live-typing** (`app-workspace-search-bar`): the `onChange` handler that updates `query` state belongs to the parent feature, not this button.
- **DocumentGrid render** — the grid re-renders on `documents` state change; that display logic belongs to `app-workspace` / `app-workspace-sidebar-documents-nav`.
- **Auth token management** — the axios interceptor reads `localStorage`; credential lifecycle is covered by `login-form-submit`.
