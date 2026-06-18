# Analyze UI Feature

You are tasked with producing a detailed analysis of a single UI feature from the eShopOnWeb ASP.NET Core 8.0 application. The output feeds a modernization effort targeting **Angular 19 + Spring Boot 3.5 (Java 25)** — every artifact you write must contain enough technical detail for a Java developer to re-implement the feature in that stack without consulting the original source.

This is a **discover-phase** command. It reads the legacy eShopOnWeb source and writes structured artifacts to `docs/entry-points/ui-features/{feature_key}/`.

---

## User Query
{{PROMPT}}

---

## Command Syntax

```
feature_key=<key>  inventory_path=<abs-path>  source_root=<abs-path>
```

| Argument | Description |
|---|---|
| `feature_key` | The `key` value from the inventory entry (e.g., `basket-view-page`) |
| `inventory_path` | Absolute path to the `inventory.json` file that contains this feature |
| `source_root` | Absolute path to the eShopOnWeb source root (e.g., `.../target_repo/source`) |

**Examples:**

```
feature_key=basket-view-page
inventory_path=/abs/path/docs/entry-points/ui-pages/basket-index/inventory.json
source_root=/abs/path/target_repo/source
```

```
feature_key=homepage-catalog-list
inventory_path=/abs/path/docs/entry-points/ui-pages/home/inventory.json
source_root=/abs/path/target_repo/source
```

```
feature_key=admin-catalog-item-list
inventory_path=/abs/path/docs/entry-points/ui-pages/admin-catalog/inventory.json
source_root=/abs/path/target_repo/source
```

---

## Output

All files are written to:

```
docs/entry-points/ui-features/{feature_key}/
├── metadata.json
├── functional-spec.md
├── call-tree.json
└── database-dependencies.json
```

### `metadata.json` — filled-in example

```json
{
  "key": "basket-view-page",
  "name": "Basket view page",
  "type": "ui-feature",
  "elementType": "ui-page",
  "uri": "/Basket",
  "location": "src/Web/Pages/Basket/Index.cshtml",
  "codeBehind": "src/Web/Pages/Basket/Index.cshtml.cs",
  "domain": "basket",
  "notes": [
    "Handles three operations on one page: view (OnGet), add-item (OnPost), update-quantities (OnPostUpdate).",
    "Anonymous users are tracked by a GUID stored in a cookie; authenticated users use their username.",
    "POST from catalog's [ADD TO BASKET] lands here as OnPost with CatalogItemViewModel."
  ]
}
```

### `functional-spec.md` — filled-in example

```markdown
# Functional spec — Basket view page

**Key:** `basket-view-page`
**URL:** `GET /Basket` (plus `POST /Basket` and `POST /Basket?handler=Update`)
**Legacy source:** `src/Web/Pages/Basket/Index.cshtml` + `Index.cshtml.cs`

## Purpose

Shows the shopper the items currently in their basket, lets them adjust quantities,
and provides the jumping-off point to checkout. Also serves as the HTTP target for
"Add to basket" posts from the catalog.

## Functional behavior

### OnGet — view

1. Resolves basket owner (cookie or auth username).
2. Calls `IBasketViewModelService.GetOrCreateBasketForUser(username)`.
3. Renders `BasketViewModel` into the page.

### OnPost — add item

1. Accepts a `CatalogItemViewModel` posted from catalog.
2. If `productDetails.Id` is null, redirects to `/Index`.
3. Loads current price; calls `IBasketService.AddItemToBasket(username, productId, price)`.
4. Redirects back to `/Basket`.

## Acceptance criteria (Gherkin)

\`\`\`
Scenario: First-time anonymous visit creates cookie + empty basket
  Given the shopper has never visited the site
  When they navigate to "/Basket"
  Then a new GUID cookie "eShop" is set on the response
  And the page renders "Basket is empty."
\`\`\`

## UI elements

| Element | Kind | Source ref |
| --- | --- | --- |
| Empty-state message | text | `Index.cshtml:83` |
| Items table | loop over `Model.BasketModel.Items` | `Index.cshtml:27-47` |
| Qty input per item | `<input type="number" min="0">` | `Index.cshtml:39` |
| Update button | submit (handler=Update) | `Index.cshtml:70-73` |
| Checkout link | link to `/Basket/Checkout` | `Index.cshtml:74` |
```

