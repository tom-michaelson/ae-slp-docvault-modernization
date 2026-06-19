# Functional Description: Login Credentials Form

> **Entry Point**: `login-form`
> **Location**: `frontend/src/components/LoginForm.jsx:95-115`
> **Type**: UI / Form
> **Domain**: auth
> **Legacy URL**: `/` (SPA root — `App.jsx` renders `<LoginForm />` when `AuthContext.isAuthenticated === false`)

---

## Executive Summary

The Login Credentials Form is the sole interactive entry point into DocVault. It renders as a centred white card on a dark (`#1a1a2e`) full-viewport background and presents two controlled inputs (Email and Password) plus a Sign In submit button. There is no dedicated `/login` route; `App.jsx` conditionally mounts this component when `AuthContext.isAuthenticated` is `false` and unmounts it when authentication succeeds.

On submission, the form delegates entirely to `AuthContext.login(email, password)`. That method orchestrates a mandatory two-step JWT flow: first `POST /api/auth/login` (which works correctly and returns `{ token, refreshToken }`), then immediately `POST /api/auth/refresh` (which is broken — bug FR-007 — because the backend returns `{ session: {...} }` instead of `{ token, refreshToken }`). The attempt to call `.split('.')` on the undefined `token` property crashes `AuthContext.login` unconditionally. The component's `catch` block captures the thrown error and writes it to local component state; separately, `AuthContext` itself sets its own `context.error` before re-throwing. Both error states render as independent `<p>` elements below the form, so in the FR-007 crash scenario two error paragraphs appear simultaneously.

There is no client-side field validation beyond the HTML5 `required` attribute on both inputs. There is no route-level authentication guard, no remember-me option, and no password reset link. Auth state lives exclusively in React context (`AuthContext`) — no Redux store is involved.

---

## User Inputs

### Form Fields

| Field Name | JS Type | Source | Required | Notes |
| --- | --- | --- | --- | --- |
| `email` | `string` | `this.state.email` (React controlled input) | yes — HTML5 `required` | `type="email"` — browser enforces email format. No custom regex or min-length rule. `onChange` calls `this.setState({ email: e.target.value })`. |
| `password` | `string` | `this.state.password` (React controlled input) | yes — HTML5 `required` | `type="password"` — value masked. No min-length constraint. `onChange` calls `this.setState({ password: e.target.value })`. |

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
| --- | --- | --- | --- |
| Submit login credentials | `<button type="submit" disabled={loading}>` — label "Sign In" (idle) or "Signing in…" (in-flight) | `LoginForm.handleSubmit` (bound to `<form onSubmit>` at line 95) | Click button or press Enter in any field |
| Update email field | `<input type="email">` onChange at line 99 | `this.setState({ email })` | Keystroke |
| Update password field | `<input type="password">` onChange at line 105 | `this.setState({ password })` | Keystroke |

### URL / Route Parameters

No URL or route parameters. The form renders at the SPA root (`/`) without a dedicated route segment. No query-string inputs are consumed by this form.

### Browser / Session Inputs

