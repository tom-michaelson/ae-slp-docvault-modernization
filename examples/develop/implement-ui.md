# Implement UI Feature

Implement a UI feature by executing all tasks in the task list, with work unit type detection, configuration validation, and checklist-driven implementation.

## Usage

```
/implement-ui task list: [task-list-path], implementation_plan: [implementation-plan-path]
```

## Input

- `task list`: Path to the task-list.md file
- `implementation_plan`: Path to the implementation-plan.md file

## Retry Handling

On retry attempts, the workflow may pass previous review feedback:

```
/implement-ui task list: `[path]`, implementation_plan: `[path]`, last implementation review result:
{
  "validated": false,
  "notes": "...",
  "remaining_issues": "..."
}
```

When `last implementation review result` is provided:
1. Read the `remaining_issues` carefully before starting
2. Focus implementation effort on fixing those specific issues first
3. Re-validate all counts after fixes
4. Ensure previously-passing validations still pass

## CRITICAL: Autonomous Execution

**This command MUST execute autonomously without asking for user input.**

- Make implementation decisions based on the implementation plan
- If something is unclear, make your best judgment and document in code comments
- Complete all tasks without stopping for approval

## Sub-Agent Support

### Developer Agent Reference

Use specialized developer agents for UI implementation tasks:

| Agent | Color | Use For |
|-------|-------|---------|
| `passage-ui-developer` | teal | Components, services, models, mappers |
| `pattern-registry-developer` | silver | Register new patterns discovered during implementation |

### Sub-Agent Dispatch for Multi-Component Pages

For pages with multiple panels or complex component hierarchies, dispatch parallel sub-agents:

```
Example: Page with 3 panels

1. Read implementation plan (main context)
2. Launch parallel passage-ui-developer agents:
   - Agent 1: "Implement main component shell, search config, routing"
   - Agent 2: "Implement Panel A configuration and data binding"
   - Agent 3: "Implement Panel B configuration and data binding"
3. Integration: Connect panels, verify data flow
```

### Sub-Agent Prompt Template

```
Implement the following UI tasks from an implementation plan.

Work Unit Type: {Page Setup | Panel | Modal}
Implementation plan section: {relevant section}
Tasks to complete: {specific checklist items}

Reference frontend architecture at: docs/target-architecture/frontend-architecture/
Use core components: TableSearchLayoutComponent, DataTableComponent, SearchFormComponent

Write production-quality code. Validate configuration counts.
After completing each task, report count validation results.

## MANDATORY: data-testid on Every Element

Every interactive or identifiable UI element MUST include a `data-testid` attribute.

**Rules:**
- HTML attribute: `data-testid` (all lowercase, no hyphen between "test" and "id")
- Component `@Input()` property: `dataTestId` (camelCase)
- Binding to HTML element: `[attr.data-testid]="dataTestId"`
- Binding to child component: `[dataTestId]="'feature-element-name'"`

**Naming format:** `{domain}-{component}-{element}`

**What MUST have data-testid:**
- Page/view wrapper `<div>`
- All `<app-*>` child components (pass via `[dataTestId]`)
- All buttons (`<app-button>`, `<button>`)
- All form fields and inputs
- Data grids (`<app-data-table>`)
- Dialogs and modals

**NEVER use:** `data-test-id`, `data-TestId`, or `dataTestid` — these are wrong.
```

### Pattern Discovery

If you discover a reusable pattern during implementation, use `pattern-registry-developer` to register it for future use.

### Parallel Execution Strategy

**CRITICAL: Maximize parallelization by launching sub-agents in a SINGLE message.**

When multiple tasks are independent, launch all their sub-agents together:

```python
# CORRECT - Launch independent tasks in ONE message (parallel execution):
Task(subagent_type="passage-ui-developer", prompt="Implement models and DTOs...")
Task(subagent_type="passage-ui-developer", prompt="Implement mappers...")
Task(subagent_type="passage-ui-developer", prompt="Set up routing...")

# After ALL complete, launch dependent tasks:
Task(subagent_type="passage-ui-developer", prompt="Implement component with configs...")
```

**Parallelization rules:**
1. **Independent tasks** → launch in single message (parallel execution)
2. **Dependent tasks** → wait for blockers to complete first
3. **Consult `task-list.md` Dependency Matrix** for guidance on what can parallelize

**Standard UI implementation waves by work unit type:**

**Page Setup:**
| Wave | Parallel Tasks | Sub-agents |
|------|---------------|------------|
| 1 | DTOs, Models, Routing setup | 3 parallel |
| 2 | Mappers, API Service interfaces | 2 parallel |
| 3 | API Service impl | 1 parallel |
| 4 | SearchConfig, PanelConfig | 2 parallel |
| 5 | Component implementation | 1 parallel |

**Panel:**
| Wave | Parallel Tasks | Sub-agents |
|------|---------------|------------|
| 1 | GridColumn config, MenuItem config | 2 parallel |
| 2 | Menu action handler, Data binding | 2 parallel |
| 3 | Selection handling | 1 parallel |

