# Functional Description: Sign In Button

> **Entry Point**: `login-form-submit`
> **Location**: `frontend/src/components/LoginForm.jsx`
> **Type**: UI / Form
> **Domain**: auth
> **Legacy URL**: `POST /api/auth/login → POST /api/auth/refresh` (client-side sequence; no page navigation on success)

## Executive Summary

The Sign In button is the form-submission trigger on the DocVault login page. When the user enters credentials and clicks the button, `LoginForm.handleSubmit` fires, delegates entirely to `AuthContext.login(email, password)`, and waits for the promise to resolve or reject. A successful authentication is intended to set `isAuthenticated = true` on the `AuthContext` provider, causing `App.render()` to unmount `<LoginForm />` and mount the main workspace in its place — a full-page client-side transition with no browser navigation.

In practice the transition never completes. `AuthContext.login` executes a mandatory two-step JWT flow: first `POST /api/auth/login` (which works correctly and returns `{ token, refreshToken }`), then immediately `POST /api/auth/refresh` (which is broken per **FR-007**: the backend returns `{ session: {…} }` instead of `{ token, refreshToken }`). The frontend unconditionally reads `refreshResponse.data.token.split('.')` at `AuthContext.jsx:75`, producing a `TypeError: Cannot read properties of undefined (reading 'split')` crash on every attempt with valid credentials.

