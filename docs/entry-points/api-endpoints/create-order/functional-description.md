# Functional Description: Create order from basket

> **Entry Point**: create-order
> **Location**: src/ApplicationCore/Services/OrderService.cs
> **Type**: API / In-process Service
> **Domain**: orders
> **Legacy method**: Microsoft.eShopWeb.ApplicationCore.Services.OrderService.CreateOrderAsync
> **Web handler**: Microsoft.eShopWeb.Web.Pages.Basket.CheckoutModel.OnPost

## Executive Summary

The `create-order` endpoint converts a basket into an immutable order, snapshotting catalog item names and picture URIs at the moment of checkout. It is the second step in a three-call checkout sequence (update quantities → create order → delete basket). The Angular checkout component calls these three steps in order; each is a separate API call. The basket is NOT deleted by this endpoint — that is the caller's responsibility.

Authentication is required — `CheckoutModel` is decorated with `[Authorize]` and the REST target must enforce a valid JWT. The endpoint has two guard-enforced early exits: if the basket is not found (`Guard.Against.Null`), the legacy throws `ArgumentNullException`; if the basket has no items (`Guard.Against.EmptyBasketOnCheckout`), it throws `EmptyBasketOnCheckoutException`. The legacy web handler catches only `EmptyBasketOnCheckoutException` (redirecting to `/Basket/Index`) — a missing basket results in an unhandled exception and HTTP 500. The Java REST target must handle both cases explicitly, returning 404 for missing basket and 422 for empty basket.

The most critical design delta is the **hardcoded shipping address**. The legacy `CheckoutModel.OnPost` passes `new Address("123 Main St.", "Kent", "OH", "United States", "44240")` directly to the service — the actual address the user might have entered on the checkout page is never used. The REST target MUST accept a real shipping address from the request body and pass it to the order service.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | POST |
| Path | `/api/orders` |
| Content-Type | `application/json` |
| Auth required | yes — JWT Bearer |

### Request Body

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `basketId` | int | yes | `Baskets.Id` of the basket to convert. Must exist and have at least one item. |
| `shippingAddress.street` | string | yes | Street address |
| `shippingAddress.city` | string | yes | City |
| `shippingAddress.state` | string | yes | State / region (may be empty for countries without states) |
| `shippingAddress.country` | string | yes | Country |
| `shippingAddress.zipCode` | string | yes | ZIP / postal code |

Request body example:
```json
{
  "basketId": 42,
  "shippingAddress": {
    "street": "123 Main St.",
    "city": "Kent",
    "state": "OH",
    "country": "United States",
    "zipCode": "44240"
  }
}
```

### Success Response

HTTP 201 Created:

```json
{
  "orderId": 17,
  "buyerId": "alice@example.com",
  "orderDate": "2025-04-27T14:32:00Z",
  "total": 47.50
}
```

The legacy `CreateOrderAsync` returns `Task` (void) — the REST response model is a design addition for the Java target. The `orderId` must come from the database-assigned primary key of the inserted `Orders` row. `total` is computed as `SUM(UnitPrice × Units)` across all `OrderItems`.

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 401 | JWT absent or invalid | empty |
| 404 | No `Baskets` row found for `basketId` | empty (legacy: unhandled `ArgumentNullException` → 500) |
| 422 | Basket found but has zero items | empty (legacy: `EmptyBasketOnCheckoutException` → redirect) |
| 500 | Unhandled exception | empty |

---

## Business Logic

### Overview

