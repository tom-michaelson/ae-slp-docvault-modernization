---
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "cd $CLAUDE_PROJECT_DIR/passage-ui && npm run format 2>&1 | tail -5"
---

# Generate UI Unit Tests

Generate UI unit tests for modified/added Angular files in the current branch. Uses git diff to discover changed files, reads test-tracking.json for pending test cases, runs Istanbul coverage analysis to identify gaps, generates Karma/Jasmine tests following project patterns, runs tests in a fix loop (max 5 attempts), and verifies the 85% coverage threshold is met.

## Common Foundation

@generate-unit-tests-common.md

## Usage

```
/generate-ui-unit-tests entry_point_folder_path: $ARGUMENTS
```

## Input

| Parameter | Description |
|-----------|-------------|
| `entry_point_folder_path` | Relative path to the entry point folder (e.g., `docs/entry-points/ui-features/2087-infrastructure-company-company-contact`). The result JSON will be written here. |

---

## Phase 0: Discover Modified UI Files

**Purpose:** Identify Angular source files changed in the current branch that need test coverage.

**Steps:**

1. Run `git diff main...HEAD --name-only -- passage-ui/src/` to find committed changes
2. Run `git diff --name-only -- passage-ui/src/` to find uncommitted staged changes
3. Merge and deduplicate all results
4. Filter to `.ts` files under `passage-ui/src/app/`
5. Exclude files that should not be unit tested:
   - `*.spec.ts` (test files themselves)
   - `*.module.ts` (Angular modules)
   - `*.routing.ts` (routing modules)
   - `**/models/**` (interfaces/types)
   - `**/environments/**` (environment configs)

**Output:** List of Angular source files requiring test coverage analysis.

**Early exit:** If no modified UI files are found AND no pending test cases in test-tracking.json, write success result and exit:

```json
{
  "validated": true,
  "notes": "No modified UI files found requiring test coverage.",
  "remaining_issues": ""
}
```

Write this to `{entry_point_folder_path}/ui-unit-test-result.json` and stop.

---

## Phase 1: Read Tracking File and Merge Targets

**Purpose:** Read test-tracking.json for pending unit test cases and merge with modified file list.

**Steps:**

1. Read `{entry_point_folder_path}/test-tracking.json`
2. Filter `testCases` where `testType` is `unit` AND `status` is `pending`
3. Build combined target list:
   - Files from Phase 0 git diff (coverage gap targets)
   - Source files referenced by pending test cases from test-tracking.json
4. Deduplicate the merged list

---

## Phase 2: Run Existing Tests and Generate Coverage Report

**Purpose:** Establish baseline coverage for the modified files.

**Steps:**

1. Run: `cd passage-ui && npx ng test --watch=false --browsers=ChromeHeadless --code-coverage 2>&1`
2. Locate Istanbul coverage report at:
   - `passage-ui/coverage/lcov.info` (LCOV format)
   - `passage-ui/coverage/coverage-summary.json` (JSON format — preferred if available)
3. Parse coverage data for modified files

**Error handling:** If the Angular build fails (compilation error), write failure result:

```json
{
  "validated": false,
  "notes": "Build failed before coverage analysis. Fix compilation errors first.",
  "remaining_issues": "Compilation errors prevent test execution."
}
```

Write this to `{entry_point_folder_path}/ui-unit-test-result.json` and stop.

---

## Phase 3: Analyze Coverage Gaps

**Purpose:** Parse Istanbul coverage report and identify files below the 85% threshold.

**Steps:**

1. For each modified file from Phase 0:
   - Extract coverage percentage from Istanbul report (statements, branches, functions, lines)
   - If coverage >= 85% (line coverage), mark file as adequately covered
   - If coverage < 85%, add to the "needs tests" list with:
     - Current coverage percentage
     - Uncovered functions/branches
2. If all modified files are adequately covered (>= 85%) AND no pending test cases, write success result and stop

**Output:** List of files needing additional test coverage.

---

## Phase 4: Generate Unit Tests

<THINKHARD>
Think deeply about each file that needs test coverage. Analyze the component/service structure, dependencies, template bindings, and behavioral patterns before generating any test code.
</THINKHARD>

