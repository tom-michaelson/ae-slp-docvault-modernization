# Describe API Endpoint

Produce a detailed technical narrative (`functional-description.md`) for an eShopOnWeb API endpoint. This document describes **how the legacy endpoint works** — the REST contract, business logic, call sequence, database dependencies, and migration constraints — in enough detail for a Java developer to implement the equivalent Spring Boot `@RestController` endpoint without reading the original C# source.

This is a **discover-phase** command. It reads the artifacts already written by `analyze-api-endpoint` plus the actual source files, and enriches them into a structured developer-facing description.

**Pipeline position:**
```
analyze-api-endpoint  →  metadata.json, call-tree.json, database-dependencies.json, functional-spec.md
describe-api-endpoint →  functional-description.md    ← this command
```

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<endpoint-key>  endpoint_dir=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | The endpoint key (e.g., `list-catalog-items-paged`) |
| `endpoint_dir` | Absolute path to the endpoint folder (e.g., `.../docs/entry-points/api-endpoints/list-catalog-items-paged`) |

Source files are resolved from `./source/{legacyLocation}` relative to cwd (`target_repo/`), using the `legacyLocation` field in `{endpoint_dir}/metadata.json`.

**Examples:**

```
key=list-catalog-items-paged
endpoint_dir=/abs/path/docs/entry-points/api-endpoints/list-catalog-items-paged
```

```
key=add-item-to-basket
endpoint_dir=/abs/path/docs/entry-points/api-endpoints/add-item-to-basket
```

---

## Idempotency

- If `{endpoint_dir}/functional-description.md` already exists → **stop immediately**. The analysis is complete.
- If `{endpoint_dir}/functional-description.in-progress.md` exists → a previous run crashed. **Overwrite it** and re-run the full analysis.
- Otherwise → proceed with full analysis.

---

## Inputs Read by This Command

From `{endpoint_dir}/`:

| File | What to extract |
|---|---|
| `metadata.json` | `key`, `name`, `domain`, `legacyEntryPoint`, `legacyLocation`, `legacyWebHandler` (if present), `targetRestContract`, `usedByUiFeatures`, `notes` |
| `functional-spec.md` | Purpose, Inputs table, Outputs JSON example, Gherkin scenarios, business rules, non-functional notes |
| `call-tree.json` | Entry point method and signature, call chain nodes, DB operations |
| `database-dependencies.json` | Tables, columns, operations, file locations |

From `./source/` (cwd-relative):

| Resolved from | What to read |
|---|---|
| `./source/{legacyLocation}` | The endpoint class file (MinimalApi) or service method file (in-process) |
| `./source/{call-tree.legacyWebHandler.file}` | The Razor Page handler that calls the service — **in-process only** |
| `./source/{call-tree.calls[].file}` | Service implementations, entity method files, Specification classes listed in the call tree |

---

## Output

```
{endpoint_dir}/functional-description.md
```

Written incrementally via:
1. Create `{endpoint_dir}/functional-description.in-progress.md` at Phase 1
2. Write each section as it is completed
3. Rename to `functional-description.md` at Phase 4 (final step)

---

## Output Template

The template below uses `list-catalog-items-paged` (MinimalApi GET) as the filled-in example. For an in-process service, replace the Component Details section and adapt the Call Sequence and Migration Notes accordingly — see the In-process service note blocks throughout.

