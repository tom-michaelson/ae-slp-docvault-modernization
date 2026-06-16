# Functional Description: Add item to basket

> **Entry Point**: `add-item-to-basket`
> **Location**: `src/ApplicationCore/Services/BasketService.cs`
> **Type**: API / In-process Service
> **Domain**: basket
> **Legacy method**: `BasketService.AddItemToBasket`
> **Web handler**: `IndexModel.OnPost` (`src/Web/Pages/Basket/Index.cshtml.cs`)

## Executive Summary

The `add-item-to-basket` operation adds a catalog item to a buyer's basket, creating the basket row lazily on first use. It backs the "Add to Basket" button on the catalog page and will be called by the Angular catalog and basket-list views. The buyer is identified by a path parameter (`buyerId`) which is a username for authenticated users or a GUID string for anonymous users.

The legacy implementation is an **in-process service** — there is no dedicated MinimalApi endpoint. The service method `BasketService.AddItemToBasket` is called from the Razor Page handler `IndexModel.OnPost`, which performs critical work before the service call: it looks up the current `CatalogItem.Price` from the database and resolves the buyer identity from the request cookie or auth state. The Spring Boot REST endpoint must replicate this pre-call logic inside its handler. **The request body must never contain a price field** — the price is always fetched server-side.

The add operation is idempotent on `catalogItemId`: if the item is already in the basket, `Basket.AddItem` increments the existing `BasketItems.Quantity` rather than inserting a duplicate row. Guard clauses in `BasketItem.SetQuantity` and `AddQuantity` reject negative quantities (< 0) with an `ArgumentException`, which propagates as HTTP 500 in the legacy web app; the Java target should return HTTP 400 via `@Min(0)` validation instead.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | POST |
| Path | `/api/baskets/for-user/{buyerId}/items` |
| Auth required | no |
| Content-Type | `application/json` |

### Path Parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `buyerId` | string | yes | Username for authenticated users; GUID string for anonymous users. Acts as the `Baskets.BuyerId` key |

### Request Body

| Field | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `catalogItemId` | int | yes | — | Primary key of the `CatalogItems` row to add. The Java handler must look up `CatalogItems.Price` for this ID server-side |
| `quantity` | int | no | 1 | Units to add. Must be ≥ 0 (0 is technically allowed by the guard). The Razor Page caller always passes `quantity=1` (default) |

> **Price is NOT in the request body.** The legacy Razor Page handler fetches `CatalogItem.Price` from the database before calling the service and passes it as a parameter. The Java REST handler must do the same — look up the price from `CatalogItems` and never trust a client-supplied price value.

### Success Response

HTTP 200 OK

```json
{
  "buyerId": "alice@example.com",
  "items": [
    {
      "catalogItemId": 3,
      "unitPrice": 19.50,
      "quantity": 2
    }
  ]
}
```

**Response fields:**

| Field | Type | Notes |
| --- | --- | --- |
| `buyerId` | string | The buyer identity — matches the `{buyerId}` path parameter |
| `items` | array | All items currently in the basket after the add (not just the added item) |
| `items[].catalogItemId` | int | `BasketItem.CatalogItemId` |
| `items[].unitPrice` | decimal | `BasketItem.UnitPrice` — price at add-to-basket time |
| `items[].quantity` | int | `BasketItem.Quantity` — total quantity after the add |

> **Legacy returns void (redirect), not a basket response.** The Razor Page handler calls `_basketViewModelService.Map(basket)` to build a view model and then `RedirectToPage()`. The REST target must construct a `BasketResponse` DTO from the `Basket` entity returned by `AddItemToBasket`. The response shape above is the target API design — not sourced from an existing REST endpoint.

### Error Responses

| Status | Condition | Legacy behavior | Java target |
| --- | --- | --- | --- |
| 404 Not Found | `catalogItemId` does not exist in `CatalogItems` | `IndexModel.OnPost` redirects to `/Index` | Return HTTP 404 |
| 400 Bad Request | `quantity < 0` (`Guard.Against.OutOfRange` throws) | HTTP 500 via unhandled exception | Return HTTP 400 via `@Min(0)` validation |