**Modal:**
| Wave | Parallel Tasks | Sub-agents |
|------|---------------|------------|
| 1 | Form field config | 1 |
| 2 | Dialog implementation, Validation | 2 parallel |
| 3 | API integration | 1 parallel |

### Claude Task Progress Tracking

Use Claude's `TaskCreate`/`TaskUpdate` tools to track component-level progress:

**Before starting each component/phase:**
```python
TaskUpdate(taskId="search-config-task-id", status="in_progress")
```

**After completing each component/phase:**
```python
TaskUpdate(taskId="search-config-task-id", status="completed")
# Check what's now unblocked
TaskList()
```

**Example tracking flow for Page Setup:**
```
# Wave 1: Models + Routing
TaskUpdate(taskId="models-task-id", status="in_progress")
TaskUpdate(taskId="routing-task-id", status="in_progress")

# Launch parallel sub-agents
Task(subagent_type="passage-ui-developer", prompt="Implement models...")
Task(subagent_type="passage-ui-developer", prompt="Set up routing...")

# After all complete:
TaskUpdate(taskId="models-task-id", status="completed")
TaskUpdate(taskId="routing-task-id", status="completed")

# Wave 2: Configs (now unblocked)
TaskUpdate(taskId="search-config-task-id", status="in_progress")
# ... continue pattern
```

---

## Phase 0: Read & Understand

### 0.1 Read Input Documents

1. **Read implementation-plan.md completely** - understand all configurations
2. **Read task-list.md** - understand all tasks to complete
3. **Extract the Work Unit Type** from the implementation plan header

### 0.2 Work Unit Type Detection (CRITICAL)

UI features follow a hierarchical work unit model. **Detect the work unit type** from the implementation plan to determine implementation focus:

| Work Unit Type | Focus | Validates | Does NOT Validate |
|----------------|-------|-----------|-------------------|
| **Page Setup** | Layout structure | Search fields + Panel IDs | Grid columns, context menus |
| **Panel** | Panel internals | Grid columns + Context menu actions | - |
| **Modal** | Dialog forms | Form fields + Validation rules | - |

**Rationale**: A page with 5 panels, each with 10+ columns, would create overwhelming checklists at Page Setup level. Each work unit stays focused and manageable.

**Detection Logic:**
1. **Page Setup**: Key ends with the page name (no panel/action suffix)
2. **Panel**: Key has one additional segment after page name
3. **Modal**: Key has action suffix (`-modify`, `-new`, `-attach-document`, `-view-attachment`)

The implementation plan header contains: `> **Work Unit Type**: [Page Setup | Panel | Modal]`

### 0.3 Read Architecture Documentation

Based on work unit type, read relevant architecture docs:

**For ALL work unit types:**
- [ ] `./docs/target-architecture/frontend-architecture/index.md`
- [ ] `./docs/target-architecture/frontend-architecture/reference/configuration.md` (FieldConfig, PanelConfig, SearchConfig)

**For Page Setup:**
- [ ] `./docs/target-architecture/frontend-architecture/page-patterns.md`
- [ ] `./docs/target-architecture/frontend-architecture/implementation-guides.md`

**For Panel:**
- [ ] `./docs/target-architecture/frontend-architecture/reference/core-components.md` (DataTable, TabPanel)

**For Modal:**
- [ ] `./docs/target-architecture/frontend-architecture/reference/core-components.md` (ConfigurableFormDialog)

---

## Phase 1: Configuration Extraction & Checklist Creation

**Extract configurations from implementation-plan.md and create checklists with expected counts.**

### 1.1 For Page Setup

Extract from implementation plan sections:

#### Search Form Checklist (if page has search)
Parse the **Search Form Configuration** section and create:

| # | Field Name | Type | Required | Status |
|---|------------|------|----------|--------|
| 1 | [name from plan] | [TEXT/LOOKUP/DATE/CHECKBOX/DROPDOWN] | [Y/N] | [ ] |
| 2 | ... | ... | ... | [ ] |

**Expected Count: [N]**

#### Layout Type
Parse the **Layout Configuration** section to identify:
- Layout Type: [simple-table | two-column | two-row | tabbed | master-tabbed-detail]

#### Panel Configuration Checklist
Parse the **PanelConfig[]** section:

| # | Panel ID | Panel Type | Status |
|---|----------|------------|--------|
| 1 | [id from plan] | [table/custom/tabs] | [ ] |
| 2 | ... | ... | [ ] |

**Expected Panel Count: [N]**

#### Tab Configuration Checklist (if layout is tabbed)
If layout type is `tabbed` or `master-tabbed-detail`, also extract tabs:

| # | Tab ID | Tab Label | Tab Panel Type | Status |
|---|--------|-----------|----------------|--------|
| 1 | [id] | [label from plan] | [table/custom] | [ ] |
| 2 | ... | ... | ... | [ ] |

**Expected Tab Count: [N]** (or N/A if not tabbed)

> **Note**: Do NOT extract grid columns or context menu actions here. Those are validated in the Panel work unit.

### 1.1.1 Handling Missing Count Information