```markdown
# Functional Description: {name}

> **Entry Point**: {key}
> **Location**: {legacyLocation}
> **Type**: API / {MinimalApi.Endpoint | In-process Service}
> **Domain**: {domain}
> **Legacy method**: {legacyEntryPoint}
> **Web handler**: {legacyWebHandler}   ← include only for in-process services

## Executive Summary

[2–3 paragraphs covering:
1. What operation this endpoint performs and which Angular component or UI feature calls it
2. The key constraints: auth requirements, lazy creation, server-side lookups, validation guards
3. Anything non-obvious about the legacy implementation that the Java developer must understand
   before implementing]

For example (list-catalog-items-paged):
The `list-catalog-items-paged` endpoint returns a paginated, optionally filtered page of catalog
items from the eShopOnWeb store. It is called by the Angular homepage on initial load and on every
filter or pagination interaction.

The endpoint performs two sequential database queries: a COUNT query to compute the total page
count, then a paginated SELECT query for the current page. Each item's `PictureUri` is rewritten
from a relative path to an absolute URL before being returned.

No authentication is required. A deliberate 1-second artificial delay (`Task.Delay(1000)`)
exists in the legacy implementation — this must NOT be carried over to the Java target.

---

## REST Contract

### HTTP Request

| Component | Value |
| --- | --- |
| Method | GET |
| Path | `/api/catalog-items` |
| Auth required | no |

### Query Parameters *(GET endpoints — omit section for POST/PUT)*

| Name | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `pageSize` | int | no | 10 | Items per page. When `0`, returns all matching items. |
| `pageIndex` | int | no | 0 | 0-indexed page number |
| `catalogBrandId` | int | no | null | Filters by `Catalog.CatalogBrandId` |
| `catalogTypeId` | int | no | null | Filters by `Catalog.CatalogTypeId` |

### Request Body *(POST/PUT endpoints — omit section for GET)*

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `catalogItemId` | int | yes | Must reference a valid CatalogItem |
| `quantity` | int | no | Default 1. Must be > 0. |

> **Price is NOT in the request body.** The legacy caller (`IndexModel.OnPost`) looks up the
> current price from Catalog before calling the service. The Java target must look up the price
> server-side — never trust a client-supplied price.

### Success Response

```json
{
  "pageCount": 2,
  "catalogItems": [
    {
      "id": 1,
      "name": ".NET Bot Black Sweatshirt",
      "pictureUri": "https://host/images/products/1.png",
      "price": 19.50,
      "catalogBrandId": 1,
      "catalogTypeId": 2
    }
  ]
}
```

### Error Responses

| Status | Condition | Body |
| --- | --- | --- |
| 401 | JWT required but absent or invalid | empty |
| 404 | Resource not found (in-process endpoints that look up by ID) | empty |
| 400 | Validation guard triggered (negative quantity, null ID, etc.) | ValidationProblem or empty |

---

## Business Logic

### Overview

[Narrative of what this endpoint does — written so a Java developer can implement it without
reading the C# source. Cover: what it queries or mutates, the key invariants that must hold,
and any branching behavior (empty result, lazy creation, redirect on error).]

list-catalog-items-paged example:
The endpoint accepts optional `catalogBrandId` and/or `catalogTypeId` filters. Both are optional;
if omitted, all items are included. Pagination is controlled by `pageSize` (items per page) and
`pageIndex` (0-based). When `pageSize=0`, all matching items are returned in a single page.

Two queries are issued: a COUNT to compute `pageCount`, then a paginated SELECT for the current
page. `pageCount = ceil(totalItems / pageSize)`. Each returned item's `PictureUri` is rewritten
from a relative storage path to an absolute URL via `IUriComposer.ComposePicUri`.

### Validation Rules

| Field / Condition | Rule | Failure behavior |
| --- | --- | --- |
| `pageSize` | Integer ≥ 0 | `Guard.Against.Negative` → exception → 500 (legacy); Java: return 400 |
| `pageIndex` | Integer ≥ 0 | Same as above |
| `productDetails.Id` | Not null (in-process) | Redirect to `/Index` (legacy web); Java: return 400 |

### Call Sequence

[Numbered walkthrough of what happens when a request arrives. Derived from `call-tree.json` and
source file reads — not just a list of method names, but what each call does and why.]

**list-catalog-items-paged:**
1. Receive request: `pageSize`, `pageIndex`, optional `catalogBrandId`, `catalogTypeId`
2. Build `CatalogFilterSpecification(catalogBrandId, catalogTypeId)` — encapsulates WHERE clause
3. `IRepository<CatalogItem>.CountAsync(spec)` → total matching items → compute `pageCount = ceil(total / pageSize)` (1 when `pageSize=0`)
4. Build `CatalogFilterPaginatedSpecification(skip=pageSize*pageIndex, take=pageSize, brandId, typeId)`
5. `IRepository<CatalogItem>.ListAsync(pagedSpec)` → materialize current page rows
6. For each item: `IUriComposer.ComposePicUri(item.PictureUri)` → rewrite to absolute URL
7. `_mapper.Map<CatalogItemDto>(item)` → project entity to DTO (AutoMapper)
8. Return `ListPagedCatalogItemResponse { pageCount, catalogItems }`

---

## Component Details

### MinimalApi.Endpoint *(include for MinimalApi.Endpoint type)*

**Class**: `CatalogItemListPagedEndpoint`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs`

**Route registration (`AddRoute()`):**
```csharp
app.MapGet("api/catalog-items", HandleAsync)
   .Produces<ListPagedCatalogItemResponse>()
   .ProducesProblem(401);
```

