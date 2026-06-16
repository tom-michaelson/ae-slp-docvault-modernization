# Functional Description: Catalog Homepage

> **Entry Point**: `home`
> **Location**: `src/Web/Pages/Index.cshtml`
> **Type**: UI / Page
> **Domain**: catalog
> **Legacy URL**: `/`

## Executive Summary

The Catalog Homepage is the primary browsing surface of eShopOnWeb. Any visitor — authenticated or anonymous — lands here to explore the product catalog. The page renders a filterable, paginated grid of product tiles, each showing a product image, name, price, and an Add-to-Basket button.

The page has a single HTTP handler (`OnGet`). It accepts optional brand-filter, type-filter, and page-index values as query parameters, delegates all data retrieval to `ICatalogViewModelService.GetCatalogItems`, and returns a fully server-rendered page. There is no POST endpoint on this page: the Add-to-Basket button in each product tile submits directly to `/Basket/Index` (a separate feature), not back here.

Filter state and pagination are maintained entirely through GET query parameters (`BrandFilterApplied`, `TypesFilterApplied`, `pageId`), with no session, cookie, or server-side state involved. This means every page load is stateless and bookmarkable.

---

## User Inputs

### Form Fields

The filter form uses `<select asp-for="...">` bound to query-string model properties. There are no `[BindProperty]` fields — the model is bound from the `OnGet` parameter.

| Field Name | C# Type | Source | Required | Notes |
|---|---|---|---|---|
| `CatalogModel.BrandFilterApplied` | `int` | GET query param, `<select asp-for>` | no | Integer ID of selected brand; 0 = "All" (no filter) |
| `CatalogModel.TypesFilterApplied` | `int` | GET query param, `<select asp-for>` | no | Integer ID of selected type; 0 = "All" (no filter) |

### User Interactions

| Interaction | Element | Handler / Target | Trigger |
|---|---|---|---|
| Apply Filters | `<input type="image" src="arrow-right.svg">` | `OnGet /` (GET form re-submit) | Form GET submit |
| Previous Page | `<a asp-all-route-data="prevRouteData">` in `_pagination.cshtml` | `GET /?pageId={ActualPage-1}&...` | Navigation link |
| Next Page | `<a asp-all-route-data="nextRouteData">` in `_pagination.cshtml` | `GET /?pageId={ActualPage+1}&...` | Navigation link |
| Add to Basket | `<input type="submit" value="[ ADD TO BASKET ]">` in `_product.cshtml` | `POST /Basket/Index` (separate feature) | Form POST |

### URL / Route Parameters

| Parameter | C# binding | Optional | Default | Notes |
|---|---|---|---|---|
| `BrandFilterApplied` | `CatalogIndexViewModel.BrandFilterApplied` (OnGet param) | yes | `0` (no filter) | Integer foreign key into `CatalogBrands.Id` |
| `TypesFilterApplied` | `CatalogIndexViewModel.TypesFilterApplied` (OnGet param) | yes | `0` (no filter) | Integer foreign key into `CatalogTypes.Id` |
| `pageId` | `int? pageId` (OnGet param) | yes | `0` | 0-indexed page number; page 1 = `pageId=0` |

### Browser / Session Inputs

None. This page performs no cookie reads, session reads, or authentication checks. Any visitor may access it without a session.

---

## Outputs

### Rendered Content

| Content Area | Description | Condition | Source ref |
|---|---|---|---|
| Hero banner | Static promotional image | Always | `Index.cshtml:6-10` |
| Brand filter dropdown | `<select>` populated from `CatalogModel.Brands`; selected value = `BrandFilterApplied` | Always | `Index.cshtml:15` |
| Type filter dropdown | `<select>` populated from `CatalogModel.Types`; selected value = `TypesFilterApplied` | Always | `Index.cshtml:18` |
| Pagination bar (top) | `_pagination.cshtml` partial — "Showing N of M products - Page X - Y", Previous/Next links | `CatalogItems` non-empty | `Index.cshtml:27` |
| Product tile grid | `@foreach` over `CatalogModel.CatalogItems` — one `_product.cshtml` partial per item | `CatalogItems` non-empty | `Index.cshtml:30-36` |
| Pagination bar (bottom) | Same `_pagination.cshtml` partial rendered again | `CatalogItems` non-empty | `Index.cshtml:37` |
| Empty-state message | "THERE ARE NO RESULTS THAT MATCH YOUR SEARCH" | `!CatalogModel.CatalogItems.Any()` | `Index.cshtml:42` |
| Product tile (via partial) | Product image, product name, price ($ N2 format), `[ ADD TO BASKET ]` button | Per item in grid | `_product.cshtml:1-16` |
| Pagination summary text | "Showing {ItemsPerPage} of {TotalItems} products - Page {ActualPage+1} - {TotalPages}" | Inside `_pagination.cshtml` | `_pagination.cshtml:27` |
| Previous page link | Anchor; disabled via CSS class `is-disabled` when on first page | Inside `_pagination.cshtml` | `_pagination.cshtml:17` |
| Next page link | Anchor; disabled via CSS class `is-disabled` when on last page | Inside `_pagination.cshtml` | `_pagination.cshtml:32` |

