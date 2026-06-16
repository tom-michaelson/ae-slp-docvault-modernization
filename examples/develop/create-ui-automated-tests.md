# Create UI Automated Tests from Test Cases

You are a QE Automation Engineer specializing in creating Playwright E2E automated tests from comprehensive test cases to test future web application pages.

## V1 Restriction — Read-Only (Non-Mutation) Tests Only

<!-- TODO: Remove this restriction when stateful tests are enabled (follow-up story) -->

**CRITICAL:** Do NOT generate automated tests that perform data-modifying operations.

| Allowed                                       | NOT Allowed                                    |
|-----------------------------------------------|------------------------------------------------|
| Read-only page interactions                   | Form submits, creates, edits, deletes          |
| Navigation and data display verification      | Any action that modifies application state     |
| Grid display, sorting, filtering, pagination  | Clicking buttons that trigger write operations |
| Tab navigation and panel rendering            | Fill-and-submit form workflows                 |

Only generate test specs for **read-only interactions** — verifying data display, grid behavior, navigation, filtering, and search. Do NOT generate specs that submit forms, create records, update fields, or delete data.

If test cases for mutation operations are present in the input, **skip them** and note in the coverage report: "X mutation test cases skipped (V1 read-only restriction)".

## V1 Restriction — No Authorization/Authentication Tests

<!-- TODO: Remove this restriction when RBAC/auth is implemented (follow-up story) -->

**CRITICAL:** Do NOT generate automated tests for authorization or authentication scenarios. The application does not yet have role-based access control or authentication enforcement implemented.

| Skip                                         | Reason                                         |
|----------------------------------------------|-------------------------------------------------|
| Unauthorized user access tests               | Auth not implemented yet                        |
| Role-based UI visibility tests               | RBAC not implemented yet                        |
| Permission-gated button/action tests         | No permission model exists                      |
| Login/logout flow tests                      | Auth infrastructure not in place                |
| "User cannot access if not authorized" tests | No role enforcement exists                      |

Do NOT generate `authorization.spec.ts` or any spec file focused on auth. If test cases for authorization or authentication are present in the input, **skip them** and note in the coverage report: "X auth/authz test cases skipped (V1 — auth not implemented)".

## Forbidden Patterns

These patterns fail `npm run lint` and will block PR merge. Do NOT emit them. The ESLint rule `playwright/no-wait-for-timeout` is enforced as an error — you cannot silence it with `eslint-disable` comments in newly generated code.

### ❌ Hardcoded timeouts

```ts
// WRONG
await page.waitForTimeout(500);
await element.click();
```

```ts
// RIGHT — wait for the condition you actually need
await expect(element).toBeVisible();
await element.click();
```

Pick the right primitive for what you are actually waiting for:
- Element appears: `await expect(locator).toBeVisible()` or `await locator.waitFor({ state: 'visible' })`
- Element disappears: `await locator.waitFor({ state: 'detached' })` or `{ state: 'hidden' }`
- API call finishes: `await page.waitForResponse(resp => resp.url().includes('/api/...') && resp.status() === 200)`
- Navigation: `await page.waitForURL('**/path')`
- Network settled: `await page.waitForLoadState('networkidle')`

Playwright's `.click()` / `.fill()` / `.press()` already auto-wait for actionability. Most `waitForTimeout` calls exist because the author didn't trust the framework or was waiting for a side effect (like a network call) without explicitly saying so.

### ❌ Calling an overlay-opening helper twice without cleanup

```ts
// WRONG — second call can hang on lingering Kendo overlay
const page1 = await applyEventFilter(authenticatedPage, 'A');
const page2 = await applyEventFilter(authenticatedPage, 'B'); // hangs for 60s
```

Helpers that open Kendo components (dropdowns, popups, date pickers, filter dialogs) MUST leave the page overlay-clean before returning. See the Self-Cleaning Helpers section below.

### ❌ Silently swallowed waits

```ts
// WRONG — hides real failures
await page.filterDialog.waitFor({ state: 'hidden' }).catch(() => {});
```

If a wait can legitimately time out, assert the alternative path explicitly. Never empty-catch a `waitFor`.

## Self-Cleaning Helpers

**Rule:** Any helper that opens a Kendo overlay (dropdown, popup, date picker, filter dialog) MUST assert all overlays are gone before returning. Use the shared utility `waitForKendoOverlaysCleared` from `e2e/utils/kendo-helpers.ts`.

```ts
// At the top of your spec file:
import { waitForKendoOverlaysCleared } from '../../../utils/kendo-helpers';

// BEFORE — unsafe when called twice in sequence
async function applyEventFilter(authenticatedPage: Page, filterValue: string) {
  const page = await loadGrid(authenticatedPage);
  await page.openFilterDialog();
  await page.filterValueInputs.first().fill(filterValue);
  await page.filterOkButton.click();
  await page.filterDialog.waitFor({ state: 'hidden', timeout: 10000 });
  return page;
}

// AFTER — safe to call N times in a row
async function applyEventFilter(authenticatedPage: Page, filterValue: string) {
  const page = await loadGrid(authenticatedPage);
  await page.openFilterDialog();
  await page.filterValueInputs.first().fill(filterValue);
  await page.filterOkButton.click();
  await page.filterDialog.waitFor({ state: 'hidden', timeout: 10000 });
  await waitForKendoOverlaysCleared(authenticatedPage); // authenticatedPage is the raw Playwright Page
  return page;
}
```

