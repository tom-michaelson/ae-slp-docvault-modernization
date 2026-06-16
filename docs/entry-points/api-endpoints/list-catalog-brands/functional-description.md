# Functional Description: List catalog brands

> **Entry Point**: `list-catalog-brands`
> **Location**: `src/PublicApi/CatalogBrandEndpoints/CatalogBrandListEndpoint.cs`
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: `Microsoft.eShopWeb.PublicApi.CatalogBrandEndpoints.CatalogBrandListEndpoint.HandleAsync`

## Executive Summary

The `list-catalog-brands` endpoint returns all brand names from the `CatalogBrands` table in a single unfiltered, unpaginated list. It is called by the Angular homepage to populate the brand filter dropdown that appears above the product grid.

The implementation is the simplest endpoint in the catalog surface: one `ListAsync()` call with no specification, no filtering, and no pagination. Every row in `CatalogBrands` is returned. The only non-trivial detail is an AutoMapper rename: the entity property `CatalogBrand.Brand` (a string) is mapped to `CatalogBrandDto.Name` in the response. Callers must use `name`, not `brand`, as the JSON field name.

No authentication is required and there are no guard clauses. The endpoint never returns a non-200 status in the success path — if `CatalogBrands` is empty, an empty list is returned rather than a 404.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `/api/catalog-brands` |
| Auth required | no |

### Query Parameters

None.

### Success Response

HTTP 200 OK:

```json
{
  "catalogBrands": [
    { "id": 1, "name": ".NET" },
    { "id": 2, "name": "Other" }
  ]
}
```

> **Field name is `name`, not `brand`.** The `CatalogBrands` table stores the brand string in a column named `Brand` (entity property `CatalogBrand.Brand`), but the AutoMapper `MappingProfile` renames it to `Name` in `CatalogBrandDto`. The JSON response always uses the key `"name"`.

### Error Responses

| Status | Condition |
| --- | --- |
| None expected | No guard clauses; empty table returns `{ "catalogBrands": [] }` with HTTP 200 |

---

## Business Logic

### Overview

The endpoint loads every row from `CatalogBrands` without filtering or pagination and maps each entity to a two-field DTO. There is no business logic beyond the full-table read and the field rename. The response wraps the list inside a `catalogBrands` envelope field inherited from `ListCatalogBrandsResponse`.

### Validation Rules

None. There are no request parameters to validate and no guard clauses in `HandleAsync`.

### Call Sequence

1. Receive request — no parameters.
2. `catalogBrandRepository.ListAsync()` (no specification) → returns all `CatalogBrand` rows ordered by the database's natural row order.
3. For each item: `_mapper.Map<CatalogBrandDto>(item)` → projects `{ Id, Brand }` to `{ Id, Name }` via AutoMapper (`Brand` → `Name` ForMember rule in `MappingProfile`).
4. Collect mapped DTOs into `response.CatalogBrands` via `AddRange`.
5. Return `Results.Ok(response)` → HTTP 200 with `ListCatalogBrandsResponse`.

---

## Component Details

### MinimalApi.Endpoint

**Class**: `CatalogBrandListEndpoint`
**File**: `src/PublicApi/CatalogBrandEndpoints/CatalogBrandListEndpoint.cs`

**Interface**: `IEndpoint<IResult, IRepository<CatalogBrand>>`

**Route registration (`AddRoute()`):**
```csharp
app.MapGet("api/catalog-brands",
    async (IRepository<CatalogBrand> catalogBrandRepository) =>
    {
        return await HandleAsync(catalogBrandRepository);
    })
   .Produces<ListCatalogBrandsResponse>()
   .WithTags("CatalogBrandEndpoints");
```

No `.RequireAuthorization()` — the route is fully public.

**Request type**: none (no request parameters or body).

**Response type**: `ListCatalogBrandsResponse`
**File**: `src/PublicApi/CatalogBrandEndpoints/CatalogBrandListEndpoint.ListCatalogBrandsResponse.cs`
**Fields**:
- `CatalogBrands` (`List<CatalogBrandDto>`) — the brand list; initialized to an empty list.
- (Inherited) `CorrelationId` (`Guid`) from `BaseResponse` — populated only when the `Guid` constructor overload is used; the no-arg constructor leaves it as `Guid.Empty`.