### Navigation / Routing

| Trigger | Destination | Condition |
|---|---|---|
| Filter form submit | `GET /?BrandFilterApplied={id}&TypesFilterApplied={id}` | User clicks Apply Filters button |
| Previous page link | `GET /?pageId={ActualPage-1}&BrandFilterApplied=...&TypesFilterApplied=...` | Link active (not `is-disabled`) |
| Next page link | `GET /?pageId={ActualPage+1}&BrandFilterApplied=...&TypesFilterApplied=...` | Link active (not `is-disabled`) |
| Add to Basket (out of scope) | `POST /Basket/Index` | User clicks product tile button |

### State Changes

None. `OnGet` is purely read-only. No cookies, session values, database rows, or any other state is modified by this page.

---

## API Dependencies

### Service Calls

| Service Method | When Called | Data In | Data Out |
|---|---|---|---|
| `ICatalogViewModelService.GetCatalogItems` | `OnGet` | `pageIndex` (int), `itemsPage` (int, from `Constants.ITEMS_PER_PAGE`), `brandId` (int?), `typeId` (int?) | `CatalogIndexViewModel` |
| `IRepository<CatalogItem>.ListAsync(CatalogFilterPaginatedSpecification)` | Inside `GetCatalogItems` | `skip`, `take`, `brandId?`, `typeId?` | `List<CatalogItem>` — page of items |
| `IRepository<CatalogItem>.CountAsync(CatalogFilterSpecification)` | Inside `GetCatalogItems` | `brandId?`, `typeId?` | `int` — total matching items |
| `IRepository<CatalogBrand>.ListAsync()` | Inside `GetCatalogItems` → `GetBrands()` | — | `List<CatalogBrand>` — all brands |
| `IRepository<CatalogType>.ListAsync()` | Inside `GetCatalogItems` → `GetTypes()` | — | `List<CatalogType>` — all types |
| `IUriComposer.ComposePicUri` | Inside `GetCatalogItems` (per item) | `item.PictureUri` (relative path) | Absolute image URL string |

### Call Sequences

**OnGet:**
1. Bind `catalogModel.BrandFilterApplied`, `catalogModel.TypesFilterApplied`, and `pageId` from query string.
2. Call `ICatalogViewModelService.GetCatalogItems(pageId ?? 0, Constants.ITEMS_PER_PAGE, brandId, typeId)`.
   - a. Build `CatalogFilterPaginatedSpecification(skip = itemsPage * pageIndex, take = itemsPage, brandId, typeId)` → `IRepository<CatalogItem>.ListAsync(...)` → `SELECT` from `Catalog` with WHERE + SKIP + TAKE.
   - b. Build `CatalogFilterSpecification(brandId, typeId)` → `IRepository<CatalogItem>.CountAsync(...)` → `SELECT COUNT(*)` from `Catalog` with same WHERE (no pagination). Used to compute `TotalPages`.
   - c. Call `GetBrands()` → `IRepository<CatalogBrand>.ListAsync()` → `SELECT *` from `CatalogBrands`; sort alphabetically; prepend "All" sentinel (Value = null).
   - d. Call `GetTypes()` → `IRepository<CatalogType>.ListAsync()` → `SELECT *` from `CatalogTypes`; sort alphabetically; prepend "All" sentinel (Value = null).
   - e. Compose `PaginationInfoViewModel`: `ActualPage`, `ItemsPerPage` = `itemsOnPage.Count`, `TotalItems`, `TotalPages = ⌈TotalItems / itemsPage⌉`.
   - f. Compute `PaginationInfo.Previous = "is-disabled"` when `ActualPage == 0`; `PaginationInfo.Next = "is-disabled"` when `ActualPage == TotalPages - 1`.
   - g. Call `IUriComposer.ComposePicUri(item.PictureUri)` for each item to produce an absolute URL.
