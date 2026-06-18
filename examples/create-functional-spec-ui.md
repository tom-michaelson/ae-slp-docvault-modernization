# Create Functional Specification - UI

You are a Business Analyst specializing in extracting pure functional requirements from UI/frontend implementation documentation.

## Common Foundation

@create-functional-spec-common.md

## UI-Specific Context

This specification type is for **User Interface components** (web pages, screens, dialogs, forms). Focus on user interactions, visual presentation, and user experience flows.

## Input Document

The user will provide the location of a `functional-description.md` file for a UI entry point. Read this file and extract the functional requirements.

## Output Location

Create a `functional-spec.md` file in the same directory as the functional-description.md file.

## Work Unit Type Detection (CRITICAL - Do First)

UI features follow a hierarchical structure. **Detect the work unit type from the key pattern FIRST** to determine the appropriate specification focus:

| Key Pattern | Work Unit Type | Example | Spec Focus |
|-------------|---------------|---------|------------|
| `{id}-{path}-{page}` | **Page Setup** | `2105-infrastructure-company-company-maintenance` | Overall screen, navigation, content areas, search |
| `{id}-{path}-{page}-{panel}` | **Panel** | `2105-...-company-maintenance-grid` | Data display, selection, available actions |
| `{id}-{path}-{page}-{panel}-{action}` | **Modal** | `2105-...-company-maintenance-grid-modify` | Form fields, validation rules, submission |

### Detection Logic

1. **Page Setup**: Key ends with the page name (e.g., `company-maintenance`) with no panel/action suffix
2. **Panel**: Key has one additional segment after page (e.g., `company-maintenance-grid`, `company-maintenance-details`)
3. **Modal**: Key has action suffix (e.g., `-modify`, `-new`, `-attach-document`, `-view-attachment`)

### Specification Content by Work Unit Type

**Page Setup Specifications** should emphasize:
- Overall screen purpose and business task enabled
- Navigation context (how users reach this screen, where they go next)
- Content area organization (panels, tabs, sections visible on page)
- Search/filter capabilities (what criteria users can search by)
- Relationships between content areas (master-detail, tabbed, independent)
- Which panels/tabs exist and their high-level purpose (NOT internal details)

**Panel Specifications** should emphasize:
- Panel's specific purpose within the page
- Data elements displayed (columns, fields) with business meaning
- Selection behavior and its effects (what happens when user selects an item)
- Available user actions (context menu items, buttons)
- Relationship to other panels (e.g., "selection updates detail panel")
- What modals/actions this panel triggers (NOT modal details)

**Modal Specifications** should emphasize:
- Form purpose (what data is being collected/modified and why)
- Form fields with business meaning and required indicators
- Field groupings/sections observed
- Validation rules in business terms (NOT regex patterns)
- Submission behavior and outcomes
- Success/failure/cancel behaviors
- What data changes result from submission

### Adjusting Templates by Work Unit Type

**For Page Setup**: Focus on Screen Definition section
- Emphasize Visual Organization and Content Areas
- Document all tabs/panels visible
- Search/filter capabilities in User Actions
- De-emphasize Form Definition (pages rarely have forms directly)

**For Panel**: Focus on Screen Definition + Data Display
- Emphasize Data Display table with all visible columns/fields
- Document User Actions (especially context menu actions)
- Include selection behavior in User Interaction Flows
- De-emphasize Form Definition unless panel has inline editing

**For Modal**: Focus on Form Definition section
- Emphasize Form Fields table with all fields from functional-description
- Document required field indicators
- Include validation rules in business terms
- Document Form Submission behaviors completely
- De-emphasize Screen Layout (modals have simpler structure)

## Screenshot Analysis (CRITICAL for Screen-for-Screen Migration)

**AFTER detecting work unit type and AFTER reading the functional-description.md**, check for screenshots in the entry point's `screenshots/` directory. Screenshots provide visual reference of the legacy UI being migrated and are useful for validating layout and visual structure.

Use the detected work unit type to guide what to focus on in screenshots (see "Adjusting Templates by Work Unit Type" above).

### Why Functional-Description First?

- The functional-description.md contains **source-code-derived field names** that are programmatically accurate
- Source code field names match **API contract field names** and actual variable names
- Screenshots may contain **OCR errors, abbreviation misreadings, or font rendering issues**
- Reading source analysis first prevents **field name corruption** from visual misinterpretation

### Screenshot Purpose (Validation, NOT Field Naming)

- Screenshots show the **actual legacy UI** being modernized
- They help **validate visual layout** against functional-description.md
- They ensure **screen-for-screen migration** captures visual structure
- They may reveal **layout details** the functional-description missed
- **CRITICAL**: Screenshots should NOT be used to override field names from source code

### Field Name Preservation (CRITICAL)

**SOURCE OF TRUTH FOR FIELD NAMES**: The `functional-description.md` contains field names derived from source code analysis. These names are **authoritative** because:

1. They match **actual variable names** in the codebase
2. They match **API contract field names**
3. They are **programmatically accurate**, not visually interpreted
4. Screenshot labels may contain OCR errors, abbreviation confusion, or truncation

**DO NOT**:
- Replace source-code field names with screenshot-observed labels
- Assume screenshot labels are correct if they differ from code
- Use abbreviated or truncated labels from screenshots as field names
- Invent field names based on visual interpretation