If the implementation plan doesn't explicitly state expected counts:
1. Count items manually from the relevant plan section
2. Document: "Expected: X (counted from [section name])"
3. If plan is genuinely ambiguous, add code comment: `// TODO: Verify count with tech plan author`

### 1.2 For Panel

Extract from implementation plan:

#### Table Columns Checklist (if table panel)
| # | Field Name | Header | Type | Width | Status |
|---|------------|--------|------|-------|--------|
| 1 | [name] | [header] | [type] | [px] | [ ] |

**Expected Count: [N]**

#### Context Menu Actions Checklist
| # | Action | Action Type | Status |
|---|--------|-------------|--------|
| 1 | [action] | [modal-crud/print/etc] | [ ] |

**Expected Count: [N]**

### 1.3 For Modal

Extract from implementation plan:

#### Action Type
Parse the **Action Configuration** section to identify:
- Action Type: [common | config-form | confirmation | custom]
- Action Name: [e.g., New, Modify, Delete, Print, Export]

#### Form Fields Checklist (if config-form or custom with form)
| # | Field Name | Type | Label | Required | Disabled (Edit) | Status |
|---|------------|------|-------|----------|-----------------|--------|
| 1 | [name] | [type] | [label] | [Y/N] | [Y/N] | [ ] |

**Expected Count: [N]** (or N/A if common/confirmation action)

#### Custom Dialog Requirements (if custom)
| Requirement | Description | Status |
|-------------|-------------|--------|
| [requirement from plan] | [details] | [ ] |

**Note**: Common table actions (Print, Export, Filter) and simple confirmations (Delete, Toggle) don't require form field checklists.

---

## Phase 2: Sequential Implementation

**CRITICAL: Implement sections in order. Mark items complete as you go. STOP if counts don't match.**

---

# PAGE SETUP Implementation

When work unit type is **Page Setup**, implement the following sections in order.

**Page Setup Focus:**
- Search form configuration (if page has search)
- Panel layout configuration (panel IDs, types, arrangement)
- Component shell with service injection
- Routing and menu registration

**Deferred to Panel Work Unit:**
- Grid column definitions
- Context menu actions
- Panel-specific data binding

> **Note**: Grid columns and context menus are validated when the individual Panel work unit is implemented, not at Page Setup level.

## 2.1 File Structure Setup

Create the component file structure per implementation plan:

```
passage-ui/src/app/{domain}/
├── views/
│   └── {feature-name}/
│       ├── {feature-name}.component.ts           # Main component
│       ├── {feature-name}.component.html         # Template
│       └── {feature-name}.component.scss         # Styles (if needed)
├── services/
│   └── {feature-name}-api.service.ts             # API service
├── dtos/
│   ├── requests/
│   │   └── {feature-name}.request.ts             # Request DTOs
│   ├── responses/
│   │   └── {feature-name}.response.ts            # Response DTOs
│   └── view-models/
│       └── {feature-name}-table-row.view-model.ts
└── mappers/
    └── {feature-name}.mapper.ts                  # Mapper
```

**Checklist:**
- [ ] Create component directory
- [ ] Create component .ts file with @Component decorator
- [ ] Create component .html template file
- [ ] Create component .scss file (if styles needed)

## 2.2 DTOs and Types Implementation

From the **Type Definitions** section of implementation plan:

### Response DTOs
- [ ] Create response DTO interface with all fields from plan
- [ ] Add JSDoc comments for each field

### View Models
- [ ] Create view model interface for table display
- [ ] Add JSDoc comments

### Request DTOs
- [ ] Create search request DTO
- [ ] Create create request DTO (if applicable)
- [ ] Create update request DTO (if applicable)

## 2.3 Mapper Implementation

From the **Mapper Design** section:

- [ ] Create mapper class with static methods
- [ ] Implement `toTableRow()` method
- [ ] Implement `toCreateRequest()` method (if applicable)
- [ ] Implement `toUpdateRequest()` method (if applicable)

## 2.4 API Service Implementation

From the **API Integration** section:

- [ ] Create API service with @Injectable decorator
- [ ] Implement list/search method
- [ ] Implement get by ID method (if applicable)
- [ ] Implement create method (if applicable)
- [ ] Implement update method (if applicable)
- [ ] Implement delete method (if applicable)

## 2.5 Search Form Configuration (CRITICAL - COUNT VALIDATION)

From the **Search Form Configuration** section:

**IMPLEMENTATION PROCESS:**

1. Create the `searchConfig: SearchConfig` object in the component
2. For EACH field in the Search Form Checklist:
   - Add field to `searchConfig.fields` array
   - Mark [x] in checklist
3. **STOP AND VERIFY**: Count fields in implementation matches expected count

```typescript
searchConfig: SearchConfig = {
  fields: [
    // ADD EACH FIELD FROM CHECKLIST
  ],
};
```

**Validation Checkpoint:**
```
Search Fields: Implemented ___ of ___ expected
[ ] PASS - counts match
[ ] FAIL - counts do NOT match → FIX BEFORE CONTINUING
```

**If counts don't match:**
1. Re-read the implementation plan Search Form Configuration section
2. Compare checklist items against implementation
3. Identify missing/extra fields
4. Fix implementation to match plan
5. Re-validate counts before proceeding

