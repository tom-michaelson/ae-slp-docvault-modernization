# Bug: Auth Refresh Returns Session Object (Frontend Login Crash)

## Description

`POST /api/auth/refresh` returns a session-shaped response `{ session: { userId, email, createdAt } }` instead of the JWT-shaped response `{ token: "eyJ...", refreshToken: "eyJ..." }` that the frontend expects.

The frontend's `AuthContext.login()` method calls `/api/auth/refresh` immediately after a successful login, then executes:
```js
const parts = refreshResponse.data.token.split('.');
```

Since `refreshResponse.data.token` is `undefined` (the response has `session`, not `token`), this throws:
> `TypeError: Cannot read properties of undefined (reading 'split')`

This crashes the login flow for every user who attempts to log in via the normal JWT path. The application is entirely unusable without the `DEV_SKIP_AUTH=true` bypass.

**Expected behavior**: `POST /api/auth/refresh` with a valid `refreshToken` returns `{ token: "eyJ...", refreshToken: "eyJ..." }`.

**Actual behavior**: Returns `{ session: { userId: "abc-123", email: "...", createdAt: "..." } }` — identical to the response from `POST /api/auth/session/login`.

**Root cause**: The `/refresh` handler was copy-pasted from the session login handler and the session-shaped return was never corrected to issue a new JWT.

## Recommended Resolution

Replace the body of the `POST /api/auth/refresh` handler in `backend/src/routes/auth.js` with logic that:
1. Verifies the provided `refreshToken` (already done — correct).
2. Issues a new short-lived access token and a new refresh token.
3. Returns `{ token: newAccessToken, refreshToken: newRefreshToken }`.

```js
const newToken = jwt.sign(
  { userId: decoded.userId, email: decoded.email, role: decoded.role || 'admin' },
  config.jwtSecret,
  { expiresIn: '1h' }
);
const newRefreshToken = jwt.sign(
  { userId: decoded.userId, email: decoded.email, type: 'refresh' },
  config.jwtSecret,
  { expiresIn: '7d' }
);
res.json({ token: newToken, refreshToken: newRefreshToken });
```

## Verification Method

Static Analysis

## Location

- **File**: `backend/src/routes/auth.js`
- **Line**: 76–87 (the `res.json({ session: { ... } })` return statement)

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The crash also exposes that `AuthContext.jsx` should validate `refreshResponse.data.token` before calling `.split('.')` — adding a null check would at minimum show a user-visible error rather than an unhandled crash.
- See also `analysis/anti_pattern/fractured_authentication.md` for the architectural root cause.
