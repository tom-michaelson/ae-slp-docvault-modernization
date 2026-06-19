# Functional Description: Login Page

> **Entry Point**: `login`
> **Location**: `frontend/src/components/LoginForm.jsx`
> **Type**: UI / Page
> **Domain**: auth
> **Legacy URL**: `/` (conditional — rendered when `AuthContext.isAuthenticated === false`)

## Executive Summary

The Login Page is the application's single authentication gateway. Because the legacy React SPA has no client-side router, `App.jsx` conditionally renders either `<LoginForm />` (when unauthenticated) or the full workspace (when authenticated). The login page therefore occupies the entire viewport until the user successfully signs in — there is no `/login` route, no navigation, and no back-button history entry to manage.

The page has two entry paths. On mount, `AuthProvider.checkAuthBypass()` issues `GET /api/health`: if the backend responds with `{ skipAuth: true }` (a dev-mode flag), `AuthContext.isAuthenticated` is set to `true` automatically and the workspace renders without the user ever seeing the form. On any network failure this check is silently swallowed and the form appears normally. The second path is manual credential entry: the user types an email and password and submits the form, which calls `AuthContext.login()`.

A critical production bug (FR-007) means that `AuthContext.login()` always fails, even with correct credentials. Login succeeds up to writing the JWT to `localStorage`, but then immediately calls `POST /api/auth/refresh` which returns a session-shaped response (`{ session: {...} }`) instead of a JWT-shaped response (`{ token, refreshToken }`). The next line — `refreshResponse.data.token.split('.')` — throws `TypeError: Cannot read properties of undefined (reading 'split')`. The Angular target must discard this redundant `/refresh` call entirely.

---

## User Inputs

### Form Fields

| Field Name | JS Type | Source | Required | Notes |
|---|---|---|---|---|
| `this.state.email` | `string` | Controlled input, `type="email"`, `onChange` → `setState` | yes (HTML5 `required`) | Placeholder: "Email". Browser validates email format via `type="email"`. No additional JS validation. |
| `this.state.password` | `string` | Controlled input, `type="password"`, `onChange` → `setState` | yes (HTML5 `required`) | Placeholder: "Password". No minimum length validation in the legacy code. |

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
|---|---|---|---|
| Submit credentials | `<button type="submit">Sign In</button>` | `LoginForm.handleSubmit` | Form `onSubmit` event |
| Email field change | `<input type="email">` | `setState({ email })` | `onChange` event |
| Password field change | `<input type="password">` | `setState({ password })` | `onChange` event |

### URL / Route Parameters

None. The login page has no dedicated URL route. It is rendered when `AuthContext.isAuthenticated === false` in `App.jsx:80`. There are no query string parameters, no route segments, and no deep-link support.

### Browser / Session Inputs

| Source | Data | Purpose |
|---|---|---|
| `GET /api/health` (on mount) | `{ skipAuth: boolean }` | Dev-mode bypass: if `skipAuth === true`, skip the login form entirely and auto-authenticate as `dev@docvault.local` (role: `admin`) |
| `process.env.REACT_APP_API_URL` | Backend base URL string | Resolves API base URL; defaults to `http://localhost:3001/api` |

> **Note**: The legacy code does **not** check `localStorage` for an existing token on mount. If the user refreshes the browser, they must log in again — there is no session persistence or token re-hydration logic in `AuthProvider.componentDidMount`.

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
|---|---|---|---|
| Full-viewport dark background | `<div>` with `height: 100vh`, `backgroundColor: '#1a1a2e'` (dark navy) | Always | `LoginForm.jsx:92` |
| Centered white card | `<div>` 360px wide, `borderRadius: 8px`, `padding: 32px`, `boxShadow` | Always | `LoginForm.jsx:93` |
| Page title | `<h1>📄 DocVault Login</h1>` (24px, weight 600, color `#1a1a2e`) | Always | `LoginForm.jsx:94` |
| Email input | `<input type="email" required>` with placeholder "Email", controlled | Always | `LoginForm.jsx:96–103` |
| Password input | `<input type="password" required>` with placeholder "Password", controlled | Always | `LoginForm.jsx:104–111` |
| Submit button | `<button type="submit">` with label "Sign In" / "Signing in…" toggle | Always; label changes while `AuthContext.loading === true`; disabled when `loading` | `LoginForm.jsx:112–114` |
| Component-level error paragraph | `<p>` in red (`#c62828`, 13px) below button | `this.state.error !== null` | `LoginForm.jsx:116` |
| Context-level error paragraph | `<p>` in red (`#c62828`, 13px) below button | `this.context.error !== null` | `LoginForm.jsx:117–119` |

