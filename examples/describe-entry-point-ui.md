# Describe Entry Point - UI

Create a detailed functional description of a UI entry point (page, screen, component) by analyzing its code, component tree, API dependencies, and user interaction logic.

## Common Foundation

@describe-entry-point-common.md

## Usage

```
/describe-entry-point-ui path: <path-to-entry-point-analysis-folder>
```

**Example:**
```
/describe-entry-point-ui path: ./docs/entry-points/ui-features/company-contact-list-page/
```

## UI-Specific Context

This command is for analyzing **User Interface entry points** including:
- Pages and screens
- Complex components
- Dialogs and modals
- Forms
- Dashboards

The analysis focuses on **user interactions, visual presentation, state management, and API consumption**.

## Work Unit Type Detection (CRITICAL - Do First)

UI features follow a hierarchical structure. **Detect the work unit type from the key pattern FIRST** to determine the appropriate analysis focus:

| Key Pattern | Work Unit Type | Example | Analysis Focus |
|-------------|---------------|---------|----------------|
| `{id}-{path}-{page}` | **Page Setup** | `2105-infrastructure-company-company-maintenance` | Overall screen structure, navigation, content area organization, search/filter |
| `{id}-{path}-{page}-{panel}` | **Panel** | `2105-...-company-maintenance-grid` | Data display, selection behavior, available actions, relationship to other panels |
| `{id}-{path}-{page}-{panel}-{action}` | **Modal** | `2105-...-company-maintenance-grid-modify` | Form fields, validation rules, submission behavior, data changes |

### Detection Logic

1. **Page Setup**: Key ends with the page name (e.g., `company-maintenance`) with no panel/action suffix
2. **Panel**: Key has one additional segment after page (e.g., `company-maintenance-grid`, `company-maintenance-details`)
3. **Modal**: Key has action suffix (e.g., `-modify`, `-new`, `-attach-document`, `-view-attachment`)

### Analysis Focus by Work Unit Type

**Page Setup Analysis** should emphasize:
- Overall screen purpose and business task enabled
- Navigation context (how users reach this screen, where they go next)
- Content area organization (panels, tabs, sections visible on page)
- Search/filter capabilities (what criteria users can search by)
- Relationships between content areas (master-detail, tabbed, independent)
- Which panels/tabs exist and their high-level purpose (NOT internal panel details)
- Page-level state management and initialization

**Panel Analysis** should emphasize:
- Panel's specific purpose within the page
- Data elements displayed (columns, fields) with business meaning
- Selection behavior and its effects (what happens when user selects an item)
- Available user actions (context menu items, toolbar buttons)
- Relationship to other panels (e.g., "selection updates detail panel")
- What modals/actions this panel triggers (NOT modal internal details)
- Panel-specific API calls and data loading

**Modal Analysis** should emphasize:
- Form purpose (what data is being collected/modified and why)
- Form fields with business meaning and required indicators
- Field groupings/sections
- Validation rules in business terms
- Submission behavior and outcomes
- Success/failure/cancel behaviors
- What data changes result from submission
- Pre-population logic (where initial values come from)

### Adjusting Template Sections by Work Unit Type

**For Page Setup**: Focus on Component Details and Workflows
- Emphasize overall page structure and navigation
- Document all tabs/panels visible at high level
- Search/filter capabilities in User Inputs
- De-emphasize Form Fields (pages rarely have forms directly)
- Workflows should cover page initialization and inter-panel coordination

**For Panel**: Focus on Rendered Content + User Interactions
- Emphasize data display with all visible columns/fields
- Document User Interactions (especially selection, context menu)
- Include selection behavior effects in Workflows
- De-emphasize Form Fields unless panel has inline editing
- Document relationship to parent page and sibling panels

**For Modal**: Focus on User Inputs (Form Fields) + Workflows
- Emphasize Form Fields table with all fields
- Document validation rules thoroughly
- Include form submission workflow completely
- De-emphasize Component Details (modals have simpler structure)
- Document pre-population and data flow

## Screenshot Analysis (When Available)

**AFTER detecting work unit type**, check for screenshots in the entry point's `screenshots/` directory. Screenshots provide valuable visual reference of the legacy UI and help validate code analysis.