The service loads the basket (with all its items) by `basketId`, validates it is non-null and non-empty, then batch-fetches the corresponding `CatalogItem` rows to snapshot their current `Name` and `PictureUri`. For each basket item it creates an `OrderItem` using the basket item's `UnitPrice` (the price at add-to-basket time, not the current catalog price) and `Quantity`. A new `Order` aggregate is then constructed from the buyer's identity (read from the basket's `BuyerId`), the supplied shipping address, and the list of order items. The aggregate is persisted with a single `AddAsync` call, which cascades all `OrderItem` rows via EF Core.

The shopping sequence in legacy is:
1. Caller calls `BasketService.SetQuantities` to sync any quantity changes (update-item-in-basket endpoint)
2. Caller calls `OrderService.CreateOrderAsync` (this endpoint)
3. Caller calls `BasketService.DeleteBasketAsync` to clear the basket (delete-item-in-basket endpoint)

The REST Angular client must replicate this three-call sequence. If step 3 fails, the basket is not cleared and the user may be able to re-order. This is a known limitation of the legacy design.

### Validation Rules

| Condition | Rule | Failure behavior |
| --- | --- | --- |
| `basketId` not found | `Guard.Against.Null(basket)` → `ArgumentNullException` | Legacy: unhandled → 500. Java: return 404 |
| Basket has 0 items | `Guard.Against.EmptyBasketOnCheckout(basket.Items)` → `EmptyBasketOnCheckoutException` | Legacy: caught → redirect to /Basket/Index. Java: return 422 |
| `catalogItemId` < 1 | `Guard.Against.OutOfRange(catalogItemId, 1, int.MaxValue)` in `CatalogItemOrdered` constructor | Exception propagates → 500 |
| `productName` is null/empty | `Guard.Against.NullOrEmpty(productName)` in `CatalogItemOrdered` constructor | Exception propagates → 500 (would happen if Catalog item has empty Name) |
| `pictureUri` is null/empty | `Guard.Against.NullOrEmpty(pictureUri)` in `CatalogItemOrdered` constructor | Exception propagates → 500 (would happen if `ComposePicUri` returns empty) |
| `buyerId` is null/empty | `Guard.Against.NullOrEmpty(buyerId)` in `Order` constructor | Exception propagates → 500 |
| Address fields | No validation in `Address` constructor — all five fields are assigned directly | DB `NOT NULL` constraint violations propagate as 500 |
| `shippingAddress` fields | Not validated in the service — Address fields are null-safe in .NET | Java target should add `@NotBlank` to all five address fields |

### Call Sequence

**Web handler pre-call (`CheckoutModel.OnPost`):**
1. `SetBasketModelAsync()` — resolves authenticated username (`User.Identity.Name`) and loads `BasketModel` via `IBasketViewModelService.GetOrCreateBasketForUser`
2. `ModelState.IsValid` check — returns `BadRequest()` if form model state is invalid
3. Builds `updateModel = items.ToDictionary(b => b.Id.ToString(), b => b.Quantity)` — maps basket item IDs to quantities from the posted form
4. `IBasketService.SetQuantities(BasketModel.Id, updateModel)` — syncs quantity changes into `BasketItems`
5. `IOrderService.CreateOrderAsync(BasketModel.Id, new Address("123 Main St.", "Kent", "OH", "United States", "44240"))` — **hardcoded address**
6. `IBasketService.DeleteBasketAsync(BasketModel.Id)` — clears the basket
7. Catches `EmptyBasketOnCheckoutException` → `RedirectToPage("/Basket/Index")`
8. On success → `RedirectToPage("Success")` → GET `/Basket/Checkout/Success`

**Service method (`OrderService.CreateOrderAsync`):**
1. Receive `basketId` (int) and `shippingAddress` (Address value object)
2. `new BasketWithItemsSpecification(basketId)` — spec filters by `Baskets.Id`, eager-loads `BasketItems`
3. `IRepository<Basket>.FirstOrDefaultAsync(basketSpec)` → SELECT `Baskets` + `BasketItems` WHERE `Id = basketId`; returns null if not found
4. `Guard.Against.Null(basket)` — throws `ArgumentNullException` if basket is null
5. `Guard.Against.EmptyBasketOnCheckout(basket.Items)` — throws `EmptyBasketOnCheckoutException` if `basket.Items` is empty
6. Extract `catalogItemIds[]` from `basket.Items.Select(i => i.CatalogItemId)`
7. `new CatalogItemsSpecification(catalogItemIds[])` — spec: `WHERE Id IN (catalogItemIds)`
8. `IRepository<CatalogItem>.ListAsync(catalogItemsSpec)` → batch SELECT from `Catalog` for all basket item catalog IDs
9. For each basket item:
   - Find matching `catalogItem` via `catalogItems.First(c => c.Id == basketItem.CatalogItemId)` — in-memory lookup (throws `InvalidOperationException` if any basket item references a deleted catalog item)
   - `new CatalogItemOrdered(catalogItem.Id, catalogItem.Name, ComposePicUri(catalogItem.PictureUri))` — snapshot name + absolute picture URI; guards: `OutOfRange(catalogItemId >= 1)`, `NullOrEmpty(productName)`, `NullOrEmpty(pictureUri)`
   - `new OrderItem(itemOrdered, basketItem.UnitPrice, basketItem.Quantity)` — price from basket (add-time), quantity from basket
10. `new Order(basket.BuyerId, shippingAddress, items)` — `Guard.Against.NullOrEmpty(buyerId)`; `OrderDate = DateTimeOffset.Now` (property initializer, not a constructor argument)
11. `IRepository<Order>.AddAsync(order)` → INSERT `Orders` row; EF Core cascades INSERT of all `OrderItem` rows

---

## Component Details

### Service Method

**Class**: `OrderService`
**File**: `src/ApplicationCore/Services/OrderService.cs`
**Method signature**: `Task CreateOrderAsync(int basketId, Address shippingAddress)`

**Injected services**: `IRepository<Basket>`, `IRepository<CatalogItem>`, `IRepository<Order>`, `IUriComposer`

**Returns**: `Task` (void) — no order ID returned. The Java target must obtain the order ID from the persisted entity after `save()`.

---

### Web Handler (`CheckoutModel.OnPost`)

**File**: `src/Web/Pages/Basket/Checkout.cshtml.cs`
**Auth**: `[Authorize]` on the class — all handlers require authentication.

**What `OnPost` does BEFORE calling the service:**
1. Calls `SetBasketModelAsync()` to load the basket by authenticated username
2. Validates `ModelState.IsValid` — returns 400 if form is invalid
3. **Syncs quantities** by calling `IBasketService.SetQuantities(BasketModel.Id, updateModel)` — this is a separate operation from the order creation
4. **Calls `CreateOrderAsync` with the HARDCODED address** — the `shippingAddress` parameter is `new Address("123 Main St.", "Kent", "OH", "United States", "44240")` regardless of any address the user entered

**What `OnPost` does AFTER the service call:**
5. `DeleteBasketAsync(BasketModel.Id)` — clears the basket (separate service call, not part of `CreateOrderAsync`)
6. `RedirectToPage("Success")` → renders `/Basket/Checkout/Success`

**Exception handling**:
- `EmptyBasketOnCheckoutException` → caught, logged as warning, redirect to `/Basket/Index`
- `ArgumentNullException` (missing basket) → NOT caught → unhandled → HTTP 500

> The Java REST endpoint replaces the entire `OnPost` sequence. The address must come from the request body (not hardcoded). Quantity sync (`SetQuantities`) is a separate prior API call in the Angular checkout flow. Basket deletion is a separate subsequent API call. This endpoint handles only step 2 (create order).

---

### Domain Entities (relevant)

**`Address`** (`src/ApplicationCore/Entities/OrderAggregate/Address.cs`):
- Value object with 5 fields: `Street`, `City`, `State`, `Country`, `ZipCode`
- No guards in constructor — all string values accepted including null/empty
- Stored in `Orders` table as flat columns with `ShipToAddress_` prefix

**`Order`** (`src/ApplicationCore/Entities/OrderAggregate/Order.cs`):
- `Guard.Against.NullOrEmpty(buyerId)` in constructor
- `OrderDate = DateTimeOffset.Now` — set as property initializer, not a constructor argument; cannot be supplied by client
- `Total()` method: `SUM(item.UnitPrice * item.Units)` — available for constructing the REST response

**`OrderItem`** (`src/ApplicationCore/Entities/OrderAggregate/OrderItem.cs`):
- `UnitPrice` — from `basketItem.UnitPrice` (price at add-to-basket time)
- `Units` — from `basketItem.Quantity`
- No guards in `OrderItem` constructor

**`CatalogItemOrdered`** (`src/ApplicationCore/Entities/OrderAggregate/CatalogItemOrdered.cs`):
- Snapshot value object — stored as three flat columns: `ItemOrdered_CatalogItemId`, `ItemOrdered_ProductName`, `ItemOrdered_PictureUri`
- Guards in constructor: `OutOfRange(catalogItemId, 1, int.MaxValue)`, `NullOrEmpty(productName)`, `NullOrEmpty(pictureUri)`
- `PictureUri` is always the **absolute URL** (via `ComposePicUri`) — not the stored relative path

---

### Specifications

**`CatalogItemsSpecification`** (`src/ApplicationCore/Specifications/CatalogItemsSpecification.cs`):
- `WHERE CatalogItems.Id IN (catalogItemIds[])` — batch SELECT for all basket item catalog IDs in one query

**`BasketWithItemsSpecification(int basketId)`** (by-ID overload, `src/ApplicationCore/Specifications/BasketWithItemsSpecification.cs`):
- `WHERE Baskets.Id = basketId AND .Include(b => b.Items)` — eager-loads `BasketItems`

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `Baskets` | SELECT | `Id`, `BuyerId` | Selected by `Baskets.Id` via `BasketWithItemsSpecification`; `BuyerId` becomes `Order.BuyerId` |
| `BasketItems` | SELECT | `CatalogItemId`, `UnitPrice`, `Quantity` | Loaded via `.Include(b => b.Items)` eager-load; `UnitPrice` is from add-to-basket time — NOT the current catalog price |
| `Catalog` | SELECT | `Id`, `Name`, `PictureUri` | Batch-fetched via `CatalogItemsSpecification(ids[])` — only `Name` and `PictureUri` are read for snapshot |
| `Orders` | INSERT | `Id`, `BuyerId`, `OrderDate`, `ShipToAddress_Street`, `ShipToAddress_City`, `ShipToAddress_State`, `ShipToAddress_Country`, `ShipToAddress_ZipCode` | Single row per checkout; `OrderDate` defaults to `DateTimeOffset.Now` |
| `OrderItems` | INSERT | `Id`, `OrderId`, `UnitPrice`, `Units`, `ItemOrdered_CatalogItemId`, `ItemOrdered_ProductName`, `ItemOrdered_PictureUri` | Cascade-inserted via EF Core when `Order` is added; one row per basket item |

---

## Security Considerations

### Authentication

- **Required**: yes — `[Authorize]` on `CheckoutModel` class; JWT Bearer required for the REST target
- **Mechanism**: JWT bearer token in `Authorization: Bearer {token}` header
- **Role required**: none — any authenticated user may create an order

### BuyerId Source

The `Order.BuyerId` is read from `basket.BuyerId` — the buyer identity associated with the basket at creation time. For authenticated users this is their username (email); for anonymous users it could be a GUID from the `eShop` cookie. The REST target should clarify whether `BuyerId` should be the JWT subject or the basket's stored `BuyerId`. Using the basket's `BuyerId` ensures consistency with the basket's identity, even if the user had an anonymous session that was later associated with their account.

### Price Integrity

The `OrderItem.UnitPrice` is taken from `basketItem.UnitPrice` — the price at the time the item was added to the basket. The current catalog price is NOT re-fetched for the order. This ensures the user pays the price they saw when they added the item, even if catalog prices changed before checkout. The Java target must preserve this behaviour — do not read price from `Catalog` here.

### Input Validation

- No validation on `shippingAddress` fields in the legacy service — all are passed directly to the `Address` value object without guards. DB `NOT NULL` constraints are the only enforcement.
- **Java target must add**: `@NotBlank` on all five address fields, `@Positive` on `basketId`.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Basket + items in one query | `BasketWithItemsSpecification` uses `.Include(b => b.Items)` — single JOIN query | Java: `@OneToMany` with `EAGER` fetch or `JOIN FETCH` JPQL — single query |
| Catalog batch fetch | `CatalogItemsSpecification(ids[])` → `WHERE Id IN (...)` — one query for all catalog items | Java: `findAllById(ids)` or `@Query("... WHERE c.id IN :ids")` |
| Cascade insert | All `OrderItem` rows inserted via EF Core cascade when `Order` is added | Java: `@OneToMany(cascade = CascadeType.PERSIST)` + `save(order)` |
| No `Task.Delay` | No artificial delay in this endpoint | N/A |
| No AutoMapper | DTO for response is a new addition — no AutoMapper in the legacy service | Java: manually construct `CreateOrderResponse { orderId, buyerId, orderDate, total }` from the persisted entity |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| **Hardcoded shipping address** | `new Address("123 Main St.", "Kent", "OH", "United States", "44240")` in `OnPost` | **Accept all 5 address fields from request body** — this is the primary design change from legacy to REST |
| Service returns void | `CreateOrderAsync` returns `Task` — no order ID available to the web handler | Java: `orderRepository.save(order)` returns the persisted entity; return `orderId` in response body as HTTP 201 |
| Empty basket handling | `EmptyBasketOnCheckoutException` caught in `OnPost` → redirect | Java: return HTTP 422 Unprocessable Entity |
| Missing basket handling | `ArgumentNullException` NOT caught in `OnPost` → HTTP 500 | Java: explicitly check `basket != null`, return HTTP 404 |
| Checkout sequence | `SetQuantities` + `CreateOrderAsync` + `DeleteBasketAsync` all called in `OnPost` | Java: these are 3 separate API calls; Angular client sequences them in order |
| `OrderDate` | `DateTimeOffset.Now` set as property initializer in `Order` entity — not client-supplied | Java: set `orderDate = Instant.now()` in the entity/service before persisting; never accept from request body |
| `BuyerId` source | `basket.BuyerId` — whatever identity was stored when the basket was created | Java: read from the loaded basket entity's `buyerId` field |
| Catalog snapshot | `CatalogItemOrdered` stores snapshot of Name + PictureUri at order time | Java: store these as plain columns in `order_items`, not as FKs to `catalog_items` |
| `PictureUri` in snapshot | `IUriComposer.ComposePicUri(catalogItem.PictureUri)` → absolute URL stored in `ItemOrdered_PictureUri` | Java: compose absolute URL before storing in `order_items.item_ordered_picture_uri` |
| `UnitPrice` source | `basketItem.UnitPrice` — snapshot from basket | Java: copy from `basket_items.unit_price` — do NOT re-fetch from `catalog_items.price` |
| `CatalogItems.First()` | In-memory lookup with `.First()` — throws if basket has item referencing deleted catalog item | Java: handle `CatalogItem` not found gracefully — return 422 or 500 with clear message |

---

## Analysis Notes

- **The checkout sequence is the caller's responsibility.** `CreateOrderAsync` only creates the order — it does not sync quantities and it does not delete the basket. The Angular client must call these three APIs in order. If the delete-basket step fails, the user may be able to re-submit the checkout form and create a duplicate order. The Java target should consider idempotency controls (e.g., idempotency key header) to prevent duplicate orders.

- **Missing basket throws `ArgumentNullException`, not a domain exception.** This exception is not caught by `OnPost` in the legacy code — it propagates as HTTP 500. The Java target must explicitly check if the basket exists and return 404 rather than letting a null-pointer exception propagate.

- **`basket.BuyerId` may be an anonymous GUID.** If the user had an anonymous session (basket created with GUID cookie identity) and then authenticated without the basket being merged, the `Order.BuyerId` will be the GUID string, not the authenticated username. The REST target should clarify whether anonymous checkout is in scope. If it is, the `Authorization` JWT's subject and the basket's `BuyerId` may differ.

- **`catalogItems.First()` throws `InvalidOperationException` if a basket item's `CatalogItemId` has no match in the fetched catalog items.** This could happen if a catalog item was deleted between add-to-basket and checkout. The legacy code lets this propagate as HTTP 500. The Java target should catch this and return 422 (item no longer available).

- **`OrderDate` is `DateTimeOffset.Now` (local time), not UTC.** Depending on the server's timezone, this may produce unexpected timestamps. The Java target should use `Instant.now()` or `OffsetDateTime.now(ZoneOffset.UTC)` for consistent UTC timestamps.

- **`Order.Total()` is a computed method, not a stored column.** The `Orders` table does not have a `Total` column — it is calculated by `SUM(UnitPrice * Units)` across `OrderItems`. The REST response `total` field must be computed by the Java service after building the order items list.

- **Address fields are stored as flat columns (`ShipToAddress_Street`, etc.), not in a separate table.** The Java entity should use `@Embedded` with `@AttributeOverrides` to map the `Address` value object to these flat columns.
