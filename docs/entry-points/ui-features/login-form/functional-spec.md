# Functional spec — Login Credentials Form

**Key:** `login-form`
**URL:** `/` (the SPA root — no dedicated route; `App.jsx` renders `<LoginForm />` when `AuthContext.isAuthenticated === false`, and the entire viewport is the login card)
**Legacy source:** `frontend/src/components/LoginForm.jsx:95-115` · `frontend/src/context/AuthContext.jsx`
**Parent feature:** `login`

---

## Purpose

Presents an email/password HTML form that is the sole interactive entry point into DocVault. When submitted, the form delegates to `AuthContext.login()`, which orchestrates a two-step JWT flow (`POST /api/auth/login` → `POST /api/auth/refresh`) against the Node.js backend. Due to bug FR-007, the `/refresh` step crashes unconditionally, so login always fails in the legacy application.

---

## Functional behavior

### handleSubmit (form `onSubmit`)

Triggered when the user submits the form (click "Sign In" or press Enter in any field).

1. Calls `e.preventDefault()` to suppress native browser form submission.
2. Reads `this.state.email` and `this.state.password` from component state.
3. Calls `await this.context.login(email, password)` (`AuthContext.login`, `AuthContext.jsx:50`).
4. If `login()` throws, catches the error and writes `this.setState({ error: err.message || 'Login failed. The app has crashed — check the console.' })`.
5. On success (currently unreachable — see FR-007), `AuthContext` sets `isAuthenticated = true`, `App.jsx` unmounts `<LoginForm />` and renders the main application shell.

### AuthContext.login (called by handleSubmit, `AuthContext.jsx:50`)

1. Sets `loading = true`, `error = null` on context state (disables the Submit button, changes its label to "Signing in…").
2. **Step 1 — POST `/api/auth/login`** (`AuthContext.jsx:55`): sends `{ email, password }`. Backend validates against hardcoded credentials (`admin@docvault.local` / `docvault123`). On HTTP 200: destructures `{ token, refreshToken }` from the response; writes both to `localStorage` (`docvault_token`, `docvault_refresh_token`). On HTTP 400: missing fields. On HTTP 401: sets `context.error = 'Invalid credentials'`, re-throws to the form.
3. **Step 2 — POST `/api/auth/refresh`** *(broken — FR-007)* (`AuthContext.jsx:68`): sends `{ refreshToken }`. The backend returns `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }`.
4. **Crash**: `AuthContext.jsx:75` calls `refreshResponse.data.token.split('.')`. Because `refreshResponse.data.token` is `undefined`, this throws `TypeError: Cannot read properties of undefined (reading 'split')`.
5. Catch block (`AuthContext.jsx:86`): sets `context.error = err.message`, `loading = false`, `isAuthenticated = false`, re-throws to `handleSubmit`.

> **Note for Java developer:** Discard the redundant `/refresh` call on login. The Angular `AuthService` should store the JWT from `POST /api/auth/login` directly into `localStorage`, set `isAuthenticated`, and never call `/refresh` immediately after `/login`.

---

## Acceptance criteria

```gherkin
Scenario: FR-007 bug — login always crashes at the refresh step
  Given the application is loaded and the user is not authenticated
  When the user enters "admin@docvault.local" in the Email field
  And the user enters "docvault123" in the Password field
  And the user clicks "Sign In"
  Then POST /api/auth/login is called with { email: "admin@docvault.local", password: "docvault123" }
  And localStorage["docvault_token"] is written with the JWT access token
  And POST /api/auth/refresh is called with the received refreshToken
  And the response body is { session: { userId, email, createdAt } }
  And AuthContext throws TypeError "Cannot read properties of undefined (reading 'split')"
  And the error paragraph below the form displays that error message
  And AuthContext.isAuthenticated remains false

Scenario: Invalid credentials — 401 from /login
  Given the application is loaded and the user is not authenticated
  When the user enters "wrong@example.com" in the Email field
  And the user enters "badpassword" in the Password field
  And the user clicks "Sign In"
  Then POST /api/auth/login returns HTTP 401 { error: "Invalid credentials" }
  And the error paragraph below the form displays "Invalid credentials"
  And the submit button becomes enabled again
  And AuthContext.isAuthenticated remains false

Scenario: Submit button disabled while request is in flight
  Given the user has clicked "Sign In" with any credentials
  When POST /api/auth/login is in flight
  Then AuthContext.loading is true
  And the submit button has attribute disabled
  And the button label reads "Signing in..."

Scenario: Empty field prevents submission (HTML5 native validation)
  Given the application is loaded and the user is not authenticated
  When the user leaves the Email field empty and clicks "Sign In"
  Then the browser's native required-field validation fires
  And no HTTP request is made
  And AuthContext.login is not called

Scenario: Two error paragraphs can render simultaneously
  Given the user submits valid credentials and the /login call succeeds
  When the /refresh call returns an unexpected shape and AuthContext crashes
  Then AuthContext.error is set to the error message (renders in context error <p>)
  And this.state.error is also set via the LoginForm catch block (renders in local error <p>)
  And both error paragraphs are visible below the form at the same time
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Form container | `<form onSubmit={this.handleSubmit}>` | `LoginForm.jsx:95` |
| Email input | `<input type="email" required>` — controlled by `this.state.email`; `onChange` calls `this.setState({ email })` | `LoginForm.jsx:96-103` |
| Password input | `<input type="password" required>` — controlled by `this.state.password`; `onChange` calls `this.setState({ password })` | `LoginForm.jsx:104-111` |
| Sign In / Signing in… button | `<button type="submit">` — `disabled` when `this.context.loading` is true; label toggles to "Signing in…" while loading | `LoginForm.jsx:112-114` |
| Local error message | conditional `<p>` — rendered only when `this.state.error` is non-null | `LoginForm.jsx:116` |
| Context error message | conditional `<p>` — rendered only when `this.context.error` is non-null | `LoginForm.jsx:117-119` |

---

## Out of scope

| Feature | Reason |
|---|---|
| Auth bypass (`checkAuthBypass`) | Lives in `AuthContext.componentDidMount` (`AuthContext.jsx:36`); fires before `LoginForm` renders and is unrelated to this form's submit flow. Belongs to the `login` page feature. |
| "📄 DocVault Login" heading and card container | Rendered at `LoginForm.jsx:93-94`, outside the `<form>` element (lines 95-115). Belongs to the `login` page feature. |
| Main application workspace | `Header`, `Sidebar`, `DocumentGrid`, `SearchBar`, `PreviewPanel` rendered by `App.jsx` only after `isAuthenticated` is true. Each has its own feature key. |
| Redux `authReducer` / `userReducer` | Neither `LoginForm` nor `AuthContext.login` dispatches any Redux actions. Auth state is held exclusively in React context. |
| `POST /api/auth/session/login` | Backend route exists (`auth.js:99`) but is never called by `LoginForm` or `AuthContext`. |
