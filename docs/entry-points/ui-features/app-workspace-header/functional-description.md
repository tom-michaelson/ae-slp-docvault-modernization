# Functional Description: Application Header

> **Entry Point**: app-workspace-header
> **Location**: frontend/src/components/Header.jsx
> **Type**: UI / Panel
> **Domain**: navigation
> **Legacy URL**: persistent — rendered in App.jsx for all authenticated routes

## Executive Summary

The Application Header is a persistent top-bar component that appears at the top of every authenticated view in DocVault. It is the primary navigation affordance that lets authenticated users switch between the three main workspace sections — Documents, Upload, and Search — without navigating to a different URL. The header is never visible to unauthenticated users; the parent `App` class component gates its rendering behind an `AuthContext.isAuthenticated` check and replaces the entire application layout (including the header) with `<LoginForm />` when the user is not logged in.

The header component itself is fully stateless. It owns no local state, reads from no context or Redux store, and makes no API calls. All navigation side-effects happen in `App.handleNavigate`, which sets `App.state.activeSection`; that state drives which content panel renders in the body area. The header receives a single `onNavigate` callback prop from its parent and forwards the clicked section string to it. Every click is guarded (`onNavigate && onNavigate(...)`) so that a missing `onNavigate` prop is a silent no-op rather than a runtime error.

The header intentionally does **not** show active-section highlighting — that visual affordance is owned exclusively by the `Sidebar` component, which also receives `activeSection` from `App` state. This creates an architectural asymmetry: the Header is a pure navigation emitter; the Sidebar is both a navigation emitter and an active-state reflector.

---

## User Inputs

### Form Fields

None — the header contains no form inputs, text fields, or data-entry controls.

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
| --- | --- | --- | --- |
| Navigate to Documents | `<span>Documents</span>` (Header.jsx:37–39) | `onNavigate('documents')` → `App.handleNavigate` → `setState({ activeSection: 'documents' })` | Click |
| Navigate to Upload | `<span>Upload</span>` (Header.jsx:40–42) | `onNavigate('upload')` → `App.handleNavigate` → `setState({ activeSection: 'upload' })` | Click |
| Navigate to Search | `<span>Search</span>` (Header.jsx:43–45) | `onNavigate('search')` → `App.handleNavigate` → `setState({ activeSection: 'search' })` | Click |

### URL / Route Parameters

None — the header does not consume URL parameters. Navigation does not change the browser URL; it mutates `App.state.activeSection` in memory only. There is no React Router integration anywhere in this component or in `App`.

### Browser / Session Inputs

None — the header reads no cookies, session storage, HTTP context, or local storage. Authentication state (`isAuthenticated`) is consumed by the **parent** `App` component via `static contextType = AuthContext`; `Header` itself never touches `AuthContext`.

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
| --- | --- | --- | --- |
| Header container | `<header>` element: flex row, `justifyContent: space-between`, `padding: 12px 24px`, `backgroundColor: #1a1a2e`, `color: #ffffff`, `boxShadow: 0 2px 4px rgba(0,0,0,0.1)` | Always (when component is mounted) | `Header.jsx:33–47` |
| Brand mark / title | `<h1>` containing "📄 DocVault", `fontSize: 20px`, `fontWeight: bold`, `margin: 0` | Always | `Header.jsx:35` |
| Nav container | `<nav>` flex row, `gap: 16px`, `alignItems: center` | Always | `Header.jsx:36–46` |
| "Documents" nav item | `<span>` with `navLinkStyle` (`color: #a0a0b0`, `cursor: pointer`, `fontSize: 14px`), onClick | Always | `Header.jsx:37–39` |
| "Upload" nav item | `<span>` with `navLinkStyle`, onClick | Always | `Header.jsx:40–42` |
| "Search" nav item | `<span>` with `navLinkStyle`, onClick | Always | `Header.jsx:43–45` |

**Note:** The header is only mounted by `App.render()` when `AuthContext.isAuthenticated === true` (App.jsx:80–82). When not authenticated, `<LoginForm />` is returned instead and `Header` is never mounted in the DOM.

### Navigation / Routing

| Trigger | Destination | Condition |
| --- | --- | --- |
| Click "Documents" | `App.state.activeSection = 'documents'`; `DocumentGrid` becomes visible content | `onNavigate` prop is truthy |
| Click "Upload" | `App.state.activeSection = 'upload'`; upload section becomes visible | `onNavigate` prop is truthy |
| Click "Search" | `App.state.activeSection = 'search'`; search section becomes visible | `onNavigate` prop is truthy |
| Any nav click, `onNavigate` absent | No-op — no state change, no error, no console warning | `onNavigate` prop is `undefined` or `null` |