| Source | Data | Purpose |
| --- | --- | --- |
| `AuthContext.isAuthenticated` (React context) | `boolean` | `App.jsx` mounts `<LoginForm />` only when `false`; the form never reads this directly |
| `AuthContext.loading` (React context) | `boolean` | Disables the submit button and toggles the button label while a login request is in flight |
| `AuthContext.error` (React context) | `string \| null` | Displayed in a second error paragraph below the form (set by `AuthContext` catch block) |
| `localStorage['docvault_token']` | JWT string | Not read by `LoginForm` itself; written by `AuthContext.login` during the (unreachable) success path |

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
| --- | --- | --- | --- |
| Dark full-viewport wrapper | `<div>` with `height: 100vh; backgroundColor: #1a1a2e` | Always | `LoginForm.jsx:92` |
| White card container | `<div>` `width: 360px`, `borderRadius: 8px`, `padding: 32px`, drop shadow | Always | `LoginForm.jsx:93` |
| Heading | `<h1>📄 DocVault Login</h1>` | Always | `LoginForm.jsx:94` |
| `<form>` element | `onSubmit={this.handleSubmit}` wrapping both inputs and the button | Always | `LoginForm.jsx:95` |
| Email input | `<input type="email" value={email} placeholder="Email" required>` | Always | `LoginForm.jsx:96-103` |
| Password input | `<input type="password" value={password} placeholder="Password" required>` | Always | `LoginForm.jsx:104-111` |
| Submit button | `<button type="submit" disabled={loading}>` — "Sign In" or "Signing in…" | Always | `LoginForm.jsx:112-114` |
| Local error paragraph | `<p style={errorStyle}>{error}</p>` — red (#c62828), 13px, centred | `this.state.error` is non-null | `LoginForm.jsx:116` |
| Context error paragraph | `<p style={errorStyle}>{this.context.error}</p>` | `this.context.error` is non-null | `LoginForm.jsx:117-119` |

### Navigation / Routing

| Trigger | Destination | Condition |
| --- | --- | --- |
| Successful login (success path — currently unreachable due to FR-007) | Main application shell (`App.jsx` unmounts `<LoginForm />` and renders `Header`, `Sidebar`, `DocumentGrid`, `SearchBar`, `PreviewPanel`) | `AuthContext.isAuthenticated` becomes `true` |
| Auth bypass via `/api/health` `skipAuth: true` flag | Main application shell (same as above, but set in `AuthContext.componentDidMount`) | Out of scope for this form — belongs to `login` page feature |

### State Changes

| State | Change | Trigger | Notes |
| --- | --- | --- | --- |
| `this.state.error` | Set to `err.message` (or fallback string) | `handleSubmit` catch block | Local to `LoginForm` component; displayed in local error `<p>` |
| `this.state.email` | Updated on each keystroke | Email `onChange` | Controlled input; cleared only by user action |
| `this.state.password` | Updated on each keystroke | Password `onChange` | Controlled input; cleared only by user action |
| `AuthContext.loading` | `true` → set on login start; `false` → set in catch block | `AuthContext.login` start / catch | Disables button; toggles label |
| `AuthContext.error` | Set to `err.message` in catch block | `AuthContext.login` catch block | Displayed in context error `<p>`; persists until next login attempt resets it to `null` |
| `AuthContext.isAuthenticated` | Remains `false` (FR-007 crash prevents success path) | `AuthContext.login` catch | Would become `true` on success — currently unreachable |
| `localStorage['docvault_token']` | Written with JWT access token | `AuthContext.login` line 63 — after successful `/login` response | Written before the crash; still present in storage after failure |
| `localStorage['docvault_refresh_token']` | Written with refresh token | `AuthContext.login` line 64 — after successful `/login` response | Written before the crash; still present in storage after failure |

---

## API Dependencies

### Service Calls

| Service Method | When Called | Data In | Data Out |
| --- | --- | --- | --- |
| `AuthContext.login(email, password)` | `handleSubmit` — after `e.preventDefault()` | `email: string`, `password: string` from component state | (void on success — sets context state) / throws on error |
| `axios.post /api/auth/login` | Inside `AuthContext.login` (line 55) | `{ email, password }` | `{ token: string, refreshToken: string }` on HTTP 200 |
| `axios.post /api/auth/refresh` | Inside `AuthContext.login` (line 68) — immediately after `/login` success | `{ refreshToken }` | BUG: returns `{ session: { userId, email, createdAt } }` — crashes client |

### Call Sequences

**handleSubmit (form submission):**
1. `e.preventDefault()` — suppress native browser navigation.
2. Destructure `{ email, password }` from `this.state`.
3. `await this.context.login(email, password)` — enter `AuthContext.login`.
4. **On success** (currently unreachable): `App.jsx` re-renders; `<LoginForm />` is unmounted; main application shell is mounted.
5. **On error** (always, due to FR-007): catch block sets `this.setState({ error: err.message || 'Login failed. The app has crashed — check the console.' })`.

**AuthContext.login (called from handleSubmit):**
1. `this.setState({ loading: true, error: null })` — disables button, clears previous context error.
2. `POST /api/auth/login` with `{ email, password }`:
   - HTTP 200: destructures `{ token, refreshToken }`, writes both to `localStorage`.
   - HTTP 400: missing fields — throws axios error (rare; HTML5 `required` prevents empty submission from reaching the server).
   - HTTP 401: `{ error: 'Invalid credentials' }` — axios throws; caught at step 6.
   - HTTP 500: server error — axios throws; caught at step 6.
3. `POST /api/auth/refresh` with `{ refreshToken }`:
   - Backend correctly verifies the refresh token but **returns `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }`** (FR-007 — copy-paste error in `auth.js:78`).
4. **Crash**: `refreshResponse.data.token.split('.')` — `refreshResponse.data.token` is `undefined` → `TypeError: Cannot read properties of undefined (reading 'split')`.
5. (Unreachable success path): would decode JWT payload, set `user`, `token`, `isAuthenticated: true`, `loading: false` in context state, and overwrite `localStorage['docvault_token']` with the refreshed token.
6. **Catch block** (`AuthContext.jsx:86`): sets `context.error = err.message`, `loading = false`, `isAuthenticated = false`, then **re-throws** to `handleSubmit`.

**Backend: POST /api/auth/login (`auth.js:17`):**
1. Validates `email` and `password` present — 400 if missing.
2. `bcrypt.compareSync(password, ADMIN_PASSWORD_HASH)` — compares against hardcoded hash of `'docvault123'`.
3. If `email !== 'admin@docvault.local'` or password mismatch → 401 `{ error: 'Invalid credentials' }`.
4. `jwt.sign({ userId: 'abc-123', email, role: 'admin' }, jwtSecret, { expiresIn: '1h' })` → access token.
5. `jwt.sign({ userId: 'abc-123', email, type: 'refresh' }, jwtSecret, { expiresIn: '7d' })` → refresh token.
6. Returns `{ token, refreshToken }` — HTTP 200.

**Backend: POST /api/auth/refresh (`auth.js:61`) — BUG:**
1. Validates `refreshToken` present — 400 if missing.
2. `jwt.verify(refreshToken, jwtSecret)` → decodes payload; throws on invalid/expired token (401).
3. Returns **`{ session: { userId, email, createdAt } }`** — this is the copy-paste bug. Should return `{ token, refreshToken }`.

---

## State Management

### Component State Fields

| Property | Type | Initial Value | Used In | Notes |
| --- | --- | --- | --- | --- |
| `this.state.email` | `string` | `''` | Email input `value`; `handleSubmit` reads it | Controlled input value |
| `this.state.password` | `string` | `''` | Password input `value`; `handleSubmit` reads it | Controlled input value |
| `this.state.error` | `string \| null` | `null` | Local error `<p>` conditional render | Set in `handleSubmit` catch; never cleared automatically (persists until next submit) |

### Context State (AuthContext)

| Property | Type | Read by LoginForm | Written by | Notes |
| --- | --- | --- | --- | --- |
| `loading` | `boolean` | Yes — disables submit button; toggles label | `AuthContext.login` (start/catch) | `true` while in-flight; `false` on error |
| `error` | `string \| null` | Yes — rendered in context error `<p>` | `AuthContext.login` catch block | Reset to `null` at start of each login attempt |
| `isAuthenticated` | `boolean` | Indirectly — `App.jsx` uses it to unmount form | `AuthContext.login` catch / success | Always `false` while FR-007 persists |
| `user` | `object \| null` | No | `AuthContext.login` success path (unreachable) | Would hold decoded JWT payload |
| `token` | `string \| null` | No | `AuthContext.login` success path (unreachable) | Would hold refreshed access token |

### localStorage

| Key | Written when | Value | Notes |
| --- | --- | --- | --- |
| `docvault_token` | After successful `POST /api/auth/login` (line 63), and would be overwritten on success path (line 85) | JWT access token string | Written before the FR-007 crash — so it IS present in storage after a failed login attempt |
| `docvault_refresh_token` | After successful `POST /api/auth/login` (line 64) | JWT refresh token string | Same — written before crash |

---

## Component Details

### Component: `LoginForm`

**File**: `frontend/src/components/LoginForm.jsx`

**Type**: React class component (`extends Component`) — not migrated to functional component (FR-016).

**Context**: `static contextType = AuthContext` — consumes `loading`, `error`, `isAuthenticated`, `login` from `AuthProvider`.

**State**: `{ email: '', password: '', error: null }`

**Methods**:
- `handleSubmit = async (e)` (line 72) — `onSubmit` handler; calls `AuthContext.login`; catches and stores errors locally.
- `render()` (line 87) — renders the full-viewport container, card, heading, form, inputs, button, and conditional error paragraphs.

**Inline styles**: All styling is via JavaScript style objects (`formStyle`, `cardStyle`, `titleStyle`, `inputStyle`, `buttonStyle`, `errorStyle`) — no external CSS file or CSS modules. Relevant values:
- Background: `#1a1a2e` (dark navy)
- Card width: 360px with 32px padding
- Button background: `#0f3460`
- Error text colour: `#c62828` (red), 13px, centred

### Context Provider: `AuthProvider`

**File**: `frontend/src/context/AuthContext.jsx`

**Type**: React class component providing `AuthContext`.

**State**: `{ user, token, loading, error, isAuthenticated }`

**Methods exposed via context**:
- `login(email, password)` (line 50) — orchestrates the two-step JWT flow.
- `logout()` (line 96) — clears user/token state and removes `localStorage` keys.

**componentDidMount**: calls `checkAuthBypass()` — out of scope for this form feature.

**Axios base URL**: `process.env.REACT_APP_API_URL || 'http://localhost:3001/api'`

### Backend Handler: `router.post('/login')` and `router.post('/refresh')`

**File**: `backend/src/routes/auth.js`

**Runtime**: Node.js / Express.

**Credentials**: Hardcoded `ADMIN_EMAIL = 'admin@docvault.local'` and `ADMIN_PASSWORD_HASH = bcrypt.hashSync('docvault123', 10)`. No database access.

**JWT config**: Secret from `config.jwtSecret`; access token expiry 1h; refresh token expiry 7d.

---

## Workflows

### Workflow 1: Submit Login Credentials (handleSubmit)

**Use case**: User provides email and password and clicks "Sign In" to authenticate.

**Preconditions**: `App.jsx` is rendering `<LoginForm />` because `AuthContext.isAuthenticated === false`.

**Steps**:

1. **Native validation gate**
   - Browser enforces `required` on both inputs before `onSubmit` fires.
   - If either field is empty, the browser shows its native validation message; `handleSubmit` is not called; no HTTP request is made.

2. **Suppress default and read fields**
   - `e.preventDefault()` prevents the browser from navigating.
   - `const { email, password } = this.state` — reads current controlled-input values.

3. **Delegate to `AuthContext.login`**
   - `await this.context.login(email, password)` (see Workflow 2 below for the full call sequence inside `AuthContext.login`).

4. **On throw (always due to FR-007)**
   - Catches `err` from `AuthContext.login`.
   - `this.setState({ error: err.message || 'Login failed. The app has crashed — check the console.' })`.
   - Local error `<p>` below the form becomes visible.
   - If `AuthContext.error` was also set (it always is), the context error `<p>` also becomes visible.
   - Submit button becomes re-enabled (`context.loading` is `false` after catch).

5. **On success (unreachable while FR-007 unfixed)**
   - `AuthContext` sets `isAuthenticated: true`.
   - `App.jsx` re-evaluates and unmounts `<LoginForm />`; mounts main application shell.
   - No redirect — the SPA conditionally renders components based on context state.

**Success outcome** (post-fix): User is authenticated; login form disappears; application workspace appears.

**Failure outcome** (current): One or two error paragraphs visible below the form; button re-enabled; user can retry.

---

### Workflow 2: AuthContext.login Execution

**Use case**: Underlying two-step JWT authentication called by `handleSubmit`.

**Preconditions**: `handleSubmit` called `AuthContext.login(email, password)` with non-empty strings.

**Steps**:

1. **Reset and disable**
   - `this.setState({ loading: true, error: null })` — disables submit button, clears prior context error.

2. **POST /api/auth/login**
   - Sends `{ email, password }` to `${API_BASE_URL}/auth/login`.
   - **HTTP 200**: response body `{ token, refreshToken }`:
     - `localStorage.setItem('docvault_token', token)` (line 63).
     - `localStorage.setItem('docvault_refresh_token', refreshToken)` (line 64).
   - **HTTP 401**: axios throws with response error; skip to step 5.
   - **HTTP 400/500**: axios throws; skip to step 5.

3. **POST /api/auth/refresh** *(bug — always crashes)*
   - Sends `{ refreshToken }` (just obtained) to `${API_BASE_URL}/auth/refresh`.
   - Backend verifies the token (valid), then returns `{ session: { userId, email, createdAt } }`.

4. **Crash**
   - `const parts = refreshResponse.data.token.split('.')` — `refreshResponse.data.token` is `undefined`.
   - `TypeError: Cannot read properties of undefined (reading 'split')` is thrown.

5. **Catch block**
   - `this.setState({ error: err.message, loading: false, isAuthenticated: false })`.
   - `throw err` — re-throws to `handleSubmit`'s catch block.

**Outcome**: Always ends in an error throw while FR-007 is present. The `localStorage` keys are populated with valid tokens up to the moment of crash.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
| --- | --- | --- |
| Login request in flight | Submit button disabled; label changes from "Sign In" to "Signing in…" | Driven by `this.context.loading === true`; no spinner, no overlay |

### Error States

| Error | Display | Recovery |
| --- | --- | --- |
| Invalid credentials (HTTP 401) | Context error `<p>` — "Invalid credentials" (from `/login` response) | User corrects fields and resubmits |
| FR-007 crash (TypeError on `/refresh`) | Both error paragraphs visible: context error `<p>` ("Cannot read properties of undefined (reading 'split')") AND local error `<p>` (same message, from `handleSubmit` catch) | No recovery path — application remains on login screen until the backend bug is fixed |
| Network failure | Context error `<p>` with axios network error message; local error `<p>` with same | User can retry |
| HTML5 required-field violation | Browser native validation bubble | User fills the field; no HTTP call made |

### Empty States

No empty state — the form always renders when the user is unauthenticated.

### Success States

| Action | Feedback | Next state |
| --- | --- | --- |
| Successful authentication (post-fix) | Instant unmount of `<LoginForm />`; application workspace renders | Main application shell visible |

---

## Use Cases

### UC-1: Authenticate with valid credentials

**User story**: As the DocVault administrator, I want to sign in with my email and password so I can access my documents.

**Workflow**: Workflow 1 → Workflow 2 (Steps 1–3 succeed, Step 4 crashes due to FR-007 until fixed).

### UC-2: Receive feedback on invalid credentials

**User story**: As a user, I want to be told when my credentials are wrong so I can correct them and try again.

**Workflow**: Workflow 2 Step 2 returns HTTP 401 → context error `<p>` shows "Invalid credentials" → button re-enabled.

### UC-3: Understand that the submit button prevents double-submission

**User story**: As a user, I should not be able to click "Sign In" twice while a login request is in flight.

**Workflow**: Workflow 2 Step 1 sets `loading = true` → button is `disabled` → button re-enables only when `loading = false` (set in catch or success path).

### UC-4: Observe dual error paragraphs on crash

**User story** (for QA/BA): As a tester, when the /refresh call crashes, both error paragraphs appear simultaneously — the context error and the local error — both showing the same TypeError message.

**Workflow**: Workflow 2 Step 4 and 5 → both `context.error` and `this.state.error` set to the same message.

---

## Security Considerations

### Authentication

- **No client-side authentication gate on the form itself.** `App.jsx` controls visibility; the form has no `[Authorize]` equivalent.
- **No CSRF protection.** The form is a React SPA submitting JSON via `axios` — no anti-forgery token. The Angular target must implement CSRF protection if the Spring Boot API requires it (standard CORS + `SameSite=Lax` cookie strategy or CSRF header).

### Credential Transmission

- Credentials are submitted as JSON (`Content-Type: application/json`) over whatever protocol the `API_BASE_URL` uses. In production, this must be HTTPS.
- The backend validates against a hardcoded bcrypt hash — no database read. The Angular/Spring Boot target must replace this with a proper user store.

### Token Storage

- **Critical**: Both `docvault_token` and `docvault_refresh_token` are stored in `localStorage`. This is vulnerable to XSS. The Angular target should evaluate using `HttpOnly` cookies instead.
- After an FR-007 crash, valid tokens are left in `localStorage` from the successful `/login` call even though authentication did not complete. A stale `docvault_token` may confuse a future `checkAuthBypass` or token-restoration flow. The Java target should only write tokens to storage on full authentication success.

### Input Validation

- **Only HTML5 `required` on both fields.** No email-format enforcement beyond `type="email"` (browser-dependent). No password complexity rule. The Angular target should add explicit `Validators.email` and `Validators.minLength` or equivalent.

### Hardcoded Credentials

- Backend hardcodes `admin@docvault.local` / `docvault123`. The Spring Boot target must use a configurable user store and never hardcode credentials.

---

## Accessibility Considerations

- Neither the email nor password `<input>` has a `<label>` element or `aria-label`. Screen readers must rely solely on the `placeholder` attribute ("Email", "Password"), which disappears when the field is filled. The Angular target should add proper `<label for>` associations.
- The submit button text "Sign In" / "Signing in…" is descriptive — acceptable for screen readers.
- No `aria-live` region for the error paragraphs. Users with screen readers will not be automatically notified when an error appears after submission. The Angular target should add `role="alert"` or `aria-live="polite"` to the error display.
- Input `type="email"` and `type="password"` trigger appropriate mobile keyboards and browser autofill heuristics — this should be preserved in the Angular target.
- No `autocomplete` attributes — browsers may still infer `autocomplete="email"` and `autocomplete="current-password"` from the input types. The Angular target should set these explicitly.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
| --- | --- | --- |
| `POST /api/auth/login` | `{ token, refreshToken }` on 200; `{ error }` on 400/401/500 | Error displayed in context error `<p>`; button re-enabled |
| `POST /api/auth/refresh` | (BUG) `{ session: { userId, email, createdAt } }` instead of `{ token, refreshToken }` | TypeError crash; both error paragraphs shown; login never completes |
| `AuthContext` (React context) | `loading`, `error`, `isAuthenticated` | Form button state and error display depend entirely on context values |

### Downstream

| System | What this feature affects | How |
| --- | --- | --- |
| `AuthContext.isAuthenticated` | Triggers `App.jsx` to unmount `<LoginForm />` and mount main workspace | React context state change → conditional render in `App.jsx` |
| `localStorage['docvault_token']` | Downstream API calls use this token as `Authorization: Bearer` header | Written by `AuthContext.login` after successful `/login` |
| `localStorage['docvault_refresh_token']` | Would be used for token refresh on API 401s (if token refresh logic existed elsewhere) | Written by `AuthContext.login` after successful `/login` |

---

## Analysis Notes

1. **FR-007 — the login always crashes.** `POST /api/auth/login` succeeds; `POST /api/auth/refresh` is called immediately and returns `{ session: {...} }` instead of `{ token, refreshToken }`. `AuthContext.jsx:75` calls `.split('.')` on the undefined `token` property, crashing unconditionally. Fix: in the Angular target, do **not** call `/refresh` immediately after `/login`. Store the token from the `/login` response directly; call `/refresh` only when the access token is near expiry.

2. **Dual error-paragraph behaviour is a design flaw.** `AuthContext.login` sets `context.error` and re-throws; `handleSubmit` catches and sets `this.state.error`. Both render independently. The Angular target should use a single unified error display strategy (e.g., one `<mat-error>` or one alert component driven by a single error observable).

3. **Stale tokens in localStorage after crash.** Because `localStorage.setItem('docvault_token', token)` (line 63) and `localStorage.setItem('docvault_refresh_token', refreshToken)` (line 64) execute before the crash at line 75, valid tokens are written to storage even though `isAuthenticated` remains `false`. Any subsequent page load that reads from `localStorage` without proper validation will find these tokens. The Angular target must not consider `localStorage` token presence as proof of authentication — always validate with a `/me` or equivalent endpoint on startup.

4. **No PRG (Post-Redirect-Get) pattern.** The SPA avoids this problem by design — there is no browser-navigable form URL, so back-button replay of a POST is not possible.

5. **No form `name` or `id` attributes on inputs.** Browser password managers may have difficulty autofilling these fields. The Angular target should add `id="email"` / `id="password"` and corresponding `<label for>` attributes.

6. **`checkAuthBypass` is out of scope but contextually relevant.** `AuthProvider.componentDidMount` calls `GET /api/health`; if the response includes `skipAuth: true`, the app sets `isAuthenticated = true` without any user interaction. This means the login form may never appear in development. The Java/Angular target should implement a similar dev-only bypass only via environment configuration, never in production code.

7. **Class component — not migrated to functional (FR-016).** `LoginForm` uses `static contextType`, class-based state, and arrow-function class fields. The Angular target is a completely different framework so this is not a migration concern — but it is a signal that the legacy codebase has not been actively maintained.

8. **Only one hardcoded admin user.** The backend's `/login` route validates against a single hardcoded `ADMIN_EMAIL`/`ADMIN_PASSWORD_HASH` pair with no database. The Spring Boot target must design a real user store (at minimum a users table with bcrypt-hashed passwords) and a configurable initial admin account via environment variables or a migration seed.

