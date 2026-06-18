# Analyze API Endpoint

You are tasked with producing a detailed analysis of a single API entry point from the eShopOnWeb ASP.NET Core 8.0 application. The output feeds a modernization effort targeting **Spring Boot 3.5 (Java 25) REST API + Angular 19 SPA** — every artifact must contain enough technical and business detail for a Java developer to implement the equivalent Spring Boot `@RestController` endpoint without consulting the original source.

This is a **discover-phase** command. It reads the legacy eShopOnWeb source and writes structured artifacts to `docs/entry-points/api-endpoints/{key}/`.

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
key=<endpoint-key>  legacy_dir=<abs-path>  location=<rel-path>  output_dir=<abs-path>
```

| Argument | Description |
|---|---|
| `key` | Logical name for this endpoint (e.g., `list-catalog-items`) |
| `legacy_dir` | Absolute path to the eShopOnWeb source root (e.g., `.../target_repo/source`) |
| `location` | Path to the entry point file, **relative to `legacy_dir`** (e.g., `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs`) |
| `output_dir` | Absolute path to the output folder — create it if needed, overwrite files if present |

**Examples:**

```
key=list-catalog-items-paged
legacy_dir=/abs/path/target_repo/source
location=src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs
output_dir=/abs/path/docs/entry-points/api-endpoints/list-catalog-items-paged
```

```
key=add-item-to-basket
legacy_dir=/abs/path/target_repo/source
location=src/ApplicationCore/Services/BasketService.cs
output_dir=/abs/path/docs/entry-points/api-endpoints/add-item-to-basket
```

```
key=authenticate-user
legacy_dir=/abs/path/target_repo/source
location=src/PublicApi/AuthEndpoints/AuthenticateEndpoint.cs
output_dir=/abs/path/docs/entry-points/api-endpoints/authenticate-user
```

---

## Entry Point Types

Two distinct patterns exist in eShopOnWeb. Detect the type from `location`:

| Pattern | Location clue | Description |
|---|---|---|
| **MinimalApi.Endpoint** | `src/PublicApi/` | Implements `IEndpoint<IResult,TRequest,TDep>`. Has `AddRoute()` + `HandleAsync()`. JWT auth, Swagger annotations. Already a REST endpoint. |
| **In-process service** | `src/Web/Services/` or `src/ApplicationCore/Services/` | Called in-process from Razor Page handlers. Not yet a REST endpoint. Will become a Spring Boot `@RestController`. |

---

## Output

Four files, written to `{output_dir}/`:

```
{output_dir}/
├── metadata.json
├── functional-spec.md
├── call-tree.json
└── database-dependencies.json
```

---

### `metadata.json` — filled-in example (MinimalApi.Endpoint)

```json
{
  "key": "list-catalog-items-paged",
  "name": "List catalog items (paginated)",
  "type": "api-endpoint",
  "domain": "catalog",
  "legacyEntryPoint": "Microsoft.eShopWeb.PublicApi.CatalogItemEndpoints.CatalogItemListPagedEndpoint.HandleAsync",
  "legacyLocation": "src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs:40",
  "targetRestContract": {
    "method": "GET",
    "path": "/api/catalog-items",
    "queryParams": [
      {"name": "pageSize",       "type": "int",  "default": 10, "optional": true},
      {"name": "pageIndex",      "type": "int",  "default": 0,  "optional": true},
      {"name": "catalogBrandId", "type": "int",  "optional": true},
      {"name": "catalogTypeId",  "type": "int",  "optional": true}
    ],
    "responseModel": "ListPagedCatalogItemResponse",
    "auth": "none",
    "notes": "MinimalApi endpoint already HTTP-exposed. Target Java endpoint keeps same route and query params."
  },
  "usedByUiFeatures": ["homepage-catalog-list"]
}
```

### `metadata.json` — filled-in example (in-process service)

```json
{
  "key": "add-item-to-basket",
  "name": "Add item to basket",
  "type": "api-endpoint",
  "domain": "basket",
  "legacyEntryPoint": "Microsoft.eShopWeb.ApplicationCore.Services.BasketService.AddItemToBasket",
  "legacyLocation": "src/ApplicationCore/Services/BasketService.cs:23",
  "legacyWebHandler": "Microsoft.eShopWeb.Web.Pages.Basket.IndexModel.OnPost",
  "targetRestContract": {
    "method": "POST",
    "path": "/api/baskets/for-user/{buyerId}/items",
    "requestModel": {
      "catalogItemId": "int",
      "quantity": "int (default 1)"
    },
    "responseModel": "BasketResponse",
    "auth": "none (buyerId from path, maps to cookie or auth username)",
    "notes": "In legacy this is called in-process from IndexModel.OnPost. The REST target must look up the current Catalog price server-side — never trust a client-supplied price."
  },
  "usedByUiFeatures": ["basket-view-page", "homepage-catalog-list"],
  "notes": [
    "Creates a basket lazily if none exists for buyerId.",
    "Increments quantity on an existing BasketItems row rather than inserting a duplicate."
  ]
}
```

---

### `functional-spec.md` — filled-in example

```markdown
# Functional spec — List catalog items

