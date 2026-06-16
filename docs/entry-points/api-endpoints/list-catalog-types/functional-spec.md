# Functional spec — List catalog types

**Key:** `list-catalog-types`
**Legacy:** `CatalogTypeListEndpoint.HandleAsync` — `GET api/catalog-types`
**Target REST:** `GET /api/catalog-types`

## Purpose

Returns the complete list of catalog types. The BlazorAdmin create/edit modals call this to populate type dropdown options; in the Angular 19 rebuild the admin form components will call it the same way. The Angular catalog filter panel may also call it to populate the type filter dropdown.

## Inputs

None. No query parameters, no path parameters, no request body.

## Outputs

HTTP 200 OK with body:

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

## Acceptance criteria

```gherkin
Scenario: Types exist
  Given 4 CatalogType rows exist
  When GET /api/catalog-types
  Then response status is 200 OK
  And response.catalogTypes.length == 4
  And each entry has an id (int) and a name (string)

Scenario: No types in database
  Given the CatalogTypes table is empty
  When GET /api/catalog-types
  Then response status is 200 OK
  And response.catalogTypes is an empty array []
```

## Business rules

1. **Full table scan, no pagination**: `ListAsync()` is called with no specification — all rows are returned in a single query. The Java target should implement the same (no paging).
2. **Property name rename**: The `CatalogType` entity stores the type label in a property named `Type`; the response DTO exposes it as `name`. The Java mapping must apply this rename (`type.getType()` → `dto.setName(...)`).
3. **No authentication required**: The endpoint has no `[Authorize]` attribute and is publicly accessible.
4. **No `IUriComposer`**: CatalogTypes have no picture URI — no URL rewriting step.
5. **Result ordering**: The legacy `ListAsync()` applies no ORDER BY — the order is database-determined. The Java target may add `ORDER BY Id` for determinism if the Angular client requires a stable ordering.

## Non-functional

- Read-only; no writes.
- No authentication required.
- Returns the entire table on every call — suitable for a small reference dataset (typically fewer than 10 rows in eShopOnWeb seed data).
- Called by BlazorAdmin on form open and by Angular filter panel on page load — low to moderate frequency; response is a good candidate for short-lived server-side caching.
- Structurally identical to `list-catalog-brands` — both return complete reference tables with an entity-property-to-`name` rename.
