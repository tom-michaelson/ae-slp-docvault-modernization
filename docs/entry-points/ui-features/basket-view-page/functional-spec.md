# Functional spec — Basket view page

**Key:** `basket-view-page`
**URL:** `GET /Basket` (plus `POST /Basket` for add, `POST /Basket?handler=Update` for update)
**Legacy source:** `src/Web/Pages/Basket/Index.cshtml` + `Index.cshtml.cs`

## Purpose

Shows the shopper the items currently in their basket, lets them adjust
quantities, and provides the jumping-off point to checkout. Also serves as the
HTTP target for "Add to basket" posts from the catalog.

## Functional behavior

### OnGet — view

1. Resolves the basket owner:
   - If `HttpContext.User` is authenticated, use `User.Identity.Name`.
   - Else read the `eShop` cookie for a GUID; if absent or invalid, mint a new
     GUID and set the cookie (10-year expiry, essential cookie).
2. Calls `IBasketViewModelService.GetOrCreateBasketForUser(username)` to fetch
   the basket or create an empty one.
3. Renders `BasketViewModel` into the page.

### OnPost — add item

1. Accepts a `CatalogItemViewModel` (from the catalog's "Add to basket" button).
2. If `productDetails.Id` is null OR the catalog item doesn't exist, redirect to `/Index`.
3. Otherwise, loads the current price from the `CatalogItem` repository and calls
   `IBasketService.AddItemToBasket(username, productId, price)`.
4. Redirects back to the basket page (`RedirectToPage()`).

### OnPostUpdate — update quantities (handler=Update)

1. Reads the list of `BasketItemViewModel { Id, Quantity }` posted from the form.
2. If `ModelState.IsValid` is false, returns without modifying the basket.
3. Loads the current basket for the user.
4. Builds `Dictionary<string, int>` (basket-item id → quantity) and calls
   `IBasketService.SetQuantities(basketId, dict)`.
5. Re-maps the resulting basket and re-renders the page.

## Acceptance criteria (Gherkin)

```
Scenario: First-time anonymous visit creates cookie + empty basket
  Given the shopper has never visited the site
  When they navigate to "/Basket"
  Then a new GUID cookie "eShop" is set on the response
  And a new Baskets row is created with BuyerId = <that GUID>
  And the page renders "Basket is empty."

Scenario: View basket with items
  Given the basket has two BasketItems
  When the shopper navigates to "/Basket"
  Then each item's picture, name, unit price, quantity, and line total are shown
  And the footer shows the sum of (Quantity * UnitPrice) as "Total"

Scenario: Add item from catalog
  Given the shopper is on the catalog page
  When they click "[ ADD TO BASKET ]" for a catalog item
  Then a POST to "/Basket" is issued with that item's Id
  And the BasketItems table reflects the added item (qty += 1 if duplicate)
  And the response is a 302 back to "/Basket"

Scenario: Update quantities
  Given the basket has items with ids X and Y
  When the shopper changes X quantity to 3, Y quantity to 0, and submits "[ Update ]"
  Then BasketItems.Quantity for X becomes 3
  And the BasketItems row for Y is deleted (RemoveEmptyItems)

Scenario: Checkout link
  Given the basket has at least one item
  When the shopper clicks "[ Checkout ]"
  Then they are routed to /Basket/Checkout
```

## UI elements

| Element | Kind | Source ref |
| --- | --- | --- |
| Hero banner image | img | `Index.cshtml:7` |
| Empty-state message | text | `Index.cshtml:83` |
| Continue Shopping (empty) | link | `Index.cshtml:87` |
| Items table header row | static row | `Index.cshtml:17-24` |
| Item rows | loop over `Model.BasketModel.Items` | `Index.cshtml:27-47` |
| Qty input per item | `<input type="number" min="0">` | `Index.cshtml:39` |
| Total row | computed (sum of line totals) | `Index.cshtml:55-58` |
| Continue Shopping (full) | link | `Index.cshtml:66` |
| Update button | submit (handler=Update) | `Index.cshtml:70-73` |
| Checkout link | link to `/Basket/Checkout` | `Index.cshtml:74` |
