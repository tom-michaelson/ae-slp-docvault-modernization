# Review UI Implementation

Review a UI implementation against the implementation_plan with **work unit type awareness** and **configuration completeness validation**.

## Usage

```
/review-ui-implementation task list: [task-list-path], implementation_plan: [technical-plan-path]
```

## Input

- `task list`: Path to the task-list.md file
- `implementation_plan`: Path to the implementation-plan.md file

## Output

Creates `implementation-review-result.json` in the same directory as the implementation_plan:

```typescript
interface ImplementationReview {
  validated: boolean;
  notes?: string | null;
  remaining_issues?: string | null;
}
```

## Scope

This command performs **UI-specific configuration validation** through static code analysis. It does NOT:
- Execute tests
- Run the application
- Build the project

**Focus**: Does the implementation have all configurations specified in the implementation_plan?

---

## Phase 0: Read & Detect Work Unit Type

### 0.1 Read Input Documents

1. **Read implementation-plan.md completely**
2. **Read task-list.md** for context
3. **Extract Work Unit Type** from the implementation_plan header

### 0.2 Work Unit Type Detection (CRITICAL)

Detect the work unit type from the implementation_plan to determine what to validate:

| Work Unit Type | What to Validate | What NOT to Validate |
|----------------|------------------|---------------------|
| **Page Setup** | Search fields, Panel IDs, Tabs, .spec.ts files | Grid columns, context menus |
| **Panel** | Grid columns, Context menu actions, Data binding | Modal forms |
| **Modal** | Form fields (if form-based), Action type correctness | - |

**Detection Logic:**
The implementation_plan header contains: `> **Work Unit Type**: [Page Setup | Panel | Modal]`

If not explicitly stated, detect from key pattern:
1. **Page Setup**: Key ends with the page name (no panel/action suffix)
2. **Panel**: Key has one additional segment after page name
3. **Modal**: Key has action suffix (`-modify`, `-new`, `-attach-document`, `-view-attachment`)

### 0.3 Read Architecture Documentation (Reference)

- `./docs/target-architecture/frontend-architecture/index.md`
- `./docs/target-architecture/frontend-architecture/reference/configuration.md`

---

## Phase 1: Extract Expected Configuration (from Plan)

Parse the implementation_plan to extract expected configuration items with counts.

### 1.1 For Page Setup

#### Search Form Configuration
Parse the **Search Form Configuration** section:

```
Expected Search Fields:
| # | Field Name | Type | Required |
|---|------------|------|----------|
| 1 | [name] | [TEXT/LOOKUP/DATE/CHECKBOX/DROPDOWN] | [Y/N] |
...

Expected Count: [N]
```

#### Panel Configuration
Parse the **Panel Configuration** or **PanelConfig[]** section:

```
Expected Panels:
| # | Panel ID | Panel Type |
|---|----------|------------|
| 1 | [id] | [table/custom/tabbed] |
...

Expected Panel Count: [N]
```

#### Tab Configuration (if tabbed layout)
Parse the **Tab Configuration** section (if layout is tabbed):

```
Expected Tabs:
| # | Tab ID | Tab Label | Tab Panel Type |
|---|--------|-----------|----------------|
| 1 | [id] | [label] | [table/custom] |
...

Expected Tab Count: [N]
```

> **Note**: Do NOT extract grid columns or context menu actions for Page Setup. Those are validated in Panel work unit.

### 1.2 For Panel

#### Table Columns Configuration
Parse the **Table Configuration** section:

```
Expected Columns:
| # | Field Name | Header | Type | Width |
|---|------------|--------|------|-------|
| 1 | [field] | [title] | [type] | [px] |
...

Expected Column Count: [N]
```

#### Context Menu Configuration
Parse the **Context Menu Configuration** section:

```
Expected Menu Actions:
| # | Action Text | Action Data |
|---|-------------|-------------|
| 1 | [text] | [data key] |
...

Expected Action Count: [N]
```

### 1.3 For Modal