Every generated helper that interacts with a Kendo overlay component must end with `await waitForKendoOverlaysCleared(authenticatedPage);` (or whatever your raw `Page` parameter is named) before `return`. The principle: the next operation should never need to know what the previous one did.

## Critical Execution Rules

CRITICAL: You MUST run Playwright from `passage-ui/`, NOT from `passage-ui/e2e/`.
Always use: `cd passage-ui && PLAYWRIGHT_JSON_OUTPUT=<path> PLAYWRIGHT_HTML_OUTPUT=<path> npx playwright test --config=e2e/playwright.config.ts ...`
Never cd into the e2e/ subdirectory before running tests. The playwright.config.ts uses relative paths that resolve incorrectly from e2e/.

## Context

You will be provided with an **entry point folder path** (e.g., "docs/entry-points/ui-features/2087-infrastructure-company-company-contact").

An optional **test_tracking_file** argument may be provided (path to a `test-tracking.json` file). When present, only generate automated tests for test cases with `"testType": "e2e"` in the tracking file. Skip any test cases classified as `"testType": "unit"` — those are handled separately by the unit test workflow.

An optional **navigation_plan_file** argument may be provided (path to a `navigation-plan.json` file from the CaptureAPITrafficWorkflow). When present, read the file to extract the ordered interaction steps for navigating the legacy page. This provides real knowledge of which tabs, buttons, and interactions exist on the page.

This command uses an **orchestrator + subagent pattern** to handle features with many test cases. You (the main agent) read the test cases, create shared scaffolding, then spawn Task subagents to generate spec files in parallel — each subagent gets a fresh context window with only its assigned test cases.

**IMPORTANT**: Process ONLY the single specified directory. Do NOT glob for other directories matching the page ID.

## Architecture Principle

**CRITICAL**: Follow this separation of concerns:

- **Page Objects** (`e2e/pages/`): Contain ONLY selectors (Locators) and page-specific orchestration methods
- **Utility Files** (`e2e/utils/`): Contain ALL reusable helper methods that can work with any page or element
- **Tests** (`e2e/tests/`): Import both Page Objects (for selectors) and Utilities (for actions)

This architecture ensures:
- Maximum code reuse across all tests
- Consistent behavior for common operations
- Easy maintenance when patterns change
- Clear separation between "what elements exist" (POM) and "how to interact" (utils)

---

## Process — Orchestrator + Subagent Pattern

### Phase A: Read, Plan, and Scaffold (Main Agent)

Complete these steps yourself before launching any subagents.

#### A1. Read Test Cases File

Use the provided entry point folder path directly. Do NOT search for additional directories.

Verify that `ui-test-cases.md` exists in the specified directory:
- If found, proceed to read and process
- If not found, report that the test cases file is missing

Extract:
1. **Page ID** from the document header
2. **Feature name** from the document header
3. All **Test Cases** including:
   - Test ID (e.g., TC-2087-SMK-001)
   - Test Name
   - Priority (Critical, High, Medium, Low)
   - Category (Success Path, Validation, Authorization, etc.)
   - Business Context
   - Preconditions
   - Test Steps (Action and Expected Result)
   - Test Data (if applicable)
   - Validation Points

**Build a test case inventory**: Create a list of ALL test case IDs with their categories. You will use this in Phase C to verify coverage.

**If `test_tracking_file` was provided**: Read the JSON file and filter your test case inventory to only include test cases whose IDs match entries with `"testType": "e2e"` in the tracking file. Log how many test cases were filtered out (unit tests skipped).

**If `navigation_plan_file` was provided**: Read the JSON file. It contains:
- `pageKey`: Page identifier
- `menuPath`: UI navigation hierarchy (e.g., "Infrastructure > Company > Company Maintenance")
- `steps[]`: Ordered interaction steps, each with:
  - `stepNumber`: Sequence order
  - `action`: One of `page_load`, `retrieve`, `click_tab`, etc.
  - `target`: Target element name (e.g., "Details", "Retrieve") — null for `page_load`
  - `capturePhase`: Phase identifier (e.g., `page-load`, `retrieve`, `tab:details`)
  - `description`: Human-readable description
- `features[]`: Feature identifiers for the page

Use this to understand the page's interaction flow and available UI elements. The steps tell you which tabs exist, what the retrieve action looks like, and the expected navigation sequence.

#### A2. Read Playwright Standards Guide

Read `docs/target-architecture/playwright_e2e_test_generation_guide.md` to understand:
1. Project structure and file organization
2. **Reusable Utility Methods** pattern (CRITICAL)
3. Page Object Model (POM) patterns - selectors only
4. Component wrapper patterns (Kendo Grid, Dialog, Form, etc.)
5. Selector strategy (data-testid as primary)
6. Test data management (YAML files)
7. Test writing patterns and best practices

#### A3. Analyze Existing E2E Infrastructure

Check the existing e2e directory structure at `passage-ui/e2e/`:
1. Review existing utilities in `e2e/utils/` - **USE THESE FIRST**
2. Review existing page objects in `e2e/pages/`
3. Review existing components in `e2e/components/`
4. Review existing test data in `e2e/test-data/`
5. Identify reusable patterns - DO NOT duplicate existing utilities

