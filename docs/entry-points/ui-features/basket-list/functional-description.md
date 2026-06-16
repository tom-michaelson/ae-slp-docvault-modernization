# Functional Description: Basket

> **Entry Point**: `basket-list`
> **Location**: `src/Web/Pages/Basket/Index.cshtml`
> **Type**: UI / Page
> **Domain**: catalog
> **Legacy URL**: `/basket`

## Executive Summary

The Basket page is the central hub for all shopping cart operations in eShopOnWeb. It handles three distinct operations on a single page: viewing the basket contents (`OnGet`), adding an item from the catalog (`OnPost`), and updating item quantities in bulk (`OnPostUpdate`). Both anonymous and authenticated users can access the page — anonymous identity is tracked via a GUID stored in a long-lived cookie, while authenticated users are identified by their ASP.NET Identity username. Either way, the buyer identity resolves through the same private helper `GetOrSetBasketCookieAndUserName()`.

Anonymous basket state is created lazily: neither the `Baskets` row nor the cookie is written until the first visit to `/Basket` or first Add to Basket action. When a user authenticates, the anonymous basket is transferred to their account via `BasketService.TransferBasketAsync` — this merge is triggered by the Identity login flow, not by this page directly. On return visits, the page reads the existing basket from the database and displays all items with live pricing from `CatalogItems`.

The `OnPost` handler is the POST target for the `[ ADD TO BASKET ]` form rendered by the `_product.cshtml` partial on the catalog homepage. It validates the item ID, reads the current price server-side from `CatalogItems` (discarding any client-supplied price), adds or increments the item in the basket, and redirects back via PRG. The `OnPostUpdate` handler — invoked by the `[ Update ]` button on the basket page itself — does **not** redirect; it re-renders the page directly after applying quantity changes, which means a browser back-button press will replay the POST.

## User Inputs

### Form Fields

`BasketModel` is **not** a `[BindProperty]`. Item quantities are received in `OnPostUpdate` as a method parameter (`IEnumerable<BasketItemViewModel> items`) bound from the form's indexed input names. No `[BindProperty]` attributes are used anywhere in `IndexModel`.

| Field Name | C# Type | Source | Required | Notes |
|---|---|---|---|---|
| `Items[i].Id` | `int` | Hidden input `name="Items[i].Id"` in item loop; bound to `OnPostUpdate` `items` parameter | Yes | `BasketItem.Id` (not `CatalogItemId`). Used to match posted quantities to basket rows |
| `Items[i].Quantity` | `int` | Number input `name="Items[i].Quantity"` `min="0"` in item loop; bound to `OnPostUpdate` `items` parameter | Yes | Min 0 — setting to 0 deletes the item via `RemoveEmptyItems()` |

**OnPost fields** (from `_product.cshtml` form POSTing to this handler):

| Field Name | C# Type | Source | Required | Notes |
|---|---|---|---|---|
| `productDetails.Id` | `int?` | Hidden `name="id"` in `_product.cshtml` | Yes (guard) | `CatalogItem.Id` — null triggers redirect to `/Index` |
| `productDetails.Name` | `string` | Hidden `name="name"` in `_product.cshtml` | No | Received but not used server-side; name read from DB |
| `productDetails.PictureUri` | `string` | Hidden `name="pictureUri"` in `_product.cshtml` | No | Received but not used server-side |
| `productDetails.Price` | `decimal` | Hidden `name="price"` in `_product.cshtml` | No | **Ignored** — price read from `CatalogItem.Price` in DB |

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
|---|---|---|---|
| Update quantities | `<button asp-page-handler="Update">[ Update ]</button>` | `OnPostUpdate` | Form POST — entire item form submitted with `handler=Update` |
| Continue Shopping | `<a asp-page="/Index">[ Continue Shopping ]</a>` | `/` catalog homepage | GET navigation link — available in both empty and loaded states |
| Checkout | `<a asp-page="./Checkout">[ Checkout ]</a>` | `/Basket/Checkout` | GET navigation link — only visible when basket has items |
| Add to Basket | `<input type="submit" value="[ ADD TO BASKET ]">` in `_product.cshtml` | `OnPost` via POST form | Form POST from catalog page — **handled here but triggered from catalog** |

### URL / Route Parameters

