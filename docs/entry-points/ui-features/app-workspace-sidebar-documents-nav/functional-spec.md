# Functional spec — All Documents Sidebar Link

**Key:** `app-workspace-sidebar-documents-nav`
**URL:** Client-side navigation only — no route or URL change
**Legacy source:** `frontend/src/components/Sidebar.jsx` (lines 44–52)
**Parent component:** `frontend/src/App.jsx`

---

## Purpose

The "📁 All Documents" item in the left-hand sidebar switches the workspace's active section to the document list view. It is the primary sidebar affordance for returning to the `DocumentGrid` after navigating to Upload, Search, or Tags. Because the app uses `App` class component state (`activeSection`) rather than a URL router, clicking this item does not change the browser address bar.

---

## Functional behavior

### onClick — All Documents `<li>`

1. User clicks the `<li>` rendered for the `{ id: 'documents', label: '📁 All Documents' }` section entry at `Sidebar.jsx:45`.
2. The inline handler evaluates `onNavigate && onNavigate(section.id)` where `section.id === 'documents'` (`Sidebar.jsx:48`).
3. `onNavigate` resolves to `App.handleNavigate` (bound at `App.jsx:88–91`).
4. `App.handleNavigate('documents')` calls `this.setState({ activeSection: 'documents' })` (`App.jsx:59`).
5. `App` re-renders; `Sidebar` receives the updated `activeSection='documents'` prop.
6. Inside `Sidebar`, the ternary at `Sidebar.jsx:47` evaluates `activeSection === section.id` for each item — the `documents` item now receives `navItemActiveStyle` (background `#0f3460`, white text) while all other items receive `navItemStyle`.
7. `DocumentGrid` is always mounted in the JSX tree (`App.jsx:97–100`); its display does not change as a direct result of this action.
8. No API call is made; no Redux action is dispatched.

**Auth pre-condition:** The `<Sidebar>` component is only mounted when `AuthContext.isAuthenticated` is `true`. If `isAuthenticated` is `false`, the entire app body is replaced by `<LoginForm>` and `Sidebar` is never rendered (`App.jsx:80–82`).

---

## Acceptance criteria

```gherkin
Scenario: Authenticated user clicks "All Documents" in the sidebar
  Given the user is authenticated (AuthContext.isAuthenticated = true)
  And activeSection is currently 'upload', 'search', or 'tags'
  When the user clicks the "📁 All Documents" sidebar item
  Then App.state.activeSection is set to 'documents'
  And the "📁 All Documents" <li> is styled with navItemActiveStyle (background #0f3460)
  And all other sidebar items are styled with navItemStyle
  And DocumentGrid remains visible in the workspace

Scenario: Documents link is already the active section
  Given activeSection is already 'documents'
  When the user clicks the "📁 All Documents" sidebar item
  Then App.setState is called with { activeSection: 'documents' } (no visible change)
  And the sidebar highlight remains on the "All Documents" item

Scenario: Prop guard prevents crash when onNavigate is not supplied
  Given Sidebar is rendered without an onNavigate prop
  When the user clicks the "📁 All Documents" item
  Then no error is thrown
  (the inline guard `onNavigate && onNavigate(section.id)` prevents the TypeError)

Scenario: Unauthenticated user cannot reach the sidebar
  Given the user is not authenticated (AuthContext.isAuthenticated = false)
  When the user loads the application
  Then LoginForm is rendered instead of the full app shell
  And the Sidebar (and its "All Documents" link) is not present in the DOM
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| `<aside>` sidebar container | structural wrapper, fixed 200 px width, dark background (`#16213e`) | `Sidebar.jsx:42` |
| `<ul>` nav list | list container, no bullet styling | `Sidebar.jsx:43` |
| **"📁 All Documents"** nav item | `<li>` with `onClick → onNavigate('documents')`; active state via inline style ternary | `Sidebar.jsx:45–51` |
| "⬆️ Upload" nav item | `<li>` with `onClick → onNavigate('upload')` | `Sidebar.jsx:45–51` |
| "🔍 Search" nav item | `<li>` with `onClick → onNavigate('search')` | `Sidebar.jsx:45–51` |
| "🏷️ Tags" nav item | `<li>` with `onClick → onNavigate('tags')` | `Sidebar.jsx:45–51` |

---

## Out of scope

- **Header navigation** (`frontend/src/components/Header.jsx`): the Header renders an equivalent "Documents" nav link that calls the same `onNavigate('documents')` prop. That surface is a separate feature (`app-workspace-header-documents-nav`). Both converge on `App.handleNavigate` but are analysed independently.
- **Upload, Search, and Tags sidebar links**: they share the same `<li>` render pattern and prop mechanism but target different workspace sections; each has its own feature key (`app-workspace-sidebar-upload-nav`, `app-workspace-sidebar-search-nav`, `app-workspace-sidebar-tags-nav`).
- **DocumentGrid content** (`frontend/src/components/DocumentGrid.jsx`): what renders in the workspace after `activeSection = 'documents'` is the document list feature, not this nav action.
- **Auth guard / LoginForm** (`frontend/src/components/LoginForm.jsx`): authentication flow is out of scope for this nav feature.
- **Redux `TOGGLE_SIDEBAR` action** (`uiReducer.js:24`): this action controls sidebar open/close state in the Redux store, but the Sidebar component itself does not read from Redux — it is purely prop-driven. `TOGGLE_SIDEBAR` is not wired to any component in the current codebase.