**Important:** Browser URL never changes on any header navigation action. There is no React Router and no `window.history` manipulation.

### State Changes

None directly from Header. The header calls `onNavigate`, which causes `App.handleNavigate` to mutate `App.state.activeSection`. No cookies, session storage, or other browser state is modified.

---

## API Dependencies

None — the header makes no service calls, API calls, or database operations.

### Service Calls

None.

### Call Sequences

**onClick (any nav item):**
1. User clicks a nav `<span>` (e.g., "Upload").
2. Arrow function evaluates: `() => onNavigate && onNavigate('upload')`.
3. `onNavigate` is truthy (`App.handleNavigate`) → calls `App.handleNavigate('upload')`.
4. `App.handleNavigate` (App.jsx:58–60) calls `this.setState({ activeSection: 'upload' })`.
5. React schedules a re-render of `App`. The body content area renders the component matching `activeSection`.
6. No API call. No DB operation. No URL change.

---

## State Management

### Component Props

| Prop | JS Type | Required | Notes |
| --- | --- | --- | --- |
| `onNavigate` | `function(section: string): void` | No (guarded) | Callback provided by `App.handleNavigate`. Called with `'documents'`, `'upload'`, or `'search'`. If omitted, clicks are silently ignored via short-circuit `&&` guard. |

### Component State

None — `Header` is a stateless functional component. It holds no local state via `useState` or class `this.state`.

### Parent State Affected (App.state)

| State Field | Type | Set By | Default | Effect |
| --- | --- | --- | --- | --- |
| `activeSection` | `string` | `App.handleNavigate(section)` called from Header's `onNavigate` | `'documents'` (App.jsx:52) | Determines which content panel renders in the body area |

---

## Component Details

### Component: `Header`

**File**: `frontend/src/components/Header.jsx` (lines 32–49)

**Type**: Stateless functional React component

**Props received**:
- `onNavigate` — callback from `App.handleNavigate`

**Inline styles defined** (all styles are JavaScript object literals; no external CSS files, no CSS class names):
- `headerStyle`: `display:flex, alignItems:center, justifyContent:space-between, padding:12px 24px, backgroundColor:#1a1a2e, color:#ffffff, boxShadow:0 2px 4px rgba(0,0,0,0.1)`
- `titleStyle`: `fontSize:20px, fontWeight:bold, margin:0`
- `navStyle`: `display:flex, gap:16px, alignItems:center`
- `navLinkStyle`: `color:#a0a0b0, textDecoration:none, fontSize:14px, cursor:pointer`

**Imports**: `React` only — no router, no context, no Redux, no service utilities.

### Parent Component: `App` (class component)

**File**: `frontend/src/App.jsx`

**Context**: `AuthContext` via `static contextType = AuthContext` (App.jsx:47); reads `isAuthenticated`

**State**: `{ activeSection: 'documents', selectedDocument: null, showPreview: false }` (App.jsx:51–55)

**Gate logic** (App.jsx:80–82):
```jsx
if (!isAuthenticated) {
  return <LoginForm />;
}
```
Header is mounted only when this check passes.

**Header usage** (App.jsx:86):
```jsx
<Header onNavigate={this.handleNavigate} />
```

### Related Components (rendered alongside Header in the authenticated layout)

| Component | Relationship | Source ref |
| --- | --- | --- |
| `Sidebar` | Also receives `onNavigate={this.handleNavigate}` AND `activeSection={activeSection}`; shows active-state highlighting that Header lacks | App.jsx:88–91 |
| `LoginForm` | Rendered **instead of** the full layout (including Header) when `!isAuthenticated` | App.jsx:80–81 |
| `DocumentGrid` | Default visible content panel; active when `activeSection === 'documents'` | App.jsx:97–100 |
| `SearchBar` | Always visible in the search container strip above the content area; delegates search to `DocumentGrid.handleSearch` | App.jsx:93–95 |
| `PreviewPanel` | Conditionally rendered when `showPreview === true`; unrelated to Header nav | App.jsx:101–105 |

---

## Workflows

### Workflow 1: Render Header on Authenticated Load

**Use case**: User opens the app or refreshes while already authenticated.

**Preconditions**: `AuthContext.isAuthenticated` is `true`.

**Steps**:

1. **Auth check in App.render()** (App.jsx:77–82)
   - `const { isAuthenticated } = this.context` reads from `AuthContext`.
   - If `false`: returns `<LoginForm />` immediately — Header workflow ends here, component is never mounted.
   - If `true`: continues to full layout render.

2. **Mount Header** (App.jsx:86)
   - `<Header onNavigate={this.handleNavigate} />` is rendered as the topmost element of the `appStyle` container.
   - `this.handleNavigate` is a bound arrow method — stable reference across renders.

