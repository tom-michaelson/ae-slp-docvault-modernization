# Functional spec — Delete catalog item

**Key:** `delete-catalog-item`
**Legacy:** `DeleteCatalogItemEndpoint.HandleAsync` — `DELETE api/catalog-items/{catalogItemId}`
**Target REST:** `DELETE /api/catalog-items/{catalogItemId}`

## Purpose

Permanently removes a catalog item by ID. The BlazorAdmin delete confirmation modal calls this endpoint when an administrator confirms the deletion; in the Angular 19 rebuild the admin delete dialog component will call it the same way.

## Inputs

| Name | Type | Optional | Default | Notes |
|---|---|---|---|---|
| `catalogItemId` | int | no | — | Path parameter. Primary key of the CatalogItems row to delete. |

No request body. Authentication: `Authorization: Bearer <jwt>` header required. Token must carry role `Administrators`.

## Outputs

HTTP 200 OK with body:

```json
{
  "status": "Deleted"
}
```

HTTP 404 Not Found (empty body) when no CatalogItems row exists for the given ID.

HTTP 401 Unauthorized when no valid JWT is supplied.

HTTP 403 Forbidden when the caller is not in the `Administrators` role.

## Acceptance criteria

```gherkin
Scenario: Happy path — item deleted
  Given a CatalogItem with Id=5 exists
  And the request carries a valid JWT for an Administrators user
  When DELETE /api/catalog-items/5
  Then the CatalogItems row with Id=5 is removed from the database
  And response status is 200 OK
  And response body is { "status": "Deleted" }

Scenario: Item not found — 404 returned
  Given no CatalogItem with Id=999 exists
  And the request carries a valid JWT for an Administrators user
  When DELETE /api/catalog-items/999
  Then no CatalogItems row is modified
  And response status is 404 Not Found

Scenario: Unauthenticated — 401 returned
  Given the request has no Authorization header
  When DELETE /api/catalog-items/5
  Then response status is 401 Unauthorized

Scenario: Wrong role — 403 returned
  Given the request carries a valid JWT for a non-Administrators user
  When DELETE /api/catalog-items/5
  Then response status is 403 Forbidden
```

## Business rules

1. **HTTP 200, not 204**: The endpoint returns `200 OK` with `{ "status": "Deleted" }` rather than the conventional `204 No Content`. The Java target should preserve this response shape for Angular client compatibility.
2. **Existence check before delete**: `GetByIdAsync` is called first; the delete only proceeds when the item is found. A missing item returns 404 — the operation is not idempotent in the "repeat-safe" sense.
3. **FK impact on BasketItems**: `BasketItems.CatalogItemId` references `CatalogItems.Id`. The endpoint itself has no cascade logic — the outcome depends on the database referential action configured on the schema. If RESTRICT is in effect, attempting to delete an item that is in an active basket will fail with a DB exception (caught by `ExceptionMiddleware` → HTTP 500). The Java target should verify and document this constraint behaviour.

## Non-functional

- Mutating (SELECT + DELETE on CatalogItems).
- JWT authentication required; `Administrators` role required.
- Called by BlazorAdmin on confirmed delete — low frequency.
- No business-logic side effects beyond removing the row; related `OrderItems` snapshots (`ItemOrdered_CatalogItemId`) are point-in-time copies and are not affected by this delete.