**Request type**: `ListPagedCatalogItemRequest`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.ListPagedCatalogItemRequest.cs`
**Fields**: `pageSize` (int, default 10), `pageIndex` (int, default 0), `catalogBrandId` (int?), `catalogTypeId` (int?)

**Response type**: `ListPagedCatalogItemResponse`
**File**: `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.ListPagedCatalogItemResponse.cs`
**Fields**: `pageCount` (int), `catalogItems` (List\<CatalogItemDto\>)

**Injected dependencies**: `IRepository<CatalogItem>`, `IMapper` (AutoMapper), `IUriComposer`

---

### In-process Service *(include for In-process Service type — replace MinimalApi section above)*

**Service class**: `BasketService`
**Service file**: `src/ApplicationCore/Services/BasketService.cs`
**Method signature**: `Task AddItemToBasket(string username, int catalogItemId, decimal price, int quantity = 1)`

**Called from web handler**: `IndexModel.OnPost`
**Web handler file**: `src/Web/Pages/Basket/Index.cshtml.cs`

**What `IndexModel.OnPost` does BEFORE calling the service:**
1. Validates `productDetails.Id` is not null — redirects to `/Index` if null
2. Calls `IRepository<CatalogItem>.GetByIdAsync(productDetails.Id)` to get the **current price**
3. If item not found → redirects to `/Index`
4. Resolves buyer identity via `GetOrSetBasketCookieAndUserName()` (cookie or auth username)
5. **Then** calls `BasketService.AddItemToBasket(username, catalogItemId, price, quantity=1)`

**What `IndexModel.OnPost` does AFTER the service call:**
- `RedirectToPage()` → GET `/Basket` (Post-Redirect-Get)

> The Java REST endpoint must replicate the pre-call logic (price lookup from Catalog, buyer
> identity resolution) inside the endpoint handler. The price must never be accepted from the
> request body.

---

## Database Dependencies

| Table | Operations | Key columns | Notes |
| --- | --- | --- | --- |
| `Catalog` | SELECT, COUNT | `Id`, `Name`, `Price`, `PictureUri`, `CatalogBrandId`, `CatalogTypeId` | COUNT for pageCount calculation; SELECT for current page via paginated specification |
| `Baskets` | SELECT, INSERT | `Id`, `BuyerId` | Lazy creation: INSERT only when no basket exists for the buyer's identity |
| `BasketItems` | INSERT, UPDATE | `BasketId`, `CatalogItemId`, `UnitPrice`, `Quantity` | INSERT if item not in basket; UPDATE (increment Quantity) if already present |

---

## Security Considerations

### Authentication

- **Required**: no / yes — JWT Bearer via `[Authorize]` + `RequireAuthorization()` in `AddRoute()`
- **Mechanism**: *(if required)* JWT bearer token in `Authorization: Bearer {token}` header
- **Notes**: ...

### Price Integrity *(if applicable)*

Price is sourced from the `Catalog` table on the server. The legacy Razor Page handler (`OnPost`) looks up the item price from `IRepository<CatalogItem>` before passing it to `AddItemToBasket`. **The Java target must replicate this server-side price lookup** — the endpoint must never accept a client-supplied price.

### Input Validation

[Describe what the endpoint validates (guard clauses, model state checks) and what it does NOT validate — so the Java developer knows where to add validation that the legacy code lacks.]

---

## Performance Notes

| Concern | Detail | Java target action |
| --- | --- | --- |
| Deliberate delay | `await Task.Delay(1000)` in `HandleAsync` | **Do NOT carry over** — this is an artificial simulation delay in the demo app |
| AutoMapper | `_mapper.Map<CatalogItemDto>(item)` per result item | Java: use MapStruct or manual projection; ensure same fields are mapped |
| Two-query pagination | COUNT query + SELECT query are separate round-trips | Java: `Page<T>` from Spring Data gives both in one call; acceptable to keep two queries if simpler |
| Lazy basket creation | `IRepository<Basket>.AddAsync` fires only when basket is null | Java: make the create idempotent (check before insert, or use upsert semantics) |

---

## Migration Notes

| Aspect | Legacy C# behavior | Java target requirement |
| --- | --- | --- |
| `pictureUri` rewriting | `IUriComposer.ComposePicUri` converts relative storage path to absolute URL using app's base URL | Java endpoint must compose the absolute URI; either store absolute URLs in DB or implement equivalent URI composition |
| `pageSize=0` semantics | When `pageSize=0`, all matching items are returned (skip=0, take=all) | Preserve this behaviour or document it is intentionally changed |
| `Task.Delay(1000)` | Artificial 1-second delay in `HandleAsync` | **Remove** — do not replicate in Java target |
| Price source (basket) | Caller (`OnPost`) looks up price from `Catalog` before calling service; service receives price as parameter | Java endpoint handler must look up price from `Catalog` entity; reject any client-supplied price field |
| Anonymous buyer identity | GUID from `eShop` cookie resolves the `BuyerId`; basket created lazily on first access | Angular client sends `buyerId` as path parameter; Java endpoint receives it and trusts it the same way |
| `Basket.RemoveEmptyItems()` | Called on SetQuantities — removes items with `Quantity=0` from the basket aggregate | Java must replicate the item-deletion behaviour when quantity is set to 0 |

---

## Analysis Notes

[Technical debt, edge cases, and anything that would surprise a Java developer implementing this endpoint.]

- `pageCount` when `pageSize=0`: the legacy code computes `pageCount = 1` when all items fit one "infinite" page. Java target should decide whether to preserve this or return `pageCount = 0` for an empty result set when `pageSize=0`.
- AutoMapper projection via `_mapper.Map<CatalogItemDto>`: the DTO may not include all entity fields. Read the `CatalogItemDto` class to confirm exactly which fields are projected — only those fields should appear in the Spring Boot response DTO.
- `BasketItem` quantity guard: `BasketItem.cs` throws `ArgumentException` if quantity ≤ 0. The Java target should return HTTP 400 rather than propagating a 500.
- `Basket.RemoveEmptyItems()` is a domain aggregate method called in `SetQuantities`, not in `AddItemToBasket`. Note it here for reference when the `update-basket-quantities` endpoint is described.
```

