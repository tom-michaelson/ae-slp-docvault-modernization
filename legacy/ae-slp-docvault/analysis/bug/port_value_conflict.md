# Bug: Port Value Conflict Across Four Configuration Points

## Description

The backend server port is defined in four separate places with four different values. When the application starts, the actual port depends on the order dotenv loads files, which `.env` file is present, and the fallback chain — none of which is clearly documented.

| Location | Value | Notes |
|----------|-------|-------|
| `backend/.env` | `PORT=3001` | Committed file; the "primary" .env |
| `backend/.env.development` | `PORT=4000` | Committed file; loaded when `NODE_ENV=development` |
| `backend/src/config.js` line 4 | `process.env.PORT \|\| 3002` | Hardcoded fallback in config module |
| `backend/src/index.js` line 99 | `config.port \|\| 8080` | Hardcoded fallback at app startup |

**If `dotenv` loads `backend/.env` first**: port is 3001.
**If `backend/.env.development` is loaded**: port is 4000.
**If neither `.env` file is loaded**: port is 3002 (config.js fallback).
**If `config.port` is falsy for any reason**: port is 8080.

The `README.md` states "The backend runs on port 3001" and the frontend `REACT_APP_API_URL` is hardcoded to `http://localhost:3001/api`. If a developer runs the backend and the wrong .env is loaded, the frontend will silently fail all API calls with no clear error pointing to the port mismatch.

**Expected behavior**: The port is defined once, clearly, and consistently.
**Actual behavior**: Four definitions, three possible runtime values beyond the stated value, and a frontend that breaks silently if the wrong value is used.

## Recommended Resolution

1. Define the port once: in `backend/.env.example` as `PORT=3001`.
2. Remove the hardcoded fallback in `backend/src/config.js` (use `process.env.PORT` only, and fail loudly if not set: `if (!process.env.PORT) throw new Error('PORT not set')`).
3. Remove the hardcoded `|| 8080` fallback in `backend/src/index.js`.
4. Remove the `PORT=4000` from `backend/.env.development` or document that `NODE_ENV=development` is expected to use a different port.

## Verification Method

Static Analysis

## Location

- **File**: `backend/src/config.js`
- **Line**: 4
- **File**: `backend/src/index.js`
- **Line**: 99

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- Document drift: the README claims port 3001 but `.env.development` sets port 4000. See `analysis/document_drift/README.md`.
- Inconsistent port configuration is especially confusing during onboarding — a developer running in `NODE_ENV=development` mode will get port 4000 while the frontend expects 3001.