**Key:** `list-catalog-items-paged`
**Legacy:** `CatalogItemListPagedEndpoint.HandleAsync` — `GET api/catalog-items`
**Target REST:** `GET /api/catalog-items`

## Purpose

Return a paginated, optionally filtered page of catalog items. Angular homepage calls
this on every load and every filter or pagination change.

## Inputs

| Name | Type | Optional | Default | Notes |
| --- | --- | --- | --- | --- |
| `pageSize` | int | yes | 10 | Items per page. When `0`, returns all matching items. |
| `pageIndex` | int | yes | 0 | 0-indexed page number |
| `catalogBrandId` | int? | yes | null | Filters by `Catalog.CatalogBrandId` |
| `catalogTypeId` | int? | yes | null | Filters by `Catalog.CatalogTypeId` |

## Outputs

\`\`\`json
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
\`\`\`

## Acceptance criteria

\`\`\`
Scenario: No filters, first page
  Given 12 catalog items exist
  When GET /api/catalog-items?pageSize=10&pageIndex=0
  Then response.catalogItems.length == 10
  And response.pageCount == 2

Scenario: Filter by brand
  Given only 3 items have catalogBrandId=5
  When GET /api/catalog-items?catalogBrandId=5
  Then response.catalogItems.length == 3
  And response.pageCount == 1

Scenario: pageSize=0 returns all items
  Given 12 catalog items exist
  When GET /api/catalog-items?pageSize=0
  Then response.catalogItems.length == 12
  And response.pageCount == 1

Scenario: PictureUri is rewritten to absolute URL
  Given a CatalogItem with PictureUri "images/products/1.png"
  When the endpoint is called
  Then response.catalogItems[0].pictureUri starts with "https://"
\`\`\`

## Business rules

- `pageCount = ceil(totalMatchingItems / pageSize)`. When `pageSize == 0`, `pageCount = 1` (or 0 if no items).
- `pictureUri` is rewritten from a relative path to an absolute URL via `IUriComposer.ComposePicUri`.
- A deliberate 1-second delay (`Task.Delay(1000)`) exists in the current implementation — **do not carry this over** to the Java target.

## Non-functional

- Read-only; no writes.
- No authentication required.
- Called on every homepage load and every filter/pagination interaction.
```

---

### `call-tree.json` — MinimalApi.Endpoint shape

```json
{
  "entryPoint": {
    "method": "Microsoft.eShopWeb.PublicApi.CatalogItemEndpoints.CatalogItemListPagedEndpoint.HandleAsync",
    "file": "src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs",
    "line": 40,
    "signature": "Task<IResult> HandleAsync(ListPagedCatalogItemRequest request, IRepository<CatalogItem> itemRepository)"
  },
  "calls": [
    {
      "method": "new CatalogFilterSpecification(brandId, typeId)",
      "file": "src/ApplicationCore/Specifications/CatalogFilterSpecification.cs"
    },
    {
      "method": "IRepository<CatalogItem>.CountAsync",
      "db": {"table": "Catalog", "op": "count"},
      "notes": "Counts matching rows for pageCount calculation."
    },
    {
      "method": "new CatalogFilterPaginatedSpecification(skip, take, brandId, typeId)",
      "file": "src/ApplicationCore/Specifications/CatalogFilterPaginatedSpecification.cs",
      "line": 7
    },
    {
      "method": "IRepository<CatalogItem>.ListAsync",
      "db": {"table": "Catalog", "op": "select"},
      "notes": "Applies pagination spec; materializes the current page of rows."
    },
    {
      "method": "IUriComposer.ComposePicUri",
      "notes": "Rewrites each item's PictureUri to an absolute URL."
    }
  ]
}
```

