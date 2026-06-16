# Functional Description: Delete catalog item

> **Entry Point**: delete-catalog-item
> **Location**: src/PublicApi/CatalogItemEndpoints/DeleteCatalogItemEndpoint.cs
> **Type**: API / MinimalApi.Endpoint
> **Domain**: catalog
> **Legacy method**: Microsoft.eShopWeb.PublicApi.CatalogItemEndpoints.DeleteCatalogItemEndpoint.HandleAsync

## Executive Summary

The `delete-catalog-item` endpoint permanently removes a single catalog item by its primary key. It is called by the BlazorAdmin delete confirmation modal; in the Angular 19 rebuild the admin delete dialog component will call it the same way. Authentication is required — the caller must supply a JWT bearing the `Administrators` role.

The flow is two steps: lookup by ID, then delete. If no row is found, HTTP 404 is returned immediately without attempting a delete. On success, the endpoint returns HTTP 200 with body `{ "status": "Deleted" }` — not the more conventional HTTP 204 No Content. The Java target must preserve this response shape for Angular client compatibility.

There is no cascade logic in the endpoint itself. `BasketItems.CatalogItemId` references `CatalogItems.Id` — if the database enforces a RESTRICT constraint and the item is currently in an active basket, the DELETE will fail with a database exception, propagating as HTTP 500. `OrderItems.ItemOrdered_CatalogItemId` is a point-in-time snapshot column (not a live FK) — deleting a catalog item does not affect historical order records.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | DELETE |
| Path | `/api/catalog-items/{catalogItemId}` |
| Auth required | yes — JWT Bearer, `Administrators` role |

### Path Parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `catalogItemId` | int | yes | Primary key of the `CatalogItems` row to delete |

No request body. No query parameters.

### Success Response

HTTP 200 OK:

```json
{
  "status": "Deleted",
  "correlationId": "00000000-0000-0000-0000-000000000000"
}
```

Note: `correlationId` is the default empty Guid because the request object is constructed in the lambda from the path parameter only — no client-supplied correlation ID is possible on this endpoint.

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 401 | JWT absent or invalid | empty |
| 403 | JWT valid but caller not in `Administrators` role | empty |
| 404 | No `CatalogItems` row found for `catalogItemId` | empty |
| 500 | DB constraint violation (e.g., active basket items reference this catalog item) | empty |

---

## Business Logic

### Overview

The endpoint loads the `CatalogItem` by primary key. If the item does not exist, it returns 404 immediately. If the item is found, it is passed to `DeleteAsync` which issues a `DELETE WHERE Id = catalogItemId`. The response object is pre-populated with `Status = "Deleted"` and returned as `Results.Ok(response)` (HTTP 200).

The endpoint has no domain logic beyond the existence check — there are no guards, no aggregate methods, no business rules to enforce. The delete operation has no built-in safeguard against removing items that are currently in baskets. Whether this fails or succeeds depends entirely on the database referential action.

The operation is **not idempotent**: a second DELETE for the same ID returns 404, not 200.

### Validation Rules

| Condition | Rule | Failure behavior |
| --- | --- | --- |
| `catalogItemId` not found | `GetByIdAsync` returns null | `Results.NotFound()` → HTTP 404 (empty body) |
| `catalogItemId` referenced by `BasketItems` | No code check — DB constraint | FK violation → unhandled exception → HTTP 500 |

### Call Sequence

1. Receive `DELETE /api/catalog-items/{catalogItemId}` — `catalogItemId` bound as `int` from path
2. Lambda constructs `new DeleteCatalogItemRequest(catalogItemId)` and calls `HandleAsync`
3. Instantiate `new DeleteCatalogItemResponse(request.CorrelationId())` — `Status = "Deleted"`, `correlationId` = default Guid (empty)
4. `IRepository<CatalogItem>.GetByIdAsync(request.CatalogItemId)` → SELECT `CatalogItems` WHERE `Id = catalogItemId`
   - If null: `return Results.NotFound()` → HTTP 404 (no body)
5. `IRepository<CatalogItem>.DeleteAsync(itemToDelete)` → DELETE `CatalogItems` WHERE `Id = catalogItemId`
6. `return Results.Ok(response)` → HTTP 200 with `{ "status": "Deleted", "correlationId": "00000000-..." }`

---

## Component Details

### MinimalApi.Endpoint

**Class**: `DeleteCatalogItemEndpoint`
**File**: `src/PublicApi/CatalogItemEndpoints/DeleteCatalogItemEndpoint.cs`

**Route registration (`AddRoute()`):**
```csharp
app.MapDelete("api/catalog-items/{catalogItemId}",
    [Authorize(Roles = "Administrators", AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]
    async (int catalogItemId, IRepository<CatalogItem> itemRepository) =>
    {
        return await HandleAsync(new DeleteCatalogItemRequest(catalogItemId), itemRepository);
    })
    .Produces<DeleteCatalogItemResponse>()
    .WithTags("CatalogItemEndpoints");
```

Note: `catalogItemId` is bound directly from the path as `int` in the lambda — the `DeleteCatalogItemRequest` is constructed inline from it. No JSON body deserialization occurs. No `.ProducesProblem(401)` is declared; 401/403 are handled automatically by the `[Authorize]` attribute.

**Request type**: `DeleteCatalogItemRequest : BaseRequest`
**File**: `src/PublicApi/CatalogItemEndpoints/DeleteCatalogItemEndpoint.DeleteCatalogItemRequest.cs`
**Fields**: `CatalogItemId` (int, `init`-only — set via constructor `DeleteCatalogItemRequest(int catalogItemId)`)