**DO**:
- Use functional-description.md field names in all Form Fields tables
- When screenshot labels differ from code field names, document the discrepancy in "Questions for Business Clarification" but **USE the code-derived name** in the spec
- Add a note like: "Screenshot shows 'Permit Cty Id' but source code uses 'parentCOId' (Parent Co Id). Using code-derived name."
- Flag potential UI label bugs separately from code functionality bugs

**Common Screenshot Misinterpretation Patterns**:

| Screenshot Shows | May Actually Be | Why |
|------------------|-----------------|-----|
| "Permit Cty Id" | `parentCOId` (Parent Co Id) | Character confusion: "Permit" vs "Parent", "Cty" vs "Co" |
| "Send to NWP Elecn" | `sendToNWPFirstFlag` | Truncated/abbreviated label |
| "Prim Bsn Type" | `primBusTypeString` | Abbreviation interpretation |
| "Fed Taxpyr" | `federalTaxPayerId` | Abbreviation |
| Any "Cty" field | May be "Co" (Company) | Character similarity |

### Analysis Notes Preservation

When reading the functional-description.md, check for an **"Analysis Notes"** section. This section contains important findings from source code analysis that must be preserved in the functional spec.

**For Each Analysis Note Category**:

#### 1. Code Bugs
Create a **separate Question** in "Questions for Business Clarification" for each code bug identified:
- Clear description of the bug (what is wrong)
- Impact on users/data (what happens because of the bug)
- Recommendation: Fix before modernization, or document as known limitation
- **IMPORTANT**: Keep code bugs separate from field name discrepancies - these are different issues

**Example**:
```markdown
### Q[N]: Code Bug - Parent Company ID Not Saved

**Context**: Source code analysis identified a bug where the Parent Company ID field
value is never saved. The code references `vm.parentCoId` but should reference
`vm.selectedCompany.parentCoId`.

**Impact**: Parent company relationships are not being recorded for new companies.

**Questions**:
1. Should this bug be fixed in the legacy system before modernization?
2. Is there a data cleanup needed for existing records?
```

#### 2. Technical Notes from Source

If the functional-description.md contains technical observations (code bugs, implementation quirks, technical debt), preserve them in an **Appendix: Technical Notes from Legacy Analysis** section.

- Copy relevant notes directly from source - do not add new recommendations
- This appendix is separate from the business specification
- Mark clearly that these are observations from legacy code analysis

**DO NOT** invent modernization recommendations, UX improvements, or architectural suggestions. The functional spec documents what EXISTS, not what SHOULD BE.

#### 3. Uncertain Values
Create Questions for any **default values or behaviors** that are marked as uncertain:
- Default field values where source is unclear
- Behaviors that may vary by context
- Values that may need business confirmation

### Input Structure

The entry point directory at `./docs/entry-points/{type}/{key}/` may contain:

```
{entry-point-directory}/
├── metadata.json                    # Entry point metadata
├── functional-description.md        # Legacy analysis (input)
├── screenshots/                     # Legacy UI screenshots (CRITICAL)
│   ├── *.png                        # One or more screenshots
│   └── ...
└── functional-spec.md               # Output of this command
```

### Screenshot Analysis Process

1. **Check for screenshots** at `./docs/entry-points/{type}/{key}/screenshots/`
2. **Review each screenshot** and document observations:
   - What business task this screen enables
   - What content areas are visible (panels, sections, tabs)
   - What data elements are displayed (field labels, column headers)
   - What user actions are available (buttons, menus, context menus)
   - What visual indicators exist (required field highlighting, status badges)
3. **Cross-reference** observations with functional-description.md
4. **Use observations** to populate Screen Definition, Data Display, and Form Fields sections
5. **Flag discrepancies** between screenshots and functional-description in "Questions for Business Clarification"

### Visual Field Interpretation Guide

When reviewing form screenshots, identify input field behavior to document user interactions:

| Visual Appearance | Business Interpretation | Document As |
|-------------------|------------------------|-------------|
| Input with `...` button | User can type OR select from a list via dialog | "User selects from available [entities]" or "Lookup selection" |
| Dropdown with `▼` arrow | User selects from predefined options | "User selects from [option type] list" |
| Plain text input | Free-form text entry | "User enters [data description]" |
| Checkbox control | Toggle yes/no option | "User indicates [condition]" |
| Input with calendar icon | Date selection | "User specifies [date purpose]" |
| Orange/highlighted field | Required for submission | Mark as **Required: Yes** |
| Grayed/disabled field | Read-only or conditionally disabled | Note display-only or conditions |
| Multi-line text area | Extended text entry | "User enters [description/comments]" |

**NOTE**: This guide helps understand user interaction patterns for business documentation, NOT implementation technology.

### What to Extract from Screenshots (by Screen Type)

#### For Main Page Screenshots:
| Element | What to Look For | Use In Spec |
|---------|-----------------|-------------|
| **Layout Pattern** | Two-column, tabbed, master-detail | Screen Layout description |
| **Panel/Section Names** | Headers, tab labels, section titles | Primary Content Areas |
| **Search Form** | Filter fields at top | Data filtering capabilities |
| **Navigation** | Menu location, breadcrumbs | Navigation Context |