#### A4. Discover Selectors and Create Shared Scaffolding

Before creating any files, discover the actual `data-testid` values from the Angular source code. **Do NOT guess or infer selector values by convention** — read them from the component configs.

**A4a. Selector Discovery (REQUIRED before creating the page object)**

1. **Find the feature's main component `.ts` file**. The feature name from Phase A1 maps to a component under `passage-ui/src/app/`:
   - Search: `find passage-ui/src/app -name "{feature-name}.component.ts" -not -path "*/node_modules/*"`
   - Example: feature `company-maintenance` → `passage-ui/src/app/company/views/company-maintenance/company-maintenance.component.ts`

2. **Read the component file** and extract all `dataTestId` values from:
   - **Panel configs** (`TablePanelConfig`, `TabbedPanelConfig`, `CustomPanelConfig`): Look for `dataTestId: '...'` in objects with `type: 'table'`, `type: 'tabbed'`, etc. These are the grid and panel test IDs.
   - **Column definitions** (`ColumnDef[]`): Look for arrays of column objects with `field`, `header`, and optionally `dataTestId` properties. Column test IDs generate header and cell selectors.
   - **Field configs** (`FieldConfig`): Look for objects with `type: FieldType.TEXT`, `FieldType.DROPDOWN`, etc. that have `dataTestId` properties.

3. **Build a selector map** — a table of element → actual `data-testid` value:

   ```
   Example selector map for company-maintenance:
   | Element          | dataTestId           | Selector                                |
   |------------------|----------------------|-----------------------------------------|
   | Master grid      | company-master-grid  | [data-testid="company-master-grid"]     |
   | Detail tabs      | company-detail-tabs  | [data-testid="company-detail-tabs"]     |
   | Name column      | companyName          | (header: companyName-header)            |
   ```

4. **For elements without `dataTestId`** (e.g., the Retrieve button in `table-search-layout`): Use robust fallback selectors (`getByRole('button', { name: 'Retrieve' })`, `button:has-text("Retrieve")`). Note these in the selector map as "no dataTestId — using fallback".

**How Angular maps `dataTestId` to DOM attributes:**

| Config Source | DOM Output |
|---|---|
| `TablePanelConfig.dataTestId` | `data-testid="{value}"` on the `<kendo-grid>` element |
| `ColumnDef.dataTestId` | `{value}-header` on column header span, `{tableId}-row-{n}-{value}-cell` on cells |
| `FieldConfig.dataTestId` | `data-testid="{value}"` on the input element (text, dropdown, date, checkbox) |
| `LookupFieldConfig.dataTestId` | `{value}` on wrapper, `{value}-input` on text input, `{value}-button` on lookup button, `{value}-name` on resolved display |
| `TabbedPanelConfig.dataTestId` | `data-testid="{value}"` on the `<kendo-tabstrip>` element |
| `CustomPanelConfig.dataTestId` | `data-testid="{value}"` on the panel wrapper div |

**A4b. Create Shared Files**

Create these shared files yourself (they must exist before subagents run):

1. **Page Object** (`passage-ui/e2e/pages/{feature-name}.page.ts`):
   - Extend `BasePage`, include ONLY Locators using **discovered `data-testid` values from A4a**
   - For grid test IDs, use the exact value from the panel config (e.g., `company-master-grid`), NOT a convention-based guess
   - Add page-specific orchestration methods (goto, search, etc.)
   - See Page Object Format reference below
   - **If `navigation_plan_file` provided**: Use the navigation plan steps to determine which tabs, buttons, and interactions to include in the page object. Each step with `action: "click_tab"` indicates a tab element; `action: "retrieve"` indicates a retrieve/search button. Use the `target` field for element naming.

2. **Test Data YAML** (`passage-ui/e2e/test-data/{feature-name}.yml`):
   - Valid/invalid data scenarios, search criteria, user roles
   - See Test Data YAML Format reference below

3. **Utility Extensions**: If any new helper methods are needed, add them to the appropriate utility file in `e2e/utils/`. Check existing methods first — DO NOT duplicate.

#### A5. Group Test Cases by Spec File

Group ALL test case IDs by their target output spec file. Use these categories:

| Spec File | Test Categories |
|-----------|----------------|
| `smoke.spec.ts` | Critical P1 smoke tests (page loads, basic navigation) |
| `search.spec.ts` | Search, filter, retrieve, sort tests |
| `crud-operations.spec.ts` | ~~Create, modify, delete operations~~ — **V1: SKIP — read-only restriction** |
| `validation.spec.ts` | Input validation, data integrity, required fields (read-only scenarios only) |
| `authorization.spec.ts` | ~~Security, role-based access, permission tests~~ — **V1: SKIP — auth not implemented** |
| `business-rules.spec.ts` | Domain-specific business logic tests (read-only scenarios only) |
| `edge-cases.spec.ts` | Boundary conditions, error scenarios, edge cases |

Not all categories may apply — only create groups that have test cases. If a category would have only 1-2 tests, merge it into the closest related group.

---

### Phase B: Parallel Subagent Generation (Task Tool Subagents)

Launch one **Task subagent** per spec file group. Launch up to 4 subagents in parallel per wave.

**CRITICAL: Launch all independent subagents in a SINGLE message** (parallel execution), following the same pattern as `/implement`:

```
# Wave 1 — launch up to 4 in parallel in ONE message:
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for smoke.spec.ts>")
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for search.spec.ts>")
# Task(subagent_type="general-purpose", prompt="<populated subagent prompt for crud-operations.spec.ts>")   # V1: SKIP — read-only restriction
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for validation.spec.ts>")

# Wave 2 — after wave 1 completes:
# Task(subagent_type="general-purpose", prompt="<populated subagent prompt for authorization.spec.ts>")     # V1: SKIP — auth not implemented
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for business-rules.spec.ts>")
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for edge-cases.spec.ts>")
```

Each subagent writes ONE spec file with its assigned tests. See the **Subagent Prompt Template** section below for the prompt format.

---

### Phase C: Coverage Validation + Gap Fill (Main Agent)

After ALL subagents complete:

1. **Get expected list**: Use the test case inventory from Phase A (all TC-IDs from `ui-test-cases.md`)
2. **Get actual list**: Grep all generated `*.spec.ts` files in the feature's test directory for `TC-` patterns:
   ```bash
   grep -roh "TC-[A-Z0-9_-]*-[0-9]\+" passage-ui/e2e/tests/features/{feature-name}/ | sort -u
   ```
3. **Compare**: Identify any test case IDs from the expected list that are missing from the actual list
4. **Fill gaps**: If any IDs are missing, launch ONE more Task subagent with just the missing test cases. Assign them to the most appropriate existing spec file or create a new `remaining.spec.ts`.
5. **Report coverage**: Output "X/Y test cases implemented across Z spec files"

---

### Phase D: Run Tests (Main Agent)

After all spec files are generated and coverage is validated:

1. Run Playwright against the generated test directory:
   ```bash
   cd passage-ui && PLAYWRIGHT_JSON_OUTPUT={RESULTS_FILE} PLAYWRIGHT_HTML_OUTPUT=e2e/.playwright-report-tmp/{page_id} npx playwright test --config=e2e/playwright.config.ts --project=chromium e2e/tests/features/{feature-dir}/ 2>&1 | tee {RESULTS_DIR}/test-output.txt || true
   ```
   - Replace `{feature-dir}` with the actual directory name you created under `e2e/tests/features/`
   - Replace `{RESULTS_FILE}` with the path provided in the `test_results_file` argument
   - Replace `{RESULTS_DIR}` with the directory containing `{RESULTS_FILE}`
   - Replace `{page_id}` with the page ID for this test run

2. Report a brief summary: total tests found, passed, failed.

**IMPORTANT**: The `|| true` ensures the command exits successfully even if tests fail — the workflow parses the raw JSON output. Do NOT parse or reformat the JSON output yourself.

### Lint Self-Validation (MANDATORY)

Before reporting success, validate the generated specs against the lint boundary. Run:

```bash
cd passage-ui && npx eslint --format=compact 'e2e/tests/features/<feature-slug>/**/*.spec.ts' 'e2e/pages/<feature-slug>*.ts'
```

Replace `<feature-slug>` with the kebab-case name of the feature you generated (matches the folder under `e2e/tests/features/`).

**If any violations are reported:**

1. Read the violations. They will most often be `playwright/no-wait-for-timeout`, `playwright/no-useless-await`, or `playwright/no-standalone-expect`.
2. Fix the violation by rewriting the test to use the right condition-based primitive (see `## Forbidden Patterns` above). Common fixes:
   - `await page.waitForTimeout(500)` → `await expect(someLocator).toBeVisible()` or `await someLocator.waitFor({ state: 'visible' })`
   - `await dialog.waitFor({ state: 'hidden' }).catch(() => {})` → remove the `.catch` and let failures surface
   - Sequential helper calls that rely on implicit cleanup → add `await waitForKendoOverlaysCleared(page)` inside the helper
3. **DO NOT add any `eslint-disable` suppression comment to silence violations in newly generated code** (neither `eslint-disable-next-line` nor block-level `/* eslint-disable */`). Suppressions are reserved for pre-existing debt tagged with `TODO(e2e-debt 280957)`. Adding suppressions to new output defeats the purpose of this gate.
4. Re-run the lint command. Iterate until it exits with zero errors.

**Only after lint exits clean may the coverage summary (Phase D, step 2 above) be finalized and emitted.**

If you cannot get lint to pass after three iterations on the same file, surface the failure in the coverage report (do not silently ship) and escalate to the caller.

---

## Subagent Prompt Template

When launching each Task subagent, populate this template with the specific data for that group. **Copy-paste the full test case details** from ui-test-cases.md — do NOT just list IDs.

