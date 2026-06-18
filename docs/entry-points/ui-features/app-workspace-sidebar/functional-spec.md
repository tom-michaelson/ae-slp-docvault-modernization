# Functional spec — App Workspace Sidebar

**Key:** `app-workspace-sidebar`
**URL:** N/A — rendered inside the authenticated app layout; not a routed page
**Legacy source:** `frontend/src/components/Sidebar.jsx`

---

## Purpose

Provides the primary workspace navigation rail, letting authenticated users switch between the four content sections of DocVault (All Documents, Upload, Search, Tags). It visually marks the currently active section and delegates selection back to the parent layout component. The sidebar is not a page; it is a persistent panel in the left column of `App.jsx`.

---

## Functional Behavior

### Render

1. Declares a fixed sections array: `[{ id: 'documents', label: '📁 All Documents' }, { id: 'upload', label: '⬆️ Upload' }, { id: 'search', label: '🔍 Search' }, { id: 'tags', label: '🏷️ Tags' }]`.
2. Maps each entry to a `<li>` element styled with `navItemActiveStyle` if `props.activeSection === section.id`, otherwise `navItemStyle`.
3. Each `<li>` has an `onClick` handler: calls `props.onNavigate(section.id)` when clicked, guarded by `onNavigate && onNavigate(section.id)` (safe if prop is absent).
4. The component itself holds no state; `activeSection` is owned by `App.jsx` (`this.state.activeSection`, initially `'documents'`).
5. `App.handleNavigate` updates `App` state on every call: `this.setState({ activeSection: section })`.

### Auth gating (parent-enforced)

The sidebar is never mounted when the user is unauthenticated. `App.jsx` checks `AuthContext.isAuthenticated` before rendering the main layout; if `false`, it renders `<LoginForm />` instead. The sidebar therefore assumes authenticated context is always present.

---

## Acceptance Criteria

```gherkin
Scenario: Default view shows "All Documents" section active
  Given the user has just authenticated
  When the workspace is rendered
  Then the sidebar is visible in the left column
  And the "📁 All Documents" item is highlighted (background #0f3460, color #ffffff)
  And all other items are rendered in muted color (#c0c0d0)

Scenario: Clicking a sidebar item switches the active section
  Given the workspace is visible with activeSection = "documents"
  When the user clicks "🔍 Search"
  Then onNavigate is called with "search"
  And the "🔍 Search" item becomes highlighted
  And the "📁 All Documents" item loses its highlight

Scenario: Tags section is accessible only via the sidebar
  Given the workspace is visible
  When the user inspects navigation elements
  Then the "🏷️ Tags" item is present in the sidebar
  And no equivalent "Tags" link exists in the Header navigation

Scenario: Sidebar is absent for unauthenticated users
  Given a user is not authenticated (isAuthenticated = false in AuthContext)
  When the App component renders
  Then <LoginForm /> is returned instead of the layout
  And the sidebar is not mounted

Scenario: onNavigate prop absent — sidebar renders without crashing
  Given the Sidebar component is rendered without an onNavigate prop
  When the user clicks any sidebar item
  Then no error is thrown (guard: onNavigate && onNavigate(section.id))
  And the visual state is unchanged (activeSection is not updated)
```

---

## UI Elements

| Element | Kind | Source ref |
|---|---|---|
| `<aside>` container | structural container (200 px wide, dark background `#16213e`) | `Sidebar.jsx:42` |
| `<ul>` navigation list | list container | `Sidebar.jsx:43` |
| **📁 All Documents** nav item | `<li>` click target | `Sidebar.jsx:44-52`, section id `documents` |
| **⬆️ Upload** nav item | `<li>` click target | `Sidebar.jsx:44-52`, section id `upload` |
| **🔍 Search** nav item | `<li>` click target | `Sidebar.jsx:44-52`, section id `search` |
| **🏷️ Tags** nav item | `<li>` click target | `Sidebar.jsx:44-52`, section id `tags` |
| Active-item highlight | conditional style (`navItemActiveStyle` vs `navItemStyle`) applied per item | `Sidebar.jsx:47` |

---

## Out of Scope

| Feature | Belongs to |
|---|---|
| Header navigation links (Documents / Upload / Search) | `app-header` — `Header.jsx` duplicates 3 of the 4 sidebar sections but is a separate component |
| Content rendered when each section is active (document grid, upload form, search results, tag list) | `app-documents-grid`, `app-upload-panel`, `app-search-panel`, `app-tags-panel` — all rendered by `App.jsx` based on `activeSection` |
| Sidebar collapse/expand (`TOGGLE_SIDEBAR` Redux action) | Defined in `uiReducer.js` but **not wired** to this component — not implemented in legacy |