> **Screenshot observation** (`login.png`): Shows the idle/empty state — dark navy background, white card with "📄 DocVault Login" heading (emoji renders as a box in screenshot), empty Email/Password inputs, enabled "Sign In" button. No error messages visible. No "Forgot password" link, no "Remember me" checkbox, no password visibility toggle.

### Navigation / Routing

| Trigger | Destination | Condition |
|---|---|---|
| `AuthContext.isAuthenticated` set to `true` | Main workspace (`App.jsx` renders `<Header>`, `<Sidebar>`, `<DocumentGrid>`, `<PreviewPanel>`) | After successful auth bypass or (if FR-007 is fixed) successful `login()` call |
| Dev-mode bypass (`GET /api/health → skipAuth: true`) | Main workspace (same as above) | On `AuthProvider.componentDidMount`, before user sees the form |

There are no explicit `window.location` or React Router `navigate()` calls. Routing is entirely driven by the `isAuthenticated` boolean in `AuthContext` state, which causes `App.jsx`'s `render()` to switch between the two views.

### State Changes

| State | Change | Trigger | Notes |
|---|---|---|---|
| `AuthContext.loading` | `true` | Start of `login()` call | Disables submit button, changes label to "Signing in…" |
| `AuthContext.loading` | `false` | Catch block in `login()` (currently always reached due to FR-007) | Re-enables submit button |
| `AuthContext.error` | Set to error message string | Catch block in `login()` | Displayed via context-level error `<p>` |
| `AuthContext.isAuthenticated` | `true` | Successful `checkAuthBypass()` (dev mode) | Workspace renders; `LoginForm` unmounted |
| `AuthContext.user` | `{ email: 'dev@docvault.local', role: 'admin' }` | Successful `checkAuthBypass()` | User object available to workspace |
| `localStorage['docvault_token']` | Set to JWT string | After successful `POST /api/auth/login` | Written before the crash in FR-007; may be stale after crash |
| `localStorage['docvault_refresh_token']` | Set to refresh token string | After successful `POST /api/auth/login` | Written before the crash in FR-007 |
| `this.state.error` (component) | Set to caught error message | `LoginForm.handleSubmit` catch block | Displayed via component-level error `<p>` |
| `this.state.email` | Updated on every keystroke | `onChange` on email input | Controlled input state |
| `this.state.password` | Updated on every keystroke | `onChange` on password input | Controlled input state |

---

## API Dependencies

### Service Calls

| Method / HTTP Call | When Called | Data In | Data Out | Notes |
|---|---|---|---|---|
| `GET /api/health` | `AuthProvider.checkAuthBypass()` on mount | — | `{ skipAuth?: boolean }` | Fires before user sees the form; used only for dev-mode bypass |
| `POST /api/auth/login` | `AuthProvider.login()` on form submit | `{ email: string, password: string }` | `{ token: string, refreshToken: string }` on 200; `{ error: 'Invalid credentials' }` on 401; `{ error: '...' }` on 400 (missing fields) | Validates against hardcoded credentials (`admin@docvault.local` / `docvault123`) per backend |
| `POST /api/auth/refresh` | `AuthProvider.login()` immediately after successful `/api/auth/login` | `{ refreshToken: string }` | `{ session: { userId, email, createdAt } }` — **BUG**: should return `{ token, refreshToken }` | Always causes a crash (FR-007); must be removed in Angular target |

### Call Sequences

**Sequence 1: Dev-Mode Auth Bypass (componentDidMount)**
1. `AppWithAuth` renders → `AuthProvider` mounts → `componentDidMount` fires
2. `checkAuthBypass()` calls `GET ${API_BASE_URL}/health`
3. If `response.data.skipAuth === true`:
   - `setState({ user: { email: 'dev@docvault.local', role: 'admin' }, isAuthenticated: true })`
   - `App.jsx` re-renders → `isAuthenticated === true` → renders workspace, never shows `<LoginForm />`
4. If network error or `skipAuth` is falsy:
   - Error caught and silently ignored
   - `App.jsx` renders `<LoginForm />`

