# Functional spec — Update catalog item

**Key:** `update-catalog-item`
**Legacy:** `UpdateCatalogItemEndpoint.HandleAsync` — `PUT api/catalog-items`
**Target REST:** `PUT /api/catalog-items` (legacy) → recommended `PUT /api/catalog-items/{id}` (Java target)

## Purpose

Updates the editable fields of an existing catalog item and returns its new state. The BlazorAdmin edit modal calls this endpoint when an administrator saves changes; in the Angular 19 rebuild the admin edit dialog component will call it the same way.

## Inputs

Request body (JSON):

| Name | Type | Optional | Default | Notes |
|---|---|---|---|---|
| `id` | int | no | — | Primary key of the item to update. Validated: range 1–10000. **Body parameter in legacy** — Java target should move this to a path parameter. |
| `catalogBrandId` | int | no | — | New brand. Validated: range 1–10000. |
| `catalogTypeId` | int | no | — | New type. Validated: range 1–10000. |
| `description` | string | no | — | New description. Must be non-null and non-empty. |
| `name` | string | no | — | New display name. Must be non-null and non-empty. |
| `price` | decimal | no | — | New unit price. Validated: range 0.01–10000. |
| `pictureUri` | string | yes | — | Accepted but **ignored** — PictureUri is not updated by this endpoint. |
| `pictureBase64` | string | yes | — | Accepted but **ignored** — image upload is disabled. |
| `pictureName` | string | yes | — | Accepted but **ignored** — image upload is disabled. |

Authentication: `Authorization: Bearer <jwt>` header required. Token must carry role `Administrators`.

## Outputs

HTTP 200 OK with body:

```json
{
  "catalogItem": {
    "id": 5,
    "name": "Updated Product Name",
    "description": "Updated description",
    "price": 24.99,
    "pictureUri": "https://host/catalog-images/eCatalog-item-default.png?0",
    "catalogTypeId": 3,
    "catalogBrandId": 2
  }
}
```

HTTP 404 Not Found (empty body) when no CatalogItems row exists for the given `id`.

HTTP 401 Unauthorized when no valid JWT is supplied.

HTTP 403 Forbidden when the caller is not in the `Administrators` role.

## Acceptance criteria

```gherkin
Scenario: Happy path — item updated
  Given a CatalogItem with Id=5 exists
  And the request carries a valid JWT for an Administrators user
  When PUT /api/catalog-items with { id: 5, name: "Updated", description: "New desc", price: 24.99, catalogBrandId: 2, catalogTypeId: 3 }
  Then the CatalogItems row for Id=5 has Name="Updated", Description="New desc", Price=24.99, CatalogBrandId=2, CatalogTypeId=3
  And response status is 200 OK
  And response.catalogItem reflects all five updated fields
  And response.catalogItem.pictureUri is an absolute URL (unchanged from stored value)

Scenario: Item not found — 404 returned
  Given no CatalogItem with Id=999 exists
  And the request carries a valid JWT for an Administrators user
  When PUT /api/catalog-items with { id: 999, ... }
  Then no CatalogItems row is modified
  And response status is 404 Not Found

Scenario: Picture fields are ignored
  Given a CatalogItem with Id=5 exists with PictureUri "eCatalog-item-default.png"
  And the request carries a valid JWT for an Administrators user
  When PUT /api/catalog-items with { id: 5, pictureUri: "custom.png", pictureBase64: "abc...", pictureName: "custom.png", ... }
  Then the CatalogItems row for Id=5 still has PictureUri = "eCatalog-item-default.png"
  And response.catalogItem.pictureUri is the absolute URL for the original stored PictureUri

Scenario: Unauthenticated — 401 returned
  Given the request has no Authorization header
  When PUT /api/catalog-items
  Then response status is 401 Unauthorized

Scenario: Wrong role — 403 returned
  Given the request carries a valid JWT for a non-Administrators user
  When PUT /api/catalog-items
  Then response status is 403 Forbidden
```

## Business rules

1. **Item ID in request body**: The legacy route is `PUT api/catalog-items` with no `{id}` path segment — `Id` comes from the JSON body. The Java target should use `PUT /api/catalog-items/{id}` for RESTful conformance and ignore any `id` field in the request body.
2. **PictureUri is never updated here**: `UpdateDetails` sets only Name, Description, and Price. `UpdateBrand` and `UpdateType` update their respective FK fields. PictureUri remains unchanged regardless of what the request body contains.
3. **Guard clauses are the runtime validation**: DataAnnotations on `UpdateCatalogItemRequest` (`[Range]`, `[Required]`) are not auto-enforced by MinimalApi. The Guard clauses inside the entity methods provide the actual runtime checks:
   - `Guard.Against.NullOrEmpty(Name)` / `Guard.Against.NullOrEmpty(Description)` — throw `ArgumentException`
   - `Guard.Against.NegativeOrZero(Price)` — throws if price ≤ 0
   - `Guard.Against.Zero(CatalogBrandId)` / `Guard.Against.Zero(CatalogTypeId)` — throw if 0
   If these throw, `ExceptionMiddleware` returns HTTP 500. The Java target should use `@Valid` on `@RequestBody` with Jakarta Bean Validation (mirroring the DataAnnotations constraints) to return HTTP 400 instead.
4. **No duplicate name check**: Unlike `create-catalog-item`, this endpoint does not verify uniqueness of the updated Name. The Java target should be consistent with this (no uniqueness check on update).
5. **Returns HTTP 200** (not 204) with the full updated `CatalogItemDto` in the response body.

## Non-functional

- Mutating (SELECT + UPDATE on CatalogItems).
- JWT authentication required; `Administrators` role required.
- Called by BlazorAdmin on every "Edit" form save — low frequency.
- `ExceptionMiddleware` handles `DuplicateException` → 409 and all other exceptions → 500. Guard clause failures produce 500 in legacy; the Java target should return 400 via Bean Validation instead.
