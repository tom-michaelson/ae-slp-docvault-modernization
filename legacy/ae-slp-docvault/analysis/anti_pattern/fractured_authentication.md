# Anti-Pattern: Fractured Authentication

## Description

Three independent authentication systems coexist in the same request pipeline: JWT middleware (`jwtAuth.js`), session-based auth (`sessionAuth.js`), and API key auth (`apiKeyAuth.js`). Each checks a different header, sets a different property on `req`, and fails in a different way. None of them are aware of the others. The result is a request pipeline where the concept of "is this user authenticated?" has no single authoritative answer, and the authorization enforcement check (`req.auth || req.user || req.session?.user`) must OR across all three possible states.

This is an anti-pattern because:
- It creates invisible coupling between systems that appear independent.
- It makes security reasoning impossible: there is no single place to verify that an unauthenticated request will be rejected.
- The API key system silently breaks all API key clients (always returns 401), which is a live bug that is invisible without understanding all three layers.
- The session system was supposed to be phased out but has been left running globally.
- The fractured state means `req.user` can be set by session auth while `req.auth` is set by JWT — these represent different shapes of the user object and are treated interchangeably.

## Category

Security, Architecture

## Occurrences

| File | Line | Code Snippet | Description |
|------|------|--------------|-------------|
| `backend/src/index.js` | 47 | `app.use('/api', apiKeyAuth);` | API key middleware applied first on all /api routes |
| `backend/src/index.js` | 50 | `app.use('/api', jwtAuth);` | JWT middleware applied second on all /api routes |
| `backend/src/index.js` | 53 | `app.use(sessionAuth);` | Session middleware applied globally (not scoped to /api) |
| `backend/src/index.js` | 62–73 | `if (req.auth \|\| req.user \|\| ...)` | Authorization enforcer ORs across all three systems |
| `backend/src/middleware/apiKeyAuth.js` | 19 | `return res.status(401)...` | Any API key always fails — stub never completed |
| `backend/src/middleware/jwtAuth.js` | 10 | `credentialsRequired: false` | JWT middleware passes through even when token is invalid |
| `backend/src/middleware/sessionAuth.js` | 11 | `req.user = req.session.user` | Session auth sets `req.user`, JWT sets `req.auth` — different shapes |

## Impact

- **Security**: An attacker who knows the API key header exists may probe the stub and discover the entire API is reachable without a valid key if JWT or session auth is also satisfied.
- **Reliability**: The `POST /api/auth/refresh` bug (returning session shape instead of JWT) is a direct symptom of this pattern — the refresh endpoint accidentally delegates to session logic because session and JWT systems are both active and not clearly delineated.
- **Maintainability**: A developer adding a new route cannot determine which auth mechanism protects it by reading the route file alone.
- **Onboarding**: New team members must understand all three systems to safely modify any auth-related code.

## Recommended Resolution

1. Choose one authentication mechanism — JWT is the stated primary.
2. Remove `sessionAuth.js` middleware and its routes (`/api/auth/session/login`).
3. Remove `apiKeyAuth.js` until API key support is fully designed and implemented.
4. Replace the multi-OR authorization check with a single `requireAuth` middleware that validates only JWT.
5. Ensure `credentialsRequired: true` on the JWT middleware so unauthenticated requests are rejected at the middleware layer, not in a per-route check.

## Verification Method

Static Analysis

## Date Analyzed

2026-05-27

## Notes or Next Steps

- The README describes all three systems as "coexisting" and "the middleware stack figures out which one is active" — this should be corrected; no such coordination logic exists.
- See `analysis/bug/api_key_auth_always_rejects.md` for the runtime consequence of the API key stub.
- See `analysis/bug/auth_refresh_returns_session_object.md` for the crash caused by session/JWT confusion.