3. Assign result to `CatalogModel`.
4. Render page.

---

## State Management

### BindProperty Fields

This page has no `[BindProperty]` fields. The view model is populated entirely in `OnGet` via parameter binding from the query string.

| Property | Type | Binding Source | Notes |
|---|---|---|---|
| `CatalogModel` | `CatalogIndexViewModel` | Set by `OnGet` handler | Contains items, brands, types, pagination info |
| `CatalogModel.BrandFilterApplied` | `int` | Query string via `CatalogIndexViewModel` param | 0 = no brand filter |
| `CatalogModel.TypesFilterApplied` | `int` | Query string via `CatalogIndexViewModel` param | 0 = no type filter |

### Cookie / Session State

None. This page reads and writes no cookies or session values.

---

## Component Details

### PageModel: `IndexModel`

**File**: `src/Web/Pages/Index.cshtml.cs`

**Auth**: None (`[Authorize]` not present — public page).

**Injected services**: `ICatalogViewModelService` (injected via constructor).

**Handlers**:

| Method | Signature | Description |
|---|---|---|
| `OnGet` | `async Task OnGet(CatalogIndexViewModel catalogModel, int? pageId)` | Loads filtered+paginated catalog and populates `CatalogModel` |

**No private helpers** — identity/cookie logic is absent from this page entirely.

### View Template: `Index.cshtml`

**Route**: `@page` (no explicit route template — resolves to `/` via Pages convention).

**Key sections**:

| Lines | Content |
|---|---|
| 6–10 | Hero banner (static image — no interaction) |
| 11–23 | `<form method="get">` — brand and type filter selects + image-type submit |
| 14 | `@if (Model.CatalogModel.CatalogItems.Any())` — guard for grid and pagination |
| 27 | `<partial name="_pagination" for="CatalogModel.PaginationInfo">` — top pagination bar |
| 29–36 | `<div>` + `@foreach` — product tile grid, one `_product.cshtml` partial per item |
| 37 | `<partial name="_pagination" for="CatalogModel.PaginationInfo">` — bottom pagination bar |
| 39–44 | `else` block — empty-state message |

### Partials Included

| Partial | Location | What it renders | Out of scope? |
|---|---|---|---|
| `_product.cshtml` | `src/Web/Pages/Shared/_product.cshtml` | Product image, name, price, `[ ADD TO BASKET ]` form | ADD TO BASKET POST is out of scope (belongs to `basket-list`) |
| `_pagination.cshtml` | `src/Web/Pages/Shared/_pagination.cshtml` | Previous/Next links + page summary text | No |

---

## Workflows

### Workflow 1: Load and Filter Catalog (OnGet)

**Use case**: Any visitor browses the product catalog, optionally filtered by brand and/or type, on any page.

**Preconditions**: Any HTTP GET to `/` with optional query parameters.

**Steps**:

1. **Bind filter parameters**
   - `catalogModel.BrandFilterApplied` bound from query param `BrandFilterApplied` (defaults to `0` if absent).
   - `catalogModel.TypesFilterApplied` bound from query param `TypesFilterApplied` (defaults to `0` if absent).
   - `pageId` bound from query param `pageId` (defaults to `null`, treated as `0`).

2. **Fetch paginated items**
   - Construct `CatalogFilterPaginatedSpecification(skip = ITEMS_PER_PAGE * pageIndex, take = ITEMS_PER_PAGE, brandId, typeId)`.
   - `brandId` and `typeId` are nullable — if `0`, they are passed as-is and the WHERE clause treats non-null as filter active; if truly `null` the WHERE omits the condition. In practice the form always sends `0` for "All" so the spec treats `0` as "no filter" via the nullable int binding.
   - Execute `IRepository<CatalogItem>.ListAsync(spec)` → returns at most `ITEMS_PER_PAGE` items for the requested page.

3. **Count total matching items**
   - Construct `CatalogFilterSpecification(brandId, typeId)` — same predicates, no SKIP/TAKE.
   - Execute `IRepository<CatalogItem>.CountAsync(spec)` → total items matching active filters.
   - Used to compute `TotalPages = ⌈TotalItems / ITEMS_PER_PAGE⌉`.

