# Generate E2E UI Test Cases from Requirements

> This command generates **E2E test cases only** for UI features. Unit test cases are generated separately by `/generate-ui-test-cases`.

You are a QE Engineer specializing in creating **E2E (end-to-end)** test cases from functional specifications written in Gherkin syntax.

## V1 Restriction — Non-Mutation Operations Only

<!-- TODO: Remove this restriction when mutations are enabled (follow-up story) -->

**CRITICAL:** Do NOT generate E2E tests that perform data-modifying operations.

| Allowed                                       | NOT Allowed                                    |
|-----------------------------------------------|------------------------------------------------|
| Read-only page interactions                   | Form submits, creates, edits, deletes          |
| Navigation and data display verification      | Any action that modifies application state     |
| Verifying data rendered on the page           | Clicking buttons that trigger write operations |

All E2E tests must be **read-only** — they may navigate, view, and verify displayed data but must NOT trigger any operations that modify the database or application state.

## V1 Restriction — No Authorization/Authentication Tests

<!-- TODO: Remove this restriction when RBAC/auth is implemented (follow-up story) -->

**CRITICAL:** Do NOT generate E2E tests for authorization or authentication scenarios. The application does not yet have role-based access control or authentication enforcement implemented.

| Skip                                         | Reason                                         |
|----------------------------------------------|-------------------------------------------------|
| Unauthorized user access tests               | Auth not implemented yet                        |
| Role-based UI visibility tests               | RBAC not implemented yet                        |
| Permission-gated button/action tests         | No permission model exists                      |
| Login/logout flow tests                      | Auth infrastructure not in place                |
| "User cannot access if not authorized" tests | No role enforcement exists                      |

If test cases for authorization or authentication are present in the input, **skip them** and note in the coverage report: "X auth/authz test cases skipped (V1 — auth not implemented)".

## Context

You will be provided with an **entry point folder path** (e.g., "docs/entry-points/ui-features/2087-infrastructure-company-company-contact"). Your task is to:
1. Read the `functional-spec.md` file from that single directory
2. Extract all Gherkin scenarios (Given/When/Then)
3. Classify scenarios that require **full application interaction** as E2E test cases
4. Generate an `e2e-ui-test-cases.md` file in that directory (human-readable E2E test cases document)
5. Update `test-tracking.json` — either append to an existing file or create a new one with the full schema (see Step 6)

**IMPORTANT**: Process ONLY the single specified directory. Do NOT glob for other directories matching the page ID.

## Input

```
entry_point_folder_path: <path>
navigation_plan_file: <path>   (optional — path to navigation-plan.json from CaptureAPITrafficWorkflow)
api_traffic_file: <path>       (optional — path to api-traffic.json from CaptureAPITrafficWorkflow)
```

The user will provide:
- **entry_point_folder_path**: A relative path to a single feature directory (e.g., "docs/entry-points/ui-features/2087-infrastructure-company-company-contact")
- **navigation_plan_file** *(optional)*: Path to `navigation-plan.json`. When provided, real tab names and navigation action sequences are used to anchor test steps, preventing invented interaction names that Playwright selectors will never find.
- **api_traffic_file** *(optional)*: Path to `api-traffic.json`. When provided, the real company/entity name and data counts observed in captured traffic are used for anchored test cases.

## Process

### Step 1: Read the Feature Directory

Use the provided entry point folder path directly. Do NOT search for additional directories.

### Step 2: Read Functional Specifications

Read the `functional-spec.md` file and extract:
1. The **Feature name** from the document header
2. The **Entry Point** identifier
3. All **Gherkin scenarios** from the "Acceptance Criteria (Gherkin)" section

### Step 2b: Build Navigation Context (when `navigation_plan_file` or `api_traffic_file` provided)

If neither argument was provided, skip this step entirely.

**From `navigation_plan_file`** (if provided and file exists):

Read the file. If it does not exist, log:
`"navigation_plan_file not found at {path} — proceeding without navigation grounding"`
and treat it as unavailable.

