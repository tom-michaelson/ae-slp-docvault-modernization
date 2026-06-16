# Functional spec — Basket

**Key:** `basket-list`
**URL:** `GET /basket` · `POST /basket` · `POST /basket?handler=Update`
**Legacy source:** `src/Web/Pages/Basket/Index.cshtml` + `src/Web/Pages/Basket/Index.cshtml.cs`

## Purpose

The Basket page shows the shopper every item currently in their cart, lets them adjust quantities and remove items, and provides the path to checkout. It also doubles as the HTTP target for Add to Basket form submissions from the catalog page — making it a three-handler page that acts as the hub for all basket mutations.

## Functional behavior

### OnGet — view basket

1. Calls `IndexModel.GetOrSetBasketCookieAndUserName()`:
   - If the user is authenticated (`User.Identity.IsAuthenticated`), returns their username.
   - Otherwise, reads `Request.Cookies[Constants.BASKET_COOKIENAME]`.
   - If no valid GUID cookie is found, generates a new GUID, writes it to `Response.Cookies[Constants.BASKET_COOKIENAME]` (essential, 10-year expiry), and returns it.
2. Calls `IBasketViewModelService.GetOrCreateBasketForUser(cookieOrUserName)`:
   - Queries `Baskets` by `BuyerId` via `BasketWithItemsSpecification` (eager-loads `BasketItems`).
   - If no basket row exists, inserts a new `Basket` and returns an empty `BasketViewModel`.
   - If basket exists, calls `Map(basket)` → `GetBasketItems()` → queries `CatalogItems` by id list to resolve `Name` and `PictureUri`.
3. Assigns result to `CatalogModel`; renders page.

### OnPost — add item from catalog

1. Accepts `CatalogItemViewModel productDetails` from the catalog `_product.cshtml` POST form.
2. If `productDetails?.Id == null`, redirects to `/Index` (catalog homepage).
3. Calls `_itemRepository.GetByIdAsync(productDetails.Id)` — queries `CatalogItems` by Id.
4. If item not found, redirects to `/Index`.
5. Calls `GetOrSetBasketCookieAndUserName()` to resolve buyer identity.
6. Calls `IBasketService.AddItemToBasket(username, productDetails.Id, item.Price)`:
   - Queries `Baskets` by `BuyerId`; creates basket row if none exists.
   - Calls `basket.AddItem(catalogItemId, price, quantity=1)`:
     - If item already in basket, increments its `Quantity`.
     - Otherwise appends a new `BasketItem`.
   - Calls `_basketRepository.UpdateAsync(basket)` — persists new/updated `BasketItems` row.
7. Calls `IBasketViewModelService.Map(basket)` to rebuild the view model.
8. Redirects to `/basket` (`RedirectToPage()`).

### OnPostUpdate — update quantities

1. Checks `ModelState.IsValid`; if invalid, returns without redirect (page re-renders with current `BasketModel`).
2. Calls `GetOrSetBasketCookieAndUserName()` to resolve buyer identity.
3. Calls `IBasketViewModelService.GetOrCreateBasketForUser(...)` — fetches current basket.
4. Builds `updateModel` dictionary: `{ Items[i].Id.ToString() → Items[i].Quantity }` from posted form values.
5. Calls `IBasketService.SetQuantities(basketView.Id, updateModel)`:
   - Queries `Baskets` by basketId; returns `Result.NotFound()` if missing.
   - For each `BasketItem` in basket: if Id present in `updateModel`, calls `item.SetQuantity(quantity)`.
   - Calls `basket.RemoveEmptyItems()` — removes all items where `Quantity == 0` from the in-memory list.
   - Calls `_basketRepository.UpdateAsync(basket)` — persists quantity UPDATEs and zero-quantity DELETEs.
   - Returns `Result<Basket>` (Ardalis.Result); implicit operator converts to `Basket` before `Map()` call.
6. Calls `IBasketViewModelService.Map(basket)` — reloads `BasketModel` for re-render.
7. No redirect — stays on `/basket`.

## Acceptance criteria

```gherkin
Scenario: Anonymous user — first visit creates cookie and empty basket
  Given the shopper has never visited the site
  When they navigate to "/basket"
  Then a new GUID cookie is written to the response (Constants.BASKET_COOKIENAME, 10-year expiry)
  And a new Baskets row is inserted with BuyerId = that GUID
  And the page renders "Basket is empty."
  And no form is shown

Scenario: Returning anonymous user — basket loaded from cookie
  Given the shopper has a valid GUID cookie and a basket with 2 items
  When they navigate to "/basket"
  Then the existing cookie is read; no new cookie is written
  And the basket form renders 2 item rows with quantities and line totals
  And the total row shows the correct sum

Scenario: Add item to basket (happy path)
  Given a CatalogItem with Id=5 exists in the database
  And the catalog page POSTs id=5 to "/basket"
  When OnPost runs
  Then the CatalogItem is fetched by Id to resolve its price
  And the item is added to the basket at the server-side price (client price is ignored)
  And the response is a redirect to "/basket"

Scenario: Add item — null product ID guard
  Given the POST body contains a null Id
  When OnPost runs
  Then the handler redirects to "/Index" without touching the basket

Scenario: Add item — catalog item not found
  Given the POST body contains Id=999 which does not exist in CatalogItems
  When OnPost runs
  Then GetByIdAsync returns null
  And the handler redirects to "/Index"

Scenario: Update quantities (happy path)
  Given the basket contains items with Ids [10, 11, 12] and quantities [2, 1, 3]
  When the shopper changes item 11 to quantity 2 and clicks [Update]
  Then OnPostUpdate updates item 11's quantity to 2 in BasketItems
  And the page re-renders with updated line totals
  And no redirect occurs

Scenario: Update with quantity 0 removes item
  Given the basket contains item Id=10 with quantity 2
  When the shopper sets quantity to 0 and clicks [Update]
  Then SetQuantities calls item.SetQuantity(0) then basket.RemoveEmptyItems()
  And the BasketItems row for item 10 is deleted
  And the page re-renders without that item

Scenario: ModelState invalid on update
  Given the posted form data fails model binding
  When OnPostUpdate runs
  Then ModelState.IsValid is false
  And the handler returns early without calling SetQuantities
  And the page re-renders (BasketModel remains at its previous state)
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Empty-state message | conditional text — "Basket is empty." | `Index.cshtml:82-84` |
| Basket items form | `<form method="post">` — renders when `BasketModel.Items.Any()` | `Index.cshtml:16-78` |
| Items loop | `@for` over `BasketModel.Items` (index-bound for model binding) | `Index.cshtml:27-47` |
| Product image per row | `<img src="@item.PictureUrl">` — hidden on screens below lg | `Index.cshtml:33` |
| Product name per row | text — `@item.ProductName` | `Index.cshtml:35` |
| Unit price per row | text — `$ @item.UnitPrice.ToString("N2")` | `Index.cshtml:36` |
| Item Id hidden input | `<input type="hidden" name="Items[i].Id">` | `Index.cshtml:38` |
| Quantity input per row | `<input type="number" min="0" name="Items[i].Quantity">` — editable | `Index.cshtml:39` |
| Line total per row | computed text — `$ @(item.Quantity × item.UnitPrice).ToString("N2")` | `Index.cshtml:41` |
| Basket total row | text — `$ @Model.BasketModel.Total().ToString("N2")` | `Index.cshtml:57` |
| Update button | `<button type="submit" asp-page-handler="Update">[ Update ]</button>` | `Index.cshtml:70` |
| Checkout link | anchor `asp-page="./Checkout"` → `/basket/checkout` | `Index.cshtml:74` |