None. The basket page accepts no query string or route parameters for data retrieval. The page route is `@page "{handler?}"` — the optional `{handler?}` segment supports `asp-page-handler="Update"` routing (generates URL `/Basket/Update` or `?handler=Update`).

### Browser / Session Inputs

| Source | Data | Purpose |
|---|---|---|
| Cookie `Constants.BASKET_COOKIENAME` (`eShop`) | GUID string | Anonymous buyer identity — must be a valid GUID or it is discarded and replaced |
| `HttpContext.User.Identity.IsAuthenticated` | bool | If `true`, bypass cookie; use `User.Identity.Name` instead |
| `HttpContext.User.Identity.Name` | string (username) | Authenticated buyer identity — used as `BuyerId` in `Baskets` table |

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source Ref |
|---|---|---|---|
| Hero banner | Static `<img src="~/images/main_banner_text.png">` | Always | `Index.cshtml:6–10` |
| Items form | `<form method="post">` containing the full basket table | `BasketModel.Items.Any()` | `Index.cshtml:16–78` |
| Column header row | Static labels: Product, Price, Quantity, Cost | Items present | `Index.cshtml:17–24` |
| Item rows | Loop: image (hidden below lg), name, unit price, quantity input, line total | Items present; one row per `BasketItem` | `Index.cshtml:27–47` |
| Total row | `$ @Model.BasketModel.Total().ToString("N2")` | Items present | `Index.cshtml:57` |
| Continue Shopping link | `<a asp-page="/Index">` | Always (in form and empty-state) | `Index.cshtml:66`, `87` |
| Update button | `<button asp-page-handler="Update">[ Update ]</button>` | Items present | `Index.cshtml:70–73` |
| Checkout link | `<a asp-page="./Checkout">[ Checkout ]</a>` | Items present | `Index.cshtml:74` |
| Empty-state heading | `<h3>Basket is empty.</h3>` | `!BasketModel.Items.Any()` | `Index.cshtml:82–84` |

**Per item row fields rendered:**

| Field | C# source | Notes |
|---|---|---|
| Product image | `item.PictureUrl` (absolute URL) | Hidden below `lg` breakpoint via `hidden-lg-down` class |
| Product name | `item.ProductName` | Fetched from `CatalogItems.Name` via `GetBasketItems` |
| Unit price | `$ @item.UnitPrice.ToString("N2")` | `BasketItem.UnitPrice` stored at time of add |
| Quantity input | `name="Items[i].Quantity"` value=`item.Quantity` | Editable; min=0 |
| Hidden Id | `name="Items[i].Id"` value=`item.Id` | `BasketItem.Id` (PK) |
| Line total | `$ @Math.Round(item.Quantity * item.UnitPrice, 2).ToString("N2")` | Computed client-side in Razor; not from DB |

### Navigation / Routing

| Trigger | Destination | Condition |
|---|---|---|
| `OnPost` with null `productDetails.Id` | `/Index` (catalog homepage) | Immediate redirect |
| `OnPost` with missing catalog item | `/Index` | Redirect after `GetByIdAsync` returns null |
| `OnPost` success | `/Basket` (`RedirectToPage()`) | PRG redirect after basket update |
| Update button → `OnPostUpdate` | Stay on `/Basket` (no redirect) | Page re-renders in-place with updated totals |
| Continue Shopping link | `/` (catalog homepage) | User navigation |
| Checkout link | `/Basket/Checkout` | User navigation — only visible when items present |

### State Changes

| State | Change | Trigger | Notes |
|---|---|---|---|
| Cookie `BASKET_COOKIENAME` | Written with `IsEssential=true`, 10-year expiry | `GetOrSetBasketCookieAndUserName()` on any handler, first anonymous visit | Only if no valid GUID cookie exists; not written in `OnPost` if guards redirect first |
| `Baskets` row | Inserted (lazy creation) | `GetOrCreateBasketForUser` (OnGet, OnPostUpdate) or `AddItemToBasket` (OnPost) when no basket exists for this buyer | One row per buyer; `BuyerId` is the cookie GUID or username |
| `BasketItems` row | Inserted | `OnPost` → `AddItemToBasket` → `basket.AddItem` | New row per unique `CatalogItemId`; existing row has `Quantity` incremented |
| `BasketItems.Quantity` | Updated | `OnPostUpdate` → `SetQuantities` → `item.SetQuantity(qty)` | Sets to posted value |
| `BasketItems` row | Deleted | `OnPostUpdate` → `SetQuantities` → `basket.RemoveEmptyItems()` | Removes rows where `Quantity == 0` before `UpdateAsync` |

