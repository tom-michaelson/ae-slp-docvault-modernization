# Functional spec — List catalog items

**Key:** `list-catalog-items`
**Legacy:** `CatalogViewModelService.GetCatalogItems(pageIndex, itemsPage, brandId?, typeId?)`
**Target REST:** `GET /api/catalog-items?pageIndex&itemsPerPage&brandId&typeId`

## Purpose

Return a page of catalog items (optionally filtered by brand and/or type) plus the
metadata needed by the Angular homepage to render filter dropdowns and pagination.

## Inputs

| Name | Type | Optional | Default | Notes |
| --- | --- | --- | --- | --- |
| `pageIndex` | int | yes | 0 | 0-indexed |
| `itemsPerPage` | int | yes | 10 | Matches `Constants.ITEMS_PER_PAGE`. If `0`, treated as "all" (legacy `take = int.MaxValue`). |
| `brandId` | int? | yes | null | When set, filters by `Catalog.CatalogBrandId` |
| `typeId` | int? | yes | null | When set, filters by `Catalog.CatalogTypeId` |

## Outputs

```json
{
  "catalogItems": [
    {
      "id": 1,
      "name": ".NET Bot Black Sweatshirt",
      "pictureUri": "https://…/images/products/1.png",
      "price": 19.50
    }
  ],
  "brands": [
    {"value": null, "text": "All", "selected": true},
    {"value": "1", "text": ".NET"}
  ],
  "types": [
    {"value": null, "text": "All", "selected": true},
    {"value": "1", "text": "Mug"}
  ],
  "brandFilterApplied": 0,
  "typesFilterApplied": 0,
  "paginationInfo": {
    "actualPage": 0,
    "itemsPerPage": 10,
    "totalItems": 12,
    "totalPages": 2,
    "previous": "is-disabled",
    "next": ""
  }
}
```

## Acceptance criteria

```
Scenario: No filters, first page
  Given 12 catalog items exist
  When the client calls GET /api/catalog-items?pageIndex=0&itemsPerPage=10
  Then catalogItems.length == 10
  And paginationInfo.totalItems == 12
  And paginationInfo.totalPages == 2
  And paginationInfo.previous == "is-disabled"
  And paginationInfo.next == ""

Scenario: Filter by brand
  Given only 3 items match brandId=5
  When the client calls GET /api/catalog-items?brandId=5
  Then all 3 items are returned
  And paginationInfo.totalItems == 3

Scenario: Oversized page
  Given 5 items match a filter
  When the client calls GET /api/catalog-items?pageIndex=0&itemsPerPage=20
  Then 5 items are returned
  And paginationInfo.totalPages == 1

Scenario: PictureUri rewriting
  Given a CatalogItem with PictureUri "images/products/1.png"
  When the catalog is listed
  Then the response's pictureUri is a fully-qualified URL (UriComposer rewrites relative paths)
```

## Business rules

- `ITEMS_PER_PAGE` default is `10` (legacy `Constants.ITEMS_PER_PAGE`).
- `totalPages = ceil(totalItems / itemsPerPage)`.
- `previous == "is-disabled"` when `actualPage == 0`.
- `next == "is-disabled"` when `actualPage == totalPages - 1`.
- Brand/Type dropdowns always include a synthetic "All" option at the top, sorted
  alphabetically by text thereafter.

## Non-functional

- Read-only; no side effects.
- Expected call rate: hit on every homepage load and every filter/pagination change.
