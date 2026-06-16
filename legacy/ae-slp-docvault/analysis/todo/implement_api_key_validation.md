# TODO: Implement API Key Validation

## Description

The API key authentication middleware was scaffolded but never completed. The validation logic that was supposed to look up the provided key against a database table is entirely absent. Currently any request with an `X-API-Key` header is rejected with 401.

## Original Comment

```
// TODO: implement API key validation
// This was supposed to look up the key in a database table
// but the table was never created and this was never finished.
//
// For now, any API key results in a 401.
// This means the API key header is checked but never actually works.
```

## Location

- **File**: `backend/src/middleware/apiKeyAuth.js`
- **Line**: 13

## Priority

High

## Estimated Effort

Large (4+ hours)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- Completing this requires: designing an `api_keys` table schema, writing a migration, implementing key lookup in the middleware, and adding a key generation/management flow.
- Until complete, the middleware should either be removed or replaced with a comment that makes clear this is non-functional.
- See `analysis/bug/api_key_auth_always_rejects.md` for the bug consequence of the stub.