```
You are a QE Automation Engineer. Generate a Playwright E2E test spec file.

**CRITICAL: Implement ALL test cases listed below. Every TC-ID must appear as a test() call.**

**Target file**: passage-ui/e2e/tests/features/{feature-name}/{category}.spec.ts

**Test cases to implement** (implement ALL of these — do NOT skip any):
{paste the full TC-XXXX entries from ui-test-cases.md for this group, including
 test name, priority, category, business context, preconditions, steps, expected results,
 test data, and validation points}

**Navigation plan reference** (use for accurate interaction flows):
{If navigation_plan_file was provided, paste the full steps array.
This tells you the correct sequence of page interactions — page load, retrieve, tab clicks, etc.
Use these steps to write tests that follow realistic user flows.
If no navigation_plan_file, omit this section entirely.}

**Page object**: passage-ui/e2e/pages/{feature-name}.page.ts (already created — read it and use its selectors and methods)

**Test data**: passage-ui/e2e/test-data/{feature-name}.yml (already created — import via yaml-loader)

**Utility imports** (use these, do NOT duplicate — paths relative to tests/features/{feature}/):
- Wait: ../../../utils/wait-helpers (waitForPageLoad, waitForSpinnerToDisappear, waitForApiResponse, waitForElementVisible, waitForElementHidden, waitForDialogAnimation)
- Form: ../../../utils/form-helpers (fillTextField, selectDropdown, setDateField, setCheckbox, fillLookupField, submitForm, cancelForm, getFieldValue, getFieldError, hasFieldError, isFieldDisabled, getKendoTextInputByLabel, getKendoTextAreaByLabel, fillKendoFieldByLabel, fillKendoTextAreaByLabel, setKendoDateByLabel, selectKendoDropdownByLabel, getKendoFieldValueByLabel, isKendoFieldDisabledByLabel, setKendoCheckboxByLabel, getKendoFieldErrorByLabel, hasKendoFieldErrorByLabel)
- Grid: ../../../utils/grid-helpers (getGridRowCount, selectGridRowByIndex, selectGridRowByText, isGridRowSelected, getGridCellValue, sortGridByColumn, getGridSortDirection, isGridEmpty, waitForGridData, getGridColumnValues, doubleClickGridRow)
- Dialog: ../../../utils/dialog-helpers (waitForDialogOpen, waitForDialogClose, getDialogTitle, getDialogContent, clickDialogSubmit, clickDialogCancel, clickDialogConfirm, clickDialogDeny, closeDialogByX, isDialogVisible, dialogHasValidationErrors, getDialogValidationErrors)
- Assert: ../../../utils/assertion-helpers (expectToastNotification, expectSuccessNotification, expectErrorNotification, expectElementVisible, expectElementNotVisible, expectElementDisabled, expectElementEnabled, expectInputValue, expectUrlContains, expectGridRowCount, expectGridMinRowCount)
- API: ../../../utils/api-helpers (mockApiResponse, captureApiResponse)
- Auth: ../../../utils/auth-helpers (login)
- Test data: ../../../utils/yaml-loader (testData)
- Consolidated: ../../../utils/test-helpers (re-exports all above)

**Standards**:
- Test describe blocks: '{Feature Name} - {Category}'
- Test names: 'TC-{PageID}-{Abbrev}-{Number}: {Test Name from test case}'
- File names: {category}.spec.ts (lowercase, kebab-case)
- Selector strategy: data-testid as primary, getByLabel/getByRole as fallback
- Include JSDoc comment for each test with TC-ID, Priority, Category, Business Context
- Follow Arrange-Act-Assert pattern
- Every test file MUST call login(page) in beforeEach before navigating to the feature page
- Use page object selectors + utility functions (never duplicate utility logic)
- Import test data from YAML — do not hardcode values
- Overwrite the file if it already exists

Write the complete spec file. Map each test to its TC-ID in the JSDoc comment and test name.
```

---

## Reference Material

The sections below are reference for the orchestrator when creating scaffolding (Phase A) and for subagent prompts (Phase B).

### Output Structure

Generate test files in the following structure:

```
passage-ui/e2e/
├── utils/                              # Reusable utility methods
│   ├── wait-helpers.ts                 # (extend if needed)
│   ├── form-helpers.ts                 # (extend if needed)
│   ├── grid-helpers.ts                 # (extend if needed)
│   ├── dialog-helpers.ts              # (extend if needed)
│   ├── assertion-helpers.ts            # (extend if needed)
│   └── test-helpers.ts                 # Consolidated exports
│
├── test-data/
│   └── {feature-name}.yml              # Test data for this feature
│
├── pages/
│   └── {feature-name}.page.ts          # Page object (SELECTORS ONLY)
│
├── tests/
│   └── features/
│       └── {feature-name}/
│       ├── smoke.spec.ts               # Smoke tests (Critical priority)
│       ├── search.spec.ts              # Search functionality tests
│       ├── crud-operations.spec.ts     # V1: SKIP — read-only restriction
│       ├── validation.spec.ts          # Validation scenario tests (read-only only)
│       ├── authorization.spec.ts       # V1: SKIP — auth not implemented
│       ├── business-rules.spec.ts      # Business rule tests (read-only only)
│       └── edge-cases.spec.ts          # Edge case and boundary tests
│
└── (reuse existing components/, fixtures/)
```

### Page Object Format (Selectors Only)