---

## Discovery Process

### Phase 0: Idempotency Check

1. Check if `{endpoint_dir}/functional-description.md` exists → **stop** if yes.
2. Check if `{endpoint_dir}/functional-description.in-progress.md` exists → overwrite it if yes and re-run the full analysis.

---

### Phase 1: Read Artifacts and Create In-Progress File

1. Read `{endpoint_dir}/metadata.json` — extract all fields.
2. **Detect entry point type:**
   - `legacyLocation` contains `src/PublicApi/` → **MinimalApi.Endpoint**
   - `legacyLocation` contains `src/Web/Services/` or `src/ApplicationCore/Services/` → **In-process service**
   - Belt-and-suspenders: if `legacyWebHandler` field is present → **In-process service**
3. Read `{endpoint_dir}/functional-spec.md` — note Purpose, Inputs table, Outputs JSON, Gherkin scenarios, business rules. These are your baseline; the description must not contradict them, only deepen them.
4. Read `{endpoint_dir}/call-tree.json` — note entry point method and signature, every call node, all `db` ops.
5. Read `{endpoint_dir}/database-dependencies.json` — note all tables, operations, columns.
6. **Write `{endpoint_dir}/functional-description.in-progress.md`** with the template header:
   ```
   # Functional Description: {name}
   > **Entry Point**: {key}
   > **Location**: {legacyLocation}
   > **Type**: API / {MinimalApi.Endpoint | In-process Service}
   > **Domain**: {domain}
   > **Legacy method**: {legacyEntryPoint}
   > **Web handler**: {legacyWebHandler}    ← only for in-process
   ```

---

### Phase 2: Read Source Files

**For MinimalApi.Endpoint:**
1. Read `./source/{legacyLocation}` — extract:
   - `AddRoute()` signature: HTTP verb, exact path string, auth policies applied
   - `HandleAsync()` body: every step, each method called, guard clauses, return values
   - Injected constructor parameters (dependencies)
2. Find and read companion request/response type files referenced in the endpoint class (look for inner class file names ending in `Request.cs` and `Response.cs`). Extract all property names and types.
3. For each call in `call-tree.json` with a `file` field, read `./source/{file}`:
   - Specification files: confirm which entity properties are filtered/selected
   - Entity method files: understand what domain mutations happen (e.g., `Basket.AddItem`, `RemoveEmptyItems`)

**For In-process service:**
1. Read `./source/{legacyLocation}` — find the specific service method matching `key` (e.g., `add-item-to-basket` → `AddItemToBasket`). Extract:
   - Method signature (return type, all parameters)
   - Guard clauses and their conditions
   - Every repository call and what it does
   - Every entity method call
   - Conditional branches (create-if-not-exists, increment-if-exists, etc.)
