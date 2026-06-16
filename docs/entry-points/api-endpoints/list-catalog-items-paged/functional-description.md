# Functional Description: List catalog items (paginated)

> **Entry Point**: `list-catalog-items-paged`
> **Location**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs`
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: `CatalogItemListPagedEndpoint.HandleAsync`

## Executive Summary

The `list-catalog-items-paged` endpoint returns a paginated, optionally filtered page of catalog items from the eShopOnWeb store. It is the primary data source for the BlazorAdmin catalog management list and will be the source for the Angular 19 homepage catalog component on every initial load, filter change, and pagination interaction.

The endpoint performs two sequential database queries: a COUNT (using `CatalogFilterSpecification`) to compute the total number of matching items and derive `pageCount`, followed by a paginated SELECT (using `CatalogFilterPaginatedSpecification`) for the actual current-page rows. When `pageSize=0`, a special "return all" mode is activated: the `take` parameter is rewritten to `int.MaxValue` inside `CatalogFilterPaginatedSpecification`, and `pageCount` is set to `1` (items present) or `0` (empty catalog). Each returned item's `PictureUri` is rewritten from its stored relative path to an absolute URL via `IUriComposer.ComposePicUri`, applied after AutoMapper mapping on the DTO. No authentication is required.

A deliberate `await Task.Delay(1000)` exists at the very start of `HandleAsync` as a demo animation aid. This **must not** be ported to the Java target under any circumstances. Apart from that delay, the endpoint is entirely read-only and stateless.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `api/catalog-items` |
| Auth required | no |

### Query Parameters

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `pageSize` | int | no | 0 | Items per page. `null` is normalised to `0` in `ListPagedCatalogItemRequest`. When `0`, all matching items are returned (take = `int.MaxValue`) |
| `pageIndex` | int | no | 0 | 0-indexed page number. `null` is normalised to `0`. `skip = pageIndex × pageSize` |
| `catalogBrandId` | int? | no | null (no filter) | Filters by `CatalogItems.CatalogBrandId`; omit to include all brands |
| `catalogTypeId` | int? | no | null (no filter) | Filters by `CatalogItems.CatalogTypeId`; omit to include all types |

### Success Response

HTTP 200 OK

```json
{
  "correlationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "pageCount": 2,
  "catalogItems": [
    {
      "id": 1,
      "name": ".NET Bot Black Sweatshirt",
      "description": ".NET Bot Black Sweatshirt",
      "price": 19.50,
      "pictureUri": "https://host/catalog-images/1.png",
      "catalogTypeId": 2,
      "catalogBrandId": 1
    }
  ]
}
```

**Response fields:**

| Field | Type | Notes |
| --- | --- | --- |
| `correlationId` | Guid | From `BaseResponse` — propagated from `request.CorrelationId()`. Java: include only if keeping request-tracing semantics; otherwise omit |
| `pageCount` | int | Total number of pages. `ceil(totalItems / pageSize)` when `pageSize > 0`; `1` when `pageSize=0` and items exist; `0` when `pageSize=0` and no items |
| `catalogItems` | `List<CatalogItemDto>` | Array of items on the current page. Empty array when no items match or page is out of range |
| `catalogItems[].id` | int | `CatalogItem.Id` |
| `catalogItems[].name` | string | `CatalogItem.Name` |
| `catalogItems[].description` | string | `CatalogItem.Description` |
| `catalogItems[].price` | decimal | `CatalogItem.Price` |
| `catalogItems[].pictureUri` | string | Absolute URL — relative `PictureUri` rewritten by `IUriComposer.ComposePicUri` |
| `catalogItems[].catalogTypeId` | int | `CatalogItem.CatalogTypeId` |
| `catalogItems[].catalogBrandId` | int | `CatalogItem.CatalogBrandId` |

### Error Responses

| Status | Condition |
| --- | --- |
| *(none defined)* | The legacy endpoint has no explicit error paths — all inputs default gracefully (null → 0, empty filter → all). Guard clauses on the repository are not present in this endpoint. |

---

## Business Logic

### Overview

The endpoint accepts optional `catalogBrandId` and/or `catalogTypeId` filters. Both are independent and additive: if both are supplied, only items matching both are returned. If neither is supplied, all catalog items are in scope.

Two queries are issued against `CatalogItems`. The first (`CountAsync`) counts all matching rows to calculate `pageCount`. The second (`ListAsync`) retrieves the specific page of rows using `.Skip(skip).Take(take)`. The order of fields in the response always matches the full `CatalogItemDto` projection — there is no field-level filtering.

After `ListAsync`, AutoMapper maps each `CatalogItem` entity to `CatalogItemDto`. Then, in a separate pass, each DTO's `PictureUri` is rewritten from a relative storage path (e.g., `catalog-images/1.png`) to an absolute URL by `IUriComposer.ComposePicUri`. The absolute form is what the response always carries — relative paths are never returned to callers.

### Validation Rules

| Field / Condition | Rule | Legacy behavior | Java target |
| --- | --- | --- | --- |
| `pageSize` | null → normalised to `0` | `pageSize ?? 0` in `ListPagedCatalogItemRequest` constructor | Accept null/absent; treat as 0 |
| `pageIndex` | null → normalised to `0` | `pageIndex ?? 0` in constructor | Accept null/absent; treat as 0 |
| `catalogBrandId` | null = no brand filter | Optional; omitted from WHERE clause when null | Same |
| `catalogTypeId` | null = no type filter | Optional; omitted from WHERE clause when null | Same |
| Negative `pageSize` / `pageIndex` | No guard clause in endpoint | Would produce a negative skip/take, which EF Core may reject at DB level | Add explicit validation: return 400 if negative |

> **Note**: The legacy endpoint has **no guard clauses** for negative values — `Guard.Against.Negative` is not called here, unlike some other endpoints. A negative `pageSize` or `pageIndex` would reach the specification constructor and could cause an EF Core exception (500). The Java target should explicitly return HTTP 400 for negative values.

### Call Sequence

1. **Artificial delay** — `await Task.Delay(1000)`. **DO NOT PORT.**
2. **Initialise response** — `new ListPagedCatalogItemResponse(request.CorrelationId())`. Sets the correlation GUID for request tracing.
3. **Build count specification** — `new CatalogFilterSpecification(request.CatalogBrandId, request.CatalogTypeId)`:
   ```sql
   WHERE (brandId IS NULL OR CatalogBrandId = brandId)
     AND (typeId IS NULL  OR CatalogTypeId = typeId)
   ```
4. **COUNT query** — `IRepository<CatalogItem>.CountAsync(filterSpec)` → `totalItems` (int). This is a full-table scan of matching rows — no pagination applied.
5. **Build paginated specification** — `new CatalogFilterPaginatedSpecification(skip: pageIndex * pageSize, take: pageSize, brandId, typeId)`:
   - If `take == 0`: rewritten to `int.MaxValue` inside the constructor — returns all matching rows.
   - Same WHERE clause as step 3 plus `.Skip(skip).Take(take)`.
6. **SELECT query** — `IRepository<CatalogItem>.ListAsync(pagedSpec)` → `IList<CatalogItem>` for current page.
7. **AutoMapper projection** — `items.Select(_mapper.Map<CatalogItemDto>)` → `List<CatalogItemDto>` added to `response.CatalogItems`. Maps all 7 fields: `Id`, `Name`, `Description`, `Price`, `PictureUri`, `CatalogTypeId`, `CatalogBrandId`.
8. **URI rewriting** — For each `CatalogItemDto` in `response.CatalogItems`: `item.PictureUri = _uriComposer.ComposePicUri(item.PictureUri)`. Called on the DTO's `PictureUri` after mapping, not on the entity.
9. **Compute `pageCount`**:
   - If `pageSize > 0`: `pageCount = (int)Math.Ceiling((decimal)totalItems / pageSize)`. Legacy uses `int.Parse(Math.Ceiling(...).ToString())` — equivalent but roundabout.
   - If `pageSize == 0`: `pageCount = totalItems > 0 ? 1 : 0`.
10. **Return** — `Results.Ok(response)` → HTTP 200.

---

## Component Details

### MinimalApi.Endpoint

**Class**: `CatalogItemListPagedEndpoint`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs`
**Interface**: `IEndpoint<IResult, ListPagedCatalogItemRequest, IRepository<CatalogItem>>`

