# Functional Description: Create catalog item

> **Entry Point**: create-catalog-item
> **Location**: src/PublicApi/CatalogItemEndpoints/CreateCatalogItemEndpoint.cs
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: Microsoft.eShopWeb.PublicApi.CatalogItemEndpoints.CreateCatalogItemEndpoint.HandleAsync

## Executive Summary

The `create-catalog-item` endpoint inserts a new catalog item and returns it as a 201 Created response. It is called by the BlazorAdmin "Create New" form; in the Angular 19 rebuild the admin create dialog component will call it the same way. Authentication is required — the caller must supply a JWT bearing the `Administrators` role.

Before inserting, the endpoint performs a name-uniqueness check: if any row in `CatalogItems` already has the exact same `Name`, it throws `DuplicateException`, which the API's `ExceptionMiddleware` intercepts and returns as HTTP 409 Conflict. Image upload is explicitly disabled in this codebase — `PictureUri`, `PictureBase64`, and `PictureName` fields in the request are silently ignored. After insert, the endpoint unconditionally overwrites `PictureUri` with a hardcoded default placeholder (`eCatalog-item-default.png`) via a second UPDATE query.

A non-obvious detail: the `PictureUri` stored in the database uses `new DateTime().Ticks` (not `DateTime.UtcNow.Ticks`) as the cache-busting query string. Since `new DateTime()` is `DateTime.MinValue` and its ticks value is always `0`, the stored path is always `images\products\eCatalog-item-default.png?0`. The Java target can skip the second UPDATE entirely by setting this value before the initial INSERT.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | POST |
| Path | `/api/catalog-items` |
| Content-Type | `application/json` |
| Auth required | yes — JWT Bearer, `Administrators` role |

### Request Body

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `catalogBrandId` | int | yes | Foreign key to `CatalogBrands.Id`. No FK validation in code — DB constraint enforced. |
| `catalogTypeId` | int | yes | Foreign key to `CatalogTypes.Id`. No FK validation in code — DB constraint enforced. |
| `description` | string | yes | Free-text description. No server-side null/empty guard in constructor. |
| `name` | string | yes | Display name. Checked for uniqueness (exact, case-sensitive at LINQ level) before insert. |
| `price` | decimal | yes | Unit price. No server-side minimum guard in constructor. |
| `pictureUri` | string | no | **Accepted but ignored.** Always overwritten with default placeholder after insert. |
| `pictureBase64` | string | no | **Accepted but ignored.** Image upload is disabled. |
| `pictureName` | string | no | **Accepted but ignored.** Image upload is disabled. |
| `correlationId` | Guid | no | Optional client-supplied correlation ID echoed back in response (inherited from `BaseRequest`). |

Request body example:
```json
{
  "catalogBrandId": 1,
  "catalogTypeId": 2,
  "description": "A great new product",
  "name": "New Product",
  "price": 29.99
}
```

### Success Response

HTTP 201 Created with `Location: api/catalog-items/{id}` header:

```json
{
  "catalogItem": {
    "id": 42,
    "name": "New Product",
    "description": "A great new product",
    "price": 29.99,
    "pictureUri": "https://host/catalog-images/eCatalog-item-default.png?0",
    "catalogTypeId": 2,
    "catalogBrandId": 1
  },
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

The `Location` header value is `api/catalog-items/{id}` (no leading slash — matches the `Results.Created` call in source).

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 401 | JWT absent or invalid | empty |
| 403 | JWT valid but caller not in `Administrators` role | empty |
| 409 | `CatalogItems.Name` already exists (exact match) | `{ "statusCode": 409, "message": "A catalogItem with name {name} already exists" }` |
| 500 | Unhandled exception (e.g., FK violation on `CatalogBrandId`/`CatalogTypeId`) | empty |

---

## Business Logic

### Overview

The endpoint creates one new catalog item. Before inserting, it counts any `CatalogItems` rows with the same `Name`. A count > 0 causes immediate rejection with HTTP 409. If the name is unique, the entity is constructed and inserted. After the INSERT succeeds (verified by `newItem.Id != 0`), the entity's `PictureUri` is overwritten with the default placeholder and a second UPDATE is issued. The response DTO is built manually and returned as `Results.Created` (HTTP 201) with a `Location` header.

There is no server-side validation of numeric fields — `price`, `catalogBrandId`, and `catalogTypeId` are passed directly to the entity constructor and repository. Foreign key violations and negative prices will cause the INSERT to fail at the database level, propagating as an unhandled exception → HTTP 500.

### Validation Rules

| Field / Condition | Rule | Failure behavior |
| --- | --- | --- |
| `name` uniqueness | `CatalogItemNameSpecification` counts existing rows WHERE `Name = request.Name` | `DuplicateException` thrown → `ExceptionMiddleware` → HTTP 409 Conflict |
| `price` | No guard in constructor — any decimal value accepted | Invalid value causes DB-level failure → HTTP 500 |
| `catalogBrandId` | No FK validation in code | DB constraint violation → HTTP 500 |
| `catalogTypeId` | No FK validation in code | DB constraint violation → HTTP 500 |
| `description` / `name` | No null/empty guard in constructor | DB `NOT NULL` constraint violation → HTTP 500 |
| `pictureUri` / `pictureBase64` / `pictureName` | Not validated — silently ignored | N/A |

### Call Sequence

1. Receive POST body → deserialize into `CreateCatalogItemRequest { CatalogBrandId, CatalogTypeId, Description, Name, Price, PictureUri, PictureBase64, PictureName }`
2. Instantiate `CreateCatalogItemResponse(request.CorrelationId())` — populates `correlationId` in response
3. Build `CatalogItemNameSpecification(request.Name)` — encapsulates `WHERE Name = request.Name`
4. `IRepository<CatalogItem>.CountAsync(spec)` → count of rows with matching `Name`
   - If count > 0: `throw new DuplicateException($"A catalogItem with name {request.Name} already exists")` → caught by `ExceptionMiddleware` → HTTP 409
5. `new CatalogItem(catalogTypeId, catalogBrandId, description, name, price, pictureUri)` — entity constructor, sets all fields (including the request's `PictureUri` temporarily)
6. `IRepository<CatalogItem>.AddAsync(newItem)` → INSERT into `CatalogItems`; returned `newItem` now has EF-assigned `Id`
7. If `newItem.Id != 0` (always true after successful INSERT):
   - `newItem.UpdatePictureUri("eCatalog-item-default.png")` → sets `PictureUri = "images\\products\\eCatalog-item-default.png?0"` (see Analysis Notes on the ticks value)
   - `IRepository<CatalogItem>.UpdateAsync(newItem)` → UPDATE `CatalogItems` SET `PictureUri = ...`
8. Build `CatalogItemDto` manually: `{ Id, CatalogBrandId, CatalogTypeId, Description, Name, PictureUri = ComposePicUri(newItem.PictureUri), Price }`
9. Set `response.CatalogItem = dto`
10. Return `Results.Created($"api/catalog-items/{dto.Id}", response)` → HTTP 201 with `Location: api/catalog-items/{id}`

---

## Component Details

### MinimalApi.Endpoint

**Class**: `CreateCatalogItemEndpoint`
**File**: `src/PublicApi/CatalogItemEndpoints/CreateCatalogItemEndpoint.cs`

**Route registration (`AddRoute()`):**
```csharp
app.MapPost("api/catalog-items",
    [Authorize(Roles = "Administrators", AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]
    async (CreateCatalogItemRequest request, IRepository<CatalogItem> itemRepository) =>
    {
        return await HandleAsync(request, itemRepository);
    })
    .Produces<CreateCatalogItemResponse>()
    .WithTags("CatalogItemEndpoints");
```

Note: no `.ProducesProblem(401)` declared in `AddRoute()`. The 401/403 responses are generated automatically by the `[Authorize]` attribute.

**Request type**: `CreateCatalogItemRequest : BaseRequest`
**File**: `src/PublicApi/CatalogItemEndpoints/CreateCatalogItemEndpoint.CreateCatalogItemRequest.cs`
**Fields**: `CatalogBrandId` (int), `CatalogTypeId` (int), `Description` (string), `Name` (string), `PictureUri` (string), `PictureBase64` (string), `PictureName` (string), `Price` (decimal)
**No DataAnnotations** — no `[Required]`, `[Range]`, or `[MinLength]` on any field.

**Response type**: `CreateCatalogItemResponse : BaseResponse`
**File**: `src/PublicApi/CatalogItemEndpoints/CreateCatalogItemEndpoint.CreateCatalogItemResponse.cs`
**Fields**: `CatalogItem` (CatalogItemDto), `CorrelationId` (Guid, inherited from `BaseResponse`)

**Injected dependencies (constructor)**: `IUriComposer`
**Injected dependencies (HandleAsync parameter)**: `IRepository<CatalogItem>` (from DI via MinimalApi parameter binding)

---

### CatalogItem Entity (relevant methods)

**File**: `src/ApplicationCore/Entities/CatalogItem.cs`

**Constructor** (`CatalogItem(int catalogTypeId, int catalogBrandId, string description, string name, decimal price, string pictureUri)`):
- No guard clauses — all values assigned directly. A null `name` or negative `price` will not throw in C#; failures are deferred to the database.

**`UpdatePictureUri(string pictureName)`** (line 56):
```csharp
PictureUri = $"images\\products\\{pictureName}?{new DateTime().Ticks}";
```
- Uses `new DateTime()` (not `DateTime.UtcNow`) — `new DateTime().Ticks` is always `0`.
- Result: `PictureUri` is always `images\products\eCatalog-item-default.png?0`.

---

### CatalogItemNameSpecification

**File**: `src/ApplicationCore/Specifications/CatalogItemNameSpecification.cs`

```csharp
Query.Where(item => catalogItemName == item.Name);
```

- Exact string match. In SQL Server with a case-insensitive collation (the typical default), this will match case-insensitively at the DB level even though the C# expression is ordinal. The Java target should clarify the intended case-sensitivity and match the collation behavior.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `CatalogItems` | COUNT, INSERT, UPDATE | `Id`, `Name`, `Description`, `Price`, `PictureUri`, `CatalogTypeId`, `CatalogBrandId` | COUNT for duplicate name check; INSERT for new row; UPDATE to overwrite `PictureUri` with default. Java target can collapse INSERT + UPDATE into single INSERT. |

---

## Security Considerations

### Authentication

- **Required**: yes — JWT Bearer token in `Authorization: Bearer {token}` header
- **Role required**: `Administrators` (`BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS = "Administrators"`)
- **Enforcement**: `[Authorize(Roles = "Administrators", AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]` on the lambda in `AddRoute()`

### Input Validation

- No server-side validation guards. The only business rule enforced in code is the duplicate name check. All other invalid inputs (null name, negative price, invalid FK IDs) result in unhandled exceptions → HTTP 500.
- **Java target must add**: `@NotBlank` on `name` and `description`, `@DecimalMin("0.01")` on `price`, `@Min(1)` on `catalogBrandId` and `catalogTypeId`, to return HTTP 400 instead of 500.

### Image Upload Disabled

- `PictureBase64` and `PictureName` are accepted but discarded. The comment in source (`// We disabled the upload functionality`) explains this was a security response to a community-reported vulnerability. The Java target should either omit these fields from the request DTO or document them as ignored.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Two-write pattern | INSERT (line 51) + UPDATE (line 60) — two round-trips for a single create | Java: set `PictureUri` to the default value before INSERT; collapse into one write |
| No AutoMapper | `CatalogItemDto` is manually constructed field-by-field in `HandleAsync` | Java: use a manual DTO constructor or MapStruct — same 7 fields |
| No `Task.Delay` | No artificial delay in this endpoint | N/A |
| Duplicate name COUNT query | One COUNT query per create request | Java: same pattern, or catch the unique constraint violation from the DB |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| HTTP response code | `Results.Created(...)` → HTTP 201 | Java: `ResponseEntity.created(URI)` — must be 201, not 200 |
| `Location` header | `$"api/catalog-items/{dto.Id}"` (no leading slash) | Java: `UriComponentsBuilder.fromPath("api/catalog-items/{id}")` — match the path exactly |
| Two-write INSERT+UPDATE | INSERT sets client-supplied `PictureUri`; UPDATE overwrites with default | Java: set `pictureUri = "images\\products\\eCatalog-item-default.png?0"` before INSERT, skip UPDATE |
| `PictureUri` stored format | `images\products\eCatalog-item-default.png?0` (backslash path separator, ticks always 0) | Java: store exactly this string if database compatibility is required; apply `IUriComposer` equivalent for response |
| `pictureUri` in response | Absolute URL via `IUriComposer.ComposePicUri` | Java: compose absolute URL from configurable base URL + stored path |
| Duplicate name check | `CatalogItemNameSpecification` WHERE `Name = request.Name` → HTTP 409 on match | Java: query by name before insert (or catch `DataIntegrityViolationException` from a DB unique index); return `409 Conflict` with same message format |
| `DuplicateException` → 409 | Thrown inside `HandleAsync`, caught by `ExceptionMiddleware` globally | Java: `@ExceptionHandler(DuplicateException)` or `@ControllerAdvice` returning 409; match response body `{ statusCode, message }` |
| No input validation | No `[Required]`, `[Range]`, or Guard clauses on request fields | Java: add `@Valid` + `@NotBlank`/`@DecimalMin`/`@Min` annotations; return 400 for invalid input |
| Auth mechanism | `[Authorize(Roles = "Administrators", AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]` | Java: `@PreAuthorize("hasRole('ADMINISTRATORS')")` or Security filter chain role check |
| Case-sensitivity of name check | Depends on SQL Server collation (typically case-insensitive) | Java: use `COLLATE` or `LOWER()` if case-insensitive uniqueness is required; document the behavior |

---

## Analysis Notes

- **`new DateTime().Ticks` is always `0`.** `UpdatePictureUri` uses `new DateTime()` (the default struct, equivalent to `DateTime.MinValue`) rather than `DateTime.UtcNow`. This means `new DateTime().Ticks == 0` always — the query string `?0` is not a cache-busting timestamp, it is a literal zero. This appears to be a latent bug; the intent was likely `DateTime.UtcNow.Ticks`. The Java target should decide whether to preserve `?0` for DB/response compatibility or use a real timestamp.

- **No FK validation in code.** `catalogBrandId` and `catalogTypeId` are written directly to the entity. If they reference non-existent `CatalogBrands` or `CatalogTypes` rows, EF Core will throw a `DbUpdateException` (FK constraint violation) at `AddAsync`, propagating as HTTP 500. The Java target should validate these exist or let the DB constraint produce a clear error — but return 400, not 500.

- **Name-uniqueness check is not atomic.** The COUNT query and INSERT are not in a single transaction in the legacy implementation. A race condition could allow two concurrent requests with the same name to both pass the count check before either inserts. If DB uniqueness constraint is applied, the second INSERT would fail with a 500 rather than a 409. The Java target should add a unique index and handle `DataIntegrityViolationException` as 409 in addition to the pre-check.

- **`[Authorize]` on the lambda, not on the class.** Unlike ASP.NET MVC controllers where `[Authorize]` can be placed on the class, here it is placed on the lambda expression inside `AddRoute()`. The Java `@PreAuthorize` equivalent should be placed on the handler method.

- **`PictureBase64` and `PictureName` are in the DTO but never read.** They are deserialized into the request object but no code path references them. The Java request DTO can omit them entirely or keep them as `@JsonIgnore`-d fields for backward compatibility with BlazorAdmin clients that send them.

- **`CatalogItemDto` fields**: The 7 fields in the response DTO are: `Id`, `Name`, `Description`, `Price`, `PictureUri`, `CatalogTypeId`, `CatalogBrandId`. No `PictureBase64`, `PictureName`, or `PictureFileName` fields — the response DTO is narrower than the request DTO.
