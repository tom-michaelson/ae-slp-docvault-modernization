# Functional Description: Delete basket (clear after checkout)

> **Entry Point**: delete-item-in-basket
> **Location**: src/ApplicationCore/Services/BasketService.cs
> **Type**: API / In-process Service
> **Domain**: basket
> **Legacy method**: Microsoft.eShopWeb.ApplicationCore.Services.BasketService.DeleteBasketAsync
> **Web handler**: Microsoft.eShopWeb.Web.Pages.Basket.CheckoutModel.OnPost

## Executive Summary

The `delete-item-in-basket` endpoint permanently deletes a basket and all its items. It is the final step in the three-call checkout sequence (update quantities → create order → delete basket). The Angular checkout component calls it only after receiving a successful order creation response — never as a standalone user-initiated action. The basket is purged atomically: the `Baskets` row and all its child `BasketItems` rows are deleted in a single `DeleteAsync` call via EF Core cascade.

The service method is simple — load by integer PK, guard against null, delete — but has one critical behavioral gap: if the basket is not found, `Guard.Against.Null` throws `ArgumentNullException`, which `CheckoutModel.OnPost` does not catch, propagating as HTTP 500. The Java REST target must explicitly check and return 404 for a missing basket. On success the legacy service returns `Task` (void); the REST target should return HTTP 204 No Content.

The metadata marks auth as "none" because the service method itself has no auth guard — authentication is enforced at the Razor Page layer via `[Authorize]` on `CheckoutModel`. For the REST target, JWT authentication must be required at the controller level. The endpoint is never called if order creation fails (the `EmptyBasketOnCheckoutException` catch block redirects without reaching `DeleteBasketAsync`).

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | DELETE |
| Path | `/api/baskets/{basketId}` |
| Auth required | yes — JWT Bearer (required at controller layer; not enforced by the service method) |

### Path Parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `basketId` | int | yes | `Baskets.Id` integer PK of the basket to delete |

No request body. No query parameters.

### Success Response

HTTP 204 No Content (no body).

Legacy `DeleteBasketAsync` returns `Task` (void).

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 401 | JWT absent or invalid | empty |
| 404 | No `Baskets` row found for `basketId` | empty (legacy: unhandled `ArgumentNullException` → HTTP 500) |
| 500 | Unhandled exception | empty |

---

## Business Logic

### Overview

The service fetches the `Basket` row by its integer primary key using `GetByIdAsync` — this is a direct PK lookup with no `Specification` and no eager loading of `BasketItems`. If the row is not found, an `ArgumentNullException` is thrown. If found, `DeleteAsync` is called, which EF Core executes as a DELETE on the `Baskets` row; the EF Core cascade-delete configuration then automatically removes all associated `BasketItems` rows in the same operation.

The `BasketItems` are never loaded into memory — the cascade is handled at the database level by EF Core's FK/cascade configuration. The Java target must replicate this cascade behavior, either via JPA `@OneToMany(cascade = CascadeType.REMOVE, orphanRemoval = true)` on the `Basket` entity or by executing a `DELETE FROM basket_items WHERE basket_id = ?` before deleting the basket row.

The operation is not called if order creation failed — the caller (`CheckoutModel.OnPost`) only reaches `DeleteBasketAsync` after `CreateOrderAsync` succeeds. If checkout fails with `EmptyBasketOnCheckoutException`, the handler redirects to `/Basket/Index` and the basket is left intact. The REST caller (Angular checkout service) must observe the same conditional: only call this endpoint after receiving a 201 from the `create-order` endpoint.

### Validation Rules

| Condition | Rule | Failure behavior |
| --- | --- | --- |
| `basketId` not found | `Guard.Against.Null(basket)` → `ArgumentNullException` | Legacy: unhandled → HTTP 500. Java: return HTTP 404 |

No other server-side validation — `basketId` is passed directly to `GetByIdAsync`.

### Call Sequence

