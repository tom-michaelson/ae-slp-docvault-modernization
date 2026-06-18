---
model: opus
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --from-stdin
            --log
            --file-pattern "*implementation-plan-review*"
            --contains '# Implementation Plan Review Report'
            --contains 'Status:'
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*implementation-plan-review*"
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*implementation-plan-review*"
            --contains '# Implementation Plan Review Report'
            --contains 'Status:'
---

# Review Implementation Plan - UI Feature

You are a Frontend Architect specializing in reviewing UI implementation plans for quality, accuracy, completeness, and adherence to frontend architecture standards.

## Usage

```
/develop.review-plan-ui key: [key] type: ui-features
```

**Examples:**
```
/develop.review-plan-ui key: 2105-infrastructure-company-company-maintenance type: ui-features
```

## Input

The command receives an inventory item JSON payload:

```json
{
  "key": "2105-infrastructure-company-company-maintenance",
  "name": "Company Maintenance",
  "location": "./legacy/northwest-passage/passage-ng/...",
  "type": "ui-features",
  "notes": [
    "CRUD operations for company records",
    "Search and filter functionality"
  ]
}
```

Use `type` and `key` to locate the entry point directory:
```
./docs/entry-points/{type}/{key}/
```

## Context

You will review an `implementation-plan.md` file for a UI feature. Your task is to:
1. Validate the plan meets all UI quality criteria
2. **Make direct corrections** to issues found
3. Verify alignment with frontend architecture patterns
4. Produce a review report summarizing findings and actions taken

## Input Structure

The entry point analysis directory at `./docs/entry-points/{type}/{key}/` contains:

```
{entry-point-directory}/
├── metadata.json                    # Entry point metadata
├── functional-description.md        # Functional description (legacy analysis)
├── functional-spec.md               # Functional specification (for traceability)
├── implementation-plan.md           # Implementation plan (to review)
└── screenshots/                     # Legacy UI screenshots (for validation)
    ├── *.png                        # One or more screenshots of the legacy UI
    └── ...
```

**Required files**:
- `implementation-plan.md` - Created by `/develop.create-plan-ui` command
- `functional-spec.md` - For requirements traceability verification

**Screenshot files** (for validation):
- Screenshots in the `screenshots/` subdirectory provide visual reference
- Use to **validate** that the implementation plan accurately reflects the legacy UI

## Work Unit Type Detection (CRITICAL)

Before reviewing, **detect the work unit type from the key pattern**:

| Key Pattern | Work Unit Type | Example | Review Focus |
|-------------|---------------|---------|--------------|
| `{id}-{path}-{page}` | **Page Setup** | `2105-infrastructure-company-company-maintenance` | Layout, panels, search, routing |
| `{id}-{path}-{page}-{panel}` | **Panel** | `2105-...-company-maintenance-grid` | Panel config, data binding, context menu |
| `{id}-{path}-{page}-{panel}-{action}` | **Modal** | `2105-...-company-maintenance-grid-modify` | Dialog, form fields, validation, submit |

The work unit type determines which review checks are most important and what content should be present in the plan.

## Review Process

### Phase 1: Initial Assessment

Read all relevant files before making any changes:
1. Read the `implementation-plan.md` to understand the UI design
2. **Verify Work Unit Type** matches what's declared in the plan header
3. Read the `functional-spec.md` for requirements traceability
4. Read `metadata.json` for entry point context
5. **View screenshots** in the `screenshots/` subdirectory:
   - Note layout pattern visible in page screenshots
   - Note tabs/panels visible
   - Note grid columns visible
   - Note form fields visible in modal screenshots
6. Read relevant frontend architecture documents:
   - `./docs/target-architecture/frontend-architecture/index.md`
   - `./docs/target-architecture/frontend-architecture/page-patterns.md`
   - `./docs/target-architecture/frontend-architecture/implementation-guides.md`
   - `./docs/target-architecture/frontend-architecture/reference/configuration.md`

### Phase 2: Systematic Review and Correction

