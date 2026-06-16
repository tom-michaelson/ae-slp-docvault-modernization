# Code Smell: Hardcoded Admin Credentials in Auth Route

## Description

The `backend/src/routes/auth.js` file contains a hardcoded admin email address and a bcrypt hash of a hardcoded password at module scope. These are used as the only valid credentials for the entire application:

```js
const ADMIN_EMAIL = 'admin@docvault.local';
const ADMIN_PASSWORD_HASH = bcrypt.hashSync('docvault123', 10);
```

The password `docvault123` is hardcoded in plain text and hashed at module load time. There is no user database table, no registration flow, and no way to change credentials without editing source code.

This is a code smell (not a bug) because the application documents itself as a demo with hardcoded credentials. However, the approach is a maintenance liability:
- The hash is computed at startup on every server start, adding unnecessary CPU time.
- The password is visible in plain text in the source file and in any developer's shell history if they've ever run `grep` on the file.
- Any future addition of real users requires changing the auth architecture entirely rather than incrementally.

## Recommended Resolution

1. Move credentials to environment variables: `ADMIN_EMAIL` and `ADMIN_PASSWORD_HASH` read from `process.env`.
2. Pre-compute the bcrypt hash offline and store the hash in the environment variable (not the plain text password).
3. For a production system, replace with a `users` database table.

## Location

- **File**: `backend/src/routes/auth.js`
- **Line**: 10–11

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The committed `backend/.env` contains `DEV_SKIP_AUTH=true`, which means these credentials are never exercised in the default developer setup — increasing the risk that the credential-handling code path is poorly tested.
