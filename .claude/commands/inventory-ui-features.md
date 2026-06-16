# Inventory UI Features

You are tasked with creating a factual inventory of UI features for one page from the **eShopOnWeb** ASP.NET Core 8 application. This inventory is an input to a modernization effort targeting **Angular 19 + Spring Boot 3.5 (Java 25)** — every entry must capture enough behavioural detail for a developer to rebuild the feature in that stack without reading the original source.

This command analyses the entry-point file, its partials, modals, and code-behind, then writes a flat JSON inventory capturing the page, its panels/forms, and user-facing actions.

## User Query
{{PROMPT}}

## Command Syntax

```
file:<relative-path-from-source-root>
page_key:<semantic-key>
domain:<business-domain>
```

**`file`** — Path to the entry-point file, relative to `./target_repo/source/`.

**`page_key`** — The semantic base key for this page (kebab-case, business-oriented). All child keys are derived from this.

**`domain`** — Business domain label (e.g., `catalog`, `basket`, `orders`, `admin`, `account`, `identity`).

**Examples:**
```
file:src/Web/Pages/Index.cshtml
page_key:homepage-catalog-list
domain:catalog
```
```
file:src/BlazorAdmin/Pages/CatalogItemPage/List.razor
page_key:admin-catalog-item-list
domain:catalog
```
```
file:src/Web/Controllers/OrderController.cs
page_key:order
domain:orders
```

---

## Output

Each page gets its own folder:
`./docs/entry-points/ui-pages/{page_key}/inventory.json`

**Structure:** A flat JSON array — the page entry first, then all panels/forms, then all actions — linked by keys.

**Established format** (matches `docs/entry-points/ui-pages/home/inventory.json`, with the addition of `javaEquivalent`):

```json
[
  {
    "key": "page-key",
    "name": "Human Readable Name",
    "elementType": "ui-page",
    "location": "src/Web/Pages/Example.cshtml",
    "uri": "/example",
    "domain": "catalog",
    "notes": [
      "Razor Page. PageModel: ExampleModel.",
      "Auth: public.",
      "Loads data via ICatalogViewModelService.GetCatalogItems.",
      "Query params: BrandFilterApplied, TypesFilterApplied, pageId."
    ],
    "javaEquivalent": "Angular 19 page component at /example; Angular service fetches data via HttpClient from Spring @RestController; service maps to Spring @Service bean"
  },
  {
    "key": "page-key-filter-form",
    "name": "Filter Form",
    "elementType": "ui-form",
    "location": "src/Web/Pages/Example.cshtml:10-23",
    "parentKey": "page-key",
    "domain": "catalog",
    "notes": [
      "GET form. Submits brand and type filter selections to the same page route.",
      "Fields: BrandFilterApplied (select), TypesFilterApplied (select).",
      "No server-side validation — all values are integer IDs from preloaded lists."
    ],
    "javaEquivalent": "Angular reactive form; on submit calls Angular service GET with ?brandId=&typeId= query params to Spring @RestController"
  },
  {
    "key": "page-key-catalog-grid",
    "name": "Catalog Product Grid",
    "elementType": "ui-panel",
    "location": "src/Web/Pages/Example.cshtml:24-45",
    "parentKey": "page-key",
    "domain": "catalog",
    "notes": [
      "Renders one tile per CatalogItem via _product.cshtml partial.",
      "Empty-state: 'THERE ARE NO RESULTS THAT MATCH YOUR SEARCH'.",
      "Paginated — items bounded by PaginationInfo.ItemsPerPage."
    ],
    "javaEquivalent": "Angular 19 component with @for loop over catalogItems from Angular service response; empty-state via @if"
  },
  {
    "key": "page-key-add-to-basket",
    "name": "Add to Basket Button",
    "elementType": "ui-action",
    "location": "src/Web/Pages/Shared/_product.cshtml:12",
    "parentKey": "page-key-catalog-grid",
    "domain": "catalog",
    "actionType": "form-post",
    "notes": [
      "POST to /Basket (handler: OnPost). Sends CatalogItemId.",
      "Price is resolved server-side — client only sends the item ID.",
      "Redirects back to the basket on success."
    ],
    "javaEquivalent": "Angular (click) handler calls Angular basket service; HTTP POST to Spring @RestController /api/basket; price looked up server-side"
  }
]
```

### Element Types

