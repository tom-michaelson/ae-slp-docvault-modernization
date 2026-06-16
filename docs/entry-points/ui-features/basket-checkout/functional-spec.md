# Functional spec — Checkout Review

**Key:** `basket-checkout`
**URL:** `GET /basket/checkout` · `POST /basket/checkout`
**Legacy source:** `src/Web/Pages/Basket/Checkout.cshtml` + `src/Web/Pages/Basket/Checkout.cshtml.cs`

## Purpose

The Checkout Review page lets an authenticated shopper review their basket items and totals one final time before committing to purchase. Clicking Pay Now creates the order, clears the basket, and redirects to a success page — making this the single page in the flow that transitions the user's cart into a permanent order record.

## Functional behavior

### OnGet — load review

1. `[Authorize]` on `CheckoutModel` — unauthenticated requests are intercepted by ASP.NET Core and redirected to the login page before this handler runs.
2. Calls `CheckoutModel.SetBasketModelAsync()` (line 70):
   - If `SignInManager.IsSignedIn(HttpContext.User)` is true, calls `IBasketViewModelService.GetOrCreateBasketForUser(User.Identity.Name)`.
   - Otherwise, calls `CheckoutModel.GetOrSetBasketCookieAndUserName()` (reads/creates cookie) and then `GetOrCreateBasketForUser(_username)`. In practice this branch is unreachable under `[Authorize]`.
3. `GetOrCreateBasketForUser` queries `Baskets` by `BuyerId` (eager-loads `BasketItems`); if no basket exists, inserts one and returns an empty view model.
4. If basket has items, calls `BasketViewModelService.Map(basket)` → `GetBasketItems()` → queries `CatalogItems` by id list for `Name` and `PictureUri`.
5. Assigns result to `BasketModel`; renders the review page.

### OnPost — place order

1. Calls `SetBasketModelAsync()` — re-fetches the basket server-side to obtain `BasketModel.Id` (the client cannot supply a trusted basket ID).
2. Checks `ModelState.IsValid`; if false, returns `BadRequest()` (HTTP 400) — no user-facing error page rendered.
3. Builds `updateModel` dictionary from posted `Items[i].Id → Items[i].Quantity` hidden fields (quantities are read-only on this page; values match what was loaded in OnGet).
4. Calls `IBasketService.SetQuantities(BasketModel.Id, updateModel)`:
   - Queries `Baskets` by `Id`; applies `item.SetQuantity()` per item; calls `basket.RemoveEmptyItems()` (removes items where Quantity=0); persists via `UpdateAsync`.
5. Calls `IOrderService.CreateOrderAsync(BasketModel.Id, address)`:
   - `address` is hardcoded as `new Address("123 Main St.", "Kent", "OH", "United States", "44240")`.
   - Re-queries `Baskets` by `Id`; calls `Guard.Against.EmptyBasketOnCheckout(basket.Items)` — throws `EmptyBasketOnCheckoutException` if Items is empty.
   - Queries `CatalogItems` by id list for `Id`, `Name`, `PictureUri` to build `CatalogItemOrdered` snapshots.
   - Constructs `Order(buyerId, shippingAddress, orderItems)`; each `OrderItem` carries `CatalogItemOrdered`, `basketItem.UnitPrice`, and `basketItem.Quantity`.
   - Inserts order via `IRepository<Order>.AddAsync(order)` — cascade inserts `OrderItems`.
6. Calls `IBasketService.DeleteBasketAsync(BasketModel.Id)` — fetches basket by Id, calls `DeleteAsync`; EF cascade deletes all `BasketItems` rows.
7. Redirects to `"Success"` → `/basket/success`.
8. **Exception path:** If `EmptyBasketOnCheckoutException` is thrown (step 5), logs a warning and redirects to `/Basket/Index` (`/basket`) without creating an order.

## Acceptance criteria