**Route registration (`AddRoute()`):**
```csharp
app.MapGet("api/catalog-items",
    async (int? pageSize, int? pageIndex, int? catalogBrandId, int? catalogTypeId,
           IRepository<CatalogItem> itemRepository) =>
    {
        return await HandleAsync(
            new ListPagedCatalogItemRequest(pageSize, pageIndex, catalogBrandId, catalogTypeId),
            itemRepository);
    })
    .Produces<ListPagedCatalogItemResponse>()
    .WithTags("CatalogItemEndpoints");
```

No `.RequireAuthorization()` — anonymous access is explicitly permitted.

**Injected constructor dependencies**: `IUriComposer`, `IMapper` (AutoMapper)
**HandleAsync dependencies (via parameter)**: `IRepository<CatalogItem>` (injected by MinimalApi DI)

---

**Request type**: `ListPagedCatalogItemRequest`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.ListPagedCatalogItemRequest.cs`
**Base**: `BaseRequest` (provides `CorrelationId()` method returning a Guid)

| Property | C# Type | Default | Notes |
| --- | --- | --- | --- |
| `PageSize` | `int` | 0 | `pageSize ?? 0` — null input normalised to 0 |
| `PageIndex` | `int` | 0 | `pageIndex ?? 0` — null input normalised to 0 |
| `CatalogBrandId` | `int?` | null | Optional brand filter |
| `CatalogTypeId` | `int?` | null | Optional type filter |

---

**Response type**: `ListPagedCatalogItemResponse`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.ListPagedCatalogItemResponse.cs`
**Base**: `BaseResponse` (carries `correlationId` Guid)

