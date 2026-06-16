# Functional spec — Update basket item quantities

**Key:** `update-item-in-basket`
**Legacy:** `BasketService.SetQuantities(basketId, quantities)` — called from `IndexModel.OnPostUpdate`
**Target REST:** `PUT /api/baskets/{basketId}/items`

## Purpose

Sets the quantities of one or more items in a basket in a single operation. Called by the Angular basket view when the user edits item quantities and clicks "Update". Items set to zero are removed from the basket; items absent from the request are left unchanged.

## Inputs

| Name | Type | In | Optional | Notes |
| --- | --- | --- | --- | --- |
| `basketId` | int | path | no | Baskets.Id integer PK |
| `items` | array | body | no | Array of basketItemId + quantity pairs |
| `items[].basketItemId` | int | body | no | BasketItems.Id of the row to update |
| `items[].quantity` | int | body | no | New quantity. Must be >= 0. 0 removes the item. |

Request body example:
```json
{
  "items": [
    { "basketItemId": 12, "quantity": 2 },
    { "basketItemId": 15, "quantity": 0 }
  ]
}
```

## Outputs

HTTP 200 OK with the updated basket:

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

Item 15 (set to quantity=0) is absent from the response — it was deleted.

## Acceptance criteria

```gherkin
Scenario: Update quantity of an existing item
  Given basket id=7 has BasketItem id=12 (catalogItemId=3, quantity=1)
  When PUT /api/baskets/7/items with { items: [{ basketItemId: 12, quantity: 3 }] }
  Then BasketItems row id=12 has Quantity=3
  And response status is 200 OK
  And response.items contains entry with basketItemId=12, quantity=3

Scenario: Set quantity to zero removes the item
  Given basket id=7 has BasketItem id=12 (quantity=1) and id=15 (quantity=2)
  When PUT /api/baskets/7/items with { items: [{ basketItemId: 15, quantity: 0 }] }
  Then BasketItems row id=15 is deleted
  And BasketItems row id=12 is unchanged
  And response.items does not contain basketItemId=15

Scenario: Items absent from request body are unchanged
  Given basket id=7 has BasketItems id=12 and id=15
  When PUT /api/baskets/7/items with { items: [{ basketItemId: 12, quantity: 5 }] }
  Then BasketItems row id=12 has Quantity=5
  And BasketItems row id=15 is unchanged

Scenario: Basket not found returns 404
  Given no Basket exists with id=999
  When PUT /api/baskets/999/items with any body
  Then response status is 404 Not Found
  (Legacy returns Result<Basket>.NotFound())

Scenario: Negative quantity rejected
  When PUT /api/baskets/7/items with { items: [{ basketItemId: 12, quantity: -1 }] }
  Then response status is 400 Bad Request
  (Guard.Against.OutOfRange in BasketItem.SetQuantity throws for quantity < 0)

Scenario: Update multiple items in one request
  Given basket id=7 has BasketItems id=12 (qty=1) and id=15 (qty=3) and id=18 (qty=2)
  When PUT /api/baskets/7/items with { items: [{ basketItemId: 12, quantity: 5 }, { basketItemId: 15, quantity: 0 }] }
  Then BasketItems id=12 has Quantity=5
  And BasketItems id=15 is deleted
  And BasketItems id=18 is unchanged (quantity=2)
```

## Business rules

1. **Partial update semantics.** Only items included in the request body are modified — the dictionary is applied as a patch. Items not listed are left at their current quantities. This is NOT a replace-all operation.
2. **Zero quantity deletes the item.** `basket.RemoveEmptyItems()` is called after all quantities are set — any `BasketItem` with `Quantity == 0` is removed from the collection and deleted by `UpdateAsync`. Setting quantity=0 is the correct way to remove an item.
3. **Quantity floor is 0.** `Guard.Against.OutOfRange(quantity, 0, int.MaxValue)` in `BasketItem.SetQuantity` — a negative quantity throws. The Java target should validate with `@Min(0)` on the DTO field to return HTTP 400 rather than 500.
4. **basketId is the integer PK, not buyerId.** The `quantities` dictionary keys are `BasketItem.Id` values (as strings in legacy), not `CatalogItem.Id` values. The Java target should deserialize them as integers.
5. **Legacy key type is string.** `Dictionary<string, int> quantities` — keys are `item.Id.ToString()` from the caller. The Java target may use integer keys directly in the request DTO.
6. **Basket must exist.** No lazy creation — `SetQuantities` returns `Result.NotFound()` if the basket row does not exist. The REST target should return 404.
7. **UnitPrice is not changed.** `SetQuantity` only mutates `Quantity`; `UnitPrice` on each `BasketItem` remains the price recorded when the item was first added.

## Non-functional

- Mutating: reads Baskets + BasketItems, writes (updates and deletes) BasketItems.
- No authentication required on the endpoint.
- Called when the user submits the basket quantity form — low frequency, one call per "Update" button click.
- All changes to a basket's items are flushed in a single `UpdateAsync` call — EF Core unit-of-work; not individually transactional per item.