#### Action Type
Parse the **Action Configuration** section:
- Action Type: [common | config-form | confirmation | custom]
- Action Name: [New | Modify | Delete | Print | Export | etc.]

#### Form Fields Configuration (if config-form or custom with form)
Parse the **Form Configuration** section:

```
Expected Form Fields:
| # | Field Name | Type | Label | Required | Disabled (Edit) |
|---|------------|------|-------|----------|-----------------|
| 1 | [name] | [type] | [label] | [Y/N] | [Y/N] |
...

Expected Field Count: [N]
```

> **Note**: Common table actions (Print, Export, Filter) and confirmation dialogs (Delete) don't require form field validation.

---

## Phase 2: Extract Actual Configuration (from Implementation)

Locate and read the implementation files to extract actual configuration.

### 2.1 Locate Implementation Files

Based on the implementation_plan's **File Structure** section, identify:
- Main component file: `{feature-name}.component.ts`
- API service file: `{feature-name}-api.service.ts`
- Mapper file: `{feature-name}.mapper.ts`

### 2.2 For Page Setup

#### Extract Search Configuration
Find and parse the `searchConfig: SearchConfig` object:

```typescript
// Look for this pattern in component file:
searchConfig: SearchConfig = {
  fields: [
    { type: FieldType.XXX, name: 'xxx', label: 'xxx', ... },
    ...
  ],
  advancedFields: [...],  // if present
};
```

Extract:
- `searchConfig.fields[]` - name, type
- `searchConfig.advancedFields[]` - name, type (if exists)

**Count ALL fields** (fields + advancedFields if present)

#### Extract Panel Configuration
Find and parse `panelConfigs` or `panels` array:

```typescript
// Look for this pattern:
panelConfigs: PanelConfig[] = [
  { type: 'table', id: 'xxx', ... },
  { type: 'tabbed', id: 'xxx', tabs: [...] },
  ...
];
```

Extract:
- Panel IDs
- Panel types

#### Extract Tab Configuration (if tabbed)
If any panel is type `'tabbed'`, extract tabs:

```typescript
{
  type: 'tabbed',
  id: 'xxx',
  tabs: [
    { id: 'tab-id', label: 'Tab Label', panel: { type: 'table', ... } },
    ...
  ]
}
```

Extract:
- Tab IDs
- Tab labels
- Tab panel types

### 2.3 For Panel

#### Extract Column Configuration
Find and parse `columns` or `GridColumn[]` array:

```typescript
// Look for this pattern:
columns: GridColumn[] = [
  { field: 'xxx', title: 'XXX', width: 100 },
  ...
];

// Or within PanelConfig:
{
  type: 'table',
  columns: [...],
  ...
}
```

Extract:
- Column fields
- Column titles

#### Extract Menu Items Configuration
Find and parse `menuItems` or `MenuItem[]` array:

```typescript
// Look for this pattern:
menuItems: MenuItem[] = [
  { text: 'New', data: 'new' },
  { text: 'Modify', data: 'modify' },
  ...
];
```

Extract:
- Menu item text
- Menu item data (action key)

### 2.4 For Modal

#### Identify Action Type
Determine how the action is implemented:
- Uses `TableMenuService` → common action
- Uses `dialogService.openConfigForm()` → config-form
- Uses `dialogService.confirm()` → confirmation
- Creates custom dialog component → custom

#### Extract Form Fields (if applicable)
Find form field configuration:

```typescript
// For config-form dialogs:
formFields: FieldConfig[] = [
  { type: FieldType.TEXT, name: 'xxx', label: 'xxx', ... },
  ...
];

// Or within openConfigForm call:
this.dialogService.openConfigForm({
  fields: [...],
  ...
});
```

Extract:
- Field names
- Field types
- Field labels

---

## Phase 3: Field-by-Field Comparison

Create comparison tables matching expected (from plan) against actual (from implementation).

### 3.1 Comparison Format

