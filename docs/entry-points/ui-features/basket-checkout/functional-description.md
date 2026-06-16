# Functional Description: Checkout Review

> **Entry Point**: `basket-checkout`
> **Location**: `src/Web/Pages/Basket/Checkout.cshtml`
> **Type**: UI / Page
> **Domain**: catalog
> **Legacy URL**: `/basket/checkout`

## Executive Summary

The Checkout Review page is the final confirmation step before a shopper commits to a purchase. It displays the current basket contents (product images, names, unit prices, quantities, and line totals) in a read-only format, along with the basket total, giving the user a last chance to review their order before payment. The page is protected by `[Authorize]` — unauthenticated visitors are redirected to the login page by ASP.NET Core before any handler code runs.

`OnGet` loads the basket and renders the review. `OnPost` (triggered by "Pay Now") executes three sequential mutations: it first applies the hidden quantities from the form back to the basket (via `SetQuantities`), then creates the order record (via `CreateOrderAsync`), and finally deletes the basket (via `DeleteBasketAsync`). A successful submission redirects to `/basket/success`. If the basket turns out to be empty when `CreateOrderAsync` runs (e.g., a race condition or concurrent session), an `EmptyBasketOnCheckoutException` is caught and the user is redirected back to `/basket` with no order created.

Two aspects are particularly significant for migration. First, the shipping address is hardcoded server-side as `"123 Main St., Kent, OH, United States, 44240"` — there is no address-entry UI in the legacy application. The Spring Boot / Angular rebuild must introduce real address capture. Second, prices on the order are snapshotted from `BasketItem.UnitPrice` (the price at add-to-basket time), not re-read from `CatalogItem.Price` at checkout — this price-lock behaviour must be preserved.

---

## User Inputs

### Form Fields

| Field Name | C# Type | Source | Required | Notes |
| --- | --- | --- | --- | --- |
| `Items[i].Id` | `int` | Hidden `<input>` — `name="Items[i].Id"` — rendered by view loop | yes | Basket item primary key; binds to `IEnumerable<BasketItemViewModel> items` in `OnPost` |
| `Items[i].Quantity` | `int` | Hidden `<input>` — `name="Items[i].Quantity"` — rendered by view loop | yes | Quantity as loaded from server; not editable by user. Posted back to ensure SetQuantities has correct values |

> **Note**: There are no `[BindProperty]` fields on `CheckoutModel`. `BasketModel` is a get-only property populated by `SetBasketModelAsync()`. The items come in as the `items` parameter to `OnPost`.

> **Note**: Quantity is intentionally read-only on this page. The `<input type="hidden">` for quantity is rendered alongside the plain-text display `@item.Quantity` — the user cannot change quantities here. Quantity editing belongs to the Basket page (`/basket`).

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
| --- | --- | --- | --- |
| Place order | `<input type="submit" value="[ Pay Now ]">` | `OnPost` — POST to `/basket/checkout` | Form submit |
| Back to basket | `<a asp-page="Index">[ Back ]</a>` | GET `/basket` | Navigation |
| Continue Shopping (empty state) | `<a asp-page="/Index">[ Continue Shopping ]</a>` | GET `/` | Navigation |

### URL / Route Parameters

| Parameter | Source | Optional | Default | Notes |
| --- | --- | --- | --- | --- |
| *(none)* | — | — | — | `@page` directive has no route template; the page is only reachable at `/basket/checkout` |

### Browser / Session Inputs