### `call-tree.json` — in-process service shape (multiple callers)

When the legacy entry point is an in-process service called from a Razor Page, represent the web handler as a wrapper around the service:

```json
{
  "legacyWebHandler": {
    "method": "Microsoft.eShopWeb.Web.Pages.Basket.IndexModel.OnPost",
    "file": "src/Web/Pages/Basket/Index.cshtml.cs",
    "line": 33
  },
  "entryPoint": {
    "method": "Microsoft.eShopWeb.ApplicationCore.Services.BasketService.AddItemToBasket",
    "file": "src/ApplicationCore/Services/BasketService.cs",
    "line": 23,
    "signature": "Task AddItemToBasket(string username, int catalogItemId, decimal price, int quantity = 1)"
  },
  "calls": [
    {
      "method": "IRepository<Basket>.FirstOrDefaultAsync(BasketWithItemsSpecification)",
      "db": {"table": "Baskets", "op": "select"}
    },
    {
      "method": "IRepository<Basket>.AddAsync",
      "db": {"table": "Baskets", "op": "insert"},
      "notes": "Only when no basket exists for the buyer."
    },
    {
      "method": "Basket.AddItem",
      "file": "src/ApplicationCore/Entities/BasketAggregate/Basket.cs",
      "line": 22,
      "notes": "Adds a new BasketItem or increments quantity if catalogItemId already present."
    },
    {
      "method": "IRepository<Basket>.UpdateAsync",
      "db": [
        {"table": "BasketItems", "op": "insert"},
        {"table": "BasketItems", "op": "update"}
      ]
    }
  ]
}
```

### `database-dependencies.json` — filled-in example

```json
[
  {
    "type": "table",
    "name": "Catalog",
    "key": "catalog",
    "operations": ["select", "count"],
    "columns": ["Id", "Name", "Price", "PictureUri", "CatalogBrandId", "CatalogTypeId"],
    "locations": [
      "src/ApplicationCore/Specifications/CatalogFilterSpecification.cs",
      "src/ApplicationCore/Specifications/CatalogFilterPaginatedSpecification.cs"
    ],
    "notes": [
      "Filtered by optional CatalogBrandId and CatalogTypeId via Specification classes.",
      "Paginated via Skip(pageSize * pageIndex).Take(pageSize)."
    ]
  }
]
```

---

## Field Rules

### metadata.json

| Field | Rule |
|---|---|
| `key` | Copied verbatim from the `key` arg |
| `name` | Human-readable name for the operation. Derive from the class/method name: `CatalogItemListPagedEndpoint` → `"List catalog items (paginated)"` |
| `type` | Always `"api-endpoint"` |
| `domain` | Derive from the namespace or folder: `CatalogItemEndpoints` → `"catalog"`, `BasketService` → `"basket"`, `AuthEndpoints` → `"auth"` |
| `legacyEntryPoint` | Fully qualified `Namespace.Class.Method` of the primary entry point (for MinimalApi: `HandleAsync`; for services: the service method itself) |
| `legacyLocation` | `{file-relative-to-legacy_dir}:{line}` of the entry point method definition |
| `legacyWebHandler` | **In-process services only.** Fully qualified name of the Razor Page handler that calls this service. Omit the field for MinimalApi endpoints. |
| `targetRestContract.method` | HTTP verb: extract from `MapGet/MapPost/MapPut/MapDelete` (MinimalApi) or derive from service verb (Get→GET, Add/Create→POST, Set/Update→PUT, Delete→DELETE) |
| `targetRestContract.path` | REST path. For MinimalApi: extract from `AddRoute()`. For in-process: derive a RESTful resource path (see Discovery Phase 1). |
| `targetRestContract.queryParams` | Array of `{name, type, default?, optional}` objects. Present only for GET endpoints. |
| `targetRestContract.requestModel` | Object describing the request body fields. Present only for POST/PUT endpoints. |
| `targetRestContract.responseModel` | Name of the response class or object shape (e.g., `"ListPagedCatalogItemResponse"`) |
| `targetRestContract.auth` | `"jwt"` if the endpoint requires `[Authorize]` or JWT bearer, `"none"` otherwise |
| `targetRestContract.notes` | 1–2 sentences about how the legacy implementation maps to the REST target — especially where the mapping is non-obvious (price lookup, lazy basket creation, etc.) |
| `usedByUiFeatures` | Array of `feature_key` strings for UI features that call this endpoint. Derive by searching `docs/entry-points/ui-features/*/call-tree.json` for the service method name. Leave as `[]` if none found. |
| `notes` | Array of factual strings about non-obvious behavior: lazy creation, guard clauses, side effects, deliberate delays to remove. Omit the field if empty. |