---

## API Dependencies

### Service Calls

| Service Method | When Called | Data In | Data Out |
|---|---|---|---|
| `IBasketViewModelService.GetOrCreateBasketForUser` | `OnGet`, `OnPostUpdate` | `username` (string) | `BasketViewModel` |
| `IRepository<CatalogItem>.GetByIdAsync` | `OnPost` | `productDetails.Id` | `CatalogItem` (price only used) |
| `IBasketService.AddItemToBasket` | `OnPost` | `username`, `catalogItemId`, `item.Price` | `Basket` |
| `IBasketViewModelService.Map` | `OnPost`, `OnPostUpdate` | `Basket` | `BasketViewModel` |
| `IBasketService.SetQuantities` | `OnPostUpdate` | `basketView.Id` (int), `Dictionary<string, int>` | `Result<Basket>` |
| `IRepository<Basket>.FirstOrDefaultAsync(BasketWithItemsSpecification)` | Inside `GetOrCreateBasketForUser`, `AddItemToBasket`, `SetQuantities` | `buyerId` string or `basketId` int | `Basket?` with `Items` eagerly loaded |
| `IRepository<Basket>.AddAsync` | `CreateBasketForUser`, `AddItemToBasket` (when no basket) | new `Basket(buyerId)` | — |
| `IRepository<Basket>.UpdateAsync` | `AddItemToBasket`, `SetQuantities` | modified `Basket` | — |
| `IRepository<CatalogItem>.ListAsync(CatalogItemsSpecification)` | Inside `GetBasketItems` (called by `Map`, `GetOrCreateBasketForUser`) | `int[]` of `CatalogItemId`s | `IList<CatalogItem>` (Name, PictureUri) |
| `IUriComposer.ComposePicUri` | Inside `GetBasketItems`, per item | relative `PictureUri` | absolute URL string |

### Call Sequences

**OnGet:**
1. `GetOrSetBasketCookieAndUserName()` → resolve buyer identity (cookie or auth username); write cookie if absent
2. `GetOrCreateBasketForUser(username)`:
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(username))` → SELECT from `Baskets` WHERE `BuyerId = username` with `Items` eagerly loaded
   - If null: insert new `Baskets` row; return empty `BasketViewModel`
   - If exists: `Map(basket)` → `GetBasketItems(basket.Items)` → `ListAsync(CatalogItemsSpecification(ids))` → compose picture URIs
3. Assign to `BasketModel`; render page

**OnPost:**
1. Guard: if `productDetails?.Id == null` → `RedirectToPage("/Index")`
2. `GetByIdAsync(productDetails.Id)` → SELECT `CatalogItems` by Id; if null → `RedirectToPage("/Index")`
3. `GetOrSetBasketCookieAndUserName()` → resolve buyer identity (only reached if guards pass)
4. `AddItemToBasket(username, productDetails.Id, item.Price)`:
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(username))` → find basket
   - If null: insert new `Baskets` row
   - `basket.AddItem(catalogItemId, price, quantity=1)` → increment if exists, insert if new
   - `UpdateAsync(basket)` → persist changes to `Baskets` + `BasketItems`
5. `Map(basket)` → reload `BasketViewModel` (SELECT `CatalogItems` for names/pictures)
6. `RedirectToPage()` → PRG back to `GET /Basket`

