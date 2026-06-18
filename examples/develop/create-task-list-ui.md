---
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --from-stdin
            --log
            --file-pattern "*task-list*"
            --contains '# Task List'
            --contains '## Overview'
            --contains '## Task Hierarchy'
            --contains '## Configuration Summary'
            --contains '## Dependency Matrix'
            --contains '## Parallelization Opportunities'
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*task-list*"
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*task-list*"
            --contains '# Task List'
            --contains '## Overview'
            --contains '## Task Hierarchy'
            --contains '## Configuration Summary'
            --contains '## Dependency Matrix'
            --contains '## Parallelization Opportunities'
---

# Create Task List - UI

Create a comprehensive, actionable task list from a technical implementation plan for UI features with **work unit type awareness** and **configuration-specific task generation**.

## Usage

```
/create-task-list-ui key: [key]
```

**Examples:**
```
/create-task-list-ui key: 2105-infrastructure-company-company-maintenance
```

```
/create-task-list-ui key: 2046-infrastructure-company-ba-request-grid
```

## Input

The command receives an inventory item JSON payload:

```json
{
  "key": "2105-infrastructure-company-company-maintenance",
  "name": "Company Maintenance Page",
  "location": "./legacy/portal/src/app/company/company-maintenance/company-maintenance.component.ts",
  "type": "ui-features",
  "notes": [
    "Angular component with Kendo UI",
    "Calls GET /api/v1/company/companies",
    "Uses Angular services for data fetching"
  ]
}
```

Use `key` to locate the entry point directory:
```
./docs/entry-points/ui-features/{key}/
```

## What This Command Does

This command analyzes a technical implementation plan for a UI feature and generates a **work unit type-specific** task list that:

- **Detects** the work unit type (Page Setup, Panel, Modal) from the implementation plan
- **Extracts** configuration details with expected counts
- **Generates** type-specific tasks focused on that work unit's scope
- **Includes** configuration details and counts in task descriptions
- **Notes** deferred work that belongs to other work units

## Input Structure

The entry point directory at `./docs/entry-points/ui-features/{key}/` contains:

```
{entry-point-directory}/
├── metadata.json                    # Entry point metadata
├── functional-spec.md               # Functional specification
├── implementation-plan.md                # Technical implementation plan (INPUT)
└── api-dependencies.json            # API dependencies (if applicable)
```

**Required files**:
- `implementation-plan.md` - Created by `/create-technical-plan-ui` command

## Output Structure

The command creates the following file in the **same directory**:

```
{entry-point-directory}/
├── ... (existing files)
└── task-list.md                # Work unit type-specific task list with checkboxes
```

---

## Phase 0: Detect Work Unit Type (CRITICAL)

### 0.1 Read Technical Plan

1. **Read implementation-plan.md completely** from the entry point directory
2. **Extract Work Unit Type** from the implementation plan header:
   ```markdown
   > **Work Unit Type**: [Page Setup | Panel | Modal]
   ```

### 0.2 Work Unit Type Detection Logic

If not explicitly stated in header, detect from key pattern:

| Pattern | Work Unit Type | Example Key |
|---------|----------------|-------------|
| Key ends with page name (no suffix) | **Page Setup** | `2105-infrastructure-company-company-maintenance` |
| Key has one additional segment after page name | **Panel** | `2105-infrastructure-company-company-maintenance-contacts-panel` |
| Key has action suffix | **Modal** | `2105-infrastructure-company-company-maintenance-modify` |

**Action suffixes for Modal detection**: `-modify`, `-new`, `-delete`, `-attach-document`, `-view-attachment`

### 0.3 Set Task Generation Focus

Based on work unit type, determine what to include and exclude:

| Work Unit Type | Task Categories to Include | Does NOT Include |
|----------------|---------------------------|------------------|
| **Page Setup** | File structure, DTOs, Mappers, API Service, SearchConfig, Layout/PanelConfig, Routing, Menu | Grid columns, context menus, form fields |
| **Panel** | Panel component, GridColumn config, MenuItem config, Data binding, Selection handling | Search form, routing, modal forms |
| **Modal** | Dialog/Form fields, Validation, Submit handler, API integration, Parent communication | Search form, routing, grid columns |

---

## Phase 1: Extract Configurations from Technical Plan

### 1.1 For Page Setup

Extract the following from implementation plan sections:

#### Search Configuration
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Fields | "Search Form Configuration" | Field names, types, required status |
| Advanced Fields | "Search Form Configuration" | Field names (if any) |
| Layout | "Search Form Configuration" | FLEX_WRAP or GRID |

**Record**: Field count + list of (name, type) pairs

#### Panel Configuration
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Panels | "Layout Configuration" or "PanelConfig" | Panel IDs, types (table/custom/tabs) |
| Layout Type | "Layout Configuration" | simple-table, two-column, tabbed, etc. |

**Record**: Panel count + list of (id, type) pairs

#### Tab Configuration (if tabbed layout)
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Tabs | "Tab Configuration" | Tab IDs, labels, panel types |

**Record**: Tab count + list of (id, label, type) triples

### 1.2 For Panel

Extract the following from implementation plan sections:

#### Panel Type Detection
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Panel Type | "Panel Type" or inferred | table, custom, tabbed |

#### Table Configuration (if table panel)
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Columns | "Table Configuration" or "GridColumn" | Field names, headers, types, widths |

**Record**: Column count + list of (field, header, width) triples

#### Context Menu Configuration
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Menu Items | "Context Menu Configuration" or "MenuItem" | Action text, action data/key |

**Record**: Action count + list of (text, data) pairs

### 1.3 For Modal

Extract the following from implementation plan sections:

#### Action Type Detection
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Action Type | "Action Configuration" | common, config-form, confirmation, custom |
| Action Name | "Action Configuration" | New, Modify, Delete, Print, etc. |

#### Form Fields (if config-form or custom with form)
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Fields | "Form Configuration" | Names, types, labels, required, disabled |

**Record**: Field count + list of (name, type, label, required, disabled) tuples

#### Validation Rules (if applicable)
| Field | Source Section | Data to Extract |
|-------|----------------|-----------------|
| Validations | "Validation" section | Rule descriptions per field |

---

## Phase 2: Generate Work Unit Type-Specific Task List

### For Page Setup - Use Page Setup Task Template

### For Panel - Use Panel Task Template

### For Modal - Use Modal Task Template

---

## Task List Format

The `task-list.md` file uses a hierarchical outline format:

```markdown
# Task List: [Feature Name]

> **Source**: [path to implementation-plan.md]
> **Generated**: [date]
> **Work Unit Type**: [Page Setup | Panel | Modal]
> **Total Tasks**: [count of leaf-level checkboxed items]

## Configuration Summary

[Extracted configuration details with counts]

## Task Hierarchy

1. Top-Level Phase or Component
1.1. Mid-Level Component or Area
[ ] 1.1.1. Specific actionable task with configuration details
[ ] 1.1.2. Another specific actionable task
```

### Formatting Rules

1. **Top-level items** (1., 2., 3.): Major phases or components (NO checkboxes)
2. **Mid-level items** (1.1., 1.2., 2.1.): Sub-components or areas (NO checkboxes)
3. **Leaf-level items** (1.1.1., 1.1.2.): Actual tasks with `[ ]` checkboxes
4. **Configuration details**: Include field/column/action lists in relevant tasks
5. **Expected counts**: Include `(Expected: N from [section])` where applicable

---

## PAGE SETUP Task Template

Use this template when work unit type is **Page Setup**.

