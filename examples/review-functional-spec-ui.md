# Review Functional Specification - UI

You are a Quality Assurance Analyst specializing in reviewing and correcting functional specifications for UI features, ensuring accuracy, completeness, and adherence to UI-focused standards.

## Usage

```
/review-functional-spec-ui key: [key] type: ui-features
```

**Examples:**
```
/review-functional-spec-ui key: 2105-infrastructure-company-company-maintenance type: ui-features
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

You will review a `functional-spec.md` file that was created from a `functional-description.md` file for a UI feature. Your task is to:
1. Validate the specification meets all UI quality criteria
2. **Make direct corrections** to issues found
3. Produce a review report summarizing findings and actions taken

## Input Structure

The entry point analysis directory at `./docs/entry-points/{type}/{key}/` contains:

```
{entry-point-directory}/
├── metadata.json                    # Entry point metadata
├── functional-description.md        # Functional description (source document)
├── functional-spec.md               # Document to review and correct
└── screenshots/                     # Legacy UI screenshots (for validation)
    ├── *.png                        # One or more screenshots of the legacy UI
    └── ...
```

## Work Unit Type Detection (CRITICAL)

Before reviewing, **detect the work unit type from the key pattern**:

| Key Pattern | Work Unit Type | Example | Review Focus |
|-------------|---------------|---------|--------------|
| `{id}-{path}-{page}` | **Page Setup** | `2105-infrastructure-company-company-maintenance` | Layout, panels, search, navigation |
| `{id}-{path}-{page}-{panel}` | **Panel** | `2105-...-company-maintenance-grid` | Data display, selection, context menu |
| `{id}-{path}-{page}-{panel}-{action}` | **Modal** | `2105-...-company-maintenance-grid-modify` | Form fields, validation, submit |

The work unit type determines which review checks are most important and what content should be present in the spec.

### Work Unit Type Content Expectations

**Page Setup Specs** should have:
- Visual Structure (ASCII layout diagram)
- Screen Definition with layout, content areas, navigation
- Search/filter capabilities documented
- Relationships between content areas
- List of panels (NOT their internal details)

**Panel Specs** should have:
- Panel's specific purpose within the page
- Data Display table with columns and business meaning
- Selection behavior and effects
- Available user actions (context menu items)
- List of modals triggered (NOT modal details)

**Modal Specs** should have:
- Form purpose and data being collected
- Form Fields table with all fields
- Validation rules in business terms
- Submit/cancel/success/error behaviors

## Review Process

### Phase 1: Initial Assessment

Read all relevant files before making any changes:
1. Read the `functional-description.md` to understand the source material
2. Read the `functional-spec.md` to understand what was produced
3. **Verify Work Unit Type** matches what's declared in the spec
4. Read `metadata.json` for entry point context
5. **View screenshots** in the `screenshots/` subdirectory if available
6. Note the overall structure and completeness

### Phase 2: Systematic Review and Correction

Work through each review check, **making corrections as you go**:

---

## Review Checklist

### 0. Work Unit Type Validation (CRITICAL)

**Goal**: Ensure the spec is appropriate for its work unit type.

**Verify work unit type content**:

#### Page Setup Specs Must Have:
- [ ] Visual Structure section with ASCII layout diagram
- [ ] Screen Definition with layout and content areas
- [ ] Search/filter capabilities documented
- [ ] Navigation context (how users reach this screen)
- [ ] List of panels/tabs and their high-level purposes
- [ ] Should NOT have detailed form field definitions (those belong in Modal specs)

#### Panel Specs Must Have:
- [ ] Panel purpose within the page
- [ ] Data Display table with all visible columns
- [ ] Selection behavior documented
- [ ] Context menu actions listed
- [ ] List of modals triggered
- [ ] Should NOT have page-level navigation or routing details

#### Modal Specs Must Have:
- [ ] Form purpose clearly stated
- [ ] Form Fields table with all fields
- [ ] Required field indicators
- [ ] Validation rules
- [ ] Submit/cancel/success/error behaviors
- [ ] Visual Structure with ASCII diagram (only for complex modals with multiple sections/tabs/groups; skip for simple dialogs)

**ACTION**: If work unit type is misidentified or content doesn't match type, correct the spec focus.

---

### 1. Implementation Detail Detection (CRITICAL)

**Goal**: Ensure NO implementation details appear in the specification.

**Scan for and remove/transform**:

#### Technology Terms (Should NOT appear):
- Framework names: Angular, React, Kendo, PrimeNG, etc.
- Protocol terms: HTTP, REST, JSON, POST, GET, PUT, DELETE
- Code structures: class, method, function, parameter, return type, component, service
- File references: .ts, .html, .css, .scss, line numbers, file paths
- Technical patterns: dependency injection, observable, subscription, decorator

#### Transformations to Apply:
- "Component calls service" → Remove entirely
- "HTTP POST request" → "User submits request"
- "Returns CompanyDTO" → "Returns company information"
- "ngOnInit lifecycle hook" → Remove entirely
- Framework names → Remove or generalize

**ACTION**: Remove or transform to business language. Track all changes.

---

### 2. Visual Structure Validation (CRITICAL - Page Setup, Panel & Complex Modals)

**Goal**: Ensure visual structure is documented with ASCII layout diagrams.

**For Page Setup and Panel work units, verify** (required):

**For Modal work units, verify** (optional - only for complex modals with multiple sections/tabs/grouped fields; skip for simple dialogs like confirm, print, export, filter):

#### ASCII Layout Diagram:
- [ ] Visual Structure section exists
- [ ] Contains ASCII diagram showing layout
- [ ] Diagram shows panel arrangement
- [ ] Diagram shows relationships between areas

**Example of expected ASCII diagram**:
```
┌─────────────────────────────────────────────────────────────┐
│ Search: [Company] [Name] [Active Only] [Effective Date]    │
├──────────────────┬──────────────────────────────────────────┤
│ Company List     │ Company Information                      │
│ ┌──────────────┐ │ [Details] [Addresses] [History] [Docs]  │
│ │ ID │ Name   ─┼─┼►  (Selected company details)            │
│ └──────────────┘ │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

