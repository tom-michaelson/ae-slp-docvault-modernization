# Functional Description: Authenticate

> **Entry Point**: authenticate
> **Location**: src/PublicApi/AuthEndpoints/AuthenticateEndpoint.cs
> **Type**: API / Ardalis.ApiEndpoints
> **Domain**: identity
> **Legacy method**: Microsoft.eShopWeb.PublicApi.AuthEndpoints.AuthenticateEndpoint.HandleAsync

## Executive Summary

The `authenticate` endpoint accepts a username and password and returns a signed JWT for use in subsequent authenticated API calls. It is the sole authentication mechanism for the PublicApi — all admin endpoints (`create-catalog-item`, `update-catalog-item`, `delete-catalog-item`) require the `Administrators` role, which is encoded in the JWT claims returned here. The Angular admin interface calls this endpoint on login form submission and stores the token for attaching to subsequent requests.

The endpoint uses ASP.NET Core Identity's `SignInManager.PasswordSignInAsync` for credential verification and account lockout enforcement. On success it calls a separate `ITokenClaimsService` to build and sign the JWT. On failure it still returns HTTP 200 — the caller must inspect the `result` and `isLockedOut` fields to determine the outcome.

A key implementation detail: **the endpoint always returns HTTP 200**, even for bad credentials, locked accounts, or unknown usernames. The JWT secret key is a hardcoded constant (`AuthorizationConstants.JWT_SECRET_KEY`) that must be replaced with a configurable secret in the Java target. The lockout comment in the source is misleading — `lockoutOnFailure: true` IS passed, so repeated failed attempts will lock the account.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | POST |
| Path | `/api/authenticate` |
| Content-Type | `application/json` |
| Auth required | no |

### Request Body

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `username` | string | yes | ASP.NET Identity username (email address for seeded accounts) |
| `password` | string | yes | Plaintext password — transmitted over HTTPS only |
| `correlationId` | Guid | no | Optional client-supplied correlation ID echoed back in response (inherited from `BaseRequest → BaseMessage`) |

Request body example:
```json
{
  "username": "demouser@microsoft.com",
  "password": "Pass@word1"
}
```

### Success Response

HTTP 200 OK is returned in **all cases** — both success and failure.