Non-obvious aspects: (1) The button's disabled/label state is driven by `AuthContext.loading`, a context-level flag — not local component state — meaning any other consumer that sets `loading = true` would also disable this button. (2) Two independent error `<p>` elements render below the form: `this.state.error` (set in `LoginForm.handleSubmit`'s catch block) and `this.context.error` (set in `AuthContext.login`'s catch block). Because `AuthContext` re-throws the error, both catch blocks fire for the same error event, and both messages may be visible simultaneously. (3) A dev-mode bypass exists: if `GET /api/health` returns `{ skipAuth: true }` during `AuthContext.componentDidMount`, the context sets `isAuthenticated = true` immediately, the login form is never rendered, and this button is never visible.

---

## User Inputs

### Form Fields

| Field Name | JS Type | Source | Required | Notes |
|---|---|---|---|---|
| `this.state.email` | `string` | `<input type="email">` controlled via `onChange` → `this.setState({ email })` | yes (`required` attr) | Browser enforces valid email format before `handleSubmit` fires. `LoginForm.jsx:96–103` |
| `this.state.password` | `string` | `<input type="password">` controlled via `onChange` → `this.setState({ password })` | yes (`required` attr) | No min-length constraint in source. `LoginForm.jsx:104–111` |

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
|---|---|---|---|
| Submit credentials | `<button type="submit">` inside `<form onSubmit={handleSubmit}>` | `LoginForm.handleSubmit` | Click or Enter key in any form field |

### URL / Route Parameters

None. This is a purely client-side action; the page URL does not change when the button is clicked.

### Browser / Session Inputs

| Source | Data | Purpose |
|---|---|---|
| `localStorage['docvault_token']` | Access JWT (string) | Written after step 1 succeeds; overwritten (intended) after step 2 succeeds (never reached due to FR-007) |
| `localStorage['docvault_refresh_token']` | Refresh JWT (string) | Written after step 1 succeeds; not re-read during the same submit flow |
| `GET /api/health` → `response.data.skipAuth` | boolean | Read at `AuthContext.componentDidMount` only; bypasses login form entirely if `true` (not part of button action) |

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
|---|---|---|---|
| Button label | "Sign In" (idle) or "Signing in..." (in-flight) | `this.context.loading === false` vs `true` | `LoginForm.jsx:113` |
| Button disabled state | `disabled` HTML attribute present | `this.context.loading === true` | `LoginForm.jsx:112` |
| Local error message | Red `<p>` with `this.state.error` text | `this.state.error` is truthy | `LoginForm.jsx:116` |
| Context error message | Red `<p>` with `this.context.error` text | `this.context.error` is truthy | `LoginForm.jsx:117–119` |

### Navigation / Routing

| Trigger | Destination | Condition |
|---|---|---|
| `AuthContext.isAuthenticated = true` | Main workspace (App re-renders, `<LoginForm />` unmounted) | Unreachable due to FR-007 in current legacy code |
| `skipAuth = true` (dev bypass) | Main workspace without login | `GET /api/health` returns `{ skipAuth: true }` at mount |

### State Changes

| State | Change | Trigger | Notes |
|---|---|---|---|
| `AuthContext.loading` | `false → true` | `login()` called | Immediately disables button and changes label |
| `AuthContext.loading` | `true → false` | `login()` resolves or rejects | Re-enables button |
| `AuthContext.error` | `null → err.message` | `login()` catch block (`AuthContext.jsx:87`) | Rendered by context error `<p>` in `LoginForm` |
| `LoginForm.state.error` | `null → err.message` | `handleSubmit` catch block (`LoginForm.jsx:81`) | Rendered by local error `<p>` in `LoginForm` |
| `localStorage['docvault_token']` | Written | Step 1 succeeds (`AuthContext.jsx:63`) | Overwrite intended at line 85 — never reached |
| `localStorage['docvault_refresh_token']` | Written | Step 1 succeeds (`AuthContext.jsx:64`) | Written once; not cleaned up on logout path |
| `AuthContext.user` | `null → payload` | Step 2 success (unreachable, FR-007) | JWT payload decoded from base64 part[1] |
| `AuthContext.isAuthenticated` | `false → true` | Step 2 success (unreachable, FR-007) | Triggers App re-render to main workspace |

---

## API Dependencies

### Service Calls

| Method / Endpoint | When Called | Data In | Data Out |
|---|---|---|---|
| `AuthContext.login(email, password)` | `LoginForm.handleSubmit` on form submit | `email: string`, `password: string` | Promise — resolves void on success; throws on failure |
| `POST /api/auth/login` | Inside `AuthContext.login`, step 1 | `{ email, password }` | `{ token: "eyJ...", refreshToken: "eyJ..." }` (200) · `{ error: "Email and password required" }` (400) · `{ error: "Invalid credentials" }` (401) |
| `POST /api/auth/refresh` | Inside `AuthContext.login`, step 2 (immediately after step 1) | `{ refreshToken }` | **BUG (FR-007):** returns `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }` |

### Call Sequences

**handleSubmit (happy path — currently crashes at step 2):**

1. `e.preventDefault()` — suppresses native browser form submission.
2. Read `email`, `password` from `this.state`.
3. `await this.context.login(email, password)` — call `AuthContext.login`.
   - a. `setState({ loading: true, error: null })` on context.
   - b. `POST /api/auth/login { email, password }` → `{ token, refreshToken }`.
   - c. `localStorage.setItem('docvault_token', token)`.
   - d. `localStorage.setItem('docvault_refresh_token', refreshToken)`.
   - e. `POST /api/auth/refresh { refreshToken }` → `{ session: {...} }` (**BUG**).
   - f. `refreshResponse.data.token.split('.')` — **crashes**: `token` is `undefined`.
   - g. Catch block: `setState({ error: err.message, loading: false, isAuthenticated: false })`; re-throws.
4. `LoginForm.handleSubmit` catch block: `this.setState({ error: err.message || 'Login failed…' })`.
5. Both error `<p>` elements render with the same `TypeError` message.

**handleSubmit (wrong credentials):**

1–3a: Same as above.
   - b. `POST /api/auth/login { email, password }` → `401 { error: "Invalid credentials" }` — axios throws.
   - c. Catch block: `setState({ error: "Request failed with status code 401", loading: false })`, re-throws.
4. `LoginForm.handleSubmit` catch: sets `this.state.error`.
5. Both error surfaces show "Request failed with status code 401".
6. `POST /api/auth/refresh` is never called.

**handleSubmit (empty fields — browser-native validation):**

1. `<form>` native validation fires on submit; `required` inputs are empty.
2. Browser blocks submit — `handleSubmit` is never invoked.
3. No HTTP requests made.

---

## State Management

### Component State Fields

| Property | Type | Initialized | Used In | Notes |
|---|---|---|---|---|
| `this.state.email` | `string` | `''` | Controlled input value; read in `handleSubmit` | `LoginForm.jsx:66` |
| `this.state.password` | `string` | `''` | Controlled input value; read in `handleSubmit` | `LoginForm.jsx:67` |
| `this.state.error` | `string \| null` | `null` | Rendered in local error `<p>` | `LoginForm.jsx:68`; set in `handleSubmit` catch (`jsx:81`) |

### Context State (AuthContext)

| Property | Type | Initialized | Consumed by this feature | Notes |
|---|---|---|---|---|
| `loading` | `boolean` | `false` | Button `disabled` attr and label | Set `true` at login start; `false` at end (success or failure) |
| `error` | `string \| null` | `null` | Context error `<p>` | Set in `AuthContext.login` catch; persists until next login attempt |
| `isAuthenticated` | `boolean` | `false` | Causes `App` re-render to workspace | Intended to go `true` on success; never reached (FR-007) |
| `user` | `object \| null` | `null` | Workspace (not this form) | JWT payload from `refreshResponse.data.token` — unreachable |
| `token` | `string \| null` | `null` | Workspace API calls | Set from `refreshResponse.data.token` — unreachable |

### localStorage State

| Key | Written | Read back | Cleared |
|---|---|---|---|
| `docvault_token` | Step 1 success (line 63); intended overwrite step 2 (line 85, unreachable) | Not re-read within this flow | `AuthContext.logout()` |
| `docvault_refresh_token` | Step 1 success (line 64) | Re-used in step 2 POST body | `AuthContext.logout()` |

---

## Component Details

### View Component: `LoginForm`

**File**: `frontend/src/components/LoginForm.jsx`

**Type**: React class component (not migrated to functional — FR-016)

**Context consumed**: `AuthContext` via `static contextType = AuthContext` (line 61)

**Local state**: `{ email: '', password: '', error: null }`

**Handlers**:
- `handleSubmit(e)` — async arrow function (line 72); calls `this.context.login`; catches errors into `this.state.error`

**Render output**: A full-viewport dark-background container (`height: 100vh`, `backgroundColor: #1a1a2e`) with a centered white card. Inside the card: an `<h1>` title "📄 DocVault Login", a `<form>`, the email input, the password input, the submit button, and up to two error paragraphs.

### Context Provider: `AuthProvider` / `AuthContext`

**File**: `frontend/src/context/AuthContext.jsx`

**Type**: React class component with `createContext`

**State**: `{ user, token, loading, error, isAuthenticated }`

**Methods exposed on context value**:
- `login(email, password)` — async, two-step JWT flow (line 50)
- `logout()` — clears state and localStorage (line 96)

**Lifecycle**:
- `componentDidMount` → `checkAuthBypass()` — polls `GET /api/health`; sets `isAuthenticated = true` if `skipAuth` is truthy (line 36–48)

### Backend Route: `POST /api/auth/login`

**File**: `backend/src/routes/auth.js`, line 17

**Auth**: none (public endpoint)

**Validation**: `email` and `password` must both be present (400 if missing)

**Credential store**: hardcoded `ADMIN_EMAIL = 'admin@docvault.local'`, password verified with `bcrypt.compareSync` against `bcrypt.hashSync('docvault123', 10)`. No database lookup.

**Success response** (`200`): `{ token: "eyJ...", refreshToken: "eyJ..." }`
- `token`: HS256 JWT, payload `{ userId: 'abc-123', email, role: 'admin' }`, 1-hour expiry
- `refreshToken`: HS256 JWT, payload `{ userId: 'abc-123', email, type: 'refresh' }`, 7-day expiry

**Error responses**: `400 { error: "Email and password required" }`, `401 { error: "Invalid credentials" }`, `500 { error: "Login failed" }`

### Backend Route: `POST /api/auth/refresh` (**BROKEN — FR-007**)

**File**: `backend/src/routes/auth.js`, line 61

**Auth**: none (validates JWT inline)

**Input**: `{ refreshToken: "eyJ..." }`

**Actual response** (`200`): `{ session: { userId, email, createdAt } }` — wrong shape. Copied from legacy `POST /api/auth/session/login` handler and never corrected.

**Expected response** (what frontend needs): `{ token: "eyJ...", refreshToken: "eyJ..." }`

**Error responses**: `400 { error: "Refresh token required" }`, `401 { error: "Invalid or expired refresh token" }`, `500 { error: "Token refresh failed" }`

---

## Workflows

### Workflow 1: Submit with Valid Credentials (Crash Path — FR-007)

**Use case**: User enters the correct credentials and clicks Sign In.

**Preconditions**: Backend running; `email = "admin@docvault.local"`, `password = "docvault123"`.

**Steps**:

1. **Form submission**
   - `<form onSubmit={handleSubmit}>` fires `LoginForm.handleSubmit(e)` (`LoginForm.jsx:72`)
   - `e.preventDefault()` prevents browser POST

2. **Delegate to context**
   - `await this.context.login(email, password)` (`LoginForm.jsx:79`)
   - `AuthContext.login` sets `loading = true`, `error = null` — button goes to "Signing in..." and is disabled

3. **Step 1 — POST /api/auth/login** (`AuthContext.jsx:55`)
   - Backend validates credentials, generates JWTs
   - Response `200 { token, refreshToken }`
   - `localStorage.setItem('docvault_token', token)` (line 63)
   - `localStorage.setItem('docvault_refresh_token', refreshToken)` (line 64)

4. **Step 2 — POST /api/auth/refresh** (`AuthContext.jsx:68`)
   - Request body: `{ refreshToken }` (the value just stored)
   - Backend verifies JWT successfully, but returns `{ session: { userId, email, createdAt } }` (**BUG**)

5. **CRASH** (`AuthContext.jsx:75`)
   - `refreshResponse.data.token` is `undefined`
   - `.split('.')` throws `TypeError: Cannot read properties of undefined (reading 'split')`

6. **Error propagation**
   - `AuthContext.login` catch: `setState({ error: "Cannot read…", loading: false, isAuthenticated: false })`; re-throws error
   - `LoginForm.handleSubmit` catch: `this.setState({ error: "Cannot read…" })` (or fallback message)

7. **Visual outcome**
   - Button re-enabled ("Sign In")
   - Two red `<p>` elements appear below the form with the TypeError message
   - `isAuthenticated` remains `false`; user stays on login page
   - `localStorage` contains `docvault_token` and `docvault_refresh_token` from step 3 (stale, never cleaned up for this crash path)

**Failure outcome**: Form appears to fail; user cannot log in regardless of credentials.

---

### Workflow 2: Submit with Invalid Credentials (401 Path)

**Use case**: User enters wrong email or password.

**Preconditions**: Backend running; credentials do not match hardcoded admin.

**Steps**:

1. **Form submission** — same as Workflow 1 steps 1–2.

2. **Step 1 — POST /api/auth/login**
   - Backend returns `401 { error: "Invalid credentials" }`
   - axios throws `Error: Request failed with status code 401`

3. **Error propagation**
   - `AuthContext.login` catch: `setState({ error: "Request failed with status code 401", loading: false })`; re-throws
   - `LoginForm.handleSubmit` catch: `this.setState({ error: "Request failed with status code 401" })`

4. **Visual outcome**
   - `POST /api/auth/refresh` is never called
   - Both error `<p>` elements render with "Request failed with status code 401"
   - Button re-enabled

---

### Workflow 3: Submit with Empty Fields (Browser Validation)

**Use case**: User clicks Sign In without filling in one or both fields.

**Preconditions**: `email` or `password` input is empty.

**Steps**:

1. User clicks submit button (or presses Enter)
2. Browser native validation intercepts because inputs have `required` attribute
3. Browser displays native validation tooltip; form submit is cancelled
4. `LoginForm.handleSubmit` is never invoked
5. No HTTP requests are made

**Visual outcome**: Native browser validation popover on the first empty required field. No application error messages rendered.

---

### Workflow 4: Dev-Mode Auth Bypass (skipAuth)

**Use case**: Development environment has `skipAuth = true` configured in the health endpoint.

**Preconditions**: `GET /api/health` returns `{ skipAuth: true }` while `AuthProvider` is mounting.

**Steps**: (This workflow does NOT involve the Sign In button)

1. `AuthProvider.componentDidMount` calls `checkAuthBypass()`
2. `GET /api/health` returns `{ skipAuth: true }`
3. `setState({ user: { email: 'dev@docvault.local', role: 'admin' }, isAuthenticated: true })`
4. `App.render()` mounts the main workspace directly; `<LoginForm />` is never rendered

**Visual outcome**: Login form (and Sign In button) are never visible to the user.

---

## Visual States

### Loading States

| Context | Indicator | Source |
|---|---|---|
| Credentials submitted, request in flight | Button is `disabled`; label changes from "Sign In" to "Signing in..." | `AuthContext.loading === true`; `LoginForm.jsx:112–113` |

### Error States

| Error | Display | Recovery |
|---|---|---|
| Valid credentials (FR-007 crash) | Two red paragraphs: `this.state.error` AND `this.context.error` both show the TypeError message | No user recovery — bug must be fixed in backend |
| Invalid credentials (401) | Two red paragraphs showing "Request failed with status code 401" | User corrects credentials and resubmits |
| Missing fields | Browser native required-field validation popover | User fills in the field |
| Backend unavailable / 500 | Two red paragraphs with "Request failed with status code 500" or "Login failed" | User retries when backend is available |

### Empty States

Not applicable — this is an action component, not a data display component.

### Success States

| Action | Feedback | Next state |
|---|---|---|
| Successful login (blocked by FR-007) | No visible feedback — `<LoginForm />` would unmount and main workspace would mount | Never reached in current code |
| Dev bypass (`skipAuth`) | Login form never shown | Main workspace rendered immediately on app load |

---

## Use Cases

### UC-1: Authenticate to access DocVault

**User story**: As a DocVault user, I want to sign in with my email and password so I can access my documents.

**Workflow**: Workflow 1 (always crashes due to FR-007) or Workflow 4 (dev bypass only)

### UC-2: Receive feedback on wrong credentials

**User story**: As a user, I want to see an error message when I enter the wrong credentials so I know to correct them.

**Workflow**: Workflow 2

### UC-3: Receive feedback on missing fields

**User story**: As a user, I want to be told if I forget to fill in a required field before the form is submitted.

**Workflow**: Workflow 3

---

## Security Considerations

### Authentication

- **Credential store**: Hardcoded in `backend/src/routes/auth.js` (`admin@docvault.local` / `docvault123`). Password is bcrypt-hashed in memory at startup. No database or configurable credential source.
- **Single account**: Only one hardcoded admin account exists. No multi-user support.
- **JWT secrets**: Loaded from `config.jwtSecret` (not visible in source reviewed). Must be an environment variable — confirm it is not hardcoded in `config.js`.

### Token Handling

- **localStorage storage**: Both `docvault_token` and `docvault_refresh_token` are stored in `localStorage`. This exposes tokens to XSS attacks. The Angular/Spring Boot target should use `HttpOnly` cookies instead.
- **Stale tokens on crash**: When FR-007 causes a crash, the access and refresh tokens written in step 1 remain in `localStorage` indefinitely (no cleanup in the crash path). Any future fix must add cleanup on login failure.
- **Token not used**: Because the crash occurs before `isAuthenticated` is set, the stored token is never consumed by application API calls in normal flow.

### Dev Bypass

- **`skipAuth` flag**: If the backend health endpoint returns `skipAuth: true`, the entire authentication flow is bypassed and a hardcoded `dev@docvault.local` admin session is created. This must never be enabled in production. The Angular/Spring Boot target should not implement this pattern, or must guard it with an environment variable that is impossible to set in production.

### CSRF

- This is a client-side React form making XHR (axios) requests. There is no CSRF token mechanism on the legacy frontend. The Spring Boot target must protect `POST /api/auth/login` with appropriate CORS and CSRF configuration (or rely on `SameSite` cookie policy if switching to `HttpOnly` cookies).

### Password Exposure

- Password is sent as plain JSON in the POST body over the configured base URL (`REACT_APP_API_URL`). In production this must be HTTPS. No transport security is enforced client-side.

---

## Accessibility Considerations

- Email and password inputs use only `placeholder` text for labeling — there are no `<label>` elements. Screen readers announce the placeholder, but once the user types, the field label disappears. The Angular target should use visible `<label for="...">` elements or `aria-label` attributes.
- The Submit button has a clear, visible text label ("Sign In" / "Signing in...") — no accessibility issues.
- Error messages are plain `<p>` tags with no `role="alert"` or `aria-live` region. Screen readers may not announce them after dynamic insertion. The Angular target should use `role="alert"` on error containers.
- No focus management on error: after a failed submit, focus remains on the button or the last focused element. The Angular target should move focus to the first error message.
- Inline styles only — no CSS classes — making it impossible to apply high-contrast themes or custom focus outlines via external stylesheets.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
|---|---|---|
| `POST /api/auth/login` (backend) | `{ token, refreshToken }` | 401: credential error shown; 400: field error shown; 500: generic error shown |
| `POST /api/auth/refresh` (backend) | Intended `{ token, refreshToken }`; actual `{ session:{…} }` | Unconditional crash for all valid-credential submissions |
| `GET /api/health` (backend) | `{ skipAuth: boolean }` | If unavailable: silently ignored; login form shown normally |

### Downstream

| System | What this action affects | How |
|---|---|---|
| `AuthContext` provider state | `isAuthenticated`, `user`, `token`, `loading`, `error` | Via `login()` method |
| `App.render()` | Switches from `<LoginForm />` to main workspace | `isAuthenticated = true` (currently unreachable) |
| `localStorage` | `docvault_token`, `docvault_refresh_token` | Written on step 1 success; not cleaned up on crash |

---

## Analysis Notes

1. **FR-007 blocks all authentication**: Every valid-credential login attempt crashes unconditionally at `AuthContext.jsx:75`. The fix is in `backend/src/routes/auth.js` line 61–84: the `/refresh` endpoint must return `{ token: "eyJ...", refreshToken: "eyJ..." }` instead of `{ session: {…} }`. The frontend code itself is correctly written for the JWT flow — no frontend fix is required.

2. **Dual error surfaces**: Because `AuthContext.login` re-throws the caught error, both `AuthContext.error` and `LoginForm.state.error` are set for every failure. The Angular target should use a single error surface to avoid redundant messages. Consider whether the context should expose an error that components also catch locally.

3. **localStorage vs HttpOnly cookies**: The legacy code uses `localStorage` for JWT storage. This is an XSS vulnerability. The Spring Boot target should issue tokens as `HttpOnly; Secure; SameSite=Strict` cookies, removing `localStorage` token handling from the Angular client entirely.

4. **Stale tokens on crash path**: After a FR-007 crash, `docvault_token` and `docvault_refresh_token` sit in `localStorage` with no associated authenticated session. On a future fix, the login code should clean up stale tokens before writing new ones (or at minimum on any catch path).

5. **No token refresh cycle**: The `POST /api/auth/refresh` call in step 2 is intended to immediately replace the 1-hour `token` with a fresh one. This pattern is unusual — normally refresh is called when a token nears expiry, not immediately after login. The Spring Boot target should clarify whether step 2 is needed at all immediately post-login, or whether a single long-lived token (or automatic refresh on 401) suffices.

6. **Class component / FR-016**: `LoginForm` is a class component, not migrated to functional React (noted as FR-016). The Angular target does not need to preserve this implementation detail, but it is useful context for understanding the `static contextType` pattern.

7. **Single hardcoded admin credential**: The backend has no database and no user management. The Spring Boot target must implement a real credential store (database-backed `UserDetailsService` or similar). The `admin@docvault.local` / `docvault123` values are for reference only.

8. **Dev bypass security**: The `skipAuth` bypass via `GET /api/health` creates an unauthenticated admin session in development. This must not be replicated in the Spring Boot target without an explicit environment guard (`if (env == "development")` only, and ideally removed entirely in favour of a dedicated test user).

9. **No "Remember Me" or session persistence**: The login form has no "Remember Me" option. On page refresh, `AuthContext` re-initialises with `isAuthenticated: false` regardless of existing localStorage tokens. The legacy app does not implement token restoration on load — the Angular target may wish to add this.
