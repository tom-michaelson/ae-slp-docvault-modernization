# Describe UI Feature

Produce a detailed technical narrative (`functional-description.md`) for an eShopOnWeb UI feature. This document describes **how the legacy feature works** — field names from source code, handler logic, service calls, visual states, and workflows — in enough detail for a Business Analyst to extract formal business requirements without reading the original C# source.

This is a **discover-phase** command. It reads the artifacts already written by `analyze-ui-feature` plus the actual source files, and enriches them into a structured developer-facing description.

**Pipeline position:**
```
analyze-ui-feature  →  functional-spec.md, call-tree.json, metadata.json
take-screenshot     →  screenshots/
describe-ui-feature →  functional-description.md          ← this command
create-functional-spec-ui  →  functional-spec.md (enriched)
```

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<feature-key>  feature_dir=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | The feature key (e.g., `basket-view-page`) |
| `feature_dir` | Absolute path to the feature folder (e.g., `.../docs/entry-points/ui-features/basket-view-page`) |

Source files are resolved from `./source/{location}` relative to cwd (`target_repo/`), using the `location` field in `{feature_dir}/metadata.json`.

**Examples:**

```
key=basket-view-page
feature_dir=/abs/path/docs/entry-points/ui-features/basket-view-page
```

```
key=homepage-catalog-list
feature_dir=/abs/path/docs/entry-points/ui-features/homepage-catalog-list
```

---

## Idempotency

- If `{feature_dir}/functional-description.md` already exists → **stop immediately**. The analysis is complete.
- If `{feature_dir}/functional-description.in-progress.md` exists → a previous run crashed. **Overwrite it** and re-run the full analysis.
- Otherwise → proceed with full analysis.

---

## Inputs Read by This Command

From `{feature_dir}/`:

| File | What to extract |
|---|---|
| `metadata.json` | `key`, `name`, `elementType`, `uri`, `location`, `codeBehind`, `domain`, `notes` |
| `functional-spec.md` | Purpose, Gherkin scenarios, business rules, inputs/outputs tables already written |
| `call-tree.json` | Handler entry points, service calls, DB operations |
| `database-dependencies.json` | Tables, columns, operations |
| `screenshots/*.png` | Visual reference of the legacy UI (if present) |

From `./source/` (cwd-relative):

| Resolved from | What to read |
|---|---|
| `./source/{location}` | The Razor Page `.cshtml` / Blazor `.razor` / MVC view template |
| `./source/{codeBehind}` | The PageModel `.cshtml.cs` or code-behind `.razor.cs` (if present) |
| Partials referenced in view | `./source/src/Web/Pages/Shared/*.cshtml` |
| Services in `call-tree.json` | `./source/{file}` for each service implementation node |

---

## Output

```
{feature_dir}/functional-description.md
```

Written incrementally via:
1. Create `{feature_dir}/functional-description.in-progress.md` at Phase 1
2. Write each section as it is completed
3. Rename to `functional-description.md` at Phase 5 (final step)

---

## Output Template