**OnPostUpdate:**
1. If `!ModelState.IsValid` → return (no changes, page re-renders with current `BasketModel`)
2. `GetOrSetBasketCookieAndUserName()` → resolve buyer identity
3. `GetOrCreateBasketForUser(username)` → reload current `BasketViewModel` (to get `basketView.Id`)
4. Build `Dictionary<string, int>`: `items.ToDictionary(b => b.Id.ToString(), b => b.Quantity)`
5. `SetQuantities(basketView.Id, updateModel)`:
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(basketId))` → find basket by integer Id
   - If null: returns `Result<Basket>.NotFound()` (no exception)
   - Per item in basket: if id in dict, call `item.SetQuantity(quantity)`
   - `basket.RemoveEmptyItems()` → remove items with `Quantity == 0`
   - `UpdateAsync(basket)` → UPDATEs quantities, DELETEs removed items
   - Returns `Result<Basket>` (implicit operator converts to `Basket`)
6. `Map(basket)` → rebuild `BasketViewModel`; assign to `BasketModel`
7. Return (no redirect) — page re-renders with updated totals

---

## State Management

### BindProperty Fields

None. `IndexModel` has no `[BindProperty]` attributes. `BasketModel` is a plain property assigned in handler methods:

```csharp
public BasketViewModel BasketModel { get; set; } = new BasketViewModel();
```

Items for `OnPostUpdate` are received as a method parameter (`IEnumerable<BasketItemViewModel> items`), bound from the form's `Items[i].Id` and `Items[i].Quantity` indexed inputs.

### Cookie / Session State

| Name | Read in | Written in | Lifetime | Purpose |
|---|---|---|---|---|
| `Constants.BASKET_COOKIENAME` (`eShop`) | `OnGet`, `OnPost`, `OnPostUpdate` (via `GetOrSetBasketCookieAndUserName`) | Same method, on first anonymous visit | 10 years from today (`DateTime.Today.AddYears(10)`) | Persists anonymous buyer identity as GUID across sessions |
| `HttpContext.User` | `GetOrSetBasketCookieAndUserName` | ASP.NET Identity middleware (login flow) | Session (auth cookie) | Authenticated buyer identity |

---

## Component Details

### PageModel: `IndexModel`

**File**: `src/Web/Pages/Basket/Index.cshtml.cs`

**Injected services**: `IBasketService`, `IBasketViewModelService`, `IRepository<CatalogItem>`

**Properties**:
- `BasketModel` (`BasketViewModel`) — plain property, NOT `[BindProperty]`; initialized to empty `BasketViewModel`

**Handlers**:
- `OnGet()` — async; loads basket for current buyer; no parameters
- `OnPost(CatalogItemViewModel productDetails)` — async; receives posted catalog item form data; returns `IActionResult`
- `OnPostUpdate(IEnumerable<BasketItemViewModel> items)` — async; receives form array of item updates; returns `void` (no redirect)

**Private helpers**:
- `GetOrSetBasketCookieAndUserName()` — resolves buyer identity; validates GUID if anonymous; creates and appends new GUID cookie if needed; called at start of every handler (except `OnPost` which calls it after guards)

**Authentication**: None — no `[Authorize]` attribute. Accessible to anonymous users.

### View Template: `Index.cshtml`

**Route**: `@page "{handler?}"` — optional `{handler?}` segment enables `asp-page-handler` routing

**Key sections**:
- Hero banner section (static `<img>`)
- Conditional branch on `Model.BasketModel.Items.Any()`:
  - **True branch** (items present): `<form method="post">` with column headers, indexed `@for` loop over items, total row, Continue Shopping link, Update button (`asp-page-handler="Update"`), Checkout link
  - **False branch** (empty basket): `<h3>Basket is empty.</h3>` + Continue Shopping link

### Partials Included

None. The basket page does not include any `<partial>` tags. The `_product.cshtml` partial is used on the **catalog homepage** and POSTs to this page — it is not rendered here.

---

## Workflows

### Workflow 1: View Basket (OnGet)

**Use case**: Shopper navigates to `/Basket` to review their cart contents.

**Preconditions**: Any visitor (anonymous or authenticated) performs a GET to `/Basket`.

**Steps**:

1. **Resolve buyer identity** (`GetOrSetBasketCookieAndUserName`)
   - If `User.Identity.IsAuthenticated`: return `User.Identity.Name`
   - Else if `BASKET_COOKIENAME` cookie exists AND its value is a valid GUID: return the GUID string
   - Else: generate `Guid.NewGuid().ToString()`, write cookie (`IsEssential=true`, expires `DateTime.Today.AddYears(10)`), return new GUID

2. **Load or create basket** (`GetOrCreateBasketForUser`)
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(username))` → SELECT `Baskets` WHERE `BuyerId = username` with `BasketItems` eagerly loaded
   - If no basket row: INSERT new `Baskets` row; return `BasketViewModel { Id, BuyerId, Items=[] }`
   - If basket exists: `Map(basket)`:
     - `GetBasketItems(basket.Items)` → SELECT `CatalogItems` WHERE `Id IN (item.CatalogItemIds)` → join with basket items to populate `ProductName`, `PictureUrl` (via `ComposePicUri`), `UnitPrice`, `Quantity`

