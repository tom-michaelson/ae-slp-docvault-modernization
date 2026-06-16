# Functional Description: Update basket item quantities

> **Entry Point**: `update-item-in-basket`
> **Location**: `src/ApplicationCore/Services/BasketService.cs`
> **Type**: API / In-process Service
> **Domain**: basket
> **Legacy method**: `Microsoft.eShopWeb.ApplicationCore.Services.BasketService.SetQuantities`
> **Web handler**: `Microsoft.eShopWeb.Web.Pages.Basket.IndexModel.OnPostUpdate`

## Executive Summary

The `update-item-in-basket` endpoint applies a partial quantity update to the items in a basket. It is called by the Angular basket view when the user edits item quantities and submits the "Update" form. The caller supplies a list of `{ basketItemId, quantity }` pairs; only the items listed are modified — items in the basket but absent from the request are left unchanged. Setting any item's quantity to zero removes it from the basket.

The key implementation detail is that this is a **patch**, not a replace: `SetQuantities` iterates the basket's existing items and updates only those whose `BasketItem.Id` appears in the provided dictionary. Items not mentioned are silently skipped. After all quantities are applied, `Basket.RemoveEmptyItems()` purges any item with `Quantity == 0` from the in-memory collection, and a single `UpdateAsync` call flushes both the UPDATEs and DELETEs to the database.

The legacy web handler (`OnPostUpdate`) first resolves the basket ID by calling `GetOrCreateBasketForUser` — it never has the basket ID directly. The REST target accepts the basket ID directly as a path parameter, which eliminates this step and means the endpoint returns 404 if the basket does not exist rather than silently creating one.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | PUT |
| Path | `/api/baskets/{basketId}/items` |
| Auth required | no |

### Path Parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `basketId` | int | yes | `Baskets.Id` integer PK of the basket to update |

### Request Body

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `items` | array | yes | One or more `{ basketItemId, quantity }` pairs to apply |
| `items[].basketItemId` | int | yes | `BasketItems.Id` of the row to update — **not** `CatalogItem.Id` |
| `items[].quantity` | int | yes | New quantity. Must be `≥ 0`. `0` removes the item. Negative values return 400. |

Request body example:

```json
{
  "items": [
    { "basketItemId": 12, "quantity": 2 },
    { "basketItemId": 15, "quantity": 0 }
  ]
}
```

> **Partial update semantics.** Items in the basket whose `BasketItem.Id` does not appear in the request body are left exactly as they are. This is NOT a replace-all operation — only the listed items are touched.

### Success Response

HTTP 200 OK with the updated basket state after the changes are applied:

```json
{
  "basketId": 7,
  "buyerId": "alice@example.com",
  "items": [
    {
      "basketItemId": 12,
      "catalogItemId": 3,
      "unitPrice": 19.50,
      "quantity": 2
    }
  ]
}
```

Item 15 (set to `quantity=0`) is absent from the response because it was deleted by `RemoveEmptyItems()`.

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 404 | Basket not found (`basketId` does not exist in `Baskets`) | empty |
| 400 | Negative quantity in request body (`Guard.Against.OutOfRange` in `BasketItem.SetQuantity`) | empty or validation problem |

---

## Business Logic

### Overview

`SetQuantities` loads the basket (with its items) by integer ID, applies a dictionary of `BasketItem.Id → newQuantity` patches in a single loop, removes zero-quantity items, then persists the result. The operation is idempotent with respect to the items provided — applying the same quantities twice produces the same state.

The partial-update contract requires the Java target to support a basket that has more items than the request body. If a basket has items A, B, and C, and only A is in the request, then B and C must remain unchanged after the call.

The `Basket.RemoveEmptyItems()` mechanism means zero and deletion are the same operation from the caller's perspective: send `quantity=0` and the item disappears from the basket. There is no separate "delete item" path for this endpoint.

### Validation Rules