| Source | Data | Purpose |
| --- | --- | --- |
| `HttpContext.User.Identity.Name` | Authenticated username | Primary buyer identity used to look up the basket via `GetOrCreateBasketForUser` |
| `SignInManager<ApplicationUser>.IsSignedIn` | Boolean | Guards which identity path `SetBasketModelAsync` takes — always true under `[Authorize]` |
| Cookie `Constants.BASKET_COOKIENAME` | GUID string | Fallback buyer identity if `IsSignedIn` is false (unreachable path under `[Authorize]`) |

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
| --- | --- | --- | --- |
| Hero banner | Static image `main_banner_text.png` | Always | `Checkout.cshtml:6–10` |
| "Review" heading | `<h1>Review</h1>` | Always | `Checkout.cshtml:13` |
| Validation summary | `<div asp-validation-summary="All">` | Always (empty if no errors) | `Checkout.cshtml:26` |
| Items table | Rows for each basket item: product image (hidden on small screens), name, unit price, hidden Id/Quantity inputs, plain-text quantity, line total | `BasketModel.Items.Any()` | `Checkout.cshtml:27–48` |
| Product image | `<img src="@item.PictureUrl">` hidden below lg breakpoint | Per item | `Checkout.cshtml:33` |
| Product name | `@item.ProductName` | Per item | `Checkout.cshtml:35` |
| Unit price | `$ @item.UnitPrice.ToString("N2")` | Per item | `Checkout.cshtml:36` |
| Quantity display | `@item.Quantity` as plain text (NOT an editable input) | Per item | `Checkout.cshtml:40` |
| Line total | `$ @Math.Round(item.Quantity * item.UnitPrice, 2).ToString("N2")` | Per item | `Checkout.cshtml:42` |
| Basket total row | `$ @Model.BasketModel.Total().ToString("N2")` | Items present | `Checkout.cshtml:58` |
| Back button | `[ Back ]` link → `/basket` | Items present | `Checkout.cshtml:67` |
| Pay Now button | `<input type="submit" value="[ Pay Now ]">` | Items present | `Checkout.cshtml:70` |
| Empty-state message | `"Basket is empty."` | `!BasketModel.Items.Any()` | `Checkout.cshtml:78–80` |
| Continue Shopping link | `[ Continue Shopping ]` → `/` | Empty state | `Checkout.cshtml:82–84` |

### Navigation / Routing

| Trigger | Destination | Condition |
| --- | --- | --- |
| Unauthenticated request | Login page (ASP.NET Core Identity default) | `[Authorize]` attribute — before any handler runs |
| `OnPost` — `ModelState.IsValid == false` | HTTP 400 BadRequest (no redirect; no page rendered) | Posted form fails model binding |
| `OnPost` — `EmptyBasketOnCheckoutException` caught | `/basket` (`RedirectToPage("/Basket/Index")`) | Basket empty at `CreateOrderAsync` time |
| `OnPost` — success | `/basket/success` (`RedirectToPage("Success")`) | Order created and basket deleted |
| Back button | GET `/basket` | User clicks `[ Back ]` |
| Continue Shopping | GET `/` | User clicks `[ Continue Shopping ]` (empty state only) |

### State Changes

| State | Change | Trigger | Notes |
| --- | --- | --- | --- |
| `BasketItems` rows | Updated (quantities); rows with Quantity=0 deleted | `OnPost` → `SetQuantities` | Applied before order creation; quantities reflect the hidden-field values from the posted form |
| `Orders` row | Inserted | `OnPost` → `CreateOrderAsync` | `BuyerId = basket.BuyerId`, `OrderDate = DateTimeOffset.Now`, `ShipToAddress` hardcoded |
| `OrderItems` rows | Inserted (one per basket item) | `OnPost` → `CreateOrderAsync` → `IRepository<Order>.AddAsync` | Cascade insert; `UnitPrice` and `Units` from basket; `CatalogItemOrdered` is a point-in-time snapshot |
| `Baskets` row | Deleted | `OnPost` → `DeleteBasketAsync` | Cascade deletes all associated `BasketItems` rows |
| Cookie `Constants.BASKET_COOKIENAME` | Written (GUID, 10-year expiry) | `GetOrSetBasketCookieAndUserName` — only if `IsSignedIn` is false | Dead code path under `[Authorize]`; included for completeness |

---

## API Dependencies

### Service Calls

| Service Method | When Called | Data In | Data Out |
| --- | --- | --- | --- |
| `IBasketViewModelService.GetOrCreateBasketForUser` | `OnGet` (via `SetBasketModelAsync`), `OnPost` (via `SetBasketModelAsync`) | `username` (`User.Identity.Name`) | `BasketViewModel` assigned to `BasketModel` |
| `IBasketService.SetQuantities` | `OnPost` | `BasketModel.Id`, `Dictionary<string, int>` (item ID → quantity from hidden fields) | `Result<Basket>` (implicit to `Basket`); mutates `BasketItems` in DB |
| `IOrderService.CreateOrderAsync` | `OnPost` | `BasketModel.Id`, hardcoded `Address` | `void` (inserts `Orders` + `OrderItems`); throws `EmptyBasketOnCheckoutException` if basket is empty |
| `IBasketService.DeleteBasketAsync` | `OnPost` (after `CreateOrderAsync`) | `BasketModel.Id` | `void`; deletes `Baskets` row + cascade `BasketItems` |