3. **Header renders its DOM structure** (Header.jsx:33–47)
   - `<header>` container with dark navy background (`#1a1a2e`).
   - `<h1>` with "📄 DocVault".
   - `<nav>` with three `<span>` items: Documents, Upload, Search.
   - All nav items use `navLinkStyle` (`#a0a0b0`) — no active-state highlighting applied.

**Success outcome**: Header is visible at the top of the page with brand mark and three nav items.

---

### Workflow 2: Navigate to a Section via Header

**Use case**: Authenticated user clicks a nav item to switch workspace sections.

**Preconditions**: Header is mounted; user is authenticated; `onNavigate` prop is `App.handleNavigate`.

**Steps**:

1. **User clicks a nav `<span>`** (e.g., "Upload")
   - `onClick` fires: `() => onNavigate && onNavigate('upload')`

2. **Guard check**
   - `onNavigate && onNavigate('upload')` — short-circuit evaluation. `onNavigate` is `App.handleNavigate` (truthy), so the call proceeds.

3. **`App.handleNavigate('upload')` executes** (App.jsx:58–60)
   - `this.setState({ activeSection: 'upload' })`

4. **React re-renders `App`**
   - `activeSection` is now `'upload'`.
   - Content area renders the upload panel.
   - `Sidebar` receives updated `activeSection='upload'` prop and highlights "Upload" in its nav list.
   - Header re-renders but its visual appearance does **not** change — nav items remain `#a0a0b0`.
   - Browser URL remains unchanged.

**Success outcome**: Upload section content is visible; Sidebar highlights Upload; Header appearance is unchanged.

---

### Workflow 3: Header Not Rendered (Unauthenticated)

**Use case**: Unauthenticated user accesses the app root, or an authenticated user's session expires and `isAuthenticated` becomes `false`.

**Preconditions**: `AuthContext.isAuthenticated` is `false`.

**Steps**:

1. **Auth check in App.render()** (App.jsx:80–82)
   - `if (!isAuthenticated)` is `true`.
   - Returns `<LoginForm />` immediately.
   - The rest of the `render()` function — including `<Header />` — is never reached.

2. **Header never mounted**
   - No `Header` component is instantiated. No `<header>` DOM element is created.

**Success outcome**: Login form is displayed; header is absent from the DOM entirely.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
| --- | --- | --- |
| Page load | None | Header is synchronously rendered; it has no async data dependency and no loading spinner |

### Error States

| Error | Display | Recovery |
| --- | --- | --- |
| `onNavigate` prop missing or null | Silent no-op — user click does nothing, no UI feedback | No automatic recovery; requires parent to pass correct prop |
| `AuthContext` unavailable | `isAuthenticated` is `undefined` (falsy) → `LoginForm` shown; Header not mounted | User must re-authenticate |

### Empty States

Not applicable — the header always renders the same three nav items regardless of application data state.

### Active / Highlighted State

The Header has **no active-state highlighting**. Nav items always render in `#a0a0b0` (grey) regardless of which section is currently active. Active-section indication is delegated to the `Sidebar` component, which receives `activeSection` as a prop and applies a highlight style internally.

### Success States

| Action | Feedback | Next state |
| --- | --- | --- |
| Nav item clicked | No visual change in Header itself | Content area switches to target section; Sidebar updates its highlight |

---

## Use Cases

### UC-1: View the application header on authenticated load

**User story**: As an authenticated user, I want to see the application header so I know what application I'm using and can access top-level navigation.

**Workflow**: Workflow 1 (Render Header on Authenticated Load)

### UC-2: Navigate to Documents via header

**User story**: As an authenticated user, I want to click the Documents link in the header so the document grid becomes the active content area.

**Workflow**: Workflow 2 (Navigate to a Section via Header) with section `'documents'`

### UC-3: Navigate to Upload via header

**User story**: As an authenticated user, I want to click the Upload link in the header so I can access the file upload interface.

**Workflow**: Workflow 2 (Navigate to a Section via Header) with section `'upload'`

### UC-4: Navigate to Search via header

**User story**: As an authenticated user, I want to click the Search link in the header so I can access the document search interface.

**Workflow**: Workflow 2 (Navigate to a Section via Header) with section `'search'`

### UC-5: Header not shown to unauthenticated user

**User story**: As an unauthenticated user, I should see the login form and not the application header.

**Workflow**: Workflow 3 (Header Not Rendered — Unauthenticated)

---

## Security Considerations

### Authentication