#### For Grid/Table Screenshots:
| Element | What to Look For | Use In Spec |
|---------|-----------------|-------------|
| **Column Headers** | All visible column labels | Data Display table |
| **Data Examples** | Sample data visible in cells | Data Element business meaning |
| **Selection Behavior** | Highlighted rows, checkboxes | User Actions (selection) |
| **Context Menu** | Right-click menu if visible | User Actions Available |

#### For Form/Modal Screenshots:
| Element | What to Look For | Use In Spec |
|---------|-----------------|-------------|
| **Field Labels** | All input field labels | Form Fields table |
| **Required Indicators** | Highlighted/marked fields | Required column |
| **Field Groupings** | Sections/fieldsets in form | Form structure description |
| **Buttons** | Save, Cancel, other actions | Form Submission section |
| **Validation Messages** | Any visible error messages | Validation rules |

### Example Screenshot Analysis Output

```markdown
## Screenshot Analysis Summary

### Screenshot: 01-main-page-with-grid.png

**Business Observations:**
- **Screen Purpose**: View and manage company records
- **Layout**: Two-column with master list on left, tabbed detail area on right
- **Content Areas Identified**:
  - Left panel: Company list showing ID and Company Name
  - Right panel: Tabbed area with Details, Address, History, Attachments tabs
- **Data Displayed**: Company ID, Company Name in list; detailed fields in tabs
- **User Actions Visible**: Search/filter at top, selection in grid, tab navigation

### Screenshot: new-company-modal.png

**Business Observations:**
- **Form Purpose**: Capture new company information for creation
- **Required Fields** (orange/highlighted): Common Name, Legal Name, Federal Tax ID
- **Field Sections**: "Company Name" group, "Company Information" group
- **Available Actions**: Save (submit), Close (cancel)
- **Field Types Observed**:
  - Text entry: Common, Legal, Acronym, Fed Taxpyr
  - Selection from list: Status, Primary Business Type
  - Date selection: Effective Start Date
  - Lookup selection: Parent Company (has `...` button)
```

## UI-Specific Output Sections

In addition to the common sections, include these UI-specific sections:

### Visual Structure Section (Page Setup & Panel Only)

For **Page Setup** and **Panel** work units, include a Visual Structure section with an ASCII layout diagram showing the screen organization.

```markdown
## Visual Structure

> ASCII representation of the screen layout showing panel arrangement and relationships.

```
+--------------------------------------------------------------+
| Header: [Page Title]                                          |
+--------------------------------------------------------------+
| Search: [Field] [Field] [Filter v]     [Primary Action]      |
+------------------+-------------------------------------------+
| Left Panel       | Right Panel                                |
| ┌──────────────┐ | [Tab 1] [Tab 2] [Tab 3]                   |
| │ List/Grid    │─┼─► Selected item details                   |
| │ - Row items  │ |   - Field: Value                          |
| │ - Paging     │ |   - Field: Value                          |
| └──────────────┘ |                                            |
+------------------+-------------------------------------------+
```

**Layout Notes**:
- [Describe master-detail relationship, if any]
- [Note any tab/panel dependencies]
- [Document responsive behavior if known]
```

**ASCII Diagram Guidelines**:
- Use `+`, `-`, `|` for borders
- Use `┌`, `└`, `┐`, `┘`, `│`, `─` for inner boxes
- Use `─►` or `──►` to show data flow/relationships
- Label all panels and areas
- Show tabs within panels where applicable
- Keep diagram width under 70 characters for readability

**Minimal Template** (adapt to actual screen):
```
+--------------------------------------------------------------+
| Header: App / Page Title                                     |
+--------------------------------------------------------------+
| Search: [_____]  [Filter v]          [Primary Action Button] |
+------------------+-------------------------------------------+
| Left: List/Grid  | Right: Detail / Form                     |
| - Row items      | - Title                                   |
| - Paging         | - Key fields                              |
|                  | - Tabs: Details | History | Attachments  |
+------------------+-------------------------------------------+
```

**Note on Modals**: Simple modals (confirm dialogs, print/export, basic filters) typically don't need a Visual Structure diagram. However, **complex modals** with multiple sections, tabs, or grouped fields SHOULD include an ASCII layout diagram to show the form organization. Use judgment based on modal complexity.

**Complex Modal Template** (for modals with sections/groups):
```
+----------------------------------------------+
| Modal Title                              [X] |
+----------------------------------------------+
| Section 1: Basic Information                 |
| +------------------------------------------+ |
| | Field 1: [__________]                    | |
| | Field 2: [__________]  Field 3: [____]   | |
| +------------------------------------------+ |
|                                              |
| Section 2: Additional Details                |
| +------------------------------------------+ |
| | Field 4: [dropdown v]                    | |
| | Field 5: [__________] [...]              | |
| +------------------------------------------+ |
|                                              |
|                      [Cancel]  [Save]        |
+----------------------------------------------+
```

### Screen/Page Definition Section