## 2.6 Page-Level Search API Integration

**If the page has a search form, connect it to the API service here.**

This is the page-level data integration point. Individual panels receive data from this search or make their own additional calls (handled in Panel work unit).

### 2.6.1 Search Handler Implementation

- [ ] Implement `onSearch(criteria: SearchCriteria)` method in component
- [ ] Call API service search method with criteria
- [ ] Map response to view model(s) using mapper
- [ ] Provide data to panels (via component properties or TableSearchLayout)

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for search handler patterns and error handling.

### 2.6.2 Data Flow to Panels

| Panel Data Pattern | When Used | Page Setup Responsibility |
|--------------------|-----------|---------------------------|
| **Shared data** | All panels show same data | Pass search results to all panels |
| **Master-detail** | Detail panels depend on master selection | Pass master data, handle selection events |
| **Independent** | Panels have own data needs | Provide search context, panels make own calls |

> **Note**: Panel-specific data adjustments (filtering, additional API calls, transformations) are handled in the Panel work unit.

**Checklist:**
- [ ] Search handler implemented
- [ ] API service called with search criteria
- [ ] Response mapped to view model
- [ ] Data provided to panel configuration

## 2.7 Layout & Panel Configuration (CRITICAL - COUNT VALIDATION)

From the **Layout Configuration** section of implementation plan.

**Reference**: See `./docs/target-architecture/frontend-architecture/page-patterns.md` for layout type details and examples.

### 2.7.1 Implementation Process

1. **Identify layout type** from implementation plan (simple-table, two-column, two-row, tabbed, master-tabbed-detail)
2. **Create `panels: PanelConfig[]`** array following the pattern from architecture docs
3. For EACH panel in the Panel Configuration Checklist:
   - Add panel config with correct `id` and `type`
   - Mark [x] in checklist
4. **If tabbed layout**: Also configure tabs array with each tab's `id`, `label`, and `type`
5. **STOP AND VERIFY**: Counts match expected

### 2.7.2 Validation Checkpoint

```
Layout Configuration Validation:
================================
Layout Type: [type from plan]          [ ] CONFIGURED
Panels:      Implemented ___ of ___    [ ] PASS [ ] FAIL
Tabs (if tabbed): ___ of ___ expected  [ ] PASS [ ] FAIL [ ] N/A

[ ] FAIL → FIX BEFORE CONTINUING
```

**If counts don't match:**
1. Re-read the implementation plan Layout Configuration section
2. Compare checklist items against implementation
3. Identify missing/extra panels or tabs
4. Fix implementation to match plan
5. Re-validate counts before proceeding

> **Note**: Panel internals (columns, context menus) are deferred to Panel work unit. Page Setup only configures the panel structure/arrangement.

## 2.8 Component Class Implementation

Implement the main component class:

- [ ] Add component decorator with selector, templateUrl, styleUrls
- [ ] Inject required services (API service, DialogService, etc.)
- [ ] Implement ngOnInit for initial data loading
- [ ] Implement onSearch handler
- [ ] Implement onRowSelect handler (if master-detail)
- [ ] Implement refresh/reload method
## 2.9 Component Template Implementation

Implement the HTML template:

- [ ] Add TableSearchLayoutComponent with searchConfig and panels
- [ ] Bind data to panels
- [ ] Add event handlers

## 2.10 Routing Configuration

From the **Routing Configuration** section:

- [ ] Add route to domain routing module
- [ ] Set route path per implementation plan
- [ ] Add route data (title, etc.)

## 2.11 Route Registry Registration

- [ ] Add entry to `ROUTE_REGISTRY` array in `passage-ui/src/app/core/constants/route-registry.constants.ts`
- [ ] Set `legacyUri` to the legacy URI from the functional spec
- [ ] Set `angularRoute` to match the route path configured in 2.10
- [ ] Set `label`, `category`, `parentCategory` (and optionally `subCategory`) per functional spec menu placement
- [ ] Verify page appears in sidebar menu after login (requires legacy URI to exist in `/api/v1/security/menu` response)

---

# PANEL Implementation

When work unit type is **Panel**, implement the following sections in order.

**Panel Focus:**
- Panel-specific configuration (columns for tables, logic for custom)
- Data binding and selection handling
- Context menu action setup (but NOT what actions do)

**Deferred to Modal Work Unit:**
- What menu actions do (opening modals, form handling)
- Modal form field configuration
- Modal submit handlers

## 3.1 Detect Panel Type

From the implementation plan, identify the panel type:

| Panel Type | Description | Implementation Focus |
|------------|-------------|---------------------|
| **Table** | Data grid panel | Column definitions, data binding, menu actions |
| **Custom** | Custom component | Sub-component creation, custom logic |

The implementation plan specifies: `Panel Type: [table | custom]`

---

## TABLE PANEL Implementation

When panel type is **table**, implement the following:

### 3.2 Column Configuration (CRITICAL - COUNT VALIDATION)

From the **Table Configuration** section of implementation plan.

**IMPLEMENTATION PROCESS:**

