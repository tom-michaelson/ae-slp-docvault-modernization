# Knowledge Gap: Config System Unused Complexity

## Description

The backend configuration system reads from multiple sources (dotenv files, environment variables, hardcoded fallbacks) but the actual configuration keys used at runtime are extremely few, and several key aspects of how values are resolved are undocumented and inconsistent.

**Configuration sources in the system:**
1. `backend/.env` (loaded by `dotenv.config()` in `config.js`)
2. `backend/.env.development` (present but not explicitly loaded — `dotenv` loads `.env` by default, not `.env.development`)
3. `process.env` (runtime environment variables from shell/OS)
4. Hardcoded fallbacks in `config.js` (`3002`, `fallback-session-secret`, `fallback-jwt-secret`)
5. Hardcoded fallback in `index.js` (`8080`)
6. `dotenv.config()` is also called separately in `db/pool.js` — potentially loading the same file twice

**Config keys defined vs actually used at runtime:**

| Key | Defined In | Used By |
|-----|-----------|---------|
| `PORT` | .env, config.js, index.js | `index.js` only |
| `DATABASE_URL` | .env, pool.js | `db/pool.js` (reads directly from `process.env`) |
| `SESSION_SECRET` | .env, config.js | `index.js` session setup |
| `JWT_SECRET` | .env, config.js | `routes/auth.js`, `middleware/jwtAuth.js` |
| `UPLOAD_DIR` | .env, config.js | `routes/upload.js`, `routes/documents.js` |
| `DEV_SKIP_AUTH` | .env | `index.js` (reads directly from `process.env.DEV_SKIP_AUTH`, not via `config`) |
| `NODE_ENV` | .env.development | Not read by any application code |

**What is not documented:**
- `db/pool.js` calls `require('dotenv').config()` independently and reads `process.env.DATABASE_URL` directly, bypassing `config.js`. This means `DATABASE_URL` is the only config key that is not mediated by the config module.
- `DEV_SKIP_AUTH` is checked via `process.env.DEV_SKIP_AUTH` directly in `index.js`, not via `config.js` — so it is not in the centralized config despite being the most sensitive configuration key.
- The fallback value `fallback-jwt-secret` in `config.js` is a known-weak secret. If `JWT_SECRET` is not set (e.g., a developer's fresh clone with no `.env` overrides), the JWT signing key is a public, predictable string.

## Area Affected

- **Module / Component**: `backend/src/config.js`, `backend/src/db/pool.js`, `backend/src/index.js`
- **Domain**: Infrastructure, Security

## Impact

- A developer configuring the app for a new environment does not know which env file to use, which keys are actually read, or which keys are loaded through `config.js` vs directly via `process.env`.
- The `fallback-jwt-secret` fallback could silently sign tokens with a known-weak key in any environment where `JWT_SECRET` is not explicitly set.
- `DEV_SKIP_AUTH` and `DATABASE_URL` are not in the config module, creating a split mental model: some config is centralized, some is not.

## Recommended Actions

1. Consolidate all environment variable reads into `config.js`. Remove direct `process.env` reads from `pool.js` and `index.js`.
2. Add startup validation: if `JWT_SECRET` or `SESSION_SECRET` equals the fallback value and `NODE_ENV !== 'development'`, throw a configuration error rather than starting with a weak secret.
3. Document the config precedence in `config.js` with a comment: which file wins, what the fallbacks are, and which keys are required vs optional.
4. Move `DEV_SKIP_AUTH` into `config.js` and add a comment that it must be `false` in any non-local environment.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- The `fallback-jwt-secret` string is now a public known value because it appears in this committed analysis artifact. Any environment that uses it is compromised.