```
### [Section Name] Validation
| # | Plan [Item] | Plan [Type] | Impl [Item] | Impl [Type] | Status |
|---|-------------|-------------|-------------|-------------|--------|
| 1 | company     | LOOKUP      | company     | LOOKUP      | OK     |
| 2 | companyName | TEXT        | -           | -           | MISSING|
| 3 | startDate   | DATE        | startDate   | TEXT        | TYPE MISMATCH |

Result: [X]/[Y] items - [PASS/FAIL]
```

### 3.2 Comparison Rules

**Matching Logic:**
- Match by name (case-insensitive)
- Verify type matches

**Status Values:**
- `OK` - Field found with matching type
- `MISSING` - Field in plan but not in implementation
- `TYPE MISMATCH` - Field found but type differs
- `EXTRA` - Field in implementation but not in plan (warning, not failure)

### 3.3 Page Setup Comparisons

1. **Search Form Validation**
   - Compare plan search fields vs `searchConfig.fields` + `advancedFields`

2. **Panel Configuration Validation**
   - Compare plan panel IDs vs implemented panels

3. **Tab Configuration Validation** (if tabbed)
   - Compare plan tabs vs implemented tabs

### 3.4 Panel Comparisons

1. **Column Validation**
   - Compare plan columns vs implemented `columns` array

2. **Menu Actions Validation**
   - Compare plan menu actions vs implemented `menuItems` array

### 3.5 Modal Comparisons

1. **Form Fields Validation** (if config-form or custom with form)
   - Compare plan form fields vs implemented fields configuration

---

## Phase 4: Count Validation

**Count validation is MANDATORY.** Fail the review if counts don't match.

### 4.1 Count Validation Format

```
Count Validation Summary:
=========================
[Category]:
  Plan specifies: [N] items (Section: [section name])
  Implementation has: [M] items
  Status: [PASS/FAIL]
```

### 4.2 Page Setup Counts

- **Search Fields**: Plan count vs implementation count
- **Panels**: Plan count vs implementation count
- **Tabs** (if tabbed): Plan count vs implementation count

### 4.3 Panel Counts

- **Columns**: Plan count vs implementation count
- **Menu Actions**: Plan count vs implementation count

### 4.4 Modal Counts

- **Form Fields** (if applicable): Plan count vs implementation count

### 4.5 Count Validation Rules

```
PASS when: Expected count == Actual count AND all items match
FAIL when: Expected count != Actual count OR any item missing/mismatched
```

---

## Phase 5: File Existence Checks

### 5.1 For Page Setup

Check existence of all files specified in implementation_plan:

```
File Existence Validation:
==========================
Component Files:
- [ ] {feature-name}.component.ts
- [ ] {feature-name}.component.spec.ts    [CRITICAL: test file]
- [ ] {feature-name}.component.html

API Service Files:
- [ ] {feature-name}-api.service.ts
- [ ] {feature-name}-api.service.spec.ts  [CRITICAL: test file]

Mapper Files:
- [ ] {feature-name}.mapper.ts
- [ ] {feature-name}.mapper.spec.ts       [CRITICAL: test file]

DTO Files:
- [ ] requests/{feature-name}.request.ts
- [ ] responses/{feature-name}.response.ts
- [ ] view-models/{feature-name}-table-row.view-model.ts
```

### 5.2 For Panel (Custom)

```
Sub-Component Files:
- [ ] {panel-name}.component.ts
- [ ] {panel-name}.component.spec.ts      [CRITICAL: test file]
- [ ] {panel-name}.component.html
```

### 5.3 For Modal (Custom)

```
Dialog Component Files:
- [ ] {dialog-name}-dialog.component.ts
- [ ] {dialog-name}-dialog.component.spec.ts  [CRITICAL: test file]
- [ ] {dialog-name}-dialog.component.html
```

### 5.4 .spec.ts File Check (CRITICAL)

**Every .ts file with logic MUST have a corresponding .spec.ts file.**

Mark as `P1 - HIGH` priority issue if any .spec.ts file is missing.

---