### functional-spec.md

| Section | Rule |
|---|---|
| **Purpose** | 2–3 sentences: what operation this performs and which Angular component calls it |
| **Inputs** | Table: Name, Type, Optional, Default, Notes. For GET: query params. For POST/PUT: request body fields. For path params: include them with "path" in Notes. |
| **Outputs** | Filled-in JSON example of the response body. Include only the fields this endpoint actually returns — not the full entity. |
| **Acceptance criteria** | Gherkin `Scenario:` blocks. At minimum: happy path, edge case (filter/no results/empty), and any guard clause that returns an error. |
| **Business rules** | Numbered list of non-obvious rules: defaults, rounding, URL rewriting, guard clauses, idempotency semantics. |
| **Non-functional** | Read-only vs mutating, auth required, expected call frequency, any notable performance concerns. |

### call-tree.json

| Field | Rule |
|---|---|
| `entryPoint.method` | Fully qualified `Namespace.Class.Method` |
| `entryPoint.signature` | Full C# method signature including return type and parameter types |
| `entryPoint.file` | Relative to `legacy_dir` |
| `entryPoint.line` | Line where the method is defined |
| `legacyWebHandler` | Present only for in-process services. Same fields as `entryPoint` but refers to the Razor Page `OnPost`/`OnGet` that triggers the service. |
| `db` | Object `{"table": "Name", "op": "select|insert|update|delete|count"}`. Use an array when a single call does multiple ops. |
| `notes` | Only for non-obvious conditional logic (e.g., "Only when no basket exists") |
| Tracing depth | Follow until you reach a `db` node or an external leaf (email, event, external HTTP). Do not trace into EF Core internals (SaveChangesAsync, DbContext). |

### database-dependencies.json

Identical rules to `analyze-ui-feature`:

| Field | Rule |
|---|---|
| `key` | Lowercase kebab-case of `name` |
| `operations` | Only ops actually performed by this endpoint. Order: select before mutate. |
| `columns` | Only columns read or written. Check entity properties accessed in the call tree. |
| `locations` | Files where the table is accessed: Specification classes, entity classes, repository calls. |
| `notes` | 1–2 sentences on *how* this endpoint uses the table. |

---

## Exclusion Criteria

Do NOT include in `database-dependencies.json`:
- Tables accessed only by the shared site layout or by other features that happen to share a service
- EF Core metadata tables (`__EFMigrationsHistory`)