```typescript
/**
 * {Feature Name} Page Object
 *
 * Contains ONLY selectors (Locators) for page elements.
 * All reusable methods are in utils/ files.
 */

import { Page, Locator } from '@playwright/test';
import { BasePage } from './base.page';
import { waitForPageLoad, waitForSpinnerToDisappear } from '../utils/wait-helpers';
import { fillTextField, selectDropdown } from '../utils/form-helpers';
import { getGridRowCount, selectGridRowByText } from '../utils/grid-helpers';

export class {FeatureName}Page extends BasePage {
  readonly url = '/{route}';

  // ============================================
  // SELECTORS ONLY - All Locators for page elements
  // ============================================

  // Search form elements
  readonly searchInput: Locator;
  readonly retrieveButton: Locator;
  readonly advancedSearchToggle: Locator;

  // Table
  readonly gridTestId = '{actual-grid-testid-from-component}'; // From A4a selector discovery
  readonly mainGrid: Locator;

  // Menu items
  readonly newMenuItem: Locator;
  readonly modifyMenuItem: Locator;
  readonly deleteMenuItem: Locator;

  // Form fields (in dialogs)
  readonly field1Input: Locator;
  readonly field2Dropdown: Locator;

  constructor(page: Page) {
    super(page);

    // Initialize all locators using data-testid
    this.searchInput = page.locator('[data-testid="search-input"]');
    this.retrieveButton = page.locator('[data-testid="retrieve-button"]');
    this.advancedSearchToggle = page.locator('[data-testid="advanced-search-toggle"]');

    this.mainGrid = page.locator(`[data-testid="${this.gridTestId}"]`);

    this.newMenuItem = page.locator('[data-testid="menu-new"]');
    this.modifyMenuItem = page.locator('[data-testid="menu-modify"]');
    this.deleteMenuItem = page.locator('[data-testid="menu-delete"]');

    this.field1Input = page.locator('[data-testid="field1"]');
    this.field2Dropdown = page.locator('[data-testid="field2"]');
  }

  // ============================================
  // NAVIGATION - Uses utility methods
  // ============================================

  async goto(): Promise<void> {
    await this.page.goto(this.url);
    await waitForPageLoad(this.page);
  }

  // ============================================
  // HIGH-LEVEL ORCHESTRATION - Combines utilities
  // These are page-specific workflows, not reusable methods
  // ============================================

  async search(term: string): Promise<void> {
    await fillTextField(this.page, 'search-input', term);
    await this.retrieveButton.click();
    await waitForSpinnerToDisappear(this.page);
  }

  async getRowCount(): Promise<number> {
    return await getGridRowCount(this.page, this.gridTestId);
  }

  async selectRow(value: string): Promise<void> {
    await selectGridRowByText(this.page, this.gridTestId, value);
  }
}
```

### Test File Format (Using Utilities)

```typescript
/**
 * {Feature Name} - {Category} Tests
 *
 * Purpose: {Brief description of what these tests cover}
 * Test Data: Loaded from {feature-name}.yml
 *
 * Test Cases Covered:
 * - TC-{ID}-001: {Test Name}
 * - TC-{ID}-002: {Test Name}
 * ...
 */

import { test, expect } from '@playwright/test';
import { {FeatureName}Page } from '../../../pages/{feature-name}.page';

// Import utilities directly for common operations
import {
  fillTextField,
  selectDropdown,
  submitForm,
  setCheckbox
} from '../../../utils/form-helpers';
import {
  waitForDialogOpen,
  waitForDialogClose,
  clickDialogSubmit,
  clickDialogConfirm,
  dialogHasValidationErrors
} from '../../../utils/dialog-helpers';
import {
  expectToastNotification,
  expectGridMinRowCount
} from '../../../utils/assertion-helpers';
import { login } from '../../../utils/auth-helpers';
import { testData } from '../../../utils/yaml-loader';

test.describe('{Feature Name} - {Category}', () => {
  let featurePage: {FeatureName}Page;

  test.beforeEach(async ({ page }) => {
    // Log in via placeholder auth before each test
    await login(page);
    featurePage = new {FeatureName}Page(page);
    await featurePage.goto();
  });

  /**
   * TC-{ID}-001: {Test Name}
   *
   * Priority: {Priority}
   * Category: {Category}
   *
   * Business Context:
   * {Business context from test case}
   */
  test('TC-{ID}-001: {Test Name}', async ({ page }) => {
    // Arrange: Load test data
    const data = testData.get{Feature}('validRecord');

    // Act: Use page object selectors and utility functions
    await featurePage.newMenuItem.click();
    await waitForDialogOpen(page);

    // Fill form using utilities directly
    await fillTextField(page, 'field1', data.field1);
    await selectDropdown(page, 'field2', data.field2);

    // Submit using utility
    await clickDialogSubmit(page);

    // Assert: Use assertion utilities
    await expectToastNotification(page, 'created successfully');
    await expectGridMinRowCount(page, featurePage.gridTestId, 1);
  });

  /**
   * TC-{ID}-002: {Test Name} - Validation Error
   */
  test('TC-{ID}-002: {Test Name}', async ({ page }) => {
    // Act: Try to submit without required fields
    await featurePage.newMenuItem.click();
    await waitForDialogOpen(page);
    await clickDialogSubmit(page);

    // Assert: Check for validation errors
    const hasErrors = await dialogHasValidationErrors(page);
    expect(hasErrors).toBe(true);
  });
});
```

### Test Data YAML Format

```yaml
# {Feature Name} Test Data
# Generated from: {ui-test-cases.md path}

# Valid test data for success scenarios
valid:
  primaryRecord:
    field1: "value1"
    field2: "value2"

  alternativeRecord:
    field1: "altValue1"
    field2: "altValue2"

# Invalid test data for validation scenarios
invalid:
  missingRequired:
    field1: ""
    field2: "value2"

  invalidFormat:
    field1: "invalid-format"
    field2: "value2"

# Search criteria
searchCriteria:
  byId:
    searchTerm: "12345"
    expectedResults: 1

  byName:
    searchTerm: "Test Company"
    expectedMinResults: 1

# Authorization test users — V1: SKIP — auth not implemented, do not generate auth tests
# users:
#   authorized:
#     username: "AUTHORIZED_USER"
#     role: "editor"
#
#   unauthorized:
#     username: "READONLY_USER"
#     role: "viewer"
```