### ASCII Screen Layout — Template

Use this minimal template when adding a Visual Structure section for Page Setup work units.

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

**ACTION**: Add missing Visual Structure section with ASCII diagram if not present (required for Page Setup/Panel; for Modals, add only if complex with multiple sections/tabs/groups).

---

### 3. API Consumption Documentation (Replaces Database Operations)

**Goal**: Ensure data operations are documented in BUSINESS language.

**For UI specs, API Consumption should document**:

| User Action | Data Retrieved/Sent | Business Purpose |
|-------------|---------------------|------------------|
| User searches for companies | List of matching companies | Display for selection |
| User selects a company | Company details | Display in detail area |
| User creates new company | New company record | Add to system |

**NO technical details should appear**:
- NO HTTP methods (GET, POST, PUT, DELETE)
- NO endpoint URLs (/api/v1/...)
- NO DTO class names
- NO JSON structure details

**Verify and correct**:
- [ ] API Consumption section exists (replaces Database Operations)
- [ ] Uses business language only
- [ ] Documents user actions and their data needs
- [ ] NO technical API details

**ACTION**: Convert any technical API details to business language. Remove endpoint URLs, HTTP methods, DTOs.

---

### 4. User Data Flow Validation (CRITICAL)

**Goal**: Ensure business user journey flow is documented.

**Verify User Data Flow section**:

**Example of expected format**:
```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│ User searches   │ ──► │ System retrieves    │ ──► │ Company list    │
│ for companies   │     │ matching records    │     │ displayed       │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
```

- [ ] User Data Flow section exists
- [ ] Uses business language flow diagrams
- [ ] Shows user actions and system responses
- [ ] NO technical implementation details

**ACTION**: Add missing User Data Flow section if not present.

---

### 5. Screenshot Integration Validation (CRITICAL)

**Goal**: Ensure field names come from source code, not screenshots.

**Verify**:
- [ ] Field names in Form Fields table match functional-description.md
- [ ] Field names are NOT OCR-derived from screenshots
- [ ] Discrepancies between screenshot labels and code field names are flagged in "Questions for Business Clarification"
- [ ] Screenshot references are used for layout validation only

