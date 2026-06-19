# Functional spec — Login Page

**Key:** `login`
**URL:** `GET /` (no dedicated route; `App.jsx` renders `<LoginForm />` when `AuthContext.isAuthenticated === false`)
**Legacy source:** `frontend/src/components/LoginForm.jsx`
**Auth context:** `frontend/src/context/AuthContext.jsx`

---

## Purpose

Provides the sole entry point for the DocVault application — a full-viewport email/password form shown to any unauthenticated visitor. Once authentication succeeds, `App.jsx` unmounts `LoginForm` and mounts the main document workspace in its place. The login step is effectively broken in production (FR-007 bug) and only bypassed via a backend dev-mode flag.

---

## Functional behavior

### componentDidMount — dev-mode auth bypass

Runs automatically when `AuthProvider` mounts, before the user sees the form.

1. `AuthProvider.checkAuthBypass()` issues `GET /api/health`.
2. If `response.data.skipAuth === true` (set by backend `DEV_SKIP_AUTH=true` env var), sets context state: `{ user: { email: 'dev@docvault.local', role: 'admin' }, isAuthenticated: true }`.
3. `App.jsx` detects `isAuthenticated === true` and replaces `<LoginForm />` with the main workspace — the user never interacts with the form.
4. On network error, the catch block swallows the exception silently and the form remains visible.

### handleSubmit — credential login

Triggered when the user submits the form (`form onSubmit`).

1. Calls `e.preventDefault()` to suppress browser navigation.
2. Reads `email` and `password` from `this.state`.
3. Calls `AuthContext.login(email, password)`.
4. Inside `AuthContext.login`:
   a. Sets `loading: true, error: null` (disables submit button, shows "Signing in…").
   b. POSTs `{ email, password }` to `POST /api/auth/login`.
   c. On `400`: missing fields error returned — caught, error state set, re-thrown.
   d. On `401`: backend returns `{ error: 'Invalid credentials' }` — caught, error state set, re-thrown.
   e. On `200`: receives `{ token, refreshToken }`. Writes both to `localStorage` (`docvault_token`, `docvault_refresh_token`).
   f. **BUG (FR-007)**: Immediately POSTs `{ refreshToken }` to `POST /api/auth/refresh`.
   g. `/refresh` returns `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }`.
   h. `refreshResponse.data.token.split('.')` throws `TypeError: Cannot read properties of undefined (reading 'split')`.
   i. Catch block sets `AuthContext.error` to the error message and sets `loading: false`; re-throws to `LoginForm.handleSubmit`.
5. `LoginForm.handleSubmit` catches the re-thrown error, writes `err.message` to `this.state.error`.
6. **Result: authentication always fails** — error message is rendered below the form.

> **Note for Java developer:** The redundant `/refresh` call immediately after `/login` is the buggy pattern to discard. The Angular `AuthService` should store the JWT received from `POST /api/auth/login` directly, decode it locally with `atob()`, and set the authenticated state — no `/refresh` call at login time.

---

## Acceptance criteria

```gherkin
Scenario: Dev-mode health bypass skips login form
  Given the backend GET /api/health returns { "skipAuth": true }
  When the application loads
  Then AuthContext.isAuthenticated is set to true before the form is shown
  And the main workspace is rendered instead of the login form
  And no credentials are entered by the user

Scenario: Happy path login (after FR-007 is fixed)
  Given the user is on the login page
  When they enter "admin@docvault.local" in the Email field
  And they enter "docvault123" in the Password field
  And they click "Sign In"
  Then POST /api/auth/login is called with { email, password }
  And the JWT token is stored in localStorage under "docvault_token"
  And AuthContext.isAuthenticated becomes true
  And the main workspace is rendered

Scenario: Wrong credentials show inline error
  Given the user is on the login page
  When they enter "wrong@example.com" in the Email field
  And they enter "badpassword" in the Password field
  And they click "Sign In"
  Then POST /api/auth/login returns HTTP 401
  And the error paragraph below the form displays "Invalid credentials"
  And the login form remains visible
  And AuthContext.isAuthenticated remains false

Scenario: Empty required field prevents submission
  Given the user is on the login page
  When they leave the Email field empty
  And they click "Sign In"
  Then the browser's native required-field validation fires
  And POST /api/auth/login is NOT called

Scenario: Submit button is disabled while request is in-flight
  Given the user has clicked "Sign In" with valid credentials
  When POST /api/auth/login is in-flight
  Then the submit button has the disabled attribute
  And the button label reads "Signing in..."
  And AuthContext.loading is true

Scenario: FR-007 bug — /refresh crashes after successful /login
  Given the user enters valid credentials and submits
  When POST /api/auth/login returns { token, refreshToken }
  And POST /api/auth/refresh returns { session: { userId, email, createdAt } }
  Then refreshResponse.data.token is undefined
  And AuthContext.login throws TypeError: Cannot read properties of undefined (reading 'split')
  And the error paragraph displays the TypeError message
  And AuthContext.isAuthenticated remains false
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Full-viewport dark background | container `<div>` (full-height flex centering) | `LoginForm.jsx:92` |
| White card panel | container `<div>` (360 px width, rounded, drop shadow) | `LoginForm.jsx:93` |
| "📄 DocVault Login" heading | `<h1>` text | `LoginForm.jsx:94` |
| Email input | `<input type="email" required>` bound to `this.state.email` | `LoginForm.jsx:96–103` |
| Password input | `<input type="password" required>` bound to `this.state.password` | `LoginForm.jsx:104–111` |
| Sign In / Signing in… button | `<button type="submit">` disabled when `AuthContext.loading === true` | `LoginForm.jsx:112–114` |
| Component-level error paragraph | conditional `<p>` shown when `this.state.error` is truthy | `LoginForm.jsx:116` |
| Context-level error paragraph | conditional `<p>` shown when `AuthContext.error` is truthy | `LoginForm.jsx:117–119` |

---

## Out of scope

| Feature | Reason |
|---|---|
| Main workspace (Header, Sidebar, DocumentGrid, PreviewPanel, SearchBar) | Rendered by `App.jsx` after `isAuthenticated === true`; belongs to `app-workspace` feature key |
| Redux `authReducer` / `userReducer` | These reducers exist in the store but `AuthProvider` and `LoginForm` do not dispatch any Redux actions — auth state lives exclusively in React context |
| Session-based login (`POST /api/auth/session/login`) | Backend route exists but is never called by `LoginForm` or `AuthContext`; belongs to the legacy session auth subsystem |
| `apiKeyAuth` middleware | Backend middleware that rejects requests with a missing/invalid `X-API-Key` header; has no frontend interaction and does not affect the login form |
