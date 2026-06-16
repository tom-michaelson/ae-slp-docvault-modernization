# Functional spec — Get or create basket for user

**Key:** `get-basket-for-user`
**Legacy:** `BasketViewModelService.GetOrCreateBasketForUser(userName)`
**Target REST:** `GET /api/baskets/for-user/{buyerId}`

## Purpose

Return the current user's basket (hydrated with items, product name, and picture URL).
Lazily creates an empty basket if none exists so callers don't have to branch.

## Inputs

| Name | Type | Notes |
| --- | --- | --- |
| `buyerId` | string | Authenticated user's username OR anonymous GUID from the basket cookie |

## Outputs

```json
{
  "id": 42,
  "buyerId": "evan@example.com",
  "items": [
    {
      "id": 100,
      "catalogItemId": 1,
      "productName": ".NET Bot Black Sweatshirt",
      "pictureUrl": "https://…/images/products/1.png",
      "unitPrice": 19.50,
      "quantity": 2
    }
  ]
}
```

## Acceptance criteria

```
Scenario: Existing basket
  Given a Basket row exists with BuyerId = "evan@example.com" and 1 BasketItem
  When GET /api/baskets/for-user/evan@example.com is called
  Then the response Id matches the Basket row
  And items.length == 1 with product name, picture URL, quantity, unitPrice populated

Scenario: No basket — lazy create
  Given no Basket row exists for BuyerId = "<guid>"
  When GET /api/baskets/for-user/<guid> is called
  Then a new Baskets row is inserted with BuyerId = <guid>
  And the response has items == []

Scenario: Item metadata hydration
  Given the basket has a BasketItem with CatalogItemId = 7
  When the basket is fetched
  Then items[0].productName == Catalog.Name for id 7
  And items[0].pictureUrl == UriComposer.ComposePicUri(Catalog.PictureUri for id 7)
```

## Business rules

- Empty basket is a valid state; never return 404 for "no basket yet".
- Item metadata (name, picture) is joined from `Catalog`; legacy does this via a
  `CatalogItemsSpecification` over the set of CatalogItemIds on the basket.
- `pictureUrl` is always the output of `IUriComposer.ComposePicUri`, never the raw
  stored relative path.
