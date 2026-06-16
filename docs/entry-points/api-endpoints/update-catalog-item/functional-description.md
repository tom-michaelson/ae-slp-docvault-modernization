# Functional Description: Update catalog item

> **Entry Point**: `update-catalog-item`
> **Location**: `src/PublicApi/CatalogItemEndpoints/UpdateCatalogItemEndpoint.cs`
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: `UpdateCatalogItemEndpoint.HandleAsync`

## Executive Summary

The `update-catalog-item` endpoint applies changes to the editable fields of an existing catalog item and returns the item's full new state. It is called by the BlazorAdmin edit modal when an administrator saves changes to a product, and will be called by the Angular 19 admin edit dialog component in the same way.

The endpoint requires a valid JWT Bearer token carrying the `Administrators` role — unauthenticated or unauthorised requests are rejected by the ASP.NET Core middleware before `HandleAsync` runs. After fetching the item by primary key (HTTP 404 if not found), three entity mutation methods are called in sequence — `UpdateDetails`, `UpdateBrand`, `UpdateType` — each enforcing guard clauses that would throw an `ArgumentException` if the input violates a constraint. `UpdateAsync` then persists the changes. The response returns all seven `CatalogItemDto` fields with the stored (unchanged) `PictureUri` rewritten to an absolute URL.

Three aspects are particularly important for migration. First, **the item ID is in the request body, not the URL path** — the legacy route is `PUT api/catalog-items` with no `{id}` segment; the Java target should move the ID to a path parameter (`PUT /api/catalog-items/{id}`) for RESTful conformance. Second, **`PictureUri`, `PictureBase64`, and `PictureName` are accepted in the request but completely ignored** — image upload is disabled in the legacy code; `PictureUri` in the stored row is never modified by this endpoint. Third, **DataAnnotations on the request type are not auto-enforced by MinimalApi** — the Guard clauses inside the entity methods are the actual runtime validation and produce HTTP 500 on failure; the Java target should use `@Valid` + Bean Validation to return HTTP 400 instead.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | PUT |
| Path | `api/catalog-items` (legacy) — Java target: `api/catalog-items/{id}` |
| Auth required | yes — JWT Bearer, `Administrators` role |
| Content-Type | `application/json` |

### Request Body

| Field | Type | Required | DataAnnotation (unenforced) | Notes |
| --- | --- | --- | --- | --- |
| `id` | int | yes | `[Range(1, 10000)]` | Primary key of the item to update. **In request body in legacy** — Java target should use path param `{id}` instead |
| `catalogBrandId` | int | yes | `[Range(1, 10000)]` | New brand FK. `Guard.Against.Zero` fires if 0 |
| `catalogTypeId` | int | yes | `[Range(1, 10000)]` | New type FK. `Guard.Against.Zero` fires if 0 |
| `description` | string | yes | `[Required]` | New description. `Guard.Against.NullOrEmpty` fires if blank |
| `name` | string | yes | `[Required]` | New display name. `Guard.Against.NullOrEmpty` fires if blank |
| `price` | decimal | yes | `[Range(0.01, 10000)]` | New unit price. `Guard.Against.NegativeOrZero` fires if ≤ 0 |
| `pictureUri` | string | no | *(none)* | **Accepted but ignored** — stored `PictureUri` is never modified by this endpoint |
| `pictureBase64` | string | no | *(none)* | **Accepted but ignored** — image upload is disabled |
| `pictureName` | string | no | *(none)* | **Accepted but ignored** — image upload is disabled |

> **DataAnnotations are metadata only.** `[Range]`, `[Required]`, etc. on `UpdateCatalogItemRequest` are not automatically validated by ASP.NET Core MinimalApi. They exist solely as documentation for tools like Swagger. The real runtime enforcement is the `Guard.Against.*` calls inside `CatalogItem`'s entity methods.

### Success Response

HTTP 200 OK

```json
{
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "catalogItem": {
    "id": 5,
    "name": "Updated Product Name",
    "description": "Updated description",
    "price": 24.99,
    "pictureUri": "https://host/catalog-images/eCatalog-item-default.png?0",
    "catalogTypeId": 3,
    "catalogBrandId": 2
  }
}
```

**Response fields:**