1. Extract column definitions from implementation plan
2. Create the `columns: FieldConfig[]` array
3. For EACH column in the Table Columns Checklist:
   - Add column config with `name`, `label`, `type`, `width`
   - Mark [x] in checklist
4. **STOP AND VERIFY**: Column count matches expected

```typescript
columns: FieldConfig[] = [
  { name: 'id', label: 'ID', type: FieldType.TEXT, width: 80 },
  { name: 'companyName', label: 'Company Name', type: FieldType.TEXT, width: 200 },
  // ADD EACH COLUMN FROM CHECKLIST
];
```

**Validation Checkpoint:**
```
Table Columns: Implemented ___ of ___ expected
[ ] PASS - counts match
[ ] FAIL - counts do NOT match → FIX BEFORE CONTINUING
```

**If counts don't match:**
1. Re-read the implementation plan Table Configuration section
2. Compare checklist items against implementation
3. Identify missing/extra columns
4. Fix implementation to match plan
5. Re-validate counts before proceeding

### 3.3 Data Binding & Page Integration

From the **Data Flow** section of implementation plan.

**Data integration varies based on whether the panel is part of a page or standalone:**

#### 3.3.1 Panel Data Loading Patterns

| Pattern | When Used | Data Source |
|---------|-----------|-------------|
| **Parent-driven** | Master-detail pages | Parent passes data via @Input |
| **Self-loading** | Standalone panels | Panel calls API directly |
| **Config-driven** | Search-based pages | TableSearchLayout handles data loading |

#### 3.3.2 Implementation Steps

**For Config-Driven Tables (most common):**
- [ ] Panel data managed by parent TableSearchLayoutComponent
- [ ] Ensure PanelConfig.dataSource is set correctly in parent
- [ ] Data loading triggered by search form submission
- [ ] No direct API call needed in panel

**For Parent-Driven (Master-Detail):**
- [ ] Create @Input() property to receive data from parent
- [ ] Create @Input() for parent selection context (e.g., selectedMasterId)
- [ ] Implement ngOnChanges to react to input changes
- [ ] Load detail data when parent selection changes

**For Self-Loading (Standalone):**
- [ ] Implement data loading in ngOnInit
- [ ] Call API service directly
- [ ] Map response to view model

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for data loading patterns and Input/Output binding examples.

#### 3.3.3 Communication Back to Parent

- [ ] Create @Output() events for actions that affect parent state
- [ ] Emit selection changes to parent (for master-detail)
- [ ] Emit refresh requests when data is modified

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for Output event patterns.

### 3.4 Selection Handling

- [ ] Implement row selection handler
- [ ] Emit selection to parent (if master-detail pattern)
- [ ] Update local state on selection

### 3.5 Context Menu Actions (CRITICAL - COUNT VALIDATION)

From the **Context Menu Configuration** section of implementation plan.

**IMPLEMENTATION PROCESS:**

1. Extract menu actions from implementation plan
2. Create the `menuItems: MenuItem[]` array
3. For EACH action in the Context Menu Checklist:
   - Add menu item with `text` and `data` (action key)
   - Mark [x] in checklist
4. **STOP AND VERIFY**: Action count matches expected

```typescript
menuItems: MenuItem[] = [
  { text: 'New', data: 'new' },
  { text: 'Modify', data: 'modify' },
  { text: 'Delete', data: 'delete' },
  // ADD EACH ACTION FROM CHECKLIST
];
```

**Validation Checkpoint:**
```
Menu Actions: Implemented ___ of ___ expected
[ ] PASS - counts match
[ ] FAIL - counts do NOT match → FIX BEFORE CONTINUING
```

**If counts don't match:**
1. Re-read the implementation plan Context Menu Configuration section
2. Compare checklist items against implementation
3. Identify missing/extra menu actions
4. Fix implementation to match plan
5. Re-validate counts before proceeding

### 3.6 Menu Action Handler (Setup Only)

Setup the menu action handler shell, but **defer modal implementation** to Modal work unit:

- [ ] Create `onMenuAction(action: string)` method
- [ ] Add switch/case for each action in checklist
- [ ] Leave TODO comments for modal opening (deferred to Modal work unit)

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for menu action handler patterns.

> **Note**: The actual modal opening and form handling is implemented when the Modal work unit is executed.

---

## CUSTOM PANEL Implementation

When panel type is **custom**, implement the following:

### 3.7 Sub-Component Creation

From the **Component Design** section of implementation plan:

- [ ] Create sub-component directory
- [ ] Create sub-component .ts file
- [ ] Create sub-component .html template
- [ ] Create sub-component .scss (if needed)

```
passage-ui/src/app/{domain}/views/{page}/components/
└── {panel-name}/
    ├── {panel-name}.component.ts
    ├── {panel-name}.component.html
    └── {panel-name}.component.scss
```

### 3.8 Component Logic

From the **Component Logic** section of implementation plan:

- [ ] Implement @Input() properties for data from parent
- [ ] Implement @Output() events for actions
- [ ] Implement component logic per implementation plan
- [ ] Add required services via dependency injection

### 3.9 Integration with Parent