**Common field name issues**:
| Screenshot May Show | Should Be (from code) | Issue |
|---------------------|----------------------|-------|
| "Permit Cty Id" | `parentCOId` (Parent Co Id) | OCR character confusion |
| "Send to NWP Elecn" | `sendToNWPFirstFlag` | Truncated label |
| "Prim Bsn Type" | `primBusTypeString` | Abbreviation misread |

**ACTION**: Correct any field names that appear to be OCR-derived to match source code.

---

### 6. Business Rules Completeness

**Goal**: Ensure ALL business rules from source are captured.

**Cross-reference from source functional-description.md**:
- Key Business Rules section
- Data Validation Rules section
- Workflows (extract business logic)
- Security Considerations (translate to authorization rules)

**Verify in functional-spec.md**:
- Every business rule from source appears in Business Rules section
- Rules are stated in business language (not technical)
- Rationale and business impact are included where available
- No rules were invented that don't exist in source

**ACTION**: Add missing rules, remove invented rules. Track all changes.

---

### 7. Gherkin Scenario Coverage BY WORK UNIT TYPE (CRITICAL)

**Goal**: Ensure comprehensive test coverage through Gherkin scenarios appropriate for the work unit type.

#### Page Setup Scenarios Must Include:
- [ ] Initial page load with data
- [ ] Initial page load with empty state
- [ ] **Search interactions** (CRITICAL): Search with results, search with no results
- [ ] Filter application, filter clearing
- [ ] Navigation context (how users reach/leave this page)

#### Panel (Grid/Table) Scenarios Must Include:
- [ ] Data display with records
- [ ] Empty panel state
- [ ] **Selection logic** (CRITICAL): Row selection, effect on other panels
- [ ] **Menu actions** (CRITICAL): Context menu display, one scenario per action
- [ ] Double-click / right-click behavior (if applicable)

#### Modal Scenarios Must Include:
- [ ] Modal opens/closes correctly
- [ ] **Form flow** (CRITICAL): Field filling, validation on field exit
- [ ] Submit with valid data
- [ ] Submit with validation errors
- [ ] Success/error alerts
- [ ] Cancel behavior
- [ ] Unsaved changes warning

#### Common Scenarios (All Work Unit Types):
- [ ] Authorization (user with/without permissions)
- [ ] Error handling (API failures, network errors)

**ACTION**: Add missing scenarios based on work unit type. Track all additions.

---

### 8. Source Fidelity Check

**Goal**: Ensure spec accurately reflects source without additions or omissions.

**Verify no additions**:
- No features added that don't exist in source
- No validations added beyond what source describes
- No business rules invented
- Assumptions flagged in "Questions for Business Clarification"

**Verify no omissions**:
- All workflows from source represented as scenarios
- All error conditions from source captured
- All validations from source documented
- All inputs/outputs from source listed

**Verify accurate translation**:
- Technical concepts correctly translated to business language
- Meanings preserved during translation
- No information lost in abstraction

**ACTION**: Remove additions, add omissions, correct mistranslations. Track all changes.

---

### 9. Structural Completeness (UI Version)

**Goal**: Ensure all required sections are present and properly formatted.

**Required sections for UI functional specs**:
- Overview (2-3 paragraphs, business language)
- Business Purpose
- Business Rules (Core, Data, Authorization, Temporal subsections)
- **Visual Structure** (layout diagram) - Page Setup & Panel
- **Screen Definition** (Layout, Content Areas, Navigation)
- **Data Display** (for panels/grids)
- **User Actions Available**
- **Form Definition** (if modal or form exists)
- **User Interaction Flows**
- **Visual States** (Loading, Error, Empty, Success)
- **API Consumption** (business language - replaces Database Operations)
- **User Data Flow** (business journey diagram)
- Acceptance Criteria with Gherkin scenarios
- Use Cases (at least one)
- Business Domain Concepts
- Functional Dependencies
- Data Validation Requirements
- Error Conditions & Business Responses
- Questions for Business Clarification (may be empty if none)
- Glossary