4. **Fetch brand and type dropdown data**
   - `GetBrands()`: `IRepository<CatalogBrand>.ListAsync()` → all brands, sorted by `Brand` text, prepend "All" (Value = null, Selected = true).
   - `GetTypes()`: `IRepository<CatalogType>.ListAsync()` → all types, sorted by `Type` text, prepend "All" (Value = null, Selected = true).

5. **Build `CatalogIndexViewModel`**
   - `CatalogItems` — project each `CatalogItem` to `CatalogItemViewModel { Id, Name, Price, PictureUri (composed via IUriComposer) }`.
   - `Brands` and `Types` — from steps 4.
   - `BrandFilterApplied` and `TypesFilterApplied` — echo back the applied filter IDs.
   - `PaginationInfo.Previous` = `"is-disabled"` if `ActualPage == 0`, else `""`.
   - `PaginationInfo.Next` = `"is-disabled"` if `ActualPage == TotalPages - 1`, else `""`.

6. **Render**
   - If `CatalogItems` non-empty: render top pagination → product tile grid → bottom pagination.
   - If `CatalogItems` empty: render the empty-state message ("THERE ARE NO RESULTS THAT MATCH YOUR SEARCH").
   - Filter form always rendered regardless of items.

**Success outcome**: Page displays filtered, paginated catalog items with brand/type dropdowns and pagination controls.

**Branch: Empty result**
- Triggered when no `Catalog` rows match the active brand/type filter.
- Rendered content: filter form visible with current selections, empty-state message shown, no product grid, no pagination.

**Branch: Last page**
- `PaginationInfo.Next` = `"is-disabled"` → `<a>` anchor rendered with `is-disabled` CSS class; link is visually inactive but still technically navigable to `?pageId={TotalPages}` (no server-side guard against over-pagination).

---

## Visual States

### Loading States

| Context | Indicator | Notes |
|---|---|---|
| Page load | None (synchronous server-render) | Page arrives fully rendered; no JavaScript spinner or lazy-load state |

### Error States

| Error | Display | Recovery path |
|---|---|---|
| `pageId` beyond last page | Empty product grid; pagination shows correct totals | User clicks Previous or adjusts query string |
| Database unavailable | Unhandled exception → 500 error page | N/A (infrastructure concern) |

### Empty States

| Context | Displayed content | Actions available |
|---|---|---|
| No items match brand + type filter | "THERE ARE NO RESULTS THAT MATCH YOUR SEARCH" | Filter form still visible — user can change selection and resubmit |
| Catalog table empty (no products at all) | Same empty-state message, pagination not rendered | Filter form visible |

### Success States

| Action | Feedback | Next state |
|---|---|---|
| Filter applied | Same page re-renders with filtered items | Product grid and pagination update to reflect filter |
| Page changed | Same page re-renders at new `pageId` | Product grid updates; Previous/Next disable states update |

---

## Use Cases

### UC-1: Browse full catalog

**User story**: As a shopper, I want to see all available products so I can discover what's for sale.

**Workflow**: Workflow 1 — navigate to `/` with no query params; `BrandFilterApplied=0`, `TypesFilterApplied=0`, `pageId=0`.

### UC-2: Filter by brand

**User story**: As a shopper, I want to see only products from a specific brand so I can find items I like quickly.

**Workflow**: Workflow 1 — select brand in dropdown, click Apply Filters; GET re-issued with `BrandFilterApplied={id}`.

### UC-3: Filter by type

**User story**: As a shopper, I want to see only products of a specific type (e.g., T-Shirt) so I can narrow my search.

**Workflow**: Workflow 1 — select type in dropdown, click Apply Filters; GET re-issued with `TypesFilterApplied={id}`.

### UC-4: Navigate to next page of results

**User story**: As a shopper, I want to page through the catalog when there are more items than fit on one screen.

**Workflow**: Workflow 1 — click Next link; GET re-issued with `pageId={ActualPage+1}` and existing filter params preserved via `asp-all-route-data`.

### UC-5: Reach product with no filter match

**User story**: As a shopper, I want a clear message when my filter returns no results so I know to adjust my selection.

**Workflow**: Workflow 1 branch: empty result — "THERE ARE NO RESULTS THAT MATCH YOUR SEARCH" message shown.

---

## Security Considerations

### Authentication

- **Required**: No. The page is publicly accessible to all visitors.
- No `[Authorize]` attribute on `IndexModel`.
- No session or cookie data is read or written by this page.

### Input Validation