| elementType | When to use |
|-------------|-------------|
| `ui-page` | The page itself (Razor Page, Blazor page, MVC view) |
| `ui-form` | `<form>` (Razor), `<EditForm>` (Blazor), or multi-step form section |
| `ui-panel` | Data table, partial view, modal dialog component, display section |
| `ui-action` | Button/link with user-facing behaviour (submit, open modal, navigate, delete) |

### Action Types

| actionType | When to use |
|------------|-------------|
| `form-post` | Form submission triggering an `OnPost*` handler or `OnValidSubmit` |
| `modal-open` | Opens a Blazor modal component (`Component.Open(id)`) |
| `modal-confirm` | Opens a confirmation/delete modal |
| `navigation` | `asp-page`, `asp-controller/action`, `NavigateTo()` or plain `href` link with user intent |
| `api-call` | Direct service call without modal (delete, toggle, refresh) |
| `filter` | GET-form submission to filter/search page data |
| `other` | Anything not matching above — use sparingly |

### Field Rules

- `key` — `{page_key}-{descriptor}`, all lowercase kebab-case
- `name` — Short human-readable label (3–6 words), title case
- `location` — Relative to `./target_repo/source/`. Include `:start-end` for panels, `:N` for single-line actions
- `parentKey` — For panels: the page key. For actions: the panel or form they appear inside
- `notes` — Array of concise factual strings. Capture: data shown/posted, service delegation, auth, empty states, redirect targets, validation rules, conditional display logic
- `javaEquivalent` — **Required on every entry.** One sentence. Name the Angular construct for UI elements and the Spring annotation/class for backend logic. No Thymeleaf — the target stack is Angular 19 SPA + Spring Boot 3.5 REST. See the reference section below.

---

## Exclusion Criteria

Do **not** create inventory entries for:

- **Layout scaffolding:** `_Layout.cshtml`, `MainLayout.razor`, `NavMenu.razor`, `_ViewStart.cshtml`, `_Imports.razor`
- **Utility components:** `Spinner.razor`, `Toast.razor`, `RedirectToLogin.razor`, `App.razor`
- **Validation scripts partials:** `_ValidationScriptsPartial.cshtml`
- **Error/Privacy pages** unless explicitly passed as the `file` argument
- **Static hero/banner sections** with no data or user interaction
- **Structural-only navigation links** — capture only actions that carry user intent (e.g. `[Pay Now]`, `[Update]`), not breadcrumbs or `[Back]` links

---

## Discovery Process

### Phase 1: Detect Page Type and Create `ui-page` Entry

#### Razor Page (`*.cshtml` in `Pages/`)
1. Read `{file}.cshtml` — extract `@page` route (if present), `ViewData["Title"]`, `@model` type
2. Read `{file}.cshtml.cs` code-behind — extract `OnGet`/`OnPost*` handlers, `[Authorize]`, injected services
3. Infer URI from folder path if no explicit `@page` route (e.g. `Pages/Basket/Checkout.cshtml` → `/basket/checkout`)

```json
{
  "key": "{page_key}",
  "name": "{title from ViewData or H1}",
  "elementType": "ui-page",
  "location": "src/Web/Pages/{path}.cshtml",
  "uri": "/{route}",
  "domain": "{domain}",
  "notes": [
    "Razor Page. PageModel: {ModelClass}.",
    "Auth: {[Authorize] annotation or 'public'}.",
    "Loads data via {service or MediatR handler}.",
    "Query params: {list any, or omit if none}."
  ],
  "javaEquivalent": "Angular 19 page component at {route}; Angular service fetches data via HttpClient from Spring @RestController; {service} becomes Spring @Service bean"
}
```

#### Blazor Component (`*.razor` with `@page`)
1. Read `{file}.razor` — extract `@page` route, `[Authorize]` attribute, component references (`<Edit @ref="...">` etc.)
2. Check for `{file}.razor.cs` code-behind if present

Note: Blazor WebAssembly pages call `PublicApi` REST endpoints. In the target stack they become **Angular 19 components** consuming **Spring Boot 3.5 `@RestController`** endpoints.