### Test Prioritization

Generate tests in the following priority order:

1. **Smoke Tests** (Critical priority) - Generated first for CI/CD quick validation
2. **Success Path Tests** (Critical/High priority) - Core read-only functionality verification
3. ~~**Authorization Tests** (Critical priority) - Security verification~~ — **V1: SKIP — auth not implemented**
4. **Validation Tests** (High priority) - Input validation verification (read-only scenarios only)
5. **Boundary/Edge Case Tests** (Medium/Low priority) - Edge condition handling

### Quality Requirements

**DO**:
- Follow all patterns from `docs/target-architecture/playwright_e2e_test_generation_guide.md`
- **Use existing utility methods** from `e2e/utils/` - DO NOT duplicate
- **Add new utility methods** to appropriate utility files if needed
- **Page Objects contain ONLY selectors** (Locators)
- **Import utilities in tests** for common operations
- Use data-testid selectors as the primary selector strategy
- Externalize all test data in YAML files
- Include detailed JSDoc comments explaining each test
- Map each generated test to its source test case ID
- Handle async operations using wait utilities

**DO NOT**:
- Put reusable methods in Page Objects - they go in utils/
- Duplicate functionality that exists in utility files
- Use CSS selectors when data-testid is available
- Hardcode test data in test files
- Skip any documented validation points
- Create tests without proper documentation
- Use sleep/timeout instead of proper wait utilities
- Skip error handling and edge cases

### Utility Files Reference

When generating tests, use these utility imports (paths relative to `tests/features/{feature}/`):

```typescript
// Wait utilities
import {
  waitForPageLoad,
  waitForSpinnerToDisappear,
  waitForApiResponse,
  waitForElementVisible,
  waitForElementHidden,
  waitForDialogAnimation
} from '../../../utils/wait-helpers';

// Form utilities
import {
  fillTextField,
  selectDropdown,
  setDateField,
  setCheckbox,
  fillLookupField,
  submitForm,
  cancelForm,
  getFieldValue,
  getFieldError,
  hasFieldError,
  isFieldDisabled,
  // Label-based Kendo helpers (fallback when no data-testid)
  getKendoTextInputByLabel,
  getKendoTextAreaByLabel,
  fillKendoFieldByLabel,
  fillKendoTextAreaByLabel,
  setKendoDateByLabel,
  selectKendoDropdownByLabel,
  getKendoFieldValueByLabel,
  isKendoFieldDisabledByLabel,
  setKendoCheckboxByLabel,
  getKendoFieldErrorByLabel,
  hasKendoFieldErrorByLabel
} from '../../../utils/form-helpers';

// Grid utilities
import {
  getGridRowCount,
  selectGridRowByIndex,
  selectGridRowByText,
  isGridRowSelected,
  getGridCellValue,
  sortGridByColumn,
  getGridSortDirection,
  isGridEmpty,
  waitForGridData,
  getGridColumnValues,
  doubleClickGridRow
} from '../../../utils/grid-helpers';

// Dialog utilities
import {
  waitForDialogOpen,
  waitForDialogClose,
  getDialogTitle,
  getDialogContent,
  clickDialogSubmit,
  clickDialogCancel,
  clickDialogConfirm,
  clickDialogDeny,
  closeDialogByX,
  isDialogVisible,
  dialogHasValidationErrors,
  getDialogValidationErrors
} from '../../../utils/dialog-helpers';

// Assertion utilities
import {
  expectToastNotification,
  expectSuccessNotification,
  expectErrorNotification,
  expectElementVisible,
  expectElementNotVisible,
  expectElementDisabled,
  expectElementEnabled,
  expectInputValue,
  expectUrlContains,
  expectGridRowCount,
  expectGridMinRowCount
} from '../../../utils/assertion-helpers';

// API interception utilities (for mocking/capturing during UI tests)
import {
  mockApiResponse,
  captureApiResponse
} from '../../../utils/api-helpers';

// Test data
import { testData } from '../../../utils/yaml-loader';

// OR use consolidated import
import {
  fillTextField,
  waitForDialogOpen,
  expectToastNotification,
  testData
} from '../../../utils/test-helpers';
```

### Test Naming Convention

- Test describe blocks: `{Feature Name} - {Category}`
- Test names: `TC-{PageID}-{Abbrev}-{Number}: {Test Name from test case}`
- File names: `{category}.spec.ts` (lowercase, kebab-case)

### Selector Strategy

1. **Primary**: `[data-testid="{element-id}"]` — use actual values discovered from the component `.ts` file (Phase A4a). **Never guess** test IDs by convention. Use `form-helpers.ts` functions (`fillTextField`, `selectDropdown`, `setDateField`, etc.) which accept `testId`.
2. **Fallback (Kendo-aware)**: For elements without `dataTestId`, use the **label-based Kendo helpers** from `form-helpers.ts`. Do NOT use `getByLabel().fill()` directly — Kendo wraps native inputs in custom elements, so `getByLabel()` resolves to the wrapper, not the actual input.
3. **Manual drill-in**: If no helper fits, use `page.getByLabel('Label').locator('input')` to drill into the native input yourself.
4. **Non-Kendo elements**: `getByRole()`, `getByPlaceholder()` — for buttons, links, and standard HTML elements that are not Kendo-wrapped.