**Sequence 2: Manual Credential Submit (handleSubmit)**
1. User submits form → `LoginForm.handleSubmit(e)` fires
2. `e.preventDefault()` prevents browser form submission
3. `this.context.login(email, password)` is called
4. Inside `AuthProvider.login()`:
   a. `setState({ loading: true, error: null })` — button disabled, label "Signing in…"
   b. `POST /api/auth/login` with `{ email, password }`
   c. On 401: Axios throws → catch block sets `error`, `loading: false`, re-throws → `LoginForm.handleSubmit` sets `this.state.error`
   d. On 200: receives `{ token, refreshToken }` → writes both to `localStorage`
   e. `POST /api/auth/refresh` with `{ refreshToken }`
   f. Backend returns `{ session: { userId, email, createdAt } }` — **wrong shape**
   g. `refreshResponse.data.token.split('.')` → `TypeError` (token is `undefined`)
   h. Catch block: sets `AuthContext.error = err.message`, `loading: false`, re-throws
   i. `LoginForm.handleSubmit` catch: sets `this.state.error = err.message`
5. Result: both `this.state.error` and `this.context.error` are set; form re-renders with two error paragraphs showing the same TypeError message

---

## State Management

### Component State Fields (`LoginForm`)

| Property | Type | Used In | Notes |
|---|---|---|---|
| `this.state.email` | `string` (initial: `''`) | Controlled email input value; read by `handleSubmit` | Cleared only on component unmount; not reset after failed login |
| `this.state.password` | `string` (initial: `''`) | Controlled password input value; read by `handleSubmit` | Not cleared after failed login |
| `this.state.error` | `string \| null` (initial: `null`) | Rendered in component-level error `<p>` | Set from `err.message` in `handleSubmit` catch block |

### Context State Fields (`AuthContext` / `AuthProvider`)

| Property | Type | Initial | Set by | Read by |
|---|---|---|---|---|
| `user` | `object \| null` | `null` | `login()` success or `checkAuthBypass()` success | `App.jsx` (indirectly — `isAuthenticated` is the gate) |
| `token` | `string \| null` | `null` | `login()` success path (never reached due to FR-007) | Not read anywhere in the legacy app — JWT is stored in `localStorage` |
| `loading` | `boolean` | `false` | `login()` start/end | `LoginForm` — disables submit button and changes label |
| `error` | `string \| null` | `null` | `login()` catch block | `LoginForm` — renders context-level error `<p>` |
| `isAuthenticated` | `boolean` | `false` | `checkAuthBypass()` success or `login()` success (unreachable due to FR-007) | `App.jsx:77` — controls which view is rendered |

### LocalStorage State

| Key | Written | Cleared | Value |
|---|---|---|---|
| `docvault_token` | `AuthProvider.login()` after `POST /api/auth/login` success | `AuthProvider.logout()` | Initial JWT from login; overwritten (theoretically) by refresh JWT on success |
| `docvault_refresh_token` | `AuthProvider.login()` after `POST /api/auth/login` success | `AuthProvider.logout()` | Refresh token for renewal |

> **Critical**: Due to FR-007, `localStorage['docvault_token']` may contain a JWT from a previously successful `/login` call that was never cleaned up when the subsequent crash occurred. The Angular target must always clean up stale tokens on a failed login attempt.

---

## Component Details

### Component: `LoginForm` (Class Component)

**File**: `frontend/src/components/LoginForm.jsx`
**Kind**: React class component (note: **not** migrated to functional — FR-016)
**Context consumed**: `AuthContext` via `static contextType = AuthContext`

**State**: `{ email: string, password: string, error: null | string }`

**Lifecycle methods**:
- `constructor(props)`: initialises state
- No `componentDidMount` on `LoginForm` itself — bypass logic lives in `AuthProvider`

**Event handlers**:
- `handleSubmit(e)` — async; calls `e.preventDefault()`, delegates to `this.context.login(email, password)`, catches errors into `this.state.error`