| Field / Condition | Rule | Failure behavior |
| --- | --- | --- |
| `basketId` (path) | Must match an existing `Baskets.Id` | `Result<Basket>.NotFound()` → REST target: 404 |
| `items[].quantity` | `≥ 0` (int) | `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)` in `BasketItem.SetQuantity` → throws `ArgumentOutOfRangeException` → REST target: 400 |
| `items[].basketItemId` | Must reference an item in the specified basket | Items not found in the basket's collection are silently ignored (no error) |
| `ModelState.IsValid` | Checked in legacy `OnPostUpdate` | Legacy: return without changes (silent); Java: return 400 |

### Call Sequence

1. **`OnPostUpdate` pre-call (web handler — replaced by REST path param):**
   - Check `ModelState.IsValid` → return without changes if false
   - `GetOrCreateBasketForUser(username)` → resolve `basketView.Id` (creates basket if absent for user)
   - Build `Dictionary<string, int>` from posted `items.Id.ToString() → items.Quantity`
   - Call `BasketService.SetQuantities(basketView.Id, quantities)`

2. **`SetQuantities` service method:**
   1. `new BasketWithItemsSpecification(basketId)` — spec filters `WHERE Baskets.Id = basketId` + `INCLUDE BasketItems`
   2. `IRepository<Basket>.FirstOrDefaultAsync(spec)` → loads basket with all its items
   3. If basket is null → return `Result<Basket>.NotFound()` — **REST target: return 404**
   4. For each `BasketItem` in `basket.Items`:
      - `quantities.TryGetValue(item.Id.ToString(), ...)` — if the item's ID is in the dictionary, call `item.SetQuantity(quantity)`
      - If the item's ID is NOT in the dictionary → skip it entirely (partial update)
   5. `basket.RemoveEmptyItems()` → `_items.RemoveAll(i => i.Quantity == 0)` — purges zero-quantity items from the in-memory collection
   6. `IRepository<Basket>.UpdateAsync(basket)` → EF Core flushes:
      - UPDATE `BasketItems` for each item whose quantity changed to a non-zero value
      - DELETE `BasketItems` for each item removed by `RemoveEmptyItems`
   7. Return `basket` (success result)

3. **`OnPostUpdate` post-call (web handler — replaced by REST response):**
   - `_basketViewModelService.Map(basket)` → maps `Basket` entity to `BasketViewModel` for view rendering
   - Re-renders the basket page with updated quantities

---

## Component Details

### In-process Service

**Service class**: `BasketService`
**Service file**: `src/ApplicationCore/Services/BasketService.cs`
**Method signature**: `Task<Result<Basket>> SetQuantities(int basketId, Dictionary<string, int> quantities)`

**Called from web handler**: `IndexModel.OnPostUpdate`
**Web handler file**: `src/Web/Pages/Basket/Index.cshtml.cs`

**What `IndexModel.OnPostUpdate` does BEFORE calling the service:**
1. Checks `ModelState.IsValid` — returns without any changes if invalid (silent no-op for invalid model state; Java: return 400)
2. Calls `_basketViewModelService.GetOrCreateBasketForUser(GetOrSetBasketCookieAndUserName())` — resolves the basket ID from the authenticated user's identity or anonymous cookie; creates a basket if none exists
3. Builds `Dictionary<string, int> updateModel` from the posted `BasketItemViewModel` items: `item.Id.ToString() → item.Quantity`
4. Calls `BasketService.SetQuantities(basketView.Id, updateModel)` — note that the basket ID is a resolved `int`; the dictionary keys are string representations of `BasketItem.Id` values (not `CatalogItem.Id`)

**What `IndexModel.OnPostUpdate` does AFTER the service call:**
- `_basketViewModelService.Map(basket)` — maps the returned `Basket` entity to a `BasketViewModel` for page rendering
- Re-renders the page in-place (no redirect — NOT a Post-Redirect-Get)

