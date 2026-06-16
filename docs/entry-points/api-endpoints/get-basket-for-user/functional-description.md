# Functional Description: Get basket for user

> **Entry Point**: get-basket-for-user
> **Location**: src/Web/Services/BasketViewModelService.cs
> **Type**: API / In-process Service
> **Domain**: basket
> **Legacy method**: Microsoft.eShopWeb.Web.Services.BasketViewModelService.GetOrCreateBasketForUser
> **Web handler**: Microsoft.eShopWeb.Web.Pages.Basket.IndexModel.OnGet

## Executive Summary

The `get-basket-for-user` endpoint returns the current basket for a buyer, enriched with product names and absolute picture URLs from the catalog. It is called by the Angular basket view on page load, by the checkout page when entering the checkout flow, and by the basket update flow to resolve the basket's integer ID before POSTing updates. Authentication is not required — both anonymous and authenticated buyers are served.

The service never returns 404. If no basket exists for the requested `buyerId`, it creates one (empty basket, no items) and returns it with a 200. This lazy-creation contract is critical: the Angular basket view must handle an empty `items` array as a valid first-time state rather than treating a missing basket as an error. The response includes two fields that are NOT stored in `BasketItems` — `productName` and `pictureUrl` are fetched from `CatalogItems` in a separate batch query and joined in-memory, making this a two-round-trip read operation per call.

Note: the actual entry point is `BasketViewModelService` (in `src/Web/Services/`), not `BasketService` (in `src/ApplicationCore/Services/`). The `legacyLocation` in `metadata.json` points to the web-layer view model service, not the application-core basket service. The REST target must replicate both the basket lookup AND the catalog enrichment — returning raw `BasketItem` rows without catalog data would be incomplete.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `/api/baskets/for-user/{buyerId}` |
| Auth required | no |

### Path Parameters

| Name | Type | Required | Notes |
| --- | --- | --- | --- |
| `buyerId` | string | yes | ASP.NET Identity username for authenticated users (e.g., `alice@example.com`); GUID string for anonymous users (e.g., `550e8400-e29b-41d4-a716-446655440000`) |

No query parameters. No request body.

### Success Response

HTTP 200 OK — always returned, even when the basket is empty or newly created:

```json
{
  "id": 42,
  "buyerId": "alice@example.com",
  "items": [
    {
      "id": 100,
      "catalogItemId": 3,
      "productName": ".NET Bot Black Sweatshirt",
      "pictureUrl": "https://host/images/products/3.png",
      "unitPrice": 19.50,
      "quantity": 2
    }
  ]
}
```

Empty / newly-created basket:
```json
{
  "id": 43,
  "buyerId": "550e8400-e29b-41d4-a716-446655440000",
  "items": []
}
```

### Response Field Notes

| Field | Source | Notes |
| --- | --- | --- |
| `id` | `Baskets.Id` | Integer PK of the basket row |
| `buyerId` | `Baskets.BuyerId` | Username or GUID string |
| `items[].id` | `BasketItems.Id` | Integer PK of the basket item row |
| `items[].catalogItemId` | `BasketItems.CatalogItemId` | FK to `CatalogItems` |
| `items[].productName` | `CatalogItems.Name` | Current catalog name (NOT from BasketItems) |
| `items[].pictureUrl` | `IUriComposer.ComposePicUri(CatalogItems.PictureUri)` | Absolute URL — NOT the stored relative path |
| `items[].unitPrice` | `BasketItems.UnitPrice` | Price at time of add — NOT the current catalog price |
| `items[].quantity` | `BasketItems.Quantity` | Current quantity in basket |

### Error Responses

This endpoint always returns HTTP 200. There are no documented error responses. An unhandled exception (e.g., `InvalidOperationException` if a basket item references a deleted catalog item) produces HTTP 500.

---

## Business Logic

### Overview

The service looks up the basket by `buyerId` string using `BasketWithItemsSpecification`, which eagerly loads `BasketItems`. If no basket exists, `CreateBasketForUser` inserts a new empty `Baskets` row and returns a `BasketViewModel` with no items.

