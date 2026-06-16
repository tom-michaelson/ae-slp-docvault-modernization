# Functional spec — Catalog Homepage

**Key:** `home`
**URL:** `GET /`
**Legacy source:** `src/Web/Pages/Index.cshtml` + `Index.cshtml.cs`

## Purpose

Presents the full product catalog to the shopper with brand and type filters, pagination, and a product tile grid. It is the primary entry point for browsing and the first step in the add-to-basket flow.

## Functional behavior

### OnGet — load and filter catalog

Signature: `public async Task OnGet(CatalogIndexViewModel catalogModel, int? pageId)`

1. Binds query parameters `BrandFilterApplied`, `TypesFilterApplied` (from `catalogModel`) and `pageId` from the request URL.
2. Calls `ICatalogViewModelService.GetCatalogItems(pageId ?? 0, Constants.ITEMS_PER_PAGE, brandId, typeId)`.
3. Inside `GetCatalogItems`:
   a. Executes `IRepository<CatalogItem>.ListAsync(CatalogFilterPaginatedSpecification)` → paginated SELECT on `Catalog`.
   b. Executes `IRepository<CatalogItem>.CountAsync(CatalogFilterSpecification)` → COUNT on `Catalog` for the same filter (used for total pages).
   c. Calls `GetBrands()` → `IRepository<CatalogBrand>.ListAsync()` → SELECT all from `CatalogBrands`; prepends "All" sentinel.
   d. Calls `GetTypes()` → `IRepository<CatalogType>.ListAsync()` → SELECT all from `CatalogTypes`; prepends "All" sentinel.
   e. Computes `PaginationInfo` (ActualPage, ItemsPerPage, TotalItems, TotalPages, Previous/Next CSS disable flags).
   f. Composes product image URLs via `IUriComposer.ComposePicUri(item.PictureUri)`.
4. Assigns resulting `CatalogIndexViewModel` to `CatalogModel` for rendering.
5. If `CatalogItems` is empty, the view renders "THERE ARE NO RESULTS THAT MATCH YOUR SEARCH"; the filter form remains visible.

## Acceptance criteria

```gherkin
Scenario: First visit with no filters renders all items on page 1
  Given the catalog contains 20 items
  And no brand or type filter is selected
  When the shopper navigates to "/"
  Then the page renders up to ITEMS_PER_PAGE product tiles
  And the brand dropdown shows "All" plus all CatalogBrands rows ordered alphabetically
  And the type dropdown shows "All" plus all CatalogTypes rows ordered alphabetically
  And the pagination widget shows "Showing N of 20 products - Page 1 - M"

Scenario: Brand filter applied narrows the catalog
  Given the catalog contains items for brand "Roslyn" and brand "NetCore"
  When the shopper selects brand "Roslyn" and submits the filter form
  Then the GET request includes query param BrandFilterApplied=<roslyn-id>
  And only items where CatalogBrandId = <roslyn-id> are rendered
  And the pagination count reflects only the filtered total

Scenario: Type filter applied narrows the catalog
  Given the catalog contains items of type "T-Shirt" and type "Mug"
  When the shopper selects type "Mug" and submits the filter form
  Then the GET request includes query param TypesFilterApplied=<mug-id>
  And only items where CatalogTypeId = <mug-id> are rendered

Scenario: Combined brand and type filter with no matching results
  Given no items exist for the selected brand/type combination
  When the shopper submits the filter form with both brand and type selected
  Then the product grid is replaced by the text "THERE ARE NO RESULTS THAT MATCH YOUR SEARCH"
  And the filter form remains visible with the current selections

Scenario: Navigating to page 2 preserves active filters
  Given the shopper has brand filter BrandFilterApplied=3 active
  When they click the "Next" pagination link
  Then the GET request includes both BrandFilterApplied=3 and pageId=1
  And the second page of filtered results is rendered
  And the "Previous" link is enabled and the "Next" link reflects remaining pages

Scenario: Last page disables the Next link
  Given the shopper is on the final page of results
  Then the "Next" anchor has the CSS class "is-disabled"
  And the "Previous" anchor does not have the "is-disabled" class

Scenario: First page disables the Previous link
  Given the shopper is on page 1 (pageId=0 or absent)
  Then the "Previous" anchor has the CSS class "is-disabled"
```

## UI elements

| Element | Kind | Source ref |
|---|---|---|
| Brand filter dropdown | `<select asp-for="CatalogModel.BrandFilterApplied">` bound to `CatalogModel.Brands` | `Index.cshtml:15` |
| Type filter dropdown | `<select asp-for="CatalogModel.TypesFilterApplied">` bound to `CatalogModel.Types` | `Index.cshtml:18` |
| Apply Filters button | `<input type="image">` submits GET filter form | `Index.cshtml:20` |
| Filter form | `<form method="get">` submitting to `/` | `Index.cshtml:13-21` |
| Pagination widget (top) | `<partial name="_pagination">` with `PaginationInfoViewModel` | `Index.cshtml:27` |
| Product tile grid | `@foreach` over `CatalogModel.CatalogItems` rendering `_product.cshtml` | `Index.cshtml:30-36` |
| Pagination widget (bottom) | `<partial name="_pagination">` with `PaginationInfoViewModel` | `Index.cshtml:37` |
| Empty-state message | conditional text block | `Index.cshtml:42` |
| Previous page link | `<a asp-all-route-data>` with `pageId = ActualPage - 1`; CSS class `is-disabled` when on page 1 | `_pagination.cshtml:17` |
| Page summary text | read-only `<span>`: "Showing N of M products - Page X - Y" | `_pagination.cshtml:27` |
| Next page link | `<a asp-all-route-data>` with `pageId = ActualPage + 1`; CSS class `is-disabled` on last page | `_pagination.cshtml:32` |
| Product tile partial | `<partial name="_product">` per item — image, name, price, Add to Basket form | `Index.cshtml:33` |

## Out of scope

- **Add to Basket** (`_product.cshtml:5`): the `[ ADD TO BASKET ]` submit button inside each product tile POSTs to `/Basket/Index` (not this page). That operation belongs to the `basket-list` feature key.
- **Site header / nav**: basket count badge, login link, and site navigation rail rendered by `_Layout.cshtml` are shared layout concerns outside this feature.