> The Java REST handler must:
> 1. Accept `basketId` from the path parameter (no prior `GetOrCreateBasketForUser` lookup needed)
> 2. Accept `items[].basketItemId` as `int` directly (not `string`) — convert to `String.valueOf(basketItemId)` only when calling the equivalent service logic, or refactor the dictionary to use `int` keys
> 3. Return 404 when `SetQuantities` returns `NotFound`
> 4. Return 200 with `BasketResponse` (the updated basket state) on success

**Service method signature detail:**
- `Dictionary<string, int> quantities` — keys are `BasketItem.Id.ToString()` in the legacy caller. The Java service layer may use `Map<Integer, Integer>` directly and avoid the string conversion.

**`BasketItem.SetQuantity` (domain method):**
```csharp
public void SetQuantity(int quantity)
{
    Guard.Against.OutOfRange(quantity, nameof(quantity), 0, int.MaxValue);
    Quantity = quantity;
}
```
Throws `ArgumentOutOfRangeException` for any `quantity < 0`. The Java target should catch this (or validate at the controller layer with `@Min(0)`) and return HTTP 400.

**`Basket.RemoveEmptyItems` (domain method):**
```csharp
public void RemoveEmptyItems()
{
    _items.RemoveAll(i => i.Quantity == 0);
}
```
Removes all `BasketItem` objects with `Quantity == 0` from the private `_items` list. EF Core change tracking converts these in-memory removals into `DELETE BasketItems WHERE Id = ?` statements during the subsequent `UpdateAsync`. Java: equivalent JPA behavior requires `cascade = CascadeType.ALL` + `orphanRemoval = true` on the `@OneToMany` relationship, or explicit `em.remove()` calls.

**Return value:** `Task<Result<Basket>>` — either `Result<Basket>.NotFound()` (basket absent) or the `Basket` entity wrapped as a success result.

**Legacy view model shapes** (informational — not the REST response model):
- `BasketViewModel`: `{ Id (int), BuyerId (string?), Items (List<BasketItemViewModel>) }`
- `BasketItemViewModel`: `{ Id (int), CatalogItemId (int), ProductName (string?), UnitPrice (decimal), OldUnitPrice (decimal), Quantity (int), PictureUrl (string?) }`

The REST target's `BasketResponse` is a subset of these fields: `{ basketId, buyerId, items[{ basketItemId, catalogItemId, unitPrice, quantity }] }`. Fields like `ProductName`, `OldUnitPrice`, and `PictureUrl` from the legacy view model are NOT included in the REST response.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `Baskets` | SELECT | `Id`, `BuyerId` | Loaded by integer PK via `BasketWithItemsSpecification`; `BuyerId` needed for the response; basket row itself is not mutated |
| `BasketItems` | SELECT, UPDATE, DELETE | `Id`, `BasketId`, `CatalogItemId`, `UnitPrice`, `Quantity` | Loaded via eager Include; UPDATE for quantity changes; DELETE for items set to zero (via EF Core cascade from `RemoveEmptyItems`) |

---

## Security Considerations

### Authentication

- **Required**: no — the endpoint has no JWT requirement in the legacy implementation.
- **Basket ownership**: not enforced at the service layer — the caller must ensure they own the basket. The legacy web layer enforces ownership implicitly: `GetOrCreateBasketForUser` ties the basket to the current user's identity (cookie or auth name). The REST target should enforce basket ownership at the controller layer — the Java handler should verify that the authenticated user (or cookie user) owns the basket with the given `basketId` before processing the update.

### Input Validation