```markdown
# Task List: [Feature Name]

> **Source**: [path to implementation-plan.md]
> **Generated**: [date]
> **Work Unit Type**: Page Setup
> **Total Tasks**: [count]

## Configuration Summary

### Search Configuration
- **Field Count**: [N] fields
- **Fields**: [field1] ([type1]), [field2] ([type2]), ...
- **Advanced Fields**: [N] fields (or None)
- **Layout**: [FLEX_WRAP | GRID]

### Panel Configuration
- **Panel Count**: [N] panels
- **Panels**: [panel1-id] ([type1]), [panel2-id] ([type2]), ...
- **Layout Type**: [simple-table | two-column | two-row | tabbed | master-tabbed-detail]

### Tab Configuration (if tabbed)
- **Tab Count**: [N] tabs
- **Tabs**: [tab1-id]: "[label1]" ([type1]), ...

---

## Task Hierarchy

1. Project Setup
1.1. File Structure
[ ] 1.1.1. Create directory: passage-ui/src/app/{domain}/views/{feature}/
[ ] 1.1.2. Create component file: {feature}.component.ts
[ ] 1.1.3. Create component test file: {feature}.component.spec.ts
[ ] 1.1.4. Create component template: {feature}.component.html
[ ] 1.1.5. Create component styles: {feature}.component.scss (if needed)

1.2. DTOs and Types
[ ] 1.2.1. Create response DTO: {feature}.response.ts with fields from API spec
[ ] 1.2.2. Create view model: {feature}-table-row.view-model.ts
[ ] 1.2.3. Create search request DTO: {feature}-search.request.ts

1.3. Mapper
[ ] 1.3.1. Create mapper: {feature}.mapper.ts
[ ] 1.3.2. Implement toTableRow() method
[ ] 1.3.3. Create mapper tests: {feature}.mapper.spec.ts

1.4. API Service
[ ] 1.4.1. Create API service: {feature}-api.service.ts
[ ] 1.4.2. Implement search() method with HttpClient
[ ] 1.4.3. Create service tests: {feature}-api.service.spec.ts

2. Search Form Configuration
2.1. SearchConfig
[ ] 2.1.1. Define searchConfig: SearchConfig object
[ ] 2.1.2. Configure [N] search fields (Expected: [N] from "Search Form Configuration"):
         - [field1] ([type1])
         - [field2] ([type2])
         - [field3] ([type3])
         - ...
[ ] 2.1.3. Configure advancedFields: [N] fields (or skip if none)
[ ] 2.1.4. Set layout: [FLEX_WRAP | GRID]
[ ] 2.1.5. Configure buttonLabel (if custom)

2.2. Search API Integration
[ ] 2.2.1. Implement onSearch(criteria) handler
[ ] 2.2.2. Connect to API service search method
[ ] 2.2.3. Map response to view model(s)
[ ] 2.2.4. Provide data to panels

3. Layout and Panel Configuration
3.1. Layout Type: [layout-type]
[ ] 3.1.1. Implement [layout-type] layout pattern
[ ] 3.1.2. Configure panel arrangement

3.2. PanelConfig Array
[ ] 3.2.1. Define panelConfigs: PanelConfig[] with [N] panels (Expected: [N] from "Layout Configuration"):
         - [panel1-id] ([panel1-type])
         - [panel2-id] ([panel2-type])
         - ...
[ ] 3.2.2. Configure panel data sources
[ ] 3.2.3. Wire panel event handlers

3.3. Tab Configuration (if tabbed layout)
[ ] 3.3.1. Configure [N] tabs (Expected: [N] from "Tab Configuration"):
         - [tab1-id]: "[tab1-label]" ([tab1-type])
         - [tab2-id]: "[tab2-label]" ([tab2-type])
         - ...

4. Routing and Menu
4.1. Route Configuration
[ ] 4.1.1. Add route to domain routing module
[ ] 4.1.2. Set route path: [route-path]
[ ] 4.1.3. Configure route data (title, permissions)

4.2. Route Registry Registration
[ ] 4.2.1. Add entry to `passage-ui/src/app/core/constants/route-registry.constants.ts`
[ ] 4.2.2. Set `legacyUri` to the legacy URI path from the functional spec (e.g., `modules/company/contacts/views/company_contacts`)
[ ] 4.2.3. Set `angularRoute` to match the route path from task 4.1.2
[ ] 4.2.4. Set `label`, `category`, and `parentCategory` per the functional spec's menu placement

5. Component Implementation
5.1. Component Class
[ ] 5.1.1. Add @Component decorator with selector, templateUrl
[ ] 5.1.2. Inject required services (API service, DialogService)
[ ] 5.1.3. Implement ngOnInit for initial setup
[ ] 5.1.4. Implement refresh/reload method

5.2. Component Template
[ ] 5.2.1. Add TableSearchLayoutComponent
[ ] 5.2.2. Bind searchConfig to search form
[ ] 5.2.3. Bind panelConfigs to panels
[ ] 5.2.4. Add event handlers

6. Testing
6.1. Component Tests
[ ] 6.1.1. Test component creation
[ ] 6.1.2. Test ngOnInit behavior
[ ] 6.1.3. Test onSearch handler
[ ] 6.1.4. Test data binding

---

## Dependency Matrix

| Task Group | Depends On | Blocks | Can Parallelize With |
|------------|------------|--------|---------------------|
| 1. File Structure | None | DTOs, Mapper | None |
| 2. DTOs/Types | File Structure | Mapper, API Service | None |
| 3. Mapper | DTOs | API Service, Tests | None |
| 4. API Service | Mapper | SearchConfig, Tests | None |
| 5. SearchConfig | API Service | PanelConfig | None |
| 6. PanelConfig | SearchConfig | Component Impl | None |
| 7. Routing/Menu | File Structure | Component Impl | Phases 2-6 |
| 8. Component Impl | PanelConfig, Routing | Testing | None |
| 9. Testing | Component Impl | None | None |

## Parallelization Opportunities

**Can run in parallel:**
- Routing/Menu registration can run parallel with DTOs through PanelConfig
- Tests for each component can start as that component completes
- Mapper tests can run while API Service is being built

**Must be sequential:**
- DTOs → Mapper → API Service → SearchConfig → PanelConfig → Component

**Sub-agent dispatch for Page Setup:**
- Wave 1: File structure + Routing setup (parallel)
- Wave 2: DTOs + Types
- Wave 3: Mapper + Mapper tests (parallel)
- Wave 4: API Service + Service tests (parallel)
- Wave 5: SearchConfig + PanelConfig
- Wave 6: Component implementation + Component tests

---

> **Note**: Grid columns and context menus are implemented in Panel work units.
> **Note**: Form fields and modals are implemented in Modal work units.
```

