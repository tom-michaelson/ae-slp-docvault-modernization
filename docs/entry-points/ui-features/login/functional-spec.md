# Functional spec — Login Page

**Key:** `login`
**URL:** `GET /` (rendered conditionally — no dedicated route; `App.jsx` renders `<LoginForm />` when `AuthContext.isAuthenticated === false`)
**Legacy source:** `frontend/src/components/LoginForm.jsx`
**Auth context:** `frontend/src/context/AuthContext.jsx`

---

## Purpose

Allows the sole application user to authenticate with an email and password before accessing the DocVault document workspace. Because the SPA has no client-side router, the login page is the entire viewport when unauthenticated — once authentication succeeds, `App.jsx` unmounts `LoginForm` and mounts the main workspace in its place.

---

## Functional behavior

### componentDidMount — auth bypass check

Executed automatically when `LoginForm` (and its parent `AuthProvider`) mounts.

1. `AuthProvider.checkAuthBypass()` issues `GET /api/health`.
2. If the response contains `{ skipAuth: true }`, sets `AuthContext` state to `{ user: { email: 'dev@docvault.local', role: 'admin' }, isAuthenticated: true }`.
3. `App.jsx` detects `isAuthenticated === true` and replaces `<LoginForm />` with the main workspace — the user never sees the form.
4. On any network error the catch block swallows the exception silently; the login form remains visible.

### handleSubmit — credential login

Triggered when the user submits the form.

1. Calls `e.preventDefault()` to suppress browser form submission.
2. Reads `email` and `password` from component state.
3. Calls `AuthContext.login(email, password)`.
4. Inside `AuthContext.login`:
   a. Sets `loading: true, error: null` in context state (disables the submit button).
   b. POSTs `{ email, password }` to `POST /api/auth/login`.
   c. On `401`: server returns `{ error: 'Invalid credentials' }` — caught as an Axios error, sets `error` state, re-throws.
   d. On `200`: receives `{ token, refreshToken }`. Writes both to `localStorage` (`docvault_token`, `docvault_refresh_token`).
   e. **BUG (FR-007)**: Immediately POSTs `{ refreshToken }` to `POST /api/auth/refresh`.
   f. The `/refresh` endpoint returns `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }`.
   g. `refreshResponse.data.token.split('.')` throws `TypeError: Cannot read properties of undefined (reading 'split')`.
   h. Catch block sets `AuthContext.error` and re-throws to `LoginForm.handleSubmit`.
5. Back in `LoginForm.handleSubmit`, the caught error is set into `this.state.error`.
6. **Result: login always fails** — the form renders the error message and `loading` returns to `false`.

> **Note for Java developer:** The `/refresh` call immediately after `/login` is the buggy pattern to discard. The Angular `AuthService` should store the JWT received from `POST /api/auth/login` directly into `localStorage` and set the authenticated state — no redundant `/refresh` call on login.

---

## Acceptance criteria

```gherkin
Scenario: Dev-mode health bypass skips login form
  Given the backend GET /api/health returns { "skipAuth": true }
  When the application loads
  Then AuthContext.isAuthenticated is set to true
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

Scenario: Empty field prevents submission (HTML5 validation)
  Given the user is on the login page
  When they leave the Email field empty
  And they click "Sign In"
  Then the browser's native required-field validation fires
  And POST /api/auth/login is NOT called

Scenario: Submit button is disabled while loading
  Given the user has submitted valid credentials
  When POST /api/auth/login is in-flight
  Then the submit button is disabled
  And the button label reads "Signing in..."
  And AuthContext.loading is true

Scenario: FR-007 bug — /refresh crashes after successful /login
  Given the user enters valid credentials and submits
  When POST /api/auth/login returns { token, refreshToken }
  And POST /api/auth/refresh returns { session: { userId, email, createdAt } }
  Then refreshResponse.data.token is undefined
  And AuthContext.login throws TypeError
  And the error paragraph displays "Cannot read properties of undefined (reading 'split')"
  And AuthContext.isAuthenticated remains false
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Full-viewport dark background | container div | `LoginForm.jsx:92` |
| Centered white card | container div | `LoginForm.jsx:93` |
| "📄 DocVault Login" heading | `<h1>` text | `LoginForm.jsx:94` |
| Email input | `<input type="email" required>` | `LoginForm.jsx:96–103` |
| Password input | `<input type="password" required>` | `LoginForm.jsx:104–111` |
| Sign In / Signing in… button | `<button type="submit">` disabled when `AuthContext.loading` | `LoginForm.jsx:112–114` |
| Component-level error message | conditional `<p>` shown when `this.state.error` is set | `LoginForm.jsx:116` |
| Context-level error message | conditional `<p>` shown when `AuthContext.error` is set | `LoginForm.jsx:117–119` |

---

## Out of scope

| Feature | Reason |
|---|---|
| Main application workspace (Header, Sidebar, DocumentGrid, PreviewPanel) | Rendered by `App.jsx` after `isAuthenticated === true`; belongs to `app-workspace` feature key |
| Redux `authReducer` / `userReducer` | These reducers exist in the Redux store but `AuthProvider` and `LoginForm` do NOT dispatch any Redux actions — authentication state lives exclusively in `AuthContext` React context |
| Session-based auth (`POST /api/auth/session/login`) | Backend route exists but is never called by `LoginForm` or `AuthContext` |