- `items[].quantity`: `Guard.Against.OutOfRange` enforces `≥ 0` in the domain layer. The Java target should add `@Min(0)` on the DTO field to return HTTP 400 before the domain layer is reached.
- `items[].basketItemId`: If a `basketItemId` in the request body does not match any item in the basket, it is silently ignored. No validation error is raised for unknown basket item IDs.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Single batch flush | All quantity changes and deletions are applied in one `UpdateAsync` call — single EF Core unit-of-work | Java: wrap in a single transaction; do not issue individual UPDATE/DELETE per item |
| Eager load | `BasketWithItemsSpecification` always loads all `BasketItems` for the basket | Acceptable for typical basket sizes (< 50 items); no optimization needed |
| In-memory filtering | `quantities.TryGetValue(item.Id.ToString(), ...)` iterates all basket items for each `UpdateAsync` | O(n) where n = basket items; negligible |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| Basket ID resolution | `OnPostUpdate` calls `GetOrCreateBasketForUser` to get the basket ID; creates basket if absent | Java: accept `basketId` as path param; return 404 if basket absent — do not create |
| Dictionary key type | `Dictionary<string, int>` — keys are `BasketItem.Id.ToString()` | Java: use `Map<Integer, Integer>` internally; no string conversion needed |
| `items[].basketItemId` vs `CatalogItemId` | Dictionary key is `BasketItem.Id` (row PK in `BasketItems`), NOT `CatalogItem.Id` | Java: deserialize as `BasketItem.Id`; do not confuse with `CatalogItemId` |
| Partial update semantics | Items absent from the dictionary are skipped unchanged | Java: implement as a patch; do not replace all items with only those in the request |
| Zero = delete | `quantity=0` sets the quantity then `RemoveEmptyItems` deletes the item | Java: `orphanRemoval=true` on the `@OneToMany` or explicit repository delete |
| `Result<Basket>.NotFound()` | Service returns a result object; caller implicit-casts to `Basket` | Java: check for not-found explicitly; return HTTP 404 |
| No auth enforcement in service | Service does not verify basket ownership | Java controller must verify the requesting user owns the basket before calling the service |
| `ModelState.IsValid` check | Silent no-op on invalid model state in `OnPostUpdate` (returns page without changes) | Java: return HTTP 400 with validation details |
| Response shape | Legacy re-renders a Razor Page with `BasketViewModel` (includes `ProductName`, `OldUnitPrice`, `PictureUrl`) | Java REST response (`BasketResponse`) is a subset: only `basketId`, `buyerId`, `items[{ basketItemId, catalogItemId, unitPrice, quantity }]` |

---

## Analysis Notes

- **`BasketItemId` vs `CatalogItemId` confusion**: The dictionary key is `BasketItem.Id` (the row PK in the `BasketItems` table), NOT `CatalogItem.Id`. The legacy `OnPostUpdate` builds the dictionary as `items.ToDictionary(b => b.Id.ToString(), ...)` where `b.Id` is `BasketItemViewModel.Id` = `BasketItem.Id`. A Java developer who conflates these two IDs will update the wrong items or fail to find any.
- **Silent ignore for unknown basket item IDs**: `quantities.TryGetValue(item.Id.ToString(), ...)` — if the caller sends a `basketItemId` that does not exist in the basket, it is simply not matched during the iteration and no error is raised. The Java target should replicate this silent-ignore behavior.
- **`OnPostUpdate` does NOT redirect**: Unlike most POST handlers in this codebase, `OnPostUpdate` re-renders the page directly without a `RedirectToPage()`. This means a browser back-button press after updating will replay the POST. The REST target does not have this concern since Angular handles the navigation.
- **Implicit `Result<T> → T` cast in legacy**: `OnPostUpdate` calls `_basketViewModelService.Map(basket)` where `basket` is `Result<Basket>`. Ardalis.Result provides an implicit operator from `Result<T>` to `T`. If `basket.IsNotFound`, the implicit cast returns `null` and `Map(null)` would throw a NullReferenceException. This is a latent bug — in practice it doesn't trigger because `GetOrCreateBasketForUser` (called just before `SetQuantities`) guarantees the basket exists. The REST target avoids this entirely by checking the result explicitly and returning 404.
- **`UnitPrice` is immutable**: `BasketItem.SetQuantity` only mutates `Quantity`. The `UnitPrice` (the price recorded at add-to-basket time) is never changed by this endpoint — the price at checkout reflects the price at the time the item was first added.
- **No catalog lookup**: Unlike `add-item-to-basket`, this endpoint does not touch the `Catalog` table at all. No price revalidation occurs — the existing `UnitPrice` on each `BasketItem` is preserved.
