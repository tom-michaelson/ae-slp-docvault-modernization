# Runtime Verification: X-API-Key Header Behavior

## Endpoint

All `GET /api/*` routes (via `apiKeyAuth` middleware on `/api`)

## Test Environment

- Backend running on port 3001 with `DEV_SKIP_AUTH=true`
- Tested via PowerShell `Invoke-WebRequest`

## Test 1 — Any API Key Returns 401

**Request:**
```
GET http://localhost:3001/api/documents
X-API-Key: valid-key-test
```

**Response (401):**
```json
{ "error": "Invalid API key" }
```

**Assessment:** **BUG CONFIRMED AT RUNTIME.** Any request with an `X-API-Key` header is unconditionally rejected with 401. The middleware does not perform any lookup — it short-circuits all subsequent auth middleware (JWT and session) and returns immediately.

## Test 2 — Request Without API Key Header Proceeds Normally

**Request:**
```
GET http://localhost:3001/api/health
(no X-API-Key header)
```

**Response (200):**
```json
{ "status": "ok", "skipAuth": true }
```

**Assessment:** Requests without `X-API-Key` header proceed through the middleware stack normally. The stub does not affect requests that do not include the header. ✓

## Test 3 — Injection Attempt via API Key Header (Safety Check)

**Request:**
```
GET http://localhost:3001/api/documents
X-API-Key: ' OR '1'='1
```

**Response (401):**
```json
{ "error": "Invalid API key" }
```

**Assessment:** The header value is not processed (middleware returns 401 before any DB lookup). No injection risk — but only because the validation is completely absent, not because it is safe. ✓ (for wrong reasons)

## Findings

The static analysis finding is confirmed at runtime. The `apiKeyAuth` middleware is a stub that cannot successfully authenticate any request. Any integration expecting to use `X-API-Key` authentication will be unconditionally blocked.

Additionally, the middleware's early-return behavior means that a legitimate JWT-authenticated client that accidentally sends an `X-API-Key` header will be rejected even with a valid JWT — a potential production incident vector.

## Reference

`analysis/bug/api_key_auth_always_rejects.md`