---

## Business Logic

### Overview

The handler receives a `buyerId` (path) and `catalogItemId` + `quantity` (body). Before any basket logic, the Java REST handler must look up `CatalogItems` by `catalogItemId` to get the current price — if no row exists, return HTTP 404.

With the price obtained, the service queries `Baskets` by `BuyerId` (eager-loading `BasketItems`). If no basket exists for the buyer, a new `Baskets` row is inserted. The entity method `Basket.AddItem` then checks whether a `BasketItem` for the same `catalogItemId` already exists in the in-memory items collection:
- **New item**: adds a new `BasketItem(catalogItemId, quantity, unitPrice)` to the in-memory list
- **Existing item**: calls `existingItem.AddQuantity(quantity)` — adds to the existing `Quantity`

`UpdateAsync` persists the result: EF Core change tracking issues either an INSERT (new `BasketItem`) or an UPDATE (incremented `Quantity`) on the `BasketItems` table.

The `UnitPrice` stored on the `BasketItem` is snapshotted at add time — it is not updated on subsequent adds of the same item (price changes after the first add are not reflected until the item is removed and re-added).

### Validation Rules

| Field | Constraint | Guard clause | Legacy failure | Java target |
| --- | --- | --- | --- | --- |
| `catalogItemId` — existence | Must exist in `CatalogItems` | Implicit — null check in `IndexModel.OnPost` | Redirect to `/Index` | HTTP 404 |
| `quantity` | ≥ 0 | `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)` in `BasketItem.SetQuantity` and `AddQuantity` | HTTP 500 (unhandled `ArgumentException`) | HTTP 400 via `@Min(0)` |
| `catalogItemId` — format | Valid int | Framework route binding | HTTP 400 (framework) | HTTP 400 (same) |

> **`Guard.Against.OutOfRange(quantity, 0, int.MaxValue)`**: the lower bound is `0`, not `1`. A `quantity` of `0` is technically valid — it adds 0 units, which is a no-op (no row is inserted; if the item existed, it retains its current quantity via `AddQuantity(0)`). The Java target should match this by using `@Min(0)`, not `@Min(1)`.

### Call Sequence

**Full sequence from web handler through to DB:**

1. **[Web handler pre-call] Null guard** — `if (productDetails?.Id == null) → RedirectToPage("/Index")`. REST target: validate `catalogItemId` is present; return 400 if missing.
2. **[Web handler pre-call] Price lookup** — `IRepository<CatalogItem>.GetByIdAsync(productDetails.Id)`:
   - `SELECT Id, Price, ... FROM CatalogItems WHERE Id = {catalogItemId}`
   - If null: redirect to `/Index`. REST target: return HTTP 404.
   - Price is extracted: `item.Price`. This is the value passed to `AddItemToBasket`.
3. **[Web handler pre-call] Buyer identity resolution** — `GetOrSetBasketCookieAndUserName()`:
   - If `User.Identity.IsAuthenticated`: return `User.Identity.Name` (the authenticated username).
   - Else: read `eShop` cookie value; validate it is a valid GUID. If not a valid GUID, generate a new GUID, write the cookie (`IsEssential=true`, 10-year expiry), and return it.
   - REST target: `buyerId` is supplied as the path parameter — skip this step; use `{buyerId}` directly.
4. **[Service] Basket lookup** — `IRepository<Basket>.FirstOrDefaultAsync(new BasketWithItemsSpecification(username))`:
   - `SELECT b.Id, b.BuyerId, bi.* FROM Baskets b LEFT JOIN BasketItems bi ON bi.BasketId = b.Id WHERE b.BuyerId = {buyerId}`
   - Returns `Basket` with `Items` eagerly loaded, or `null`.
5. **[Service] Lazy basket creation** — if `basket == null`:
   - `IRepository<Basket>.AddAsync(new Basket(username))` → `INSERT INTO Baskets (BuyerId) VALUES ({buyerId})`
   - The newly created `basket` is used in the next step.
