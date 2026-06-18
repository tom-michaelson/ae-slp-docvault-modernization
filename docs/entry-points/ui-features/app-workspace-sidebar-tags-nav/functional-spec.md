# Functional spec — Workspace sidebar – Tags navigation

**Key:** `app-workspace-sidebar-tags-nav`
**URL:** Client-side only — no route change; sets `App.state.activeSection = 'tags'`
**Legacy source:** `frontend/src/components/Sidebar.jsx` (lines 33–58)

---

## Purpose

The sidebar's Tags item lets the user signal intent to work in the Tags context of the
workspace. Clicking it highlights the item as active and updates the app's `activeSection`
state. In the current legacy implementation, no distinct tags view is mounted in response —
the main content area continues to render the document grid unchanged.

---

## Functional behavior

### onClick — navigate to Tags section

1. User clicks the `<li>` element labelled "🏷️ Tags" (`Sidebar.jsx:48`).
2. The `onClick` handler calls `onNavigate('tags')` — the callback prop supplied by `App`.
3. `App.handleNavigate('tags')` runs (`App.jsx:58`), calling `this.setState({ activeSection: 'tags' })`.
4. React re-renders `<Sidebar>` with `activeSection === 'tags'`, applying `navItemActiveStyle` to the Tags item and resetting all other items to `navItemStyle`.
5. `App.jsx` does **not** conditionally mount a separate tags view — `<DocumentGrid>` remains rendered regardless of `activeSection`.

### Visual active-state toggle

- `Sidebar.jsx:47` uses a ternary: `activeSection === section.id ? navItemActiveStyle : navItemStyle`.
- `navItemActiveStyle` → background `#0f3460`, text `#ffffff`.
- `navItemStyle` → no background, text `#c0c0d0`.
- Only one section can be active at a time (controlled by `App.state.activeSection`).

---

## Acceptance criteria

```gherkin
Scenario: Clicking Tags highlights it and deactivates the previous active item
  Given the user is on the workspace with activeSection = 'documents'
  When they click the "🏷️ Tags" sidebar item
  Then the Tags item renders with background color #0f3460 and text color #ffffff
  And the Documents item renders without a background color

Scenario: Tags section click does not navigate away or reload documents
  Given DocumentGrid is showing a list of documents
  When the user clicks the "🏷️ Tags" sidebar item
  Then the document grid content is unchanged
  And no API call to GET /api/documents is made

Scenario: Tags section is not accessible from the header nav
  Given the user is on the workspace
  Then the Header component renders links for Documents, Upload, and Search only
  And there is no Tags link in the header

Scenario: Refreshing the page clears the active section back to default
  Given the user has set activeSection = 'tags'
  When the page is refreshed
  Then App re-initialises with activeSection = 'documents' (constructor default)
  And the Tags sidebar item is no longer highlighted
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Sidebar `<aside>` container | structural wrapper | `Sidebar.jsx:42` |
| Navigation `<ul>` | list container | `Sidebar.jsx:43` |
| "📁 All Documents" nav item | `<li>` clickable, calls `onNavigate('documents')` | `Sidebar.jsx:44–52` |
| "⬆️ Upload" nav item | `<li>` clickable, calls `onNavigate('upload')` | `Sidebar.jsx:44–52` |
| "🔍 Search" nav item | `<li>` clickable, calls `onNavigate('search')` | `Sidebar.jsx:44–52` |
| "🏷️ Tags" nav item | `<li>` clickable, calls `onNavigate('tags')` — **this feature** | `Sidebar.jsx:44–52` |
| Active-state highlight | conditional style via ternary on `activeSection === section.id` | `Sidebar.jsx:47` |

---

## Out of scope

| Feature | Key | Notes |
|---|---|---|
| Per-document inline tag editor modal | `app-workspace-doc-tag-editor` | Lives in `DocumentGrid.renderTagEditor()`. Opened via the 🏷️ button on each document card/row; calls `PUT /api/documents/:id/tags`. Distinct from this navigation item. |
| Header navigation bar (Documents, Upload, Search) | `app-workspace-header-nav` | `Header.jsx` provides overlapping navigation for three of the four sections. Tags is absent from the header. |
| Document grid main content area | `app-workspace-document-grid` | `DocumentGrid` is always mounted; its behaviour on the tags section is identical to the documents section — it does not filter by tag when `activeSection === 'tags'`. |

---

## Migration notes for Angular 19 target

- In Angular, `activeSection` maps to a router outlet or an `@Input` binding on the shell layout component. The Tags route should be `/workspace/tags`.
- Because no tags-specific view exists in the legacy app, the Angular implementation is expected to introduce a real tags browser (listing all tags with document counts) at this route.
- The `Sidebar` maps to a `SidebarComponent` with an `[activeSection]` input and a `(navigate)` output event. The `RouterLinkActive` directive replaces the manual ternary style logic.
- `App.state.activeSection` has no Redux backing in the legacy code; in the Angular target, active route state is owned by the Angular Router, not a Redux/NgRx store slice.
