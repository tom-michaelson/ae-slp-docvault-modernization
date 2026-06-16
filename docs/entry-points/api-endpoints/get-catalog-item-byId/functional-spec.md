# Functional spec — Get catalog item by ID

**Key:** `get-catalog-item-byId`
**Legacy:** `CatalogItemGetByIdEndpoint.HandleAsync` — `GET api/catalog-items/{catalogItemId}`
**Target REST:** `GET /api/catalog-items/{catalogItemId}`

## Purpose

Returns the full details for a single catalog item by its primary key. The BlazorAdmin panel calls this when loading an item for the edit or detail modal; in the Angular 19 rebuild the admin detail and edit components will call it the same way.

## Inputs

| Name | Type | Optional | Default | Notes |
|---|---|---|---|---|
| `catalogItemId` | int | no | — | Path parameter. The primary key of the CatalogItems row. |

## Outputs

HTTP 200 with body:

```json
{
  "catalogItem": {
    "id": 1,
    "name": ".NET Bot Black Sweatshirt",
    "description": ".NET Bot Black Sweatshirt",
    "price": 19.50,
    "pictureUri": "https://host/catalog-images/1.png",
    "catalogTypeId": 2,
    "catalogBrandId": 1
  }
}
```

HTTP 404 (empty body) when no CatalogItems row exists for the given ID.

## Acceptance criteria

```gherkin
Scenario: Item found
  Given a CatalogItem with Id=5 exists in the database
  When GET /api/catalog-items/5
  Then the response status is 200 OK
  And response.catalogItem.id == 5
  And all seven fields (id, name, description, price, pictureUri, catalogTypeId, catalogBrandId) are present
  And response.catalogItem.pictureUri is an absolute URL

Scenario: Item not found
  Given no CatalogItem with Id=999 exists
  When GET /api/catalog-items/999
  Then the response status is 404 Not Found
  And the response body is empty

Scenario: PictureUri is rewritten to absolute URL
  Given a CatalogItem with PictureUri "catalog-images/5.png"
  When GET /api/catalog-items/5
  Then response.catalogItem.pictureUri starts with "https://"
  And the relative path segment is preserved in the absolute URL
```

## Business rules

1. Returns `404 Not Found` immediately when `GetByIdAsync` returns null — no further processing occurs.
2. `pictureUri` is rewritten from the stored relative path to an absolute URL via `IUriComposer.ComposePicUri`. The Java target must apply the same transformation using a configurable base URL.
3. Unlike `CatalogItemListPagedEndpoint`, this endpoint constructs `CatalogItemDto` manually (no AutoMapper). The Java target may use MapStruct or manual mapping — either is correct.
4. All seven `CatalogItemDto` fields are always returned when the item is found — no field projection.

## Non-functional

- Read-only; no writes.
- No authentication required.
- Single primary-key lookup — constant time regardless of catalog size.
- No artificial delay (unlike the list endpoint).