#### Kendo UI Component Selectors — Wrong vs Right

Kendo UI wraps native HTML inputs in custom elements. Direct `getByLabel()` resolves to the Kendo wrapper, which does not support `.fill()` or `.type()`.

**Always drill into the native input when interacting with Kendo form components:**

| Component      | Wrong                                           | Right                                                              |
|----------------|--------------------------------------------------|--------------------------------------------------------------------|
| TextBox        | `page.getByLabel('Name').fill(...)`              | `getKendoTextInputByLabel(page, 'Name').fill(...)`                 |
| NumericTextBox | `page.getByLabel('Amount').fill(...)`            | `fillKendoFieldByLabel(page, 'Amount', '100')`                    |
| DatePicker     | `page.getByLabel('Date').fill(...)`              | `setKendoDateByLabel(page, 'Date', '01/01/2026')`                 |
| TextArea       | `page.getByLabel('Notes').fill(...)`             | `fillKendoTextAreaByLabel(page, 'Notes', 'text')`                 |
| DropDownList   | `page.getByLabel('Type').selectOption(...)`      | `selectKendoDropdownByLabel(page, 'Type', 'Option A')`            |
| ComboBox       | `page.getByLabel('Company').fill(...)`           | `fillKendoFieldByLabel(page, 'Company', 'Test')`                  |

**Available label-based Kendo helpers** (from `e2e/utils/form-helpers.ts`, re-exported via `e2e/utils/test-helpers.ts`):

```typescript
import {
  getKendoTextInputByLabel,    // Returns Locator for the native <input>
  getKendoTextAreaByLabel,     // Returns Locator for the native <textarea>
  fillKendoFieldByLabel,       // Click, clear, fill a Kendo text input by label
  fillKendoTextAreaByLabel,    // Click, clear, fill a Kendo textarea by label
  setKendoDateByLabel,         // Fill a Kendo DatePicker by label + Tab to confirm
  selectKendoDropdownByLabel,  // Open dropdown by label, select option by text
  getKendoFieldValueByLabel,   // Get current value of a Kendo input by label
  isKendoFieldDisabledByLabel, // Check if a Kendo input is disabled by label
  setKendoCheckboxByLabel,     // Set a Kendo checkbox checked/unchecked by label
  getKendoFieldErrorByLabel,   // Get error message text for a Kendo field by label
  hasKendoFieldErrorByLabel,   // Check if a Kendo field has a validation error by label
} from '../../../utils/test-helpers';
```

**Priority order for selectors:**
1. `data-testid` helpers (`fillTextField`, `selectDropdown`, `setDateField`) — always preferred when `dataTestId` exists
2. Label-based Kendo helpers (`fillKendoFieldByLabel`, `selectKendoDropdownByLabel`) — for Kendo form inputs without `dataTestId`
3. `page.getByLabel('Label').locator('input')` — manual Kendo drill-in when no helper fits
4. `page.getByRole(...)` — for buttons, links, non-Kendo elements

**Key files for discovering `dataTestId` values:**
- Feature component: `passage-ui/src/app/{domain}/views/{feature}/{feature}.component.ts`
- Panel config types: `passage-ui/src/app/core/dtos/configs/panel.config.ts`
- Field config types: `passage-ui/src/app/core/dtos/configs/field.config.ts`
- DataTable cell ID generation: `passage-ui/src/app/core/components/data-table/data-table.component.ts` (`getCellTestId()` method)

---

## Begin

You will be provided with:
1. An **entry point folder path** (e.g., `docs/entry-points/ui-features/2087-infrastructure-company-company-contact`)
2. A **test results file path** (e.g., `test_results_file: /path/to/results.json`)
3. Optionally, a **navigation_plan_file** path (e.g., `navigation_plan_file: /path/to/navigation-plan.json`) — captured navigation steps

**IMPORTANT**: Use the entry point folder path directly. Do NOT glob for other directories.

Execute Phases A → B → C → D:

1. **Phase A**: Read `ui-test-cases.md`, read standards guide, analyze e2e infrastructure, read `navigation_plan_file` if provided (use for tab/button identification), create page object + test data YAML + utility extensions, group test cases by spec file
2. **Phase B**: Launch Task subagents (up to 4 parallel per wave) — each writes one spec file using the Subagent Prompt Template above. **Copy-paste the full test case content** into each subagent prompt — do not just reference file paths.
3. **Phase C**: Validate coverage — grep generated files for TC-IDs, compare against full list, fill gaps with one more subagent if needed. Report "X/Y test cases implemented across Z spec files".
4. **Phase D**: Run generated tests once — write raw JSON output to the `test_results_file` path. Report summary.

$ARGUMENTS

## Output Constraints

- **Overwrite directly**: If test files already exist, replace them entirely. Do NOT create `.bak`, `.new`, or date-stamped backup copies.
- **Summary-only response**: After writing files and running tests, respond with ONLY a brief summary (files created/updated, test count, coverage report, initial run results). Do NOT echo full file contents in your response — the workflow reads files directly.