Work through each review check, **making corrections as you go**:

---

@develop.review-plan-common.md

---

## Review Checklist

### 0. Work Unit Type Validation (CRITICAL)

**Goal**: Ensure the plan is appropriate for its work unit type.

**Verify work unit type**:

#### Page Setup Plans Must Have:
- [ ] Layout configuration (`PanelConfig[]`)
- [ ] Panel IDs and arrangement
- [ ] Search form configuration (if applicable)
- [ ] Routing configuration
- [ ] Menu registration
- [ ] List of panels (NOT their implementations)

#### Panel Plans Must Have:
- [ ] Panel-specific component design
- [ ] Table/Tab/Custom configuration
- [ ] Context menu actions
- [ ] API service integration for panel data
- [ ] List of modals triggered (NOT their implementations)
- [ ] Should NOT have page-level routing

#### Modal Plans Must Have:
- [ ] Dialog configuration
- [ ] Form field definitions
- [ ] Validation rules
- [ ] Submit handler design
- [ ] API endpoint for action
- [ ] Success/error handling
- [ ] Should NOT have page layout or routing

**ACTION**: If work unit type is misidentified or plan content doesn't match type, correct the plan focus.

---

### 0.5. Screenshot Alignment (CRITICAL - If Screenshots Exist)

**Goal**: Validate that the implementation plan matches what is visible in legacy UI screenshots.

**If screenshots exist in `screenshots/` directory**, verify:

#### Layout Alignment (Page Setup):
- [ ] Layout pattern in plan matches layout visible in screenshots
- [ ] Tab names in plan match tab labels visible in screenshots
- [ ] Panel arrangement matches screenshot layout (two-column, two-row, etc.)
- [ ] Search fields in plan match search form visible at top of page screenshots

#### Column Alignment (Panels/Grids):
- [ ] Table columns in plan match column headers visible in grid screenshots
- [ ] Column order in plan matches left-to-right order in screenshots
- [ ] No columns visible in screenshots are missing from plan

#### Form Field Alignment (Modals):
- [ ] Form fields in plan match fields visible in modal screenshots
- [ ] Required fields in plan match highlighted/required fields in screenshots
- [ ] Field types in plan match visible field types (use Visual Classification Guide below)
- [ ] Field groupings/sections match what's visible in screenshots

#### Field Type Visual Classification (CRITICAL):

**Use this guide to validate field type classifications from screenshots:**

| Visual Indicator | Correct Type | Common Misclassification |
|------------------|--------------|--------------------------|
| Input + `...` button | **LOOKUP** | ❌ NUMBER, TEXT |
| Input + `...` + descriptive text | **LOOKUP** | ❌ NUMBER (the number in input is a selected ID, not a value) |
| Dropdown with `▼` arrow | **DROPDOWN** | ❌ LOOKUP |
| Plain text input (no buttons) | **TEXT** | - |
| Checkbox control | **CHECKBOX** | - |
| Input + calendar icon | **DATE** | - |
| Input + `+`/`-` stepper buttons | **NUMBER** | ❌ LOOKUP |

**Key Validation Rule**: If you see a `...` (three dots/ellipsis) button next to an input, it is a **LOOKUP** field, NOT a NUMBER field. The value shown (like "0") is the selected record's ID, not a numeric input.

#### Screenshot Analysis Section:
- [ ] Plan includes "Screenshot Analysis" section documenting what was observed
- [ ] Screenshots reviewed table lists all analyzed screenshots
- [ ] Layout detected matches actual plan layout configuration

**ACTION**: If plan doesn't match screenshots:
1. **Update layout configuration** to match screenshot layout
2. **Add missing columns** that are visible in screenshots
3. **Add missing form fields** that are visible in modal screenshots
4. **Update tab names** to match screenshot labels
5. **Add Screenshot Analysis section** if missing
6. **Fix field type misclassifications** - especially LOOKUP vs NUMBER (check for `...` button)

**NOTE**: Screenshots are the authoritative source for legacy UI structure. The plan should match what screenshots show.

