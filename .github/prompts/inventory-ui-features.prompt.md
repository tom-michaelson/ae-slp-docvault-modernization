# Inventory UI Features

You are tasked with creating a factual inventory of UI features for one page from the **legacy React/Node.js application**. This inventory is an input to a modernization effort targeting **Angular 19 + .NET** — every entry must capture enough behavioural detail for a developer to rebuild the feature in that stack without reading the original source.

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
file:src/pages/DocumentList.tsx
page_key:document-list-page
domain:documents
```
```
file:src/components/DocumentUploadPanel.tsx
page_key:document-upload-panel
domain:documents
```
```
file:src/pages/DocumentDetail.tsx
page_key:document-detail-view
domain:documents
```

---

## Output

Each page gets its own folder:
`./docs/entry-points/ui-pages/{page_key}/inventory.json`

**Structure:** A flat JSON array — the page entry first, then all panels/forms, then all actions — linked by keys.

**Established format** (matches `docs/entry-points/ui-pages/home/inventory.json`, with the addition of `dotnetEquivalent`):

```json
[
  {
    "key": "page-key",
    "name": "Human Readable Name",
    "elementType": "ui-page",
    "location": "src/pages/DocumentList.tsx",
    "uri": "/documents",
    "domain": "documents",
    "notes": [
      "React Page Component. Route: /documents.",
      "Auth: protected (requires authenticated user).",
      "Loads data via useDocuments hook calling documentService.getDocuments.",
      "Query params: page, filter, status."
    ],
    "dotnetEquivalent": "Angular 19 page component at /documents; Angular service fetches data via HttpClient from ASP.NET Core [ApiController]; service maps to .NET service class"
  },
  {
    "key": "page-key-filter-form",
    "name": "Filter Form",
    "elementType": "ui-form",
    "location": "src/pages/DocumentList.tsx:10-23",
    "parentKey": "page-key",
    "domain": "documents",
    "notes": [
      "Controlled form. Submits filter state to trigger re-fetch on the same route.",
      "Fields: status (select), filter (text input).",
      "No server-side validation — filter params are passed directly to API."
    ],
    "dotnetEquivalent": "Angular reactive form; on change calls Angular service GET with ?filter=&status= query params to ASP.NET Core [ApiController]"
  },
  {
    "key": "page-key-document-list",
    "name": "Document List",
    "elementType": "ui-panel",
    "location": "src/pages/DocumentList.tsx:24-45",
    "parentKey": "page-key",
    "domain": "documents",
    "notes": [
      "Renders one row per Document via DocumentRow component.",
      "Empty-state: 'No documents found.'.",
      "Paginated — items bounded by pageSize."
    ],
    "dotnetEquivalent": "Angular 19 component with @for loop over documents from Angular service response; empty-state via @if"
  },
  {
    "key": "page-key-upload-button",
    "name": "Upload Document Button",
    "elementType": "ui-action",
    "location": "src/pages/DocumentList.tsx:12",
    "parentKey": "page-key-document-list",
    "domain": "documents",
    "actionType": "navigation",
    "notes": [
      "Navigates to /documents/upload.",
      "Visible to all authenticated users.",
      "No server action — pure client navigation."
    ],
    "dotnetEquivalent": "Angular routerLink to /documents/upload"
  }
]
```

### Element Types

| elementType | When to use |
|-------------|-------------|
| `ui-page` | The page itself (React page component, route-level component) |
| `ui-form` | `<form>` in React, controlled form managed by useState/useFormik/React Hook Form |
| `ui-panel` | Data table, child component, modal/dialog, display section |
| `ui-action` | Button/link with user-facing behaviour (submit, open modal, navigate, delete) |

### Action Types

| actionType | When to use |
|------------|-------------|
| `form-submit` | Form submission triggering an `onSubmit` handler |
| `modal-open` | Opens a modal/dialog component |
| `modal-confirm` | Opens a confirmation/delete modal |
| `navigation` | `<Link to="...">`, `useNavigate()`, or plain `href` link with user intent |
| `api-call` | Direct service call without modal (delete, toggle, refresh) |
| `filter` | GET-form submission to filter/search page data |
| `other` | Anything not matching above — use sparingly |

### Field Rules

- `key` — `{page_key}-{descriptor}`, all lowercase kebab-case
- `name` — Short human-readable label (3–6 words), title case
- `location` — Relative to `./target_repo/source/`. Include `:start-end` for panels, `:N` for single-line actions
- `parentKey` — For panels: the page key. For actions: the panel or form they appear inside
- `notes` — Array of concise factual strings. Capture: data shown/posted, service delegation, auth, empty states, redirect targets, validation rules, conditional display logic
- `dotnetEquivalent` — **Required on every entry.** One sentence. Name the Angular construct for UI elements and the .NET class/attribute for backend logic. The target stack is Angular 19 SPA + .NET REST API. See the reference section below.

---

## Exclusion Criteria

Do **not** create inventory entries for:

- **Layout scaffolding:** `AppShell.tsx`, `NavBar.tsx`, `Footer.tsx`, `Layout.tsx`, `_app.tsx`
- **Utility components:** `Spinner.tsx`, `Toast.tsx`, `ErrorBoundary.tsx`, `ProtectedRoute.tsx`
- **Validation helper components:** `FormError.tsx`, `FieldError.tsx`
- **Error/404 pages** unless explicitly passed as the `file` argument
- **Static hero/banner sections** with no data or user interaction
- **Structural-only navigation links** — capture only actions that carry user intent (e.g. `[Upload]`, `[Delete]`), not breadcrumbs or `[Back]` links

---

## Discovery Process

### Phase 1: Detect Page Type and Create `ui-page` Entry

#### React Page Component (`*.tsx` / `*.jsx` in `pages/` or `views/`)
1. Read `{file}` — extract route path (from React Router config or file-based routing), `useAuth` / `ProtectedRoute` usage (auth), imported hooks and services
2. Check for a companion hook file (`use*.ts`) — the data-fetching logic source
3. Infer URI from router config or folder convention (e.g. `pages/DocumentList.tsx` → `/documents`)

```json
{
  "key": "{page_key}",
  "name": "{title from page heading or component name}",
  "elementType": "ui-page",
  "location": "src/pages/{path}.tsx",
  "uri": "/{route}",
  "domain": "{domain}",
  "notes": [
    "React Page Component. Route: /{route}.",
    "Auth: {protected (useAuth / ProtectedRoute) or 'public'}.",
    "Loads data via {hook or service call}.",
    "Query params: {list any, or omit if none}."
  ],
  "dotnetEquivalent": "Angular 19 page component at /{route}; Angular service fetches data via HttpClient from ASP.NET Core [ApiController]; {service} becomes .NET service class"
}
```

#### React Feature Component (`*.tsx` / `*.jsx` in `components/` or `features/`)
1. Read `{file}` — extract props interface, local state, imported services or hooks
2. Check for `@ref`, callback props, or `useImperativeHandle` — these imply parent-controlled open/close
3. Note: Feature components may not have their own route — their URI is the parent page's route

```json
{
  "key": "{page_key}",
  "name": "{component display name}",
  "elementType": "ui-page",
  "location": "src/components/{path}.tsx",
  "uri": "{parent page route}",
  "domain": "{domain}",
  "notes": [
    "React Feature Component. No standalone route — rendered by parent page.",
    "Auth: {inherited from parent or 'public'}.",
    "Loads data via {imported hook or service}."
  ],
  "dotnetEquivalent": "Angular 19 child component; receives data as @Input() or fetches via Angular service from ASP.NET Core [ApiController]; route guarded by parent"
}
```

#### React Container Component (uses Redux / Context / data hooks)
1. Read `{file}` — identify `useSelector`/`useDispatch` or `useContext` calls, slice/context name
2. Read the Redux slice or context provider file
3. Identify `useQuery`/`useMutation` (React Query) or similar data-fetching hooks

```json
{
  "key": "{page_key}",
  "name": "{container display name}",
  "elementType": "ui-page",
  "location": "src/containers/{path}.tsx",
  "uri": "/{route}",
  "domain": "{domain}",
  "notes": [
    "React Container Component. Route: /{route}.",
    "Auth: {protected via ProtectedRoute or useAuth hook}.",
    "Data loaded via Redux thunk / React Query — {slice or query key name}."
  ],
  "dotnetEquivalent": "Angular 19 page component at /{route}; data fetched via Angular service from ASP.NET Core [ApiController]; route guarded by Angular AuthGuard"
}
```

---

### Phase 2: Extract Panel and Form Entries

#### ui-form — Forms

- React: `<form onSubmit={handler}>` with controlled inputs, or libraries like Formik / React Hook Form

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
  "dotnetEquivalent": "Angular 19 reactive form (FormGroup/FormControl); on submit calls Angular service HTTP {method} to ASP.NET Core [ApiController]; model validation via Data Annotations"
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
  "dotnetEquivalent": "Angular 19 component with @for (or *ngFor) over {collection} loaded via Angular service from ASP.NET Core [ApiController]"
}
```