3. **Render page**
   - If `BasketModel.Items.Any()`: render items table with quantity inputs, total row, Update and Checkout actions
   - If `!BasketModel.Items.Any()`: render "Basket is empty." heading with Continue Shopping link

**Success outcome**: Page renders with current basket contents or empty-state message.

---

### Workflow 2: Add Item to Basket (OnPost)

**Use case**: Shopper clicks `[ ADD TO BASKET ]` on a product tile on the catalog page.

**Preconditions**: POST arrives at `/Basket` from `_product.cshtml` form with `CatalogItemViewModel` fields.

**Steps**:

1. **Guard: null product ID**
   - If `productDetails?.Id == null` → `RedirectToPage("/Index")`; stop. Cookie is NOT written in this path.

2. **Guard: item existence and price lookup**
   - `GetByIdAsync(productDetails.Id)` → SELECT `CatalogItems` by Id
   - If item not found → `RedirectToPage("/Index")`; stop
   - `item.Price` is the server-side authoritative price — the `price` field POSTed by the form is **not used**

3. **Resolve buyer identity**
   - `GetOrSetBasketCookieAndUserName()` — same logic as Workflow 1 step 1
   - Cookie is written here if this is the buyer's first interaction

4. **Add item to basket** (`AddItemToBasket`)
   - `FirstOrDefaultAsync(BasketWithItemsSpecification(username))` → find buyer's basket
   - If no basket: INSERT new `Baskets` row
   - `basket.AddItem(catalogItemId, price, quantity=1)`:
     - If `CatalogItemId` already in `basket.Items`: increment existing `BasketItem.Quantity` by 1
     - If new: append a new `BasketItem(catalogItemId, price, quantity=1)` to the collection
   - `UpdateAsync(basket)` → persist: UPDATE `Baskets`, INSERT or UPDATE `BasketItems`

5. **Rebuild view model** (`Map(basket)`) — reloads item details from `CatalogItems`

6. **Redirect** — `RedirectToPage()` → GET `/Basket` (PRG pattern)

**Success outcome**: Item added or incremented; shopper lands on basket page via GET.

---

### Workflow 3: Update Quantities (OnPostUpdate)

**Use case**: Shopper edits quantity inputs on the basket page and clicks `[ Update ]`.

**Preconditions**: POST arrives at `/Basket/Update` (or `?handler=Update`) with form array of `Items[i].Id` and `Items[i].Quantity`.

**Steps**:

1. **Validate model state**
   - If `!ModelState.IsValid` → return immediately (no redirect, no DB changes); page re-renders with current `BasketModel` (default empty — note: this means the page re-renders blank if model binding fails)

2. **Resolve buyer identity** and **reload basket**
   - `GetOrSetBasketCookieAndUserName()` — resolve buyer
   - `GetOrCreateBasketForUser(username)` → reload `BasketViewModel` (needed for `basketView.Id`)

3. **Build quantity update map**
   - `items.ToDictionary(b => b.Id.ToString(), b => b.Quantity)` → `{"itemId" → newQuantity}`

4. **Apply quantities** (`SetQuantities(basketView.Id, updateModel)`)
   - SELECT basket by integer `basketId` with items eagerly loaded
   - If basket not found: return `Result<Basket>.NotFound()` — no exception; implicit operator converts to null `Basket`
   - For each `BasketItem` whose `Id` is in the dictionary: call `item.SetQuantity(newQuantity)`
   - `basket.RemoveEmptyItems()` → remove all items where `Quantity == 0` from in-memory collection
   - `UpdateAsync(basket)` → persist: UPDATE quantity rows, DELETE zero-quantity rows

5. **Rebuild view model** (`Map(basket)`)
   - `Result<Basket>` is implicitly converted to `Basket` via Ardalis.Result operator before passing to `Map`
   - `Map` calls `GetBasketItems` to reload `ProductName`, `PictureUrl` from `CatalogItems`

6. **Re-render page** — no redirect (stays on `/Basket`); updated `BasketModel` drives the view

**Success outcome**: Quantities updated; page re-renders with new quantities and totals.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
|---|---|---|
| Page load | None | Synchronous server-rendered; page arrives fully populated |

### Error States

