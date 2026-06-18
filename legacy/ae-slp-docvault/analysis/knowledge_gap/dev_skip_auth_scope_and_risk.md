# Knowledge Gap: DEV_SKIP_AUTH Scope and Risk

## Description

`DEV_SKIP_AUTH=true` is committed in `backend/.env`. When this flag is set, a middleware in `index.js` injects a hardcoded admin user object into every request (`req.user`, `req.auth`, and `req.skipAuth = true`), bypassing all authentication checks.

What is not documented anywhere:
1. **Scope**: Does `DEV_SKIP_AUTH` bypass only the auth enforcer, or does it also bypass individual route-level auth checks? Currently it bypasses the enforcer in `index.js` — but no route has its own `requireAuth` check, so all routes are bypassed.
2. **Side effects on auth testing**: Because `DEV_SKIP_AUTH=true` is the committed default, a developer running the app without overriding it will never exercise the JWT login flow. The auth crash bug (null reference on token refresh) would only be discovered by a developer who explicitly sets `DEV_SKIP_AUTH=false`.
3. **Production risk surface**: The flag is checked via `process.env.DEV_SKIP_AUTH === 'true'`. If this environment variable is set in any production environment (accidentally or intentionally), the entire API is unauthenticated. There is no safeguard that prevents this value in `NODE_ENV=production`.
4. **The injected user shape**: The bypass injects `{ email: 'dev@docvault.local', role: 'admin' }` but does not include `userId`. JWT-decoded tokens include `userId`. Code that reads `req.auth.userId` or `req.user.userId` will get `undefined` in bypass mode but a value in real auth mode — a hidden behavioral difference between development and production.

## Area Affected

- **Module / Component**: `backend/src/index.js` (line 34–41), `backend/.env`
- **Domain**: Security, Infrastructure

## Impact

- The committed `DEV_SKIP_AUTH=true` means every developer who clones the repo and starts the backend without creating their own `.env.local` override runs in unauthenticated mode without knowing it.
- The `AuthContext.checkAuthBypass()` in the frontend calls `/api/health` and auto-authenticates if `skipAuth: true` is returned — meaning the frontend also detects and adapts to this bypass. This is a significant undocumented coupling between frontend and backend configuration.
- Any future code that depends on `req.user.userId` will work in production (JWT auth) but silently get `undefined` in development (bypass mode), making bugs reproducible only in production.

## Recommended Actions

1. Remove `DEV_SKIP_AUTH=true` from the committed `backend/.env`. Set it only in developers' local `.env.local` files (which are gitignored).
2. Add a startup guard: if `DEV_SKIP_AUTH === 'true'` and `NODE_ENV === 'production'`, throw a startup error.
3. Add `userId: 'dev-user-id'` to the injected bypass user object so the shape matches real JWT output.
4. Document the flag in `README.md` with an explicit warning about its scope and production risk.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- The `AuthContext.checkAuthBypass()` call to `/api/health` that detects and accepts `skipAuth: true` is also undocumented behavior — a developer reading `AuthContext.jsx` would not expect the health endpoint to influence authentication state.