```json
{
  "key": "{page_key}",
  "name": "{PageTitle or H1}",
  "elementType": "ui-page",
  "location": "src/BlazorAdmin/Pages/{path}.razor",
  "uri": "{@page route}",
  "domain": "{domain}",
  "notes": [
    "Blazor WebAssembly page. Calls PublicApi REST endpoints.",
    "Auth: {role requirement or 'public'}.",
    "Loads data via {service calls in OnInitializedAsync or similar}."
  ],
  "javaEquivalent": "Angular 19 page component at {route}; data loaded via Angular service (HttpClient) from Spring @RestController; route guarded by Angular AuthGuard requiring {role} via Spring Security"
}
```

#### MVC Controller (`*Controller.cs`)
Create one `ui-page` entry per `[HttpGet]` action that returns `View()`.

1. Read the controller — find each GET action, its route, auth, MediatR/service call
2. Find the corresponding view at `src/Web/Views/{Controller}/{Action}.cshtml`

```json
{
  "key": "{page_key}-{action-kebab}",
  "name": "{Action Name}",
  "elementType": "ui-page",
  "location": "src/Web/Views/{Controller}/{Action}.cshtml",
  "uri": "/{controller}/{action}",
  "domain": "{domain}",
  "notes": [
    "MVC View. Controller: {ControllerName}.{ActionName}.",
    "Auth: {[Authorize] details}.",
    "Loads data via {handler or service}."
  ],
  "javaEquivalent": "Angular 19 page component at /{controller}/{action}; data fetched from Spring Boot @RestController @GetMapping; {service} becomes Spring @Service"
}
```

---

### Phase 2: Extract Panel and Form Entries

#### ui-form — Forms

- Razor: `<form method="get">` (filter) or `<form method="post">` / `<form asp-page="...">` (mutation)
- Blazor: `<EditForm Model="...">`

```json
{
  "key": "{page_key}-{descriptor}-form",
  "name": "{Descriptor} Form",
  "elementType": "ui-form",
  "location": "{file}:{start-end}",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "{GET or POST}. Submits to {handler or route}.",
    "Fields: {list key input fields}.",
    "Validation: {DataAnnotationsValidator / server-side / none}.",
    "On success: {redirect target or response}."
  ],
  "javaEquivalent": "Angular 19 reactive form (FormGroup/FormControl); on submit calls Angular service HTTP {method} to Spring @RestController; @Valid on @RequestBody DTO with Jakarta Bean Validation"
}
```

#### ui-panel — Data Tables

Look for `<table>` or `@foreach` over a collection rendering repeated rows.

```json
{
  "key": "{page_key}-{descriptor}-table",
  "name": "{Descriptor} Table",
  "elementType": "ui-panel",
  "location": "{file}:{start-end}",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "Renders each {entity} from {Model.Collection}.",
    "Columns: {list column headers}.",
    "Empty-state: '{message if present}'.",
    "Row-level actions: {list if any}."
  ],
  "javaEquivalent": "Angular 19 component with @for (or *ngFor) over {collection} loaded via Angular service from Spring @RestController"
}
```

#### ui-panel — Partial Views

Look for `<partial name="...">` tags. Read the partial file and create child entries from its content.

```json
{
  "key": "{page_key}-{partial-name}",
  "name": "{Partial Purpose}",
  "elementType": "ui-panel",
  "location": "src/Web/Pages/Shared/_{partial-name}.cshtml",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "Partial view rendered from {referencing file}:{line}.",
    "{What the partial displays or does}.",
    "Model: {type passed via for= attribute}."
  ],
  "javaEquivalent": "Dedicated Angular 19 child component; receives data as @Input() from parent component"
}
```

#### ui-panel — Blazor Modal Components

Look for `<ComponentName @ref="ComponentVariable" ...>` where the component is a sibling `.razor` file. Read the modal file and add its form and actions as children.

```json
{
  "key": "{page_key}-{component-name}-modal",
  "name": "{Component Name} Modal",
  "elementType": "ui-panel",
  "location": "src/BlazorAdmin/Pages/{path}/{ComponentName}.razor",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "Bootstrap modal dialog. Opened via {ComponentVariable}.Open({params}).",
    "{What the modal does — create/edit/delete/view}.",
    "On save: calls {PublicApi endpoint}; fires OnSaveClick to reload parent list."
  ],
  "javaEquivalent": "Angular 19 dialog component (Angular CDK or Angular Material MatDialog); calls Spring @RestController {HTTP method} {endpoint} via Angular service"
}
```

#### ui-panel — Display Sections

Read-only sections with no form or table.