**Inline styles** (all defined as module-level `const` objects):
- `formStyle`: full-viewport dark navy container
- `cardStyle`: white 360px card, 8px border radius, shadow
- `titleStyle`: 24px bold, dark navy heading
- `inputStyle`: full-width, 10px/12px padding, 1px border, 4px radius
- `buttonStyle`: full-width, dark navy (#0f3460) background, white text
- `errorStyle`: red (#c62828) 13px centred paragraph

### Component: `AuthProvider` (Class Component)

**File**: `frontend/src/context/AuthContext.jsx`
**Kind**: React class component providing `AuthContext` via `<AuthContext.Provider value={...}>`
**Context exported**: `AuthContext` (created with `createContext(null)`)

**State**: `{ user, token, loading, error, isAuthenticated }`

**Methods available on context value**:
- `login(email, password)` — async; always crashes in production (FR-007)
- `logout()` — synchronous; clears state and localStorage

**Environment**:
- `API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api'`

### Component: `App` (Class Component, gating parent)

**File**: `frontend/src/App.jsx`
**Relevant logic**: `if (!isAuthenticated) return <LoginForm />;` (line 80)
**Mount order**: `AppWithAuth` → `Provider (Redux)` → `AuthProvider` → `App` → conditionally `LoginForm` or workspace

---

## Workflows

### Workflow 1: Dev-Mode Auth Bypass (componentDidMount / checkAuthBypass)

**Use case**: Developer or CI environment with `DEV_SKIP_AUTH` backend flag bypasses the login form automatically.

**Preconditions**: Application loads; `AuthProvider.componentDidMount` fires before `App` has a chance to render `<LoginForm />`.

**Steps**:

1. **Mount sequence**
   - `AppWithAuth` renders → wraps `<Provider>` (Redux) → `<AuthProvider>` → `<App />`
   - `AuthProvider.componentDidMount()` fires at line 31 → calls `checkAuthBypass()`

2. **Health check**
   - `axios.get('${API_BASE_URL}/health')` — GET request to the backend health endpoint
   - Awaits response

3. **Bypass decision**
   - If `response.data.skipAuth === true`:
     - `setState({ user: { email: 'dev@docvault.local', role: 'admin' }, isAuthenticated: true })`
     - `App.jsx` re-renders: `isAuthenticated === true` → returns workspace instead of `<LoginForm />`
     - User never sees the login form
   - If `response.data.skipAuth` is falsy (including missing):
     - No state change; `App.jsx` renders `<LoginForm />`
   - If network error:
     - Catch block silently swallows the error
     - `App.jsx` renders `<LoginForm />`

**Success outcome**: Workspace renders with `user = { email: 'dev@docvault.local', role: 'admin' }` and `isAuthenticated = true`. No credentials entered.

**Failure outcome**: Login form appears (normal user experience).

---

### Workflow 2: Credential Login (handleSubmit) — **Broken in production**

**Use case**: User enters email and password to authenticate against the DocVault API.

**Preconditions**: `AuthContext.isAuthenticated === false`; `<LoginForm />` is visible; user has filled both fields.

**Steps**:

1. **Form submission**
   - User clicks "Sign In" button or presses Enter
   - `<form onSubmit={this.handleSubmit}>` fires `handleSubmit(e)`
   - `e.preventDefault()` suppresses browser navigation

2. **Read credentials from state**
   - `const { email, password } = this.state`

3. **Delegate to context**
   - `await this.context.login(email, password)` — calls `AuthProvider.login()`

4. **Context: start loading**
   - `setState({ loading: true, error: null })`
   - Submit button becomes disabled with label "Signing in…"

5. **Context: POST /api/auth/login**
   - `axios.post('${API_BASE_URL}/auth/login', { email, password })`
   - **On 401**: Axios throws (server responds `{ error: 'Invalid credentials' }`) → jump to step 9
   - **On 400**: Axios throws (server responds `{ error: '...' }` for missing fields) → jump to step 9
   - **On 200**: receives `{ token, refreshToken }` → continue to step 6

6. **Context: write initial tokens to localStorage**
   - `localStorage.setItem('docvault_token', token)`
   - `localStorage.setItem('docvault_refresh_token', refreshToken)`

7. **Context: POST /api/auth/refresh** ← **BUG (FR-007)**
   - `axios.post('${API_BASE_URL}/auth/refresh', { refreshToken })`
   - Backend returns `{ session: { userId, email, createdAt } }` — wrong shape

8. **Context: CRASH**
   - `refreshResponse.data.token.split('.')` — `refreshResponse.data.token` is `undefined`
   - `TypeError: Cannot read properties of undefined (reading 'split')` is thrown

9. **Context: catch block**
   - `setState({ error: err.message, loading: false, isAuthenticated: false })`
   - Re-throws error to `LoginForm.handleSubmit`

10. **LoginForm: catch block**
    - `this.setState({ error: err.message || 'Login failed. The app has crashed — check the console.' })`

11. **Re-render**
    - Submit button re-enabled with label "Sign In"
    - Two error `<p>` elements appear:
      - Component-level: `this.state.error` (below button, `LoginForm.jsx:116`)
      - Context-level: `this.context.error` (below component error, `LoginForm.jsx:117–119`)
    - Both contain the same TypeError message in the FR-007 case

**Success outcome (after FR-007 is fixed)**: `AuthContext.isAuthenticated` becomes `true`; `App.jsx` renders workspace; `LoginForm` unmounts.

**Current failure outcome**: Login always fails with `TypeError`; form remains visible; error messages displayed.

---

## Visual States

### Loading State

| Context | Indicator | Notes |
|---|---|---|
| POST /api/auth/login in-flight | Submit button disabled, label changes to "Signing in…" | Driven by `AuthContext.loading === true`; button has `disabled={loading}` |

### Error States

| Error | Display | Recovery |
|---|---|---|
| 401 Invalid credentials | Red `<p>` below button (component-level): "Request failed with status code 401" (Axios default message) | User re-enters credentials |
| FR-007 crash (correct credentials) | Two red `<p>` paragraphs: component and context both show "Cannot read properties of undefined (reading 'split')" | Cannot recover — bug must be fixed server-side or by removing the `/refresh` call |
| Network error on `/login` | Red `<p>` with Axios network error message | User retries or checks network |
| Network error on health check | Silent — login form appears normally | None required |

### Empty / Initial State

| Context | Display | Actions available |
|---|---|---|
| Unauthenticated, no bypass | Dark navy background, white card, empty Email/Password fields, enabled "Sign In" button | Enter credentials and submit |

### Success State

| Action | Feedback | Next state |
|---|---|---|
| Dev-mode bypass (`skipAuth: true`) | Immediate — `LoginForm` never renders | Workspace renders |
| Credential login (post FR-007 fix) | No visual confirmation on `LoginForm` — component unmounts as workspace replaces it | Workspace renders |

---

## Use Cases

### UC-1: Developer bypasses login in dev environment

**User story**: As a developer, I want the login form to be skipped automatically in dev mode so I don't need to enter credentials during local development.

**Workflow**: Workflow 1 (Dev-Mode Auth Bypass)

### UC-2: Administrator logs in with credentials

**User story**: As the application administrator, I want to enter my email and password to access the DocVault workspace.

**Workflow**: Workflow 2 (Credential Login) — currently broken (FR-007); functional after fix

### UC-3: Incorrect credentials show an error

**User story**: As a user who has typed the wrong password, I want to see a clear error message so I know to try again.

**Workflow**: Workflow 2, 401 branch (step 9 catch)

### UC-4: Empty fields prevent API call

**User story**: As a user who accidentally submits without filling in a field, I want to be told which field is missing without a network call being made.

**Mechanism**: HTML5 `required` attribute on both inputs; browser native validation fires before `onSubmit` handler. No POST is made.

---

## Security Considerations

### Authentication Model

- **Public route**: No authentication guard on the login page itself. `App.jsx` renders `<LoginForm />` whenever `AuthContext.isAuthenticated === false`.
- **Single user**: The backend validates against hardcoded credentials (`admin@docvault.local` / `docvault123`). There is no user database, registration flow, or password reset. The Angular target must implement equivalent credential validation.

### Token Storage

- **localStorage**: Both JWT and refresh token are stored in `localStorage` (keys: `docvault_token`, `docvault_refresh_token`). This is vulnerable to XSS attacks. The Angular target should consider `HttpOnly` cookies or a secure in-memory alternative, but must match the existing backend contract.
- **Stale token risk**: Due to FR-007, `localStorage['docvault_token']` may be written with a valid JWT but the app remains in an unauthenticated state (the crash occurs after the write). The Angular target must ensure atomic success — only write tokens when the entire login sequence succeeds, and clean up on failure.

### CSRF

- No anti-forgery tokens in the React legacy app (SPA with Axios; no form action URLs). The Angular target's `HttpClient` default CSRF behaviour (`X-XSRF-TOKEN`) should be evaluated against the Spring Boot API's CSRF configuration.

### Password Field

- `<input type="password">` — masked by browser. No additional masking, no copy protection, no auto-complete suppression (`autocomplete` attribute not set in legacy code).

### Dev Bypass Security

- The `skipAuth` bypass is controlled entirely by the backend (`GET /api/health → { skipAuth: true }`). If the backend is misconfigured in a non-dev environment with this flag, any user can access the workspace without credentials. This must be a server-side environment guard only.

---

## Accessibility Considerations

- No `<label>` elements for the email or password inputs — only placeholder text (`placeholder="Email"`, `placeholder="Password"`). Screen readers may not announce field purpose correctly. The Angular target must add proper `<label for>` associations or `aria-label` attributes.
- No `aria-live` region for error messages — screen readers may not announce errors injected after submission.
- No `role="alert"` on error paragraphs.
- The `<h1>` heading "📄 DocVault Login" provides a page-level landmark; the emoji character renders as a visible icon but may be announced as a long description by screen readers.
- The submit button changes its label (`"Sign In"` / `"Signing in…"`) but no `aria-busy` attribute is set during loading.
- No keyboard focus management — focus remains on the last active input after submission; no focus is moved to the error message.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
|---|---|---|
| `GET /api/health` | `{ skipAuth?: boolean }` | Error swallowed silently; login form appears normally |
| `POST /api/auth/login` | `{ token, refreshToken }` on 200 | Login fails; error displayed |
| `POST /api/auth/refresh` | Should return `{ token, refreshToken }` — currently returns `{ session: {...} }` (bug) | Always crashes the login flow |

### Downstream

| System | What this page enables | How |
|---|---|---|
| `App.jsx` / main workspace | Renders after `isAuthenticated === true` | `AuthContext.isAuthenticated` state change triggers `App.render()` to switch views |
| `localStorage` | Stores JWT for use by other API calls | `AuthProvider.login()` writes `docvault_token` and `docvault_refresh_token` |

---

## Analysis Notes

1. **FR-007 — Remove `/refresh` call on login.** The `POST /api/auth/refresh` call immediately after `POST /api/auth/login` must not be replicated in the Angular target. The `AuthService` should store the JWT received from `POST /api/auth/login` directly into `localStorage` and set `isAuthenticated = true`. No redundant refresh call on login.

2. **No session persistence on reload.** `AuthProvider.componentDidMount` only calls `checkAuthBypass()` — it does NOT check `localStorage` for an existing `docvault_token`. This means every browser reload forces re-login. The Angular target should decide whether to implement token re-hydration on app init (read token from `localStorage`, validate, restore auth state) — this is a business decision, not an existing behaviour to replicate.

3. **No client-side routing.** The legacy app has no React Router or similar. The login "page" is just a conditional in `App.jsx:80`. The Angular target will have a proper route (`/login`) with an `AuthGuard` that redirects unauthenticated users — this is a structural difference, not a feature gap.

4. **Class component — not migrated to functional.** `LoginForm` is a React class component (FR-016 flag in comments). The Angular equivalent is a standard Angular component with a reactive form — no class/functional distinction applies.

5. **Dual error display.** Both `this.state.error` (component-level) and `this.context.error` (context-level) are rendered as separate `<p>` elements. In the FR-007 crash scenario both show the same message, producing duplicate errors. The Angular target should consolidate error display into a single location.

6. **Redux is unused by auth.** `App.jsx` wraps `<Provider store={store}>` and the Redux store has `authReducer` and `userReducer`, but `AuthProvider` and `LoginForm` do not dispatch any Redux actions. All auth state lives exclusively in `AuthContext`. The Angular target should use a service-level state (e.g., `BehaviorSubject` in `AuthService`) and not involve NgRx for auth state unless explicitly decided.

7. **Hardcoded credentials.** The backend validates against `admin@docvault.local` / `docvault123`. This is relevant for E2E tests in the Angular target — use these credentials in test scenarios until the backend is updated.

8. **Two localStorage writes before crash.** In the FR-007 scenario, `localStorage['docvault_token']` and `localStorage['docvault_refresh_token']` are written with valid values from `/login` before the crash. These stale tokens persist across page refreshes. The Angular target must clean up localStorage on login failure.

9. **`API_BASE_URL` environment variable.** The Angular target must use `environment.apiUrl` (or equivalent Angular environment file) mapped to `REACT_APP_API_URL`. Default: `http://localhost:3001/api`.

10. **No `Authorization` header setup in login flow.** The legacy app writes the JWT to `localStorage` but the login flow itself does not set a default Axios Authorization header. Presumably other API calls read from `localStorage['docvault_token']` directly. The Angular target's `HttpInterceptor` should read from the auth service and attach `Authorization: Bearer {token}` to all requests.