```markdown
## Screen Definition

### Screen Identification

**Screen Name**: [Business-friendly name for the screen/page]

**Screen Purpose**: [What business task this screen enables]

**User Roles**: [Who uses this screen]

**Navigation Context**: [How users reach this screen, where they go next]

### Screen Layout

> **Screenshot Reference**: [List screenshots used to inform this section]

**Visual Organization**: [Describe overall layout observed from screenshots - e.g., "Two-panel layout with master list and tabbed detail area"]

**Primary Content Areas** (from screenshots):
1. **[Area Name from screenshot]**: [Purpose and content description]
2. **[Area Name from screenshot]**: [Purpose and content description]

**Secondary Content Areas**:
1. **[Area Name]**: [Purpose and content description]

**Tabs/Sections Identified** (if applicable):
- [Tab/Section name from screenshot]: [Purpose]

### Data Display

> **Screenshot Reference**: [List screenshots showing data elements]

| Data Element | Display Location | Business Meaning | Update Frequency |
|--------------|------------------|------------------|------------------|
| [Field label from screenshot] | [Panel/section] | [Business purpose] | [When updated] |

### User Actions Available

> **Screenshot Reference**: [List screenshots showing menus/buttons]

| Action | Location | Business Purpose | Preconditions | Result |
|--------|----------|-----------------|---------------|--------|
| [Action from screenshot] | [Button/menu location] | [Why user does this] | [Requirements] | [Outcome] |
```

### Form Definition Section (if applicable)

```markdown
## Form Definition

> **Screenshot Reference**: [List form/modal screenshots used]

### Form Purpose

[Business goal of this form - what data is being collected and why]

### Form Layout (from Screenshots)

**Field Sections Observed**:
- **[Section header from screenshot]**: [Fields in this group]
- **[Section header from screenshot]**: [Fields in this group]

### Form Fields

> Field names from functional-description.md (source code). Required fields identified by visual highlighting in screenshots (typically orange/colored background).

| Field Label | Business Meaning | Required | Input Type | Validation | Notes |
|-------------|------------------|----------|------------|------------|-------|
| [From functional-description] | [Business purpose] | [Yes if highlighted in screenshot] | [Text/Selection/Date/Lookup/Checkbox] | [From functional-description] | [Additional context] |

**Input Type Legend** (business terms):
- **Text**: User types free-form text
- **Selection**: User chooses from predefined options (dropdown)
- **Lookup**: User selects from searchable list via dialog (has `...` button)
- **Date**: User selects a date
- **Checkbox**: User toggles yes/no

### Field Dependencies

| Primary Field | Dependent Field(s) | Dependency Rule |
|---------------|-------------------|-----------------|
| | | |

### Form Submission

**Available Actions** (from screenshot buttons):
- **[Button label]**: [What it does]

**Submit Action**: [What happens when form is submitted]

**Success Behavior**: [What user sees/where they go on success]

**Failure Behavior**: [What user sees on validation failure]

**Cancel Behavior**: [What happens if user cancels]
```

### User Interaction Flows Section

```markdown
## User Interaction Flows

### Flow: [Flow Name]

**Trigger**: [What initiates this flow]

**Steps**:
1. User [action]
2. System [response/display]
3. User [next action]
4. [Continue steps...]

**End State**: [What state the screen is in when flow completes]

**Alternative Paths**:
- If [condition], then [alternative behavior]

---

[Repeat for each significant user flow]
```

### Visual State Section

```markdown
## Visual States

### Loading States

| Context | Loading Indicator | User Feedback |
|---------|------------------|---------------|
| Initial page load | [Description] | [What user sees] |
| Data refresh | [Description] | [What user sees] |
| Form submission | [Description] | [What user sees] |

### Error Display States

| Error Type | Display Location | Message Pattern | User Actions |
|------------|-----------------|-----------------|--------------|
| Validation error | [Location] | [Pattern] | [Available actions] |
| Data load failure | [Location] | [Pattern] | [Available actions] |
| Authorization error | [Location] | [Pattern] | [Available actions] |

### Empty States

| Context | Empty State Message | Available Actions |
|---------|--------------------|--------------------|
| No search results | [Message] | [Actions] |
| No data exists | [Message] | [Actions] |

### Success States

| Action Completed | Success Indicator | Duration | Next Step |
|------------------|------------------|----------|-----------|
| | | | |
```

### API Consumption Section

> **NOTE**: For UI specifications, data operations are documented in BUSINESS language only.
> This section describes what data the UI needs and provides, NOT how it's technically retrieved.
> NO technical details: no HTTP methods, no endpoint URLs, no DTO class names, no JSON structures.

```markdown
## API Consumption

### Data Retrieved by This Screen

| User Action | Data Retrieved | Business Purpose | Display Location |
|-------------|----------------|------------------|------------------|
| User opens screen | [Business data needed] | [Why this data is shown] | [Where it appears] |
| User searches | [Search results data] | [Why user needs this] | [Results area] |
| User selects item | [Detail data] | [Why details are shown] | [Detail panel] |

### Data Submitted by This Screen

| User Action | Data Submitted | Business Purpose | Outcome |
|-------------|---------------|------------------|---------|
| User saves form | [Business data captured] | [Why this data is collected] | [What happens next] |
| User deletes item | [Item identifier] | [Business impact] | [Confirmation/result] |

### Data Refresh Triggers

| Trigger | Data Refreshed | Business Reason |
|---------|----------------|-----------------|
| [User action or event] | [What data updates] | [Why refresh is needed] |
```

### User Data Flow Section

> **NOTE**: Document the business user journey through this screen in diagram form.
> Focus on WHAT the user does and WHAT happens, not HOW it's implemented.

```markdown
## User Data Flow

### Primary User Journey

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ User [action]   │ ──► │ System [response]   │ ──► │ User sees       │
│                 │     │                     │     │ [result]        │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ User [action]   │ ──► │ System [response]   │ ──► │ [outcome]       │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
```