```json
{
  "key": "{page_key}-{descriptor}-display",
  "name": "{Descriptor} Display",
  "elementType": "ui-panel",
  "location": "{file}:{start-end}",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "Read-only. Shows {fields or data}.",
    "Driven by {ViewModel class or service}."
  ],
  "javaEquivalent": "Angular 19 component with read-only template; data bound via @Input() or loaded from Spring @RestController via Angular service"
}
```

---

### Phase 3: Extract Action Entries

#### Razor Pages — Form Submit Buttons

Look for `<input type="submit">`, `<button type="submit">`, `<button asp-page-handler="...">`. Read the corresponding `OnPost{Handler}()` in the code-behind.

```json
{
  "key": "{page_key}-{descriptor}-action",
  "name": "{Button Label}",
  "elementType": "ui-action",
  "location": "{file}:{line}",
  "parentKey": "{panel-key or form-key}",
  "domain": "{domain}",
  "actionType": "form-post",
  "notes": [
    "Submits to {OnPost handler}.",
    "{What the handler does}.",
    "Redirects to {destination} on success.",
    "Validation: {any notable server-side rules}."
  ],
  "javaEquivalent": "Angular (ngSubmit) calls Angular service HTTP {method} to Spring @RestController @{Mapping}; on success Angular Router navigates to {destination}"
}
```

#### Razor Pages — Navigation Links

Capture `<a asp-page="...">` or `<a asp-controller="..." asp-action="...">` links that carry user intent.

```json
{
  "key": "{page_key}-{descriptor}-link",
  "name": "{Link Label}",
  "elementType": "ui-action",
  "location": "{file}:{line}",
  "parentKey": "{panel-key}",
  "domain": "{domain}",
  "actionType": "navigation",
  "notes": [
    "Navigates to {target route}.",
    "{Conditional display rule if applicable}."
  ],
  "javaEquivalent": "Angular routerLink to {route}"
}
```

#### Blazor — `@onclick` Handlers

Read the handler from `@code` or `.razor.cs` to classify:
- `Component.Open(id)` → `modal-open`
- `service.Delete(id)` directly → `api-call`
- `NavigationManager.NavigateTo(...)` → `navigation`

```json
{
  "key": "{page_key}-{descriptor}-action",
  "name": "{Button Label}",
  "elementType": "ui-action",
  "location": "{file}:{line}",
  "parentKey": "{panel-key}",
  "domain": "{domain}",
  "actionType": "modal-open",
  "notes": [
    "Opens {ComponentName} modal via {ComponentVariable}.Open({params}).",
    "{What the modal allows the user to do}.",
    "Calls PublicApi {HTTP method} {endpoint path}."
  ],
  "javaEquivalent": "Angular (click) handler opens Angular dialog; dialog calls Spring @RestController {HTTP method} {endpoint} via Angular service"
}
```

#### Blazor — `OnValidSubmit` Form Saves

```json
{
  "key": "{page_key}-{form-descriptor}-save",
  "name": "Save",
  "elementType": "ui-action",
  "location": "{modal-file}:{line}",
  "parentKey": "{form-key}",
  "domain": "{domain}",
  "actionType": "form-post",
  "notes": [
    "OnValidSubmit calls {CatalogItemService.Method(_item)} → PublicApi {HTTP method} {path}.",
    "Fires OnSaveClick EventCallback to reload parent list.",
    "Closes modal on success.",
    "Validation: DataAnnotationsValidator on {Model class} — constraints: {list key constraints}."
  ],
  "javaEquivalent": "Angular (ngSubmit) on reactive form calls Angular service HTTP {method} to Spring @RestController; @Valid on @RequestBody DTO; Jakarta Bean Validation mirrors DataAnnotations constraints"
}
```

---

## Implementation Workflow

### Step 1: Parse Parameters
Extract `file`, `page_key`, and `domain` from the user query.

### Step 2: Determine Page Type
- `.cshtml` in `Pages/` → Razor Page
- `.razor` with `@page` → Blazor WebAssembly page
- `*Controller.cs` → MVC controller (one `ui-page` per `[HttpGet]` action)

### Step 3: Process the Entry-Point File
Run Phases 1–3 on the entry-point and all referenced files (partials, modal components).

- Track visited file paths to avoid re-processing
- Maximum reference depth: 2 levels

### Step 4: Write Output
1. Create folder `./docs/entry-points/ui-pages/{page_key}/` if it does not exist
2. Write `./docs/entry-points/ui-pages/{page_key}/inventory.json` — overwrite if already present

