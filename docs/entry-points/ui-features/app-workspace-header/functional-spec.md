# Functional spec — Application Header

**Key:** `app-workspace-header`
**URL:** `/` (SPA — authenticated workspace; no discrete route for this component)
**Legacy source:** `frontend/src/components/Header.jsx` (lines 33–49) · `frontend/src/App.jsx`

---

## Purpose

The workspace header is the persistent top bar of the DocVault application. It displays the application brand mark ("📄 DocVault") and provides one-click navigation links to the three primary sections (Documents, Upload, Search). It is rendered only when the user is authenticated; the parent `App` component gates it behind an `AuthContext.isAuthenticated` check and returns `<LoginForm />` instead when the user is not logged in.

---

## Functional behavior

### Render — initial mount

1. `App.render()` (App.jsx:75) reads `AuthContext.isAuthenticated`.
2. If `false`, renders `<LoginForm />` — Header is not mounted.
3. If `true`, renders `<Header onNavigate={this.handleNavigate} />` as the topmost element of the app layout.
4. Header renders a `<header>` element containing:
   - An `<h1>` with the literal text "📄 DocVault".
   - A `<nav>` with three `<span>` elements: "Documents", "Upload", "Search".
5. Header is stateless and consumes no Redux store; it is a pure presentation component.

### onClick — Documents nav item

1. User clicks the "Documents" `<span>` (Header.jsx:37).
2. `onNavigate && onNavigate('documents')` calls `App.handleNavigate('documents')`.
3. `App.handleNavigate` calls `this.setState({ activeSection: 'documents' })`.
4. React re-renders `App`; updated `activeSection` prop is passed to `Sidebar`, which highlights "📁 All Documents".
5. **No content-area change in legacy app** — `DocumentGrid` is always rendered regardless of `activeSection`.
6. No HTTP request is made.

### onClick — Upload nav item

1. User clicks the "Upload" `<span>` (Header.jsx:40).
2. `onNavigate && onNavigate('upload')` calls `App.handleNavigate('upload')`.
3. `App.handleNavigate` calls `this.setState({ activeSection: 'upload' })`.
4. Sidebar highlights "⬆️ Upload".
5. **Legacy limitation — visual only:** No upload panel is mounted. `DocumentGrid` continues to render. The drag-and-drop upload widget is embedded inside `DocumentGrid`, not in a separate panel gated by `activeSection`.
6. No HTTP request is made.

### onClick — Search nav item

1. User clicks the "Search" `<span>` (Header.jsx:43).
2. `onNavigate && onNavigate('search')` calls `App.handleNavigate('search')`.
3. `App.handleNavigate` calls `this.setState({ activeSection: 'search' })`.
4. Sidebar highlights "🔍 Search".
5. **No content-area change** — `SearchBar` is always mounted in the `searchContainerStyle` div (App.jsx:93–95) regardless of `activeSection`.
6. No HTTP request is made.

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user sees the header
  Given AuthContext.isAuthenticated is true
  When the application renders
  Then the header <header> element is visible
  And it displays the text "DocVault"
  And the nav items "Documents", "Upload", and "Search" are all present

Scenario: Unauthenticated user does not see the header
  Given AuthContext.isAuthenticated is false
  When the application renders
  Then the <header> element is NOT rendered
  And <LoginForm /> is rendered instead

Scenario: Clicking Documents nav sets activeSection
  Given the user is authenticated and any activeSection is current
  When the user clicks "Documents" in the header
  Then App.state.activeSection becomes 'documents'
  And Sidebar highlights "📁 All Documents"
  And DocumentGrid remains visible (no panel switch occurs)
  And no HTTP request is made

Scenario: Clicking Upload nav is visual-only in legacy
  Given the user is authenticated
  When the user clicks "Upload" in the header
  Then App.state.activeSection becomes 'upload'
  And Sidebar highlights "⬆️ Upload"
  And DocumentGrid is still rendered (no dedicated upload panel appears)
  And no HTTP request is made

Scenario: Clicking Search nav sets activeSection
  Given the user is authenticated
  When the user clicks "Search" in the header
  Then App.state.activeSection becomes 'search'
  And Sidebar highlights "🔍 Search"
  And SearchBar remains mounted (it is always visible regardless of activeSection)
  And no HTTP request is made

Scenario: onNavigate prop is absent — no crash
  Given Header is rendered without an onNavigate prop
  When the user clicks any nav item
  Then no JavaScript error is thrown
  And the click is silently ignored (guarded by onNavigate && onNavigate(...))
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| App brand title "📄 DocVault" | `<h1>` static text | `Header.jsx:35` |
| `<nav>` container | `<nav>` flex row (3 children) | `Header.jsx:36–46` |
| "Documents" nav link | `<span>` onClick → onNavigate('documents') | `Header.jsx:37–39` |
| "Upload" nav link | `<span>` onClick → onNavigate('upload') | `Header.jsx:40–42` |
| "Search" nav link | `<span>` onClick → onNavigate('search') | `Header.jsx:43–45` |

---

## Out of scope

| Feature | Belongs to |
|---|---|
| SearchBar (always-visible search form below header) | `app-workspace-header-search-nav` |
| Search API call flow triggered by SearchBar submission | `app-workspace-header-search-nav` |
| Sidebar navigation (mirrors header links; adds Tags) | separate sidebar feature |
| Auth guard / LoginForm rendering | `login-form-submit` |
| DocumentGrid document listing | `document-grid-controls` |
| Active-state visual highlighting (Sidebar only, not Header) | sidebar feature |
