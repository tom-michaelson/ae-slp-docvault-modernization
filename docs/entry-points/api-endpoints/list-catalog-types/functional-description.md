# Functional Description: List catalog types

> **Entry Point**: `list-catalog-types`
> **Location**: `src/PublicApi/CatalogTypeEndpoints/CatalogTypeListEndpoint.cs`
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: `Microsoft.eShopWeb.PublicApi.CatalogTypeEndpoints.CatalogTypeListEndpoint.HandleAsync`

## Executive Summary

The `list-catalog-types` endpoint returns the complete list of catalog types from the `CatalogTypes` table in a single unfiltered, unpaginated response. It is called by the BlazorAdmin create/edit item modals to populate the type dropdown, and by the Angular catalog filter panel to populate the type filter on the homepage.

The implementation is structurally identical to `list-catalog-brands`: one `ListAsync()` call with no specification, no filtering, and no pagination. The only notable detail is an AutoMapper rename — the entity property `CatalogType.Type` (a string) maps to `CatalogTypeDto.Name` in the response. Callers must use `"name"` as the JSON key, not `"type"`.

No authentication is required. There are no guard clauses or validation rules. An empty `CatalogTypes` table returns HTTP 200 with an empty `catalogTypes` array rather than a 404.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `/api/catalog-types` |
| Auth required | no |

### Query Parameters

None.

### Success Response

HTTP 200 OK:

```json
{
  "catalogTypes": [
    { "id": 1, "name": "Mug" },
    { "id": 2, "name": "T-Shirt" },
    { "id": 3, "name": "Sheet" },
    { "id": 4, "name": "USB Memory Stick" }
  ]
}
```

> **Field name is `name`, not `type`.** The `CatalogTypes` table stores the type label in a column named `Type` (entity property `CatalogType.Type`), but the AutoMapper `MappingProfile` renames it to `Name` in `CatalogTypeDto`. The JSON response always uses the key `"name"`.

### Error Responses

| Status | Condition |
| --- | --- |
| None expected | No guard clauses; empty table returns `{ "catalogTypes": [] }` with HTTP 200 |

---

## Business Logic

### Overview

The endpoint loads every row from `CatalogTypes` with no filtering or pagination and maps each entity to a two-field DTO. There is no business logic beyond the full-table read and the field rename. The response wraps the list in a `catalogTypes` envelope field from `ListCatalogTypesResponse`.

### Validation Rules

None. No request parameters exist to validate and `HandleAsync` contains no guard clauses.

### Call Sequence

1. Receive request — no parameters.
2. `catalogTypeRepository.ListAsync()` (no specification) → returns all `CatalogType` rows in database natural order.
3. For each item: `_mapper.Map<CatalogTypeDto>(item)` → projects `{ Id, Type }` to `{ Id, Name }` via AutoMapper (`Type` → `Name` ForMember rule in `MappingProfile`).
4. Collect mapped DTOs into `response.CatalogTypes` via `AddRange`.
5. Return `Results.Ok(response)` → HTTP 200 with `ListCatalogTypesResponse`.

---

## Component Details

### MinimalApi.Endpoint

**Class**: `CatalogTypeListEndpoint`
**File**: `src/PublicApi/CatalogTypeEndpoints/CatalogTypeListEndpoint.cs`

**Interface**: `IEndpoint<IResult, IRepository<CatalogType>>`

**Route registration (`AddRoute()`):**
```csharp
app.MapGet("api/catalog-types",
    async (IRepository<CatalogType> catalogTypeRepository) =>
    {
        return await HandleAsync(catalogTypeRepository);
    })
    .Produces<ListCatalogTypesResponse>()
    .WithTags("CatalogTypeEndpoints");
```

No `.RequireAuthorization()` — fully public.

**Request type**: none (no parameters of any kind).

**Response type**: `ListCatalogTypesResponse`
**File**: `src/PublicApi/CatalogTypeEndpoints/CatalogTypeListEndpoint.ListCatalogTypesResponse.cs`
**Fields**:
- `CatalogTypes` (`List<CatalogTypeDto>`) — the type list; initialized to an empty list.
- (Inherited) `CorrelationId` (`Guid`) from `BaseResponse` — always `Guid.Empty` when the no-arg constructor is used (as it is in `HandleAsync`).

**DTO type**: `CatalogTypeDto`
**File**: `src/PublicApi/CatalogTypeEndpoints/CatalogTypeDto.cs`
**Fields**: `Id` (int), `Name` (string)