6. **[Service → Entity] Add item** — `basket.AddItem(catalogItemId, price, quantity)`:
   - Checks `Items.Any(i => i.CatalogItemId == catalogItemId)`:
     - **False** (new item): `_items.Add(new BasketItem(catalogItemId, quantity, unitPrice))` — constructor calls `SetQuantity(quantity)` which calls `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)`.
     - **True** (existing item): `existingItem.AddQuantity(quantity)` — calls `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)`, then `Quantity += quantity`.
7. **[Service] Persist** — `IRepository<Basket>.UpdateAsync(basket)`:
   - EF Core change tracking: if a new `BasketItem` was added → `INSERT INTO BasketItems (BasketId, CatalogItemId, UnitPrice, Quantity) VALUES (...)`
   - If existing `BasketItem.Quantity` was incremented → `UPDATE BasketItems SET Quantity = {new_qty} WHERE Id = {itemId}`
   - The `Baskets` row itself is also touched by `UpdateAsync` (EF Core tracks the aggregate root), but no column on `Baskets` changes.
8. **[Service] Return** — `AddItemToBasket` returns `basket` (the `Basket` entity with updated `Items`).
9. **[Web handler post-call]** — `IndexModel.OnPost` calls `_basketViewModelService.Map(basket)` for the view model, then `RedirectToPage()`. The REST target instead maps the returned `Basket` to a `BasketResponse` DTO and returns HTTP 200.

---

## Component Details

### In-process Service

**Service class**: `BasketService`
**Service file**: `src/ApplicationCore/Services/BasketService.cs`
**Method signature**: `Task<Basket> AddItemToBasket(string username, int catalogItemId, decimal price, int quantity = 1)`

**Injected dependencies**: `IRepository<Basket>`, `IAppLogger<BasketService>`

---

**Called from web handler**: `IndexModel.OnPost`
**Web handler file**: `src/Web/Pages/Basket/Index.cshtml.cs`
**Handler signature**: `Task<IActionResult> OnPost(CatalogItemViewModel productDetails)`

**What `IndexModel.OnPost` does BEFORE calling the service:**
1. Null guard on `productDetails?.Id` — returns redirect to `/Index` if null
2. `IRepository<CatalogItem>.GetByIdAsync(productDetails.Id)` — fetches current item for its `Price`; redirects to `/Index` if null
3. `GetOrSetBasketCookieAndUserName()` — resolves buyer identity (authenticated username or validated GUID from cookie, with new GUID creation if absent)
4. Calls `_basketService.AddItemToBasket(username, productDetails.Id, item.Price)` — **`quantity` uses the default value of 1; the Razor Page never passes an explicit quantity**

**What `IndexModel.OnPost` does AFTER the service call:**
- `_basketViewModelService.Map(basket)` — builds a `BasketViewModel` for the view
- `RedirectToPage()` → GET `/Basket` (Post-Redirect-Get)

> The Java REST endpoint must replicate steps 1–3 inside its handler method. Price is always server-side. The `buyerId` path parameter replaces the `GetOrSetBasketCookieAndUserName()` cookie/auth lookup.

---

**Entity: `Basket`**
**File**: `src/ApplicationCore/Entities/BasketAggregate/Basket.cs`

| Method | Logic |
| --- | --- |
| `AddItem(catalogItemId, unitPrice, quantity)` | If no existing item with matching `catalogItemId` → `new BasketItem(...)` added. If exists → `AddQuantity(quantity)` called on existing item |
| `RemoveEmptyItems()` | Not called by this operation — only used in `SetQuantities` |

---

**Entity: `BasketItem`**
**File**: `src/ApplicationCore/Entities/BasketAggregate/BasketItem.cs`

| Method | Guard clause | Effect |
| --- | --- | --- |
| Constructor `BasketItem(catalogItemId, quantity, unitPrice)` | `SetQuantity(quantity)` called in constructor | Sets `CatalogItemId`, `UnitPrice`, `Quantity`; guard fires if `quantity < 0` |
| `AddQuantity(quantity)` | `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)` | `Quantity += quantity`; guard fires if `quantity < 0` |
| `SetQuantity(quantity)` | `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)` | `Quantity = quantity`; guard fires if `quantity < 0` |

