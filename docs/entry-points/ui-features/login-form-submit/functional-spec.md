# Functional spec — Sign In Button

**Key:** `login-form-submit`
**URL:** Client-side form submit; calls `POST /api/auth/login` then `POST /api/auth/refresh`
**Legacy source:** `frontend/src/components/LoginForm.jsx` (button at line 112)
**Code-behind:** `frontend/src/context/AuthContext.jsx` (`AuthContext.login`, line 50)
**Parent feature:** `login-form`

---

## Purpose

The Sign In button is the form submission trigger for the DocVault login page. When clicked it
authenticates the user via a two-step JWT flow — an initial login call immediately followed by a
token-refresh call — and, on success, transitions the entire application from the unauthenticated
state (`<LoginForm />`) to the authenticated main workspace rendered by `App`. In practice the
refresh step is broken (FR-007): it crashes on every valid credential submission, making the
application permanently unauthenticated via the normal login path.

---

## Functional behavior

### handleSubmit — form submit

1. Calls `e.preventDefault()` to suppress the native browser POST (`LoginForm.jsx:73`).
2. Reads `email` and `password` from `this.state`.
3. Calls `await this.context.login(email, password)` (`AuthContext.jsx:79`); this sets
   `AuthContext.loading = true`, which simultaneously disables the button and changes its label
   to "Signing in...".
4. **On success:** `AuthContext` sets `isAuthenticated = true`; `App.render()` replaces
   `<LoginForm />` with the main workspace layout.
5. **On failure:** catches `err` and sets
   `this.state.error = err.message || 'Login failed. The app has crashed — check the console.'`;
   the message renders as a `<p>` below the form (`LoginForm.jsx:116`).

### AuthContext.login — two-step JWT flow

1. Sets context state `loading: true, error: null` (`AuthContext.jsx:51`).
2. **Step 1 — login:** `POST /api/auth/login` with `{ email, password }`.
   - Backend (`backend/src/routes/auth.js:17`) validates against hardcoded credentials
     `admin@docvault.local` / `docvault123` (bcrypt compare). No database lookup.
   - On `200`: returns `{ token: "eyJ...", refreshToken: "eyJ..." }`.
   - On `400`: `{ error: "Email and password required" }`.
   - On `401`: `{ error: "Invalid credentials" }`.
   - Frontend stores both tokens:
     `localStorage['docvault_token']` and `localStorage['docvault_refresh_token']`
     (`AuthContext.jsx:63–64`).
3. **Step 2 — refresh (BROKEN, FR-007):** `POST /api/auth/refresh` with `{ refreshToken }`.
   - Backend (`auth.js:61`) calls `jwt.verify(refreshToken, config.jwtSecret)` — this part
     works — but then **returns `{ session: { userId, email, createdAt } }`** (shape copied
     from the legacy `/session/login` handler) instead of `{ token, refreshToken }`.
   - Frontend executes `refreshResponse.data.token.split('.')` at `AuthContext.jsx:75`.
   - **CRASH:** `refreshResponse.data.token` is `undefined` →
     `TypeError: Cannot read properties of undefined (reading 'split')`.
   - The `isAuthenticated = true` transition at `AuthContext.jsx:78` is never reached.
4. Catch block (`AuthContext.jsx:86–93`): sets `context.error = err.message`,
   `loading: false`, `isAuthenticated: false`; re-throws so `LoginForm.handleSubmit`
   also catches and sets `this.state.error`.

### Auth bypass — dev / health check (contextual)

`AuthContext.componentDidMount` (`AuthContext.jsx:31`) calls `GET /api/health`. If
`response.data.skipAuth === true`, the context sets `isAuthenticated = true` without ever
rendering `<LoginForm>`. This path bypasses `handleSubmit` entirely.

---

## Acceptance criteria

```gherkin
Scenario: Submit with correct credentials always crashes due to FR-007
  Given the backend is running and the refresh endpoint is unpatched
  And the user has entered email "admin@docvault.local" and password "docvault123"
  When the user clicks "Sign In"
  Then POST /api/auth/login returns 200 with { token, refreshToken }
  And both tokens are written to localStorage
  And POST /api/auth/refresh is called immediately with the refreshToken
  And the backend returns { session: { userId, email, createdAt } }
  And AuthContext crashes with TypeError "Cannot read properties of undefined (reading 'split')"
  And the error message "Login failed. The app has crashed — check the console." appears below the form
  And isAuthenticated remains false

Scenario: Submit with wrong credentials shows 401 error
  Given the backend is running
  And the user has entered email "bad@example.com" and password "wrong"
  When the user clicks "Sign In"
  Then POST /api/auth/login returns 401 with { error: "Invalid credentials" }
  And POST /api/auth/refresh is never called
  And an error message appears below the form
  And the user remains on the login page

Scenario: Submit with empty fields is blocked by browser validation
  Given the user has not filled in the email or password field
  When the user clicks "Sign In"
  Then the browser's native required-field validation fires on the HTML input
  And LoginForm.handleSubmit is never invoked
  And no HTTP requests are made

Scenario: Button is disabled while the request is in flight
  Given the user has clicked "Sign In" and the request is pending
  When AuthContext.loading transitions to true
  Then the Sign In button has the HTML disabled attribute
  And the button label reads "Signing in..."

Scenario: Dev-mode skipAuth bypass skips the login form entirely
  Given GET /api/health returns { skipAuth: true }
  When the application first mounts
  Then AuthContext.checkAuthBypass sets isAuthenticated = true
  And App renders the main workspace without rendering LoginForm
  And the Sign In button is never shown to the user
```

---

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Form container | `<form onSubmit={handleSubmit}>` | `LoginForm.jsx:95` |
| Email input | `<input type="email" required>` controlled by `this.state.email` | `LoginForm.jsx:96–103` |
| Password input | `<input type="password" required>` controlled by `this.state.password` | `LoginForm.jsx:104–111` |
| **Sign In / Signing in... button** | `<button type="submit">` disabled when `this.context.loading === true`; label is conditional | `LoginForm.jsx:112–114` |
| Local error message | `<p>` rendered when `this.state.error` is truthy | `LoginForm.jsx:116` |
| Context error message | `<p>` rendered when `this.context.error` is truthy (independent of local error) | `LoginForm.jsx:117–119` |

---

## Known bugs

| Bug ID | Description |
|---|---|
| FR-007 | `POST /api/auth/refresh` (`auth.js:78`) returns `{ session:{…} }` instead of `{ token:"…" }`. `AuthContext.login` calls `.split('.')` on `undefined` at line 75, crashing unconditionally whenever valid credentials are submitted. Fix: return `{ token, refreshToken }` from the refresh endpoint. |

---

## Out of scope

- The `checkAuthBypass` / `GET /api/health` initialization path is `AuthContext` startup
  behavior, not triggered by this button. Documented above as context only.
- The `logout` action (`AuthContext.logout`) is a separate feature key.
- The full visual layout of the login card (title, card chrome, page background, inline styles)
  belongs to parent feature key `login-form`.