### `call-tree.json` — filled-in example

```json
{
  "handlers": [
    {
      "entryPoint": {
        "method": "Microsoft.eShopWeb.Web.Pages.Basket.IndexModel.OnGet",
        "file": "src/Web/Pages/Basket/Index.cshtml.cs",
        "line": 28
      },
      "calls": [
        {
          "method": "IndexModel.GetOrSetBasketCookieAndUserName",
          "file": "src/Web/Pages/Basket/Index.cshtml.cs",
          "line": 68,
          "reads": ["Request.HttpContext.User.Identity", "Request.Cookies['eShop']"],
          "writes": ["Response.Cookies['eShop']"]
        },
        {
          "method": "IBasketViewModelService.GetOrCreateBasketForUser",
          "file": "src/Web/Services/BasketViewModelService.cs",
          "line": 28,
          "calls": [
            {
              "method": "IRepository<Basket>.FirstOrDefaultAsync(BasketWithItemsSpecification)",
              "db": {"table": "Baskets", "op": "select"}
            },
            {
              "method": "IRepository<Basket>.AddAsync",
              "db": {"table": "Baskets", "op": "insert"},
              "notes": "Only when no basket exists for the user."
            }
          ]
        }
      ]
    }
  ]
}
```

For pages with a single handler (no POST), use `"entryPoint"` + `"calls"` at the top level (no `"handlers"` array):

```json
{
  "entryPoint": {
    "method": "Microsoft.eShopWeb.Web.Pages.IndexModel.OnGet",
    "file": "src/Web/Pages/Index.cshtml.cs",
    "line": 18
  },
  "calls": [...]
}
```

### `database-dependencies.json` — filled-in example

```json
[
  {
    "type": "table",
    "name": "Baskets",
    "key": "baskets",
    "operations": ["select", "insert"],
    "columns": ["Id", "BuyerId"],
    "locations": [
      "src/Infrastructure/Data/Migrations/20201202111507_InitialModel.cs",
      "src/ApplicationCore/Specifications/BasketWithItemsSpecification.cs"
    ],
    "notes": [
      "Looked up by BuyerId (username or anon GUID) via BasketWithItemsSpecification.",
      "Row inserted lazily when a user without an existing basket first visits or adds an item."
    ]
  }
]
```

---

## Field Rules

### metadata.json

| Field | Rule |
|---|---|
| `key` | Copied verbatim from the matching inventory entry |
| `name` | Copied verbatim from the inventory entry |
| `type` | Always `"ui-feature"` |
| `elementType` | Copied from inventory entry (`ui-page`, `ui-panel`, etc.) |
| `uri` | The HTTP path. For Razor Pages derive from folder path or `@page` route. For MVC derive from `[Route]` + action name. |
| `location` | Relative to `source_root`. For Razor Pages: `.cshtml` file. For Blazor: `.razor` file. For MVC: the controller `.cs` file. |
| `codeBehind` | `.cshtml.cs` or `.razor.cs` if it exists; omit the field if none. |
| `domain` | Copied from inventory entry |
| `notes` | 2–4 factual strings that would not be obvious from the file name alone. Focus on non-obvious behaviors (cookie handling, dual-path POST handlers, anonymous vs authenticated routing, etc.) |

### functional-spec.md

| Section | Rule |
|---|---|
| **Purpose** | 2–3 sentences: what the user does here, why it matters in the shopping flow |
| **Functional behavior** | One sub-section per handler (OnGet, OnPost, OnPostUpdate, etc.) or per route action. Numbered steps. Reference method names. |
| **Acceptance criteria** | Gherkin `Scenario:` blocks. Minimum one per handler. Cover the happy path + at least one edge case (empty state, validation failure, auth gate). |
| **UI elements** | A table with columns: Element, Kind (text/link/img/form/loop/partial), Source ref (`File.cshtml:N`). List every visible element that has user-facing behaviour. Omit purely structural wrapper divs. |
| **Out of scope** | Optional section. Use it when adjacent features (e.g., site header basket count) are visible in the same template but belong to a different feature key. |