### Step 5: Report Summary

```
Page processed: {page_key} ({elementType})
Route:          {uri}
Output:         ./docs/entry-points/ui-pages/{page_key}/inventory.json

Entries written:
  Pages:   N
  Forms:   N
  Panels:  N
  Actions: N  (form-post: N, modal-open: N, api-call: N, navigation: N, filter: N)
```

---

## Examples

### Example 1: Razor Page — Basket Checkout

```
/inventory-ui-features file:src/Web/Pages/Basket/Checkout.cshtml page_key:basket-checkout domain:basket
```

Expected entries:
- `basket-checkout` (ui-page) — `/basket/checkout`, requires auth
- `basket-checkout-order-form` (ui-form) — POST form wrapping the items list
- `basket-checkout-items-table` (ui-panel) — read-only line-items display inside the form
- `basket-checkout-pay-now` (ui-action, form-post) — `[Pay Now]` → `OnPost` creates order
- `basket-checkout-back` (ui-action, navigation) — `[Back]` → `/basket`

### Example 2: Blazor Page — Admin Catalog List

```
/inventory-ui-features file:src/BlazorAdmin/Pages/CatalogItemPage/List.razor page_key:admin-catalog-item-list domain:catalog
```

Expected entries:
- `admin-catalog-item-list` (ui-page) — `/admin`, requires `ADMINISTRATORS` role
- `admin-catalog-item-list-catalog-table` (ui-panel) — table of all catalog items
- `admin-catalog-item-list-create-modal` (ui-panel) — `Create.razor` modal
- `admin-catalog-item-list-edit-modal` (ui-panel) — `Edit.razor` modal
- `admin-catalog-item-list-delete-modal` (ui-panel) — `Delete.razor` modal
- `admin-catalog-item-list-details-modal` (ui-panel) — `Details.razor` modal
- `admin-catalog-item-list-create-new` (ui-action, modal-open) — `[Create New]` → `CreateComponent.Open()`
- `admin-catalog-item-list-edit` (ui-action, modal-open) — `[Edit]` row button → `EditComponent.Open(id)`
- `admin-catalog-item-list-delete` (ui-action, modal-open) — `[Delete]` row button → `DeleteComponent.Open(id)`
- `admin-catalog-item-list-details` (ui-action, modal-open) — row click → `DetailsComponent.Open(id)`

From Edit modal (Phase 2 modal tracking):
- `admin-catalog-item-edit-modal-form` (ui-form) — `<EditForm Model="_item">` with DataAnnotations
- `admin-catalog-item-edit-modal-save` (ui-action, form-post) — `OnValidSubmit` → `CatalogItemService.Edit(_item)` → `PUT /api/catalog-items/{id}`
- `admin-catalog-item-edit-modal-cancel` (ui-action) — `[Cancel]` → closes modal, no data change

### Example 3: MVC Controller — Orders

```
/inventory-ui-features file:src/Web/Controllers/OrderController.cs page_key:order domain:orders
```

Expected entries:
- `order-my-orders` (ui-page) — `/order/my-orders`, requires `[Authorize]`
- `order-detail` (ui-page) — `/order/detail/{orderId}`, requires `[Authorize]`
- `order-my-orders-orders-table` (ui-panel) — columns: Order#, Date, Total, Status
- `order-my-orders-detail-link` (ui-action, navigation) — `Detail` per row → `/order/detail/{id}`
- `order-my-orders-cancel-link` (ui-action, navigation) — `Cancel`, shown only when `status == "submitted"`

---

## Important Notes

1. **Factual only.** No complexity scores, migration estimates, or subjective analysis.
2. **Flat array.** All entries in one array, linked by keys.
3. **Line numbers.** Always include in `location` for panels and actions.
4. **No README.** Only write `inventory.json`.
5. **Follow modal components.** When a Blazor page references `<Edit @ref="...">`, read that `.razor` file and include its forms and actions.
6. **Follow partials.** When a Razor Page uses `<partial name="...">`, read the partial and include its sub-panels and actions.
7. **`parentKey` chain.** Actions inside a modal form point to the modal's `ui-form` key, not the top-level page.
8. **Cancel buttons.** Skip pure UI-dismiss buttons. Include cancel only if it performs meaningful work (e.g. discards a draft).
9. **Conditional actions.** Include entries for conditionally shown actions (e.g. Cancel only when `status == "submitted"`); note the condition in `notes`.
10. **MVC controllers.** One `ui-page` per `[HttpGet]` returning `View()`. POST-only handlers become `ui-action` entries on their form.
11. **`javaEquivalent` on every entry.** Required. Name the Angular construct for UI, the Spring annotation for backend. Do not write "N/A". No Thymeleaf — target is Angular 19 SPA + Spring Boot 3.5 REST.