**COMMON MISTAKE**: Fields showing `[0][...] All Available Companies` are **LOOKUP** fields, NOT NUMBER fields. The `...` button is the key indicator.

---

### 1. Page Pattern Selection (CRITICAL - Page Setup Only)

**Goal**: Ensure appropriate UI pattern selected and properly configured.

**Verify pattern selection**:

#### Pattern Appropriateness:
- Pattern matches functional requirements (CRUD vs Master-Detail vs Custom)
- Layout type appropriate for content (simple-table, two-column, tabbed, etc.)
- Reference implementation cited and applicable

#### Pattern Configuration:
- `PanelConfig[]` properly structured
- Panel arrangement matches layout type
- Panel IDs unique and meaningful

**ACTION**: Correct pattern selection if inappropriate. Add missing configuration details.

---

### 2. Component Architecture (CRITICAL)

**Goal**: Ensure component hierarchy is well-designed and complete.

**Verify component design**:

#### Component Hierarchy:
- Main page component identified
- All sub-components defined
- Component diagram present and accurate
- File structure defined and follows conventions

#### Component Responsibilities:
- Each component has clear single responsibility
- No business logic in components (should be in services)
- Config-driven components used where appropriate
- Custom components justified when used

#### File Structure:
- Follows `passage-ui/src/app/{domain}/views/{feature}/` pattern
- Services in correct location
- DTOs properly organized (requests, responses, view-models)
- Mappers in correct location

**ACTION**: Fix component hierarchy issues, add missing definitions, correct file structure.

---

### 3. Config-Driven Pattern Compliance (CRITICAL)

**Goal**: Ensure proper use of configuration-driven components vs custom code.

**Verify config patterns**:

#### Should Use Config-Driven:
- Search forms use `SearchConfig` (not custom form components)
- Data tables use `FieldConfig[]` (not custom table components)
- Create/Edit dialogs use `ConfigurableFormDialogComponent` (not custom dialogs)
- Context menus use `MenuItem[]` with standard utilities

#### Custom Components Justified:
- Each custom component has documented justification
- Custom components don't duplicate config-driven functionality
- Complex visualization or interaction that can't be config-driven

#### Anti-Patterns to Flag:
- Custom table component when config-driven suffices
- Custom form dialog when ConfigurableFormDialogComponent works
- Custom search form when SearchConfig works
- Reinventing pagination, sorting, filtering

**ACTION**: Replace unnecessary custom components with config-driven patterns. Document justification for necessary custom components.

---

### 4. Data Flow Design (CRITICAL)

**Goal**: Ensure proper API → DTO → Mapper → ViewModel flow.

**Verify data flow**:

#### API Service Design:
- API service follows established pattern
- Uses `ApiService` base correctly
- Returns typed responses
- Handles errors appropriately

#### DTO Completeness:
- Response DTOs match expected API response structure
- Request DTOs match expected API request structure
- All fields have types defined
- Field descriptions present

#### View Model Design:
- View models optimized for UI display (not raw API response)
- All display fields present
- Calculated/derived fields defined
- Field names appropriate for template binding

#### Mapper Design:
- Mapper transforms Response → ViewModel
- All field mappings documented
- Transformations explained (date formatting, null handling, etc.)
- Static methods used correctly

**ACTION**: Complete DTO definitions, add missing view model fields, document mapper transformations.

---

### 5. UI Configuration Completeness (CRITICAL)

**Goal**: Ensure all UI configurations are complete and correct.

**Verify configurations**:

#### Search Form Config:
- All search fields from functional spec present
- Field types appropriate (TEXT, DATE, DROPDOWN, etc.)
- Labels user-friendly
- Required/optional correctly marked
- Dropdown options documented (or API source specified)

#### Table Columns Config:
- All display fields from functional spec present
- Column widths appropriate
- Sortable columns identified
- Format/pipe specified for dates, numbers, currency
- Column order logical