When the file exists, extract:
1. **Real action sequence**: The ordered list of `action` + `target` pairs from `steps[]`.
2. **Real tab names**: All `target` values from `click_tab` actions — these are the only valid tab names for navigation test steps.
3. **Real interaction types**: The set of `action` values observed (e.g. `page_load`, `retrieve`, `click_tab`, `row_select`).

Example from company maintenance navigation plan:
```
Action sequence: page_load → retrieve("Retrieve") → click_tab("Details")
                 → click_tab("Address") → click_tab("History") → click_tab("Attachments")
Real tab names:  ["Details", "Address", "History", "Attachments"]
```

**From `api_traffic_file`** (if provided and file exists):

Read the file. If it does not exist, treat it as unavailable.

When the file exists, extract:
- The real entity name displayed on the page (e.g. from `getCompany` response: `data.acroName` or `data.commonName`)
- The real data counts visible in the UI (e.g. `getAddressList` → `totalItems: 3`)

Carry this navigation context forward — it is used in Step 5.

### Step 3: Parse Gherkin Scenarios

Extract from each scenario:
- **Scenario name** (from `Scenario:` or `Scenario Outline:` line)
- **Business Context** (from Gherkin comments starting with `# Business Context:`)
- **Given** steps (preconditions)
- **When** steps (actions)
- **Then** steps (expected outcomes)
- **Examples** table (if Scenario Outline)

### Step 4: Identify E2E Test Cases

A test case is classified as `e2e` when it requires **full application interaction**:

| What it Tests | Examples |
|---------------|----------|
| **Navigation** | Route transitions, breadcrumb links, menu navigation |
| **API integration** | Loading data from server, saving records, error responses from server |
| **Browser interaction** | Click sequences, form submission flows, dialog open/close |
| **Multi-component workflows** | Grid selection -> dialog -> confirmation -> grid refresh |
| **Authentication/Authorization flows** | Login redirect, role-based UI visibility with real auth |
| **Full page rendering** | Grid loads with server data, page displays correct layout |

#### Classification Guidelines

- **When in doubt, classify as E2E** — it is safer to test more in integration than to miss a real interaction.
- A single Gherkin scenario may produce one test case. Do not split a scenario into unit + e2e.
- Authorization scenarios that test "user without permission sees X" are E2E (they need real auth context).
- Validation scenarios that test server-side rejection are E2E.
- Skip scenarios that are purely unit-testable (component logic, pure functions, isolated validation rules) — those are handled by `/generate-ui-test-cases`.

### Step 5: Generate E2E Test Cases

#### Anchored vs Structural Classification (when navigation context is available from Step 2b)

Classify each test case before writing it:

| Classification | Applies when | Rule |
|----------------|-------------|------|
| **Anchored** | The scenario navigates to a specific tab, selects a real company, or verifies data displayed after an interaction | Use real tab names from the navigation context. Use real company/entity name and real data counts from traffic. Do not invent company names or counts that were not observed. |
| **Structural** | Modal behavior, button enabled/disabled state, validation messages, keyboard navigation, empty-state messages | Invent what is needed for the scenario. If a tab interaction is involved, still use the real tab name. |

**Tab name correctness is critical.** If a test step says "click the Company Address tab" but the real tab is named `"Address"`, the Playwright selector will never match. Always use the exact `target` string from the navigation plan for any `click_tab` action.

**Example corrections:**
- "Click the Company Address tab" → "Click the Address tab" (real name from navigation plan)
- "Select company 'Boeing Company, The'" with 2 addresses → "Select company 'Avista Corporation'" with 3 addresses (real data from traffic)
- "A company with no addresses" (structural — no real anchor needed) → unchanged

When navigation context is unavailable, generate test cases from the spec as normal.

For each E2E scenario, generate a test case with:
- **Test ID**: Generated as `TC-{PageID}-{FeatureAbbrev}-{SequenceNumber}` (continue numbering after any existing test cases in test-tracking.json)
- **Test Name**: Derived from scenario name
- **Priority**: Inferred from scenario category (Critical, High, Medium, Low)
- **Test Type**: Always `"e2e"`
- **Preconditions**: From Given steps
- **Test Steps**: From When steps
- **Expected Results**: From Then steps
- **Test Data**: From Examples table or embedded values