#### ui-panel — Child Components

Look for imported React components rendered in JSX. Read the component file and create child entries from its content.

```json
{
  "key": "{page_key}-{component-name}",
  "name": "{Component Purpose}",
  "elementType": "ui-panel",
  "location": "src/components/{ComponentName}.tsx",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "Child component rendered from {referencing file}:{line}.",
    "{What the component displays or does}.",
    "Props: {key props passed from parent}."
  ],
  "dotnetEquivalent": "Dedicated Angular 19 child component; receives data as @Input() from parent component"
}
```

#### ui-panel — React Modal / Dialog Components

Look for components that render a modal overlay (e.g., conditionally rendered with `isOpen` prop, or using a portal). Read the modal file and add its form and actions as children.

```json
{
  "key": "{page_key}-{component-name}-modal",
  "name": "{Component Name} Modal",
  "elementType": "ui-panel",
  "location": "src/components/{ComponentName}Modal.tsx",
  "parentKey": "{page_key}",
  "domain": "{domain}",
  "notes": [
    "Modal/dialog component. Opened via {isOpen state or ref.open()}.",
    "{What the modal does — create/edit/delete/view}.",
    "On save: calls {API endpoint} via service; fires onSuccess callback to reload parent list."
  ],
  "dotnetEquivalent": "Angular 19 dialog component (Angular CDK or Angular Material MatDialog); calls ASP.NET Core [ApiController] {HTTP method} endpoint via Angular service"
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
  "dotnetEquivalent": "Angular 19 component with read-only template; data bound via @Input() or loaded from ASP.NET Core [ApiController] via Angular service"
}
```