#### Form Fields Config:
- All create/edit fields from functional spec present
- Field types appropriate
- Validation rules complete (required, pattern, min/max)
- Field order logical for data entry
- Help text where needed

#### Menu Config (Panel Work Unit):
- Menu actions **match the inventory** - each action should have a corresponding entry point folder
- Discover actions by finding sibling folders with pattern `{panel-key}-{action}` that have `elementType: "ui-menu-action"`
- Each action's `actionName` and `actionType` from `metadata.json` informs the menu configuration
- If inventory has `print`, `table-filter`, or `export` action types, use `createStandardTableMenu()`
- If inventory only has `modal-crud` actions (e.g., New, Modify), do NOT include `createStandardTableMenu()`
- All inventoried actions should be documented in the menu configuration

**Verification Process**:
1. List folders in `./docs/entry-points/ui-features/` starting with the panel's key
2. Read `metadata.json` from each action folder to get `actionName` and `actionType`
3. Verify the plan's menu items match the discovered actions exactly

**ACTION**: Verify menu items match inventory. Remove items not in inventory. Add missing items that ARE in inventory.

---

### 6. State Management Design

**Goal**: Ensure component state is well-designed.

**Verify state management**:

#### State Properties:
- All necessary state properties defined
- Types specified for all state
- Initial values documented
- Loading states handled

#### State Flow:
- State changes documented for each user action
- Side effects (API calls) identified
- Refresh/reload patterns defined
- Selection state handled (if master-detail)

#### No Anti-Patterns:
- No direct state mutation (use immutable patterns)
- No state stored in services unnecessarily
- No orphaned state that's never used

**ACTION**: Complete state definitions, document state flow, fix anti-patterns.

---

### 7. Validation Design

**Goal**: Ensure client-side validation is comprehensive.

**Verify validation**:

#### Validation Rules:
- All validation rules from functional spec implemented
- Angular validators specified (Validators.required, etc.)
- Custom validators documented if needed
- Error messages defined

#### Cross-Field Validation:
- Dependencies between fields documented
- Validation timing specified (on change, on blur, on submit)

#### Validation Coverage:
- Every required field has required validator
- Format fields have pattern validators
- Numeric fields have min/max where applicable
- Date fields have range constraints where applicable

**ACTION**: Add missing validators, document error messages, complete cross-field validation.

---

### 8. Error Handling Design

**Goal**: Ensure error scenarios are properly handled.

**Verify error handling**:

#### Error Scenarios:
- API errors handled (400, 404, 500)
- Validation errors displayed properly
- Network errors handled
- Concurrent modification handling (if applicable)

#### Error Display:
- Uses `AppDialogService` for error dialogs
- Form field errors shown inline
- User-friendly messages defined
- No technical error messages exposed to users

**ACTION**: Complete error scenario coverage, add missing handlers, improve error messages.

---

### 9. Placeholder Feature Compliance (CRITICAL)

**Goal**: Ensure placeholder features are NOT implemented.

**Verify no implementation of placeholder features**:

| Feature | Should NOT Be Implemented | What to Do Instead |
|---------|--------------------------|-------------------|
| Authorization/Permissions | No `PermissionService`, no route guards | Add TODO comment |
| Toast Notifications | No `NotificationService` | Use `console.log` + `dialogService.showError` |
| File Upload | No file upload components | Create placeholder panel |
| Keyboard Shortcuts | No keyboard handlers | Skip entirely |
| Audit Trail | No audit components | Create placeholder panel |
| Cascading Dropdowns | No cascade logic | Use independent dropdowns |
| Bulk Operations | No multi-select operations | Single selection only |
| Charts/Visualizations | No chart components | Create placeholder panel |

**ACTION**: Remove any implementation of placeholder features. Replace with TODO comments or placeholder panels.

---

### 10. Requirements Traceability

**Goal**: Ensure all functional requirements are addressed by the UI design.

**Verify coverage**:

#### Input Coverage:
- Every functional input has a form field or search field
- Field types appropriate for data type
- Validation matches functional spec constraints