| Error | Display | Recovery |
|---|---|---|
| `productDetails.Id` is null on `OnPost` | Silent redirect to `/Index` | User returns to catalog |
| `CatalogItem` not found on `OnPost` | Silent redirect to `/Index` | User returns to catalog |
| `ModelState.IsValid == false` on `OnPostUpdate` | Page re-renders with blank `BasketModel` (empty state appearance) | User must navigate back and retry |
| `SetQuantities` basket not found | `Result.NotFound()` returned; `Map(null)` would throw — potential unhandled exception | Rare edge case; basket should always exist at this point |

### Empty States

| Context | Message | Actions available |
|---|---|---|
| Basket has no items (first visit or all items removed) | "Basket is empty." (`<h3>`) | "[ Continue Shopping ]" link → `/` |

### Success States

| Action | Feedback | Next state |
|---|---|---|
| `OnGet` with items | Items table with quantities, unit prices, line totals, basket total | User can update or checkout |
| `OnPost` (Add to Basket) | Redirect to `/Basket` GET | Basket shows added/incremented item |
| `OnPostUpdate` | Page re-renders in-place | Updated quantities and totals visible immediately |

---

## Use Cases

### UC-1: View basket before checkout

**User story**: As a shopper, I want to see all items in my basket so I can review my order before paying.

**Workflow**: Workflow 1 (View Basket — OnGet)

### UC-2: Add a product to the basket

**User story**: As a shopper, I want to add a product from the catalog to my basket so I can purchase it.

**Workflow**: Workflow 2 (Add Item — OnPost); initiated from `_product.cshtml` on the catalog page

### UC-3: Adjust item quantities

**User story**: As a shopper, I want to change how many of each item I want before checkout.

**Workflow**: Workflow 3 (Update Quantities — OnPostUpdate)

### UC-4: Remove an item by zeroing its quantity

**User story**: As a shopper, I want to remove an unwanted item by setting its quantity to 0.

**Workflow**: Workflow 3 — quantity `0` triggers `RemoveEmptyItems()` which deletes the `BasketItems` row

### UC-5: Proceed to checkout

**User story**: As a shopper, I want to proceed from my basket to the checkout flow.

**Workflow**: User clicks `[ Checkout ]` link → navigates to `/Basket/Checkout` (handled by `basket-checkout` feature — out of scope here)

### UC-6: Return to catalog from empty basket

**User story**: As a shopper with an empty basket, I want a way back to the catalog to continue shopping.

**Workflow**: User clicks `[ Continue Shopping ]` link → navigates to `/` catalog homepage

---

## Security Considerations

### Authentication

- **Required**: No — no `[Authorize]` attribute. Anonymous users can view, add items to, and update their basket.
- Anonymous identity is tracked via an `IsEssential=true` GUID cookie. The cookie is validated as a GUID — non-GUID values are discarded and a new cookie is minted, preventing cookie injection via malformed values.

### Price Integrity

- **Critical**: `OnPost` reads `item.Price` from `CatalogItems` after `GetByIdAsync`. The `price` field submitted in the POST body via `_product.cshtml`'s hidden input is **completely ignored**. The Java target must replicate this server-side price resolution and must never accept price from the Angular client.

### Anonymous-to-Authenticated Basket Merge

- `BasketService.TransferBasketAsync(anonymousId, userName)` **is implemented** and merges basket items when a user logs in. This is called by the Identity login flow (not by this page). All items from the anonymous basket are added to the user's basket, and the anonymous basket row is deleted. The Java target must implement equivalent transfer during the authentication handshake.

### CSRF

- The basket form uses `method="post"` and is protected by Razor Pages' built-in anti-forgery token mechanism (automatically injected via tag helpers). The Java/Spring Boot target must implement equivalent CSRF protection on all basket mutation endpoints.

### ModelState Failure on Update

- If `ModelState.IsValid == false` in `OnPostUpdate`, the handler returns without calling `GetOrSetBasketCookieAndUserName()`, meaning no cookie is written. The page re-renders with a blank `BasketModel` (the `BasketModel` property is initialized to `new BasketViewModel()` and is never populated in this path). This results in the empty-state view appearing to the user, which is misleading.

---

## Accessibility Considerations