---

## PANEL Task Template

Use this template when work unit type is **Panel**.

```markdown
# Task List: [Feature Name] - [Panel Name]

> **Source**: [path to implementation-plan.md]
> **Generated**: [date]
> **Work Unit Type**: Panel
> **Panel Type**: [table | custom | tabbed]
> **Total Tasks**: [count]

## Configuration Summary

### Panel Type: [table | custom | tabbed]

### Table Configuration (if table panel)
- **Column Count**: [N] columns
- **Columns**: [field1]: "[header1]" ([width1]px), ...

### Context Menu Configuration
- **Action Count**: [N] actions
- **Actions**: [text1] ([data1]), [text2] ([data2]), ...

---

## Task Hierarchy

1. Panel Setup
1.1. Panel Identification
[ ] 1.1.1. Identify panel location in parent component
[ ] 1.1.2. Read parent page configuration

2. Table Panel Configuration (if table panel)
2.1. GridColumn Configuration
[ ] 2.1.1. Define columns: GridColumn[] with [N] columns (Expected: [N] from "Table Configuration"):
         - [field1]: "[header1]" ([width1]px)
         - [field2]: "[header2]" ([width2]px)
         - [field3]: "[header3]" ([width3]px)
         - ...
[ ] 2.1.2. Configure column types and formats
[ ] 2.1.3. Configure sortable/filterable options

2.2. MenuItem Configuration
[ ] 2.2.1. Define menuItems: MenuItem[] with [N] actions (Expected: [N] from "Context Menu Configuration"):
         - [text1]: [data1]
         - [text2]: [data2]
         - ...
[ ] 2.2.2. Add separators where needed
[ ] 2.2.3. Configure disabled states (if any)

2.3. Menu Action Handler
[ ] 2.3.1. Implement onMenuAction(action) handler
[ ] 2.3.2. Add case for each action:
         - [action1]: [TODO: implement in Modal work unit]
         - [action2]: [TODO: implement in Modal work unit]
         - ...

3. Data Binding
3.1. Data Loading Pattern: [config-driven | parent-driven | self-loading]
[ ] 3.1.1. Implement data binding for [pattern]
[ ] 3.1.2. Configure dataSource property

3.2. Selection Handling
[ ] 3.2.1. Implement row selection handler
[ ] 3.2.2. Configure selection mode (single/multiple)
[ ] 3.2.3. Emit selection to parent (if master-detail)

3.3. Parent Communication
[ ] 3.3.1. Define @Input() properties (if parent-driven)
[ ] 3.3.2. Define @Output() events for parent notification
[ ] 3.3.3. Implement ngOnChanges (if needed)

4. Custom Panel Configuration (if custom panel)
4.1. Component Creation
[ ] 4.1.1. Create panel component directory
[ ] 4.1.2. Create panel component files (.ts, .spec.ts, .html, .scss)

4.2. Component Implementation
[ ] 4.2.1. Define @Input() properties
[ ] 4.2.2. Define @Output() events
[ ] 4.2.3. Implement component logic per plan
[ ] 4.2.4. Inject required services

4.3. Integration
[ ] 4.3.1. Add component to parent template
[ ] 4.3.2. Bind inputs from parent
[ ] 4.3.3. Handle outputs in parent

5. Testing
5.1. Panel Tests
[ ] 5.1.1. Test column configuration renders correctly
[ ] 5.1.2. Test menu actions trigger handlers
[ ] 5.1.3. Test data binding
[ ] 5.1.4. Test selection handling

---

## Dependency Matrix

| Task Group | Depends On | Blocks | Can Parallelize With |
|------------|------------|--------|---------------------|
| 1. Panel Setup | Parent Page Setup | GridColumn, MenuItem | None |
| 2. GridColumn Config | Panel Setup | Menu Handler | None |
| 3. MenuItem Config | Panel Setup | Menu Handler | GridColumn Config |
| 4. Menu Handler | GridColumn, MenuItem | Data Binding | None |
| 5. Data Binding | Menu Handler | Selection | None |
| 6. Selection Handling | Data Binding | Parent Comm | None |
| 7. Parent Communication | Selection | Testing | None |
| 8. Custom Panel (if applicable) | Panel Setup | Integration | GridColumn, MenuItem |
| 9. Testing | All implementation | None | None |

## Parallelization Opportunities

**Can run in parallel:**
- GridColumn config and MenuItem config can run in parallel
- Custom panel creation can run parallel with table config
- Tests can start after each component completes

**Must be sequential:**
- Panel Setup → Config → Handler → Data Binding → Selection → Parent Comm

**Sub-agent dispatch for Panel:**
- Wave 1: Panel setup + identification
- Wave 2: GridColumn config + MenuItem config (parallel)
- Wave 3: Menu action handler
- Wave 4: Data binding + Selection handling
- Wave 5: Parent communication + Testing (parallel)

---

> **Note**: Modal dialogs triggered by menu actions are implemented in Modal work units.
```