**Purpose:** Create Karma/Jasmine tests for under-covered code AND pending test cases from test-tracking.json, following the project's established patterns.

**For each file needing tests:**

### Step 1: Read and Analyze Source

Read the source file completely to understand its structure, dependencies, inputs/outputs, and template interactions.

### Step 2: Identify File Type and Test Pattern

| Source File Type | Test Pattern | Key Imports | Location |
|-----------------|-------------|-------------|----------|
| Component (`*.component.ts`) | `TestBed.configureTestingModule` | `ComponentFixture`, mock services | Adjacent `.spec.ts` |
| Service (`*.service.ts`) | `TestBed.configureTestingModule` | `HttpClientTestingModule` (if HTTP) | Adjacent `.spec.ts` |
| Pipe (`*.pipe.ts`) | Direct instantiation | None (usually pure) | Adjacent `.spec.ts` |
| Guard/Resolver | `TestBed.configureTestingModule` | `RouterTestingModule` | Adjacent `.spec.ts` |

### Step 3: Check for Existing Tests

If a `.spec.ts` file already exists:
- Read the existing test file
- Identify which behaviors are already tested
- Only generate tests for uncovered behaviors
- Add new `it` blocks to the existing `describe` (do NOT create a duplicate file)

### Step 4: Generate Test Methods

For each uncovered behavior and pending test case:
- Follow the Arrange/Act/Assert pattern
- Mock services with `jasmine.createSpyObj`
- Use `fakeAsync`/`tick` for async operations
- Use `NO_ERRORS_SCHEMA` for child component isolation
- **Include TC-ID in `it` block descriptions**: `it('should {behavior} (TC-{ID})', ...)`

### Component Test Template

```typescript
/**
 * Unit Tests for {ClassName}
 *
 * Test Cases Covered:
 * - TC-{ID}-001: {Test Name}
 * - TC-{ID}-002: {Test Name}
 */
import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { NO_ERRORS_SCHEMA } from '@angular/core';
// ... imports matching existing project patterns

describe('{ClassName}', () => {
  let component: {ClassName};
  let fixture: ComponentFixture<{ClassName}>;
  let mockService: jasmine.SpyObj<{ServiceName}>;

  beforeEach(async () => {
    mockService = jasmine.createSpyObj('{ServiceName}', ['method1', 'method2']);

    await TestBed.configureTestingModule({
      declarations: [{ClassName}],
      providers: [{ provide: {ServiceName}, useValue: mockService }],
      imports: [/* required modules */],
      schemas: [NO_ERRORS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent({ClassName});
    component = fixture.componentInstance;
  });

  /** TC-{ID}-001: {Test Name} */
  it('should {expected behavior} (TC-{ID}-001)', () => {
    // Arrange
    mockService.method1.and.returnValue(of(mockData));
    // Act
    fixture.detectChanges();
    // Assert
    expect(component.someProperty).toBeTruthy();
  });

  /** TC-{ID}-002: {Test Name} (async) */
  it('should {async behavior} (TC-{ID}-002)', fakeAsync(() => {
    // Arrange
    mockService.method2.and.returnValue(of(mockData));
    // Act
    component.loadData();
    tick();
    // Assert
    expect(component.data).toEqual(mockData);
  }));
});
```

### Service Test Template

```typescript
/**
 * Unit Tests for {ServiceName}
 *
 * Test Cases Covered:
 * - TC-{ID}-001: {Test Name}
 */
import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';

describe('{ServiceName}', () => {
  let service: {ServiceName};
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [HttpClientTestingModule],
      providers: [{ServiceName}]
    });
    service = TestBed.inject({ServiceName});
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  /** TC-{ID}-001: {Test Name} */
  it('should {expected behavior} (TC-{ID}-001)', () => {
    // Arrange
    const mockResponse = { /* ... */ };
    // Act
    service.getData().subscribe(result => {
      // Assert
      expect(result).toEqual(mockResponse);
    });
    const req = httpMock.expectOne('/api/endpoint');
    expect(req.request.method).toBe('GET');
    req.flush(mockResponse);
  });
});
```