- Quantity inputs have `type="number"` with `min="0"` — provides basic browser validation and numeric keyboard support.
- The basket items table uses `<section>` elements rather than `<table>/<tr>/<td>` — column associations may not be announced correctly by screen readers. The Angular target should use a proper HTML `<table>` with `<th scope="col">` for basket columns.
- No ARIA labels on the quantity inputs — screen readers cannot announce which item a quantity input belongs to. Angular target should associate each input with a descriptive label.
- "[ Continue Shopping ]" and "[ Checkout ]" links use bracket-wrapped text (`[ ... ]`) — this may be announced awkwardly by screen readers. Angular target should use clean button/link text.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
|---|---|---|
| `CatalogItems` table | `Price` (for `OnPost`), `Name` + `PictureUri` (for basket display via `GetBasketItems`) | `OnPost`: redirect to `/Index` if item not found. `OnGet`: basket items rendered without names/images if lookup fails |
| `Baskets` + `BasketItems` tables | Basket contents (owned by buyer) | Empty basket shown; new basket created lazily |
| Cookie `BASKET_COOKIENAME` | Anonymous buyer GUID | New GUID minted if cookie absent or invalid |
| `HttpContext.User` (ASP.NET Identity) | Authenticated buyer username | Falls back to anonymous cookie identity |

### Downstream

| System | What this page affects | How |
|---|---|---|
| `/Basket/Checkout` (`basket-checkout` feature) | User proceeds to checkout | `[ Checkout ]` link (GET) — only shown when items present |
| `/` (`homepage-catalog-list` feature) | User returns to catalog | `[ Continue Shopping ]` link (GET) |
| `BasketService.TransferBasketAsync` | Called by Identity login middleware, not this page | Merges anonymous basket into authenticated user basket on sign-in |

---

## Analysis Notes

- **`BasketModel` is NOT a `[BindProperty]`**: Items are bound via the `OnPostUpdate(IEnumerable<BasketItemViewModel> items)` parameter, not a `[BindProperty]` field. The form's `Items[i].Id` and `Items[i].Quantity` indexed names bind to the `items` parameter case-insensitively. The Java target should bind these as a request body list or form parameter array — not as a top-level body object.
- **`OnPostUpdate` does NOT redirect (PRG missing)**: After updating quantities, the handler re-renders the page without redirecting. A browser back-button press after clicking `[ Update ]` will replay the POST, potentially applying the same quantity changes again. The Java/Angular target should implement PRG (Post-Redirect-Get) on quantity update.
- **`ModelState.IsValid == false` renders misleading empty state**: When model binding fails in `OnPostUpdate`, `BasketModel` is never populated, so the page shows "Basket is empty." even though the basket has items. The Angular target should validate client-side before submission and return meaningful error messages if server-side validation fails.
- **Cookie expiry uses `DateTime.Today.AddYears(10)`** (not `DateTime.UtcNow.AddYears(10)`) — this is a midnight-based local time expiry, not UTC. The Java target should use UTC-based expiry or a sliding window consistent with the browser expectations.
- **Anonymous basket merge IS implemented**: `BasketService.TransferBasketAsync` merges items from anonymous basket to authenticated basket. This is called by Identity events during login — the Java target must implement equivalent transfer on first authenticated request, or risk shoppers losing items they added as guests.
- **`SetQuantities` uses integer `basketId` (not `buyerId`)**: The `OnPostUpdate` flow first calls `GetOrCreateBasketForUser` to get the `BasketViewModel.Id` (integer PK), then passes that to `SetQuantities`. This is important — `SetQuantities` does NOT look up by buyer cookie. The Java target must fetch the basket ID before updating.
- **`Ardalis.Result<Basket>` implicit conversion**: `SetQuantities` returns `Result<Basket>`. The implicit operator on `Ardalis.Result` converts it to `Basket` (the value) — if `Result.NotFound()` is returned, the implicit conversion returns `null`, which would cause a null reference exception in `Map(basket)`. This is a latent bug in the legacy code.
- **`UnitPrice` stored at add-time**: `BasketItem.UnitPrice` is set when the item is added (`AddItemToBasket` passes `item.Price` from the catalog). If the catalog price changes later, existing basket items retain their original price. This is intentional pricing behavior the Java target must replicate.
- **Screenshot note**: Two screenshots captured — `basket-list-empty.png` (empty state: "Basket is empty." + Continue Shopping) and `basket-with-items.png` (loaded state: .NET Bot Black Sweatshirt qty 2 @ $19.50 = $39.00, .NET Black & White Mug qty 1 @ $8.50 = $8.50, Total $47.50 with Update and Checkout buttons).