### Call Sequences

**OnGet:**
1. `[Authorize]` — if not authenticated, middleware redirects to login; handler never runs
2. `SetBasketModelAsync()`:
   - `SignInManager.IsSignedIn(HttpContext.User)` → true (always under `[Authorize]`)
   - `GetOrCreateBasketForUser(User.Identity.Name)`:
     - `FirstOrDefaultAsync(BasketWithItemsSpecification(buyerId))` — SELECT Baskets WHERE BuyerId = username, eager-load BasketItems
     - If no basket: `AddAsync(new Basket(username))` — INSERT; return empty view model
     - If basket exists: `Map(basket)` → `GetBasketItems()` → `ListAsync(CatalogItemsSpecification(ids))` — SELECT CatalogItems WHERE Id IN [...] for Name, PictureUri
     - `IUriComposer.ComposePicUri` per item — relative → absolute PictureUri
3. Render page with `BasketModel`

**OnPost (Pay Now):**
1. `[Authorize]` — guaranteed authenticated
2. `SetBasketModelAsync()` — re-fetches basket server-side to get `BasketModel.Id` (same DB sequence as OnGet)
3. `ModelState.IsValid` check — if false, return `BadRequest()` immediately
4. Build `updateModel = items.ToDictionary(b => b.Id.ToString(), b => b.Quantity)`
5. `SetQuantities(BasketModel.Id, updateModel)`:
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(basketId))` — SELECT by int Id
   - `item.SetQuantity(qty)` per item in dictionary
   - `basket.RemoveEmptyItems()` — removes items with Quantity=0
   - `UpdateAsync(basket)` — UPDATE BasketItems quantities; DELETE zero-quantity rows
6. `CreateOrderAsync(BasketModel.Id, new Address("123 Main St.", "Kent", "OH", "United States", "44240"))`:
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(basketId))` — SELECT Baskets again
   - `Guard.Against.EmptyBasketOnCheckout(basket.Items)` — throws `EmptyBasketOnCheckoutException` if empty
   - `ListAsync(CatalogItemsSpecification(ids))` — SELECT CatalogItems for Id, Name, PictureUri (NOT Price)
   - Build `OrderItem(CatalogItemOrdered, basketItem.UnitPrice, basketItem.Quantity)` per item
   - `AddAsync(new Order(basket.BuyerId, shippingAddress, items))` — INSERT Orders + OrderItems
7. `DeleteBasketAsync(BasketModel.Id)`:
   - `GetByIdAsync(basketId)` — SELECT Baskets by Id (no eager load needed)
   - `DeleteAsync(basket)` — DELETE Baskets; cascade DELETE BasketItems
8. `RedirectToPage("Success")` → GET `/basket/success`

**Exception path (EmptyBasketOnCheckoutException):**
- Caught in `catch` block in `OnPost`
- `_logger.LogWarning(emptyBasketOnCheckoutException.Message)`
- `RedirectToPage("/Basket/Index")` → GET `/basket`

---

## State Management

### BindProperty Fields

| Property | Type | Notes |
| --- | --- | --- |
| *(none)* | — | `CheckoutModel` has no `[BindProperty]` fields. `BasketModel` is a server-populated read-only property. `items` is bound as a method parameter on `OnPost`. |

### Method Parameter Binding (OnPost)

| Parameter | Type | Binding Source | Notes |
| --- | --- | --- | --- |
| `items` | `IEnumerable<BasketItemViewModel>` | Form fields `Items[i].Id` and `Items[i].Quantity` (both hidden inputs) | Each `BasketItemViewModel` must expose `Id` (int) and `Quantity` (int) |

### Cookie / Session State