### call-tree.json

| Field | Rule |
|---|---|
| `method` | Fully qualified C# method signature — namespace.Class.Method for external calls, Class.Method for page-local helpers |
| `file` | Relative to `source_root` |
| `line` | Integer. Use the line where the method is defined (not the call site). Omit if line cannot be determined. |
| `db` | Object `{"table": "TableName", "op": "select\|insert\|update\|delete\|select count"}`. Use an array when a single call performs multiple ops. |
| `notes` | Optional string — only for non-obvious conditional logic (e.g., "Only when no basket exists"). |
| `reads` / `writes` | Optional arrays for cookie or session access. Document HTTP context side effects that won't be obvious from the method signature. |

Trace calls until you reach either:
- A `db` node (repository call hitting a table), or
- A leaf method with no further calls into application code (utility/external service)

### database-dependencies.json

| Field | Rule |
|---|---|
| `key` | Lowercase kebab-case version of `name` (e.g., `"BasketItems"` → `"basket-items"`) |
| `operations` | Array subset of `["select", "insert", "update", "delete", "select count"]`. Order: select before mutate. |
| `columns` | Columns actually read or written by this feature. Not all columns in the table — only those touched. |
| `locations` | Files where this table is accessed: migration defining it, specification/repository accessing it, entity class. |
| `notes` | 1–2 sentences per entry. Focus on *how* this feature uses the table (e.g., "Rows deleted lazily via Basket.RemoveEmptyItems when quantity reaches zero"). |

---

## Exclusion Criteria

Do NOT add entries to `database-dependencies.json` for:
- Tables used by the shared site layout (e.g., `AspNetUsers` queried by the header login widget) unless the feature itself queries them
- Tables touched only in admin-side features referenced from this page

Do NOT add nodes to `call-tree.json` for:
- EF Core internals (SaveChangesAsync, DbContext itself)
- DI container resolution or middleware pipeline
- ViewResult / PageResult construction (the return value, not the logic)

Do NOT list UI elements in `functional-spec.md` for:
- Shared layout scaffolding (`_Layout.cshtml`, `MainLayout.razor`)
- Structural wrapper divs with no user-facing behaviour
- SEO meta tags

---

## Discovery Process

### Phase 1: Locate the Feature in Inventory

1. Read `inventory_path` — it is a JSON array of inventory entries.
2. Find the entry whose `"key"` matches `feature_key`. If not found, stop and report the error.
3. Extract: `name`, `elementType`, `location`, `uri`, `domain`, `notes` from the entry.
4. Determine the **page type** from `location`:
   - Path under `src/Web/Pages/` with `.cshtml` extension → **Razor Page**
   - Path ending in `.razor` → **Blazor component**
   - Path containing `Controller.cs` → **MVC Controller**

**Output:** Populated `metadata.json` — write this file immediately before continuing.

---

### Phase 2: Read Source Files

#### Razor Page (`*.cshtml` + `*.cshtml.cs`)

1. Read `{source_root}/{location}` — the `.cshtml` view template.
2. Read `{source_root}/{location}.cs` — the PageModel code-behind.
3. Identify all `@page` route, `@model`, injected services (`[Inject]` or constructor params in PageModel), and `[BindProperty]` fields.
4. Identify all handler methods: `OnGet`, `OnPost`, `OnPost{Handler}`, `OnGetAsync`, etc.
5. For each `<partial name="..." />` or `<partial tag-helper>` in the view, read that partial file from `src/Web/Pages/Shared/` or adjacent folder.
6. Note every `asp-page-handler`, `asp-action`, `asp-controller`, and `asp-route-*` on form and link elements.