2. Read `./source/{call-tree.legacyWebHandler.file}` — find the Razor Page handler (`OnPost`, `OnGet`, etc.). Extract:
   - What it does BEFORE calling the service (price lookup, identity resolution, validation, null guards)
   - What parameters it constructs for the service call
   - What it does AFTER the service call (redirect, re-render, error handling)
3. For each entity method file in `call-tree.json`, read `./source/{file}` — understand domain invariants (what guards throw, what side effects happen, which DB columns are actually written).
4. For each Specification file in `call-tree.json`, read `./source/{file}` — confirm which columns are queried and what the WHERE clause does.

---

### Phase 3: Write All Sections

Write each section to `functional-description.in-progress.md` as it is completed — do not batch.

**Section order:**
1. Executive Summary
2. REST Contract (HTTP Request → Query Params or Request Body → Success Response → Error Responses)
3. Business Logic (Overview → Validation Rules → Call Sequence)
4. Component Details (MinimalApi.Endpoint section -or- In-process Service section based on type)
5. Database Dependencies
6. Security Considerations
7. Performance Notes
8. Migration Notes
9. Analysis Notes

**MinimalApi.Endpoint emphasis:**
- REST Contract is the primary deliverable — fill every field from `AddRoute()` and request/response types
- Call Sequence is a direct walkthrough of `HandleAsync()` body
- Migration Notes covers: `Task.Delay` removal, `pictureUri` rewriting, AutoMapper DTO projection

**In-process service emphasis:**
- Component Details must document BOTH the service method AND the web handler's pre/post-call logic
- Call Sequence should trace: web handler pre-call → service method → entity methods → repositories
- Migration Notes is especially important — the Java target REST endpoint must replicate the web handler's pre-call logic (identity resolution, price lookup) inside the handler, not just the service method logic

---

### Phase 4: Finalise

1. Review: all Gherkin scenarios from `functional-spec.md` are reflected somewhere in Business Logic.
2. Review: all tables from `database-dependencies.json` appear in the Database Dependencies table.
3. Review: `targetRestContract` fields from `metadata.json` are fully reflected in the REST Contract section.
4. Review: any `Task.Delay`, AutoMapper usage, price-source concerns, or domain guard clauses are captured in Performance Notes, Migration Notes, or Analysis Notes.
5. Rename: `functional-description.in-progress.md` → `functional-description.md`

---

## Implementation Workflow

### Step 1: Parse Parameters
Read `key` and `endpoint_dir` from `{{PROMPT}}`.

### Step 2: Idempotency Check
If `{endpoint_dir}/functional-description.md` exists → stop immediately.

### Step 3: Read All Artifacts
Read `metadata.json`, `functional-spec.md`, `call-tree.json`, `database-dependencies.json` from `endpoint_dir`.

### Step 4: Detect Entry Point Type
From `legacyLocation` in `metadata.json`: `src/PublicApi/` → MinimalApi; otherwise → In-process service.

### Step 5: Write In-Progress File
Create `{endpoint_dir}/functional-description.in-progress.md` with the header block.

### Step 6: Read Source Files
- MinimalApi: endpoint class + companion request/response types + Specification and entity files from call tree
- In-process: service method file + Razor Page caller file + entity method files + Specification files

### Step 7: Write All Sections
Write sections 1–9 incrementally to the in-progress file as each is completed.

### Step 8: Rename to Final
`mv {endpoint_dir}/functional-description.in-progress.md {endpoint_dir}/functional-description.md`

### Step 9: Report Summary
```
Key:              {key}
Entry point type: {MinimalApi.Endpoint | In-process service}
HTTP contract:    {METHOD} {path}
Auth required:    {yes | no}
DB tables:        {list}
Source files read: {count}
Output:           {endpoint_dir}/functional-description.md
```

---

## Worked Examples

### Example 1: MinimalApi GET — `list-catalog-items-paged`

**Input:**
```
key=list-catalog-items-paged
endpoint_dir=/path/docs/entry-points/api-endpoints/list-catalog-items-paged
```

**Entry point type:** MinimalApi (`legacyLocation` = `src/PublicApi/CatalogItemEndpoints/...`)

**Artifacts read:** `metadata.json` (MinimalApi, domain=catalog, no `legacyWebHandler`), `functional-spec.md` (4 Gherkin scenarios), `call-tree.json` (2 repository calls + IUriComposer call), `database-dependencies.json` (Catalog: select + count)