### Kendo Component Mocking Patterns

When testing components that use Kendo UI:
- Import Kendo test modules where available
- Mock complex Kendo components (Grid, Dialog, etc.) if test modules aren't available
- Use `NO_ERRORS_SCHEMA` to suppress Kendo template errors in isolated tests
- Test Kendo event handlers via direct method calls on the component

---

## Phase 5: Run Tests and Fix Loop

**Purpose:** Execute generated tests and fix any failures in a loop.

**Loop structure (max 5 attempts):**

```
for attempt in 1..5:
    1. Run tests: cd passage-ui && npx ng test --watch=false --browsers=ChromeHeadless 2>&1 | tee {entry_point_folder_path}/unit-test-results-raw.txt || true
    2. The raw output file is required for AWA fix loop compatibility
    3. If all tests pass → break loop, proceed to Phase 6
    4. If tests fail:
       a. Capture the failure output
       b. Read the failing test and the source under test
       c. Analyze the failure root cause:
          - Missing module imports → add to TestBed imports
          - Mock setup incorrect → fix spy configuration
          - Async handling → wrap in fakeAsync/tick or use done callback
          - Form control names mismatch → align with template
          - Template compilation → check selector names, inputs/outputs
       d. Apply the fix (edit the test file)
       e. Continue loop
```

**Fix strategy prioritization:**
1. Fix the test (most common — generated test had wrong assumptions)
2. Only fix production code if the test reveals a genuine bug

**If max attempts exhausted and tests still fail:**
- Log which tests still fail and why
- Continue to Phase 6 with partial results

---

## Phase 6: Verify Coverage and Write Result

**Purpose:** Confirm the 85% coverage threshold is met after test generation.

**Steps:**

1. Re-run with coverage: `cd passage-ui && npx ng test --watch=false --browsers=ChromeHeadless --code-coverage 2>&1`
2. Parse Istanbul coverage report for modified files
3. Calculate final coverage percentages

**Update test-tracking.json** per common Phase 5:
- Match TC-IDs in test output to test case entries
- Update status (`passing`/`failing`), `filePath`, and `lastError` for each test case
- Update `unitSummary` counts

**Write result file** to `{entry_point_folder_path}/ui-unit-test-result.json`:

```json
{
  "validated": true|false,
  "notes": "Coverage summary — X files checked, Y tests generated, Z% average coverage achieved",
  "remaining_issues": "List of files still under threshold with details (or empty string)"
}
```

**`validated: true`** when:
- All modified files meet or exceed the 85% threshold, OR
- No modified UI files were found (nothing to do)

**`validated: false`** when:
- One or more modified files are still below 85% after max fix attempts
- Build/compilation errors prevented test execution

---

## Success Criteria

- [ ] Modified UI files correctly identified via git diff
- [ ] Pending test cases read from test-tracking.json
- [ ] Istanbul coverage report generated and parsed
- [ ] Coverage gaps identified for modified files only
- [ ] Unit tests generated following Angular/Karma/Jasmine patterns
- [ ] TC-ID included in `it` block descriptions for tracking-sourced tests
- [ ] Tests pass after generation (or after fix loop, max 5 attempts)
- [ ] Coverage threshold (85%) verified
- [ ] Result JSON written to `ui-unit-test-result.json`
- [ ] test-tracking.json updated with TC-ID results
- [ ] No existing tests broken by new test additions
- [ ] Generated tests pass formatting (via PostToolUse hook)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No modified files | Early success exit (`validated: true`) |
| Build/compilation failure | Early failure exit (`validated: false`) with message |
| Istanbul report missing | Re-run with `--code-coverage`; fail if still missing |
| Fix loop exhaustion | Report partial success with `remaining_issues` listing still-failing tests |
| Existing test failures | Note them but don't block — only newly generated tests must pass |

## Logging

- Log each phase start/end with summary
- Log file-level coverage analysis results
- Log each test generation action (created new file vs. added to existing)
- Log each fix loop attempt with the specific failure and fix applied