#### Output Coverage:
- Every functional output has a table column or display element
- Formatting matches functional spec requirements
- All data from functional spec is displayed

#### Action Coverage:
- Every use case has UI mechanism to trigger it
- CRUD operations all have menu items/buttons
- Workflows can be completed through UI

#### Business Rule Coverage:
- Validation rules from functional spec implemented
- Conditional logic documented
- Error conditions have user feedback

**ACTION**: Add missing fields/columns, complete action coverage, document business rule implementation.

---

### 11. Core Component Selection

**Goal**: Ensure appropriate Core Components are used (configuration-driven wrappers around Kendo UI).

**Verify Core Component usage**:

#### Component Selection:
- Uses `TableSearchLayoutComponent` for page layout (not custom layouts)
- Uses `SearchFormComponent` via `SearchConfig` (not custom search forms)
- Uses `DataTableComponent` via `PanelConfig` (not custom table components)
- Uses `ConfigurableFormDialogComponent` for modals (not custom dialogs)
- Uses `AppDialogService` for confirm/alert/error dialogs

#### Form Input Components:
- Uses `FieldType` enum for field type selection
- Uses `FieldConfig[]` for form field definitions
- Available types: TEXT, DATE, DROPDOWN, LOOKUP, CHECKBOX

#### Configuration Approach:
- Configuration objects documented (`SearchConfig`, `PanelConfig[]`, `FieldConfig[]`)
- No direct Kendo component usage when Core Component exists
- Custom components only when Core Component won't work (with justification)

**ACTION**: Replace direct Kendo usage with Core Components. Document why if custom component is required.

---

### 12. Routing and Navigation

**Goal**: Ensure routing is properly configured.

**Verify routing**:

#### Route Definition:
- Route path defined
- Route matches convention (`/{domain}/{feature}`)
- Component specified
- Data properties (title) set

#### Menu Integration:
- Menu item defined for navigation
- Menu placement appropriate
- Icon specified (if applicable)

**ACTION**: Complete routing configuration, add menu registration.

---

### 13. Testing Strategy

**Goal**: Ensure testing approach is adequate.

**Verify testing**:

#### Test Scenarios:
- Component render tests defined
- User interaction tests defined
- Form validation tests defined
- API integration tests defined

#### Mock Strategy:
- Services mocked appropriately
- Test data documented
- Async handling specified

**ACTION**: Complete testing strategy, add missing test scenarios.

---

### 14. Structural Completeness

**Goal**: Ensure all required sections are present.

**Required sections for UI features**:
- Executive Summary
- Page Pattern Selection
- Component Architecture (with diagram)
- Data Flow Design (DTOs, ViewModels, Mappers)
- UI Configuration Design (Search, Table, Form, Menu)
- State Management
- Validation Design
- Error Handling
- Placeholder Features section
- Routing Configuration
- Testing Strategy
- Open Questions
- References

**ACTION**: Add missing sections, complete partial sections.

---

### 15. data-testid Planning (MANDATORY)

**Goal**: Ensure the plan specifies `data-testid` values for all key elements.

**Convention to enforce**:
- HTML attribute: `data-testid` (all lowercase, no hyphen between "test" and "id")
- Angular `@Input()` property: `dataTestId` (camelCase)
- Naming format: `{domain}-{component}-{element}` (kebab-case, lowercase)

**Verify plan includes a data-testid reference table in the Component Architecture section:**

For **Page Setup** plans:
- [ ] Page wrapper value specified (e.g. `company-contact-page`)
- [ ] Grid value specified (e.g. `company-contact-grid`)
- [ ] Search form value specified
- [ ] Button values specified for all action buttons

For **Panel** plans:
- [ ] Panel grid value specified
- [ ] Context menu button values specified per action

For **Modal** plans:
- [ ] Dialog container value specified
- [ ] Each form field value specified
- [ ] Save/Cancel button values specified

