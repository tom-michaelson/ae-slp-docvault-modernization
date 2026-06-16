# Functional spec — Delete basket (clear after checkout)

**Key:** `delete-item-in-basket`
**Legacy:** `BasketService.DeleteBasketAsync(basketId)` — called from `CheckoutModel.OnPost`
**Target REST:** `DELETE /api/baskets/{basketId}`

## Purpose

Permanently deletes a basket and all its items. In the legacy app this is called as the final cleanup step of the checkout flow — after the order is successfully created, the basket is purged. The Angular checkout flow will call this endpoint at the same point in the sequence.

## Inputs

| Name | Type | In | Optional | Notes |
| --- | --- | --- | --- | --- |
| `basketId` | int | path | no | Baskets.Id integer PK of the basket to delete |

No request body.

## Outputs

HTTP 204 No Content on success (no response body).

Legacy `DeleteBasketAsync` returns `Task` (void) — there is no response object to map.

## Acceptance criteria

```gherkin
Scenario: Delete existing basket
  Given Basket id=7 exists with 3 BasketItems rows
  When DELETE /api/baskets/7
  Then the Baskets row id=7 is deleted
  And all 3 BasketItems rows for basket id=7 are deleted
  And response status is 204 No Content

Scenario: Basket not found returns 404
  Given no Basket exists with id=999
  When DELETE /api/baskets/999
  Then response status is 404 Not Found
  (Legacy Guard.Against.Null throws ArgumentNullException → HTTP 500; REST target MUST return 404)

Scenario: Empty basket can be deleted
  Given Basket id=5 exists with 0 BasketItems rows
  When DELETE /api/baskets/5
  Then the Baskets row id=5 is deleted
  And response status is 204 No Content

Scenario: Called within checkout sequence
  Given a valid basket and a successfully created order
  When the checkout flow calls DELETE /api/baskets/{basketId} as the last step
  Then the basket is removed
  And the user is redirected to the Success page (handled by Angular, not this endpoint)
```

## Business rules

1. **Whole-basket delete, not single-item.** This operation removes the Basket row AND all its BasketItems rows via cascade delete. It is not possible to delete a single item using this endpoint — use `update-item-in-basket` (PUT with quantity=0) for item-level removal.
2. **Must not be called if order creation fails.** The legacy `CheckoutModel.OnPost` catches `EmptyBasketOnCheckoutException` and redirects without calling `DeleteBasketAsync`. The REST caller (Angular checkout service) must only call this endpoint after receiving a successful order creation response.
3. **404 on missing basket.** Legacy `Guard.Against.Null(basket, nameof(basket))` throws `ArgumentNullException` which surfaces as HTTP 500. The Java `@DeleteMapping` handler must explicitly check for null and return `ResponseEntity.notFound()` (HTTP 404).
4. **No partial deletion.** The entire basket is removed atomically — Basket row + all BasketItems rows — in a single `DeleteAsync` call. There is no rollback path within the service.
5. **basketId is integer PK.** The service takes `int basketId` (Baskets.Id), not a buyerId string. The caller must have already resolved the basket's integer ID before invoking this endpoint.
6. **Caller requires authentication.** `CheckoutModel` is `[Authorize]` — this endpoint is only called from authenticated checkout flows in legacy. The Java `@DeleteMapping` should require JWT authentication even though the service layer itself has no auth guard.

## Non-functional

- Mutating: deletes Baskets row and all child BasketItems rows (cascade).
- Called once per successful checkout — very low frequency, one call per completed order.
- Always the last step in the checkout sequence — never called in isolation by the UI.
- Legacy page requires `[Authorize]`; the REST target should require JWT authentication.