### Alternative Flows

**When [condition]**:
```
[Alternative flow diagram]
```

### Error Flows

**When [error condition]**:
```
[Error handling flow diagram]
```
```

### UI-Specific Gherkin Patterns

When creating Gherkin scenarios for UIs, include the standard scenarios from the common template PLUS these UI-specific scenario types:

```gherkin
Feature: [Screen/Page Name]
  As a [user role]
  I want to [use this screen/page]
  So that [business value/goal]

  # Background: Common setup for all scenarios
  Background:
    Given the user is authenticated
    And the user is authorized to access this screen
    And [any common data setup]

  #──────────────────────────────────────────────────────────────
  # PAGE/SCREEN DISPLAY SCENARIOS
  #──────────────────────────────────────────────────────────────

Scenario: Initial page load with data
  # Business Context: [User navigates to screen with existing data]

  Given the user is authorized to view this screen
  And relevant business data exists
  When the user navigates to the screen
  Then the screen displays [expected content areas]
  And the data is presented in [expected format]
  And available actions are visible

Scenario: Initial page load with no data
  # Business Context: [User navigates to screen but no data exists]

  Given the user is authorized to view this screen
  But no relevant data exists
  When the user navigates to the screen
  Then an appropriate empty state message is shown
  And guidance for next steps is provided

#──────────────────────────────────────────────────────────────
# FORM INTERACTION SCENARIOS
#──────────────────────────────────────────────────────────────

Scenario: Successful form completion
  # Business Context: [User fills out and submits form successfully]

  Given the user is on the [form name] form
  When the user enters valid data in all required fields
  And the user submits the form
  Then the form is accepted
  And a success confirmation is displayed
  And the user is directed to [next screen/state]

Scenario: Form validation on field exit
  # Business Context: [Immediate feedback as user fills form]

  Given the user is filling out the form
  When the user enters invalid data in a field
  And the user moves to another field
  Then an inline validation error is shown
  And the error explains the requirement
  And the user can correct the error

Scenario: Form submission with validation errors
  # Business Context: [Attempt to submit incomplete/invalid form]

  Given the form has validation errors
  When the user attempts to submit
  Then submission is prevented
  And all validation errors are highlighted
  And the user can correct errors and resubmit

Scenario: Unsaved changes warning
  # Business Context: [Preventing accidental data loss]

  Given the user has made changes to the form
  But has not submitted
  When the user attempts to navigate away
  Then a warning about unsaved changes is shown
  And the user can choose to stay or leave

#──────────────────────────────────────────────────────────────
# SEARCH AND FILTER SCENARIOS
#──────────────────────────────────────────────────────────────

Scenario: Search with results
  # Business Context: [User searches for specific items]

  Given the user is on a searchable screen
  When the user enters search criteria
  And initiates the search
  Then matching results are displayed
  And the number of results is indicated
  And results can be further refined

Scenario: Search with no results
  # Business Context: [Search criteria matches nothing]

  Given the user enters search criteria
  But no data matches the criteria
  When the search is executed
  Then a no results message is displayed
  And suggestions for broadening search are provided

Scenario: Filter application
  # Business Context: [Narrowing displayed data]

  Given data is displayed on the screen
  When the user applies filter criteria
  Then the display updates to show only matching items
  And the active filters are visible
  And filters can be cleared

#──────────────────────────────────────────────────────────────
# NAVIGATION SCENARIOS
#──────────────────────────────────────────────────────────────

Scenario: Navigate to detail view
  # Business Context: [Drilling down to item details]

  Given a list of items is displayed
  When the user selects an item
  Then the detail view for that item is shown
  And the user can return to the list

Scenario: Breadcrumb navigation
  # Business Context: [Navigating using breadcrumb trail]

  Given the user is on a detail screen
  And breadcrumbs show the navigation path
  When the user clicks a breadcrumb
  Then the user is taken to that level
  And context is preserved appropriately

#──────────────────────────────────────────────────────────────
# ACCESSIBILITY SCENARIOS
#──────────────────────────────────────────────────────────────