```markdown
# Functional Description: {name}

> **Entry Point**: {key}
> **Location**: {location}
> **Type**: UI / {Page | Panel | Form}
> **Domain**: {domain}
> **Legacy URL**: {uri}

## Executive Summary

[2–3 paragraphs covering:
1. What task this page enables for the user
2. The main handlers/operations and how they interact
3. Any non-obvious aspects (anonymous vs auth, cookie tracking, lazy creation, etc.)]

## User Inputs

### Form Fields

[Table of all input fields the user can interact with. Use C# property names from
[BindProperty], <input asp-for="...">, or Blazor @bind — these are the authoritative
field names for the downstream create-functional-spec-ui command.]

| Field Name | C# Type | Source | Required | Notes |
| --- | --- | --- | --- | --- |
| `ProductDetails.Id` | int | `[BindProperty]` + `OnPost` param | yes | CatalogItem to add |
| `Items[].Quantity` | int | `[BindProperty]` form array | yes | Min 0 |

### User Interactions

[Buttons, links, and form submits. Reference the handler or route they invoke.]

| Interaction | Element | Handler / Target | Trigger |
| --- | --- | --- | --- |
| Update quantities | `<button type="submit">Update</button>` | `OnPostUpdate` (handler=Update) | Form POST |
| Checkout | `<a asp-page="/Basket/Checkout">` | `/Basket/Checkout` | Navigation |
| Add to basket | `<button>` in `_product.cshtml` | `OnPost` via form to `/Basket` | Form POST |

### URL / Route Parameters

[Query string params and route segments that reach this page.]

| Parameter | Source | Optional | Default | Notes |
| --- | --- | --- | --- | --- |
| `pageId` | Query string | yes | 0 | 0-indexed page number |
| `BrandFilterApplied` | Query string | yes | null | Filter by brand |

### Browser / Session Inputs

[Cookie reads, HTTP context user, session, TempData consumed on load.]

| Source | Data | Purpose |
| --- | --- | --- |
| Cookie `eShop` | Buyer GUID | Anonymous basket identity |
| `HttpContext.User.Identity` | Username | Authenticated basket identity |

---

## Outputs

### Rendered Content

[What the page renders for the user. Include loops, conditionals, and partials.
Reference the source file and line numbers.]

| Content Area | Description | Condition | Source ref |
| --- | --- | --- | --- |
| Empty state message | "Basket is empty." + Continue Shopping link | `!Model.BasketModel.Items.Any()` | `Index.cshtml:83` |
| Items table | Rows for each `BasketItem` (picture, name, price, qty input, total) | Items present | `Index.cshtml:27–47` |
| Total row | Sum of `Quantity * UnitPrice` across all items | Items present | `Index.cshtml:55–58` |
| Update button | POST to handler=Update | Items present | `Index.cshtml:70–73` |
| Checkout link | Link to `/Basket/Checkout` | Items present | `Index.cshtml:74` |
| _product partial | Product tile (picture, name, price, ADD TO BASKET) | Per catalog item | `_product.cshtml` |

### Navigation / Routing

[Redirects and links with business conditions.]

| Trigger | Destination | Condition |
| --- | --- | --- |
| OnPost with null productId | `/Index` | `productDetails.Id == null` |
| OnPost success | `/Basket` (RedirectToPage) | Item added |
| Checkout link | `/Basket/Checkout` | User clicks link |

### State Changes

[Session, cookie writes, TempData, ViewData set by this page.]

| State | Change | Trigger | Notes |
| --- | --- | --- | --- |
| Cookie `eShop` | Written with 10-year expiry | OnGet, first anonymous visit | GUID minted if cookie absent or invalid |
| `Baskets` row | Inserted | OnGet or OnPost, no basket exists | Lazy creation via service |

---

## API Dependencies

[Service methods called by this feature. Use names from call-tree.json.
"When called" = which handler calls it.]

### Service Calls

| Service Method | When Called | Data In | Data Out |
| --- | --- | --- | --- |
| `IBasketViewModelService.GetOrCreateBasketForUser` | OnGet, OnPostUpdate | `username` | `BasketViewModel` |
| `IBasketService.AddItemToBasket` | OnPost | `username`, `catalogItemId`, `price` | (void, modifies Basket) |
| `IBasketService.SetQuantities` | OnPostUpdate | `basketId`, `{itemId → qty}` dict | (void, modifies BasketItems) |
| `IRepository<CatalogItem>.GetByIdAsync` | OnPost | `catalogItemId` | `CatalogItem` (for current price) |

### Call Sequences

**OnGet:**
1. Resolve buyer identity (cookie or auth username)
2. Call `GetOrCreateBasketForUser(username)` → returns `BasketViewModel`
3. Render page with `BasketViewModel`

**OnPost (add item):**
1. Receive `CatalogItemViewModel productDetails`
2. If `productDetails.Id == null` → redirect to `/Index`
3. `GetByIdAsync(productDetails.Id)` → load current price from Catalog
4. `AddItemToBasket(username, productId, price)` → add/increment item
5. Redirect back to `/Basket`

**OnPostUpdate:**
1. Receive `IEnumerable<BasketItemViewModel> items`
2. If `ModelState.IsValid == false` → return without changes
3. `GetOrCreateBasketForUser` → reload basket
4. Build `Dictionary<string, int>` → `SetQuantities(basketId, dict)`
5. Re-render page

---

## State Management

[For Razor Pages: BindProperty fields, ViewData, TempData, session/cookie state.]

### BindProperty Fields

| Property | Type | Used In | Notes |
| --- | --- | --- | --- |
| `BasketModel` | `BasketViewModel` | OnGet (renders), OnPostUpdate (receives) | Top-level basket view model |
| (items in `BasketModel`) | `IList<BasketItemViewModel>` | OnPostUpdate | Posted back by form |

### Cookie / Session State

| Name | Read in | Written in | Purpose |
| --- | --- | --- | --- |
| `eShop` (cookie) | OnGet, OnPost | OnGet (first visit) | Anonymous buyer ID — GUID |
| `HttpContext.User` | OnGet, OnPost | (ASP.NET Identity middleware) | Authenticated buyer identity |

---

## Component Details

### PageModel: `IndexModel`

**File**: `src/Web/Pages/Basket/Index.cshtml.cs`

**Injected services**: `IBasketViewModelService`, `IBasketService`, `IRepository<CatalogItem>`, `ILogger<IndexModel>`

**Handlers**:
- `OnGetAsync()` — loads and renders basket
- `OnPostAsync(CatalogItemViewModel)` — adds item
- `OnPostUpdateAsync(IEnumerable<BasketItemViewModel>)` — updates quantities

**Private helpers**:
- `GetOrSetBasketCookieAndUserName()` — resolves buyer identity; sets cookie for anonymous users

### View Template: `Index.cshtml`

**Key sections**:
- Hero banner image (static)
- Empty-state block (`@if (!Model.BasketModel.Items.Any())`)
- Items table (loop over `Model.BasketModel.Items`)
- Total calculation row
- Update form (POSTs to `handler=Update`)
- Checkout link

### Partials Included

| Partial | Location | What it renders |
| --- | --- | --- |
| `_product.cshtml` | `src/Web/Pages/Shared/_product.cshtml` | Product tile with ADD TO BASKET form |
| `_pagination.cshtml` | `src/Web/Pages/Shared/_pagination.cshtml` | Pagination bar (not used on basket page) |

---

## Workflows

### Workflow 1: View Basket (OnGet)

**Use case**: Shopper opens their basket to review items before checking out.

**Preconditions**: Any visitor (anonymous or authenticated) navigates to `/Basket`.

**Steps**:

1. **Resolve buyer identity**
   - Code: `GetOrSetBasketCookieAndUserName()`
   - If authenticated: use `User.Identity.Name`
   - If anonymous: read `eShop` cookie; if absent, mint a new GUID and write cookie (10-year expiry)

2. **Load or create basket**
   - Call `IBasketViewModelService.GetOrCreateBasketForUser(username)`
   - If no `Baskets` row exists for this `BuyerId`: insert one (lazy creation)
   - Joins `BasketItems` with `Catalog` to produce `BasketViewModel`

3. **Render page**
   - If `Items` is empty: show "Basket is empty." + Continue Shopping link
   - If `Items` present: render items table with qty inputs, total row, Update and Checkout actions

**Success outcome**: Page renders with current basket contents (or empty-state message).

---

### Workflow 2: Add Item (OnPost)

**Use case**: Shopper clicks [ADD TO BASKET] on a product tile.

**Preconditions**: POST arrives from `_product.cshtml` form with `CatalogItemViewModel`.

**Steps**:

1. **Validate item identity**
   - If `productDetails.Id == null`: redirect to `/Index` immediately

2. **Look up current price** (important: price from DB, not from POST body)
   - `IRepository<CatalogItem>.GetByIdAsync(productDetails.Id)`
   - If item not found: redirect to `/Index`

3. **Add item to basket**
   - Resolve buyer identity (same as Workflow 1 step 1)
   - `IBasketService.AddItemToBasket(username, catalogItemId, price, quantity=1)`
   - If no basket exists for buyer: creates one
   - If `catalogItemId` already in basket: increments `Quantity` on existing row
   - If new: inserts a `BasketItems` row

4. **Redirect**
   - `RedirectToPage()` → GET `/Basket` (shows updated basket)

**Success outcome**: Item added or incremented; user sees updated basket via redirect.

---

### Workflow 3: Update Quantities (OnPostUpdate)

**Use case**: Shopper edits quantities and clicks [UPDATE].

**Preconditions**: POST from the items table form with `handler=Update`.

**Steps**:

1. **Validate model state**
   - If `ModelState.IsValid == false`: return without modifying basket

2. **Reload basket**
   - `GetOrCreateBasketForUser(username)` (reloads current state)

3. **Apply quantity changes**
   - Build `Dictionary<string, int>` from posted `items` (id → quantity)
   - `IBasketService.SetQuantities(basketId, quantitiesDict)`
   - Sets each `BasketItem.Quantity` to the posted value
   - Items with `Quantity == 0` are deleted via `Basket.RemoveEmptyItems()`

4. **Re-render**
   - Re-map basket and render updated page (no redirect — stays on basket page)

**Success outcome**: Quantities updated; page re-renders with new totals.

---

## Visual States

### Loading States

| Context | Indicator | Notes |
| --- | --- | --- |
| Page load | None (server-rendered, synchronous) | Page arrives fully rendered; no spinner |

### Error States

| Error | Display | Recovery |
| --- | --- | --- |
| Invalid `catalogItemId` on POST | Silent redirect to `/Index` | User returns to catalog |
| `ModelState` invalid on PostUpdate | Page re-renders without changes | User corrects and retries |
| Guard constraint violation (qty < 0) | Unhandled exception → 500 | Avoid by validating `min="0"` on qty input |

### Empty States

| Context | Message | Actions available |
| --- | --- | --- |
| Basket has no items | "Basket is empty." | "Continue Shopping" link → `/` |

### Success States

| Action | Feedback | Next state |
| --- | --- | --- |
| Add item | Redirect to `/Basket` | Basket re-renders with item included |
| Update quantities | Page re-renders | New totals visible inline |

---

## Use Cases

### UC-1: Browse basket before checkout

**User story**: As a shopper, I want to see all items in my basket so I can review my order before paying.

**Workflow**: Workflow 1 (View Basket)

### UC-2: Add a product to the basket

**User story**: As a shopper, I want to add a product from the catalog to my basket so I can purchase it later.

**Workflow**: Workflow 2 (Add Item)

### UC-3: Adjust item quantities

**User story**: As a shopper, I want to change how many of each item I want so I can buy the right amount.

**Workflow**: Workflow 3 (Update Quantities)

### UC-4: Remove an item

**User story**: As a shopper, I want to remove an item by setting its quantity to 0 so my basket only contains what I want.

**Workflow**: Workflow 3 — quantity set to 0 triggers deletion via `RemoveEmptyItems()`

---

## Security Considerations

### Authentication

- **Required**: No — anonymous users can view and add items to their basket.
- **Anonymous identity**: Tracked via `eShop` GUID cookie. Cookie is set `HttpOnly=false` (essential cookie, no consent required per legacy code).
- **Authenticated identity**: On login, the anonymous basket should be merged with the user's basket (if this is implemented — check `BasketService` for merge logic).

### Price Integrity

- **Critical**: Price is read from `Catalog` on the server during `OnPost`. The POSTed `CatalogItemViewModel` carries the catalogItemId only — price is NOT trusted from the client. This must be preserved in the Java target.

### CSRF

- Razor Pages includes an anti-forgery token in all forms by default (`<form method="post">` + `@Html.AntiForgeryToken()` via tag helpers). The Java target must implement equivalent CSRF protection.

---

## Accessibility Considerations

- Qty inputs have `type="number"` with `min="0"` — provides basic keyboard and validation support.
- No ARIA labels observed on the items table — screen reader may not announce column headers for data cells.
- "Continue Shopping" links provide navigation escape from empty/full basket states.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
| --- | --- | --- |
| `Catalog` table | Current item price (OnPost), item name + picture URI (OnGet via BasketViewModelService) | OnPost redirects to /Index; OnGet shows items without details |
| `Baskets` + `BasketItems` tables | Basket contents | Empty basket shown |
| Cookie `eShop` | Buyer identity for anonymous users | New anonymous basket created |

### Downstream

| System | What this page affects | How |
| --- | --- | --- |
| `/Basket/Checkout` | User proceeds to checkout | Link (GET) |
| `/` (catalog) | User returns to browsing | Link (GET) |

---

## Analysis Notes

- The `eShop` cookie is written with a 10-year expiry and is classified as "essential" (no cookie consent banner). The Java target should replicate the lifetime and classification.
- `OnPostUpdate` does NOT redirect — it re-renders the page directly. This means a browser back-button press after updating will replay the POST. Consider implementing PRG (Post-Redirect-Get) in the Java target.
- Anonymous-to-authenticated basket merge: the legacy code does not explicitly merge baskets on login. If the Angular app sends the anonymous `buyerId` cookie to the Spring Boot API, the server must decide whether to merge on first authenticated request. Flag for business clarification.
- `Task.Delay` is NOT present in this endpoint (it appears only in `CatalogItemListPagedEndpoint`).
```