**DTO type**: `CatalogBrandDto`
**File**: `src/PublicApi/CatalogBrandEndpoints/CatalogBrandDto.cs`
**Fields**: `Id` (int), `Name` (string)

**Injected dependencies**: `IMapper` (AutoMapper — injected via constructor); `IRepository<CatalogBrand>` (resolved from the DI container and passed directly into `HandleAsync` by the MinimalApi lambda, not injected via constructor).

**AutoMapper mapping** (`src/PublicApi/MappingProfile.cs`):
```csharp
CreateMap<CatalogBrand, CatalogBrandDto>()
    .ForMember(dto => dto.Name, options => options.MapFrom(src => src.Brand));
```
The `CatalogBrand.Id` maps by convention; only `Brand` → `Name` requires an explicit rule.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `CatalogBrands` | SELECT | `Id`, `Brand` | Full-table read — no WHERE clause, no pagination. Returns rows in database natural order. |

---

## Security Considerations

### Authentication

- **Required**: no.
- No `[Authorize]` attribute, no `.RequireAuthorization()` call in `AddRoute()`, no JWT bearer requirement.
- The endpoint is fully public — callable without any token.

### Input Validation

No user-supplied parameters to validate.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Full-table scan | `ListAsync()` with no specification reads all rows | Acceptable — `CatalogBrands` is a small lookup table (typically < 50 rows); no pagination needed |
| Row ordering | No `ORDER BY` in the specification — order depends on storage/index order | Java: add `ORDER BY id ASC` (or `ORDER BY brand ASC`) if a stable order is required by the Angular dropdown |
| AutoMapper | `_mapper.Map<CatalogBrandDto>(item)` per row | Java: use MapStruct or manual projection; the only mapping rule is `Brand` → `Name` |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| Field rename `Brand` → `Name` | `MappingProfile` ForMember: `src.Brand` → `dto.Name` | Java DTO must serialize the field as `"name"` in JSON; the entity/table column is named `brand` |
| No `Task.Delay` | Not present in this endpoint | Nothing to remove |
| No `IUriComposer` | `CatalogBrand` has no picture URI | Nothing to rewrite |
| `CorrelationId` in response | `BaseResponse.CorrelationId` defaults to `Guid.Empty` when no-arg constructor used | Java: include `correlationId` as an empty UUID string (`"00000000-0000-0000-0000-000000000000"`) in the response body, or omit it — verify with Angular consumer |
| No pagination | All brands returned in one response | Java: do not add pagination; no `pageCount` field |
| No filtering | No query params accepted | Java: do not add brand-name filtering unless specified by the Angular team |

---

## Analysis Notes

- **`CorrelationId` field**: `ListCatalogBrandsResponse` extends `BaseResponse` which carries a `CorrelationId` (Guid). The no-arg constructor is used in `HandleAsync`, so `CorrelationId` will always be `Guid.Empty` (`00000000-0000-0000-0000-000000000000`) in the response. The Java target should include this field to preserve API shape compatibility, even though it carries no useful value.
- **Row ordering is non-deterministic**: The legacy `ListAsync()` issues a `SELECT * FROM CatalogBrands` with no `ORDER BY`. The Angular dropdown will display brands in whatever order the database returns them. If the product team wants alphabetical brand names, the Java target should add an explicit sort — the legacy code does not do this.
- **`CatalogBrand.Brand` private setter**: The entity has `public string Brand { get; private set; }` — only constructable via the `CatalogBrand(string brand)` constructor. No mutation methods exist. This is a read-only reference data entity; Java can model it as an immutable `@Entity` with no setters.
- **No companion `Request.cs` file**: Unlike endpoints such as `CatalogItemListPagedEndpoint`, this endpoint takes no request parameters and has no request type. The MinimalApi lambda's only parameter is the repository, injected from DI. The Java `@GetMapping` method signature will take no `@RequestParam` or `@RequestBody` arguments.
- **`WithTags("CatalogBrandEndpoints")`**: Sets the Swagger UI tag/group for this endpoint. Java: use `@Tag(name = "CatalogBrandEndpoints")` on the controller class if maintaining Swagger grouping parity.
