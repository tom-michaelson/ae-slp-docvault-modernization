# Functional spec — Application Header

**Key:** `app-workspace-header`
**URL:** persistent — rendered across all authenticated views (no dedicated route)
**Legacy source:** `frontend/src/components/Header.jsx` (lines 33–49)

---

## Purpose

The workspace header is the persistent top bar of the DocVault application. It displays the application brand mark and provides one-click navigation links to the three primary sections of the workspace (Documents, Upload, Search). It is rendered only when the user is authenticated; unauthenticated users see the `LoginForm` component in its place.

---

## Functional behavior

### Render

1. `App.render()` (App.jsx:75) checks `AuthContext.isAuthenticated`.
2. If `false`, renders `<LoginForm />` — Header is never mounted.
3. If `true`, renders `<Header onNavigate={this.handleNavigate} />` as the topmost element of the app layout.
4. Header renders a `<header>` element containing:
   - An `<h1>` displaying "📄 DocVault".
   - A `<nav>` containing three `<span>` navigation items: Documents, Upload, Search.

### onClick — Documents nav item

1. User clicks the "Documents" `<span>` (Header.jsx:37).
2. Calls `onNavigate('documents')` — guarded: no-op if prop is `undefined` or `null`.
3. `App.handleNavigate('documents')` calls `this.setState({ activeSection: 'documents' })`.
4. App re-renders; `DocumentGrid` becomes the visible content panel.

### onClick — Upload nav item

1. User clicks the "Upload" `<span>` (Header.jsx:40).
2. Calls `onNavigate('upload')`.
3. `App.handleNavigate('upload')` calls `this.setState({ activeSection: 'upload' })`.
4. App re-renders showing the upload section.

### onClick — Search nav item

1. User clicks the "Search" `<span>` (Header.jsx:43).
2. Calls `onNavigate('search')`.
3. `App.handleNavigate('search')` calls `this.setState({ activeSection: 'search' })`.
4. App re-renders showing the search section.

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user sees the header
  Given the user is authenticated (AuthContext.isAuthenticated is true)
  When the application renders
  Then the header element is visible
  And it contains the text "DocVault"
  And the nav items "Documents", "Upload", and "Search" are visible

Scenario: Unauthenticated user does not see the header
  Given the user is not authenticated (AuthContext.isAuthenticated is false)
  When the application renders
  Then the header element is NOT rendered
  And the LoginForm is rendered instead

Scenario: User clicks the Documents nav item
  Given the user is on any section of the workspace
  When the user clicks the "Documents" nav item in the header
  Then App.state.activeSection is set to "documents"
  And the DocumentGrid panel becomes visible

Scenario: User clicks the Upload nav item
  Given the user is on any section of the workspace
  When the user clicks the "Upload" nav item in the header
  Then App.state.activeSection is set to "upload"
  And the upload section becomes visible

Scenario: User clicks the Search nav item
  Given the user is on any section of the workspace
  When the user clicks the "Search" nav item in the header
  Then App.state.activeSection is set to "search"
  And the search section becomes visible

Scenario: onNavigate prop is not provided
  Given the Header is rendered without an onNavigate prop
  When the user clicks any nav item
  Then no error is thrown (guarded by onNavigate && onNavigate(...) pattern)
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| App logo / brand title "📄 DocVault" | `<h1>` text | `Header.jsx:35` |
| "Documents" nav item | `<span>` with onClick | `Header.jsx:37–39` |
| "Upload" nav item | `<span>` with onClick | `Header.jsx:40–42` |
| "Search" nav item | `<span>` with onClick | `Header.jsx:43–45` |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| Sidebar navigation (also exposes 'tags' section) | `app-workspace-sidebar` |
| Login / logout flow | `login-form`, `AuthContext` |
| Active-section highlighting (visual active state is only in Sidebar, not Header) | `app-workspace-sidebar` |
| DocumentGrid, PreviewPanel, SearchBar (rendered in body below Header) | their respective feature keys |