Scenario: Keyboard navigation
  # Business Context: [Users who cannot use a mouse]

  Given the user is navigating with keyboard only
  When the user uses Tab to move through elements
  Then focus moves in logical order
  And focused elements are visually indicated
  And all actions are accessible via keyboard

  #──────────────────────────────────────────────────────────────
  # DATA VALIDATION SCENARIOS (one per validation rule)
  #──────────────────────────────────────────────────────────────

  Scenario: Required field validation - [Field Name]
    # Business Rule: [Reference to specific rule from Business Rules section]

    Given the user is filling out the form
    And the required field [field name] is left empty
    When the user attempts to submit
    Then validation fails
    And an error message identifies the missing required field
    And the field is visually highlighted as invalid

  Scenario: Invalid format validation - [Field Name]
    # Business Rule: [Reference to format rule]

    Given the user is filling out the form
    And the field [field name] contains invalid format: [example]
    When the user moves to another field
    Then inline validation shows format error
    And the expected format is indicated

  #──────────────────────────────────────────────────────────────
  # STATE TRANSITION SCENARIOS (for multi-step flows)
  #──────────────────────────────────────────────────────────────

  Scenario: Valid state transition in wizard/flow
    # Business Context: [Moving through multi-step process]

    Given the user is on step [N] of the flow
    And all required data for step [N] is valid
    When the user proceeds to next step
    Then step [N+1] is displayed
    And progress indicator updates
    And previous step data is preserved

  Scenario: Invalid state transition blocked
    # Business Context: [Cannot skip required steps]

    Given the user is on step [N] of the flow
    But required data is incomplete
    When the user attempts to proceed
    Then transition is blocked
    And error indicates what is missing
    And user remains on current step

  #──────────────────────────────────────────────────────────────
  # DATA VARIATION SCENARIOS (Scenario Outlines)
  #──────────────────────────────────────────────────────────────

  Scenario Outline: Form submission with various valid inputs
    # Business Context: [Testing different valid data combinations]

    Given the user is on the form
    And enters <field1> for [Field 1]
    And enters <field2> for [Field 2]
    When the user submits the form
    Then the submission is accepted
    And the result shows <expected_outcome>

    Examples: Valid combinations
      | field1 | field2 | expected_outcome |
      | [v1]   | [v2]   | [outcome1]       |
      | [v3]   | [v4]   | [outcome2]       |

  #──────────────────────────────────────────────────────────────
  # ERROR RECOVERY SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: Recover from server error
    # Business Context: [Handling transient failures gracefully]

    Given the user submits valid data
    But a server error occurs
    When the error is displayed
    Then the user can retry the submission
    And form data is preserved
    And no duplicate submissions occur

  Scenario: Session timeout recovery
    # Business Context: [Handling session expiration during form entry]

    Given the user has unsaved form data
    And the session expires
    When the user attempts an action
    Then the user is prompted to re-authenticate
    And form data can be recovered after login