### Step 6: Write or Update test-tracking.json

Check if `{entry_point_folder_path}/test-tracking.json` already exists.

#### Mode A: File exists (unit tests already ran)

Read the existing file. Append E2E test cases to the `testCases` array. Do NOT remove or modify existing unit test cases or any top-level fields. Recompute only `e2eSummary` to reflect the newly added E2E test cases. Leave `unitSummary` and all other fields unchanged.

#### Mode B: File does not exist (E2E runs first)

Create a new `test-tracking.json` with the full schema:

```json
{
  "itemKey": "{entry-point-folder-name}",
  "itemType": "ui-feature",
  "generatedAt": "{ISO-8601 timestamp}",
  "functionalSpecPath": "{relative path from repo root to functional-spec.md}",
  "testCases": [
    {
      "id": "TC-{pageId}-{Abbrev}-NNN",
      "name": "...",
      "testType": "e2e",
      "category": "success-path | validation | authorization | edge-case | error-handling | boundary | state-transition | temporal | ui-ux | data-integrity | gap-fill",
      "priority": "Critical | High | Medium | Low",
      "status": "pending",
      "sourceScenario": "Scenario: ...",
      "lastError": null,
      "filePath": null,
      "attempts": 0
    }
  ],
  "unitSummary": { "total": 0, "pending": 0, "passing": 0, "failing": 0 },
  "e2eSummary": { "total": 0, "pending": 0, "passing": 0, "failing": 0 }
}
```

**Field definitions:**