If the basket is found, `GetBasketItems` batch-fetches all `CatalogItem` rows matching the basket's `CatalogItemIds` in a single `IN (...)` query. For each basket item, it performs an in-memory lookup of the corresponding catalog item (using `.First()`), then builds a `BasketItemViewModel` combining data from both `BasketItem` (ID, UnitPrice, Quantity, CatalogItemId) and `CatalogItem` (Name → ProductName, PictureUri → PictureUrl rewritten to absolute URL).

The critical separation: `UnitPrice` comes from `BasketItem` (the price at add-to-basket time), while `ProductName` and `PictureUrl` come from the current `CatalogItem`. If a catalog item's price changes after it was added to the basket, the basket item still shows the original price — but its name and picture would reflect the current catalog values.

### Validation Rules

| Condition | Rule | Failure behavior |
| --- | --- | --- |
| `buyerId` | No validation — any string is accepted | N/A; accepted and passed directly to the spec |
| Basket item references deleted catalog item | `catalogItems.First(c => c.Id == basketItem.CatalogItemId)` throws `InvalidOperationException` | HTTP 500 |

No other validation exists. The service does not check ownership — any caller can request any `buyerId`'s basket.

### Call Sequence

**Web handler (`IndexModel.OnGet`):**
1. `GetOrSetBasketCookieAndUserName()` — resolves buyerId:
   - If `User.Identity.IsAuthenticated` → return `User.Identity.Name` (e.g., `alice@example.com`)
   - If anonymous but `eShop` cookie present → read cookie value; validate it is a parseable GUID via `Guid.TryParse`; if not a valid GUID, nullify it
   - If no valid buyerId: mint `Guid.NewGuid().ToString()`, write to `eShop` cookie (`IsEssential = true`, 10-year expiry)
2. Call `GetOrCreateBasketForUser(userName)`
3. Assign result to `BasketModel` for Razor Page rendering

**Service method (`BasketViewModelService.GetOrCreateBasketForUser`):**
1. Receive `userName` (string) — the resolved buyerId
2. `new BasketWithItemsSpecification(userName)` — spec: `WHERE BuyerId == userName AND .Include(b => b.Items)`
3. `IRepository<Basket>.FirstOrDefaultAsync(basketSpec)` → SELECT `Baskets JOIN BasketItems WHERE BuyerId = userName`; returns null if no basket exists
4. **Path A — basket is null (lazy creation)**:
   - `new Basket(userId)` → new entity
   - `IRepository<Basket>.AddAsync(basket)` → INSERT `Baskets` row (no items)
   - Return `BasketViewModel { Id = basket.Id, BuyerId = basket.BuyerId, Items = (null/empty) }`
5. **Path B — basket found**:
   - Call `GetBasketItems(basket.Items)`:
     - Extract `catalogItemIds[]` from `basket.Items.Select(b => b.CatalogItemId)`
     - `new CatalogItemsSpecification(catalogItemIds[])` — spec: `WHERE Id IN (catalogItemIds)`
     - `IRepository<CatalogItem>.ListAsync(spec)` → batch SELECT `CatalogItems`
     - For each basket item: `catalogItems.First(c => c.Id == basketItem.CatalogItemId)` — in-memory lookup
     - Build `BasketItemViewModel { Id, UnitPrice, Quantity, CatalogItemId, PictureUrl = ComposePicUri(catalogItem.PictureUri), ProductName = catalogItem.Name }`
   - Call `Map(basket)`:
     - Return `BasketViewModel { Id = basket.Id, BuyerId = basket.BuyerId, Items = [BasketItemViewModels] }`
6. Return `BasketViewModel`

---

## Component Details

### Service Method

**Class**: `BasketViewModelService`
**File**: `src/Web/Services/BasketViewModelService.cs`
**Method signature**: `Task<BasketViewModel> GetOrCreateBasketForUser(string userName)`

**Injected services**: `IRepository<Basket>`, `IRepository<CatalogItem>`, `IUriComposer`, `IBasketQueryService` (not used by this method)

**Private helpers**:
- `CreateBasketForUser(string userId)` (line 41) — inserts a new empty basket, returns minimal `BasketViewModel`
- `GetBasketItems(IReadOnlyCollection<BasketItem> basketItems)` (line 53) — batch-fetches catalog data and maps to `BasketItemViewModel` list
- `Map(Basket basket)` (line 77) — calls `GetBasketItems` and wraps in `BasketViewModel`