---

## Discovery Process

### Phase 0: Idempotency Check and Work Unit Type Detection

1. Check: does `{feature_dir}/functional-description.md` exist?
   - Yes → **stop**. Print "functional-description.md already exists for {key} — skipping."
   - No → continue.
2. Read `{feature_dir}/metadata.json`. Extract `elementType`:
   - `"ui-page"` → **Page** analysis focus (overall structure, all handlers, navigation)
   - `"ui-panel"` → **Panel** analysis focus (data display, selection, parent relationship)
   - `"ui-action"` → **Form/Modal** analysis focus (form fields, validation, submission)
3. Note the source file paths: `./source/{location}` and `./source/{codeBehind}` (if present).

---

### Phase 1: Read Artifacts and Create In-Progress File

1. Read `{feature_dir}/metadata.json` — extract all fields.
2. Read `{feature_dir}/functional-spec.md` — note Gherkin scenarios, business rules, inputs/outputs already written. This becomes your baseline; the description must not contradict it.
3. Read `{feature_dir}/call-tree.json` — note all handler entry points, service methods called, DB ops.
4. Read `{feature_dir}/database-dependencies.json` — note all tables and operations.
5. Check `{feature_dir}/screenshots/` — list any `.png` files present.
6. **Write `{feature_dir}/functional-description.in-progress.md`** with the template header:
   ```
   # Functional Description: {name}
   > **Entry Point**: {key}
   > **Location**: {location}
   > **Type**: UI / {Page | Panel | Form}
   > **Domain**: {domain}
   > **Legacy URL**: {uri}
   ```