**Web handler context (`CheckoutModel.OnPost` — step 3):**
1. `SetQuantities(BasketModel.Id, updateModel)` — first, quantities are synced (separate prior call)
2. `CreateOrderAsync(BasketModel.Id, hardcoded address)` — then, order is created (separate prior call)
3. **`DeleteBasketAsync(BasketModel.Id)`** ← this endpoint (only reached on successful order creation)
4. If `EmptyBasketOnCheckoutException` is thrown at step 2 → redirect to `/Basket/Index`; `DeleteBasketAsync` is NOT called
5. On success → `RedirectToPage("Success")`

**Service method (`BasketService.DeleteBasketAsync`):**
1. Receive `basketId` (int)
2. `IRepository<Basket>.GetByIdAsync(basketId)` → SELECT `Baskets` WHERE `Id = basketId`; no items eager-loaded
   - Returns null if row not found
3. `Guard.Against.Null(basket, nameof(basket))` → throws `ArgumentNullException` if null
4. `IRepository<Basket>.DeleteAsync(basket)` → DELETE `Baskets` WHERE `Id = basketId`; EF Core cascade deletes all `BasketItems` rows for this basket

---

## Component Details

### Service Method

**Class**: `BasketService`
**File**: `src/ApplicationCore/Services/BasketService.cs`
**Method signature**: `Task DeleteBasketAsync(int basketId)`

**Injected services**: `IRepository<Basket>`, `IAppLogger<BasketService>`

**Returns**: `Task` (void) — the REST target should return HTTP 204 No Content.

**Key implementation detail**: `GetByIdAsync(basketId)` uses the integer PK overload directly — it does NOT use `BasketWithItemsSpecification`. The `BasketItems` rows are never loaded into the application's in-memory collection; their deletion is handled entirely by EF Core's cascade-delete behavior based on the FK relationship defined in the schema.

---

### Web Handler (`CheckoutModel.OnPost`)

**File**: `src/Web/Pages/Basket/Checkout.cshtml.cs`
**Auth**: `[Authorize]` on the `CheckoutModel` class — all handlers require authentication.

**What `OnPost` does BEFORE calling `DeleteBasketAsync`:**
1. `SetBasketModelAsync()` — resolves authenticated username and loads `BasketModel`
2. `SetQuantities(BasketModel.Id, updateModel)` — syncs basket quantities from posted form
3. `CreateOrderAsync(BasketModel.Id, new Address("123 Main St.", ...))` — creates the order

**`DeleteBasketAsync` is only reached if `CreateOrderAsync` succeeds.**

**What `OnPost` does AFTER `DeleteBasketAsync`:**
- `RedirectToPage("Success")` → GET `/Basket/Checkout/Success`

**Exception handling relevant to this endpoint:**
- `EmptyBasketOnCheckoutException` (from `CreateOrderAsync`) → caught → redirect to `/Basket/Index` → `DeleteBasketAsync` NOT called
- `ArgumentNullException` (from `Guard.Against.Null` inside `DeleteBasketAsync`) → NOT caught → HTTP 500

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `Baskets` | SELECT, DELETE | `Id`, `BuyerId` | SELECT by integer PK (no Specification, no Items include); DELETE cascades to child BasketItems rows |
| `BasketItems` | DELETE | `Id`, `BasketId`, `CatalogItemId`, `UnitPrice`, `Quantity` | Deleted via EF Core cascade — never loaded into memory; no explicit query issued |

---

## Security Considerations

### Authentication

- **Service method has no auth guard.** The legacy service (`BasketService.DeleteBasketAsync`) does not check authentication — it trusts that the caller has already been authenticated.
- **Web handler is `[Authorize]`.** `CheckoutModel` requires authentication at the page level — so in practice this service is always called by an authenticated user.
- **Metadata notes `auth: "none"`** — this reflects the service layer only. For the REST target, JWT authentication must be enforced at the controller/handler level.
- **Java target must**: add `@PreAuthorize("isAuthenticated()")` or configure JWT filter chain for `DELETE /api/baskets/{basketId}`.

