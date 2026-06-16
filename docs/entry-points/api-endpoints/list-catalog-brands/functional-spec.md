# Functional spec — List catalog brands

**Key:** `list-catalog-brands`
**Legacy:** `CatalogBrandListEndpoint.HandleAsync` — `GET api/catalog-brands`
**Target REST:** `GET /api/catalog-brands`

## Purpose

Returns the complete list of catalog brands. The BlazorAdmin create/edit modals call this to populate brand dropdown options; in the Angular 19 rebuild the admin form components will call it the same way. The Angular catalog filter panel may also call it to populate the brand filter dropdown.

## Inputs

None. No query parameters, no path parameters, no request body.

## Outputs

HTTP 200 OK with body:

```json
{
  "catalogBrands": [
    { "id": 1, "name": ".NET" },
    { "id": 2, "name": "Other" },
    { "id": 3, "name": "Roslyn" }
  ]
}
```

## Acceptance criteria

```gherkin
Scenario: Brands exist
  Given 3 CatalogBrand rows exist
  When GET /api/catalog-brands
  Then response status is 200 OK
  And response.catalogBrands.length == 3
  And each entry has an id (int) and a name (string)

Scenario: No brands in database
  Given the CatalogBrands table is empty
  When GET /api/catalog-brands
  Then response status is 200 OK
  And response.catalogBrands is an empty array []
```

## Business rules

1. **Full table scan, no pagination**: `ListAsync()` is called with no specification — all rows are returned in a single query. The Java target should implement the same (no paging).
2. **Property name rename**: The `CatalogBrand` entity stores the brand label in a property named `Brand`; the response DTO exposes it as `name`. The Java mapping must apply this rename (`brand.getBrand()` → `dto.setName(...)`).
3. **No authentication required**: The endpoint has no `[Authorize]` attribute and is publicly accessible.
4. **No `IUriComposer`**: CatalogBrands have no picture URI — no URL rewriting step.
5. **Result ordering**: The legacy `ListAsync()` applies no ORDER BY — the order is database-determined. The Java target may add `ORDER BY Id` for determinism if the Angular client requires a stable ordering.

## Non-functional

- Read-only; no writes.
- No authentication required.
- Returns the entire table on every call — suitable for a small reference dataset (typically fewer than 10 rows in eShopOnWeb seed data).
- Called by BlazorAdmin on form open and by Angular filter panel on page load — low to moderate frequency; response is a good candidate for short-lived server-side caching.
