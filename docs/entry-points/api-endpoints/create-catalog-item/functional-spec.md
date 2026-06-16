# Functional spec — Create catalog item

**Key:** `create-catalog-item`
**Legacy:** `CreateCatalogItemEndpoint.HandleAsync` — `POST api/catalog-items`
**Target REST:** `POST /api/catalog-items`

## Purpose

Creates a new catalog item and returns its persisted representation. The BlazorAdmin create modal calls this endpoint when an administrator submits the "Create New" form; in the Angular 19 rebuild the admin create dialog component will call it the same way.

## Inputs

Request body (JSON):

| Name | Type | Optional | Default | Notes |
|---|---|---|---|---|
| `catalogBrandId` | int | no | — | Foreign key to CatalogBrands. |
| `catalogTypeId` | int | no | — | Foreign key to CatalogTypes. |
| `description` | string | no | — | Free-text description of the item. |
| `name` | string | no | — | Display name. Must be unique across all existing CatalogItems (exact, case-sensitive match). |
| `price` | decimal | no | — | Unit price. |
| `pictureUri` | string | yes | — | Accepted but **ignored** — immediately overwritten with default placeholder after insert. |
| `pictureBase64` | string | yes | — | Accepted but **ignored** — image upload is disabled. |
| `pictureName` | string | yes | — | Accepted but **ignored** — image upload is disabled. |

Authentication: `Authorization: Bearer <jwt>` header required. Token must carry role `Administrators`.

## Outputs

HTTP 201 Created with `Location: api/catalog-items/{id}` header and body:

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
  }
}
```

HTTP 409 Conflict when a CatalogItem with the same `name` already exists:

```json
{
  "statusCode": 409,
  "message": "A catalogItem with name New Product already exists"
}
```

HTTP 401 Unauthorized when no valid JWT is supplied.

HTTP 403 Forbidden when a valid JWT is supplied but the caller is not in the `Administrators` role.

## Acceptance criteria

```gherkin
Scenario: Happy path — new item created
  Given no CatalogItem with name "New Product" exists
  And the request carries a valid JWT for an Administrators user
  When POST /api/catalog-items with { name: "New Product", price: 29.99, ... }
  Then a new CatalogItems row is inserted
  And response status is 201 Created
  And response.catalogItem.id is the newly assigned primary key
  And response.catalogItem.pictureUri is an absolute URL containing "eCatalog-item-default.png"
  And the Location header is "api/catalog-items/{id}"

Scenario: Duplicate name — 409 returned
  Given a CatalogItem with name "Existing Product" already exists
  And the request carries a valid JWT for an Administrators user
  When POST /api/catalog-items with { name: "Existing Product", ... }
  Then no new CatalogItems row is inserted
  And response status is 409 Conflict
  And response body contains message "A catalogItem with name Existing Product already exists"

Scenario: Unauthenticated — 401 returned
  Given the request has no Authorization header
  When POST /api/catalog-items
  Then response status is 401 Unauthorized

Scenario: Wrong role — 403 returned
  Given the request carries a valid JWT for a non-Administrators user
  When POST /api/catalog-items
  Then response status is 403 Forbidden

Scenario: Picture upload fields are ignored
  Given a valid admin JWT
  When POST /api/catalog-items with { pictureUri: "custom.png", pictureBase64: "abc...", pictureName: "custom.png", ... }
  Then the persisted PictureUri is "images\products\eCatalog-item-default.png?{ticks}"
  And the response pictureUri is an absolute URL for the default placeholder, not "custom.png"
```

## Business rules

1. **Uniqueness check before insert**: `CatalogItemNameSpecification` counts rows WHERE `Name = request.Name`. If count > 0, `DuplicateException` is thrown, caught by `ExceptionMiddleware`, and returned as HTTP 409 Conflict. The Java target should return `409 Conflict` for the same condition.
2. **Image upload is disabled**: `PictureUri`, `PictureBase64`, and `PictureName` in the request are accepted but completely ignored. After insert, `CatalogItem.UpdatePictureUri("eCatalog-item-default.png")` always overwrites `PictureUri` to `images\products\eCatalog-item-default.png?{ticks}`. The Java target can skip the two-step insert+update by setting the default PictureUri before the initial INSERT.
3. **Two DB writes in legacy**: `AddAsync` (INSERT) followed by `UpdateAsync` (UPDATE for PictureUri). The Java port should consolidate into a single INSERT.
4. **`pictureUri` in response is an absolute URL**: `IUriComposer.ComposePicUri` rewrites the stored relative path. The Java target must apply the same transformation using a configurable base URL.
5. **Auth**: JWT Bearer, `Administrators` role (`BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS = "Administrators"`).
6. Returns **HTTP 201 Created** (not 200) with a `Location` header pointing to the new resource.

## Non-functional

- Mutating (INSERT + UPDATE on CatalogItems).
- JWT authentication required; `Administrators` role required.
- Called by BlazorAdmin on every "Create New" form submission — low frequency.
- `ExceptionMiddleware` in the PublicApi pipeline handles `DuplicateException` → 409 and all other exceptions → 500. The Java target should mirror this exception-to-status-code mapping.