| Field | Type | Notes |
| --- | --- | --- |
| `correlationId` | Guid | From `BaseResponse` — propagated from `request.CorrelationId()` |
| `catalogItem.id` | int | `CatalogItem.Id` (unchanged) |
| `catalogItem.name` | string | Updated `CatalogItem.Name` |
| `catalogItem.description` | string | Updated `CatalogItem.Description` |
| `catalogItem.price` | decimal | Updated `CatalogItem.Price` |
| `catalogItem.pictureUri` | string | Absolute URL composed from the **unchanged stored** `PictureUri` via `IUriComposer.ComposePicUri` |
| `catalogItem.catalogTypeId` | int | Updated `CatalogItem.CatalogTypeId` |
| `catalogItem.catalogBrandId` | int | Updated `CatalogItem.CatalogBrandId` |

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 404 Not Found | `GetByIdAsync(request.Id)` returns null | empty |
| 401 Unauthorized | No `Authorization: Bearer` header, or invalid JWT | empty |
| 403 Forbidden | Valid JWT but caller is not in `Administrators` role | empty |
| 500 Internal Server Error | Guard clause triggered (null/empty Name or Description, price ≤ 0, brand/type ID = 0) — `ExceptionMiddleware` catches | error body from `ExceptionMiddleware` |

---

## Business Logic

### Overview

The endpoint loads the target `CatalogItem` by primary key. If not found, it returns HTTP 404 immediately. If found, it applies mutations through three domain entity methods: `UpdateDetails` (Name, Description, Price), `UpdateBrand` (CatalogBrandId), and `UpdateType` (CatalogTypeId). Each method carries its own guard clauses that throw `ArgumentException` on invalid input. After `UpdateAsync` persists the changes, the endpoint constructs a `CatalogItemDto` manually — no AutoMapper — reading the now-updated entity fields plus composing the stored (unchanged) `PictureUri` to an absolute URL.

Exactly five columns are updated: `Name`, `Description`, `Price`, `CatalogBrandId`, `CatalogTypeId`. `PictureUri` is read back from the entity for the response but is never written by this endpoint. The entity's `UpdatePictureUri()` method exists on `CatalogItem` but is not called here.

### Validation Rules

| Field | Guard clause | Exception type | Legacy failure | Java target |
| --- | --- | --- | --- | --- |
| `Name` | `Guard.Against.NullOrEmpty(details.Name)` | `ArgumentException` | HTTP 500 via `ExceptionMiddleware` | HTTP 400 via `@NotBlank` + `@Valid` |
| `Description` | `Guard.Against.NullOrEmpty(details.Description)` | `ArgumentException` | HTTP 500 | HTTP 400 |
| `Price` | `Guard.Against.NegativeOrZero(details.Price)` | `ArgumentException` | HTTP 500 | HTTP 400 via `@DecimalMin("0.01")` |
| `CatalogBrandId` | `Guard.Against.Zero(catalogBrandId)` | `ArgumentException` | HTTP 500 | HTTP 400 via `@Min(1)` |
| `CatalogTypeId` | `Guard.Against.Zero(catalogTypeId)` | `ArgumentException` | HTTP 500 | HTTP 400 via `@Min(1)` |
| `Id` — not found | null from `GetByIdAsync` | *(not thrown)* | HTTP 404 | HTTP 404 |

> **Guard range note**: `Guard.Against.Zero` rejects only 0 — negative IDs are not guarded by this clause. The DataAnnotation `[Range(1, 10000)]` on `Id`, `CatalogBrandId`, `CatalogTypeId` would have covered negative inputs, but it is not enforced. Java target: use `@Min(1)` on all three to prevent negatives from reaching the service layer.

### Call Sequence

1. **Initialise response** — `new UpdateCatalogItemResponse(request.CorrelationId())`. Sets the correlation Guid.
2. **Primary-key lookup** — `IRepository<CatalogItem>.GetByIdAsync(request.Id)`:
   - `SELECT Id, Name, Description, Price, PictureUri, CatalogTypeId, CatalogBrandId FROM CatalogItems WHERE Id = {id}`
   - If `null`: return `Results.NotFound()` → HTTP 404 empty body. Handler exits here.