---

### Phase 3: Extract Action Entries

#### React — Form Submit Buttons

Look for `<button type="submit">` inside `<form onSubmit={handler}>`, or `formik.handleSubmit`. Read the corresponding handler function.

```json
{
  "key": "{page_key}-{descriptor}-action",
  "name": "{Button Label}",
  "elementType": "ui-action",
  "location": "{file}:{line}",
  "parentKey": "{panel-key or form-key}",
  "domain": "{domain}",
  "actionType": "form-submit",
    "{What the handler does}.",
    "Redirects to {destination} on success.",
    "Validation: {any notable server-side rules}."
  ],
  "dotnetEquivalent": "Angular (ngSubmit) calls Angular service HTTP {method} to ASP.NET Core [ApiController]; on success Angular Router navigates to {destination}"
}
```

#### React — Navigation Links

Capture `<Link to="...">` (React Router), `<a href="...">`, or `useNavigate()` calls that carry user intent.

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
  "dotnetEquivalent": "Angular routerLink to {route}"
}
```

#### React — `onClick` Handlers

Read the handler function to classify:
- `setIsOpen(true)` / modal state setter → `modal-open`
- `service.delete(id)` directly → `api-call`
- `navigate('/path')` (useNavigate) → `navigation`

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
    "Opens {ComponentName} modal via {setIsOpen(true) or similar state setter}.",
    "{What the modal allows the user to do}.",
    "Calls API {HTTP method} {endpoint path}."
  ],
  "dotnetEquivalent": "Angular (click) handler opens Angular dialog; dialog calls ASP.NET Core [ApiController] {HTTP method} endpoint via Angular service"
}
```