- **Required**: Yes, implicitly — the header is only mounted when `AuthContext.isAuthenticated === true`. However, the `Header` component itself has **no authorization check**; the gate lives entirely in `App.render()`. If `Header` were ever rendered outside of `App` (e.g., in a test or alternate entry point), it would lack any auth protection.
- The header does not render any user identity information (no username, no role, no account details).
- The header exposes no actions that modify data — all nav clicks are in-memory state mutations with no server requests.

### Data Exposure

None — the header renders only static string literals ("📄 DocVault", "Documents", "Upload", "Search"). No user data, document metadata, or server responses are surfaced in this component.

### CSRF

Not applicable — the header performs no form submissions and makes no HTTP requests.

---

## Accessibility Considerations

- Nav items are `<span>` elements with `onClick` handlers, **not** `<button>` or `<a>` elements. This has significant accessibility implications:
  - **Keyboard navigation**: `<span>` is not focusable by default. Keyboard-only users cannot reach or activate header nav items via Tab or Enter/Space.
  - **Screen readers**: The `<nav>` landmark is present (good), but `<span>` items are not announced as interactive controls; a screen reader user may not know the items are clickable.
- The `<nav>` element provides a navigation landmark discoverable by screen readers.
- No `aria-label` on the `<nav>` element — screen readers cannot distinguish this nav landmark from others on the page (e.g., the Sidebar's nav).
- No `aria-current` attribute to indicate the active section (and Header renders no active-state styling anyway).
- **Angular target recommendation**: Replace `<span onClick>` with `<button>` or `<a routerLink>` elements to restore full keyboard and screen reader accessibility. Add `aria-label="Main navigation"` to `<nav>`. Consider adding `[attr.aria-current]` binding for the active route item.

---

## Integration Points

### Upstream (what Header depends on)

| Source | Data provided | Failure impact |
| --- | --- | --- |
| `App` class component | `onNavigate` callback prop | Without it, nav clicks silently do nothing (guarded); no visual error |
| `AuthContext.isAuthenticated` (consumed by `App`, not Header directly) | Gates whether Header is mounted at all | If auth context is unavailable, Header is never rendered |

### Downstream (what Header affects)

| System | What this feature affects | How |
| --- | --- | --- |
| `App.state.activeSection` | Set to `'documents'`, `'upload'`, or `'search'` | Via `onNavigate` → `App.handleNavigate` → `setState` |
| `DocumentGrid` panel | Becomes the visible content panel when `activeSection === 'documents'` | App re-renders content area based on state |
| Upload section panel | Becomes the visible content panel when `activeSection === 'upload'` | App re-renders content area based on state |
| Search section panel | Becomes the visible content panel when `activeSection === 'search'` | App re-renders content area based on state |
| `Sidebar` | Reflects active section highlight via `activeSection` prop | App passes updated prop on each re-render |

---

## Analysis Notes

- **No React Router — URL does not reflect navigation**: Clicking header nav items mutates React in-memory state only; the browser URL never changes. A user bookmarking the app while in the Upload section will land on the Documents section (the default `activeSection: 'documents'` from App.jsx:52) on next visit. The Angular target **must** use Angular Router with URL-reflected navigation paths (e.g., `/documents`, `/upload`, `/search`) to fix this architectural gap.
- **Active-state asymmetry between Header and Sidebar**: The Header has zero active-state visual feedback; the Sidebar shows active highlighting. This is an inconsistency — the Angular target should implement `routerLinkActive` on the header nav links to provide visual feedback consistent with the sidebar.
- **Span-not-button accessibility debt**: Using `<span onClick>` instead of `<button>` or `<a>` makes the header nav inaccessible to keyboard-only users. Flag as a BA-level accessibility requirement for the Angular target.
- **All inline styles**: The component uses JavaScript object inline styles with no CSS class names or stylesheets. The Angular target should migrate to component SCSS with semantic class names.
- **`onNavigate` guard pattern**: The `onNavigate && onNavigate(...)` short-circuit is a defensive measure against a missing prop. Angular's `@Output() navigate = new EventEmitter<string>()` makes the contract explicit and eliminates the need for this guard.
- **Header vs Sidebar nav parity gap**: The Header exposes three sections (documents, upload, search). The Sidebar exposes four (documents, upload, search, **tags**). The `tags` section is absent from the Header. The Angular target team should clarify with stakeholders whether the top nav should also expose `tags`, or whether the asymmetry is intentional (Sidebar-only feature).
- **Default active section is `'documents'`**: This default is set in `App.constructor` (App.jsx:52), not in Header. The Angular target should replicate this as the default route (e.g., a redirect from `/` to `/documents`).
- **Header is not itself a class component**: Unlike `App`, `Header` is a functional component with no lifecycle methods and no class-based patterns. It does not need migration away from class components (that debt belongs to `App` — see App.jsx:2 comment `// App.jsx — class component (NOT migrated to functional — FR-016)`).