| Name | Read in | Written in | Purpose |
| --- | --- | --- | --- |
| `Constants.BASKET_COOKIENAME` | `GetOrSetBasketCookieAndUserName` (unreachable under `[Authorize]`) | `GetOrSetBasketCookieAndUserName` (unreachable under `[Authorize]`) | Anonymous buyer identity fallback — dead path for this page |
| `HttpContext.User` | `SetBasketModelAsync` | ASP.NET Core Identity middleware | Authenticated buyer identity — always available under `[Authorize]` |

---

## Component Details

### PageModel: `CheckoutModel`

**File**: `src/Web/Pages/Basket/Checkout.cshtml.cs`

**Authorization**: `[Authorize]` at class level — all handlers require authentication

**Injected services**:
- `IBasketService` — `SetQuantities`, `DeleteBasketAsync`
- `IBasketViewModelService` — `GetOrCreateBasketForUser`
- `SignInManager<ApplicationUser>` — `IsSignedIn` check in `SetBasketModelAsync`
- `IOrderService` — `CreateOrderAsync`
- `IAppLogger<CheckoutModel>` — warning logging on empty-basket exception

**Properties**:
- `BasketModel` (`BasketViewModel`, public get/set) — populated by `SetBasketModelAsync`; initialized to `new BasketViewModel()` (empty) to prevent null reference on render

**Handlers**:
- `OnGet()` → `Task` — loads basket, renders review page
- `OnPost(IEnumerable<BasketItemViewModel> items)` → `Task<IActionResult>` — places order; wrapped in try/catch for `EmptyBasketOnCheckoutException`

**Private helpers**:
- `SetBasketModelAsync()` — called by both `OnGet` and `OnPost`; branches on `IsSignedIn` (cookie path is dead code under `[Authorize]`)
- `GetOrSetBasketCookieAndUserName()` — GUID cookie read/create (dead code path)

### View Template: `Checkout.cshtml`

**Key sections**:
- Hero banner (static image)
- `<h1>Review</h1>` heading
- Conditional on `Model.BasketModel.Items.Any()`:
  - Items review form (`<form asp-page="Checkout" method="post">`)
    - `<div asp-validation-summary="All">` — for model validation errors
    - `@for` loop over `BasketModel.Items` with column layout: product image, name, unit price, hidden Id/Quantity, plain-text quantity, line total
    - Basket total row
    - `[ Back ]` link and `[ Pay Now ]` submit button
  - Else: "Basket is empty." + `[ Continue Shopping ]` link

### Partials Included

*(None — Checkout.cshtml includes no `<partial>` tags)*

### Referenced Services (Implementation Files)

| Service | Implementation File |
| --- | --- |
| `IOrderService` | `src/ApplicationCore/Services/OrderService.cs` |
| `IBasketService` | `src/ApplicationCore/Services/BasketService.cs` |
| `IBasketViewModelService` | `src/Web/Services/BasketViewModelService.cs` |

---

## Workflows

### Workflow 1: View Checkout Review (OnGet)

**Use case**: Authenticated shopper navigates to `/basket/checkout` to review their order before paying.

**Preconditions**: User is authenticated (enforced by `[Authorize]`). User navigates to `/basket/checkout` via GET.

**Steps**:

1. **Authentication gate**
   - `[Authorize]` attribute — if the request is unauthenticated, ASP.NET Core Identity redirects to the configured login URL before this handler runs. No basket query occurs.

2. **Load basket**
   - `SetBasketModelAsync()` is called.
   - `SignInManager.IsSignedIn(HttpContext.User)` → true.
   - `GetOrCreateBasketForUser(User.Identity.Name)`:
     - Queries `Baskets` by `BuyerId = username`, eager-loading `BasketItems`.
     - If no basket row: inserts one and returns an empty `BasketViewModel`.
     - If basket exists: joins `BasketItems` with `CatalogItems` to resolve `Name` and `PictureUri` per item. `IUriComposer.ComposePicUri` converts relative picture paths to absolute URLs.
   - Result assigned to `BasketModel`.

3. **Render review page**
   - If `BasketModel.Items.Any()`: render the items review table with read-only quantities, basket total, `[ Back ]` and `[ Pay Now ]` buttons.
   - If items empty: render "Basket is empty." + `[ Continue Shopping ]` link.