### Input Validation

- No validation on `basketId` beyond the null guard after lookup. A `basketId` of `0` or a negative integer will attempt `GetByIdAsync`, find nothing, and throw `ArgumentNullException` → 500 (legacy). Java target may add `@Positive` on `basketId` to return 400.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| No items loaded | `GetByIdAsync` does not load `BasketItems` — no eager join | Java: `findById(basketId)` without fetching items; rely on cascade delete |
| Cascade delete | EF Core deletes all `BasketItems` via DB cascade in same transaction as parent | Java: configure `@OneToMany(cascade = CascadeType.REMOVE, orphanRemoval = true)` or issue explicit `deleteByBasketId` before deleting basket |
| No `Task.Delay` | No artificial delay | N/A |
| No AutoMapper | No DTO — returns void | Java: return `ResponseEntity.noContent().build()` (HTTP 204) |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| HTTP response | `Task` (void) — web handler redirects after success | Java: `ResponseEntity.noContent().build()` → HTTP 204 No Content |
| Missing basket | `Guard.Against.Null` → `ArgumentNullException` → HTTP 500 (unhandled) | Java: `Optional.empty()` from `findById` → return `ResponseEntity.notFound()` (HTTP 404) |
| Auth | `[Authorize]` on Razor Page class; service has no auth guard | Java: require JWT at `@DeleteMapping` handler; service method has no auth check |
| Cascade delete | EF Core cascade-deletes `BasketItems` automatically | Java: `@OneToMany(cascade = CascadeType.REMOVE, orphanRemoval = true)` on `Basket.items`; or `basketItemRepository.deleteByBasketId(basketId)` before `basketRepository.deleteById(basketId)` |
| No items loaded before delete | `GetByIdAsync` (plain PK lookup, no includes) then `DeleteAsync` | Java: `deleteById(basketId)` or load + delete; either works if cascade is configured |
| Checkout sequence position | Step 3 — only called after `CreateOrderAsync` succeeds | Angular client must sequence: `update-item-in-basket` → `create-order` → this endpoint; must NOT call on order failure |

---

## Analysis Notes

- **Auth mismatch between service and caller.** The service has no auth guard, but the web handler is `[Authorize]`. The REST target must add auth at the controller layer — not the service layer. This is the same pattern as `create-order`.

- **Cascade delete is implicit.** The `BasketItems` rows are removed by EF Core's cascade configuration, not by explicit code in `DeleteBasketAsync`. The Java target must verify that `@OneToMany(cascade = CascadeType.REMOVE, orphanRemoval = true)` is configured on `Basket.items`, or implement an explicit delete query. If neither is done, the Java delete will fail with a FK constraint violation (the `Baskets` row references `BasketItems` via the `basket_id` FK column).

- **Not idempotent.** A second DELETE for the same `basketId` returns 404 (basket already gone). The Angular checkout flow should not retry this call — if the basket is gone, the checkout is already complete.

- **Called only on checkout success.** The Angular checkout service must only invoke this endpoint after `create-order` returns HTTP 201. If `create-order` fails (422 empty basket, 404 basket not found), this endpoint must NOT be called. If it is called after a partial failure, the basket is deleted but no order exists — the user loses their basket without getting an order.

- **`basketId` is the integer PK, not `buyerId`.** The caller must have already resolved the basket's integer `Id` from the `BasketModel` — the REST target does not accept a buyer username or GUID here. The Angular client must store the basket's `id` from a prior `get-basket-for-user` call and use it here.

- **Empty basket deletion is valid.** There is no guard against deleting a basket with zero items (the `EmptyBasketOnCheckoutException` guard is in `OrderService.CreateOrderAsync`, not in `DeleteBasketAsync`). A basket with no items can be deleted successfully.