**Check for wrong formats**:
- Any `data-test-id` reference → **CRITICAL: correct to `data-testid`**
- Any `dataTestid` (lowercase 'd' at end) → **CRITICAL: correct to `dataTestId`**
- Any values with spaces, underscores, or uppercase → **flag as naming violation**

**ACTION**: If data-testid reference table is missing, add it. Correct any wrong formats found.

---

## Phase 3: Correction Priorities

When making corrections, prioritize:

1. **CRITICAL** - Must fix:
   - Wrong pattern selection
   - Missing config-driven patterns (using custom when config works)
   - Incomplete data flow (missing DTOs, ViewModels, Mappers)
   - Placeholder features incorrectly implemented
   - Missing UI configurations

2. **HIGH** - Should fix:
   - Incomplete validation rules
   - Missing requirements traceability
   - Component hierarchy issues
   - State management gaps

3. **MEDIUM** - Fix if time permits:
   - Testing strategy gaps
   - Documentation clarity
   - Error message improvements

4. **LOW** - Optional:
   - Formatting improvements
   - Style preferences

**Preserve what's good**: Don't rewrite things that are already correct.

---

## Phase 4: Generate Review Report

Create `implementation-plan-review.md` in the same directory.

### If Issues Were Found and Corrected

```markdown
# Implementation Plan Review Report (UI Feature)

> **Reviewed**: [date]
> **Plan**: [path to implementation-plan.md]
> **Source Spec**: [path to functional-spec.md]
> **Feature Type**: UI Feature
> **Status**: PASSED WITH CORRECTIONS

## Executive Summary

[2-3 sentences: Overall assessment and summary of corrections made]

## Pattern & Architecture Alignment

| Aspect | Status | Notes |
|--------|--------|-------|
| Page Pattern | ✓/Corrected | [Details] |
| Component Hierarchy | ✓/Corrected | [Details] |
| Config-Driven Compliance | ✓/Corrected | [Details] |
| Data Flow | ✓/Corrected | [Details] |

## Screenshot Alignment

[If screenshots exist in the entry point directory]

| Screenshot | What It Shows | Plan Alignment |
|------------|---------------|----------------|
| [filename.png] | [Layout/Panel/Modal] | ✓ Matches / Corrected |

| Element | Screenshot Shows | Plan Has | Status |
|---------|------------------|----------|--------|
| Layout Pattern | [e.g., two-column with tabs] | [plan's layout] | ✓/Corrected |
| Tabs/Panels | [list from screenshot] | [list from plan] | ✓/Corrected |
| Grid Columns | [columns visible] | [columns in config] | ✓/Corrected |
| Form Fields | [fields visible] | [fields in config] | ✓/Corrected |

## Corrections Made

### Critical Issues Corrected

| Issue | Category | Location | Correction |
|-------|----------|----------|------------|
| [Description] | [Pattern/Config/DataFlow/etc.] | [Section] | [What was changed] |

### High Priority Issues Corrected

| Issue | Category | Location | Correction |
|-------|----------|----------|------------|
| [Description] | [Category] | [Section] | [What was changed] |

### Medium/Low Priority Issues Corrected

| Issue | Category | Location | Correction |
|-------|----------|----------|------------|
| [Description] | [Category] | [Section] | [What was changed] |

## Configuration Completeness

| Config Type | Status | Issues Found | Corrections |
|-------------|--------|--------------|-------------|
| Search Form | ✓/Corrected | [N] | [Summary] |
| Table Columns | ✓/Corrected | [N] | [Summary] |
| Form Fields | ✓/Corrected | [N] | [Summary] |
| Menu Items | ✓/Corrected | [N] | [Summary] |

## Data Flow Completeness

| Component | Status | Notes |
|-----------|--------|-------|
| Response DTOs | ✓/Corrected | [Details] |
| View Models | ✓/Corrected | [Details] |
| Request DTOs | ✓/Corrected | [Details] |
| Mappers | ✓/Corrected | [Details] |

## Placeholder Feature Compliance

| Feature | Status | Notes |
|---------|--------|-------|
| Authorization | ✓ Not implemented / ⚠️ Removed | [Details] |
| Notifications | ✓ Not implemented / ⚠️ Removed | [Details] |
| File Upload | ✓ Not implemented / ⚠️ Removed | [Details] |
| [Other] | ✓/⚠️ | [Details] |

## Requirements Traceability

| Requirement Type | Coverage | Gaps Addressed |
|------------------|----------|----------------|
| Form Inputs | [%] | [Summary] |
| Table Outputs | [%] | [Summary] |
| User Actions | [%] | [Summary] |
| Validation Rules | [%] | [Summary] |

## Issues Requiring Human Review

[If any issues couldn't be automatically corrected]

| Issue | Category | Location | Recommendation |
|-------|----------|----------|----------------|
| [Description] | [Category] | [Section] | [What human should do] |

## Quality Metrics

| Metric | Value |
|--------|-------|
| Total Issues Found | [N] |
| Critical Issues | [N] |
| High Priority Issues | [N] |
| Medium/Low Issues | [N] |
| Auto-Corrected | [N] |
| Needs Human Review | [N] |

## Certification

- [x] Implementation plan is now ready for UI implementation
- [x] Frontend architecture alignment verified
- [x] Configurations complete for development
- [x] No placeholder features implemented
- [x] data-testid reference table present with correct naming convention

---

*Review completed by Legacy Analyzer Agent*
```