**Important**: `UnitPrice` is set in the constructor and is **never updated** by `AddQuantity` or `AddItem`. If the same item is added twice, the `UnitPrice` on the `BasketItem` remains the price from the first add.

---

**Specification: `BasketWithItemsSpecification`**
**File**: `src/ApplicationCore/Specifications/BasketWithItemsSpecification.cs`

Two overloads — this operation uses the `string buyerId` overload:
```csharp
Query.Where(b => b.BuyerId == buyerId).Include(b => b.Items);
```
Generates: `SELECT ... FROM Baskets WHERE BuyerId = {buyerId}` with `LEFT JOIN BasketItems` (or `Include` equivalent). Loads all `BasketItem` rows for the basket into the `Items` collection.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `CatalogItems` (`Catalog`) | SELECT (by PK) | `Id`, `Price` | Read by the web handler BEFORE calling the service — to get the authoritative item price. Returns 404 if null |
| `Baskets` | SELECT (by BuyerId), INSERT | `Id`, `BuyerId` | SELECT via `BasketWithItemsSpecification` (eager-loads Items); INSERT only when no basket exists for `buyerId` |
| `BasketItems` | SELECT (via Baskets eager load), INSERT or UPDATE | `Id`, `BasketId`, `CatalogItemId`, `UnitPrice`, `Quantity` | Loaded as part of the Baskets JOIN; INSERT if `catalogItemId` is new to the basket; UPDATE (Quantity only) if item already exists |

---

## Security Considerations

### Authentication

- **Required**: No. The endpoint is publicly accessible by design. `buyerId` in the path is the resource key, not an auth token.
- **Anonymous basket identity**: For anonymous users in the legacy web app, the `buyerId` is a GUID string stored in the `eShop` cookie. The Angular client sends this GUID as the `{buyerId}` path parameter. The Java endpoint receives it and uses it as-is.
- **Authenticated basket identity**: For authenticated users, the `buyerId` is the `User.Identity.Name` (the ASP.NET Identity username / email). The Angular client sends the authenticated user's identifier as `{buyerId}`.
- **No ownership verification**: The legacy code does not verify that the caller is the owner of the basket identified by `buyerId`. Any caller who knows a `buyerId` can add items to that basket. The Java target should be aware of this and can optionally add caller-verification if needed.

### Price Integrity

- **Critical**: Price is never accepted from the request body. The Java handler must call `catalogItemRepository.findById(catalogItemId)` to get `CatalogItem.price`, then pass that price to the basket service. This must not be skipped.
- **UnitPrice snapshot**: the price stored in `BasketItem.UnitPrice` is the price at add time. Price changes in the catalog after the add do not affect the basket total. This is intentional and must be preserved.

### Input Validation

