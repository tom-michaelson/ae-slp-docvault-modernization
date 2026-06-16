# Runtime Verification: POST /api/auth/refresh — Session Object Bug

## Endpoint

`POST /api/auth/refresh`

## Test Environment

- Backend started with `DEV_SKIP_AUTH=true` and `DATABASE_URL` pointing to localhost PostgreSQL (not running for DB tests, but the auth routes do not require PostgreSQL)
- Node.js backend running on port 3001
- Tested via PowerShell `Invoke-WebRequest`

## Test 1 — Valid Login Flow (Baseline)

**Request:**
```
POST http://localhost:3001/api/auth/login
Content-Type: application/json
{ "email": "admin@docvault.local", "password": "docvault123" }
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Assessment:** Login works correctly. Response shape matches what `AuthContext` expects. ✓

## Test 2 — Token Refresh (Bug Confirmation)

**Request:**
```
POST http://localhost:3001/api/auth/refresh
Content-Type: application/json
{ "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." }
```

**Response (200):**
```json
{
  "session": {
    "userId": "abc-123",
    "email": "admin@docvault.local",
    "createdAt": "2026-05-27T19:16:12.342Z"
  }
}
```

**Assessment:** **BUG CONFIRMED AT RUNTIME.** The refresh endpoint returns a 200 with a `session` object instead of `{ token, refreshToken }`. The `token` field is absent. `AuthContext.login()` executes `refreshResponse.data.token.split('.')` which throws `TypeError: Cannot read properties of undefined (reading 'split')`. The login flow crashes for every user. ✗

## Test 3 — Missing Refresh Token

**Request:**
```
POST http://localhost:3001/api/auth/refresh
Content-Type: application/json
{}
```

**Response (400):**
```json
{ "error": "Refresh token required" }
```

**Assessment:** Input validation for missing token works correctly. ✓

## Findings

The static analysis finding is confirmed at runtime. `POST /api/auth/refresh` returns a session-shaped response. The application is completely unusable via the JWT login path without the `DEV_SKIP_AUTH` bypass.

## Reference

`analysis/bug/auth_refresh_returns_session_object.md`