**Injected dependencies**: `IMapper` (AutoMapper — injected via constructor); `IRepository<CatalogType>` (resolved from the DI container and passed directly into `HandleAsync` by the MinimalApi lambda, not via constructor).

**AutoMapper mapping** (`src/PublicApi/MappingProfile.cs`):
```csharp
CreateMap<CatalogType, CatalogTypeDto>()
    .ForMember(dto => dto.Name, options => options.MapFrom(src => src.Type));
```
`CatalogType.Id` maps by convention; only `Type` → `Name` requires an explicit rule.

**Entity**: `CatalogType`
**File**: `src/ApplicationCore/Entities/CatalogType.cs`
**Properties**: `Id` (inherited from `BaseEntity`), `Type` (string, `private set`) — constructable only via `CatalogType(string type)`. No mutation methods.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `CatalogTypes` | SELECT | `Id`, `Type` | Full-table read — no WHERE clause, no ORDER BY, no pagination. Returns rows in database natural order. |

---

## Security Considerations

### Authentication

- **Required**: no.
- No `[Authorize]` attribute and no `.RequireAuthorization()` call in `AddRoute()`.
- Fully public — callable without a JWT token.

### Input Validation

No user-supplied parameters exist to validate.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Full-table scan | `ListAsync()` with no specification reads all rows | Acceptable — `CatalogTypes` is a small reference table (4 rows in seed data); no pagination needed |
| Row ordering | No `ORDER BY` in the specification — order is database-determined | Java: add `ORDER BY id ASC` (or `ORDER BY type ASC`) if a stable order is required |
| AutoMapper | `_mapper.Map<CatalogTypeDto>(item)` per row | Java: use MapStruct or manual projection; only mapping rule is `Type` → `Name` |
| Caching candidate | Small, infrequently changing reference data called on every form open and page load | Java: consider `@Cacheable` with short TTL (e.g., 60 s); legacy has no caching |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| Field rename `Type` → `Name` | `MappingProfile` ForMember: `src.Type` → `dto.Name` | Java DTO must serialize the field as `"name"` in JSON; the entity/table column is named `type` |
| No `Task.Delay` | Not present in this endpoint | Nothing to remove |
| No `IUriComposer` | `CatalogType` has no picture URI | Nothing to rewrite |
| `CorrelationId` in response | `BaseResponse.CorrelationId` defaults to `Guid.Empty` when no-arg constructor used | Java: include `correlationId` as `"00000000-0000-0000-0000-000000000000"` or omit; verify with Angular consumer |
| No pagination | All types returned in one response | Java: do not add pagination |
| No filtering | No query params accepted | Java: do not add type-name filtering unless specified |

---

## Analysis Notes

- **Structurally identical to `list-catalog-brands`**: The two endpoints share the exact same pattern — `IEndpoint<IResult, IRepository<T>>`, `ListAsync()` with no spec, AutoMapper with a single ForMember rename. The only differences are the entity type (`CatalogType` vs `CatalogBrand`), the renamed property (`Type` vs `Brand`), and the envelope field name (`catalogTypes` vs `catalogBrands`). Java developers can implement both with the same controller pattern.
- **`CorrelationId` field**: Always `Guid.Empty` at runtime — same note as `list-catalog-brands`. Include it in the Java response shape for API compatibility.
- **Row ordering is non-deterministic**: `ListAsync()` issues no `ORDER BY`. If the Angular dropdown or BlazorAdmin form requires a stable ordering (alphabetical or by ID), the Java target should add an explicit sort clause. The legacy code does not.
- **`CatalogType.Type` private setter**: Only constructable via the `CatalogType(string type)` constructor — no setters exposed. Java can model this as an immutable `@Entity` with no setter for the `type` field.
- **Used by BlazorAdmin**: The `usedByUiFeatures` field in `metadata.json` is empty (`[]`), but both `functional-spec.md` and the metadata notes confirm BlazorAdmin calls this endpoint to populate the type dropdown in create/edit catalog item forms. The Angular filter panel also calls it. This usage pattern means the response must be consistently ordered relative to what BlazorAdmin expects — verify with the BlazorAdmin component.
- **No companion `Request.cs` file**: The MinimalApi lambda takes only the repository from DI. Java `@GetMapping` method needs no `@RequestParam` or `@RequestBody` arguments.