**Success outcome**: Shopper sees a read-only summary of their basket with a "Pay Now" button.

---

### Workflow 2: Place Order (OnPost)

**Use case**: Authenticated shopper clicks `[ Pay Now ]` to commit the purchase.

**Preconditions**: Shopper is authenticated. POST arrives at `/basket/checkout` with `Items[i].Id` and `Items[i].Quantity` hidden fields for each basket item.

**Steps**:

1. **Re-load basket server-side**
   - `SetBasketModelAsync()` — same sequence as OnGet. Obtains `BasketModel.Id` (the trusted basket primary key from the server; the client does not supply this).

2. **Validate model state**
   - If `ModelState.IsValid == false`: return `BadRequest()` (HTTP 400). No order is created. No user-facing error page is rendered.

3. **Sync quantities**
   - Build `updateModel = items.ToDictionary(b => b.Id.ToString(), b => b.Quantity)`.
   - `IBasketService.SetQuantities(BasketModel.Id, updateModel)`:
     - Loads basket by integer `basketId`.
     - Calls `item.SetQuantity(qty)` per item present in `updateModel`.
     - `basket.RemoveEmptyItems()` removes items with `Quantity == 0`.
     - `UpdateAsync(basket)` persists quantity UPDATEs and zero-quantity DELETEs to `BasketItems`.
   - **Why this step?** Although quantities are read-only on this page, the same mechanism used by the Basket page's `OnPostUpdate` is reused here to ensure the DB basket is consistent with what was displayed when the order is created.

4. **Create order**
   - `IOrderService.CreateOrderAsync(BasketModel.Id, new Address("123 Main St.", "Kent", "OH", "United States", "44240"))`:
     - Re-queries `Baskets` by `Id` (third DB query for baskets in this request).
     - `Guard.Against.EmptyBasketOnCheckout(basket.Items)` — if `Items` is empty, throws `EmptyBasketOnCheckoutException` (caught below).
     - Fetches `CatalogItems` by id list for `Id`, `Name`, `PictureUri` (NOT `Price`).
     - Builds `CatalogItemOrdered(catalogItemId, name, absolutePictureUri)` snapshot per item.
     - Constructs `OrderItem(itemOrdered, basketItem.UnitPrice, basketItem.Quantity)` — price comes from `BasketItem.UnitPrice` (locked at add-to-basket time).
     - `new Order(basket.BuyerId, shippingAddress, items)` — `OrderDate = DateTimeOffset.Now` set in constructor.
     - `IRepository<Order>.AddAsync(order)` — INSERT `Orders` row + cascade INSERT `OrderItems` rows.

5. **Delete basket**
   - `IBasketService.DeleteBasketAsync(BasketModel.Id)`:
     - `GetByIdAsync(basketId)` — SELECT basket by Id.
     - `DeleteAsync(basket)` — DELETE `Baskets` row; EF cascade DELETE all `BasketItems` rows.

6. **Redirect to success**
   - `RedirectToPage("Success")` → GET `/basket/success`.

**Exception path — EmptyBasketOnCheckoutException:**
- Thrown by `Guard.Against.EmptyBasketOnCheckout` inside `CreateOrderAsync` when `basket.Items` is empty after `SetQuantities`.
- Caught by the `catch (EmptyBasketOnCheckoutException)` block in `OnPost`.
- `_logger.LogWarning(exception.Message)` — warning level, not error.
- `RedirectToPage("/Basket/Index")` → GET `/basket`.
- No `Orders` or `OrderItems` rows are inserted. `DeleteBasketAsync` is NOT called (basket is empty but row still exists).

**Success outcome**: Order record created, basket cleared, shopper redirected to `/basket/success`.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
| --- | --- | --- |
| Page load | None (server-rendered, synchronous) | Page arrives fully rendered |

### Error States