| Property | C# Type | Notes |
| --- | --- | --- |
| `CatalogItems` | `List<CatalogItemDto>` | Initialised to empty list; items added via `AddRange` |
| `PageCount` | `int` | Set after COUNT query |
| `CorrelationId` | Guid (from `BaseResponse`) | Request tracing identifier |

---

**DTO type**: `CatalogItemDto`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemDto.cs`

| Property | C# Type | Source entity field |
| --- | --- | --- |
| `Id` | `int` | `CatalogItem.Id` |
| `Name` | `string` | `CatalogItem.Name` |
| `Description` | `string` | `CatalogItem.Description` |
| `Price` | `decimal` | `CatalogItem.Price` |
| `PictureUri` | `string` | `CatalogItem.PictureUri` — rewritten to absolute URL after mapping |
| `CatalogTypeId` | `int` | `CatalogItem.CatalogTypeId` |
| `CatalogBrandId` | `int` | `CatalogItem.CatalogBrandId` |

---

**Specification: `CatalogFilterSpecification`**
**File**: `src/ApplicationCore/Specifications/CatalogFilterSpecification.cs`

```csharp
Query.Where(i =>
    (!brandId.HasValue || i.CatalogBrandId == brandId) &&
    (!typeId.HasValue || i.CatalogTypeId == typeId));
```

Used exclusively for the COUNT query. No `.Skip()`, `.Take()`, or ordering applied.

---

**Specification: `CatalogFilterPaginatedSpecification`**
**File**: `src/ApplicationCore/Specifications/CatalogFilterPaginatedSpecification.cs`

```csharp
if (take == 0) take = int.MaxValue;   // "return all" mode
Query
    .Where(i =>
        (!brandId.HasValue || i.CatalogBrandId == brandId) &&
        (!typeId.HasValue || i.CatalogTypeId == typeId))
    .Skip(skip)
    .Take(take);
