# Functional spec — Upload Header Link

**Key:** `app-workspace-header-upload-nav`
**URL:** Client-side navigation only — no route or URL change
**Legacy source:** `frontend/src/components/Header.jsx` (lines 40–42)
**Parent component:** `frontend/src/App.jsx`

---

## Purpose

The "Upload" link in the top navigation bar switches the workspace's active section to `'upload'`, which highlights the corresponding Sidebar item and signals user intent to upload documents. Because the legacy app uses component-level state rather than a URL router, clicking this link does not change the browser address bar. The embedded upload area inside `DocumentGrid` is always visible regardless of `activeSection`, so this link primarily serves as a wayfinding signal rather than a view-gate.

---

## Functional behavior

### onClick — Upload span

1. User clicks the `<span>Upload</span>` at `Header.jsx:40`.
2. The inline handler evaluates `onNavigate && onNavigate('upload')`.
3. `onNavigate` resolves to `App.handleNavigate` (bound at `App.jsx:86`).
4. `App.handleNavigate('upload')` calls `this.setState({ activeSection: 'upload' })` (`App.jsx:59`).
5. App re-renders. `DocumentGrid` is always present in the JSX tree; its visibility and upload area do not depend on `activeSection`. The `Sidebar` reads `activeSection` and applies `navItemActiveStyle` to the `upload` list item (`Sidebar.jsx:46–48`).
6. No API call is made; no Redux dispatch is triggered.

**Auth pre-condition:** The `<Header>` component is only mounted when `AuthContext.isAuthenticated` is `true`. If `isAuthenticated` is `false`, the entire app body is replaced by `<LoginForm>` and `Header` is never rendered (see `App.jsx:80–82`).

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user clicks Upload nav link
  Given the user is authenticated (AuthContext.isAuthenticated = true)
  And activeSection is currently 'documents' or 'search'
  When the user clicks the "Upload" span in the header nav
  Then App.state.activeSection is set to 'upload'
  And the Sidebar highlights the "⬆️ Upload" item
  And DocumentGrid (including its upload area) remains visible in the workspace

Scenario: Upload link is already active
  Given activeSection is already 'upload'
  When the user clicks the "Upload" span
  Then App.setState is called with { activeSection: 'upload' } (no-op in practice)
  And no visible change occurs

Scenario: Prop guard prevents crash when onNavigate is not supplied
  Given Header is rendered without an onNavigate prop
  When the user clicks the "Upload" span
  Then no error is thrown
  And the application remains functional
  (the inline guard `onNavigate && onNavigate(...)` prevents the TypeError)

Scenario: Unauthenticated user cannot reach the Upload link
  Given the user is not authenticated (AuthContext.isAuthenticated = false)
  When the user loads the application
  Then LoginForm is rendered instead of the full app shell
  And Header (and the Upload nav link) is not present in the DOM
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Header container `<header>` | structural wrapper with dark background (`#1a1a2e`) | `Header.jsx:34` |
| App title `📄 DocVault` | `<h1>` text — not interactive | `Header.jsx:35` |
| `<nav>` link group | flex container holding all three nav spans | `Header.jsx:36–46` |
| Documents nav link | `<span>` with `onClick → onNavigate('documents')` | `Header.jsx:37–39` |
| **Upload** nav link | `<span>` with `onClick → onNavigate('upload')` | `Header.jsx:40–42` |
| Search nav link | `<span>` with `onClick → onNavigate('search')` | `Header.jsx:43–45` |

---

## Out of scope

- **Sidebar upload navigation** (`frontend/src/components/Sidebar.jsx`): the Sidebar renders an equivalent "⬆️ Upload" list item that also calls `onNavigate('upload')`. That surface is a separate feature key (`app-workspace-sidebar-upload-nav`).
- **DocumentGrid upload area** (`frontend/src/components/DocumentGrid.jsx`): the drag-and-drop and click-to-upload controls inside `DocumentGrid` are always rendered and are distinct features (`document-grid-upload-area`, `document-grid-upload-drop`, `document-grid-upload-click`). This nav link merely highlights the sidebar; it does not gate the upload UI.
- **UploadButton component** (`frontend/src/components/UploadButton.jsx`): a standalone upload component that is not mounted in `App.jsx` and is unrelated to this nav link.
- **Auth guard / LoginForm** (`frontend/src/components/LoginForm.jsx`): authentication flow is out of scope for this nav feature.
- **Documents nav link** and **Search nav link** in the same `<nav>`: share the same component and prop pattern but are distinct features with their own feature keys.