3. **Apply name/description/price update** — `existingItem.UpdateDetails(new CatalogItemDetails(request.Name, request.Description, request.Price))`:
   - `Guard.Against.NullOrEmpty(Name)` — throws `ArgumentException` if null or empty
   - `Guard.Against.NullOrEmpty(Description)` — throws if null or empty
   - `Guard.Against.NegativeOrZero(Price)` — throws if ≤ 0
   - Sets `Name`, `Description`, `Price` on the in-memory entity
4. **Apply brand update** — `existingItem.UpdateBrand(request.CatalogBrandId)`:
   - `Guard.Against.Zero(CatalogBrandId)` — throws if 0
   - Sets `CatalogBrandId` on the in-memory entity
5. **Apply type update** — `existingItem.UpdateType(request.CatalogTypeId)`:
   - `Guard.Against.Zero(CatalogTypeId)` — throws if 0
   - Sets `CatalogTypeId` on the in-memory entity
6. **Persist** — `IRepository<CatalogItem>.UpdateAsync(existingItem)`:
   - EF Core change tracking generates: `UPDATE CatalogItems SET Name=…, Description=…, Price=…, CatalogBrandId=…, CatalogTypeId=… WHERE Id=…`
   - `PictureUri` is unchanged in the entity, so EF Core does not include it in the UPDATE statement
7. **Construct DTO manually** — all seven fields assigned inline; `PictureUri = _uriComposer.ComposePicUri(existingItem.PictureUri)` rewrites the stored relative path to absolute URL
8. **Return** — `Results.Ok(response)` → HTTP 200

---

## Component Details

### MinimalApi.Endpoint

**Class**: `UpdateCatalogItemEndpoint`
**File**: `src/PublicApi/CatalogItemEndpoints/UpdateCatalogItemEndpoint.cs`
**Interface**: `IEndpoint<IResult, UpdateCatalogItemRequest, IRepository<CatalogItem>>`

**Route registration (`AddRoute()`):**
```csharp
app.MapPut("api/catalog-items",
    [Authorize(
        Roles = BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS,
        AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]
    async (UpdateCatalogItemRequest request, IRepository<CatalogItem> itemRepository) =>
    {
        return await HandleAsync(request, itemRepository);
    })
    .Produces<UpdateCatalogItemResponse>()
    .WithTags("CatalogItemEndpoints");
```

Authorization is applied via the `[Authorize]` attribute on the lambda. The role value `ADMINISTRATORS` resolves to the string `"Administrators"` from `BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS`. The authentication scheme is `JwtBearerDefaults.AuthenticationScheme` (`"Bearer"`).

Note: `.ProducesProblem(401)`, `.ProducesProblem(403)`, and `.ProducesProblem(404)` are **not declared** — these responses occur at runtime but are absent from the OpenAPI schema.

**Injected constructor dependencies**: `IUriComposer`
**HandleAsync dependencies (via parameter)**: `IRepository<CatalogItem>` (injected by MinimalApi DI)

> **No AutoMapper**: Like `CatalogItemGetByIdEndpoint`, this endpoint constructs `CatalogItemDto` manually. `IMapper` is not injected.

---

**Request type**: `UpdateCatalogItemRequest`
**File**: `src/PublicApi/CatalogItemEndpoints/UpdateCatalogItemEndpoint.UpdateCatalogItemRequest.cs`
**Base**: `BaseRequest` (provides `CorrelationId()`)

| Property | C# Type | DataAnnotation | Notes |
| --- | --- | --- | --- |
| `Id` | `int` | `[Range(1, 10000)]` | Item to update — body field, not path param. Unenforced by MinimalApi |
| `CatalogBrandId` | `int` | `[Range(1, 10000)]` | New brand FK. Unenforced by MinimalApi |
| `CatalogTypeId` | `int` | `[Range(1, 10000)]` | New type FK. Unenforced by MinimalApi |
| `Description` | `string` | `[Required]` | Unenforced by MinimalApi |
| `Name` | `string` | `[Required]` | Unenforced by MinimalApi |
| `Price` | `decimal` | `[Range(0.01, 10000)]` | Unenforced by MinimalApi |
| `PictureUri` | `string` | *(none)* | Accepted but **ignored** |
| `PictureBase64` | `string` | *(none)* | Accepted but **ignored** |
| `PictureName` | `string` | *(none)* | Accepted but **ignored** |