```

Same WHERE predicate as `CatalogFilterSpecification` but adds `.Skip(skip).Take(take)`. When `take==0` (i.e., `pageSize=0`), `int.MaxValue` is used to return all rows. **No `ORDER BY` is applied** — row order depends on the database engine's default (typically primary key ascending in SQL Server / SQLite, but not guaranteed). The Java target should consider adding an explicit `ORDER BY Id ASC` for deterministic pagination.

---

## Database Dependencies

| Table | Operations | Key columns used | Notes |
| --- | --- | --- | --- |
| `CatalogItems` | COUNT, SELECT | `Id`, `Name`, `Description`, `Price`, `PictureUri`, `CatalogTypeId`, `CatalogBrandId` | COUNT issued first (no pagination) for `pageCount`; SELECT issued second with `.Skip().Take()` for current page data. Both queries use same WHERE predicate |

---

## Security Considerations

### Authentication

- **Required**: No. `AddRoute()` calls `.Produces<>()` but does not call `.RequireAuthorization()`. The endpoint is publicly accessible.
- The BlazorAdmin caller does authenticate separately, but authentication is not enforced at this endpoint. The Java Spring Boot target should keep the endpoint unauthenticated for the Angular catalog homepage use case, or add optional JWT auth if admin-only access is desired.

### Input Validation

- No guard clauses against negative integers — a negative `pageSize` or `pageIndex` reaches the database layer and may cause a runtime exception. Java target should validate: `pageSize >= 0`, `pageIndex >= 0`.
- No maximum `pageSize` cap — a caller can request `pageSize=1000000` and receive all rows. Java target should consider a configurable cap (e.g., `pageSize <= 500`).
- No SQL injection risk — Ardalis.Specification uses parameterised EF Core queries.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| `Task.Delay(1000)` | First line of `HandleAsync` — deliberate 1-second artificial delay | **Remove completely** — do not replicate in Java target |
| Two-round-trip queries | COUNT then SELECT are separate DB calls | Java: `Page<T>` from Spring Data JPA executes both in one call; acceptable. If keeping two separate queries, use the same WHERE predicate for both |
| AutoMapper projection | `_mapper.Map<CatalogItemDto>(item)` per result item — full entity loaded then projected | Java: use MapStruct or manual DTO constructor; project only the 7 `CatalogItemDto` fields; consider a `@Query` projection at the JPA level to avoid loading unused entity fields |
| URI rewriting per item | `IUriComposer.ComposePicUri` called in a foreach loop over every item in the response | Java: apply equivalent per-item URI composition; keep it simple (string concatenation of base URL + relative path) |
| No ordering | Neither specification applies `ORDER BY` — row order is non-deterministic | Java: add `ORDER BY id ASC` at the query level for deterministic pagination results |
| Called on every interaction | Invoked by Angular homepage on every load, filter change, and page flip | Ensure no N+1 queries are introduced; the current implementation is two flat queries |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| `Task.Delay(1000)` | First statement in `HandleAsync` — artificial delay for demo async spinner | **Remove** — do not port to Java |
| `pictureUri` rewriting | `IUriComposer.ComposePicUri(dto.PictureUri)` rewrites relative path to absolute URL using the app's configured base URL | Java: implement equivalent. Store relative paths in DB and compose absolute URL at response time using a configurable `catalog.baseUrl` property. Or store absolute URLs in the DB and skip composition |
| `pageSize=0` semantics | `CatalogFilterPaginatedSpecification` rewrites `take=0` to `take=int.MaxValue`; `pageCount` is set to `1` (items) or `0` (empty) | Preserve this behaviour exactly — BlazorAdmin calls the endpoint without `pageSize` (defaults to 0) to get all items |
| `pageCount` formula | `ceil(totalItems / pageSize)` for `pageSize > 0`; `1` or `0` for `pageSize=0` | Replicate exactly. Do not use Spring Data `Page.getTotalPages()` directly unless you verify it matches this formula for all edge cases |
| `pageCount` casting | Legacy uses `int.Parse(Math.Ceiling(...).ToString())` — roundabout but equivalent to `(int)Math.Ceiling(...)` | Java: use `(int) Math.ceil((double) totalItems / pageSize)` |
| `correlationId` in response | `BaseResponse` includes a `correlationId` Guid propagated from the request | Java: either include a request-trace UUID in the response, or omit it. Confirm with Angular team whether they consume this field |
| AutoMapper → 7 DTO fields | `CatalogItemDto` has exactly 7 fields: `id`, `name`, `description`, `price`, `pictureUri`, `catalogTypeId`, `catalogBrandId` | Java response DTO must expose exactly these 7 fields with these JSON names (camelCase). Do not add or remove fields without a consuming-client update |
| No `ORDER BY` | Current specs apply no ordering | Java: add `ORDER BY id ASC` for deterministic results — pagination without ordering produces unreliable page splits |
| No auth | Endpoint is publicly accessible | Keep unauthenticated unless explicit requirement added. Do not add `@PreAuthorize` or equivalent |
| Null query param handling | Null `pageSize` / `pageIndex` → 0 (in constructor) | Java: use `@RequestParam(defaultValue = "0")` or equivalent to normalise absent params to 0 |

---

## Analysis Notes

- **`pageCount` when `pageSize=0` and items exist**: returns `1`, not `ceil(12/maxInt) = 1`. This is semantically "one infinite page containing all items." The BlazorAdmin admin list relies on this when calling `GET /api/catalog-items` with no params — it expects all items and `pageCount=1`. The Java target must not change this.

- **`pageCount` when `pageSize=0` and catalog is empty**: returns `0`. A Java `Math.ceil(0 / MAX_VALUE)` also returns `0.0`, so this case is automatically consistent — but confirm your specific formula handles it.

- **`CatalogItemDto` does not include `CatalogBrandName` or `CatalogTypeName`**: only the ID references are returned. Callers that need the brand/type names must call the separate `list-catalog-brands` or `list-catalog-types` endpoints and join on the client.

- **`PictureUri` is rewritten on the DTO after AutoMapper**: `ComposePicUri` is called on `item.PictureUri` *after* mapping, meaning the AutoMapper profile maps the raw relative path and then it is overwritten. A Java equivalent that constructs the absolute URI during the mapping step (e.g., in a MapStruct `@AfterMapping`) is equally correct.

- **No `description` field filter in either Specification**: `Description` is stored in `CatalogItems` but is not filterable via this endpoint — it is only returned in the response.

- **BlazorAdmin vs Angular call patterns**: BlazorAdmin calls `GET /api/catalog-items?PageSize=10&PageIndex=0` for its paged list view, and `GET /api/catalog-items` (no params, `pageSize=0`) for bulk operations. The Angular 19 homepage component will use the paged form exclusively. Both call the same endpoint.

- **`int.MaxValue` as "take all"**: when `pageSize=0` → `take=int.MaxValue`, EF Core generates a `SELECT TOP 2147483647 ...` (SQL Server) or equivalent. This is not an issue with the current demo dataset (12 items) but would be significant at scale. The Java target might want to cap this at a configurable maximum (e.g., 10,000).

- **No `SELECT *`**: EF Core materialises the full `CatalogItem` entity, but AutoMapper only projects 7 of its fields into `CatalogItemDto`. A JPA `@Query` with a DTO constructor projection (`SELECT new CatalogItemDto(...)`) would be more efficient if `CatalogItem` has many columns not included in the DTO.
