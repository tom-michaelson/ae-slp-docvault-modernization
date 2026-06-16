# Functional spec — List catalog items (paginated)

**Key:** `list-catalog-items-paged`
**Legacy:** `CatalogItemListPagedEndpoint.HandleAsync` — `GET api/catalog-items`
**Target REST:** `GET /api/catalog-items`

## Purpose

Returns a paginated, optionally brand- and type-filtered page of catalog items. The BlazorAdmin panel calls this on list load; in the Angular 19 rebuild the catalog homepage component will also call it on every page load, filter change, and pagination change.

## Inputs

| Name | Type | Optional | Default | Notes |
|---|---|---|---|---|
| `pageSize` | int | yes | 0 | Items per page. When `0`, all matching items are returned (take = int.MaxValue). |
| `pageIndex` | int | yes | 0 | 0-indexed page number. Skip = pageIndex × pageSize. |
| `catalogBrandId` | int? | yes | null | Filters by `CatalogItems.CatalogBrandId`. Omit to return all brands. |
| `catalogTypeId` | int? | yes | null | Filters by `CatalogItems.CatalogTypeId`. Omit to return all types. |

## Outputs

```json
{
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

## Acceptance criteria

```gherkin
Scenario: No filters, first page
  Given 12 catalog items exist
  When GET /api/catalog-items?pageSize=10&pageIndex=0
  Then response.catalogItems.length == 10
  And response.pageCount == 2

Scenario: No filters, second page
  Given 12 catalog items exist
  When GET /api/catalog-items?pageSize=10&pageIndex=1
  Then response.catalogItems.length == 2
  And response.pageCount == 2

Scenario: pageSize=0 returns all items
  Given 12 catalog items exist
  When GET /api/catalog-items?pageSize=0
  Then response.catalogItems.length == 12
  And response.pageCount == 1

Scenario: pageSize=0 with empty catalog
  Given 0 catalog items exist
  When GET /api/catalog-items?pageSize=0
  Then response.catalogItems.length == 0
  And response.pageCount == 0

Scenario: Filter by brand
  Given only 3 items have catalogBrandId=5
  When GET /api/catalog-items?catalogBrandId=5
  Then response.catalogItems.length == 3
  And response.pageCount == 1

Scenario: Filter by type and brand combined
  Given 2 items match catalogBrandId=2 AND catalogTypeId=1
  When GET /api/catalog-items?catalogBrandId=2&catalogTypeId=1
  Then response.catalogItems.length == 2

Scenario: Filter returns no items
  Given no items match catalogBrandId=99
  When GET /api/catalog-items?catalogBrandId=99
  Then response.catalogItems.length == 0
  And response.pageCount == 0

Scenario: PictureUri is rewritten to absolute URL
  Given a CatalogItem with PictureUri "catalog-images/1.png"
  When GET /api/catalog-items is called
  Then response.catalogItems[0].pictureUri starts with "https://"
  And the relative path segment is preserved in the absolute URL
```

## Business rules

1. `pageCount = ceil(totalMatchingItems / pageSize)` when `pageSize > 0`.
2. When `pageSize == 0`: `pageCount = 1` if any matching items exist, `0` if none.
3. `skip = pageIndex * pageSize`. When `pageSize == 0`, skip is also `0`.
4. `pictureUri` is rewritten from the stored relative path to an absolute URL via `IUriComposer.ComposePicUri` — the Java target must apply the same transformation using a configurable base URL.
5. All seven `CatalogItemDto` fields are always returned — there is no field projection; the Java target should return the same set.
6. Filters are additive (AND): supplying both `catalogBrandId` and `catalogTypeId` returns only items matching both.

## Non-functional

- Read-only; no writes.
- No authentication required.
- Two sequential DB queries per request: one COUNT (for pageCount) and one SELECT (for the page data). The Java target may combine these into a single query with `Page<T>` if the framework supports it.
- **Do NOT port the `Task.Delay(1000)` artificial delay** present at the top of the legacy `HandleAsync` — it exists only as a demo of async loading spinners.
- Called on every admin list load and on every Angular homepage filter/pagination interaction — latency-sensitive.