**`BasketViewModel` fields**: `Id` (int), `BuyerId` (string), `Items` (List\<BasketItemViewModel\>)

**`BasketItemViewModel` fields**: `Id` (int), `UnitPrice` (decimal), `Quantity` (int), `CatalogItemId` (int), `PictureUrl` (string — absolute URL), `ProductName` (string)

Note: the response field is `PictureUrl` (not `PictureUri`) — the naming differs from other basket-adjacent endpoints that use `pictureUri`.

---

### Web Handler (`IndexModel.OnGet`)

**File**: `src/Web/Pages/Basket/Index.cshtml.cs`
**No `[Authorize]`** — anonymous access is allowed.

**What `OnGet` does BEFORE calling the service:**
1. Calls `GetOrSetBasketCookieAndUserName()` to resolve the buyer identity:
   - Authenticated: `User.Identity.Name` (guaranteed non-null by a Guard inside the helper)
   - Anonymous with valid `eShop` cookie: the GUID string from the cookie (validated via `Guid.TryParse`)
   - Anonymous without valid cookie: a newly minted `Guid.NewGuid().ToString()` — written to the `eShop` cookie with `IsEssential = true` and 10-year expiry

**What `OnGet` does AFTER the service call:**
- Assigns the returned `BasketViewModel` to `BasketModel` for Razor rendering

**Also called from:**
- `CheckoutModel.SetBasketModelAsync` (line 70) — uses the same `GetOrCreateBasketForUser` pattern for checkout page entry
- `IndexModel.OnPostUpdate` (line 62) — resolves basket ID before applying quantity updates

---

### Specifications (relevant)

**`BasketWithItemsSpecification(string buyerId)`**:
```csharp
Query.Where(b => b.BuyerId == buyerId).Include(b => b.Items);
```
- Exact case-sensitive string match on `BuyerId`
- Eager-loads `BasketItems` collection via JOIN

**`CatalogItemsSpecification(params int[] ids)`**:
```csharp
Query.Where(c => ids.Contains(c.Id));
```
- `WHERE Id IN (...)` — single batch query for all basket item catalog IDs

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `Baskets` | SELECT, INSERT | `Id`, `BuyerId` | SELECT with eager load via `BasketWithItemsSpecification`; INSERT on lazy creation when no basket exists for `buyerId` |
| `BasketItems` | SELECT | `Id`, `CatalogItemId`, `UnitPrice`, `Quantity`, `BasketId` | Loaded via `.Include(b => b.Items)` in same query as parent `Basket`; never mutated by this endpoint |
| `Catalog` | SELECT | `Id`, `Name`, `PictureUri` | Batch-fetched via `CatalogItemsSpecification(ids[])`; only `Name` and `PictureUri` are used |

---

## Security Considerations

### Authentication

- **Required**: no — any caller may retrieve any basket by `buyerId`
- Anonymous users are identified by their GUID `buyerId` — the web handler generates and stores this GUID in the `eShop` cookie for the lifetime of the browser session (10 years)

### Ownership Validation

The service accepts any string as `userName` and returns the corresponding basket. There is no check that the caller is authorized to read that buyer's basket. An authenticated user could supply a different `buyerId` and read another user's basket contents.

**Java target must add**: validate that the authenticated user's identity (JWT `sub`) matches the requested `buyerId` path parameter before returning basket data.

### Cookie Validation in Web Handler