#### React — Form Save (onSubmit)

```json
{
  "key": "{page_key}-{form-descriptor}-save",
  "name": "Save",
  "elementType": "ui-action",
  "location": "{modal-file}:{line}",
  "parentKey": "{form-key}",
  "domain": "{domain}",
  "actionType": "form-submit",
  "notes": [
    "onSubmit calls {service.method(data)} → API {HTTP method} {path}.",
    "Fires onSuccess callback to reload parent list.",
    "Closes modal on success.",
    "Validation: {React Hook Form / Formik / manual} on {model} — constraints: {list key constraints}."
  ],
  "dotnetEquivalent": "Angular (ngSubmit) on reactive form calls Angular service HTTP {method} to ASP.NET Core [ApiController]; model validation via Data Annotations"
}
```

---

## Implementation Workflow

### Step 1: Parse Parameters
Extract `file`, `page_key`, and `domain` from the user query.

### Step 2: Determine Page Type
- `*.tsx` / `*.jsx` in `pages/` or `views/` → React Page Component
- `*.tsx` / `*.jsx` in `components/` or `features/` → React Feature Component
- `*.tsx` / `*.jsx` using Redux / Context / data hooks → React Container Component

### Step 3: Process the Entry-Point File
Run Phases 1–3 on the entry-point and all referenced files (child components, modal components).

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
  Actions: N  (form-submit: N, modal-open: N, api-call: N, navigation: N, filter: N)