| Error | Display | HTTP Status | Recovery |
| --- | --- | --- | --- |
| `ModelState.IsValid == false` | No page rendered — raw HTTP 400 response | 400 Bad Request | No user-facing guidance; a browser refresh re-navigates to OnGet |
| `EmptyBasketOnCheckoutException` | Silent redirect to `/basket` | 302 → GET `/basket` | User sees their (now empty) basket page |
| `Guard.Against.Null(basket)` in `CreateOrderAsync` | Unhandled exception → 500 | 500 | Would occur if basket was deleted between `SetQuantities` and `CreateOrderAsync` — race condition |
| Unauthenticated access | Redirect to login page | 302 → login | User logs in and is returned to the page |

### Empty States

| Context | Message | Actions available |
| --- | --- | --- |
| Basket has no items | "Basket is empty." | `[ Continue Shopping ]` link → `/` |

### Success States

| Action | Feedback | Next state |
| --- | --- | --- |
| Pay Now (happy path) | Redirect to `/basket/success` | Order confirmed page |

---

## Use Cases

### UC-1: Review order before paying

**User story**: As an authenticated shopper, I want to see a final summary of my basket (product names, quantities, prices, and total) before I pay so that I can confirm I'm buying the right items.

**Workflow**: Workflow 1 (View Checkout Review)

### UC-2: Place order

**User story**: As an authenticated shopper, I want to click Pay Now to create my order and have my basket cleared so that my purchase is confirmed.

**Workflow**: Workflow 2 (Place Order)

### UC-3: Go back to edit basket

**User story**: As a shopper reviewing my order, I want to go back to my basket to adjust quantities or remove items before paying.

**Interaction**: `[ Back ]` link → GET `/basket`

### UC-4: Handle empty basket at checkout

**User story**: As a shopper, if my basket is empty when I reach checkout (e.g., session expired, concurrent device), I want to be returned to the basket page rather than shown a broken checkout experience.

**Workflow**: Workflow 2 — `EmptyBasketOnCheckoutException` exception path

### UC-5: Authenticated-only access

**User story**: As an unauthenticated visitor who bookmarks `/basket/checkout`, I want to be prompted to log in so that my order is associated with my account.

**Mechanism**: `[Authorize]` attribute — ASP.NET Core Identity middleware handles the redirect before any handler runs.

---

## Security Considerations

### Authentication

- **Required**: Yes — `[Authorize]` at the class level. All handlers require an authenticated user. There is no anonymous checkout path.
- **Enforcement**: ASP.NET Core Identity redirects to `/Identity/Account/Login?ReturnUrl=%2Fbasket%2Fcheckout` before `OnGet` or `OnPost` runs. The Spring Boot target must enforce equivalent authentication at the endpoint level.

### Basket ID Trust

- **Critical**: `BasketModel.Id` (used by `SetQuantities`, `CreateOrderAsync`, `DeleteBasketAsync`) is obtained server-side via `SetBasketModelAsync()` — it is resolved from `User.Identity.Name`, not taken from the POST body. The client cannot forge or substitute a different basket ID. The Spring Boot target must derive basket identity from the authenticated principal, not a client-supplied parameter.

### Price Integrity

- **Price lock**: `OrderItem.UnitPrice` is set from `BasketItem.UnitPrice` (the price at add-to-basket time). `CatalogItem.Price` is NOT read during checkout. This means price changes after an item is added to the basket do not affect the order total. This is intentional business behaviour that must be preserved in the Angular/Spring Boot target.

### CSRF

- Razor Pages `<form asp-page="Checkout" method="post">` generates an anti-forgery token automatically via tag helpers. The Spring Boot target must implement equivalent CSRF protection (e.g., Spring Security CSRF tokens or SameSite cookie).

### ModelState Validation Failure Response

- `BadRequest()` returns HTTP 400 with no body. There is no user-facing error message. The Angular target may want to return a structured error response instead.

---

## Accessibility Considerations

- Quantities are shown as plain text next to hidden `<input type="hidden">` elements — screen readers will read the text quantity without also announcing the hidden input.
- No ARIA roles on the table-like layout (CSS grid with `<article>` / `<section>` elements) — screen readers may not announce column headers for data rows. The Angular rebuild should use a proper `<table>` with `<th>` headers.
- Column headers ("Product", "Price", "Quantity", "Cost") are in separate `<section>` elements above the data rows — they are not associated with the data cells via `<th scope="col">`.
- `[ Back ]` and `[ Pay Now ]` are labelled by their visible text — adequate for screen readers.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
| --- | --- | --- |
| `Baskets` + `BasketItems` tables | Basket contents, quantities, item prices | Empty basket shown on OnGet; `EmptyBasketOnCheckoutException` on OnPost |
| `CatalogItems` table | Item names and picture URIs for display (OnGet) and order snapshots (OnPost) | Items shown without names/images; order snapshots would be incomplete |
| `HttpContext.User` / ASP.NET Core Identity | Authenticated username | Page inaccessible without auth; `Guard.Against.Null` on `User.Identity.Name` throws if name absent |