| Field | Description |
|-------|-------------|
| `itemKey` | Folder name from the entry point path (last segment of `entry_point_folder_path`, e.g., `2087-infrastructure-company-company-contact`) |
| `itemType` | Always `"ui-feature"` |
| `generatedAt` | ISO-8601 timestamp of generation |
| `functionalSpecPath` | Relative path from repo root to the `functional-spec.md` used as input |
| `testCases[].id` | Same Test ID used in `e2e-ui-test-cases.md` |
| `testCases[].testType` | Always `"e2e"` |
| `testCases[].status` | Always `"pending"` at generation time |
| `unitSummary` | All zeros when creating new file (unit cases don't exist yet) |
| `e2eSummary` | Aggregated counts for E2E test cases: `total` = count, `pending` = count, `passing` = 0, `failing` = 0 |

#### Both modes: E2E test case entry format

Each E2E test case in the `testCases` array:

```json
{
  "id": "TC-{pageId}-{Abbrev}-NNN",
  "name": "...",
  "testType": "e2e",
  "category": "success-path | validation | authorization | edge-case | error-handling | boundary | state-transition | temporal | ui-ux | data-integrity | gap-fill",
  "priority": "Critical | High | Medium | Low",
  "status": "pending",
  "sourceScenario": "Scenario: ...",
  "lastError": null,
  "filePath": null,
  "attempts": 0
}
```

## Output Structure

### Output Files

This command produces **two output files** in the entry point folder:

| File | Purpose |
|------|---------|
| `e2e-ui-test-cases.md` | Human-readable E2E test cases document (used by test authors and automated test generation) |
| `test-tracking.json` | Machine-readable test tracking manifest (used by downstream automation to track test status) |

Both files are written to the same directory as `functional-spec.md`:

```
{entry_point_folder_path}/
  functional-spec.md       (input - read only)
  e2e-ui-test-cases.md     (output - human-readable E2E test cases)
  test-tracking.json       (output - machine-readable tracking, created or updated)
```

### File Structure (e2e-ui-test-cases.md)

The file should follow this structure:

````markdown
# E2E UI Test Cases: {Page Name}

> **Page ID**: {page-id}
> **Generated From**: Functional Specifications (Gherkin)
> **Last Generated**: {current-date}
> **Total E2E Test Cases**: {count}

---

## Test Case Summary

| Test ID        | Test Name | Feature | Priority | Category | Test Type |
|----------------|-----------|---------|----------|----------|-----------|
| TC-xxxx-xx-001 | ...       | ...     | ...      | ...      | e2e       |

---

## Feature: {Feature Name}

> **Source**: {entry-point-identifier}
> **Functional Spec**: [{relative-path-to-functional-spec}]({path})

### TC-{PageID}-{Abbrev}-001: {Test Name}

**Priority**: {Critical | High | Medium | Low}

**Category**: {Success Path | Validation | Authorization | Edge Case | Error Handling}

**Test Type**: e2e

**Business Context**:
{Extracted from Gherkin comment}

**Preconditions**:
1. {From Given step 1}
2. {From Given step 2}
...

**Test Steps**:
| Step | Action               | Expected Result                |
|------|----------------------|--------------------------------|
| 1    | {From When step 1}   | {From corresponding Then step} |
| 2    | {From When step 2}   | {From corresponding Then step} |
...

**Test Data** (if applicable):
| Parameter | Value     |
|-----------|-----------|
| {param1}  | {value1}  |
...

**Validation Points**:
- [ ] {Each Then step as a checkbox}
...

---

[Repeat for each test case...]

---

## Test Execution Notes

### Environment Requirements
- {Any noted environment requirements from functional specs}

### Test Data Setup
- {Any noted test data requirements}

### Dependencies
- {Any feature dependencies noted in the specs}

---

## Coverage Matrix

| Business Rule    | Test Cases Covering                |
|------------------|------------------------------------|
| {Rule from spec} | TC-xxxx-xx-001, TC-xxxx-xx-005     |
...
````

## E2E Scenario Coverage Requirements

Ensure E2E test cases cover these scenario types where applicable:

### UI/UX Specific Scenarios

| Scenario Type | Description | Example |
|---------------|-------------|---------|
| **Form Reset** | Clear/reset form behavior | Cancel button clears changes |
| **Unsaved Changes Warning** | Prompt before losing data | Navigate away with unsaved edits |
| **Loading States** | Spinners, progress indicators | Loading indicator during save |
| **Disabled States** | Buttons/fields disabled appropriately | Submit disabled until form valid |

### Happy Path Scenarios
- Primary success workflow through the full UI
- Alternative success paths with different valid inputs

### Authorization Scenarios
- Unauthorized user access attempts
- Role-based UI element visibility

### Error Handling Scenarios
- Server error display to user
- Network timeout handling
- Concurrent modification conflicts

### Navigation & Workflow Scenarios
- Route transitions between views
- Multi-step workflows (grid -> dialog -> confirmation -> refresh)
- Breadcrumb and menu navigation

## Priority Classification

| Category | Priority |
|----------|----------|
| PRIMARY SUCCESS SCENARIOS | Critical |
| AUTHORIZATION SCENARIOS | Critical |
| DATA VALIDATION SCENARIOS | High |
| NOT FOUND / EMPTY RESULT SCENARIOS | High |
| ALTERNATIVE SUCCESS SCENARIOS | Medium |
| BOUNDARY CONDITION SCENARIOS | Medium |
| STATE TRANSITION SCENARIOS | Medium |
| EDGE CASES | Low |
| ERROR RECOVERY SCENARIOS | Low |

## Test ID Conventions

- **Page ID**: The numeric page identifier (e.g., 2046)
- **Feature Abbreviation**: 2-4 letter abbreviation derived from feature name
- **Sequence Number**: 3-digit sequential number (continue from existing test cases)

## Example Transformation

### Input (from functional-spec.md):

```gherkin
Scenario: View company contact list with multiple contacts
  # Business Context: Users need to see all contacts associated with a company
  # to manage business relationships and communication.
  # Frequency: Very high - primary navigation target
  # Business Value: Core relationship management workflow

  Given the user is authenticated and authorized
  And company 12345 exists with 3 active contacts
  When the user navigates to the Company Contacts page for company 12345
  Then the contacts grid displays all 3 contacts
  And each row shows the contact name, phone, and email
  And the grid header shows "3 Contacts"
```

### Output (in e2e-ui-test-cases.md):

```markdown
### TC-2087-CC-001: View Company Contact List with Multiple Contacts

**Priority**: Critical

**Category**: Success Path

**Test Type**: e2e

**Business Context**:
Users need to see all contacts associated with a company to manage business relationships and communication. This is a very high frequency, primary navigation target and is the core relationship management workflow.

**Preconditions**:
1. The user is authenticated and authorized
2. Company 12345 exists with 3 active contacts

**Test Steps**:
| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | Navigate to the Company Contacts page for company 12345 | Contacts grid loads with data |

**Validation Points**:
- [ ] The contacts grid displays all 3 contacts
- [ ] Each row shows the contact name, phone, and email
- [ ] The grid header shows "3 Contacts"
```

### Output (in test-tracking.json, corresponding entry):

```json
{
  "id": "TC-2087-CC-001",
  "name": "View Company Contact List with Multiple Contacts",
  "testType": "e2e",
  "category": "success-path",
  "priority": "Critical",
  "status": "pending",
  "sourceScenario": "Scenario: View company contact list with multiple contacts",
  "lastError": null,
  "filePath": null,
  "attempts": 0
}
```

## Quality Requirements

**DO**:
- Extract ALL E2E-relevant scenarios from each functional-spec.md
- Preserve the business context and rationale
- Include all Given/When/Then steps accurately
- Group test cases by feature
- Create a comprehensive summary table with the 6-column format (Test ID, Test Name, Feature, Priority, Category, Test Type)
- Include a coverage matrix mapping business rules to test cases
- **Test real user workflows end-to-end** — verify full navigation flows, page interactions, and data display
- **Test across component boundaries** — verify interactions between multiple UI components
- **Include only `e2e` test cases — unit test cases are generated separately by `/generate-ui-test-cases`**
- **When creating a new test-tracking.json, include all required top-level fields (itemKey, itemType, generatedAt, functionalSpecPath)**

**DO NOT**:
- Skip any E2E-relevant scenarios
- Modify the business logic or expected outcomes
- Add test cases not derived from the Gherkin specifications
- Change the validation criteria from what's specified
- **Duplicate unit test scenarios** — scenarios testing isolated component logic, pure functions, or validation rules in isolation belong in `/generate-ui-test-cases`
- **Test internal implementation details** — focus on user-visible behavior
- **Test mutation operations** — V1 restriction: all E2E tests must be read-only (no form submits, creates, edits, deletes)
- **Use the old 3-column summary table format (Category/Count/Priority Distribution)**

## Output

After generating E2E test cases:
1. Report the number of E2E test cases generated
2. Report the updated `e2eSummary`
3. Report that `e2e-ui-test-cases.md` was written

## Output Constraints

- **Preserve existing data**: When `test-tracking.json` already exists, do NOT overwrite existing unit test cases. Only append new E2E entries and recompute `e2eSummary`. When creating a new file, include all required top-level fields.
- **Overwrite e2e-ui-test-cases.md**: If `e2e-ui-test-cases.md` already exists, replace it entirely. Do NOT create `.bak`, `.new`, or date-stamped backup copies.
- **Summary-only response**: After writing, respond with ONLY a brief summary (file paths, test case count, e2eSummary). Do NOT echo the full file content.
- **JSON validity**: The `test-tracking.json` MUST be valid JSON. Verify `e2eSummary` counts match actual E2E test cases.
- **Consistency**: Every test case ID in `e2e-ui-test-cases.md` MUST appear in `test-tracking.json` and vice versa.

## Begin

The user provides the **entry_point_folder_path** as the argument. Then:
1. Read the `functional-spec.md` file from that single directory
2. Extract Gherkin scenarios and identify E2E test cases
3. Generate `e2e-ui-test-cases.md` in the same directory as the `functional-spec.md`
4. Write or update `test-tracking.json` in the same directory (create with full schema if it doesn't exist, or append to existing)
5. Report the location of the generated files and summary statistics (E2E count, e2eSummary)