### Why Use Screenshots?

- Screenshots show the **actual legacy UI** being analyzed
- They provide **visual confirmation** of layout, fields, and user interactions
- They help **validate** the code analysis findings
- They reveal **UI details** that may not be obvious from code alone
- They provide **business context** through visible labels and organization

### Screenshot Analysis Process

1. **Check for screenshots** at `{entry_point_analysis}/screenshots/`
2. **If screenshots exist**, review each one and note:
   - What business task this screen enables
   - What content areas are visible (panels, sections, tabs)
   - What data elements are displayed (field labels, column headers)
   - What user actions are available (buttons, menus, context menus)
   - What visual indicators exist (required field highlighting, status badges)
3. **Cross-reference** screenshot observations with code analysis
4. **Use observations** to validate and enrich:
   - User Inputs section (form fields, interactions)
   - Rendered Content section (what's displayed)
   - Visual States section (loading indicators, error displays)
5. **Flag discrepancies** between screenshots and code in Analysis Notes

### Visual Element Interpretation Guide

When reviewing screenshots, identify UI patterns to document user interactions:

| Visual Appearance | Business Interpretation | Document As |
|-------------------|------------------------|-------------|
| Input with `...` button | User can type OR select from a list via dialog | Lookup field with search dialog |
| Dropdown with `▼` arrow | User selects from predefined options | Selection from dropdown list |
| Plain text input | Free-form text entry | Text input field |
| Checkbox control | Toggle yes/no option | Boolean checkbox |
| Input with calendar icon | Date selection | Date picker field |
| Orange/highlighted field | Required for submission | Mark as Required: Yes |
| Grayed/disabled field | Read-only or conditionally disabled | Note display-only or conditions |
| Multi-line text area | Extended text entry | Text area for comments/notes |
| Grid with column headers | Tabular data display | Data grid with columns |
| Tab strip | Multiple content sections | Tabbed interface |

### What to Extract from Screenshots (by Work Unit Type)

#### For Page Setup Screenshots:
| Element | What to Look For | Use In Description |
|---------|-----------------|-------------------|
| **Layout Pattern** | Two-column, tabbed, master-detail | Component Details, overall structure |
| **Panel/Section Names** | Headers, tab labels, section titles | Rendered Content areas |
| **Search Form** | Filter fields at top | User Inputs (form fields) |
| **Navigation Elements** | Menu location, breadcrumbs | Navigation/Routing section |
| **Toolbar Actions** | Buttons, menu items | User Interactions |

#### For Panel Screenshots:
| Element | What to Look For | Use In Description |
|---------|-----------------|-------------------|
| **Column Headers** | All visible column labels | Rendered Content (data display) |
| **Data Examples** | Sample data visible in cells | Business meaning context |
| **Selection Indicators** | Highlighted rows, checkboxes | User Interactions (selection) |
| **Context Menu** | Right-click menu if visible | User Interactions (actions) |
| **Toolbar/Action Buttons** | Panel-specific actions | User Interactions |

#### For Modal Screenshots:
| Element | What to Look For | Use In Description |
|---------|-----------------|-------------------|
| **Field Labels** | All input field labels | User Inputs (form fields) |
| **Required Indicators** | Highlighted/marked fields | Required column in form fields |
| **Field Groupings** | Sections/fieldsets in form | Form structure description |
| **Action Buttons** | Save, Cancel, other actions | User Interactions |
| **Validation Messages** | Any visible error messages | Validation rules |

## Input Structure

The UI entry point analysis folder contains:

```
{entry_point_analysis}/
├── metadata.json              # Entry point metadata (key, location, type, notes)
├── component-tree.txt         # Component hierarchy from entry point
├── code/                      # Extracted code tree matching component-tree.txt
│   └── [ComponentName.tsx.md] # Markdown files with extracted component code
├── api-dependencies.json      # API endpoints called by this UI
├── state-dependencies.json    # State stores/contexts used (optional)
└── screenshots/               # Legacy UI screenshots (optional but valuable)
    └── *.png                  # One or more screenshots of the UI
```

**Note on Screenshots**: The `screenshots/` directory is optional but highly valuable when available. Screenshots provide visual confirmation of the UI structure and help validate code analysis findings. See "Screenshot Analysis" section above for how to use them.

## Output Structure

The command creates files in the entry point analysis folder:

**During Analysis (In Progress)**:
```
{entry_point_analysis}/functional-description.in-progress.md
```

**After Completion**:
```
{entry_point_analysis}/functional-description.md
```

**Status Indication**:
- `.in-progress.md` suffix indicates analysis is actively running or crashed mid-way
- `.md` (no suffix) indicates analysis completed successfully
- This allows easy identification of incomplete analyses for recovery or restart

## Analysis Process

### Phase 0: Work Unit Type Detection and Screenshot Review (CRITICAL - Do First)

1. **Read metadata.json** to get the entry point key
2. **DETECT WORK UNIT TYPE** from key pattern:
   - **Page Setup**: Key ends with page name (e.g., `company-maintenance`)
   - **Panel**: Key has panel suffix (e.g., `company-maintenance-grid`, `company-maintenance-details`)
   - **Modal**: Key has action suffix (e.g., `company-maintenance-grid-modify`, `-new`, `-delete`)
3. **Note the analysis focus** based on work unit type (see "Analysis Focus by Work Unit Type" above)
4. **Check for screenshots** at `{entry_point_analysis}/screenshots/`
5. **If screenshots exist**, analyze each one:
   - Document the screen/panel/modal purpose and layout
   - List all visible content areas (panels, tabs, sections)
   - Extract all field labels and column headers
   - Note required field indicators (highlighting)
   - Identify available user actions (buttons, menus)
   - Create mental model of UI structure to guide code analysis
6. **Document screenshot observations** (will be used to validate and enrich code analysis)

### Phase 1: Context Gathering and Initial Setup

1. **Read metadata.json** fully to understand UI entry point type, location, and key context
2. **Read component-tree.txt** to understand the component hierarchy
3. **Read api-dependencies.json** to identify all API calls
4. **Read state-dependencies.json** (if exists) to understand state management
5. **Scan code/ directory** to understand available extracted components
6. **CHECK SHARED PATTERNS**: Read `docs/shared-functional-descriptions/index.md`
7. **Cross-reference with screenshot observations** (if screenshots were analyzed in Phase 0)
8. **Create initial todo list** for tracking analysis progress
9. **WRITE: Create functional-description.in-progress.md with template structure**
   - Include work unit type in metadata header
   - Adjust template sections based on work unit type focus
10. **WRITE: Executive Summary section**
    - Mention work unit type and its role in the UI hierarchy
    - Reference parent page if this is a Panel or Modal

### Phase 2: UI Analysis and Input/Output Documentation

**Adjust focus based on work unit type detected in Phase 0.**

1. **Read extracted component files** from the code/ directory
2. **ANALYZE AND WRITE: Identify all user inputs** (emphasize for Modals)
   - Form fields and their validations
   - User interactions (clicks, selections, drags)
   - URL/route parameters
   - Query string parameters
   - **Validate against screenshots**: Ensure all visible fields from screenshots are documented
   - **WRITE to functional-description.in-progress.md**: Update User Inputs section
3. **ANALYZE AND WRITE: Identify all API calls**
   - Which endpoints are called
   - When they are called (on mount, on action, etc.)
   - What data is sent/received
   - **WRITE to functional-description.in-progress.md**: Update API Dependencies section
4. **ANALYZE AND WRITE: Identify all outputs** (emphasize for Pages and Panels)
   - Rendered content and components
   - Navigation/routing changes
   - State updates
   - Browser storage changes
   - **Validate against screenshots**: Ensure all visible content areas from screenshots are documented
   - **WRITE to functional-description.in-progress.md**: Update Outputs section
5. **Map user interaction logic** (collect for workflow writing)
   - **For Pages**: Focus on navigation and inter-panel coordination
   - **For Panels**: Focus on selection behavior and triggered actions
   - **For Modals**: Focus on form submission flow
   - **Verify action locations**: For each button/action, confirm WHERE it appears:
     - Search bar buttons (page-level, e.g., `w-search-bar button-label`) → document in search/filter section
     - Panel menu items (e.g., `menu-items="vm.menuItems"`) → verify against actual array in controller code
     - Do NOT assume a function name implies a menu item exists
6. **WRITE: Key Business Rules section** as discovered
7. **WRITE: Validation Rules section** as discovered (emphasize for Modals)

### Phase 3: State and Component Analysis

1. **For each significant component**:
   - Understand its props and state
   - Identify user interactions it handles
   - Note any conditional rendering logic
   - **WRITE to functional-description.in-progress.md**: Add to Component Details section
2. **For each state dependency**:
   - Identify what state is read
   - Identify what state is modified
   - Understand state lifecycle
   - **WRITE**: Add to State Management section
3. **VERIFY**: Component and state sections complete before workflows

### Phase 4: User Interaction Workflow Documentation

**CRITICAL: Write each workflow as you complete it!**

1. **Identify major user journeys**:
   - Primary user task flow
   - Alternative paths (search, filter, etc.)
   - Error handling and recovery paths
2. **For EACH workflow**:
   - Document user action triggers
   - Map state changes
   - Include API call sequences
   - Note visual feedback
   - **WRITE to functional-description.in-progress.md**: Complete workflow BEFORE next

### Phase 5: Use Case Extraction and Finalization

1. **Identify business use cases** from workflow analysis
2. **Frame as user stories**
3. **WRITE**: Add each use case
4. **WRITE**: Visual States section
5. **WRITE**: Accessibility Considerations section (if applicable)
6. **WRITE**: Analysis Notes section
7. **Final review and rename file**

## UI-Specific Output Template

```markdown
# Functional Description: [UI Entry Point Name]

> **Entry Point**: [key from metadata.json]
> **Location**: [location from metadata.json]
> **Type**: UI / [Page | Component | Dialog | Form]

## Executive Summary

[2-3 paragraph overview of this UI's purpose, key functionality, and user context]

## User Inputs

### Form Fields

| Field | Type | Label | Required | Validation | Business Meaning |
|-------|------|-------|----------|------------|------------------|
| fieldName | text/select/etc | Display Label | Yes/No | Rules | What this collects |

### User Interactions

| Interaction | Element | Trigger | Business Purpose |
|-------------|---------|---------|------------------|
| Click | Button/Link | On click | What happens |
| Select | Dropdown | On change | What it affects |
| Drag | List item | On drag end | Reordering purpose |

### URL/Route Parameters

| Parameter | Source | Required | Business Meaning |
|-----------|--------|----------|------------------|
| :id | URL path | Yes | Identifies the resource |
| tab | Query string | No | Active tab selection |

### Browser/Session Inputs

| Source | Data | Purpose |
|--------|------|---------|
| localStorage | userPrefs | Persisted user settings |
| sessionStorage | tempData | Session-specific state |
| Cookie | authToken | Authentication context |

## Outputs

### Rendered Content

| Content Area | Description | Conditions | Data Source |
|--------------|-------------|------------|-------------|
| Header | Page title and actions | Always | Static + props |
| Data Table | List of items | When data loaded | API response |
| Empty State | No data message | When list empty | Static |

### Navigation/Routing

| Trigger | Destination | Conditions | Data Passed |
|---------|-------------|------------|-------------|
| Save button | /details/:id | On success | Created ID |
| Cancel button | Previous page | Always | None |
| Row click | /item/:id | Always | Item ID |

### State Changes

| State | Change Type | Trigger | Business Impact |
|-------|-------------|---------|-----------------|
| formData | Update | Field change | Form state |
| selectedItems | Add/Remove | Checkbox | Selection for bulk action |
| isLoading | Toggle | API call | Loading indicator |

### Browser Storage Updates

| Storage | Key | When Updated | Data Stored |
|---------|-----|--------------|-------------|
| localStorage | lastSearch | On search | Search criteria |
| sessionStorage | formDraft | On field change | Unsaved form data |

### Analytics/Tracking Events

| Event | Trigger | Data Sent | Purpose |
|-------|---------|-----------|---------|
| page_view | On mount | Page name | Usage tracking |
| button_click | On action | Action name | Interaction tracking |

## API Dependencies

### API Calls Made

| Endpoint | Method | When Called | Request Data | Response Used For |
|----------|--------|-------------|--------------|-------------------|
| /api/items | GET | On mount | filters, page | Populate list |
| /api/items/:id | PUT | On save | form data | Update item |
| /api/items/:id | DELETE | On delete | - | Remove item |

### API Call Sequences

**On Page Load**:
1. Call `/api/user/preferences` to get display settings
2. Call `/api/items` with default filters
3. Render list when both complete

**On Form Submit**:
1. Validate form client-side
2. Call `/api/items` POST or PUT
3. On success: navigate to list
4. On error: display error message

## State Management

### Local Component State

| State Variable | Type | Initial Value | Purpose |
|----------------|------|---------------|---------|
| isOpen | boolean | false | Modal visibility |
| formData | object | {} | Form field values |
| errors | object | {} | Validation errors |

### Global/Shared State

| Store/Context | State Accessed | Operations | Purpose |
|---------------|----------------|------------|---------|
| UserContext | currentUser | Read | Display user info |
| ItemsStore | items, loading | Read/Write | Item list management |
| NotificationContext | - | dispatch | Show toast messages |

### State Lifecycle

| State | Created | Updated | Cleared |
|-------|---------|---------|---------|
| formData | On mount (from props) | On field change | On submit success |
| selectedItems | Empty array | On checkbox | On bulk action complete |

## Component Details

### Primary Component: [ComponentName]

**Purpose**: [What this component does]

**Props**:
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| itemId | string | Yes | ID of item to display |
| onSave | function | Yes | Callback on save |

**Key Behavior**:
- [Behavior 1]
- [Behavior 2]

**Child Components**:
- [ChildComponent1]: [Purpose]
- [ChildComponent2]: [Purpose]

---

### Subcomponent: [ChildComponentName]

[Same structure]

## Workflows

### Workflow 1: [Primary User Task Name]

**Use Case**: [What the user is trying to accomplish]

**Actors**: [User role(s)]

**Preconditions**: [What must be true before this flow]

**Steps**:

1. **[User Action]** - [What the user does]
   - **UI Element**: [Button/Form/etc]
   - **Visual Feedback**: [Loading spinner, disabled state, etc.]

2. **[System Response]** - [What the UI does]
   - **API Call**: [If applicable]
   - **State Change**: [What state updates]
   - **Visual Update**: [What the user sees]

3. **[Next User Action or System Response]**
   - **Validation**: [Any validation that occurs]
   - **Error Handling**: If [error], show [message]

[Continue for all steps]

**Success Outcome**: [What the user sees on success]

**Error Paths**:
- [Error scenario 1]: [What user sees, recovery options]
- [Error scenario 2]: [What user sees, recovery options]

---

### Workflow 2: [Alternative User Task]

[Same structure]

---

## Visual States

### Loading States

| Context | Indicator | User Feedback |
|---------|-----------|---------------|
| Initial page load | Full page spinner | "Loading..." |
| Data refresh | Inline spinner | Table skeleton |
| Form submit | Button disabled + spinner | "Saving..." |

### Error States

| Error Type | Display Location | Message Pattern | Recovery Action |
|------------|-----------------|-----------------|-----------------|
| API failure | Toast notification | "Failed to load. Try again." | Retry button |
| Validation | Inline under field | Field-specific message | Fix and resubmit |
| Not found | Full page | "Item not found" | Back button |

### Empty States

| Context | Message | Call to Action |
|---------|---------|----------------|
| No search results | "No items match your search" | Clear filters button |
| No data exists | "No items yet" | Create first item button |

### Success States

| Action | Indicator | Duration | Next Step |
|--------|-----------|----------|-----------|
| Save | Toast "Saved successfully" | 3 seconds | Auto-dismiss |
| Delete | Toast "Deleted" | 3 seconds | List refreshes |

## Use Cases

### UC-1: [Use Case Title]

**Description**: [What the user wants to accomplish]

**User Story**: As a [role], I want to [action] so that [value]

**Workflow**: Workflow 1

**Frequency**: [How often - if known]

---

## Security Considerations

### Route Protection

- **Authentication Required**: [Yes/No]
- **Role Restrictions**: [Roles that can access]
- **Redirect on Unauthorized**: [Where sent if not authorized]

### Data Security

- **Sensitive Data Displayed**: [Any PII, financial, etc.]
- **Masking Applied**: [What is masked and when]
- **Secure Input Handling**: [Password fields, etc.]

### Client-Side Security

- **XSS Prevention**: [How user input is sanitized]
- **CSRF Protection**: [Token handling if applicable]

## Accessibility Considerations

- **Keyboard Navigation**: [How keyboard users navigate]
- **Screen Reader Support**: [ARIA labels, roles]
- **Focus Management**: [Modal focus trapping, etc.]
- **Color Contrast**: [Any known issues]

## Integration Points

### Upstream (Data Sources)

| Source | Purpose | Failure Impact |
|--------|---------|----------------|
| API Endpoint | Data retrieval | Show error state |
| Auth Service | User context | Redirect to login |

### Downstream (Affected Systems)

| System | What This UI Affects | How |
|--------|---------------------|-----|
| Backend API | Data modifications | Via API calls |
| Analytics | Usage data | Event tracking |

## Analysis Notes

[Any additional observations, uncertainties, or areas requiring further investigation]

- [Note 1]
- [Note 2]
```

## Example Execution

```
User: /describe-entry-point-ui path: ./docs/entry-points/ui-features/company-maintenance-details/

Agent Response (Iterative Approach):

Phase 0 - Work Unit Type Detection and Screenshot Review (CRITICAL):
1. Reads metadata.json to get entry point key
2. ⚡ DETECTS WORK UNIT TYPE: Key is "company-maintenance-details"
   - Pattern: {page}-{panel} → This is a PANEL
   - Analysis Focus: Data display, selection behavior, relationship to parent page
3. Checks for screenshots at ./docs/entry-points/ui-features/company-maintenance-details/screenshots/
4. ⚡ SCREENSHOTS FOUND: company-details-panel.png
5. ⚡ ANALYZES SCREENSHOT:
   - Panel displays read-only company information
   - Organized into: Effective Dates bar, Company Name section, Company Information section
   - 23 fields identified from labels (Common, Legal, FERC, Fed Taxpyr, Status, etc.)
   - All fields appear disabled/grayed (read-only panel)
   - No action buttons visible in panel itself
6. Documents screenshot observations for validation during code analysis

Phase 1 - Context Gathering and Initial Setup:
7. Creates comprehensive todo list for analysis phases
8. Reads metadata.json fully to understand entry point context
9. Reads component-tree.txt to map component hierarchy
10. Reads api-dependencies.json overview
11. ⚡ CHECKS docs/shared-functional-descriptions/index.md for patterns
12. ⚡ DETECTS: This is a Detail View pattern (read-only display)
13. Cross-references with screenshot observations - confirms read-only panel structure
14. ⚡ WRITES functional-description.in-progress.md with template structure
    - Adjusts template: Emphasizes Rendered Content, de-emphasizes Form Fields
    - Includes work unit type (Panel) in metadata
15. ⚡ WRITES Executive Summary section:
    - Mentions this is a Panel within Company Maintenance page
    - Describes read-only detail display purpose
    - References parent page relationship

Phase 2 - Inputs and Outputs (Panel Focus):
16. Reads extracted component files from code/ directory
17. Analyzes user inputs - confirms read-only (no editable inputs)
18. ⚡ WRITES Form Fields table with all 23 fields marked "N/A (read-only)"
19. ⚡ WRITES User Interactions - selection from parent grid triggers data load
20. ⚡ VALIDATES against screenshot: All 23 fields from screenshot documented
21. Analyzes API calls - getCompany and getCompanyHistoryList
22. ⚡ WRITES API Dependencies section with call sequences
23. Analyzes rendered content - emphasizes this section per Panel focus
24. ⚡ WRITES detailed Rendered Content table (Date Bar, Name Section, Info Section)
25. ⚡ VALIDATES against screenshot: Content areas match observed structure

Phase 3 - State and Component Analysis:
26. Analyzes component props and state
27. ⚡ WRITES Component Details section - emphasizes data binding patterns
28. Documents relationship to parent controller (shared controller pattern)
29. Analyzes state dependencies
30. ⚡ WRITES State Management section with local and global state

Phase 4 - Workflows (Panel-Specific):
31. Identifies main workflow: View Company Details (triggered by grid selection)
32. Maps data flow from grid selection → API call → panel population
33. ⚡ WRITES Workflow 1 with:
    - Selection behavior triggering data load
    - Relationship to parent page grid
    - Visual feedback for loading states
34. Identifies secondary workflow: View Company History
35. ⚡ WRITES Workflow 2 with history tab population logic
36. ⚡ WRITES Visual States section (loading, empty, disabled states)

Phase 5 - Use Cases and Finalization:
37. Extracts business use cases from workflows
38. ⚡ WRITES Use Cases section with UC-1 through UC-5
39. ⚡ WRITES Security Considerations section
40. ⚡ WRITES Accessibility Considerations section (notes legacy gaps)
41. ⚡ WRITES Integration Points section - documents event bus communication
42. ⚡ WRITES Analysis Notes for uncertainties and modernization recommendations
43. Final review - validates all screenshot observations are documented
44. ⚡ RENAMES file: mv functional-description.in-progress.md functional-description.md
45. Marks all todos as completed

Result: Complete functional description created iteratively at:
./docs/entry-points/ui-features/company-maintenance-details/functional-description.md

Note:
- Phase 0 detected PANEL work unit type, adjusted analysis focus accordingly
- Screenshots analyzed FIRST, observations used to validate code analysis
- All 23 fields from screenshot confirmed in documentation
- Panel-specific focus: Emphasized rendered content, selection behavior, parent relationship
- File was built section-by-section during analysis, not dumped all at once
- The .in-progress.md suffix was used during analysis, then renamed to .md upon completion
```

## Advanced Features

### Handling Complex Component Hierarchies

When UI entry points have deep or complex component structures:

1. **Identify key components**: Focus on components with significant business logic or state
2. **Document parent-child relationships**: Understand props drilling and callbacks
3. **Map state flow**: Track where state is defined and how it propagates
4. **Note render optimization**: Identify any memoization or performance patterns

### Handling Complex User Interactions

For entry points with complex user interaction flows:

1. **Identify major vs minor interactions**:
   - Major: Different business scenarios (create vs edit vs view)
   - Minor: Simple UI toggles or cosmetic changes
2. **Create separate workflows for major interactions**
3. **Document minor variations within workflow steps**
4. **Use sequence diagrams for complex multi-step interactions** if helpful

### Validation and Quality Assurance

After creating functional description:

1. **Completeness check**: All inputs, outputs, workflows, visual states documented
2. **Accuracy check**: Cross-reference with extracted component code
3. **User perspective check**: Written for UX designers and product managers, not just developers
4. **Spec-ready check**: Sufficient detail to write design specifications
5. **Missing context check**: Identify any gaps requiring further investigation

## UI-Specific Success Criteria

In addition to common success criteria:

**Phase 0 Compliance (Work Unit Type & Screenshots)**:
- [ ] Work unit type detected from key pattern (Page Setup / Panel / Modal)
- [ ] Analysis focus adjusted based on work unit type
- [ ] Screenshots directory checked for available screenshots
- [ ] If screenshots exist, all screenshots analyzed before code analysis
- [ ] Screenshot observations documented and used to validate code analysis
- [ ] Discrepancies between screenshots and code flagged in Analysis Notes

**Work Unit Type Focus Verification**:
- [ ] **For Page Setup**: Overall screen structure, navigation, content areas emphasized
- [ ] **For Panel**: Data display, selection behavior, parent relationship emphasized
- [ ] **For Modal**: Form fields, validation rules, submission flow emphasized
- [ ] Template sections adjusted appropriately (emphasized/de-emphasized)

**UI Analysis Completeness**:
- [ ] All user input methods identified (forms, interactions, URL params)
- [ ] All API calls documented with trigger conditions
- [ ] Component hierarchy understood and documented
- [ ] State management patterns identified
- [ ] Visual states documented (loading, error, empty, success)
- [ ] User interaction flows mapped as workflows
- [ ] All visible elements from screenshots accounted for in documentation

**UI Documentation Quality**:
- [ ] Workflows written from user perspective
- [ ] Visual feedback documented for each action
- [ ] Error handling and recovery paths documented
- [ ] Accessibility considerations noted
- [ ] Parent/child relationships documented (for Panels and Modals)
- [ ] Executive summary mentions work unit type and hierarchical context

## UI-Specific Troubleshooting

### Work Unit Type Detection Issues

**Problem**: Unclear whether entry point is Page Setup, Panel, or Modal

**Solutions**:
1. **Check the key pattern** in metadata.json:
   - Page Setup: Key ends with page name only (e.g., `company-maintenance`)
   - Panel: Key has one additional segment (e.g., `company-maintenance-grid`, `company-maintenance-details`)
   - Modal: Key has action suffix (e.g., `-modify`, `-new`, `-delete`, `-view`)
2. **Look at the location** - Modal HTML files often have "new", "modify", or "popup" in the path
3. **Check parent references** - Panels and Modals should have `parentKey` in metadata.json
4. **Review screenshots** - Visual layout often makes work unit type obvious
5. **When in doubt**, document the ambiguity and analyze as the most likely type

**Problem**: Entry point doesn't fit standard Page/Panel/Modal hierarchy

**Solutions**:
1. Some UIs may be standalone components or widgets - document as appropriate
2. Use the closest matching work unit type for analysis focus
3. Note the deviation in Analysis Notes section
4. Adjust template sections based on actual UI characteristics

### Missing or Incomplete Screenshots

**Problem**: No screenshots available in screenshots/ directory

**Solutions**:
1. Proceed with code-only analysis
2. Note in Analysis Notes that screenshots were not available
3. Flag any UI structure assumptions that would benefit from visual confirmation
4. Recommend capturing screenshots during validation phase

**Problem**: Screenshots don't match the code being analyzed

**Solutions**:
1. Screenshots may be from a different version of the UI
2. Document discrepancies in Analysis Notes
3. Prioritize code analysis as source of truth for behavior
4. Use screenshots for visual context but validate against code
5. Flag differences for SME review

**Problem**: Screenshots show multiple screens/states

**Solutions**:
1. Analyze each screenshot separately
2. Document which screenshot shows which state (initial, after action, error, etc.)
3. Use multiple screenshots to understand the complete user flow
4. Reference specific screenshots in workflow documentation

### Missing Component Code

**Problem**: Expected component not in code/ directory

**Solutions**:
1. Check if component is in component-tree but extraction was skipped
2. Use symbol-body-extractor subagent to extract specific missing component
3. Check if component is from a third-party library (document as external dependency)
4. Document in Analysis Notes section if truly not available

### Complex State Management

**Problem**: State flow is difficult to trace

**Solutions**:
1. Map out state from root component to leaves
2. Identify all useState, useReducer, and context providers
3. Create a state flow diagram if complex
4. Document state dependencies between components
5. Note any global state management (Redux, MobX, Zustand, etc.)

### Unclear User Interaction Logic

**Problem**: Event handlers and callbacks are complex to trace

**Solutions**:
1. Start from UI elements (buttons, forms, etc.) and trace callback props
2. Document the component hierarchy for event bubbling
3. Note any event delegation patterns
4. Trace async operations to their resolution (success/error handling)
5. Document in Analysis Notes and flag for SME review

### Missing API Documentation

**Problem**: API endpoints are called but not well documented

**Solutions**:
1. Cross-reference with api-dependencies.json
2. Use network inspection patterns to identify API calls
3. Look for fetch, axios, or other HTTP client usage
4. Document request/response shapes from code if API docs unavailable

## UI-Specific Shared Patterns

Common UI patterns to check for:

1. **CRUD Table Page** pattern
   - List view with filtering, sorting, pagination
   - Row actions (edit, delete, view)
   - Bulk selection and actions

2. **Form Page** pattern
   - Create/Edit form with validation
   - Save, Cancel, Delete actions
   - Unsaved changes warning

3. **Detail View** pattern
   - Read-only display of entity
   - Related data sections
   - Action buttons

4. **Dashboard** pattern
   - Multiple data widgets
   - Filters affecting multiple sections
   - Drill-down navigation

5. **Wizard/Multi-Step Form** pattern
   - Sequential steps
   - Progress indicator
   - Back/Next navigation

---

**End of Command Specification**
