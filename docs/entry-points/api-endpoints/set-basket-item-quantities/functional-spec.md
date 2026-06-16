# Functional spec — Set basket item quantities

**Key:** `set-basket-item-quantities`
**Legacy:** `BasketService.SetQuantities(basketId, Dictionary<string, int>)`
**Target REST:** `PUT /api/baskets/{basketId}/items`

## Purpose

Update the quantity of multiple items in a basket in a single call. Any item
with a new quantity of `0` is removed from the basket.

## Inputs

```json
{
  "quantities": {
    "100": 3,
    "101": 0
  }
}
```

Keys are **BasketItem ids** (stringified), values are the new quantity.
`basketId` comes from the path.

## Outputs

The updated basket (same shape as `get-basket-for-user`).

## Acceptance criteria

```
Scenario: Update quantity of one item
  Given basket 42 has BasketItems [{id:100, qty:1}, {id:101, qty:2}]
  When PUT /api/baskets/42/items with { "quantities": { "100": 5 } }
  Then BasketItems row 100 now has Quantity = 5
  And row 101 is unchanged
  And the response includes both rows

Scenario: Zero quantity deletes
  Given basket 42 has BasketItems [{id:100, qty:1}]
  When PUT /api/baskets/42/items with { "quantities": { "100": 0 } }
  Then BasketItems row 100 is deleted
  And response.items is []

Scenario: Unknown basketId
  Given no Baskets row with Id = 9999
  When PUT /api/baskets/9999/items is called
  Then the response is 404 (Result<Basket>.NotFound in legacy)
  And no DB writes occur

Scenario: Partial update leaves other items alone
  Given basket 42 has BasketItems [100, 101, 102]
  When PUT is called with { "quantities": { "100": 4 } }
  Then only row 100 is updated
  And rows 101 and 102 are unchanged

Scenario: Negative quantity rejected
  Given quantities = { "100": -1 }
  When the endpoint is called
  Then the server rejects (Guard.Against.OutOfRange in BasketItem.SetQuantity)
  And no partial writes are persisted
```

## Business rules

- **Partial update semantics.** Only the BasketItem ids present in `quantities` are
  modified; missing ids are left alone.
- **Zero deletes.** Setting `quantity = 0` results in the row being deleted as part
  of the same transaction (`Basket.RemoveEmptyItems`).
- **Negative rejected.** `BasketItem.SetQuantity` guards against negatives.
- **Basket must exist.** Returns `NotFound` if `basketId` is unknown.