```

---

## Examples

### Example 1: React Page — Document List

```
/inventory-ui-features file:src/pages/DocumentList.tsx page_key:document-list-page domain:documents
```

Expected entries:
- `document-list-page` (ui-page) — `/documents`, requires auth
- `document-list-page-filter-form` (ui-form) — controlled form with status/filter inputs
- `document-list-page-document-list` (ui-panel) — renders DocumentRow per document
- `document-list-page-upload-button` (ui-action, navigation) — `[Upload]` → `/documents/upload`
- `document-list-page-delete` (ui-action, api-call) — `[Delete]` row button → `documentService.delete(id)`

### Example 2: React Feature Component — Document Upload Panel

```
/inventory-ui-features file:src/components/DocumentUploadPanel.tsx page_key:document-upload-panel domain:documents
```

Expected entries:
- `document-upload-panel` (ui-page) — `/documents/upload`, requires auth
- `document-upload-panel-upload-form` (ui-form) — `<form onSubmit={handleUpload}>` with file input and metadata fields
- `document-upload-panel-submit` (ui-action, form-submit) — `[Upload]` → `documentService.uploadDocument(data)` → `POST /api/documents`
- `document-upload-panel-cancel` (ui-action, navigation) — `[Cancel]` → `/documents`

### Example 3: React Page — Document Detail

```
/inventory-ui-features file:src/pages/DocumentDetail.tsx page_key:document-detail-view domain:documents
```

Expected entries:
- `document-detail-view` (ui-page) — `/documents/:id`, requires auth
- `document-detail-view-metadata-display` (ui-panel) — read-only metadata section
- `document-detail-view-edit-modal` (ui-panel) — edit modal opened via edit button
- `document-detail-view-edit-button` (ui-action, modal-open) — `[Edit]` → opens edit modal
- `document-detail-view-download` (ui-action, api-call) — `[Download]` → `documentService.download(id)`

---

## Important Notes

1. **Factual only.** No complexity scores, migration estimates, or subjective analysis.
2. **Flat array.** All entries in one array, linked by keys.
3. **Line numbers.** Always include in `location` for panels and actions.
4. **No README.** Only write `inventory.json`.
5. **Follow modal components.** When a React page renders a modal component, read that `.tsx` file and include its forms and actions.
6. **Follow child components.** When a page imports and renders a feature component, read the component file and include its sub-panels and actions.
7. **`parentKey` chain.** Actions inside a modal form point to the modal's `ui-form` key, not the top-level page.
8. **Cancel buttons.** Skip pure UI-dismiss buttons. Include cancel only if it performs meaningful work (e.g. discards a draft).
9. **Conditional actions.** Include entries for conditionally shown actions (e.g. Delete only when user is owner); note the condition in `notes`.
10. **Container components.** One `ui-page` per routed container. Non-routed containers become `ui-panel` entries under their parent page.
11. **`dotnetEquivalent` on every entry.** Required. Name the Angular construct for UI, the .NET class/attribute for backend. Do not write "N/A". Target is Angular 19 SPA + .NET REST API.

---

## Angular 19 + .NET Reference

The target stack has **no server-rendered HTML** — Angular 19 SPA handles all UI; ASP.NET Core `[ApiController]` provides all data as JSON.

### Page / Routing

| React / Node.js | Angular 19 + .NET |
|---|---|
| React Router `<Route path="/route">` | Angular page component at `/route`; data via Angular service (HttpClient) → ASP.NET Core `[ApiController]` |
| File-based routing (Next.js pages/) | Angular 19 page component at same route |
| `ProtectedRoute` / `useAuth` check | Angular `AuthGuard` on route + .NET auth policy on endpoint |
| `useAuth` checking role | Angular `AuthGuard` checking role + .NET `[Authorize(Roles = "...")]` |
| Route param `:id` | Angular `ActivatedRoute` snapshot + ASP.NET Core `[FromRoute] int id` |
| Redux thunk / React Query call | .NET service class method call |

### Forms & Validation

| React / Node.js | Angular 19 + .NET |
|---|---|
| `<form onSubmit={handler}>` | Angular reactive form `(ngSubmit)` calling Angular service HTTP POST |
| `onSubmit` handler function | ASP.NET Core `[ApiController]` `[HttpPost]` action |
| Formik / React Hook Form `handleSubmit` | Angular reactive form `(ngSubmit)`; validation via `Validators` + Data Annotations on DTO |
| Yup / Zod schema constraints | `[Required]`, `[Range]`, `[StringLength]` on .NET DTO (Data Annotations) |
| `navigate('/destination')` after submit | Angular `Router.navigate(['/destination'])` after successful HTTP response |

### Data Display

| React / Node.js | Angular 19 + .NET |
|---|---|
| `{items.map(item => ...)}` over array | Angular `@for` (or `*ngFor`) over array from Angular service response |
| Imported child component `<ItemCard />` | Dedicated Angular child component; data passed as `@Input()` |
| `{item.someProperty}` | Angular template `{{ item.someProperty }}` |
| Pagination via query params | .NET `IQueryable` pagination; Angular component renders page controls from response metadata |
| `{items.length === 0 && <EmptyState />}` | Angular `@if` (or `*ngIf`) on the empty-state block |

### Services & Data Access

| React / Node.js | Angular 19 + .NET |
|---|---|
| Custom hook `useDocuments()` calling service | Angular `@Injectable` service using `HttpClient` + .NET `[ApiController]` + service class |
| `documentService.getDocuments()` (REST call) | Angular service using `HttpClient` calling ASP.NET Core `[ApiController]` |
| Redux store / slice | Angular signals or NgRx store |
| React Query `useQuery` | Angular service with `HttpClient` observable |
| Context provider for shared state | Angular `@Injectable` singleton service or NgRx store |

### React UI Patterns → Angular 19

| React | Angular 19 |
|---|---|
| Modal with `isOpen` state (`useState(false)`) | Angular CDK Dialog or `MatDialog`; opened via `dialog.open(ComponentClass)` |
| `onSuccess` callback prop | `@Output() EventEmitter` or shared service `Subject` |
| `ref` / `useImperativeHandle` | `@ViewChild(ComponentClass)` |
| `useEffect(() => { fetchData() }, [])` | `ngOnInit()` calling Angular service; use `async` pipe or subscribe |
| Manual `setState` / `forceUpdate` | Angular signals or `ChangeDetectorRef.markForCheck()` |
| Component props | `@Input()` |
| `useNavigate()` / `navigate('/path')` | `Router.navigate([path])` |