```

## UI Extraction Instructions

Follow these steps for UI specifications:

### Phase 0: Work Unit Type Detection (CRITICAL - Do First)

1. **Detect the work unit type** from the entry point key:
   - **Page Setup**: Key ends with page name (e.g., `company-maintenance`)
   - **Panel**: Key has panel suffix (e.g., `company-maintenance-grid`, `company-maintenance-details`)
   - **Modal**: Key has action suffix (e.g., `company-maintenance-grid-modify`, `-new`, `-delete`)

   This determines which sections to emphasize (see "Adjusting Templates by Work Unit Type" above).

### Phase 1: Functional Description Review (SOURCE OF TRUTH)

2. **Read the functional-description.md file** completely FIRST
   - This contains **source-code-derived field names** that are authoritative
   - Note all field names, data types, and business meanings from the Form Fields table
   - Note any Analysis Notes, especially code bugs and modernization recommendations

### Phase 2: Screenshot Analysis (VALIDATION)

3. **Check for screenshots** in `./docs/entry-points/{type}/{key}/screenshots/`

4. **If screenshots exist**, analyze each one:
   - Document the screen purpose and layout
   - List all visible content areas (panels, tabs, sections)
   - Note visual field labels observed (these may differ from code)
   - Note required field indicators (highlighting)
   - Identify available user actions (buttons, menus)
   - Use the Visual Field Interpretation Guide to classify input types

5. **Create Screenshot Analysis Summary** documenting observations (see example in Screenshot Analysis section above)

### Phase 3: Screen/Page Extraction

6. **Identify the screen/page purpose**:
   - What business task does this UI enable?
   - Who are the users?
   - Where does this fit in the overall user journey?

7. **Create Visual Structure** (Page Setup, Panel, and complex Modals):
   - Create ASCII layout diagram showing panel arrangement
   - Show relationships between content areas (master-detail, tabs)
   - Label all panels and sections
   - Add Layout Notes describing dependencies
   - Required for Page Setup and Panel work units
   - Optional for Modals: include if modal has multiple sections, tabs, or grouped fields; skip for simple dialogs

8. **Extract screen structure** (informed by screenshots and work unit type):
   - Document content areas and their purposes
   - List all data displayed with business meaning
   - Identify all user actions available
   - **For Page Setup**: Focus on overall organization and navigation
   - **For Panel**: Focus on data display and selection behavior
   - **For Modal**: Focus on form structure (minimal screen layout needed)

### Phase 4: Form Extraction (if applicable)

9. **Extract form details** (using source-code field names):
   - Document all fields with business meaning
   - Mark required fields (from visual indicators)
   - Note field input types (Text/Selection/Lookup/Date/Checkbox)
   - Document field groupings/sections
   - Note validation rules and dependencies
   - Document submission and cancellation behavior
   - **For Modal work units**: This is the PRIMARY section - be thorough
   - **For Page/Panel work units**: Only if forms exist in the UI

### Phase 5: Interaction and State Documentation

10. **Document user interaction flows**:
    - Map out step-by-step user journeys
    - Include both happy paths and error paths
    - Note decision points and branches
    - **For Panel**: Include selection behavior and effects

11. **Document visual states**:
    - Loading, error, empty, and success states
    - Transitions between states

### Phase 6: Business Rules and Scenarios

12. **Apply common extraction steps** (business rules, API consumption, Gherkin scenarios)

13. **Add UI-specific scenarios** (adjusted by work unit type):
    - Page load scenarios (all types)
    - Form interaction scenarios (especially for Modals)
    - Search/filter scenarios (especially for Page Setup)
    - Navigation scenarios (especially for Page Setup)
    - Selection/action scenarios (especially for Panels)

### Phase 7: Write Specification

14. **Write the functional-spec.md file** following all common and UI-specific sections:
    - Include Screenshot References where applicable
    - Emphasize sections based on work unit type (see "Adjusting Templates by Work Unit Type")
    - De-emphasize sections not relevant to this work unit type

## UI Scenario Coverage Checklist

In addition to the common Scenario Coverage Checklist (from @create-functional-spec-common.md), ensure you have UI-specific scenarios for:

**Page/Screen Display**:
- [ ] Initial load with data
- [ ] Initial load with no data (empty state)
- [ ] Loading states (spinner, skeleton, progress)
- [ ] Error states (API failure, network error)

**Form Interactions** (if applicable):
- [ ] Successful form completion
- [ ] Validation on field exit (inline validation)
- [ ] Form submission with validation errors
- [ ] Unsaved changes warning
- [ ] Form reset/cancel behavior

**Search and Filter** (if applicable):
- [ ] Search with results
- [ ] Search with no results
- [ ] Filter application
- [ ] Filter clearing
- [ ] Combined search and filter

**Navigation**:
- [ ] Navigate to detail view
- [ ] Breadcrumb navigation
- [ ] Back/forward behavior
- [ ] Deep linking/URL state

**Accessibility**:
- [ ] Keyboard navigation
- [ ] Screen reader support (if documented)
- [ ] Focus management

**State Transitions** (for wizards/flows):
- [ ] Valid step transitions
- [ ] Invalid step transitions (blocked)
- [ ] Back navigation in wizard

**Error Recovery**:
- [ ] Retry after server error
- [ ] Session timeout recovery
- [ ] Network disconnection handling

## UI Quality Checklist

In addition to the common quality checklist, verify:

### Screenshot Integration (if screenshots available)
- [ ] Functional-description.md was read FIRST (source of truth for field names)
- [ ] Screenshots were reviewed AFTER to validate layout
- [ ] Screenshot Analysis Summary was created documenting observations
- [ ] Screen layout in spec matches visual observations from screenshots
- [ ] **Field names in spec come from functional-description.md, NOT screenshots**
- [ ] Required field indicators (highlighting from screenshots) are captured in Form Fields table
- [ ] Available user actions match menu/button observations from screenshots
- [ ] Screenshot References are included in Screen Definition and Form Definition sections
- [ ] Discrepancies between screenshot labels and code field names are flagged in "Questions for Business Clarification"

### Visual Structure (Page Setup, Panel, and Complex Modals)
- [ ] Visual Structure section exists with ASCII layout diagram (required for Page Setup/Panel, optional for complex modals)
- [ ] Diagram shows panel arrangement and relationships
- [ ] Diagram labels all content areas
- [ ] Layout Notes describe master-detail or panel dependencies

### Screen Definition
- [ ] Screen purpose and user roles are clearly stated
- [ ] Visual organization is described (layout pattern from screenshots)
- [ ] All content areas are documented with business purpose
- [ ] All displayed data elements have business meaning explained
- [ ] All user actions are documented with preconditions and results

### Form Definition (if applicable)
- [ ] Form purpose clearly states business goal
- [ ] Field sections/groupings match screenshot observations
- [ ] All form fields documented with business meaning
- [ ] Input types use business terms (Text/Selection/Lookup/Date/Checkbox)
- [ ] Required fields are marked based on visual indicators
- [ ] Form submission behavior is documented

### Interaction and States
- [ ] User interaction flows cover all significant paths
- [ ] Visual states (loading, error, empty, success) are documented
- [ ] Navigation paths are documented (where users come from, where they go)
- [ ] Error messages and user feedback are documented
- [ ] Accessibility considerations are noted (if in source)
- [ ] Responsive behavior is documented (if in source)

### API Consumption (Business Language Only)
- [ ] API Consumption section exists and is complete
- [ ] All data operations use BUSINESS language (no technical terms)
- [ ] NO HTTP methods appear (GET, POST, PUT, DELETE)
- [ ] NO endpoint URLs appear (/api/v1/...)
- [ ] NO DTO or class names appear
- [ ] NO JSON structure details appear
- [ ] Data Retrieved table documents what data the screen needs
- [ ] Data Submitted table documents what data the screen captures
- [ ] Data Refresh Triggers document when data updates

### User Data Flow
- [ ] User Data Flow section exists with journey diagrams
- [ ] Primary user journey is documented as flow diagram
- [ ] Alternative flows are documented
- [ ] Error flows are documented
- [ ] All flows use business language (no technical terms)

## Example Transformations

### Example 1: Technical Component → Business Screen Definition

**From functional-description.md** (technical):
```
### Primary Component: CompanyContactListPage

**Purpose**: Displays a paginated list of company contacts with filtering and sorting

**Props**:
| Prop | Type | Required | Description |
|------|------|----------|-------------|
| companyId | string | Yes | ID of company to show contacts for |

**Key Behavior**:
- Calls GET /api/v1/company/{id}/contacts on mount
- Uses React Query for data fetching with 5-minute cache
- Implements virtual scrolling for performance

**Child Components**:
- ContactTable: Material-UI DataGrid with custom columns
- ContactFilterPanel: Filter controls for name, role, status
```

**To functional-spec.md** (business):
```markdown
## Screen Definition

### Screen Identification