- [ ] Add component to parent template
- [ ] Bind inputs from parent state
- [ ] Handle output events in parent

---

## Panel Validation Summary

**Before marking Panel implementation complete:**

### For Table Panels
```
Panel Validation Summary (Table):
=================================
Column Definitions:  Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
Menu Actions:        Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
Data Integration:
  - Data Loading Pattern: [config-driven | parent-driven | self-loading]
  - Data Binding:         [ ] CONFIGURED
  - Parent Communication: [ ] CONFIGURED (if master-detail)
Selection Handling:      [ ] CONFIGURED

(Modal form handling validated in Modal work unit)

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### For Custom Panels
```
Panel Validation Summary (Custom):
==================================
Sub-Component Files: [ ] CREATED
Component Logic:     [ ] IMPLEMENTED per plan
Parent Integration:  [ ] CONFIGURED
Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

---

# MODAL Implementation

When work unit type is **Modal**, implement the following sections in order.

**Modal Focus:**
- Connect menu actions from Panel to appropriate dialog type
- Implement all modal logic (form handling, validation, API calls)
- Handle API integrations (create, update, delete)
- Communicate results back to parent panel for refresh

**Configuration-First Approach:**
Use configuration-driven dialogs whenever possible. Only create custom dialog components when config-driven options cannot meet requirements.

## 4.1 Detect Action Type

From the implementation plan, identify the action type to determine implementation approach:

| Action Type | Implementation | When to Use |
|------------|----------------|-------------|
| **Common Table Actions** | `TableMenuService` | Print, Export, Filter |
| **Simple CRUD** | `openConfigForm()` | Standard form with 5-15 fields |
| **Confirmation** | `dialogService.confirm()` | Delete, toggle, simple yes/no |
| **Complex Form** | Custom Dialog Component | Multi-step wizard, dynamic fields, complex validation |

The implementation plan specifies: `Action Type: [common | config-form | confirmation | custom]`

---

## COMMON TABLE ACTIONS Implementation

For **Print**, **Export**, **Filter** actions:

### 4.2 Common Actions Setup

These actions are handled by the `TableMenuService` and don't require custom implementation.

- [ ] Import `TableMenuService` in panel component
- [ ] Use `createStandardTableMenu()` to add menu items
- [ ] Delegate to `TableMenuService.handleMenuClick()` in menu handler

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for TableMenuService pattern.

**No additional work required** - the service handles Print, Export, and Filter automatically.

---

## CONFIG-DRIVEN FORM Implementation

For **Simple CRUD** actions (New, Modify with standard form fields):

### 4.3 Form Fields Configuration (CRITICAL - COUNT VALIDATION)

From the **Form Configuration** section of implementation plan.

**IMPLEMENTATION PROCESS:**

1. Extract form fields from implementation plan
2. Create `FieldConfig[]` array for the dialog
3. For EACH field in the Form Fields Checklist:
   - Add field config with correct type, name, label, validation
   - Mark [x] in checklist
4. **STOP AND VERIFY**: Field count matches expected

```typescript
formFields: FieldConfig[] = [
  { type: FieldType.TEXT, name: 'name', label: 'Name', required: true },
  { type: FieldType.LOOKUP, name: 'company', label: 'Company', lookupKey: LookupKey.COMPANY },
  // ADD EACH FIELD FROM CHECKLIST
];
```

**Validation Checkpoint:**
```
Form Fields: Implemented ___ of ___ expected
[ ] PASS - counts match
[ ] FAIL - counts do NOT match → FIX BEFORE CONTINUING
```

**If counts don't match:**
1. Re-read the implementation plan Form Configuration section
2. Compare checklist items against implementation
3. Identify missing/extra form fields
4. Fix implementation to match plan
5. Re-validate counts before proceeding

### 4.4 Mode-Based Form Fields

If form is used for both Create and Edit:

- [ ] Create `getFormFields(mode: 'new' | 'edit', data?: Entity)` function
- [ ] Add conditional `disabled` for fields readonly in edit mode
- [ ] Add conditional `defaultValue` for pre-populating edit data

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for mode-based form fields pattern.

### 4.5 Dialog Opening

- [ ] Implement dialog opening method for each action
- [ ] Use `dialogService.openConfigForm()` with:
  - `title`: Dialog title
  - `fields`: Form field configuration
  - `onSubmit`: API call function
  - `width`: Dialog width (optional)
  - `data`: Pre-populated data for edit mode

### 4.6 API Integration

- [ ] Call appropriate API service method in `onSubmit`
- [ ] Handle success response (close dialog, show success message)
- [ ] Handle error response (show error, keep dialog open)

### 4.7 Parent Panel Refresh

- [ ] On success, emit event to parent OR call parent refresh method
- [ ] Clear panel selection if applicable
- [ ] Reload panel data

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for CRUD operations pattern.

---

## CONFIRMATION DIALOG Implementation

For **Delete**, **Toggle**, and simple **Yes/No** actions:

### 4.8 Confirmation Dialog

- [ ] Use `dialogService.confirm(message, title)` for confirmation
- [ ] Handle confirmed response (proceed with action)
- [ ] Handle cancelled response (do nothing)

