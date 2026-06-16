# Functional spec — Add item to basket

**Key:** `add-item-to-basket`
**Legacy:** `BasketService.AddItemToBasket(username, catalogItemId, price, quantity = 1)` — called from `IndexModel.OnPost`
**Target REST:** `POST /api/baskets/for-user/{buyerId}/items`

## Purpose

Adds (or increments) a product in a user's basket. Creates the basket on demand.

## Inputs

```json
{
  "catalogItemId": 1,
  "quantity": 1
}
```

`buyerId` comes from the path; price is looked up server-side from `Catalog`.

## Outputs

The updated basket (same shape as `get-basket-for-user`).

## Acceptance criteria

```
Scenario: Add new item to empty basket
  Given no Basket exists for buyerId "u1"
  When POST /api/baskets/for-user/u1/items with { catalogItemId: 3, quantity: 1 }
  Then a Baskets row is created (BuyerId = "u1")
  And a BasketItems row is created with CatalogItemId=3, Quantity=1, UnitPrice=<current Catalog.Price>

Scenario: Add existing item increments quantity
  Given a basket for "u1" already has BasketItems row for catalogItemId=3 with Quantity=1
  When POST /api/baskets/for-user/u1/items with { catalogItemId: 3, quantity: 2 }
  Then the existing BasketItems row's Quantity becomes 3
  And no additional BasketItems row is created

Scenario: Unknown catalog item
  Given catalogItemId = 9999 doesn't exist
  When POST /api/baskets/for-user/u1/items with { catalogItemId: 9999 }
  Then the basket is unchanged
  And the response is 404 or a redirect to the catalog (legacy redirects to /Index)

Scenario: Negative quantity rejected
  Given quantity = -1
  When the endpoint is called
  Then the server rejects the request (Guard.Against.OutOfRange in BasketItem.SetQuantity)
```

## Business rules

- **Price is authoritative from the server.** The Razor page looks up the current
  `Catalog.Price` before calling the service; the REST endpoint MUST do the same.
- `quantity` defaults to `1` when absent.
- An "add" of an already-present `catalogItemId` increments the existing row's
  quantity rather than inserting a duplicate — see `Basket.AddItem` (Basket.cs:22).
- Minimum quantity is `0`; attempting to add `< 0` raises `Guard.Against.OutOfRange`.