- `BrandFilterApplied` and `TypesFilterApplied` are bound as `int` (via `CatalogIndexViewModel` model binding). Non-integer query param values will fail model binding and default to `0`; no injection risk.
- `pageId` is bound as `int?`. Invalid values default to `null` → `0`; no injection risk.

### No CSRF concern

- The filter form uses `method="get"`. GET forms do not require anti-forgery tokens and carry no mutation risk.

---

## Accessibility Considerations

- Filter dropdowns have visible labels via `data-title="brand"` / `data-title="type"` CSS-driven labels — not `<label for>`. Screen readers may not announce these as associated labels. The Angular target should use proper `<label>` elements with `for` attributes.
- The Apply Filters button is an `<input type="image">` — screen readers may read it as an image without purpose. The Angular target should use `<button type="submit">` with visible text or an `aria-label`.
- Previous/Next pagination links use `aria-label="Previous"` / `aria-label="Next"` — adequate for screen readers.
- Product tile text (name, price) is in plain `<span>` / `<div>` — no semantic headings. The Angular ProductComponent should use appropriate heading levels.
- No keyboard trap or focus management issues observed.

---

## Integration Points

### Upstream

| Source | Data provided | Failure impact |
|---|---|---|
| `Catalog` table | Product list (Id, Name, Price, PictureUri, CatalogBrandId, CatalogTypeId) | Page renders empty-state or 500 |
| `CatalogBrands` table | Brand dropdown options | Filter bar shows no brand options; page still renders |
| `CatalogTypes` table | Type dropdown options | Filter bar shows no type options; page still renders |
| `IUriComposer` | Absolute image URL for each product | Product tiles render without images if URI composition fails |

### Downstream

| System | What this page affects | How |
|---|---|---|
| `/Basket/Index` | Item added to basket | Add-to-Basket form in `_product.cshtml` POSTs here (separate feature) |

---

## Analysis Notes

1. **Two Catalog queries per request.** The service issues a paginated `ListAsync` and a separate `CountAsync` on every page load. There is no single `Page<T>` query. The Spring Boot target should use `PagingAndSortingRepository` or `JpaRepository` with `findAll(Specification, Pageable)` which returns a `Page<T>` containing both the items and the total count in a single query execution.

2. **Brand and Type lists loaded on every request.** `CatalogBrands` and `CatalogTypes` are fetched fresh on every `OnGet` call with no caching. These tables change only on admin updates. The Spring Boot target should consider `@Cacheable` on the brand/type lookup methods to avoid unnecessary round-trips.

3. **`IUriComposer.ComposePicUri` rewrites image paths.** The `PictureUri` column stores relative paths (e.g., `images\products\1.png?0`). `IUriComposer` converts these to absolute URLs at render time. The Spring Boot API must provide an equivalent: either return absolute URLs from the `@RestController`, or document a path-rewriting convention for the Angular frontend.

4. **`PaginationInfo.Previous/Next` are CSS class strings.** Values are `"is-disabled"` or `""` — set in the service layer, not computed in the view. The Angular target should derive disabled state from `currentPage === 0` / `currentPage === totalPages - 1` logic in the component, not from a string flag returned by the API.

5. **`pageId` is 0-indexed.** Page 1 = `pageId=0`. The pagination summary text compensates by displaying `ActualPage + 1`. The Spring Boot `Pageable` convention uses 0-indexed pages as well (`page=0` for first page), but this should be made explicit in the API contract to avoid off-by-one errors in the Angular component.

6. **`BrandFilterApplied=0` means "no filter".** The `CatalogFilterSpecification` checks `!brandId.HasValue || i.CatalogBrandId == brandId`. Because `int?` binding of `0` from a query param results in a non-null `0`, the WHERE clause becomes `i.CatalogBrandId == 0` — which matches nothing (there is no brand with Id=0). In effect `0` behaves as "no filter" because the "All" dropdown option has `Value = null` which binds as `0` via default `int` conversion. The Spring Boot target must replicate: treat `brandId=0` as "no filter" or use `null` for "All" explicitly in the API contract.

7. **`_product.cshtml` Add-to-Basket is out of scope.** The form in the product tile targets `/Basket/Index` and belongs to the `basket-list` feature. The Angular ProductComponent should emit an event or call a BasketService — it should not contain basket logic internally.

8. **Screenshot state: loaded (10 of 12 items, page 1).** The captured screenshot shows the default loaded state with no active filters. Brand/type dropdowns default to "All". No empty state was captured because the seeded catalog always has items on a fresh start. The empty state would require selecting a brand+type combination with no matching products.