**Formatting requirements**:
- Tables properly formatted with all columns
- Gherkin syntax correct (Given/When/Then)
- Markdown renders correctly
- Consistent heading levels
- ASCII diagrams readable

**ACTION**: Add missing sections (even if minimal). Fix formatting issues. Track all changes.

---

### 10. Language Quality

**Goal**: Ensure clear, professional business language throughout.

**Check for**:
- Consistent terminology (same term used for same concept)
- Clear, unambiguous statements
- Active voice preferred
- No jargon or technical terms
- Proper grammar and spelling
- Professional tone

**ACTION**: Correct language issues. Track significant changes.

---

### 11. Cross-Reference Integrity

**Goal**: Ensure internal references are consistent.

**Verify**:
- Business rules referenced in Gherkin comments exist in Business Rules section
- Data elements in input/output tables match what's used in scenarios
- Error conditions in table match scenario error handling
- Use cases reference actual business rules
- Glossary terms match usage in document
- Field names in Form Fields match those used in scenarios

**ACTION**: Fix inconsistencies. Track all changes.

---

### 12. Technical Notes Validation

**Goal**: If technical notes appendix exists, ensure content came from source.

**Verify**:
- [ ] Notes are observations from functional-description.md, not agent-generated recommendations
- [ ] No invented UX improvements, architectural suggestions, or feature additions
- [ ] Appendix is clearly marked as separate from business specification

**ACTION**: Remove any agent-generated recommendations not in source document.

---

### 13. Questions for Business Clarification Validation (CRITICAL)

**Goal**: Ensure the Questions section contains ONLY genuine ambiguities from existing system analysis - no improvement suggestions.

**Context**: This is a modernization project. The goal is to preserve exact current behavior. Questions should only exist when the existing system's behavior genuinely cannot be determined.

**Review each question and REMOVE if it:**
- Suggests adding new features or capabilities ("Should we add...")
- Asks about preferences for how things "should" work
- Proposes improvements to current behavior
- Asks about new system implementation choices
- Raises questions that could be answered by analyzing the existing system

**Questions are ONLY appropriate when:**
- The existing system behaves inconsistently in different situations
- It's genuinely unclear what the system does in a specific case
- There is conflicting or unused functionality that needs clarification

**Inappropriate question patterns to REMOVE:**

| Pattern | Why It's Wrong | Action |
|---------|---------------|--------|
| "Should we add filtering/sorting?" | Suggests new feature | Remove entirely |
| "What would users prefer?" | Asks for preferences, not current behavior | Remove entirely |
| "Should the form have validation for...?" | If it doesn't exist today, don't suggest it | Remove entirely |
| "What is the process for...?" | Process question, not system behavior | Remove entirely |

**If section contains inappropriate questions:**
1. Remove the inappropriate questions
2. If the behavior can be determined from source, document it in the appropriate section
3. If no valid questions remain, replace with: "No clarification needed - all behavior determined from existing system analysis."

**ACTION**: Remove inappropriate questions. This is a CRITICAL check - improvement suggestions do not belong in a modernization specification.

---

## Phase 3: Correction Priorities

When making corrections, prioritize:

1. **CRITICAL** - Must fix:
   - Wrong work unit type or mismatched content
   - Implementation details in specification
   - Missing Visual Structure (for Page Setup/Panel)
   - Missing API Consumption section (or has technical details)
   - Missing Gherkin scenarios for the work unit type
   - Field names derived from screenshots instead of source code
   - Inappropriate questions (improvement suggestions instead of genuine ambiguities)

2. **HIGH** - Should fix:
   - Missing business rules from source
   - Missing User Data Flow section
   - Added content not in source
   - Major structural issues

3. **MEDIUM** - Fix if time permits:
   - Minor structural issues
   - Language clarity improvements

4. **LOW** - Optional:
   - Minor formatting
   - Style preferences

**Preserve what's good**: Don't rewrite things that are already correct.

---

## Phase 4: Generate Review Report

Create `functional-spec-review.md` in the same directory.

### If Issues Were Found and Corrected