## Phase 5.5: data-testid Attribute Validation

**Verify that all generated HTML templates use the correct `data-testid` attribute convention.**

### 5.5.1 Scan for Wrong Attribute Names

Run these checks on all `.component.html` files in the implementation:

```bash
# Check for the wrong hyphenated variant
grep -rn "data-test-id" passage-ui/src/app/{feature-path}/

# Check for wrong mixed-case variant
grep -rn "data-TestId" passage-ui/src/app/{feature-path}/
```

Any match is a **P0 - BLOCKING** violation.

### 5.5.2 Verify data-testid Presence

Check that the following elements have `[attr.data-testid]` or `[dataTestId]` bindings:

| Element | Check |
|---------|-------|
| Page wrapper `<div>` | `[attr.data-testid]` present |
| `<app-data-table>` | `[dataTestId]="..."` present |
| `<app-button>` elements | `[dataTestId]="..."` present |
| `<app-text-input>` / `<app-dropdown>` etc. | `[dataTestId]="..."` present |
| Dialog components | `[dataTestId]="..."` present |

Missing `data-testid` on a required element is a **P1 - HIGH** violation.

### 5.5.3 Verify Naming Convention

All `data-testid` values must follow `{domain}-{component}-{element}` format:
- Lowercase, kebab-case
- No spaces or underscores
- Descriptive of the element's role

Example violations: `testId1`, `my_button`, `DataGrid` — flag as **P2 - MEDIUM**.

### 5.5.4 Report Format

```
data-testid Validation:
========================
Wrong attribute names found: [PASS / FAIL - list files]
Required elements with data-testid: [N/M present]
Naming convention issues: [list or "none"]
Overall: [PASS / FAIL]
```

---

## Phase 5.6: Route Registry Validation (Page Setup only)

**Skip this section for Panel and Modal work units — only Page Setup registers routes.**

### 5.6.1 Entry Exists

Check that `passage-ui/src/app/core/constants/route-registry.constants.ts` contains an entry where `angularRoute` matches the route path from the implementation plan.

```
Route Registry Validation:
==========================
Entry in ROUTE_REGISTRY:        [ ] YES  [ ] NO
angularRoute matches route:     [ ] YES  [ ] NO
legacyUri populated:            [ ] YES  [ ] NO
label populated:                [ ] YES  [ ] NO
category populated:             [ ] YES  [ ] NO
```

Missing route registry entry is a **P0 - BLOCKING** violation (page will not appear in navigation menu).

### 5.6.2 Route Path Consistency

Verify `angularRoute` in route registry matches the route path in the domain routing module (e.g., `company.ts` or `infrastructure.routes.ts`). A mismatch means the menu link will 404.

---

## Phase 6: Generate Review Result

### 6.1 Determine Validation Status

```
validated = true IF AND ONLY IF ALL of the following are true:
- All expected configuration files exist
- All .spec.ts test files exist for logic-containing files
- All field/column/panel counts match
- All field-by-field comparisons pass (no MISSING or TYPE MISMATCH)
- No wrong data-testid attribute names (data-test-id, data-TestId) found in templates
- All required UI elements have data-testid bindings
- Route registry entry exists with matching angularRoute (Page Setup only)

validated = false IF ANY of the following are true:
- Expected files missing
- Count mismatches
- Fields/columns missing from implementation
- Type mismatches between plan and implementation
- Required .spec.ts files missing
- Wrong data-testid attribute name used (e.g. data-test-id) — P0 BLOCKING
- Required elements missing data-testid — P1 HIGH
- Route registry entry missing for Page Setup work unit — P0 BLOCKING
```

### 6.2 Compile remaining_issues

**Format for `remaining_issues`** (if validated = false):

