# Bug: API Key Auth Always Rejects Valid Keys

## Description

The `apiKeyAuth` middleware returns HTTP 401 for every request that includes an `X-API-Key` header, regardless of the key value. The validation logic is a stub: the comment acknowledges a database lookup was intended but never implemented.

```js
if (apiKey) {
  // TODO: implement API key validation
  return res.status(401).json({ error: 'Invalid API key' });
}
```

Any service or integration that sends an `X-API-Key` header will be unconditionally rejected with 401. This includes:
- Service account integrations mentioned in the README ("Added for service account integrations")
- Automated systems that set the API key header expecting authenticated access

Additionally, since `apiKeyAuth` is the first middleware on `/api` routes, a request with an API key header never reaches JWT or session auth — it is rejected before those systems can validate the request.

**Expected behavior**: A valid API key grants access to `/api` routes.
**Actual behavior**: Any API key returns 401. No valid API key exists.

## Recommended Resolution

Either:
1. **Remove the `X-API-Key` check entirely** until API key authentication is properly designed and implemented (a `api_keys` database table, key generation flow, and validation logic are all absent).
2. **Or** move the TODO stub behind a feature flag that disables the check until it is ready, so the header does not cause rejection.

Do not deploy an auth middleware that unconditionally rejects authenticated requests while being described as a working feature.

## Verification Method

Static Analysis

## Location

- **File**: `backend/src/middleware/apiKeyAuth.js`
- **Line**: 15–20

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The README says "Integration docs coming soon" for API key auth — this implies external teams may be expecting this feature to work.
- The middleware also runs before JWT auth on `/api` routes, meaning it could block legitimate JWT-authenticated requests if a client accidentally includes an `X-API-Key` header.