---

## Angular 19 + Spring Boot 3.5 Reference

The target stack has **no Thymeleaf** — Angular 19 SPA handles all UI; Spring Boot 3.5 `@RestController` provides all data as JSON.

### Page / Routing

| ASP.NET Core | Angular 19 + Spring Boot 3.5 |
|---|---|
| Razor Page `@page "/route"` | Angular page component at `/route`; data via Angular service (HttpClient) → Spring `@RestController` |
| Blazor `@page "/route"` | Angular 19 page component at same route |
| MVC `@Controller` + `View()` | Angular page component; Spring `@RestController` provides JSON |
| `[Authorize]` | Angular `AuthGuard` on route + Spring Security `.authenticated()` on endpoint |
| `[Authorize(Roles = "ADMINISTRATORS")]` | Angular `AuthGuard` checking role + Spring `@PreAuthorize("hasRole('ADMINISTRATORS')")` |
| Route param `{orderId:int}` | Angular `ActivatedRoute` snapshot + Spring `@PathVariable int orderId` |
| `IMediator.Send(new Query(...))` | Spring `@Service` method call |

### Forms & Validation

| ASP.NET Core | Angular 19 + Spring Boot 3.5 |
|---|---|
| `<form method="post">` | Angular reactive form `(ngSubmit)` calling Angular service HTTP POST |
| `OnPost{Handler}()` in PageModel | Spring `@RestController` `@PostMapping` |
| `<EditForm OnValidSubmit="...">` | Angular reactive form `(ngSubmit)`; validation via `Validators` + Spring `@Valid` on `@RequestBody` |
| `[Required]`, `[Range]`, `[StringLength]` | `@NotNull`, `@Min`/`@Max`, `@Size` on Java DTO (Jakarta Validation) |
| Redirect after POST | Angular `Router.navigate(['/destination'])` after successful HTTP response |

### Data Display

| ASP.NET Core | Angular 19 + Spring Boot 3.5 |
|---|---|
| `@foreach` over `Model.Collection` | Angular `@for` (or `*ngFor`) over array from Angular service response |
| `<partial name="_product">` | Dedicated Angular child component; data passed as `@Input()` |
| `@Model.SomeProperty` | Angular template `{{ item.someProperty }}` |
| Pagination via `PaginationInfo` | Spring Data `Page<T>` / `Pageable` from `@RestController`; Angular component renders page controls from response metadata |
| `@if (!Model.Items.Any())` | Angular `@if` (or `*ngIf`) on the empty-state block |

### Services & Data Access

| ASP.NET Core | Angular 19 + Spring Boot 3.5 |
|---|---|
| `ICatalogViewModelService` injected into PageModel | Angular `@Injectable` service using `HttpClient` + Spring `@Service` + `@RestController` |
| `CatalogItemService` (Blazor, calls REST) | Angular service using `HttpClient` calling Spring `@RestController` |
| `IRepository<T>` | Spring Data JPA `JpaRepository<T, ID>` |
| `Ardalis.Specification` | Spring Data JPA `Specification<T>` or query method derivation |
| `IMediator` / MediatR | Spring `@Service` method call |

### Blazor UI Patterns → Angular 19

| Blazor | Angular 19 |
|---|---|
| Bootstrap modal (`_modalDisplay = "block"`) | Angular CDK Dialog or `MatDialog`; opened via `dialog.open(ComponentClass)` |
| `EventCallback<string> OnSaveClick` | `@Output() EventEmitter` or shared service `Subject` |
| `@ref="ComponentVariable"` | `@ViewChild(ComponentClass)` |
| `OnInitializedAsync` | `ngOnInit()` calling Angular service; use `async` pipe or subscribe |
| `StateHasChanged()` | Angular signals or `ChangeDetectorRef.markForCheck()` |
| `[Parameter]` | `@Input()` |
| `NavigationManager.NavigateTo(path)` | `Router.navigate([path])` |