For Delete actions:
- [ ] Confirm with user before deleting
- [ ] Call API delete method on confirmation
- [ ] Refresh parent panel on success
- [ ] Clear selection

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for delete operation pattern.

---

## CUSTOM DIALOG COMPONENT Implementation

For **Complex Forms**, **Wizards**, and actions requiring **Custom UI**:

### 4.9 When to Use Custom Dialog

Use custom dialog component when:
- Multi-step wizard required
- Dynamic field visibility based on user input
- Complex cross-field validation
- Non-form content (embedded tables, file upload, preview)
- Specialized interactions

### 4.10 Custom Dialog Component Creation

- [ ] Create dialog component directory
- [ ] Create dialog component .ts file
- [ ] Create dialog component .html template
- [ ] Create dialog component .scss (if needed)

```
passage-ui/src/app/{domain}/components/{action-name}-dialog/
├── {action-name}-dialog.component.ts
├── {action-name}-dialog.component.html
└── {action-name}-dialog.component.scss
```

### 4.11 Custom Dialog Implementation

- [ ] Inject `DialogRef` for closing dialog
- [ ] Create form with `FormBuilder` if form-based
- [ ] Implement all business logic per implementation plan
- [ ] Implement validation rules
- [ ] Return result object with `{ action: 'submit' | 'cancel', data?: any }`

### 4.12 Custom Dialog Opening

- [ ] Open with Kendo `DialogService.open()`
- [ ] Pass data via component instance properties
- [ ] Handle result in subscription

### 4.13 API Integration (Custom)

- [ ] Call API service methods for data operations
- [ ] Handle loading states
- [ ] Handle success/error responses

### 4.14 Parent Panel Integration

- [ ] Emit refresh event to parent on success
- [ ] Close dialog and return result
- [ ] Parent handles refresh and selection clearing

> **Reference**: See [implementation-guides.md](./docs/target-architecture/frontend-architecture/implementation-guides.md) for custom dialog component pattern.

---

## Modal Validation Summary

**Before marking Modal implementation complete:**

### For Common Table Actions
```
Modal Validation Summary (Common Actions):
==========================================
TableMenuService Imported:  [ ] YES
createStandardTableMenu():  [ ] USED
handleMenuClick() Handler:  [ ] IMPLEMENTED

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### For Config-Driven Forms
```
Modal Validation Summary (Config Form):
=======================================
Form Fields:            Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
Mode-Based Fields:      [ ] IMPLEMENTED (if Create + Edit)
Dialog Opening:         [ ] IMPLEMENTED
API Integration:        [ ] IMPLEMENTED
Parent Refresh:         [ ] CONFIGURED
Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### For Confirmation Dialogs
```
Modal Validation Summary (Confirmation):
========================================
confirm() Called:       [ ] YES
API Call on Confirm:    [ ] IMPLEMENTED
Parent Refresh:         [ ] CONFIGURED
Selection Cleared:      [ ] YES

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### For Custom Dialog Components
```
Modal Validation Summary (Custom Dialog):
=========================================
Component Files Created: [ ] .ts, .html, .scss
Business Logic:         [ ] IMPLEMENTED per plan
Form Fields (if form):  Implemented ___ of ___ expected  [ ] PASS [ ] FAIL [ ] N/A
Validation Rules:       [ ] IMPLEMENTED
API Integration:        [ ] IMPLEMENTED
Result Return:          [ ] { action, data } pattern
Parent Integration:     [ ] CONFIGURED

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

---

## Phase 3: Validation Summary

**Before marking implementation complete, verify ALL counts match:**

### Page Setup Validation
```
Configuration Validation Summary (Page Setup):
==============================================
Layout Type:          [type]                           [ ] CONFIGURED
Search Form Fields:   Implemented ___ of ___ expected  [ ] PASS [ ] FAIL [ ] N/A (no search)
Search API Integration:
  - Search Handler:   [ ] IMPLEMENTED
  - API Service Call: [ ] CONFIGURED
  - Data to Panels:   [ ] CONFIGURED
Panel Configurations: Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
Tabs (if tabbed):     Implemented ___ of ___ expected  [ ] PASS [ ] FAIL [ ] N/A
(Grid columns and context menus validated in Panel work unit)

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### Panel Validation (Table)
```
Configuration Validation Summary (Table Panel):
===============================================
Column Definitions:  Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
Menu Actions:        Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
Data Integration:
  - Data Loading Pattern: [config-driven | parent-driven | self-loading]
  - Data Binding:         [ ] CONFIGURED
  - Parent Communication: [ ] CONFIGURED (if master-detail)
Selection Handling:      [ ] CONFIGURED

(Modal form handling validated in Modal work unit)

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### Panel Validation (Custom)
```
Configuration Validation Summary (Custom Panel):
================================================
Sub-Component Files: [ ] CREATED
Component Logic:     [ ] IMPLEMENTED per implementation plan
Parent Integration:  [ ] CONFIGURED

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

### Modal Validation
```
Configuration Validation Summary (Modal):
=========================================
Action Type: [common | config-form | confirmation | custom]