The legacy `GetOrSetBasketCookieAndUserName()` validates the anonymous cookie value with `Guid.TryParse` — a cookie containing a non-GUID string (e.g., a tampered value) is treated as absent and a new GUID is minted. The REST target doesn't need this cookie logic since `buyerId` comes from the path parameter, but should document that `buyerId` format is not validated server-side for anonymous users.

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Two-query pattern | (1) `Baskets JOIN BasketItems` by buyerId; (2) `Catalog IN (ids)` | Java: `findByBuyerIdWithItems` (JOIN FETCH) + `findAllById(ids)` — same two-query pattern |
| N+1 risk | `GetBasketItems` uses `.First()` in-memory per item after batch fetch — no N+1 queries | Java: same pattern — batch `findAllById` then in-memory join |
| Lazy create on every new user | `AddAsync` fires once per new buyer identity — very low frequency | Java: `save(new Basket(userId))` if not found |
| No `Task.Delay` | No artificial delay | N/A |
| No AutoMapper | `BasketItemViewModel` manually constructed field-by-field | Java: manual DTO construction or MapStruct — same 6 fields |
| Empty basket on lazy create | `GetBasketItems` NOT called for lazy-created basket — the `Items` property is null/absent | Java: return `items: []` for newly created basket |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| Never returns 404 | Lazy-creates a basket if none exists; always returns 200 | Java: same — if basket not found, insert empty basket and return 200 with `items: []` |
| `pictureUrl` is absolute | `IUriComposer.ComposePicUri(catalogItem.PictureUri)` rewrites stored path | Java: compose absolute URL from configurable base URL + stored path; return absolute URL in response |
| Field name `pictureUrl` | Response uses `pictureUrl` (not `pictureUri`) | Java: JSON field name must be `pictureUrl` for Angular client compatibility |
| `unitPrice` from basket | `BasketItem.UnitPrice` — the price at add time | Java: read `basket_items.unit_price` — do NOT use current `catalog_items.price` |
| `productName` from catalog | `CatalogItem.Name` — current catalog name at query time | Java: join `catalog_items` by `catalog_item_id` for name; current name is correct |
| Two-round-trip read | Basket+Items query then Catalog batch query | Java: acceptable to keep as two queries; Spring Data `Page<T>` not needed here |
| buyerId identity | Authenticated: `User.Identity.Name`; Anonymous: validated GUID from `eShop` cookie | REST: `buyerId` comes from the path parameter — no cookie handling needed |
| Ownership check absent | Any caller can read any basket | Java: add authorization check — JWT `sub` must match `buyerId` |
| In-memory `.First()` lookup | `catalogItems.First(c => c.Id == basketItem.CatalogItemId)` throws if catalog item deleted | Java: use `.findFirst()` / `stream().filter().findFirst()` and handle empty Optional → 422 or remove stale item |

---

## Analysis Notes

- **`productName` reflects current catalog, `unitPrice` does not.** If an item's name changes in the catalog after it was added to the basket, the basket view will show the new name but the original add-time price. This is intentional — the basket preserves the price commitment but shows current product identity. The Java target should preserve this split: price from `basket_items`, name+picture from `catalog_items`.

- **`.First()` throws on deleted catalog items.** If a `BasketItem.CatalogItemId` references a catalog item that has since been deleted (via `delete-catalog-item`), `catalogItems.First(c => c.Id == ...)` throws `InvalidOperationException` → HTTP 500. The Java target should use `.filter().findFirst()` returning an `Optional` and either skip the stale item or return 422.

- **The `BasketViewModel` returned by `CreateBasketForUser` has null `Items`.** The property is not explicitly initialized to an empty list in the lazy-create path — `Items` is left as `null` in the returned `BasketViewModel`. The REST response mapper must handle null `Items` and serialize as `[]`. In Java, initialize the field with `new ArrayList<>()` to avoid null serialization.

- **`buyerId` string comparison is case-sensitive.** The `BasketWithItemsSpecification` uses `b.BuyerId == buyerId` — this becomes a case-sensitive SQL comparison if the database collation is CS (case-sensitive). If the Angular client sends `alice@example.com` but the database stores `Alice@Example.Com`, no basket will be found and a new one will be lazy-created. The Java target should normalize `buyerId` to lowercase or match the collation behavior.

- **The endpoint is also called by `CheckoutModel` and `OnPostUpdate`.** In the REST world, the Angular client calls this endpoint explicitly (to get basket ID before posting updates). It is a multipurpose read that serves the basket view, the checkout entry, and the quantity update preparation.

- **`IBasketQueryService` is injected but not used by this method.** `CountTotalBasketItems` is a separate method on the service. The Java target should implement this as a separate endpoint or include an `itemCount` in the basket response.