---

## MODAL Task Template

Use this template when work unit type is **Modal**.

```markdown
# Task List: [Feature Name] - [Action Name] Modal

> **Source**: [path to implementation-plan.md]
> **Generated**: [date]
> **Work Unit Type**: Modal
> **Action Type**: [common | config-form | confirmation | custom]
> **Total Tasks**: [count]

## Configuration Summary

### Action Configuration
- **Action Type**: [common | config-form | confirmation | custom]
- **Action Name**: [New | Modify | Delete | Print | Export | ...]

### Form Fields (if config-form or custom)
- **Field Count**: [N] fields
- **Fields**:
  - [name1]: [type1] ("[label1]") [required: Y/N] [disabled in edit: Y/N]
  - [name2]: [type2] ("[label2]") [required: Y/N] [disabled in edit: Y/N]
  - ...

---

## Task Hierarchy

1. Action Type Detection
1.1. Action Type: [common | config-form | confirmation | custom]
[ ] 1.1.1. Identify action type from implementation plan
[ ] 1.1.2. Read parent panel configuration

2. Common Table Actions (if action type = common)
2.1. TableMenuService Integration
[ ] 2.1.1. Import TableMenuService in parent panel
[ ] 2.1.2. Use createStandardTableMenu() for menu items
[ ] 2.1.3. Delegate to TableMenuService.handleMenuClick()
[ ] 2.1.4. No additional implementation needed

3. Config-Form Actions (if action type = config-form)
3.1. Form Fields Configuration
[ ] 3.1.1. Define formFields: FieldConfig[] with [N] fields (Expected: [N] from "Form Configuration"):
         - [name1]: [type1] ("[label1]") [required: Y/N]
         - [name2]: [type2] ("[label2]") [required: Y/N]
         - ...
[ ] 3.1.2. Configure LookupKey for LOOKUP fields: [list]
[ ] 3.1.3. Configure DropdownKey for DROPDOWN fields: [list]

3.2. Mode-Based Fields (if Create + Edit)
[ ] 3.2.1. Create getFormFields(mode: 'new' | 'edit', data?) function
[ ] 3.2.2. Add disabled property for edit-only readonly fields: [list]
[ ] 3.2.3. Add defaultValue for pre-population

3.3. Dialog Opening
[ ] 3.3.1. Implement openNew() method using dialogService.openConfigForm()
[ ] 3.3.2. Implement openEdit(row) method using dialogService.openConfigForm()
[ ] 3.3.3. Configure dialog title, width, fields

3.4. API Integration
[ ] 3.4.1. Implement onSubmit handler for create
[ ] 3.4.2. Implement onSubmit handler for update
[ ] 3.4.3. Handle success: close dialog, show toast
[ ] 3.4.4. Handle error: show error, keep dialog open

3.5. Parent Panel Refresh
[ ] 3.5.1. Emit refresh event to parent on success
[ ] 3.5.2. Clear selection if applicable

4. Confirmation Actions (if action type = confirmation)
4.1. Confirmation Dialog
[ ] 4.1.1. Implement delete confirmation using dialogService.confirm()
[ ] 4.1.2. Configure confirmation message and title

4.2. API Integration
[ ] 4.2.1. Call API delete method on confirmation
[ ] 4.2.2. Handle success: refresh parent, clear selection
[ ] 4.2.3. Handle error: show error toast

5. Custom Dialog (if action type = custom)
5.1. Dialog Component Creation
[ ] 5.1.1. Create dialog directory: {action-name}-dialog/
[ ] 5.1.2. Create dialog files (.ts, .spec.ts, .html, .scss)

5.2. Dialog Implementation
[ ] 5.2.1. Inject DialogRef for closing
[ ] 5.2.2. Create form with FormBuilder (if form-based)
[ ] 5.2.3. Define form fields: [N] fields
         - [name1]: [type1] [required: Y/N]
         - ...
[ ] 5.2.4. Implement validation rules
[ ] 5.2.5. Implement business logic per plan

5.3. API Integration
[ ] 5.3.1. Inject API service
[ ] 5.3.2. Implement submit handler
[ ] 5.3.3. Handle loading states
[ ] 5.3.4. Return result: { action: 'submit' | 'cancel', data?: any }

5.4. Parent Integration
[ ] 5.4.1. Open dialog from parent with DialogService.open()
[ ] 5.4.2. Pass data via component instance
[ ] 5.4.3. Handle result in subscription
[ ] 5.4.4. Refresh parent on success

6. Testing
6.1. Modal Tests
[ ] 6.1.1. Test form field configuration
[ ] 6.1.2. Test validation rules
[ ] 6.1.3. Test submit handler
[ ] 6.1.4. Test error handling
[ ] 6.1.5. Test dialog close/cancel

---

## Dependency Matrix

| Task Group | Depends On | Blocks | Can Parallelize With |
|------------|------------|--------|---------------------|
| 1. Action Type Detection | Parent Panel | Form Config | None |
| 2. Form Fields Config | Action Type | Mode-Based, Dialog | None |
| 3. Mode-Based Fields | Form Fields | Dialog Opening | None |
| 4. Dialog Opening | Mode-Based | API Integration | None |
| 5. API Integration | Dialog Opening | Parent Refresh | None |
| 6. Parent Refresh | API Integration | Testing | None |
| 7. Custom Dialog (if custom) | Action Type | API Integration | Form Fields |
| 8. Testing | All implementation | None | None |

## Parallelization Opportunities

**Can run in parallel:**
- Common actions use TableMenuService - no additional implementation needed
- For config-form: Form field config setup while dialog opening is designed
- Testing can start after dialog implementation completes

**Must be sequential:**
- Action detection → Form config → Dialog → API → Parent refresh

**Sub-agent dispatch for Modal:**
- Wave 1: Action type detection
- Wave 2: Form fields config (if config-form/custom)
- Wave 3: Mode-based fields + Dialog opening
- Wave 4: API integration
- Wave 5: Parent refresh + Testing (parallel)

---

> **Note**: Form fields should match implementation plan exactly. Count validation is critical.
```