```
CONFIGURATION ISSUES:

1. MISSING [CATEGORY] (P0 - BLOCKING)
   Technical Plan specifies [N] [items] (Section: [section name])
   Implementation has [M] [items]

   Missing:
   - [item name] ([type]) - not found in [location]

   Location: [implementation file path]

2. TYPE MISMATCH (P0 - BLOCKING)
   Field: [field name]
   Technical Plan: [expected type] (Section: [section name])
   Implementation: [actual type]

   Location: [file:line if possible]

3. MISSING TEST FILE (P1 - HIGH)
   Expected: [filename].spec.ts
   Actual: File not found

   Location: [expected path]

4. COUNT MISMATCH (P0 - BLOCKING)
   Category: [category name]
   Expected: [N] (from [section name])
   Actual: [M]

   [List missing items]

REQUIRED ACTIONS:
1. [Specific action to fix issue 1]
2. [Specific action to fix issue 2]
...
```

### 6.3 Priority Levels

- **P0 - BLOCKING**: Missing configuration, count mismatch, type mismatch
- **P1 - HIGH**: Missing .spec.ts files, incomplete implementation
- **P2 - MEDIUM**: Extra fields (implementation has more than plan), minor deviations

### 6.4 Write JSON Output

Create `implementation-review-result.json` in the entry point directory:

```json
{
  "validated": false,
  "notes": "Configuration validation failed. 1 search field missing, 2 columns missing.",
  "remaining_issues": "CONFIGURATION ISSUES:\n\n1. MISSING SEARCH FIELDS..."
}
```

**Or if validated:**

```json
{
  "validated": true,
  "notes": "Implementation is configuration-complete. All 5 search fields, 3 panels, and 12 columns match the implementation_plan. All .spec.ts test files exist.",
  "remaining_issues": null
}
```

---

## Validation Rules Summary

### Page Setup Validation

| Check | Pass Condition | Fail Condition |
|-------|----------------|----------------|
| Search Fields | All fields present with correct types | Any field missing or type mismatch |
| Panels | All panel IDs present with correct types | Any panel missing |
| Tabs (if tabbed) | All tabs present with correct labels | Any tab missing |
| Test Files | All .spec.ts files exist | Any .spec.ts missing |

### Panel Validation

| Check | Pass Condition | Fail Condition |
|-------|----------------|----------------|
| Columns | All columns present with correct fields | Any column missing |
| Menu Actions | All actions present | Any action missing |
| Test Files | Component .spec.ts exists | .spec.ts missing |

### Modal Validation

| Check | Pass Condition | Fail Condition |
|-------|----------------|----------------|
| Action Type | Correct action type implemented | Wrong action type |
| Form Fields | All fields present (if form-based) | Any field missing |
| Test Files | Dialog .spec.ts exists (if custom) | .spec.ts missing |

---

## Example Review Output

### Example 1: Validated Implementation

```
REVIEW RESULT: VALIDATED

Work Unit Type: Page Setup

Configuration Validation:
=========================

Search Form Fields:
| # | Plan Field | Plan Type | Impl Field | Impl Type | Status |
|---|------------|-----------|------------|-----------|--------|
| 1 | company    | LOOKUP    | company    | LOOKUP    | OK     |
| 2 | activeOnly | CHECKBOX  | activeOnly | CHECKBOX  | OK     |
| 3 | startDate  | DATE      | startDate  | DATE      | OK     |

Result: 3/3 fields - PASS

Panel Configuration:
| # | Plan Panel ID     | Plan Type | Impl Panel ID     | Impl Type | Status |
|---|-------------------|-----------|-------------------|-----------|--------|
| 1 | company-list      | table     | company-list      | table     | OK     |

Result: 1/1 panels - PASS

File Existence:
- [x] company-maintenance.component.ts
- [x] company-maintenance.component.spec.ts
- [x] company-maintenance-api.service.ts
- [x] company-maintenance-api.service.spec.ts
- [x] company-maintenance.mapper.ts
- [x] company-maintenance.mapper.spec.ts

All checks passed.
```

### Example 2: Failed Validation