**Response type**: `DeleteCatalogItemResponse : BaseResponse`
**File**: `src/PublicApi/CatalogItemEndpoints/DeleteCatalogItemEndpoint.DeleteCatalogItemResponse.cs`
**Fields**: `Status` (string, default `"Deleted"`), `CorrelationId` (Guid, inherited from `BaseResponse`, default empty Guid)

**Injected dependencies (constructor)**: none — `DeleteCatalogItemEndpoint` has no constructor-injected fields
**Injected dependencies (HandleAsync parameter)**: `IRepository<CatalogItem>` (from DI via MinimalApi parameter binding)

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `CatalogItems` | SELECT, DELETE | `Id` | SELECT by PK to confirm existence; DELETE by PK on found row |
| `BasketItems` | (indirect) | `CatalogItemId` (FK to `CatalogItems.Id`) | Not touched by this endpoint; FK constraint may prevent delete if active basket items reference this item |

---

## Security Considerations

### Authentication

- **Required**: yes — JWT Bearer token in `Authorization: Bearer {token}` header
- **Role required**: `Administrators` (`BlazorShared.Authorization.Constants.Roles.ADMINISTRATORS = "Administrators"`)
- **Enforcement**: `[Authorize(Roles = "Administrators", AuthenticationSchemes = JwtBearerDefaults.AuthenticationScheme)]` on the lambda in `AddRoute()`

### Input Validation

- No server-side validation on `catalogItemId` beyond existence check. A value of `0` or a negative integer would attempt a `GetByIdAsync` call and return 404 if not found.
- **Java target may add**: `@Positive` on `catalogItemId` path variable to return 400 for obviously invalid IDs before hitting the database.

### Cascade / Referential Integrity

- `BasketItems.CatalogItemId` references `CatalogItems.Id`. The referential action is defined in the migration schema. If `RESTRICT` (the EF Core default), a delete of an item in an active basket will throw a `DbUpdateException` → HTTP 500.
- `OrderItems.ItemOrdered_CatalogItemId` is a snapshot column stored as plain int — it has no FK constraint to `CatalogItems`. Deleting a catalog item will not affect existing order records.
- **Java target must**: verify the database FK constraint behavior and either: (a) reject the delete with a meaningful 409 Conflict if active basket items exist, or (b) cascade-delete or null-out the `BasketItems.CatalogItemId` reference before deleting.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Two-query pattern | SELECT by PK then DELETE — two round-trips | Java: `findById` + `delete` is standard; acceptable. Alternative: single `deleteById` that throws `EmptyResultDataAccessException` on miss |
| No `Task.Delay` | No artificial delay | N/A |
| No AutoMapper | Response constructed directly from `DeleteCatalogItemResponse` defaults | Java: manually set `status = "Deleted"` in response DTO |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| HTTP response code | `Results.Ok(response)` → HTTP 200 with body | Java: `ResponseEntity.ok(response)` — must be 200, NOT 204, for Angular client compatibility |
| Response body | `{ "status": "Deleted", "correlationId": "00000000-..." }` | Java: return same shape; `correlationId` may be omitted or echoed from request header if added later |
| Not idempotent | Second DELETE for same ID returns 404 | Java: same behavior — `findById` returns empty Optional → 404 |
| No cascade handling | DB constraint determines outcome for items in active baskets | Java: evaluate FK referential action; add explicit check + 409 if needed |
| Auth | `[Authorize(Roles = "Administrators")]` on lambda | Java: `@PreAuthorize("hasRole('ADMINISTRATORS')")` or Security filter chain |
| Path parameter binding | `int catalogItemId` bound from path; `DeleteCatalogItemRequest` constructed inline | Java: `@PathVariable int catalogItemId` bound in controller method |
| `correlationId` | Default empty Guid (client cannot supply it on DELETE with no body) | Java: `correlationId` can be omitted from response, or read from a request header (e.g., `X-Correlation-ID`) if tracing is added |

---

## Analysis Notes

- **HTTP 200 instead of 204 is intentional.** `Results.Ok(response)` returns a body with `{ "status": "Deleted" }`. This is non-standard for DELETE but the BlazorAdmin (and future Angular client) reads this response body. The Java target must return 200 with the body — not 204.

- **`correlationId` is always the empty Guid on this endpoint.** The `DeleteCatalogItemRequest` is constructed from the path parameter `int catalogItemId` only. There is no JSON body from which a client-supplied `correlationId` could be deserialized. The response will always include `"correlationId": "00000000-0000-0000-0000-000000000000"`. The Java target can either omit the field or derive a correlation ID from a request header.

- **Not idempotent.** A second DELETE for an already-deleted item returns 404. If the Angular checkout or admin flow retries on network error, it may incorrectly surface a 404 as an error even though the delete succeeded. The Java target could make this idempotent by returning 200 when the item is already gone — but that changes the legacy contract.

- **No `DeleteCatalogItemEndpoint` constructor.** Unlike `CreateCatalogItemEndpoint` (which injects `IUriComposer`), this endpoint has no constructor. `IRepository<CatalogItem>` is injected as a HandleAsync parameter via MinimalApi's DI binding.

- **`OrderItems.ItemOrdered_CatalogItemId` is safe.** This column stores the catalog item ID as a point-in-time snapshot — it has no FK constraint. Deleting a catalog item does not orphan or cascade to order history, which is the correct behavior for a historical record.

- **BasketItems FK risk.** If a user has the item in their basket when an admin deletes it, the next basket read may fail or surface a stale item (depending on query design). The Java target should decide whether to: (a) reject the delete with 409 if basket references exist, (b) silently remove basket references before deleting, or (c) accept the DB constraint failure as HTTP 500 (legacy behavior).
