# Knowledge Gap: Auth Middleware Precedence and req.user Contract

## Description

Three authentication middlewares run on every `/api` request. Their interaction order, the conditions under which each sets state on `req`, and the shape of the user object each produces are not documented anywhere. A developer modifying any auth-related code must reverse-engineer the coordination logic from three separate files and the enforcement check in `index.js`.

Specific unknown behaviors for a new developer:

1. **What happens when JWT and session auth are both satisfied simultaneously?** JWT sets `req.auth = { userId, email, role }`; session sets `req.user = { userId, email }` (no `role`). The authorization enforcer accepts either. Code that reads `req.user?.role` works in JWT-authenticated sessions but silently gets `undefined` in session-authenticated requests.

2. **What is the actual middleware execution order?** `apiKeyAuth` → `jwtAuth` → `jwtErrorHandler` → `sessionAuth` → auth enforcer. But `apiKeyAuth` short-circuits with 401 on any API key, meaning JWT and session auth never run if `X-API-Key` is present.

3. **What does "no auth method succeeded" mean in practice?** If JWT token is missing (no `Authorization` header), `req.auth` is not set. If no session exists, `req.user` is not set. The enforcer then checks `req.session?.user` as a third fallback — but this is the same as `req.user` since `sessionAuth` already copies it. The triple-check is redundant.

4. **What is the contract for `req.skipAuth`?** The `DEV_SKIP_AUTH` bypass sets `req.user = { email, role: 'admin' }` and `req.auth = { email, role: 'admin' }` and `req.skipAuth = true`. Routes that check only `req.auth` will work; routes that check `req.user` will work; but the `role: 'admin'` is hardcoded and differs from the shape produced by a real JWT (`userId` included) vs session auth (`userId` included, no `role`).

## Area Affected

- **Module / Component**: `backend/src/index.js`, `backend/src/middleware/`
- **Domain**: Security, Infrastructure

## Impact

- A developer adding authorization to a new route does not know which of `req.auth`, `req.user`, or `req.session.user` to check — or which one contains the `role` field needed for admin checks.
- The DEV_SKIP_AUTH bypass hardcodes `role: 'admin'` but no route currently uses `req.auth.role` for access control. If role-based access control is added, the bypass shape may not match the real JWT shape.
- Bugs in this layer are invisible in the default development setup because `DEV_SKIP_AUTH=true` bypasses all three middleware.

## Recommended Actions

1. Write a single ADR (Architecture Decision Record) documenting which auth mechanism is authoritative and what properties are guaranteed on `req.user` after auth middleware runs.
2. Add a `req.currentUser` normalization middleware that runs after all three auth systems and produces a consistent `{ userId, email, role }` object regardless of which auth method succeeded.
3. Document the `DEV_SKIP_AUTH` flag in the README with an explicit warning that it must never be set to `true` in production.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- See `analysis/anti_pattern/fractured_authentication.md` for the design-level issue.
- The undefined `role` behavior in session-authenticated requests could become a security vulnerability if role-based access control is added without normalizing `req.user`.