```markdown
# Functional Specification Review Report (UI Feature)

> **Reviewed**: [date]
> **Specification**: [path to functional-spec.md]
> **Source**: [path to functional-description.md]
> **Work Unit Type**: [Page Setup / Panel / Modal]
> **Status**: PASSED WITH CORRECTIONS

## Executive Summary

[2-3 sentences: Overall assessment and summary of corrections made]

## Work Unit Type Verification

| Aspect | Status | Notes |
|--------|--------|-------|
| Key Pattern Detection | ✓/Corrected | [Details] |
| Content Matches Type | ✓/Corrected | [Details] |
| Appropriate Focus | ✓/Corrected | [Details] |

## Screenshot Integration

| Aspect | Status | Notes |
|--------|--------|-------|
| Field names from source code | ✓/Corrected | [Details] |
| Layout validated vs screenshots | ✓/N/A | [Details] |
| Discrepancies documented | ✓/Corrected | [Details] |

## Visual Structure Validation

| Aspect | Status | Notes |
|--------|--------|-------|
| ASCII Layout Diagram | ✓/Added/N/A | [Required for Page/Panel; optional for complex modals] |
| Panel Arrangement | ✓/Corrected/N/A | [Details] |
| Relationships Shown | ✓/Corrected/N/A | [Details] |

## API Consumption Validation

| Aspect | Status | Notes |
|--------|--------|-------|
| Section Present | ✓/Added | [Details] |
| Business Language Only | ✓/Corrected | [Details] |
| No Technical Details | ✓/Corrected | [Details] |

## User Data Flow Validation

| Aspect | Status | Notes |
|--------|--------|-------|
| Section Present | ✓/Added | [Details] |
| Business Flow Diagram | ✓/Added/N/A | [Details] |
| User Actions Documented | ✓/Corrected | [Details] |

## Corrections Made

### Critical Issues Corrected

| Issue | Category | Location | Correction |
|-------|----------|----------|------------|
| [Description] | [Work Unit/Visual Structure/API/etc.] | [Section] | [What was changed] |

### High Priority Issues Corrected

| Issue | Category | Location | Correction |
|-------|----------|----------|------------|
| [Description] | [Category] | [Section] | [What was changed] |

### Medium/Low Priority Issues Corrected

| Issue | Category | Location | Correction |
|-------|----------|----------|------------|
| [Description] | [Category] | [Section] | [What was changed] |

## Issues Requiring Human Review

[If any issues couldn't be automatically corrected]

| Issue | Category | Location | Recommendation |
|-------|----------|----------|----------------|
| [Description] | [Category] | [Section] | [What human should do] |

## Gherkin Scenario Coverage by Work Unit Type

### [Work Unit Type] Scenarios

| Scenario Category | Status | Scenarios Present | Notes |
|-------------------|--------|-------------------|-------|
| [Category per work unit type] | ✓/Added/Gap | [List] | [Details] |

#### Page Setup Coverage (if applicable)
| Category | Status | Notes |
|----------|--------|-------|
| Initial page load with data | ✓/Added/Gap | [Details] |
| Search with results | ✓/Added/Gap | [Details] |
| Search with no results | ✓/Added/Gap | [Details] |
| Filter application | ✓/Added/Gap/N/A | [Details] |
| Navigation context | ✓/Added/Gap | [Details] |

#### Panel Coverage (if applicable)
| Category | Status | Notes |
|----------|--------|-------|
| Data display | ✓/Added/Gap | [Details] |
| Selection logic | ✓/Added/Gap | [Details] |
| Menu actions | ✓/Added/Gap | [Details] |
| Context menu display | ✓/Added/Gap | [Details] |

#### Modal Coverage (if applicable)
| Category | Status | Notes |
|----------|--------|-------|
| Modal opens/closes | ✓/Added/Gap | [Details] |
| Form flow | ✓/Added/Gap | [Details] |
| Validation on field exit | ✓/Added/Gap | [Details] |
| Submit success | ✓/Added/Gap | [Details] |
| Submit with errors | ✓/Added/Gap | [Details] |
| Cancel behavior | ✓/Added/Gap | [Details] |

## Implementation Details Removed

| Term/Text Removed | Location | Replacement |
|-------------------|----------|-------------|
| [Technical term] | [Section] | [Business language] |

[If none: "No implementation details found in specification."]

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

- [x] Specification is now ready for stakeholder review
- [x] Work unit type correctly identified and content matches
- [x] Visual structure documented (required for Page Setup/Panel; verified for complex modals)
- [x] API consumption uses business language only
- [x] Field names derived from source code, not screenshots

---

*Review completed by Legacy Analyzer Agent*
```

