# TODO Distribution Summary

## Overview

A total of **10 TODO/FIXME/HACK/NOTE markers** were found across the codebase, spread across **7 unique files**. No FIXME or HACK markers were found — all markers are TODO or NOTE.

| Marker Type | Count |
|-------------|-------|
| TODO | 8 |
| NOTE | 2 |
| FIXME | 0 |
| HACK | 0 |

## Files Containing Markers

| File | Markers |
|------|---------|
| `backend/src/middleware/apiKeyAuth.js` | 1 TODO — unimplemented feature |
| `backend/src/services/IndexManager.js` | 1 TODO — unimplemented feature |
| `backend/src/db/migrations/003-create-trigger.sql` | 1 NOTE — deliberate tag omission |
| `frontend/src/store.js` | 3 TODOs — abandoned refactor action items |
| `frontend/src/middleware/customMiddleware.js` | 1 TODO — unconnected analytics |
| `frontend/src/components/DocumentGrid.jsx` | 3 TODOs — batch operations not started |
| `frontend/src/utils/fileHelpers.js` | 1 NOTE — design smell observation |
| `frontend/src/reducers/userReducer.js` | 1 NOTE (header comment about duplication) |
| `frontend/src/reducers/filtersReducer.js` | 1 NOTE (header comment about duplication) |
| `frontend/src/reducers/documentsReducer.js` | 1 NOTE (header comment about duplication) |

## Production-Critical Paths

Two markers are on production-critical code paths:

1. **`apiKeyAuth.js` — `// TODO: implement API key validation`**: This is on the authentication middleware that runs before every `/api` request. The stub causes real runtime failures (any API key returns 401).

2. **`003-create-trigger.sql` — `-- NOTE: NEW.tags deliberately omitted`**: This is in the database migration that runs on every new installation. The omission causes silent data loss (tags dropped on upload).

## Temporary Workarounds Never Resolved

The `store.js` TODOs reference "sprint 14, maybe?" — indicating they were written with an explicit deferral and have not been revisited. The `customMiddleware.js` TODO references an analytics account that "was never set up" — a dependency that was never created.

## Maintenance Culture Assessment

The TODO distribution in DocVault tells a consistent story: features were started to scaffolding depth and then parked. The authentication system has a stub that actively breaks clients. The search pipeline has a placeholder that ensures it always uses the slowest path. The analytics middleware runs on every action dispatch but transmits nothing. Rather than either completing or removing these stubs, the codebase accumulated "I'll finish this later" markers — and "later" never came. What is unusual is that several NOTE comments are self-aware about the duplication and redundancy in the codebase, written by developers who clearly recognized the problems but did not address them. This pattern — recognition without resolution — is a signal of a team under time pressure that consistently deferred cleanup rather than integrated it into normal development flow.
