# Functional Description: Get catalog item by ID

> **Entry Point**: `get-catalog-item-byId`
> **Location**: `src/PublicApi/CatalogItemEndpoints/CatalogItemGetByIdEndpoint.cs`
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: `CatalogItemGetByIdEndpoint.HandleAsync`

## Executive Summary

The `get-catalog-item-byId` endpoint returns the full details for a single catalog item by its primary key. It is called by the BlazorAdmin `CatalogItemService` when loading an item for the edit or detail view, and will be called by the Angular 19 admin detail and edit components in the same way.

The endpoint is a simple primary-key lookup: a single `GetByIdAsync` call retrieves the `CatalogItem` row; if the row does not exist, HTTP 404 is returned immediately with an empty body. If the row is found, all seven fields are manually projected into a `CatalogItemDto` — unlike the list endpoint (`CatalogItemListPagedEndpoint`), **no AutoMapper is used here**; the fields are assigned one by one inline. The `PictureUri` is rewritten from its stored relative path to an absolute URL via `IUriComposer.ComposePicUri` during this construction.

No authentication is required and no artificial delay exists. This is the simplest endpoint in the catalog API: one DB round-trip, one possible early exit (404), one URI rewrite.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `api/catalog-items/{catalogItemId}` |
| Auth required | no |

### Path Parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `catalogItemId` | int | yes | Primary key of the `CatalogItems` row to fetch. Bound directly from the URL path segment |

### Success Response

HTTP 200 OK

```json
{
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "catalogItem": {
    "id": 5,
    "name": ".NET Bot Black Sweatshirt",
    "description": ".NET Bot Black Sweatshirt",
    "price": 19.50,
    "pictureUri": "https://host/catalog-images/5.png",
    "catalogTypeId": 2,
    "catalogBrandId": 1
  }
}
```

**Response fields:**

| Field | Type | Notes |
| --- | --- | --- |
| `correlationId` | Guid | From `BaseResponse` — propagated from `request.CorrelationId()`. Java: include only if keeping request-tracing semantics |
| `catalogItem` | object | The matched item. `null` / absent when 404 |
| `catalogItem.id` | int | `CatalogItem.Id` |
| `catalogItem.name` | string | `CatalogItem.Name` |
| `catalogItem.description` | string | `CatalogItem.Description` |
| `catalogItem.price` | decimal | `CatalogItem.Price` |
| `catalogItem.pictureUri` | string | Absolute URL — `IUriComposer.ComposePicUri(item.PictureUri)` applied inline |
| `catalogItem.catalogTypeId` | int | `CatalogItem.CatalogTypeId` |
| `catalogItem.catalogBrandId` | int | `CatalogItem.CatalogBrandId` |

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 404 Not Found | `GetByIdAsync` returns null — no `CatalogItems` row for the given ID | empty |

---

## Business Logic

### Overview

The request carries a single integer `catalogItemId` (path parameter). `HandleAsync` calls `IRepository<CatalogItem>.GetByIdAsync(catalogItemId)`, which issues a primary-key SELECT. If the result is null, the handler returns `Results.NotFound()` immediately — no further processing. If the item is found, a `CatalogItemDto` is constructed by assigning each of the seven entity fields directly (no mapping framework), with `PictureUri` composed to an absolute URL in the same step. The DTO is placed in the response object and returned as HTTP 200.

### Validation Rules

| Field / Condition | Rule | Legacy behavior | Java target |
| --- | --- | --- | --- |
| `catalogItemId` — not found | null result from `GetByIdAsync` | `Results.NotFound()` → HTTP 404 empty body | Same: return 404 |
| `catalogItemId` — invalid int | ASP.NET Minimal API route binding fails — 400 from framework | HTTP 400 (framework-level, before `HandleAsync`) | Spring: `@PathVariable int` binding failure → 400 automatically |
| `catalogItemId` — negative | No guard clause — negative IDs reach `GetByIdAsync`; no row exists; returns 404 | 404 Not Found | Same: 404 via natural miss |

### Call Sequence

1. **Initialise response** — `new GetByIdCatalogItemResponse(request.CorrelationId())`. Sets the correlation Guid from `BaseRequest`.
2. **Primary-key lookup** — `IRepository<CatalogItem>.GetByIdAsync(request.CatalogItemId)`:
   - Generates: `SELECT Id, Name, Description, Price, PictureUri, CatalogTypeId, CatalogBrandId FROM CatalogItems WHERE Id = {catalogItemId}` (single row; no specification class; EF Core primary key shortcut)
   - Returns: `CatalogItem` entity or `null`