**Source files read:** `CatalogItemListPagedEndpoint.cs`, `ListPagedCatalogItemRequest.cs`, `ListPagedCatalogItemResponse.cs`, `CatalogFilterSpecification.cs`, `CatalogFilterPaginatedSpecification.cs`

**REST Contract:** `GET /api/catalog-items` with 4 optional query params; no auth

**Call Sequence:** COUNT query for `pageCount` → paginated SELECT → URI rewrite per item → AutoMapper projection → return response

**Key Migration Notes:**
- `Task.Delay(1000)` in `HandleAsync` — **do NOT carry over to Java**
- `pictureUri` rewriting via `IUriComposer` — implement equivalent in Java
- `pageSize=0` → return all items — preserve or explicitly change

**Key Analysis Notes:**
- AutoMapper projects entity → DTO; read `CatalogItemDto` to confirm which fields appear in response
- `pageCount` calculation when `pageSize=0` should be clarified in business rules

---

### Example 2: In-process service POST — `add-item-to-basket`

**Input:**
```
key=add-item-to-basket
endpoint_dir=/path/docs/entry-points/api-endpoints/add-item-to-basket
```

**Entry point type:** In-process service (`legacyLocation` = `src/ApplicationCore/Services/BasketService.cs`, `legacyWebHandler` field present)

**Artifacts read:** `metadata.json` (in-process, domain=basket, `legacyWebHandler=IndexModel.OnPost`), `functional-spec.md`, `call-tree.json` (Baskets select/insert, BasketItems insert/update), `database-dependencies.json`

**Source files read:** `BasketService.cs` (AddItemToBasket method), `Index.cshtml.cs` (OnPost handler), `Basket.cs` (AddItem entity method), `BasketItem.cs` (quantity guard), `BasketWithItemsSpecification.cs`

**REST Contract:** `POST /api/baskets/for-user/{buyerId}/items` with body `{catalogItemId, quantity}`; no auth

**Component Details covers BOTH:**
- Service method: lazy basket creation, AddItem (increment vs insert), repository calls
- Web handler pre-call: price lookup from Catalog, null ID guard, buyer identity resolution

**Key Migration Notes:**
- Price must be looked up server-side in Java — never from request body
- Buyer identity: GUID from `eShop` cookie becomes `buyerId` path parameter in REST target

**Key Analysis Notes:**
- `BasketItem` quantity guard throws `ArgumentException` on ≤ 0 — Java should return 400
- `Basket.RemoveEmptyItems()` is a domain method relevant to the update-quantities endpoint, not this one — note its existence

---

## Important Notes

1. **The REST Contract section is the Java developer's primary reference.** Every field from `targetRestContract` in `metadata.json` must appear here, enriched with the detail from source reads. A vague REST Contract causes rework in the develop phase.

2. **In-process services: document the web handler's pre-call logic explicitly.** The service method alone is not the complete picture. The Razor Page handler performs meaningful work before calling it — price lookup, identity resolution, validation. The Java REST endpoint must replicate that logic inside its handler. Capture it fully in Component Details and Migration Notes.

3. **Do not contradict `functional-spec.md`.** The Gherkin and business rules already written there are correct. The description deepens them — it does not change their meaning.

4. **Source path resolution.** All source files are at `./source/{path}` relative to cwd. If `call-tree.json` lists `src/ApplicationCore/Services/BasketService.cs`, read it from `./source/src/ApplicationCore/Services/BasketService.cs`.

5. **Migration Notes is the most important section for preventing Java bugs.** Always check for and document:
   - `Task.Delay` — **do NOT carry over**
   - Price lookup pattern — must happen server-side
   - Lazy creation — replicate the idempotency semantics
   - `pictureUri` rewriting — implement equivalent in Java
   - Anonymous buyer identity — understand cookie-to-path-parameter mapping

6. **Performance Notes is where AutoMapper usage is flagged.** Java developers may not realise the legacy code is doing object-to-DTO mapping and that specific fields are projected. Note which fields the DTO includes.

7. **Write incrementally.** Write each section to the `.in-progress.md` file as you complete it. Do not draft the entire document in memory and write once at the end — long analyses can be interrupted.

8. **`legacyWebHandler` in metadata.json is the signal for in-process services.** Its `file` field (from `call-tree.json`) gives you the exact Razor Page file to read. Use it.