---

## Analysis Process

### Phase 0: Read and Detect Work Unit Type

1. **Read implementation-plan.md completely** from the entry point directory
2. **Extract Work Unit Type** from header or detect from key pattern
3. **Set task generation focus** - determine which template to use

### Phase 1: Extract Configurations

Based on work unit type, extract relevant configurations:

**For Page Setup:**
- [ ] Extract SearchConfig.fields (count + names + types)
- [ ] Extract PanelConfig[] (count + IDs + types)
- [ ] Extract Layout type
- [ ] Extract Tab configuration (if tabbed layout)

**For Panel:**
- [ ] Detect panel type (table/custom/tabbed)
- [ ] Extract GridColumn[] (count + fields + headers + widths)
- [ ] Extract MenuItem[] (count + text + data)
- [ ] Extract data binding pattern

**For Modal:**
- [ ] Detect action type (common/config-form/confirmation/custom)
- [ ] Extract FieldConfig[] (count + names + types + required + disabled)
- [ ] Extract validation rules
- [ ] Extract API endpoints

### Phase 2: Generate Task List

1. **Select appropriate template** based on work unit type
2. **Populate Configuration Summary** with extracted data
3. **Fill in task placeholders** with specific configuration details
4. **Include expected counts** from implementation plan sections
5. **Add notes** about deferred work (to other work units)

