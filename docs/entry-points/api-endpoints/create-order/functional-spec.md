# Functional spec — Create order from basket

**Key:** `create-order`
**Legacy:** `OrderService.CreateOrderAsync(basketId, shippingAddress)` — called from `CheckoutModel.OnPost`
**Target REST:** `POST /api/orders`

## Purpose

Creates an order from the contents of a basket, snapshotting current catalog item names and picture URIs into immutable OrderItem records. Called by the Angular checkout flow as the second step of the three-step checkout sequence (update quantities → create order → delete basket).

## Inputs

| Name | Type | In | Optional | Notes |
| --- | --- | --- | --- | --- |
| `basketId` | int | body | no | Baskets.Id of the basket to convert to an order |
| `shippingAddress.street` | string | body | no | Street address |
| `shippingAddress.city` | string | body | no | City |
| `shippingAddress.state` | string | body | no | State/region |
| `shippingAddress.country` | string | body | no | Country |
| `shippingAddress.zipCode` | string | body | no | ZIP / postal code |

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

**Critical design delta from legacy:** The legacy `CheckoutModel.OnPost` hardcodes the address as `new Address("123 Main St.", "Kent", "OH", "United States", "44240")`. The REST target MUST accept a real address in the request body — the hardcoded address must not be carried over.

## Outputs

HTTP 201 Created with the new order reference:

```json
{
  "orderId": 17,
  "buyerId": "alice@example.com",
  "orderDate": "2025-04-27T14:32:00Z",
  "total": 47.50
}
```

Legacy `CreateOrderAsync` returns `Task` (void). The REST `@PostMapping` should return `ResponseEntity<CreateOrderResponse>` with HTTP 201 and the inserted Order.Id.

## Acceptance criteria

```gherkin
Scenario: Successful order creation
  Given an authenticated user "alice@example.com"
  And basket id=42 has 2 BasketItems for catalogItemIds 3 and 7
  When POST /api/orders with { basketId: 42, shippingAddress: { street: "1 High St", city: "London", state: "", country: "UK", zipCode: "EC1A 1BB" } }
  Then response status is 201 Created
  And an Orders row is inserted with BuyerId="alice@example.com"
  And 2 OrderItems rows are inserted with snapshotted Name and PictureUri from Catalog
  And OrderItems.UnitPrice equals the BasketItem.UnitPrice at add-time (not current catalog price)

Scenario: Empty basket rejected
  Given basket id=42 has 0 BasketItems
  When POST /api/orders with { basketId: 42, shippingAddress: {...} }
  Then response status is 422 Unprocessable Entity
  (Guard.Against.EmptyBasketOnCheckout throws EmptyBasketOnCheckoutException)

Scenario: Basket not found returns 404
  Given no basket exists with id=999
  When POST /api/orders with { basketId: 999, shippingAddress: {...} }
  Then response status is 404 Not Found
  (Guard.Against.Null(basket) throws ArgumentNullException)

Scenario: Unauthenticated request rejected
  Given no JWT token in the Authorization header
  When POST /api/orders
  Then response status is 401 Unauthorized

Scenario: Catalog snapshot is immutable
  Given order id=17 was created when CatalogItem id=3 had Name=".NET Mug"
  When the CatalogItem id=3 is later renamed to ".NET Black Mug"
  Then OrderItems for order id=17 still show ItemOrdered_ProductName=".NET Mug"
```

## Business rules

1. **Shipping address MUST come from the client.** The legacy `CheckoutModel.OnPost` hardcodes `new Address("123 Main St.", "Kent", "OH", "United States", "44240")`. The Java REST handler must accept all five address fields from the request body and pass them to the service.
2. **OrderItem.UnitPrice is from BasketItem, not Catalog.** The price used in each OrderItem is `basketItem.UnitPrice` — the price at the time the item was added to the basket. The current catalog price is NOT re-fetched for the order. This preserves price integrity if catalog prices change between add-to-basket and checkout.
3. **Catalog data is snapshotted as `CatalogItemOrdered`.** `ItemOrdered_ProductName` and `ItemOrdered_PictureUri` are stored directly in OrderItems — not as foreign keys to Catalog. Changes to Catalog after order creation do not affect historical orders.
4. **`PictureUri` is rewritten to absolute URL.** `IUriComposer.ComposePicUri(catalogItem.PictureUri)` is called when constructing each `CatalogItemOrdered` — the stored `ItemOrdered_PictureUri` is always an absolute URL.
5. **Empty basket throws before creating the order.** `Guard.Against.EmptyBasketOnCheckout(basket.Items)` throws `EmptyBasketOnCheckoutException` if there are no basket items. The REST target should return HTTP 422; the legacy catches this and redirects to `/Basket/Index`.
6. **Missing basket returns 404.** `Guard.Against.Null(basket)` throws `ArgumentNullException` — legacy results in HTTP 500. The Java target must explicitly check and return 404.
7. **Authentication required.** `CheckoutModel` is `[Authorize]`. The `@PostMapping` must be guarded by `@PreAuthorize` or Spring Security filter requiring a valid JWT.
8. **The service does NOT delete the basket.** Basket deletion is the caller's responsibility (`DeleteBasketAsync` called after `CreateOrderAsync` by `CheckoutModel.OnPost`). The Angular checkout service must call `delete-item-in-basket` separately after this endpoint succeeds.
9. **`Order.OrderDate` defaults to `DateTimeOffset.Now`.** Set automatically in the entity constructor — not accepted from the client.

## Non-functional

- Mutating: reads Baskets, BasketItems, and Catalog; inserts Orders and OrderItems.
- Requires authentication (caller is `[Authorize]`).
- Called once per completed checkout — very low frequency, one call per order placed.
- Not idempotent — each successful call creates a new Orders row; calling twice creates duplicate orders.
- Part of a three-call checkout sequence: `update-item-in-basket` → `create-order` → `delete-item-in-basket`. The REST caller (Angular) must execute these in order.