Do NOT add call tree nodes for:
- EF Core pipeline internals (`SaveChangesAsync`, `DbContext.Set<T>()`)
- DI container resolution
- AutoMapper `Map<>` calls (note AutoMapper usage in the entry point metadata but don't trace into it)
- `Results.Ok()`, `Results.NotFound()`, etc. (return value construction)

Do NOT set `legacyWebHandler` for MinimalApi endpoints — those are already HTTP exposed.

---

## Discovery Process

### Phase 1: Detect Entry Point Type and Read the File

1. Check `location`:
   - Contains `src/PublicApi/` → **MinimalApi.Endpoint**
   - Contains `src/Web/Services/` or `src/ApplicationCore/Services/` → **In-process service**
2. Read `{legacy_dir}/{location}`.
3. **MinimalApi.Endpoint:** Locate `AddRoute()` to extract the HTTP verb and path. Locate `HandleAsync()` to get the entry point method and its signature.
4. **In-process service:** Identify the specific service method this `key` refers to. (The `key` is the logical API name — match it to a method name: `add-item-to-basket` → `AddItemToBasket`.) Also search `src/Web/Pages/` for Razor Page handlers that call this method — that becomes `legacyWebHandler`.

**For MinimalApi — read companion files:**
- `{EndpointClassName}.{RequestClassName}.cs` — request type definition
- `{EndpointClassName}.{ResponseClassName}.cs` — response type definition
- `{EndpointClassName}.ClaimValue.cs` or similar if present

**For in-process service — read caller:**
- Read the Razor Page `.cshtml.cs` file that calls this service method (found via search or from `legacyWebHandler`)
- Note what the caller does before/after calling the service (e.g., price lookup, redirect)

**Derive `targetRestContract`:**
- MinimalApi: extract from `AddRoute()` → the `MapGet("api/catalog-items", ...)` call
- In-process: derive RESTful path using these rules:
  - Resource = entity the service operates on (Basket, CatalogItem, Order)
  - `GetXxx(id)` → `GET /api/{resources}/{id}`
  - `GetXxxForUser(username)` → `GET /api/{resources}/for-user/{buyerId}`
  - `AddXxx(userId, ...)` → `POST /api/{resources}/for-user/{buyerId}/items`
  - `SetXxx` / `UpdateXxx` → `PUT /api/{resources}/{id}/...`
  - `DeleteXxx` → `DELETE /api/{resources}/{id}`

---

### Phase 2: Trace the Call Tree

Starting from the entry point method (`HandleAsync` or the service method):

1. List every method called directly.
2. For each service method called, read the implementation file in `src/Web/Services/` or `src/ApplicationCore/Services/`.
3. For each Specification constructor call, read the spec file in `src/ApplicationCore/Specifications/` to confirm which DB table it targets.
4. For each repository call (`IRepository<T>` or `IReadRepository<T>`), record the table and op.
5. For each entity method call (e.g., `Basket.AddItem`, `Basket.RemoveEmptyItems`), read the entity file in `src/ApplicationCore/Entities/` to understand the mutation and note it.
6. Continue 3 levels deep, stopping at `db` nodes or external leaves.
7. Note cookie reads/writes encountered along the way (relevant for basket buyer resolution).

---

### Phase 3: Identify Database Dependencies

From the call tree:

1. Collect every distinct `db.table` across all nodes.
2. For each table:
   a. Collect all `op` values → `operations` array.
   b. Read the entity class in `src/ApplicationCore/Entities/` — list only properties actually accessed or mutated by this endpoint → `columns`.
   c. Collect all file paths where the table appears in the call tree → `locations`.
   d. Write 1–2 factual sentences on how this endpoint uses the table → `notes`.

---

### Phase 4: Determine `usedByUiFeatures`

Search existing `docs/entry-points/ui-features/*/call-tree.json` files. For each, check whether the `legacyEntryPoint` service method name appears anywhere in the call tree nodes. If yes, add that feature's `key` to the `usedByUiFeatures` array.

If `docs/entry-points/ui-features/` doesn't exist yet or contains no files, leave the array empty.

---

### Phase 5: Compose All Output Files

**Write `metadata.json`** — construct from discovery above. Write immediately (create `output_dir` if needed), overwrite if present.

**Write `call-tree.json`** — overwrite if present.

**Write `database-dependencies.json`** — overwrite if present.

**Write `functional-spec.md`:**
- Purpose: 2–3 sentences from the `[SwaggerOperation]` summary (MinimalApi) or from the service method's XML doc / inferred from the name.
- Inputs table: derive from request type fields (MinimalApi) or service method parameters (in-process). For in-process services, note which parameters come from the path, query string, or request body in the target REST design.
- Outputs: produce a filled-in JSON example, not a schema. Use realistic-looking placeholder values matching the response type's fields.
- Acceptance criteria: minimum one scenario per significant branch (happy path, empty/no-result, guard-clause failure, auth rejection if applicable).
- Business rules: non-obvious rules only — defaults, rounding, idempotency, lazy creation, guard clauses, anything marked with `Guard.Against.*`.
- Non-functional: whether read-only, auth required (check for `[Authorize]`, JWT registration in `Program.cs`), call frequency.

---

## Implementation Workflow

### Step 1: Parse Parameters
Extract `key`, `legacy_dir`, `location`, `output_dir` from `{{PROMPT}}`.

### Step 2: Detect Entry Point Type
Check `location` prefix: `src/PublicApi/` → MinimalApi; `src/Web/Services/` or `src/ApplicationCore/Services/` → in-process service.

### Step 3: Read Source Files
- For MinimalApi: read endpoint `.cs` + request/response companion files.
- For in-process: read service file + Razor Page caller.

### Step 4: Derive `targetRestContract`
Extract (MinimalApi) or derive (in-process) the HTTP method, path, params, response model, and auth requirement.

### Step 5: Write metadata.json
Write to `{output_dir}/metadata.json` — create folder if needed, overwrite if present.

### Step 6: Trace Call Tree
Follow handler → services → repositories → DB, 3 levels max.

### Step 7: Write call-tree.json
Write to `{output_dir}/call-tree.json` — overwrite if present.

### Step 8: Identify DB Dependencies
Collect tables from call tree; enrich with columns and locations.

### Step 9: Write database-dependencies.json
Write to `{output_dir}/database-dependencies.json` — overwrite if present.

### Step 10: Determine usedByUiFeatures
Search `docs/entry-points/ui-features/*/call-tree.json` for the service method name.

### Step 11: Write functional-spec.md
Write to `{output_dir}/functional-spec.md` — overwrite if present.

### Step 12: Report Summary
```
Key:              {key}
Entry point type: {MinimalApi.Endpoint | In-process service}
HTTP contract:    {METHOD} {path}
DB tables:        {list}
Gherkin blocks:   {count}
usedByUiFeatures: {list or "[]"}
Files written:    metadata.json, call-tree.json, database-dependencies.json, functional-spec.md
```

---

## Worked Examples

### Example 1: MinimalApi.Endpoint — `CatalogItemListPagedEndpoint`

**Input:**
```
key=list-catalog-items-paged
legacy_dir=/path/target_repo/source
location=src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs
output_dir=/path/docs/entry-points/api-endpoints/list-catalog-items-paged
```

**Entry point type:** MinimalApi (`src/PublicApi/`)

**Files read:**
- `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.cs`
- `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.ListPagedCatalogItemRequest.cs`
- `src/PublicApi/CatalogItemEndpoints/CatalogItemListPagedEndpoint.ListPagedCatalogItemResponse.cs`
- `src/ApplicationCore/Specifications/CatalogFilterSpecification.cs`
- `src/ApplicationCore/Specifications/CatalogFilterPaginatedSpecification.cs`

**targetRestContract:** `GET /api/catalog-items` (extracted from `app.MapGet("api/catalog-items", ...)`)

**Auth:** None (no `[Authorize]`, not registered with JWT policy in Program.cs)

**DB tables:** `Catalog` (select + count)

**Gherkin blocks:** 4 (no-filter, filter-by-brand, pageSize-0, pictureUri-rewriting)

**Notable business rule to capture:** Deliberate `Task.Delay(1000)` in HandleAsync — flag explicitly in business rules as "do NOT carry over to Java target."

---

### Example 2: In-process service — `BasketService.AddItemToBasket`

**Input:**
```
key=add-item-to-basket
legacy_dir=/path/target_repo/source
location=src/ApplicationCore/Services/BasketService.cs
output_dir=/path/docs/entry-points/api-endpoints/add-item-to-basket
```

**Entry point type:** In-process service (`src/ApplicationCore/Services/`)

**Files read:**
- `src/ApplicationCore/Services/BasketService.cs` — find `AddItemToBasket` method
- `src/Web/Pages/Basket/Index.cshtml.cs` — `OnPost` handler (legacyWebHandler)
- `src/ApplicationCore/Entities/BasketAggregate/Basket.cs` — `AddItem` entity method
- `src/ApplicationCore/Entities/BasketAggregate/BasketItem.cs` — quantity guard
- `src/ApplicationCore/Specifications/BasketWithItemsSpecification.cs`

**targetRestContract derived:**
- Verb: `AddItemToBasket` starts with "Add" → `POST`
- Resource: Basket → `/api/baskets/for-user/{buyerId}/items`
- Request body: `catalogItemId` (int), `quantity` (int, default 1)
- Price: not in request body — server looks up from Catalog (important business rule)

**legacyWebHandler:** `IndexModel.OnPost` (caller does the price lookup before calling the service — note this in `targetRestContract.notes`)

**DB tables:** `Baskets` (select + insert), `BasketItems` (insert + update)

**Gherkin blocks:** 4 (add to empty basket, increment existing, unknown catalog item, negative quantity guard)

---

### Example 3: MinimalApi.Endpoint with JWT — `AuthenticateEndpoint`

**Input:**
```
key=authenticate-user
legacy_dir=/path/target_repo/source
location=src/PublicApi/AuthEndpoints/AuthenticateEndpoint.cs
output_dir=/path/docs/entry-points/api-endpoints/authenticate-user
```

**Entry point type:** MinimalApi (`src/PublicApi/`)

**targetRestContract:** `POST /api/authenticate` (extracted from `MapPost`)

**Auth:** `"none"` — this endpoint IS the auth endpoint; it accepts credentials and returns a JWT. Subsequent endpoints use `[Authorize]`.

**Files read:** endpoint + `AuthenticateRequest.cs` + `AuthenticateResponse.cs` + `UserInfo.cs` + `ClaimValue.cs`

**DB tables:** ASP.NET Identity tables (`AspNetUsers` via `SignInManager` / `UserManager`). Document the Identity tables as the `database-dependencies.json` entries even though they are accessed through Identity abstractions.

**Non-functional note:** Returns a short-lived JWT. The Java target should issue a token with the same claim structure for compatibility with the Angular client.

---

## Important Notes

1. **Two entry point types, two discovery paths.** The `location` prefix determines everything — apply only the matching discovery path. Do not confuse `HandleAsync` (MinimalApi) with in-process service methods.

2. **`targetRestContract` is the deliverable for Java.** This is what the Spring Boot developer implements. Make it precise: exact HTTP verb, full resource path, every query param or request body field, the response model name. Vague contracts cause rework.

3. **In-process services need a derived REST path.** When `location` points to a service file, you must design the REST path yourself using the resource-oriented rules in Phase 1. The Java developer has no other reference for the target route.

4. **Price lookup stays server-side.** The basket service endpoints in legacy receive a price parameter from the Razor Page caller. The REST target must look up the price server-side. Always capture this in `targetRestContract.notes` and in the business rules section.

5. **Deliberate delays are legacy artifacts.** `CatalogItemListPagedEndpoint` contains `await Task.Delay(1000)`. Flag any such artificial delays in the business rules section with an explicit "do NOT carry over" note.

6. **AutoMapper.** `CatalogItemListPagedEndpoint` uses AutoMapper (`_mapper.Map<CatalogItemDto>`). Note its presence in the call tree as a leaf node — do not trace into it. Mention in the functional spec that the Java target should map entity → DTO in the same way.

7. **`usedByUiFeatures` may be empty.** If `docs/entry-points/ui-features/` doesn't exist yet, write `"usedByUiFeatures": []` — the workflow will populate it in a later pass.

8. **Idempotency.** All four output files overwrite cleanly on each run. Re-running with the same inputs must produce identical output.

9. **`db.op` for Identity tables.** ASP.NET Identity operations go through `UserManager`/`SignInManager` — you cannot read the raw SQL, but you can infer: `FindByNameAsync` → `select`, `CheckPasswordSignInAsync` → `select`. Document as `{"table": "AspNetUsers", "op": "select"}`.

10. **`legacyLocation` line number.** Always include the line number of the method *definition* (not the call site). If you cannot determine it precisely, omit the `:N` suffix rather than guessing.