```json
{
  "result": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "demouser@microsoft.com",
  "isLockedOut": false,
  "isNotAllowed": false,
  "requiresTwoFactor": false,
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

Failed authentication (wrong password):
```json
{
  "result": false,
  "token": "",
  "username": "demouser@microsoft.com",
  "isLockedOut": false,
  "isNotAllowed": false,
  "requiresTwoFactor": false,
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

Locked-out account:
```json
{
  "result": false,
  "token": "",
  "username": "demouser@microsoft.com",
  "isLockedOut": true,
  "isNotAllowed": false,
  "requiresTwoFactor": false,
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

### Response Fields

| Field | Type | Value on success | Value on failure |
| --- | --- | --- | --- |
| `result` | bool | `true` | `false` |
| `token` | string | signed JWT string | `""` (empty string) |
| `username` | string | echoed from request | echoed from request |
| `isLockedOut` | bool | `false` | `true` if account is locked |
| `isNotAllowed` | bool | `false` | `true` if sign-in not allowed (email unconfirmed, etc.) |
| `requiresTwoFactor` | bool | `false` | `true` if 2FA is required |
| `correlationId` | Guid | echoed from request | echoed from request |

### Error Responses

This endpoint does not return 4xx or 5xx for authentication failures. The only non-200 scenario is an unhandled server exception (e.g., database unavailable → 500).

---

## Business Logic

### Overview

The endpoint performs credential verification via ASP.NET Core Identity and, on success, generates a signed JWT containing the user's name and role claims. The JWT is used by the Angular admin interface for subsequent authorized API calls.

The critical design choice is that all outcomes — success, wrong password, unknown user, locked account — return HTTP 200. The Angular client must inspect the `result` boolean to determine whether authentication succeeded, and check `isLockedOut` to display an appropriate error message.

Account lockout is enabled (`lockoutOnFailure: true`). After a configurable number of failed attempts (ASP.NET Identity default: 5), the account is locked for a configurable duration (default: 5 minutes). During lockout, `PasswordSignInAsync` returns `IsLockedOut: true` without checking the password.

### Validation Rules

| Condition | Behavior |
| --- | --- |
| Valid credentials | `result=true`, JWT token returned |
| Invalid password (not locked) | `result=false`, `token=""`, `isLockedOut=false` |
| Invalid password (lockout threshold reached) | `result=false`, `token=""`, `isLockedOut=true` |
| Unknown username | `result=false`, `token=""` — ASP.NET Identity returns `SignInResult.Failed` without revealing that the user doesn't exist |
| Account locked out (lockout already in effect) | `result=false`, `isLockedOut=true` — password is not checked |
| 2FA required | `result=false`, `requiresTwoFactor=true` — not wired up in eShopOnWeb |

There is no server-side validation of `username` or `password` fields (no null/empty guards, no length checks). If `username` or `password` is null or empty, `PasswordSignInAsync` returns `SignInResult.Failed`.

### Call Sequence

1. Receive POST body → deserialize into `AuthenticateRequest { Username, Password }`
2. Instantiate `AuthenticateResponse(request.CorrelationId())` — populates `correlationId` field
3. Call `SignInManager.PasswordSignInAsync(username, password, isPersistent: false, lockoutOnFailure: true)`
   - Looks up `AspNetUsers` row by username
   - Validates password hash
   - Increments failed attempt count if wrong password
   - Locks account if threshold reached
   - Returns `SignInResult { Succeeded, IsLockedOut, IsNotAllowed, RequiresTwoFactor }`
4. Populate response fields: `Result`, `IsLockedOut`, `IsNotAllowed`, `RequiresTwoFactor`, `Username`
5. **If `result.Succeeded == true` only**: call `ITokenClaimsService.GetTokenAsync(username)`
   - `UserManager.FindByNameAsync(username)` → SELECT AspNetUsers by username
   - `UserManager.GetRolesAsync(user)` → SELECT AspNetUserRoles for user
   - Build claims list: `[ClaimTypes.Name = username]` + `[ClaimTypes.Role = role]` for each role
   - Create `SecurityTokenDescriptor { Subject, Expires = UtcNow + 7 days, SigningCredentials = HMAC-SHA256 }`
   - Sign token using `Encoding.ASCII.GetBytes(AuthorizationConstants.JWT_SECRET_KEY)`
   - Return serialized JWT string
6. Assign `response.Token = jwt` (or leave `""` if sign-in failed)
7. Return `response` as `ActionResult<AuthenticateResponse>` → HTTP 200

---

## Component Details

### Ardalis.ApiEndpoints Endpoint

**Class**: `AuthenticateEndpoint`
**File**: `src/PublicApi/AuthEndpoints/AuthenticateEndpoint.cs`

**Base class pattern**:
```csharp
EndpointBaseAsync
    .WithRequest<AuthenticateRequest>
    .WithActionResult<AuthenticateResponse>
```

This is **Ardalis.ApiEndpoints** — different from the MinimalApi `IEndpoint<IResult, TRequest, TDep>` pattern used by catalog endpoints. Route is registered via `[HttpPost("api/authenticate")]` attribute, not via `AddRoute()` / `app.MapPost()`. The endpoint is picked up by standard ASP.NET Core MVC controller scanning.

**Injected dependencies**: `SignInManager<ApplicationUser>`, `ITokenClaimsService`

**Request type**: `AuthenticateRequest : BaseRequest`
**File**: `src/PublicApi/AuthEndpoints/AuthenticateEndpoint.AuthenticateRequest.cs`
**Fields**: `Username` (string), `Password` (string), `CorrelationId` (Guid, inherited)

**Response type**: `AuthenticateResponse : BaseResponse`
**File**: `src/PublicApi/AuthEndpoints/AuthenticateEndpoint.AuthenticateResponse.cs`
**Fields**: `Result` (bool, default false), `Token` (string, default ""), `Username` (string, default ""), `IsLockedOut` (bool, default false), `IsNotAllowed` (bool, default false), `RequiresTwoFactor` (bool, default false), `CorrelationId` (Guid, inherited)

---

### Token Claims Service

**Interface**: `ITokenClaimsService`
**Implementation**: `IdentityTokenClaimService`
**File**: `src/Infrastructure/Identity/IdentityTokenClaimService.cs`

**Method**: `Task<string> GetTokenAsync(string userName)`

**JWT construction**:
- Key: `Encoding.ASCII.GetBytes("SecretKeyOfDoomThatMustBeAMinimumNumberOfBytes")` — from `AuthorizationConstants.JWT_SECRET_KEY`
- Algorithm: HMAC-SHA256 (`SecurityAlgorithms.HmacSha256Signature`)
- Expiry: `DateTime.UtcNow.AddDays(7)`
- Claims: `ClaimTypes.Name = userName` + one `ClaimTypes.Role` per role assigned to the user in Identity

**Edge case**: If `UserManager.FindByNameAsync` returns null inside `GetTokenAsync`, it throws `UserNotFoundException`. This should not occur in practice because `PasswordSignInAsync` would have already returned `Succeeded=false` for an unknown username, but the guard exists as a safety net.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `AspNetUsers` | SELECT | `Id`, `UserName`, `NormalizedUserName`, `PasswordHash`, `LockoutEnabled`, `LockoutEnd`, `AccessFailedCount` | Accessed twice on success: once by `PasswordSignInAsync` (credential check + lockout state) and once by `FindByNameAsync` inside `GetTokenAsync`. On failure, accessed once by `PasswordSignInAsync`. |
| `AspNetUserRoles` | SELECT | `UserId`, `RoleId` | Accessed only on success by `GetRolesAsync(user)` to build JWT role claims. JOIN with `AspNetRoles` to resolve role names. |

---

## Security Considerations

### Authentication

- **Required on this endpoint**: No — this endpoint IS the authentication gateway.
- The endpoint has no `[Authorize]` attribute.

### JWT Secret Key

- **Critical**: The signing key is the hardcoded constant `"SecretKeyOfDoomThatMustBeAMinimumNumberOfBytes"` stored in `AuthorizationConstants.JWT_SECRET_KEY`.
- **Java target must**: load the secret from configuration (environment variable, secrets manager) — never hardcode.
- All catalog admin endpoints verify this same key (`Program.cs` line 54 configures JWT bearer validation using the same constant).

### Password Handling

- Passwords are transmitted in the POST body as plaintext — HTTPS is the assumed transport.
- Hashing is performed by ASP.NET Core Identity (BCrypt-based `PasswordHasher<TUser>`) on the server side.
- The Java target must use a compatible password hasher only if migrating existing users; for new users, Spring Security's `BCryptPasswordEncoder` is standard.

### Lockout Policy

- `lockoutOnFailure: true` is passed — failed attempts DO count toward lockout.
- Default ASP.NET Identity lockout: 5 failures → 5-minute lockout (configurable in `IdentityOptions`).
- The `isLockedOut` response field signals to the client that further attempts are futile until the lockout expires. The Java target should return an equivalent signal.

### Username Enumeration

- A correct or incorrect username both return `result: false` with no differentiation. This prevents username enumeration from the response body.

### Input Validation

- No server-side validation guards on `username` or `password` (no null checks, no length limits). `PasswordSignInAsync` handles null/empty gracefully by returning `SignInResult.Failed`.
- The Java target should add `@NotBlank` validation on both fields to return 400 rather than silently failing.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Two AspNetUsers lookups on success | `PasswordSignInAsync` queries the user once; `GetTokenAsync` calls `FindByNameAsync` again | Java: load user once and pass to token generation to avoid the second lookup |
| No `Task.Delay` | No artificial delay in this endpoint | N/A |
| JWT signed per request | Token generated fresh on every successful login; no caching | Acceptable — JWT is stateless by design |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| Always HTTP 200 | `HandleAsync` returns `response` directly — no `BadRequest` or `Unauthorized` | Java: preserve this contract exactly. Angular client checks `result` boolean, not HTTP status. |
| JWT secret from constant | `AuthorizationConstants.JWT_SECRET_KEY = "SecretKeyOfDoomThatMustBeAMinimumNumberOfBytes"` | Java: inject from `application.properties` / env var / secrets manager |
| JWT expiry | `DateTime.UtcNow.AddDays(7)` | Java: configure same 7-day expiry (`jjwt` / `spring-security-oauth2` `setExpiration`) |
| JWT claims | `ClaimTypes.Name` (mapped as `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name`) and `ClaimTypes.Role` | Java: use standard claims `sub` (subject) and `roles` or match the exact claim URIs if Angular parses them by key |
| Ardalis.ApiEndpoints | Route registered via `[HttpPost]` attribute; endpoint class scanned as MVC controller | Java: standard `@RestController @PostMapping` — no special framework needed |
| `correlationId` in request/response | `BaseMessage` holds a `Guid CorrelationId`; response echoes the request's ID | Java: include `correlationId` as optional UUID in request/response DTOs for tracing |
| Lockout enabled | `lockoutOnFailure: true` enforced | Java: configure `UserDetailsService` + `AbstractUserDetailsAuthenticationProvider` lockout, or replicate via `FailedLoginAttempt` table |
| `requiresTwoFactor` | Returned but 2FA is not wired up in eShopOnWeb | Java: return `false` unless 2FA is later added |
| `isNotAllowed` | Returned; triggered when email is unconfirmed (RequireConfirmedEmail = false in eShopOnWeb) | Java: return `false`; replicate if email confirmation is added |

---

## Analysis Notes

- **The source comment is wrong.** Line 41–43 says "This doesn't count login failures towards account lockout" but the actual call on line 44 passes `lockoutOnFailure: true`. The true behavior is that lockout IS enforced. Document this for Java developers who read the source.
- **`UserNotFoundException` in `GetTokenAsync`** is a defensive guard — if somehow `FindByNameAsync` returns null after `PasswordSignInAsync` succeeded, it throws rather than generating a token for an unknown user. The Java implementation should include a similar safety check.
- **No refresh token mechanism.** The JWT is valid for 7 days. There is no refresh endpoint — the client must re-authenticate after expiry. The Java target should clarify whether refresh tokens are in scope.
- **Username format.** Seeded accounts use email addresses as usernames (`demouser@microsoft.com`). ASP.NET Identity normalizes usernames to uppercase for lookup. The Java target should also normalize to be case-insensitive on lookup.
- **Two AspNetUsers round-trips on success.** `PasswordSignInAsync` does its own lookup internally, then `GetTokenAsync` calls `FindByNameAsync` a second time. The Java implementation can avoid this by passing the loaded user object directly to the token generation method.
- **`isPersistent: false`.** Session cookie behavior. Not relevant to a stateless JWT API but worth noting: no persistent session cookie is set.