#### Blazor Component (`*.razor` + optional `*.razor.cs`)

1. Read `{source_root}/{location}` — the `.razor` template.
2. If a `.razor.cs` code-behind exists, read it too.
3. Identify `@inject` services, `@code` block, `@page` route directive.
4. Identify `<EditForm>`, `OnValidSubmit`, `@onclick` handlers.
5. Follow `@ref` and `<ChildComponent>` imports one level deep.

#### MVC Controller + View (`*Controller.cs` + `*.cshtml`)

1. Read the controller file at `{source_root}/{location}`.
2. Identify the action method(s) relevant to `feature_key` (match by action name in `uri`).
3. Read the corresponding Razor view file from `src/Web/Views/{ControllerName}/{ActionName}.cshtml`.
4. Identify `[Authorize]`, `[HttpGet]`, `[HttpPost]`, route parameters, and view model type.

---

### Phase 3: Trace the Call Tree

For each handler method identified in Phase 2:

1. List every service method called directly from the handler.
2. For each service method, read the service implementation file (search `src/Web/Services/` and `src/ApplicationCore/Services/`).
3. For each repository call (any method on `IRepository<T>`, `IReadRepository<T>`, or `IAsyncRepository<T>`), record the Specification class passed and the DB table it targets.
4. Follow nested service calls up to 3 levels deep, stopping at a `db` node or a leaf.
5. Record cookie and session reads/writes encountered along the way.

**Finding files:** Repository implementations live in `src/Infrastructure/Data/`. Specification classes live in `src/ApplicationCore/Specifications/`. Entity classes live in `src/ApplicationCore/Entities/`.

**DB table determination:** The Specification class name usually implies the table (e.g., `BasketWithItemsSpecification` → `Baskets`). Confirm by checking the entity class the specification is typed against.

**Call tree JSON template per handler:**

```json
{
  "entryPoint": {
    "method": "{Namespace}.{PageModel}.{HandlerMethod}",
    "file": "{location relative to source_root}",
    "line": {line number}
  },
  "calls": [
    {
      "method": "{IServiceInterface}.{MethodName}",
      "file": "{service impl file}",
      "line": {line},
      "calls": [
        {
          "method": "{IRepository<Entity>}.{RepoMethod}({SpecificationClass})",
          "db": {"table": "{TableName}", "op": "{op}"}
        }
      ]
    }
  ]
}
```

For pages with multiple handlers, wrap all handler objects in a `"handlers"` array.

---

### Phase 4: Identify Database Dependencies

From the completed call tree:

1. Collect every distinct `db.table` value across all handlers.
2. For each table:
   a. Collect all distinct `op` values from its nodes → `operations` array.
   b. Find the entity class for this table in `src/ApplicationCore/Entities/` — extract the property names that are read or mutated by this feature → `columns` array.
   c. Collect all file paths where this table appears in the call tree → `locations` array. Add the migration file defining the table schema if you can identify it from `src/Infrastructure/Data/Migrations/`.
   d. Write 1–2 factual sentences about *how* this feature uses the table → `notes` array.

**DB dependency JSON template:**

```json
{
  "type": "table",
  "name": "{PascalCase table name}",
  "key": "{kebab-case table name}",
  "operations": ["{op1}", "{op2}"],
  "columns": ["{Col1}", "{Col2}"],
  "locations": ["{file1}", "{file2}"],
  "notes": ["{factual note about usage}"]
}
```

---

### Phase 5: Compose the Functional Spec

Using the source you have read, produce `functional-spec.md` with the following sections:

**Header block:**
```
# Functional spec — {name}

**Key:** `{feature_key}`
**URL:** `{uri}` (list all HTTP methods if more than one handler)
**Legacy source:** `{location}` + `{codeBehind if present}`
```

**Purpose:** 2–3 sentences describing the user goal served by this page.

**Functional behavior:** One sub-section per handler (`### OnGet`, `### OnPost`, etc.). Numbered steps. Reference real method names. If the handler redirects, name the destination. If it checks auth or cookies, describe that logic explicitly.