---

**Response type**: `UpdateCatalogItemResponse`
**File**: `src/PublicApi/CatalogItemEndpoints/UpdateCatalogItemEndpoint.UpdateCatalogItemResponse.cs`
**Base**: `BaseResponse` (carries `correlationId` Guid)

| Property | C# Type | Notes |
| --- | --- | --- |
| `CatalogItem` | `CatalogItemDto` | Populated after successful update. Null only if 404 (but handler exits before populating) |
| `CorrelationId` | Guid (from `BaseResponse`) | Request tracing identifier |

---

**Entity: `CatalogItem`**
**File**: `src/ApplicationCore/Entities/CatalogItem.cs`

Mutation methods called by this endpoint:

| Method | Guard clauses | Fields mutated | Fields NOT touched |
| --- | --- | --- | --- |
| `UpdateDetails(CatalogItemDetails)` | `NullOrEmpty(Name)`, `NullOrEmpty(Description)`, `NegativeOrZero(Price)` | `Name`, `Description`, `Price` | `PictureUri`, `CatalogBrandId`, `CatalogTypeId` |
| `UpdateBrand(int)` | `Zero(catalogBrandId)` | `CatalogBrandId` | all others |
| `UpdateType(int)` | `Zero(catalogTypeId)` | `CatalogTypeId` | all others |

`UpdatePictureUri(string)` exists on `CatalogItem` but is **not called** by this endpoint.

`CatalogItemDetails` is a `readonly record struct` nested inside `CatalogItem`, carrying `Name?`, `Description?`, and `Price`.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `CatalogItems` | SELECT (by PK), UPDATE | `Id`, `Name`, `Description`, `Price`, `PictureUri` (read-only for response), `CatalogTypeId`, `CatalogBrandId` | SELECT first by primary key; UPDATE only the five mutable fields; `PictureUri` is included in the SELECT but excluded from the UPDATE (EF Core change tracking only writes modified properties) |

---

## Security Considerations

### Authentication

- **Required**: Yes — JWT Bearer.
- **Mechanism**: `Authorization: Bearer <token>` header. Token must be a valid JWT signed by the configured authority.
- **Role required**: `Administrators` (string value). This role is defined in `BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS`.
- **Enforcement**: `[Authorize(Roles = "Administrators", AuthenticationSchemes = "Bearer")]` attribute on the MinimalApi lambda. ASP.NET Core authentication middleware intercepts before `HandleAsync` runs:
  - No token → HTTP 401
  - Valid token but wrong role → HTTP 403
- Java target: use `@PreAuthorize("hasRole('ADMINISTRATORS')")` or Spring Security `HttpSecurity.authorizeHttpRequests()` to enforce the same role.

### Input Validation

**Validated by Guard clauses (runtime, throw → HTTP 500 in legacy):**
- `Name` and `Description` must be non-null and non-empty
- `Price` must be > 0
- `CatalogBrandId` and `CatalogTypeId` must be ≠ 0 (negatives pass through in legacy)

**Not validated at all (no guard clause):**
- `Id` range — any int reaching `GetByIdAsync` is accepted; natural 404 if no row matches
- `CatalogBrandId` and `CatalogTypeId` referential integrity — no FK existence check before `UpdateAsync`; DB constraint would fire if the brand/type ID doesn't exist (exception → 500)
- `Name` uniqueness — no duplicate check (unlike `create-catalog-item`)

