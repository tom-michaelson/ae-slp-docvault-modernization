# Functional spec — Grid/List View Toggle

**Key:** `document-grid-view-toggle`
**URL:** N/A — embedded button in the DocumentGrid controls toolbar; not a routed page
**Legacy source:** `frontend/src/components/DocumentGrid.jsx` (lines 996–1002 for button, 606–610 for handler, 1025–1031 for layout switch)

---

## Purpose

Lets the user switch the document library between a card-grid layout (thumbnails in a multi-column CSS grid) and a compact list layout (single-column rows with icon, name, metadata, and tag count). The toggle is a pure client-side preference with no persistence; it resets to `'grid'` on every page load.

---

## Functional behavior

### handleViewToggle — toggle click

1. User clicks the view-toggle `<button>` in the controls bar (line 996–1002).
2. `onClick` fires `this.handleViewToggle` (line 606).
3. `handleViewToggle` calls `this.setState` with a functional updater that flips `state.viewMode`:
   - `'grid'` → `'list'`
   - `'list'` → `'grid'`
4. React re-renders `DocumentGrid.render()`.
5. The document container `<div>` at line 1026 reads the new `viewMode` and applies either `styles.grid` (CSS grid, `repeat(auto-fill, minmax(280px, 1fr))`) or `styles.list` (flex column).
6. The `.map()` at line 1028 calls either `this.renderCard(doc)` or `this.renderListRow(doc)` for each document in `displayDocs`.
7. The toggle button itself re-renders: active style (dark `#0f3460` background + white text) when `viewMode === 'grid'`; inactive style (white background + `#ccc` border) when `viewMode === 'list'`.
8. The button label also flips: `'☰'` (list-switch icon) when in grid mode; `'⊞'` (grid-switch icon) when in list mode.
9. The status bar at line 1039 reflects the current viewMode in its `View: {viewMode}` label.

---

## Acceptance criteria

```gherkin
Scenario: Default state renders grid layout
  Given a user has loaded the DocumentGrid with documents present
  When the component first mounts
  Then state.viewMode is 'grid'
  And the document container uses the CSS grid layout (styles.grid)
  And each document is rendered as a card via renderCard()
  And the toggle button displays '☰' with the active (dark) style
  And the button title attribute reads 'Switch to list'

Scenario: Clicking toggle switches to list layout
  Given state.viewMode is 'grid'
  When the user clicks the view-toggle button
  Then state.viewMode becomes 'list'
  And the document container switches to flex-column layout (styles.list)
  And each document is rendered as a row via renderListRow()
  And the toggle button displays '⊞' with the inactive (light) style
  And the button title attribute reads 'Switch to grid'

Scenario: Clicking toggle again switches back to grid layout
  Given state.viewMode is 'list'
  When the user clicks the view-toggle button
  Then state.viewMode becomes 'grid'
  And the document container switches back to CSS grid layout
  And each document is rendered as a card via renderCard()

Scenario: Toggle with empty document list
  Given state.viewMode is 'grid' and no documents are loaded (displayDocs.length === 0)
  When the user clicks the view-toggle button
  Then state.viewMode becomes 'list'
  And the empty-state panel (renderEmpty) is still displayed unchanged
  And no error is thrown

Scenario: View mode does not persist across page reload
  Given the user toggled to 'list' mode
  When the page is reloaded (component re-mounts)
  Then state.viewMode is reset to 'grid' (constructor default)
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| View-toggle button | `<button onClick>` — conditionally styled; fires `handleViewToggle` | `DocumentGrid.jsx:996-1002` |
| Button label | Text — `'☰'` when viewMode is `'grid'`; `'⊞'` when viewMode is `'list'` | `DocumentGrid.jsx:1001` |
| Button active style | Inline style switch — `styles.viewToggleActive` (dark fill) vs `styles.viewToggle` (outline) | `DocumentGrid.jsx:997` |
| Document container div | `<div>` — `styles.grid` (CSS multi-column grid) vs `styles.list` (flex column) based on viewMode | `DocumentGrid.jsx:1026` |
| Grid card renderer | Loop — `renderCard(doc)` renders each document as a card when viewMode is `'grid'` | `DocumentGrid.jsx:865-904` |
| List row renderer | Loop — `renderListRow(doc)` renders each document as a compact row when viewMode is `'list'` | `DocumentGrid.jsx:907-933` |
| Status bar view label | Text — displays `View: {viewMode}` reflecting current mode | `DocumentGrid.jsx:1039` |

---

## Out of scope

- **Document card content** (`renderCard`): the card itself, tag badges, preview link, and tag-edit button belong to the `document-grid-card` feature key.
- **List row content** (`renderListRow`): the row icon, name, metadata, and tag-edit button belong to the `document-grid-list-row` feature key.
- **Controls bar siblings**: the search input, file-type filter select, and refresh button share the same controls bar but belong to separate feature keys (`document-grid-search-filter`, `document-grid-refresh`).
- **viewMode persistence**: `viewMode` is never written to `localStorage`, a cookie, or a Redux store; any future persistence requirement is new behaviour, not a migration of existing behaviour.