**Acceptance criteria:** Gherkin `Scenario:` blocks. Rules:
- At minimum: one happy path scenario per handler.
- Always include: the empty-state scenario if the page shows a list.
- Always include: the auth/redirect scenario if `[Authorize]` is present.
- Always include: the error/invalid-input scenario if the page accepts a POST.

**UI elements table:** Columns — Element | Kind | Source ref. Include:
- All form inputs and submit buttons
- All navigation links with specific destinations
- All loops rendering lists of items
- All conditionally rendered blocks (`@if`, `asp-if`, Blazor `@if`)
- All partials included by name

**Out of scope** (optional): List features visible in the same template that belong to other feature keys (e.g., the site-wide header basket count, the shared navigation rail).

---

## Implementation Workflow

### Step 1: Parse Parameters
Read `feature_key`, `inventory_path`, `source_root` from `{{PROMPT}}`.

### Step 2: Locate Feature Entry
Read `inventory_path` (JSON array). Find entry matching `feature_key`. If missing, report error and stop.

### Step 3: Write metadata.json
Construct from the inventory entry. Write to `docs/entry-points/ui-features/{feature_key}/metadata.json` — create the folder if needed, overwrite if present.

### Step 4: Read Source Files
Based on page type detected from `location`:
- Razor Page → read `.cshtml` + `.cshtml.cs` + referenced partials
- Blazor → read `.razor` + optional `.razor.cs` + child components (1 level)
- MVC → read controller `.cs` + view `.cshtml`

### Step 5: Trace Call Tree
Follow handler methods → services → repositories → DB. Build the call tree structure in memory.

### Step 6: Write call-tree.json
Write to `docs/entry-points/ui-features/{feature_key}/call-tree.json` — overwrite if present.

### Step 7: Identify DB Dependencies
From the call tree, collect all tables, their operations, columns, and locations.

### Step 8: Write database-dependencies.json
Write to `docs/entry-points/ui-features/{feature_key}/database-dependencies.json` — overwrite if present.

### Step 9: Write functional-spec.md
Compose all sections (Purpose, Functional behavior, Gherkin, UI elements). Write to `docs/entry-points/ui-features/{feature_key}/functional-spec.md` — overwrite if present.

### Step 10: Report Summary
Output a brief summary:
```
Feature key:    {feature_key}
Page type:      {Razor Page | Blazor | MVC}
Handlers:       {list, e.g. OnGet, OnPost, OnPostUpdate}
DB tables:      {list, e.g. Baskets, BasketItems, Catalog}
Gherkin blocks: {count}
UI elements:    {count}
Output folder:  docs/entry-points/ui-features/{feature_key}/
Files written:  metadata.json, call-tree.json, database-dependencies.json, functional-spec.md
```

---

## Worked Examples

### Example 1: Razor Page with multiple handlers — `basket-view-page`

**Input:**
```
feature_key=basket-view-page
inventory_path=/path/docs/entry-points/ui-pages/basket-index/inventory.json
source_root=/path/target_repo/source
```

**Files read:**
- `src/Web/Pages/Basket/Index.cshtml`
- `src/Web/Pages/Basket/Index.cshtml.cs`
- `src/Web/Services/BasketViewModelService.cs`
- `src/ApplicationCore/Services/BasketService.cs`
- `src/ApplicationCore/Entities/BasketAggregate/Basket.cs`
- `src/ApplicationCore/Entities/BasketAggregate/BasketItem.cs`
- `src/ApplicationCore/Specifications/BasketWithItemsSpecification.cs`

**call-tree.json handlers:** `OnGet`, `OnPost`, `OnPostUpdate`
**database-dependencies.json tables:** `Baskets` (select/insert), `BasketItems` (select/insert/update/delete), `Catalog` (select)
**Gherkin scenarios:** 5 (anonymous visit, view with items, add item, update quantities, checkout link)
**UI elements:** 9 (empty message, items table, qty input, total row, Continue Shopping links ×2, Update button, Checkout link, hero banner)