### If No Issues Found

```markdown
# Implementation Plan Review Report (UI Feature)

> **Reviewed**: [date]
> **Plan**: [path to implementation-plan.md]
> **Source Spec**: [path to functional-spec.md]
> **Feature Type**: UI Feature
> **Status**: PASSED

## Summary

The UI implementation plan meets all quality criteria. No corrections were required.

All review checks passed:
- ✓ Appropriate page pattern selected
- ✓ Component architecture well-designed
- ✓ Config-driven patterns used correctly
- ✓ Data flow complete (DTOs, ViewModels, Mappers)
- ✓ UI configurations complete
- ✓ No placeholder features implemented
- ✓ Requirements traceability maintained
- ✓ All sections complete

## Certification

- [x] Implementation plan is ready for UI implementation
- [x] Frontend architecture alignment verified
- [x] Configurations complete for development

---

*Review completed by Legacy Analyzer Agent*
```

### If Major Issues Found

```markdown
# Implementation Plan Review Report (UI Feature)

> **Reviewed**: [date]
> **Plan**: [path to implementation-plan.md]
> **Source Spec**: [path to functional-spec.md]
> **Feature Type**: UI Feature
> **Status**: NEEDS MAJOR REVISION

## Summary

This UI implementation plan requires significant rework and cannot be adequately corrected through editing alone.

## Critical Problems

1. [Fundamental issue #1 - e.g., "Wrong pattern selected - should be Master-Detail not CRUD"]
2. [Fundamental issue #2 - e.g., "No data flow design - missing all DTOs and ViewModels"]
3. [Fundamental issue #3 - e.g., "Implements authorization which is a placeholder feature"]

## Recommendation

Return to planning phase using the `/develop.create-plan-ui` command with closer attention to:
- [Specific guidance]
- [Specific guidance]

---

*Review completed by Legacy Analyzer Agent*
```

---

## Execution Instructions

1. **Parse the key and type parameters** from the command invocation

2. **Construct the directory path**: `./docs/entry-points/{type}/{key}/`

3. **Read all relevant files from the directory**:
   - `implementation-plan.md` (required)
   - `functional-spec.md` (required for traceability)
   - `metadata.json` (for context)
   - Frontend architecture documents

4. **Systematically work through each review check**

5. **Make corrections directly** to implementation-plan.md as you find issues

6. **Track all findings** for the report

7. **Generate the review report** as `implementation-plan-review.md` in the same directory

8. **Provide brief summary** to user of review outcome

---

## Begin

The user will invoke this command with key and type parameters. Use these to locate the entry point directory at `./docs/entry-points/{type}/{key}/`, then read the required files and begin the review process.
