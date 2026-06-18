# Functional spec — App workspace header — Documents nav link

**Key:** `app-workspace-header-documents-nav`
**URL:** Client-side navigation only — no route or URL change
**Legacy source:** `frontend/src/components/Header.jsx` (lines 37–39)
**Parent component:** `frontend/src/App.jsx`

---

## Purpose

The "Documents" link in the top navigation bar switches the workspace's active section to the document list view. It is the primary affordance for returning to the `DocumentGrid` after the user has navigated to Upload or Search. Because the app uses component-level state rather than a URL router, clicking this link does not change the browser address bar.

---

## Functional behavior

### onClick — Documents span

1. User clicks the `<span>Documents</span>` at `Header.jsx:37`.
2. The inline handler evaluates `onNavigate && onNavigate('documents')`.
3. `onNavigate` resolves to `App.handleNavigate` (bound at `App.jsx:86`).
4. `App.handleNavigate('documents')` calls `this.setState({ activeSection: 'documents' })` (`App.jsx:59`).
5. App re-renders. `DocumentGrid` is always present in the JSX tree; its visibility does not depend on `activeSection`. The `Sidebar` reads `activeSection` and applies `navItemActiveStyle` to the `documents` list item.
6. No API call is made; no Redux dispatch is triggered.

**Auth pre-condition:** The `<Header>` component is only mounted when `AuthContext.isAuthenticated` is `true`. If `isAuthenticated` is `false`, the entire app body is replaced by `<LoginForm>` and `Header` is never rendered (see `App.jsx:80–82`).

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user clicks Documents nav link
  Given the user is authenticated (AuthContext.isAuthenticated = true)
  And activeSection is currently 'upload' or 'search'
  When the user clicks the "Documents" span in the header nav
  Then App.state.activeSection is set to 'documents'
  And the Sidebar highlights the "All Documents" item
  And DocumentGrid remains visible in the workspace

Scenario: Prop guard prevents crash when onNavigate is not supplied
  Given Header is rendered without an onNavigate prop
  When the user clicks the "Documents" span
  Then no error is thrown
  And the application remains functional
  (the inline guard `onNavigate && onNavigate(...)` prevents the TypeError)

Scenario: Unauthenticated user cannot reach the Documents link
  Given the user is not authenticated (AuthContext.isAuthenticated = false)
  When the user loads the application
  Then LoginForm is rendered instead of the full app shell
  And Header (and the Documents nav link) is not present in the DOM

Scenario: Documents link is already active
  Given activeSection is already 'documents'
  When the user clicks the "Documents" span
  Then App.setState is called with { activeSection: 'documents' } (no-op in practice)
  And no visible change occurs
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Header container `<header>` | structural wrapper with dark background (`#1a1a2e`) | `Header.jsx:34` |
| App title `📄 DocVault` | `<h1>` text — not interactive | `Header.jsx:35` |
| `<nav>` link group | flex container holding all three nav spans | `Header.jsx:36–46` |
| **Documents** nav link | `<span>` with `onClick → onNavigate('documents')` | `Header.jsx:37–39` |
| Upload nav link | `<span>` with `onClick → onNavigate('upload')` | `Header.jsx:40–42` |
| Search nav link | `<span>` with `onClick → onNavigate('search')` | `Header.jsx:43–45` |

---

## Out of scope

- **Sidebar navigation** (`frontend/src/components/Sidebar.jsx`): the Sidebar renders an equivalent "All Documents" link and also calls `onNavigate('documents')`. That surface is a separate feature. Both converge on `App.handleNavigate` but are analysed independently.
- **Upload nav link** and **Search nav link** in the same `<nav>`: they share the same component and prop pattern but are distinct workspace sections with their own feature keys.
- **Auth guard / LoginForm** (`frontend/src/components/LoginForm.jsx`): authentication flow is out of scope for this nav feature.
- **DocumentGrid content** (`frontend/src/components/DocumentGrid.jsx`): what renders after `activeSection = 'documents'` is set belongs to the document list feature, not this nav link.
