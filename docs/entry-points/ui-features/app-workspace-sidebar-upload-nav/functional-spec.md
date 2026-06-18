# Functional spec — Upload Sidebar Link

**Key:** `app-workspace-sidebar-upload-nav`
**URL:** N/A — in-page state change only (no URL route)
**Legacy source:** `frontend/src/components/Sidebar.jsx` (lines 36–38, 44–52)

---

## Purpose

The Upload Sidebar Link is the "⬆️ Upload" navigation entry in the application's left sidebar. Clicking it signals the user's intent to enter upload mode by setting `activeSection = 'upload'` in the root `App` component, which visually highlights the item. In the legacy app this is a visual-only affordance: the main content area does not switch to an upload panel — actual file upload is accessed via the drag-and-drop zone embedded in `DocumentGrid`. The Angular target must implement this as a proper route (`/upload`) that renders a dedicated upload view.

---

## Functional behavior

### onClick — navigate to upload section

1. User clicks the `<li>` element whose `section.id === 'upload'` and `section.label === '⬆️ Upload'`.
2. The `onClick` handler calls `onNavigate && onNavigate('upload')` (guard prevents crash when prop is omitted).
3. `onNavigate` resolves to `App.handleNavigate`, which calls `this.setState({ activeSection: 'upload' })`.
4. React re-renders `App`; the updated `activeSection` prop is passed to `Sidebar`, causing the Upload `<li>` to render with `navItemActiveStyle` (background `#0f3460`, text `#ffffff`) instead of the default `navItemStyle`.
5. No route change, no URL update, no HTTP request, and no change to the main content area occurs in the legacy implementation — `DocumentGrid` is always rendered regardless of `activeSection`.

### Passive render — active state display

1. On every render, Sidebar evaluates `activeSection === section.id` for each item.
2. When `activeSection === 'upload'`, the Upload `<li>` receives `navItemActiveStyle`; all other items receive `navItemStyle`.
3. The component is stateless: it owns no local state and relies entirely on the `activeSection` prop.

---

## Acceptance criteria

```gherkin
Scenario: Clicking Upload link highlights it in the sidebar
  Given the app is authenticated and rendered
  And activeSection is not 'upload'
  When the user clicks "⬆️ Upload" in the sidebar
  Then App.state.activeSection becomes 'upload'
  And the Upload <li> renders with background-color '#0f3460'
  And all other sidebar items render with the default background

Scenario: Upload link is already active — re-click is idempotent
  Given activeSection is already 'upload'
  When the user clicks "⬆️ Upload" again
  Then App.state.activeSection remains 'upload'
  And no visible change occurs

Scenario: Sidebar renders without onNavigate prop — no crash
  Given Sidebar is rendered without an onNavigate prop
  When the user clicks "⬆️ Upload"
  Then no JavaScript error is thrown
  And the click is silently ignored (guard: onNavigate && onNavigate(section.id))

Scenario: Main content area does not change on Upload nav click
  Given the main content area shows DocumentGrid
  When the user clicks "⬆️ Upload" in the sidebar
  Then DocumentGrid is still rendered (not replaced by an upload panel)
  And no HTTP request is made
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Upload nav `<li>` | Clickable list item (active/inactive conditional style) | `Sidebar.jsx:44–52` |
| Upload icon + label text `⬆️ Upload` | Text inside `<li>` | `Sidebar.jsx:49` |
| Active highlight style | Conditional inline style (`navItemActiveStyle` when `activeSection === 'upload'`) | `Sidebar.jsx:47` |
| `onNavigate` prop call | Event handler invoking parent callback | `Sidebar.jsx:48` |

---

## Out of scope

| Feature | Key | Notes |
|---|---|---|
| Full Sidebar component (all nav items) | `app-workspace-sidebar` | This spec covers only the Upload `<li>`; the Documents, Search, and Tags links are separate features. |
| Actual file upload functionality | N/A (DocumentGrid internal) | Drag-and-drop upload area and `UploadButton` live inside `DocumentGrid.jsx` and are not driven by this nav link. |
| Header Upload nav link | `app-workspace-header-upload-nav` | A separate Upload link exists in the header; it shares the same `handleNavigate` mechanism but is a distinct element. |
