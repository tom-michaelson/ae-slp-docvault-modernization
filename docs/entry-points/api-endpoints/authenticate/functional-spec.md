# Functional spec — Authenticate user

**Key:** `authenticate`
**Legacy:** `AuthenticateEndpoint.HandleAsync` — `POST api/authenticate`
**Target REST:** `POST /api/authenticate`

## Purpose

Validates a username and password against ASP.NET Identity and returns a JWT bearer token on success. BlazorAdmin calls this on login to obtain a token that it then attaches to all subsequent PublicApi requests as an `Authorization: Bearer` header.

## Inputs

| Name | Type | Optional | Notes |
| --- | --- | --- | --- |
| `username` | string | no | ASP.NET Identity username (typically an email address in eShopOnWeb) |
| `password` | string | no | Plaintext password — transmitted over HTTPS only |

Request body (JSON):

```json
{
  "username": "admin@microsoft.com",
  "password": "Pass@word1"
}
```

## Outputs

HTTP 200 OK with body in all cases (success, bad credentials, locked out):

```json
{
  "result": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "admin@microsoft.com",
  "isLockedOut": false,
  "isNotAllowed": false,
  "requiresTwoFactor": false
}
```

On failed authentication (`result: false`), `token` is an empty string `""`.

## JWT structure (on success)

- **Algorithm:** HMAC-SHA256
- **Expiry:** 7 days from issuance (`exp = now + 7d`)
- **Claims:**
  - `ClaimTypes.Name` → the authenticated username
  - `ClaimTypes.Role` → one entry per role the user holds in `AspNetUserRoles` (e.g., `"Administrators"`)
- **Key source:** `AuthorizationConstants.JWT_SECRET_KEY` (configured in appsettings)

## Acceptance criteria

```gherkin
Scenario: Valid credentials
  Given a user "admin@microsoft.com" with password "Pass@word1" exists
  When POST /api/authenticate with {"username": "admin@microsoft.com", "password": "Pass@word1"}
  Then response status is 200 OK
  And response.result is true
  And response.token is a non-empty JWT string
  And response.isLockedOut is false

Scenario: Invalid password
  Given a user "admin@microsoft.com" exists
  When POST /api/authenticate with incorrect password
  Then response status is 200 OK
  And response.result is false
  And response.token is ""
  And response.isLockedOut is false

Scenario: Account locked out
  Given a user has exceeded the maximum failed-login attempts
  When POST /api/authenticate with any password
  Then response status is 200 OK
  And response.result is false
  And response.isLockedOut is true

Scenario: Unknown username
  Given no user with the provided username exists
  When POST /api/authenticate
  Then response status is 200 OK
  And response.result is false
  And response.token is ""

Scenario: JWT contains role claim
  Given "admin@microsoft.com" has the "Administrators" role in AspNetUserRoles
  When POST /api/authenticate with valid credentials
  Then the decoded JWT payload contains a ClaimTypes.Role claim with value "Administrators"
```

## Business rules

1. **Always returns HTTP 200**: Success, bad credentials, and lockout all return 200 OK. The Java target must replicate this — do not return 401 on credential failure; callers check `response.result`.
2. **lockoutOnFailure is enabled**: `PasswordSignInAsync` is called with `lockoutOnFailure: true`. After ASP.NET Identity's configured failure threshold (default: 5), the account is locked and `isLockedOut: true` is returned.
3. **Token only on success**: `ITokenClaimsService.GetTokenAsync` is called only when `result.Succeeded`. When auth fails, `token` is `""` — not null, not omitted.
4. **JWT expiry is 7 days**: `DateTime.UtcNow.AddDays(7)`. The Java target should match this duration.
5. **Roles embedded in JWT**: All roles from `AspNetUserRoles` for the user are added as `ClaimTypes.Role` claims. The `Administrators` role is what gates the catalog admin endpoints.
6. **No cookie issued**: `isPersistent: false` is passed to `PasswordSignInAsync` and PublicApi uses JWT bearer auth only. No Set-Cookie header is emitted.
7. **`isPersistent` is false**: The Identity sign-in is stateless — no session is created on the server. The JWT is the only credential returned.
8. **Ardalis.ApiEndpoints pattern**: This endpoint uses `EndpointBaseAsync` (not the MinimalApi `IEndpoint` pattern). The Java `@RestController` method should be a `@PostMapping("/api/authenticate")` returning `ResponseEntity<AuthenticateResponse>`.

## Non-functional

- Mutates state (increments `AccessFailedCount` or sets `LockoutEnd`) on failed attempts — not idempotent.
- No authentication required on the endpoint itself.
- Called by BlazorAdmin login form on every admin sign-in; low frequency.
- The JWT is used as a bearer token for all other PublicApi endpoints that require `[Authorize(Roles = "Administrators")]`.
