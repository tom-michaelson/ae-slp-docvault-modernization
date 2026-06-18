# Functional spec — Sign In Button

**Key:** `login-form-submit`
**URL:** Client-side form submit; calls `POST /api/auth/login` then `POST /api/auth/refresh`
**Legacy source:** `frontend/src/components/LoginForm.jsx` (button at line 112)
**Code-behind:** `frontend/src/context/AuthContext.jsx` (`AuthContext.login`, line 50)
**Parent feature:** `login-form`

---

## Purpose

The Sign In button is the form submission trigger for the DocVault login page. When clicked it
authenticates the user via a two-step JWT flow (initial login immediately followed by a token
refresh) and, on success, transitions the entire application from the unauthenticated state
(`<LoginForm />`) to the authenticated main workspace rendered by `App`. In practice, step two
is broken (FR-007) and the flow always crashes after valid credentials are accepted.

---

## Functional behavior

### handleSubmit — form submit

1. Calls `e.preventDefault()` to suppress the native browser POST.
2. Reads `email` and `password` from `this.state`.
3. Sets `this.context.loading = true` (via `AuthContext.login`), which simultaneously disables
   the button and changes its label to "Signing in...".
4. Calls `await this.context.login(email, password)` (`AuthContext.jsx:50`).
5. **On success:** `AuthContext` sets `isAuthenticated = true`; `App.render()` switches from
   `<LoginForm />` to the main workspace layout.
6. **On failure:** catches `err` and sets `this.state.error = err.message || 'Login failed.
   The app has crashed — check the console.'`; the error message renders below the form.

### AuthContext.login — two-step JWT flow

1. Sets `loading = true`, `error = null` on the context state.
2. **Step 1 — login:** `POST /api/auth/login` with `{email, password}`.
   - Backend (`backend/src/routes/auth.js:17`) validates against hardcoded credentials
     (`admin@docvault.local` / `docvault123`). No database lookup.
   - On `200`: returns `{token: "eyJ...", refreshToken: "eyJ..."}`.
   - On `400`: missing fields. On `401`: wrong credentials.
   - Frontend stores both tokens in `localStorage` keys `docvault_token` and
     `docvault_refresh_token`.
3. **Step 2 — refresh (BROKEN, FR-007):** `POST /api/auth/refresh` with `{refreshToken}`.
   - Backend verifies the JWT, then **returns `{session: {userId, email, createdAt}}`** —
     wrong shape copied from the legacy session-auth handler.
   - Frontend calls `refreshResponse.data.token.split('.')`.
   - **CRASH:** `refreshResponse.data.token` is `undefined` →
     `TypeError: Cannot read properties of undefined (reading 'split')`.
4. Catch block: sets `context.error = err.message`, `loading = false`,
   `isAuthenticated = false`; re-throws so `LoginForm.handleSubmit` also catches and sets
   `this.state.error`.

### Auth bypass — dev mode (contextual)

`AuthContext.componentDidMount` calls `GET /api/health`. If `response.data.skipAuth === true`
the context immediately sets `isAuthenticated = true`, bypassing the login form entirely.
This path does not go through `handleSubmit`.

---

## Acceptance criteria

```gherkin
Scenario: Submit with correct credentials always crashes (FR-007)
  Given the backend is running
  And the user has entered email "admin@docvault.local" and password "docvault123"
  When the user clicks "Sign In"
  Then POST /api/auth/login returns 200 with { token, refreshToken }
  And both tokens are written to localStorage
  And POST /api/auth/refresh is called immediately with the refreshToken
  And AuthContext crashes with TypeError "Cannot read properties of undefined (reading 'split')"
  And the error message "Login failed. The app has crashed — check the console." appears below the form
  And isAuthenticated remains false

Scenario: Submit with wrong credentials shows 401 error
  Given the backend is running
  And the user has entered email "bad@example.com" and password "wrong"
  When the user clicks "Sign In"
  Then POST /api/auth/login returns 401 with { error: "Invalid credentials" }
  And POST /api/auth/refresh is never called
  And the error message "Request failed with status code 401" appears below the form
  And the user remains on the login page

Scenario: Button is disabled while the request is in flight
  Given the user has submitted the form
  When AuthContext.loading is true
  Then the Sign In button has the HTML "disabled" attribute
  And the button label reads "Signing in..."

Scenario: Required fields prevent submit when empty
  Given the user has not filled in the email field
  When the user clicks "Sign In"
  Then the browser's native required-field validation fires
  And LoginForm.handleSubmit is never invoked
  And no HTTP requests are made

Scenario: Dev-mode skipAuth bypass skips login form
  Given GET /api/health returns { skipAuth: true }
  When the application first mounts
  Then AuthContext.checkAuthBypass sets isAuthenticated = true
  And App renders the main workspace without ever rendering LoginForm
  And the Sign In button is never visible
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Form container | `<form onSubmit={handleSubmit}>` | `LoginForm.jsx:95` |
| Email input | `<input type="email" required>` controlled by `this.state.email` | `LoginForm.jsx:96–103` |
| Password input | `<input type="password" required>` controlled by `this.state.password` | `LoginForm.jsx:104–111` |
| **Sign In / Signing in... button** | `<button type="submit">` disabled when `this.context.loading === true` | `LoginForm.jsx:112–114` |
| Local error message | `<p>` conditionally rendered when `this.state.error` is truthy | `LoginForm.jsx:116` |
| Context error message | `<p>` conditionally rendered when `this.context.error` is truthy | `LoginForm.jsx:117–119` |

---

## Known bugs captured in this feature

| Bug ID | Description |
|---|---|
| FR-007 | `POST /api/auth/refresh` returns `{session:{…}}` instead of `{token:"…"}`. `AuthContext.login` calls `.split('.')` on `undefined`, crashing unconditionally whenever valid credentials are submitted. |

---

## Out of scope

- The `checkAuthBypass` / `GET /api/health` initialization path is `AuthContext` startup
  behavior, not part of this button action. Documented above as context only.
- The `logout` action (`AuthContext.logout`) is a separate feature key.
- The full visual layout of the login card (title, card chrome, inline styles) belongs to
  parent feature key `login-form`.