```gherkin
Scenario: Unauthenticated user is redirected to login
  Given the shopper is not signed in
  When they navigate to "/basket/checkout"
  Then ASP.NET Core redirects them to the login page (before OnGet runs)
  And no basket query is executed

Scenario: Authenticated user views non-empty basket
  Given the shopper is signed in and has 3 items in their basket
  When they navigate to "/basket/checkout"
  Then the review table renders 3 rows with product image, name, unit price, quantity (read-only), and line total
  And the footer shows the correct basket total
  And quantities are displayed as text, not editable inputs

Scenario: Authenticated user views empty basket
  Given the shopper is signed in and their basket is empty
  When they navigate to "/basket/checkout"
  Then BasketModel.Items is empty
  And the page renders "Basket is empty." with no form

Scenario: Pay Now — happy path
  Given the shopper is signed in with 2 items in their basket
  When they click Pay Now
  Then SetQuantities is called with the hidden Id/Quantity pairs from the form
  And CreateOrderAsync inserts one Orders row and two OrderItems rows
  And the shipping address on the order is "123 Main St., Kent, OH, United States, 44240"
  And DeleteBasketAsync removes the Baskets row and cascades to BasketItems
  And the response is a redirect to "/basket/success"

Scenario: Pay Now — basket emptied between OnGet and OnPost
  Given the shopper's basket is empty when OnPost calls CreateOrderAsync
  When OnPost runs
  Then Guard.Against.EmptyBasketOnCheckout throws EmptyBasketOnCheckoutException
  And the exception is caught; a warning is logged
  And the response is a redirect to "/basket" (no order is created)

Scenario: Pay Now — ModelState invalid
  Given the posted form data fails model binding
  When OnPost runs
  Then ModelState.IsValid is false
  And the handler returns HTTP 400 BadRequest
  And no SetQuantities, CreateOrderAsync, or DeleteBasketAsync calls are made

Scenario: Order line item prices are not re-fetched from catalog
  Given a catalog item's price changed after it was added to the basket
  When the shopper checks out
  Then the OrderItem.UnitPrice equals BasketItem.UnitPrice (price at add-to-basket time)
  And CatalogItem.Price is not read during checkout
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Review heading | text — "Review" | `Checkout.cshtml:13` |
| Empty-state message | conditional text — "Basket is empty." | `Checkout.cshtml:78-80` |
| Order review form | `<form asp-page="Checkout" method="post">` — renders when basket is non-empty | `Checkout.cshtml:16-74` |
| Items loop | `@for` over `BasketModel.Items` (index-bound for hidden field model binding) | `Checkout.cshtml:27-48` |
| Product image per row | `<img src="@item.PictureUrl">` — hidden on screens below lg | `Checkout.cshtml:33` |
| Product name per row | text — `@item.ProductName` | `Checkout.cshtml:35` |
| Unit price per row | text — `$ @item.UnitPrice.ToString("N2")` | `Checkout.cshtml:36` |
| Item Id hidden input | `<input type="hidden" name="Items[i].Id">` | `Checkout.cshtml:38` |
| Quantity hidden input | `<input type="hidden" name="Items[i].Quantity">` (read-only display, not editable) | `Checkout.cshtml:39` |
| Quantity display text | `@item.Quantity` — shown as plain text, not an input | `Checkout.cshtml:40` |
| Line total per row | computed text — `$ @(item.Quantity × item.UnitPrice).ToString("N2")` | `Checkout.cshtml:42` |
| Basket total row | text — `$ @Model.BasketModel.Total().ToString("N2")` | `Checkout.cshtml:58` |
| Pay Now button | `<input type="submit" value="[ Pay Now ]">` | `Checkout.cshtml:70` |

## Out of scope

| Element | Reason |
|---|---|
| Shipping address form | No address UI exists in the legacy app — address is hardcoded server-side. The Spring Boot rebuild must introduce address capture. |
| `/basket/success` page | Redirect target after order creation; belongs to a separate feature key. |