---

### Example 2: Razor Page with filter form — `homepage-catalog-list`

**Input:**
```
feature_key=homepage-catalog-list
inventory_path=/path/docs/entry-points/ui-pages/home/inventory.json
source_root=/path/target_repo/source
```

**Files read:**
- `src/Web/Pages/Index.cshtml`
- `src/Web/Pages/Index.cshtml.cs`
- `src/Web/Pages/Shared/_product.cshtml`
- `src/Web/Pages/Shared/_pagination.cshtml`
- `src/Web/Services/CatalogViewModelService.cs`
- `src/ApplicationCore/Specifications/CatalogFilterPaginatedSpecification.cs`
- `src/ApplicationCore/Specifications/CatalogFilterSpecification.cs`

**call-tree.json:** Single `OnGet` handler tree
**database-dependencies.json tables:** `Catalog` (select, select count), `CatalogBrands` (select), `CatalogTypes` (select)
**Gherkin scenarios:** 4 (no filter, brand filter, page 2, empty result)
**UI elements:** 7 (hero, brand select, type select, submit button, pagination ×2, product tile grid)

**Note on partials:** `_product.cshtml` renders the individual product tile including the `ADD TO BASKET` button. That button POSTs to `/Basket` — this is out of scope for this spec (belongs to `basket-view-page`). Document the element row but add an out-of-scope note.

---

### Example 3: Blazor admin component — `admin-catalog-item-list`

**Input:**
```
feature_key=admin-catalog-item-list
inventory_path=/path/docs/entry-points/ui-pages/admin-catalog/inventory.json
source_root=/path/target_repo/source
```

**Page type detection:** `location` ends in `.razor` → Blazor component
**Files read:** `.razor` file, `.razor.cs` code-behind if present, `@inject`-ed service interfaces
**call-tree.json:** One or more `@onclick`/`OnValidSubmit` entry points, each tracing to repository calls
**Note:** Blazor components call services directly in `@code` blocks — trace `@inject`-ed services rather than PageModel handlers.

---

## Important Notes

1. **Three page types, three discovery paths.** Razor Pages, Blazor components, and MVC controllers each have distinct handler/service patterns. Detect the page type first (Phase 1) and apply only the matching discovery path in Phase 2.

2. **Trace depth: stop at DB, not at the repository interface.** Follow calls through service classes and into Specification constructors until you reach an explicit `db` node. Do not stop at the interface boundary — read the implementation.

3. **Multiple handlers = `"handlers"` array.** Use the flat (`"entryPoint"` + `"calls"`) shape only for single-handler pages. Use `"handlers": [...]` whenever there is more than one entry point on the page.

4. **Columns = touched columns only.** Do not list all columns in the EF entity. Only list the columns actually read or written by this feature's handlers. Check the Specification `Include()` chains and the entity mutation methods.

5. **Partials scope.** Read partials that are included in the page and extract their UI elements into the `functional-spec.md` table. However, if a partial implements a feature with its own `feature_key` (e.g., a checkout widget), mark it as out of scope rather than duplicating the analysis.

6. **Idempotency.** All four output files are overwritten cleanly on each run. A second run with the same inputs must produce identical output.

7. **Source refs use relative paths.** In the UI elements table, `Source ref` values are relative to `source_root` (e.g., `Index.cshtml:39`, not absolute paths).

8. **Gherkin covers edge cases that matter for Java.** The Gherkin scenarios will be consumed by the Spring Boot developer. Always cover: cookie/session creation (anonymous user), auth redirect (if `[Authorize]` is present), empty-list state, and validation failure on POST. These are the cases most likely to be missed when reimplementing.

9. **`javaEquivalent` is in inventory, not here.** This command does not add `javaEquivalent` to any output. That field lives in `inventory.json`. The Java developer uses `call-tree.json` and `functional-spec.md` together to understand the mapping.

10. **No screenshots directory.** Unlike the NW Passage reference command, this command does not create a `screenshots/` folder. If screenshots already exist in the output folder, do not delete them.