**Java target recommendations:**
- Add `@Valid` on `@RequestBody UpdateCatalogItemRequest` with Jakarta Bean Validation annotations mirroring the DataAnnotations: `@Min(1)` on `Id`, `CatalogBrandId`, `CatalogTypeId`; `@DecimalMin("0.01")` on `Price`; `@NotBlank` on `Name`, `Description`. This converts Guard-clause failures from HTTP 500 to HTTP 400.
- Optionally validate FK existence for `CatalogBrandId` and `CatalogTypeId` before the UPDATE to return 400/404 instead of a DB constraint error.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| No `Task.Delay` | Not present in this endpoint | Nothing to remove |
| No AutoMapper | DTO constructed manually field-by-field — no reflection overhead | Java: manual DTO constructor or MapStruct |
| Two DB calls | `GetByIdAsync` (SELECT) + `UpdateAsync` (UPDATE) — two round-trips | Java: same pattern; no optimisation needed for low-frequency admin operation |
| No FK existence check | Brand/type IDs not validated against `CatalogBrands`/`CatalogTypes` before write | Java may leave this as-is (DB constraint will catch), or add explicit FK lookup |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| ID in request body | `PUT api/catalog-items` with `id` as a JSON body field — no path segment | Java target: `PUT /api/catalog-items/{id}` as path param; ignore any `id` in the JSON body |
| `pictureUri` in request | Accepted in body (`PictureUri` field) but **never applied** to the entity | Java: accept but ignore (or reject with 400 if supplied — confirm with API design decision) |
| `pictureBase64` / `pictureName` | Accepted but ignored — upload disabled | Java: same |
| `pictureUri` in response | Read from stored entity (unchanged) → composed to absolute URL via `IUriComposer` | Java: compose absolute URI from stored relative path; do not use any request-body `pictureUri` |
| DataAnnotations unenforced | `[Range]`, `[Required]` on request fields are not auto-validated by MinimalApi | Java: activate `@Valid` on the request body to enforce equivalent constraints |
| Guard clause failures → 500 | `ArgumentException` from Guards propagates to `ExceptionMiddleware` → HTTP 500 | Java: `@Valid` + Bean Validation will return HTTP 400 instead — preferred |
| Auth role string | `BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS = "Administrators"` | Java: match the exact role string `"Administrators"` in JWT claims / Spring Security config |
| No AutoMapper | DTO built field-by-field | Java: manual DTO or MapStruct; 7 fields exactly matching `CatalogItemDto` |
| Response wraps item | `{ "catalogItem": { ... } }` — not a bare DTO | Java response class must have a `catalogItem` field |
| HTTP 200 with body | Returns 200 OK with full DTO (not 204 No Content) | Java: return `ResponseEntity.ok(response)` with body |

---

## Analysis Notes

- **`Id` in body vs path**: The legacy design embeds `Id` in the JSON body of a PUT to an un-parameterised route (`PUT api/catalog-items`). This violates REST conventions (PUT should identify the resource via URI) and makes the route ambiguous. The Java target should move `Id` to the path — `PUT /api/catalog-items/{id}` — and **not accept it from the request body** to avoid mismatch errors.

- **Picture update is a completely separate flow**: `CatalogItem.UpdatePictureUri(pictureName)` exists and is callable, but is not invoked by this endpoint. Picture upload is handled elsewhere (possibly a Blazor component that was disabled). The Java admin UI that introduces image management should call a dedicated endpoint, not this one.

- **`Guard.Against.Zero` vs `Guard.Against.Negative`**: `UpdateBrand` and `UpdateType` use `Guard.Against.Zero` which rejects only `0` — a negative brand/type ID (e.g., `-1`) would pass the guard and reach `UpdateAsync`. If the `CatalogBrands`/`CatalogTypes` table has a FK constraint, the DB will reject it with a 500. Java target should use `@Min(1)` to block negatives before they reach the service.

- **`Guard.Against.NegativeOrZero(Price)`**: this guard rejects `0` and negative prices. A `Price` of `0.01` is the minimum accepted. The DataAnnotation `[Range(0.01, 10000)]` matches — Java: use `@DecimalMin(value = "0.01", inclusive = true)`.

- **`ProducesProblem` not declared for 401/403/404**: the OpenAPI (Swagger) schema for this endpoint will only advertise HTTP 200. BlazorAdmin clients must handle 401, 403, and 404 defensively. Java: declare `@ApiResponse` for all four codes in the Spring annotation.

- **EF Core selective UPDATE**: because `PictureUri` is never modified via `UpdatePictureUri`, EF Core's change tracking will not include it in the generated UPDATE statement. The Java JPA target using `@DynamicUpdate` or selective field updates achieves the same. If using a naïve JPA `.save()`, verify that `PictureUri` is not overwritten with null if the field is absent from the request body.

- **No optimistic concurrency**: there is no `RowVersion` / `[Timestamp]` / ETag check. Two concurrent admin edits to the same item will result in last-write-wins. This is acceptable for a low-traffic admin endpoint but worth flagging.