### Phase 3: Task Granularity Check

Review each leaf-level task and ensure it:
- [ ] Is specific and actionable
- [ ] Can be completed in a reasonable timeframe (hours to 1 day)
- [ ] Has a clear definition of "done"
- [ ] Includes configuration details where applicable
- [ ] References expected counts from implementation plan

### Phase 4: Dependency Analysis

Analyze task dependencies based on work unit type:

**For Page Setup:**
- File structure → DTOs → Mapper → API Service → SearchConfig → PanelConfig → Routing
- Tests can run in parallel with next component

**For Panel:**
- Panel setup → GridColumn config → MenuItem config → Data binding → Selection handling
- Tests can run in parallel with parent communication

**For Modal:**
- Action type detection → Form config → Dialog implementation → API integration → Parent refresh
- Tests can run in parallel with parent integration

### Phase 5: Claude Task Tracking (Optional)

If the implementing agent will use Claude's task tracking:

1. **Create component-level tasks** using `TaskCreate`:
   ```
   TaskCreate(
     subject="Create SearchConfig with 4 fields",
     description="Configure search form fields: company, companyName, activeOnly, effectiveDate",
     activeForm="Configuring search form"
   )
   ```

2. **Set dependencies** using `TaskUpdate` with `addBlockedBy`:
   ```
   // Panel config depends on DTOs/Mapper
   TaskUpdate(taskId="panel-config-id", addBlockedBy=["dto-task-id", "mapper-task-id"])
   ```

### Phase 6: Generate Output

1. **Write task-list.md** with work unit type-specific template
2. **Count total tasks** (only leaf-level checkbox items)
3. **Add metadata** (source, date, work unit type, task count)
4. **Include Configuration Summary section**
5. **Include Dependency Matrix section**
6. **Include Parallelization Opportunities section**

---

## Critical Guidelines

### Work Unit Type Awareness

**CRITICAL**: Generate tasks ONLY for the current work unit type's scope:

| Work Unit | Generate Tasks For | Do NOT Generate Tasks For |
|-----------|-------------------|---------------------------|
| Page Setup | File structure, DTOs, SearchConfig, PanelConfig | Grid columns, context menus, form fields |
| Panel | GridColumn, MenuItem, data binding | Search form, routing, modal forms |
| Modal | Form fields, dialog, validation, API | Search form, routing, grid columns |

### Configuration-Specific Tasks

**CRITICAL**: Tasks must include configuration details from the implementation plan:

```markdown
GOOD (Configuration-specific):
[ ] 2.1.2. Configure [4] search fields (Expected: 4 from "Search Form Configuration"):
         - company (LOOKUP)
         - companyName (TEXT)
         - activeOnly (CHECKBOX)
         - effectiveDate (DATE)

BAD (Generic):
[ ] 2.1.2. Configure search fields
```

### Count Validation

**CRITICAL**: Every configuration task must include expected count:

```markdown
[ ] 2.1.1. Define columns: GridColumn[] with [8] columns (Expected: 8 from "Table Configuration"):
         - id, companyName, status, effectiveDate, createdBy, createdDate, modifiedBy, modifiedDate
```

### Task Hierarchical Organization

**Level 1 (Top-Level)** - Major phases:
- Examples: "Project Setup", "Search Form Configuration", "Table Panel Configuration"
- No checkboxes
- Typically 5-8 top-level items per work unit type

**Level 2 (Mid-Level)** - Sub-components:
- Examples: "File Structure", "SearchConfig", "GridColumn Configuration"
- No checkboxes
- Typically 2-4 mid-level items per top-level item

**Level 3 (Leaf-Level)** - Specific tasks:
- Examples: "Define searchConfig with 4 fields: ..."
- WITH checkboxes `[ ]`
- Include configuration details and expected counts

### Notes About Deferred Work

Always include notes at the end about what is deferred to other work units:

```markdown
> **Note**: Grid columns and context menus are implemented in Panel work units.
> **Note**: Form fields and modals are implemented in Modal work units.
```

---

## Task Management

Use TodoWrite tool to track progress:

```
Phase 0 - Detection:
- Read implementation-plan.md
- Extract Work Unit Type
- Set task generation focus

Phase 1 - Extraction:
- Extract SearchConfig details (Page Setup)
- Extract PanelConfig details (Page Setup)
- Extract GridColumn details (Panel)
- Extract MenuItem details (Panel)
- Extract FieldConfig details (Modal)

Phase 2 - Generation:
- Select work unit type template
- Populate Configuration Summary
- Fill task placeholders with configuration details
- Include expected counts
- Add deferred work notes

Phase 3 - Quality:
- Verify task granularity
- Check configuration details are included
- Verify expected counts are present
- Count total tasks

Phase 4 - Output:
- Write task-list.md
- Add metadata with work unit type
- Final formatting review
```

---

## UI Technology Stack Reference

### Frontend Framework
- Angular 19+ with TypeScript
- Standalone components preferred
- OnPush change detection where appropriate

### State Management
- Angular Services with BehaviorSubjects/Signals for server state
- NgRx or Services for global UI state
- Component properties for local state

### UI Component Library
- Kendo UI for Angular (grids, forms, dialogs, etc.)
- Custom theme configuration

### Form Handling
- Angular Reactive Forms (FormGroup, FormControl)
- Angular Validators for validation

### Routing
- Angular Router with lazy loading
- Route guards (AuthGuard, CanDeactivate)

### Testing
- Jasmine/Karma for unit tests
- Angular Testing Utilities for component tests
- Cypress for E2E tests

---

## Success Criteria

### Work Unit Type Detection
- [ ] Correctly detects work unit type from implementation plan header or key pattern
- [ ] Uses Page Setup/Panel/Modal template based on type

### Configuration Extraction
- [ ] Extracts all relevant configurations for the work unit type
- [ ] Counts match what's in implementation plan
- [ ] Configuration details (names, types, labels) are captured

### Task Generation
- [ ] Uses work unit type-specific template
- [ ] Tasks include configuration details (field names, column names, action names)
- [ ] Tasks include expected counts with source references
- [ ] Three-level hierarchy is consistent
- [ ] Checkboxes only on leaf-level tasks

### Alignment with Workflow
- [ ] Matches work unit type detection logic in implement-ui/review-ui
- [ ] Uses same configuration terminology
- [ ] Notes deferred work to other work units
- [ ] Task structure aligns with implementation order

### Quality
- [ ] Leaf-level tasks are specific and actionable
- [ ] Configuration details enable count validation during implementation
- [ ] No generic tasks without configuration context
- [ ] Testing tasks included for implementation tasks

---

## Troubleshooting

### Wrong Work Unit Type Detected

**Problem**: Task list includes tasks for wrong scope (e.g., grid columns in Page Setup)

**Solutions**:
1. Check implementation plan header for `> **Work Unit Type**: [type]`
2. Verify key pattern matches detection rules
3. If ambiguous, default to most likely type based on content

### Missing Configuration Details

**Problem**: Tasks don't include specific field/column/action names

**Solutions**:
1. Re-read relevant section of implementation plan
2. Extract all configuration items with names/types
3. Include full list in task description

### Count Mismatch Concerns

**Problem**: Unsure if extracted count matches implementation plan

**Solutions**:
1. Count items manually from implementation plan section
2. Document source: "Expected: X from [section name]"
3. If plan is ambiguous, note: "Verify count with tech plan author"

### Too Many/Few Tasks

**Problem**: Task list seems bloated or incomplete for work unit type

**Solutions**:
1. Verify using correct template for work unit type
2. Page Setup should NOT have column/menu/form field tasks
3. Panel should NOT have routing/search/modal form tasks
4. Modal should NOT have routing/search/column tasks

---

## Reference Files

When generating task lists, reference:

| File | Purpose |
|------|---------|
| `.claude/commands/implement-ui.md` | Work unit types, configuration extraction, implementation order |
| `.claude/commands/review-ui-implementation.md` | Configuration validation patterns, count validation |
| `.claude/commands/update-ui-technical-plan-based-on-code-changes.md` | Work unit type detection |
| `docs/target-architecture/frontend-architecture/reference/configuration.md` | Configuration type definitions |

---

**End of Command Specification**