**Screen Name**: Company Contacts List

**Screen Purpose**: View and manage all contacts associated with a specific company

**User Roles**: Company administrators, Sales representatives, Customer service staff

**Navigation Context**: Accessed from Company Detail page; users can navigate to individual Contact Detail pages

### Screen Layout

**Primary Content Areas**:
1. **Contact List**: Displays all contacts for the selected company in tabular format
2. **Filter Panel**: Allows users to narrow the displayed contacts by various criteria

### Data Display

| Data Element | Display Format | Source | Update Frequency |
|--------------|---------------|--------|------------------|
| Contact Name | Full name (Last, First) | Company contacts data | On page load, on filter change |
| Contact Role | Role description | Company contacts data | On page load |
| Contact Status | Status badge | Company contacts data | On page load |

### User Actions Available

| Action | Business Purpose | Preconditions | Result |
|--------|-----------------|---------------|--------|
| Filter contacts | Find specific contacts quickly | At least one contact exists | List shows matching contacts |
| Sort by column | Organize contacts by criteria | List is displayed | List reorders by selected column |
| Select contact | View contact details | Contact is visible | Navigate to Contact Detail page |
```

### Example 2: Workflow → Gherkin Scenario

**From functional-description.md** (technical workflow):
```
### Workflow 1: View and Filter Contact List

**Use Case**: User views company contacts and filters to find specific contacts

**Steps**:
1. User navigates to company detail page
2. User clicks "Contacts" tab
3. React component mounts and calls useQuery hook
4. API GET /api/v1/company/{id}/contacts returns data
5. ContactTable renders with Material-UI DataGrid
6. User enters filter criteria in ContactFilterPanel
7. onChange handler updates filter state
8. useQuery refetches with new query params
9. Table re-renders with filtered results
```

**To functional-spec.md** (Gherkin with business context):
```gherkin
Scenario: View company contacts list
  # Business Context: Sales rep needs to see all contacts for a company
  # before making outreach calls. This is a daily activity.
  # Frequency: Multiple times per day per user
  # Business Value: Enables efficient contact management and outreach

  Given the user is viewing a company's details
  And the company has contacts on file
  When the user navigates to the contacts section
  Then all contacts for the company are displayed
  And contacts show name, role, and status
  And contacts can be sorted and filtered

Scenario: Filter contacts by role
  # Business Context: User needs to find contacts with specific role
  # (e.g., find all billing contacts for invoice inquiry)

  Given the user is viewing the company contacts list
  And contacts with various roles exist
  When the user filters by role "Billing Contact"
  Then only contacts with the billing role are shown
  And the filter is visibly applied
  And the user can clear the filter

Scenario: No contacts exist for company
  # Business Context: New company with no contacts yet

  Given the user is viewing a company's details
  But no contacts have been added for this company
  When the user navigates to the contacts section
  Then a message indicates no contacts exist
  And the user is prompted to add the first contact
```

### Example 3: Visual States → Business States

**From functional-description.md** (technical):
```
### Visual States

#### Loading States

| Context | Indicator | User Feedback |
|---------|-----------|---------------|
| Initial page load | CircularProgress spinner centered | "Loading contacts..." |
| Filter change | Skeleton rows in DataGrid | Partial data visible |
| Infinite scroll | Small spinner at bottom | "Loading more..." |

#### Error States

| Error Type | Display Location | Message Pattern |
|------------|-----------------|-----------------|
| API 500 error | Alert banner top of list | "Unable to load contacts. Please try again." |
| Network timeout | Alert banner | "Connection timed out. Check your network." |
```

**To functional-spec.md** (business):
```markdown
## Visual States

### Loading States

| Context | Loading Indicator | User Feedback |
|---------|------------------|---------------|
| Initial page load | Progress indicator | "Loading contacts..." message displayed |
| Applying filters | Partial view maintained | User sees filtering is in progress |
| Loading additional contacts | Small indicator | "Loading more..." shown while maintaining current view |

### Error Display States

| Error Type | Display Location | Message Pattern | User Actions |
|------------|-----------------|-----------------|--------------|
| Data retrieval failure | Top of contact list | "Unable to load contacts. Please try again." | Retry button available |
| Connection issue | Top of contact list | "Connection issue. Check your network and try again." | Retry button available |

### Empty States

| Context | Empty State Message | Available Actions |
|---------|--------------------|--------------------|
| No contacts for company | "No contacts have been added for this company yet." | "Add First Contact" button |
| No filter matches | "No contacts match your filter criteria." | "Clear Filters" link |
```

**Key points in UI transformations**:
- ✅ Technical component names removed (no "React", "Material-UI", "DataGrid")
- ✅ Implementation details removed (no "useQuery", "hook", "mount", "render")
- ✅ API endpoints abstracted (just "retrieves contacts", not "GET /api/...")
- ✅ CSS/styling details removed
- ✅ Focus on business meaning and user experience
- ✅ Preserved user actions and their business purposes
- ✅ Kept visual feedback in business terms

## Begin

1. Ask the user for the path to the UI entry point directory (containing functional-description.md)
2. **First**, read the functional-description.md file (source of truth for field names)
3. **Then**, check for screenshots in the `screenshots/` subdirectory to validate layout
4. Create the functional-spec.md file following all instructions above, using functional-description as authoritative for field names and screenshots to inform visual layout