3. **Null guard** — if `item is null`: return `Results.NotFound()` → HTTP 404 with empty body. Handler exits here.
4. **Manual DTO construction** — assign all seven fields inline:
   ```csharp
   response.CatalogItem = new CatalogItemDto
   {
       Id            = item.Id,
       CatalogBrandId = item.CatalogBrandId,
       CatalogTypeId  = item.CatalogTypeId,
       Description   = item.Description,
       Name          = item.Name,
       PictureUri    = _uriComposer.ComposePicUri(item.PictureUri),
       Price         = item.Price
   };
   ```
   `PictureUri` is composed to an absolute URL during this step.
5. **Return** — `Results.Ok(response)` → HTTP 200 with JSON body.

---

## Component Details

### MinimalApi.Endpoint

**Class**: `CatalogItemGetByIdEndpoint`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemGetByIdEndpoint.cs`
**Interface**: `IEndpoint<IResult, GetByIdCatalogItemRequest, IRepository<CatalogItem>>`

**Route registration (`AddRoute()`):**
```csharp
app.MapGet("api/catalog-items/{catalogItemId}",
    async (int catalogItemId, IRepository<CatalogItem> itemRepository) =>
    {
        return await HandleAsync(new GetByIdCatalogItemRequest(catalogItemId), itemRepository);
    })
    .Produces<GetByIdCatalogItemResponse>()
    .WithTags("CatalogItemEndpoints");
```

No `.RequireAuthorization()` — anonymous access permitted. No `.ProducesProblem(404)` declared (oversight in the legacy code — the 404 case is not advertised in OpenAPI metadata, but is returned at runtime).

**Injected constructor dependencies**: `IUriComposer`
**HandleAsync dependencies (via parameter)**: `IRepository<CatalogItem>` (injected by MinimalApi DI)

> **No AutoMapper**: Unlike `CatalogItemListPagedEndpoint`, this endpoint does not inject `IMapper`. The `CatalogItemDto` is built field-by-field. The Java target may use MapStruct or manual mapping — either is acceptable, but the field set must match exactly.

---

**Request type**: `GetByIdCatalogItemRequest`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemGetByIdEndpoint.GetByIdCatalogItemRequest.cs`
**Base**: `BaseRequest` (provides `CorrelationId()`)

| Property | C# Type | Notes |
| --- | --- | --- |
| `CatalogItemId` | `int` | Bound from `{catalogItemId}` path segment via constructor |

---

**Response type**: `GetByIdCatalogItemResponse`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemGetByIdEndpoint.GetByIdCatalogItemResponse.cs`
**Base**: `BaseResponse` (carries `CorrelationId` Guid)

| Property | C# Type | Notes |
| --- | --- | --- |
| `CatalogItem` | `CatalogItemDto` | Null when 404 path taken (but 404 exits before this property is serialised) |
| `CorrelationId` | Guid (from `BaseResponse`) | Request tracing identifier |

---

**DTO type**: `CatalogItemDto`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemDto.cs`
**Shared with**: `CatalogItemListPagedEndpoint`

| Property | C# Type | Source entity field | Notes |
| --- | --- | --- | --- |
| `Id` | `int` | `CatalogItem.Id` | |
| `Name` | `string` | `CatalogItem.Name` | |
| `Description` | `string` | `CatalogItem.Description` | |
| `Price` | `decimal` | `CatalogItem.Price` | |
| `PictureUri` | `string` | `CatalogItem.PictureUri` → rewritten to absolute URL | |
| `CatalogTypeId` | `int` | `CatalogItem.CatalogTypeId` | |
| `CatalogBrandId` | `int` | `CatalogItem.CatalogBrandId` | |

---

## Database Dependencies

| Table | Operations | Key columns used | Notes |
| --- | --- | --- | --- |
| `CatalogItems` | SELECT (by primary key) | `Id`, `Name`, `Description`, `Price`, `PictureUri`, `CatalogTypeId`, `CatalogBrandId` | Single row lookup via `GetByIdAsync` — no specification class; EF Core generates a primary-key WHERE clause directly |