---

### Phase 2: Read Source Files

1. Read `./source/{location}` — the view template.
   - Razor Page: extract `@page` route, `@model` type, all `asp-for`, `asp-page-handler`, `asp-page`, `<partial>` tags, `@if` / `@foreach` blocks
   - Blazor: extract `@page`, `@inject`, `<EditForm>`, `@bind`, `@onclick`, `@if`, child components
   - MVC: extract `asp-controller`, `asp-action`, `asp-route-*`, all form inputs
2. Read `./source/{codeBehind}` (if present) — the PageModel or code-behind.
   - Extract: `[BindProperty]` fields and their C# types
   - Extract: all `OnGet*`, `OnPost*` method signatures
   - Extract: `[Authorize]` attribute if present
   - Extract: constructor-injected services
   - Extract: any cookie read/write logic (`Request.Cookies`, `Response.Cookies`)
3. For each `<partial name="..." />` or `@ref` modal component referenced in the view, read it from `./source/src/Web/Pages/Shared/` or the adjacent folder. Limit to 2 levels deep.
4. For each service method in `call-tree.json` that has a `file` property, read that file from `./source/{file}` to understand the logic.

---

### Phase 3: Screenshot Analysis (if screenshots present)

For each `.png` in `{feature_dir}/screenshots/`:

1. View the screenshot image.
2. Document:
   - **Screen state shown** (empty, loaded, form open, error, etc.)
   - **Content areas visible** (panels, forms, tables, empty states)
   - **Field labels** as displayed (note: these may differ from C# property names — use C# names in Form Fields table, note display label discrepancies here)
   - **Buttons and actions visible**
   - **Required field indicators** (highlighted inputs)
3. Cross-reference with source analysis:
   - Does the screenshot show content that the source analysis found? ✓
   - Does the source analysis describe content not visible in the screenshot? (different state)
   - Are there display labels that look different from C# property names? Flag in Analysis Notes.

---

### Phase 4: Write All Sections

Write each section to `functional-description.in-progress.md` as it is completed — do not wait until all sections are drafted before writing.

**For Page work units** (elementType = `ui-page`):
- Emphasize: all handlers, full workflows for each handler, rendered content table, navigation/routing
- Include: URL/route parameters, cookie/session inputs
- State Management: BindProperty fields, cookie state
- Component Details: PageModel class, partials, services injected
- Visual States: empty state, error paths, redirect outcomes

**For Panel work units** (elementType = `ui-panel`):
- Emphasize: data display (columns/fields with C# names), selection behavior, relationship to parent page
- De-emphasize: form fields (unless panel has inline editing)

**For Form/Modal work units** (elementType = `ui-action`):
- Emphasize: Form Fields table (every field with C# name, type, required, validation), submission workflow, validation rules
- De-emphasize: page structure

**Section order** (follow the output template above):
1. Executive Summary
2. User Inputs (Form Fields → User Interactions → URL/Route Parameters → Browser/Session Inputs)
3. Outputs (Rendered Content → Navigation/Routing → State Changes)
4. API Dependencies (Service Calls → Call Sequences)
5. State Management (BindProperty Fields → Cookie/Session State)
6. Component Details (PageModel → View Template → Partials)
7. Workflows (one H3 per handler — write in full before moving to next)
8. Visual States (Loading → Error → Empty → Success)
9. Use Cases
10. Security Considerations
11. Accessibility Considerations
12. Integration Points
13. Analysis Notes

---

### Phase 5: Finalise

1. Review: all sections written, all Gherkin scenarios from `functional-spec.md` are reflected somewhere in the workflows or use cases.
2. Review: all `[BindProperty]` fields appear in Form Fields table with their C# property names.
3. Review: all service methods from `call-tree.json` appear in the API Dependencies section.
4. Rename: `functional-description.in-progress.md` → `functional-description.md`

---

## Implementation Workflow

### Step 1: Parse Parameters
Read `key` and `feature_dir` from `{{PROMPT}}`.

### Step 2: Idempotency Check
If `{feature_dir}/functional-description.md` exists → stop.

### Step 3: Read All Artifacts
Read `metadata.json`, `functional-spec.md`, `call-tree.json`, `database-dependencies.json` from `feature_dir`. List screenshots if any.

### Step 4: Detect Work Unit Type
Use `elementType` from `metadata.json`.

### Step 5: Write In-Progress File
Create `{feature_dir}/functional-description.in-progress.md` with the header block.

### Step 6: Read Source Files
Read view template + code-behind from `./source/{location}` + `./source/{codeBehind}`. Read referenced partials and service implementations.

### Step 7: Analyse Screenshots
If screenshots present, view and document each one.

### Step 8: Write All Sections
Write sections 1–13 of the output template incrementally.

### Step 9: Rename to Final
`mv {feature_dir}/functional-description.in-progress.md {feature_dir}/functional-description.md`

### Step 10: Report Summary
```
Key:           {key}
Work unit type: {Page | Panel | Form}
Handlers:      {list, e.g. OnGet, OnPost, OnPostUpdate}
Form fields:   {count of BindProperty / input fields documented}
Workflows:     {count}
Use cases:     {count}
Screenshots:   {count analysed, or "none"}
Output:        {feature_dir}/functional-description.md
```

---

## Worked Examples

### Example 1: Page with multiple handlers — `basket-view-page`

**Input:**
```
key=basket-view-page
feature_dir=/path/docs/entry-points/ui-features/basket-view-page
```

**Artifacts read:** `metadata.json` (elementType=ui-page), `functional-spec.md`, `call-tree.json` (3 handlers), `database-dependencies.json` (Baskets, BasketItems, Catalog), `screenshots/basket-empty.png`

**Source files read:** `./source/src/Web/Pages/Basket/Index.cshtml`, `./source/src/Web/Pages/Basket/Index.cshtml.cs`, `./source/src/Web/Services/BasketViewModelService.cs`, `./source/src/ApplicationCore/Services/BasketService.cs`

**Form fields documented:** `BasketModel` (BindProperty), `Items[].Id`, `Items[].Quantity` (from POST form array)

**Workflows:** 3 (View, Add Item, Update Quantities)

**Key Analysis Notes:**
- `OnPostUpdate` does not redirect — browser back-button replays POST
- Price read from Catalog server-side on OnPost — must not be client-supplied
- Anonymous basket identity via `eShop` GUID cookie with 10-year expiry

---

### Example 2: Read-only page with filter — `homepage-catalog-list`

**Input:**
```
key=homepage-catalog-list
feature_dir=/path/docs/entry-points/ui-features/homepage-catalog-list
```

**Artifacts read:** `metadata.json` (elementType=ui-page), `functional-spec.md`, `call-tree.json` (1 handler: OnGet), `database-dependencies.json` (Catalog, CatalogBrands, CatalogTypes), `screenshots/homepage.png`

**Source files read:** `./source/src/Web/Pages/Index.cshtml`, `./source/src/Web/Pages/Index.cshtml.cs`, `./source/src/Web/Pages/Shared/_product.cshtml`, `./source/src/Web/Pages/Shared/_pagination.cshtml`

**Form fields documented:** No `[BindProperty]` for data entry — `CatalogIndexViewModel` binds from query string (`BrandFilterApplied`, `TypesFilterApplied`, `pageId`)

**URL/Route Parameters:** `BrandFilterApplied` (int?), `TypesFilterApplied` (int?), `pageId` (int?, default 0)

**Workflows:** 1 (Load and filter catalog)

**Key Analysis Notes:**
- Filter is applied via a GET form — no POST. Angular target should use query params.
- `_product.cshtml` partial submits to `/Basket` — this is out of scope for this feature but appears in the rendered content.
- `IUriComposer.ComposePicUri` rewrites relative PictureUri to absolute URLs — Java target must do the same.

---

## Important Notes

1. **Write incrementally.** Write each section to `functional-description.in-progress.md` as you complete it. Do not draft the entire document in memory and write once at the end — long analyses can be interrupted.

2. **Field names from C# source, not display labels.** The `create-functional-spec-ui` command uses field names from this document as authoritative. Always use C# property names (`BasketModel.Items`, `Input.Email`) not display labels ("Basket Items", "Email Address") in the Form Fields table.

3. **Do not contradict `functional-spec.md`.** The Gherkin and business rules already written there are correct. Do not change their meaning — deepen them.

4. **Partials are in scope for rendered content.** A `<partial name="_product" />` renders product tiles that contain an ADD TO BASKET form. Include the partial's content in the Rendered Content table but note it is "via `_product.cshtml` partial" and mark downstream effects (the basket POST) as a separate feature's concern.

5. **Cookie identity is security-relevant.** Always document cookie reads/writes explicitly in Browser/Session Inputs, State Changes, and Security Considerations. The Java target needs this detail to implement equivalent session tracking.

6. **One workflow per handler.** Every `OnGet*` and `OnPost*` method in the PageModel gets its own named Workflow section. Include the full step-by-step logic including branches and redirects.

7. **Analysis Notes is the place for technical debt and migration flags.** Anything that would surprise a Java developer implementing the equivalent endpoint belongs here: deliberate delays, PRG missing, price lookup pattern, anonymous-to-auth merge logic.

8. **Source path resolution.** Source files are at `./source/{location}` relative to cwd. If a service file listed in `call-tree.json` has path `src/ApplicationCore/Services/BasketService.cs`, read it from `./source/src/ApplicationCore/Services/BasketService.cs`.