```
REVIEW RESULT: NOT VALIDATED

Work Unit Type: Page Setup

Configuration Validation:
=========================

Search Form Fields:
| # | Plan Field  | Plan Type | Impl Field  | Impl Type | Status  |
|---|-------------|-----------|-------------|-----------|---------|
| 1 | company     | LOOKUP    | company     | LOOKUP    | OK      |
| 2 | companyName | TEXT      | -           | -         | MISSING |
| 3 | activeOnly  | CHECKBOX  | activeOnly  | CHECKBOX  | OK      |
| 4 | startDate   | DATE      | startDate   | TEXT      | TYPE MISMATCH |

Result: 2/4 fields - FAIL

File Existence:
- [x] company-maintenance.component.ts
- [ ] company-maintenance.component.spec.ts  [MISSING]
- [x] company-maintenance-api.service.ts
- [x] company-maintenance-api.service.spec.ts

---

remaining_issues:

CONFIGURATION ISSUES:

1. MISSING SEARCH FIELD (P0 - BLOCKING)
   Technical Plan specifies 4 search fields (Section: Search Form Configuration)
   Implementation has 3 search fields

   Missing:
   - companyName (TEXT) - not found in searchConfig.fields

   Location: passage-ui/src/app/.../company-maintenance.component.ts

2. TYPE MISMATCH (P0 - BLOCKING)
   Field: startDate
   Technical Plan: DATE (Section: Search Form Configuration)
   Implementation: TEXT

   Location: passage-ui/src/app/.../company-maintenance.component.ts (searchConfig.fields)

3. MISSING TEST FILE (P1 - HIGH)
   Expected: company-maintenance.component.spec.ts
   Actual: File not found

   Location: passage-ui/src/app/.../views/company-maintenance/

REQUIRED ACTIONS:
1. Add missing 'companyName' TEXT field to searchConfig.fields
2. Change 'startDate' field type from TEXT to DATE in searchConfig.fields
3. Create company-maintenance.component.spec.ts with component tests
```

---

## Critical Guidelines

### Focus on Configuration Completeness

This review specifically validates:
- SearchConfig completeness (fields, types)
- PanelConfig completeness (IDs, types)
- GridColumn completeness (fields, titles)
- MenuItem completeness (text, data)
- FieldConfig completeness (names, types) for forms

### Count Validation is Non-Negotiable

**Always perform explicit count validation:**
```
Plan specifies: N items
Implementation has: M items
Status: [PASS if N==M, FAIL otherwise]
```

### Be Specific in remaining_issues

Each issue must include:
1. What is wrong (missing/mismatch)
2. What the plan specifies (with section reference)
3. What the implementation has
4. Exact file location
5. Specific fix action

### Guide the Retry Loop

The `remaining_issues` field guides the `/implement-ui` retry loop. Make issues actionable:
- Bad: "Search configuration incomplete"
- Good: "Add missing 'company' LOOKUP field to searchConfig.fields"

---

## Success Criteria

**Review is Complete When:**
- [ ] Work unit type detected from implementation_plan
- [ ] Expected configuration extracted from implementation_plan with counts
- [ ] Actual configuration extracted from implementation code
- [ ] Field-by-field comparison tables generated
- [ ] Count validation performed for all categories
- [ ] File existence verified (especially .spec.ts files)
- [ ] `implementation-review-result.json` created with correct schema
- [ ] `remaining_issues` (if any) includes specific fix actions

**Review Catches These Common Issues:**
- [ ] Missing search fields (like the LOOKUP field scenario)
- [ ] Missing grid columns
- [ ] Missing context menu actions
- [ ] Type mismatches (TEXT vs LOOKUP, DATE vs TEXT)
- [ ] Missing .spec.ts test files
- [ ] Panel ID mismatches
- [ ] Tab configuration mismatches

---

## Related Resources

- **Architecture Standards:** `passage-ui-architect` agent defines UI layer patterns, config-driven patterns, and quality standards
- **Review Mode:** When used in remediation validation, `passage-ui-architect` can be launched in review mode with `Mode: REVIEW` to validate implementations against its domain-specific criteria

---

**End of Command Specification**