### If No Issues Found

```markdown
# Functional Specification Review Report (UI Feature)

> **Reviewed**: [date]
> **Specification**: [path to functional-spec.md]
> **Source**: [path to functional-description.md]
> **Work Unit Type**: [Page Setup / Panel / Modal]
> **Status**: PASSED

## Summary

The UI functional specification meets all quality criteria. No corrections were required.

All review checks passed:
- ✓ Work unit type correctly identified and content matches
- ✓ No implementation details in specification
- ✓ Visual structure documented with ASCII diagram (required for Page/Panel; verified for complex modals)
- ✓ API consumption documented in business language
- ✓ User data flow documented
- ✓ Field names from source code (not screenshots)
- ✓ All business rules captured
- ✓ Comprehensive Gherkin scenario coverage for work unit type
- ✓ Source fidelity maintained
- ✓ All sections complete and properly formatted
- ✓ Clear business language throughout

## Certification

- [x] Specification is ready for stakeholder review

---

*Review completed by Legacy Analyzer Agent*
```

### If Major Issues Found

```markdown
# Functional Specification Review Report (UI Feature)

> **Reviewed**: [date]
> **Specification**: [path to functional-spec.md]
> **Source**: [path to functional-description.md]
> **Work Unit Type**: [Page Setup / Panel / Modal]
> **Status**: NEEDS MAJOR REVISION

## Summary

This UI specification requires significant rework and cannot be adequately corrected through editing alone.

## Critical Problems

1. [Fundamental issue #1]
2. [Fundamental issue #2]
3. [Fundamental issue #3]

## Recommendation

Return to creation phase using the `/create-functional-spec-ui` command with closer attention to:
- [Specific guidance]

---

*Review completed by Legacy Analyzer Agent*
```

---

## Quality Standards

A specification **PASSES** if:
- Work unit type correctly identified and content matches
- Zero critical issues remain after corrections
- Visual Structure documented (required for Page Setup/Panel; verified for complex modals)
- API Consumption uses business language only
- Gherkin scenarios cover the work unit type requirements
- No implementation details in specification
- All required sections are present
- Field names from source code, not screenshots
- Questions section contains only genuine ambiguities (or is empty/states no clarification needed)

A specification **PASSES WITH CORRECTIONS** if:
- Corrections were made but specification now meets standards
- Issues were minor to moderate in severity
- Core content was accurate but needed refinement

A specification **NEEDS MAJOR REVISION** if:
- Wrong work unit type with major content mismatch
- Fundamental structural problems
- Large portions of source content missing
- Significant inaccuracies in business rules
- Cannot be corrected through editing alone

---

## Execution Instructions

1. **Parse the key and type parameters** from the command invocation

2. **Construct the directory path**: `./docs/entry-points/{type}/{key}/`

3. **Detect work unit type** from key pattern

4. **Read all relevant files from the directory**:
   - `functional-description.md` (source document)
   - `functional-spec.md` (document to review and correct)
   - `metadata.json` (for context)
   - Screenshots in `screenshots/` subdirectory (for validation)

5. **Systematically work through each review check** based on work unit type

6. **Make corrections directly** to functional-spec.md as you find issues

7. **Track all findings** for the report

8. **Generate the review report** as `functional-spec-review.md` in the same directory

9. **Provide brief summary** to user of review outcome

---

## Begin

The user will invoke this command with key and type parameters. Use these to locate the entry point directory at `./docs/entry-points/{type}/{key}/`, detect the work unit type from the key, then read the required files and begin the review process.