---

## Security Considerations

### Authentication

- **Required**: No. `AddRoute()` does not call `.RequireAuthorization()`. The endpoint is publicly accessible.
- BlazorAdmin callers authenticate via the app's ASP.NET Identity session, but this is not enforced at the endpoint level. The Angular 19 admin components should send appropriate credentials if the endpoint is placed behind auth in the Java target.
- The Java Spring Boot target may choose to add `@PreAuthorize` or equivalent if admin-only access is required, but this would be a behavioural change from the legacy.

### Input Validation

- The only input is `catalogItemId` (int). ASP.NET route binding rejects non-integer path values with HTTP 400 before `HandleAsync` runs — the Java target gets the same behaviour automatically via Spring's `@PathVariable int` binding.
- No guard clause against zero or negative IDs — they are accepted and result in a natural 404 (no row has Id ≤ 0 in the seeded data).
- No SQL injection risk — EF Core uses parameterised primary key queries.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| No `Task.Delay` | Unlike the list endpoint, no artificial delay is present | Nothing to remove |
| Single primary-key lookup | `GetByIdAsync` is an EF Core primary-key shortcut — most efficient possible DB read | Java: use `findById(id)` on a JPA repository; same O(1) lookup |
| No AutoMapper | DTO is manually constructed — no reflection overhead | Java: manual DTO constructor or MapStruct — either is fine for a single object |
| One DB round-trip | Only one query; no second COUNT query | No optimisation needed |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| `pictureUri` rewriting | `_uriComposer.ComposePicUri(item.PictureUri)` rewrites relative path to absolute URL during DTO construction | Java: apply equivalent URI composition; use a configurable `catalog.baseUrl` property |
| No AutoMapper | `CatalogItemDto` fields are assigned one by one — no mapping framework | Java: construct DTO manually or use MapStruct; must include all 7 fields |
| 404 on null | `if (item is null) return Results.NotFound()` — empty body | Java: return `ResponseEntity.notFound().build()` or throw a `ResponseStatusException(HttpStatus.NOT_FOUND)` |
| `correlationId` in response | `BaseResponse` includes a Guid propagated from the request | Java: include or omit as decided for the project; confirm with Angular team |
| No auth | Publicly accessible | Keep unauthenticated unless a specific requirement is added |
| Path param name | `catalogItemId` in path template and in `GetByIdCatalogItemRequest.CatalogItemId` | Java: `@PathVariable("catalogItemId") int catalogItemId` — keep the same URL path variable name |
| Response wrapper | Item is under `catalogItem` key: `{ "catalogItem": { ... } }` — NOT a bare object | Java response DTO must wrap the item under a `catalogItem` field, not return the DTO directly |

---

## Analysis Notes

- **Response shape wraps the item**: the response is `{ "correlationId": "...", "catalogItem": { ... } }`, not `{ "id": ..., "name": ... }`. The Java `@RestController` method must return a wrapper object with a `catalogItem` field — not the DTO directly. This is easy to miss.

- **`ProducesProblem(404)` not declared**: the `AddRoute()` call includes `.Produces<GetByIdCatalogItemResponse>()` but does not declare `.ProducesProblem(404)`. The 404 is returned at runtime but is absent from the OpenAPI schema. The Java target's `@ApiResponse(responseCode = "404")` annotation should document this case explicitly.

- **`CatalogItemDto` is shared with the list endpoint**: both `CatalogItemGetByIdEndpoint` and `CatalogItemListPagedEndpoint` use the same `CatalogItemDto` class. The Java target's shared DTO record/class should be designed to serve both endpoints — confirm the field set is identical (it is: 7 fields).

- **`GetByIdAsync` vs `FirstOrDefaultAsync(spec)`**: this endpoint uses the repository's `GetByIdAsync` primitive (EF Core primary-key shortcut), not an `Ardalis.Specification`. No `Specification` class is involved. The Java target can use `findById(id)` directly on the JPA repository — no need for a custom query.

- **`CatalogItem.PictureUri` is a relative path in the DB**: the stored value is something like `catalog-images/5.png` (without a leading slash or host). `IUriComposer.ComposePicUri` prepends the configured base URL. The Java target must not return the raw stored value.

- **No `description` truncation or projection**: the full `Description` string is returned as-is. There is no length cap or HTML sanitisation in the legacy code.