For Common Actions:
  - TableMenuService:   [ ] CONFIGURED

For Config-Form:
  - Form Fields:        Implemented ___ of ___ expected  [ ] PASS [ ] FAIL
  - Mode-Based Fields:  [ ] IMPLEMENTED (if Create + Edit)
  - API Integration:    [ ] IMPLEMENTED
  - Parent Refresh:     [ ] CONFIGURED

For Confirmation:
  - confirm() Dialog:   [ ] IMPLEMENTED
  - API Integration:    [ ] IMPLEMENTED
  - Parent Refresh:     [ ] CONFIGURED

For Custom Dialog:
  - Component Files:    [ ] CREATED
  - Form Fields (if any): ___ of ___ expected  [ ] PASS [ ] FAIL [ ] N/A
  - Business Logic:     [ ] IMPLEMENTED per plan
  - API Integration:    [ ] IMPLEMENTED
  - Parent Refresh:     [ ] CONFIGURED

Overall Status: [ ] VALIDATED [ ] NOT VALIDATED
```

**CRITICAL: If ANY count mismatches exist, DO NOT mark implementation complete. Fix first.**

---

## Phase 4: Task List Update

After all implementation is complete and validated:

1. Update task-list.md with [x] for completed items
2. Verify all checkboxed items in task list are marked complete

---

## Critical Guidelines

### Sequential Implementation
- UI components often live in single files
- Implement in order: DTOs → Mappers → Services → Configurations → Component → Template
- Do NOT parallelize within a single component file

### Count Validation is MANDATORY
- Extract expected counts from implementation plan
- Track implemented counts as you go
- STOP and fix if counts don't match before proceeding

### Field Type Reference

When implementing search form or form fields, use correct FieldType:

| Visual/Description | FieldType |
|-------------------|-----------|
| Plain text input | `FieldType.TEXT` |
| Input with `...` button (modal lookup) | `FieldType.LOOKUP` |
| Dropdown with options | `FieldType.DROPDOWN` |
| Date picker | `FieldType.DATE` |
| Checkbox | `FieldType.CHECKBOX` |
| Numeric input | `FieldType.NUMBER` |

### Core Components to Use

| Purpose | Core Component |
|---------|---------------|
| Page layout with search | `TableSearchLayoutComponent` |
| Search form | `SearchFormComponent` |
| Data table | `DataTableComponent` |
| Form dialog | `ConfigurableFormDialogComponent` |
| Dialogs (confirm, alert) | `AppDialogService` |

---

## Success Criteria

### For Page Setup

**Implementation is complete when:**
- [ ] All files created per implementation plan file structure
- [ ] All DTOs/ViewModels/Mappers implemented
- [ ] API service implemented with all methods
- [ ] **Search form configuration matches plan (COUNT VALIDATED)**
- [ ] **Search API integration implemented:**
  - [ ] Search handler connected to API service
  - [ ] Response mapped to view model(s)
  - [ ] Data provided to panels
- [ ] **Panel configuration matches plan (COUNT VALIDATED)**
- [ ] Component class implemented with all handlers
- [ ] Template implemented with proper bindings
- [ ] Routing configured
- [ ] All task-list.md items marked complete

> **Note**: Grid columns and context menus are NOT validated at Page Setup - those are validated in Panel work unit.

### For Panel

**Implementation is complete when:**
- [ ] Panel component/configuration implemented
- [ ] **Grid columns match plan (COUNT VALIDATED)**
- [ ] **Context menu actions match plan (COUNT VALIDATED)**
- [ ] **Data integration configured:**
  - [ ] Data loading pattern identified (config-driven/parent-driven/self-loading)
  - [ ] Data binding implemented
  - [ ] Parent communication configured (if master-detail)
- [ ] Selection handling implemented
- [ ] All task-list.md items marked complete

### For Modal

**Implementation is complete when (by action type):**

**Common Table Actions (Print, Export, Filter):**
- [ ] TableMenuService imported and configured
- [ ] createStandardTableMenu() used
- [ ] handleMenuClick() delegating to service
- [ ] All task-list.md items marked complete

**Config-Driven Forms (Simple CRUD):**
- [ ] **Form fields match plan (COUNT VALIDATED)**
- [ ] Mode-based form fields (if Create + Edit)
- [ ] openConfigForm() implemented
- [ ] API integration implemented (onSubmit)
- [ ] Parent panel refresh configured
- [ ] All task-list.md items marked complete

**Confirmation Dialogs (Delete, Toggle):**
- [ ] dialogService.confirm() implemented
- [ ] API call on confirmation
- [ ] Parent panel refresh on success
- [ ] Selection cleared on success
- [ ] All task-list.md items marked complete

**Custom Dialog Components:**
- [ ] Dialog component files created (.ts, .html, .scss)
- [ ] **Form fields match plan (COUNT VALIDATED)** (if form-based)
- [ ] Business logic implemented per implementation plan
- [ ] Validation rules implemented
- [ ] API integration implemented
- [ ] Result return pattern ({ action, data })
- [ ] Parent panel integration configured
- [ ] All task-list.md items marked complete

---

**End of Command Specification**