### Downstream

| System | What this page affects | How |
| --- | --- | --- |
| `Orders` table | Creates one order per successful checkout | `IOrderService.CreateOrderAsync` → `IRepository<Order>.AddAsync` |
| `OrderItems` table | Creates one row per basket item in the order | Cascade insert via EF |
| `Baskets` + `BasketItems` tables | Deletes the basket and all its items | `IBasketService.DeleteBasketAsync` → `DeleteAsync` (EF cascade) |
| `/basket/success` page | Redirect target after successful order | `RedirectToPage("Success")` |
| `/basket` page | Redirect target on empty-basket exception | `RedirectToPage("/Basket/Index")` |

---

## Analysis Notes

- **Hardcoded shipping address**: `new Address("123 Main St.", "Kent", "OH", "United States", "44240")` is baked into `OnPost`. There is no address form, no address entity on the user profile, and no address validation. The Spring Boot rebuild must introduce an address-entry step (either before checkout or on the checkout page itself). This is flagged in `metadata.json`.

- **Four Baskets SELECTs in a single OnPost request**: `SetBasketModelAsync` (1), `SetQuantities` (2), `CreateOrderAsync` (3), `DeleteBasketAsync` (4) each execute `FirstOrDefaultAsync` or `GetByIdAsync` on the `Baskets` table independently. The Spring Boot port should load the basket once and pass it through the service chain rather than re-querying per step.

- **`SetQuantities` in OnPost is redundant for normal flow**: The quantities posted as hidden fields mirror exactly what was rendered in OnGet (they are server-generated hidden inputs, not editable by the user). In practice `SetQuantities` does not change anything unless a zero-quantity item was somehow posted. However, the pattern is preserved to maintain consistency with the Basket page's update flow. The Angular target might consider whether this step is needed.

- **`EmptyBasketOnCheckoutException` race condition**: If a shopper opens two tabs and submits both concurrently, the second `CreateOrderAsync` call will find an empty basket (the first submission deleted it) and redirect to `/basket` silently. No duplicate-order protection exists beyond this guard. Consider idempotency keys in the Spring Boot target.

- **`BadRequest()` on model validation failure**: HTTP 400 with no body is returned when `ModelState.IsValid` is false. There is no UI shown to the user and no error message. The Angular/Spring Boot target should return a structured error response.

- **`Guard.Against.Null(User?.Identity?.Name)`**: `SetBasketModelAsync` guards against a null username at the top of the method. Under `[Authorize]` this should never be null, but it would throw an `ArgumentNullException` (not caught) if it were. The Spring Boot target should handle this via authentication enforcement rather than a runtime guard.

- **`GetOrSetBasketCookieAndUserName` is dead code**: Because `[Authorize]` is at the class level, `_signInManager.IsSignedIn(HttpContext.User)` will always be `true` when any handler runs. The `else` branch in `SetBasketModelAsync` and the entire `GetOrSetBasketCookieAndUserName` method are unreachable. The Angular/Spring Boot rebuild can omit this path.

- **`CatalogItemOrdered` is a point-in-time snapshot**: The `ItemOrdered_ProductName` and `ItemOrdered_PictureUri` stored with each `OrderItem` are the name and image URI at checkout time, not current catalog values. This means order history remains accurate even if catalog items are later renamed or have their images changed. The Angular target must preserve this snapshot pattern.

- **`OrderDate` precision**: `new Order(...)` sets `OrderDate = DateTimeOffset.Now` in the `Order` constructor. The time zone is the server's local time zone, not UTC. The Spring Boot target should use UTC (`Instant.now()` / `ZonedDateTime.now(ZoneOffset.UTC)`).