- `quantity < 0` — guard fires in entity method; currently returns HTTP 500. Java target: add `@Min(0)` on the request field.
- `catalogItemId` non-existent — currently a web redirect. Java target: return HTTP 404.
- No `buyerId` format validation in the service — the service accepts any non-null string as `BuyerId`. The Java target should accept both GUID strings and email-style usernames.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| No `Task.Delay` | Not present in this operation | Nothing to remove |
| Two write operations | `AddAsync` (if lazy-create) + `UpdateAsync` are separate EF Core calls — not wrapped in an explicit transaction | Java: `@Transactional` at the service method level to ensure both writes succeed or both roll back |
| Eager load of all basket items | `BasketWithItemsSpecification` loads ALL `BasketItems` for the basket into memory before the in-memory upsert check | For baskets with many items, consider JPA `@Query` to check existence and increment in a single UPDATE, or accept the current load-all-then-check pattern |
| Price lookup as a separate DB call | Web handler calls `GetByIdAsync(catalogItemId)` separately before the service | Java: keep as a single `findById` call; do not merge with the basket query |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| Price source | `IndexModel.OnPost` calls `IRepository<CatalogItem>.GetByIdAsync(productDetails.Id)` to get `item.Price` before calling the service | Java handler must call `catalogItemRepository.findById(catalogItemId)` → use `catalogItem.getPrice()`; never accept price from request body |
| `catalogItemId` not found | `IndexModel.OnPost` redirects to `/Index` | Java handler: return HTTP 404 |
| Buyer identity | Cookie GUID or auth username, resolved by `GetOrSetBasketCookieAndUserName()` | REST target: `{buyerId}` path parameter — use directly as the basket `BuyerId` |
| Quantity default | Service default parameter `quantity = 1`; Razor Page always passes default | Java: default `quantity` to `1` if absent from request body |
| Negative quantity | Guard throws `ArgumentException` → HTTP 500 | Java: `@Min(0)` on `quantity` → HTTP 400 |
| Lazy basket creation | `AddAsync(new Basket(username))` only when `FirstOrDefaultAsync` returns null | Java: `findByBuyerId(buyerId)` → if empty, persist `new Basket(buyerId)` before adding item |
| Upsert on `catalogItemId` | `Basket.AddItem` checks in-memory list; inserts new `BasketItem` or increments existing | Java: load all basket items from DB; check if `catalogItemId` exists; INSERT or UPDATE accordingly |
| `UnitPrice` not updated on re-add | `AddQuantity` only increments `Quantity`; `UnitPrice` stays at first-add price | Java: on an existing `BasketItem`, only update `Quantity` — do not overwrite `UnitPrice` |
| EF Core `UpdateAsync` covers both Baskets and BasketItems | Single `UpdateAsync` call persists lazy-created basket row AND item changes via EF Core change tracking | Java: ensure both `Basket` save and `BasketItem` save happen in the same `@Transactional` method |
| Response from web handler | Web handler returns a page redirect, not JSON | Java: map the returned `Basket` entity to `BasketResponse { buyerId, items[] }` and return HTTP 200 |
| Web handler uses quantity=1 always | Razor Page does not accept quantity from the form (only item ID) | REST target accepts any `quantity ≥ 0`; this is intentional for the API |

---

## Analysis Notes

- **Web handler passes `quantity=1` always**: `IndexModel.OnPost` calls `AddItemToBasket(username, productDetails.Id, item.Price)` using the default `quantity=1`. The REST target accepts an explicit `quantity` from the request body — this is the correct REST API behaviour and an intentional improvement over the form-based UI.

- **`Guard.Against.OutOfRange` lower bound is 0, not 1**: `quantity=0` is technically valid and results in a no-op (adds 0 units). If the item is new to the basket, a `BasketItem` with `Quantity=0` would be created. This is probably an oversight in the legacy code. The Java target could add `@Min(1)` to prevent degenerate zero-quantity items, but this is a behavioural change — flag for BA review.

- **`UnitPrice` snapshot caveat on re-add**: If the same `catalogItemId` is added twice, `AddQuantity` is called but `UnitPrice` is NOT updated to the current catalog price. The stored `UnitPrice` reflects the price at the time of the first add. This is intentional — see business rule 7 in `functional-spec.md`. A price change in the catalog between two adds of the same item is silently ignored.

- **`BasketWithItemsSpecification` loads all items**: the specification loads all `BasketItems` for the basket into memory for the `AddItem` in-memory check. For large baskets, a targeted EXISTS + increment query would be more efficient. The Java target can choose to replicate this load-all pattern or use a more targeted query — either is correct.

- **`AddAsync` for lazy creation then `UpdateAsync` for item**: The legacy code calls `AddAsync` when creating a new basket, which persists the `Baskets` row immediately. Then `UpdateAsync` is called after `AddItem`, which persists the `BasketItems` row. Two separate EF Core round-trips with no explicit transaction wrapper. The Java `@Transactional` annotation ensures atomicity, but note the basket creation and item addition are currently not atomic in the legacy code.

- **Anonymous-to-authenticated basket transfer**: `BasketService.TransferBasketAsync` exists to merge an anonymous basket into an authenticated user's basket on login. This is called by the Identity cookie events, not by this endpoint. The add-item endpoint is not responsible for the transfer.

- **`BasketResponse` is a target API design DTO**: the legacy in-process service returns the `Basket` entity directly to the Razor Page handler. The `BasketResponse` structure in the functional spec is the designed REST response shape — the Java developer must create this DTO class.
