# Fix Unit Test Failures

Fix failing unit tests based on error output. Applies targeted, minimal fixes to test files only — does NOT re-run tests (the workflow handles re-running via bash).

## Arguments

You will receive named arguments: $ARGUMENTS

- `entry_point_folder_path` — Path to the entry point folder (e.g., `docs/entry-points/ui-features/2087-infrastructure-company-company-contact`)
- `error_file` — Path to the file containing test failure output (e.g., `{entry_point_folder_path}/unit-test-results-raw.txt`)

## Process

### Phase 1: Read Error Output and Tracking File

1. Read the error file at `error_file` to understand all failures
2. Read `{entry_point_folder_path}/test-tracking.json` to identify which test cases are `failing`
3. If the error file is empty or no test cases are failing, report "No failures to fix" and stop

### Phase 2: Parse and Categorize Failures

For each failing test, extract:
- **Test file path** and **test name** (from the error output)
- **Error type** and **error message**
- **TC-ID** (from the test name or `@DisplayName`)

Categorize each failure:

| Category | Symptoms | Typical Fix |
|----------|----------|-------------|
| Import/Dependency | `Cannot find module`, `is not a known element`, `NoSuchBeanDefinitionException` | Fix imports, add missing module/provider declarations |
| Mock Setup | `spy ... to have been called`, `Wanted but not invoked`, `NullInjectorError` | Fix mock configuration, add missing mock methods/returns |
| Assertion | `Expected X to equal Y`, `ComparisonFailure` | Fix expected values or fix test logic to match implementation |
| Async/Timing | `Timeout`, `async function did not complete`, `Received promise rejected` | Add `fakeAsync`/`tick`, `waitForAsync`, or fix async handling |
| Type Mismatch | `TypeError`, `Cannot read property of undefined`, `ClassCastException` | Fix mock return types, null handling, or type casting |
| Test Logic | Test is fundamentally wrong (testing non-existent behavior) | Rewrite the test to correctly test the implementation |

### Phase 3: Read Context

For each failing test file:

1. **Read the test file** to understand what it tests and how
2. **Read the implementation file** being tested to understand actual behavior
3. **Read the functional spec** (from `functionalSpecPath` in test-tracking.json) if the expected behavior is unclear

### Phase 4: Apply Fixes

Fix each failing test file. Apply the **minimum change** needed to make the test correct.

**Fix priority** (try in order):
1. **Fix imports** — missing modules, incorrect paths
2. **Fix mock setup** — missing return values, wrong spy configuration
3. **Fix assertions** — expected values that don't match actual implementation
4. **Fix async handling** — missing fakeAsync, tick, or waitForAsync wrappers
5. **Rewrite test** — only if the test is fundamentally wrong (testing behavior that doesn't exist)

**Rules**:
- **Preserve passing tests** — only modify tests that are actually failing
- **Do NOT modify implementation code** — only fix test files
- **Do NOT weaken assertions** to make tests pass (e.g., removing checks, loosening matchers)
- **Do NOT add `skip`/`xit`/`xdescribe`/`@Disabled`** to bypass failures
- **Keep TC-ID references** intact in test names and documentation
- If a test needs to be rewritten, keep the same TC-ID and test intent

### Phase 5: Update test-tracking.json

After fixing all test files, update `{entry_point_folder_path}/test-tracking.json`:

1. For each test case that was fixed: clear `lastError` (set to `null`), keep `status` as `failing` (the workflow will re-run and update status)
2. Increment `attempts` by 1 for each fixed test case
3. Write the updated JSON back

**IMPORTANT**: Do NOT change `status` to `passing` — only the actual test run (handled by the workflow) determines pass/fail status.

## Common Fix Patterns

### Angular / Karma / Jasmine (UI Features)

**Missing module in TestBed**:
```typescript
// Before (fails with "'app-child' is not a known element")
TestBed.configureTestingModule({ declarations: [ParentComponent] });
// After
TestBed.configureTestingModule({
  declarations: [ParentComponent],
  schemas: [NO_ERRORS_SCHEMA] // or import the child module
});
```

**Mock not returning value**:
```typescript
// Before (fails with "Cannot read property 'subscribe' of undefined")
const mockService = jasmine.createSpyObj('Svc', ['getData']);
// After
const mockService = jasmine.createSpyObj('Svc', ['getData']);
mockService.getData.and.returnValue(of(mockData));
```

**Async test missing fakeAsync**:
```typescript
// Before (fails with timeout)
it('should load data', () => { ... });
// After
it('should load data', fakeAsync(() => {
  // ... test code
  tick();
  // ... assertions
}));
```

**Wrong form control name**:
```typescript
// Before (fails with "Cannot find control with name: 'companyName'")
expect(component.form.get('companyName')).toBeTruthy();
// After — check the actual FormGroup definition
expect(component.form.get('company_name')).toBeTruthy();
```

### JUnit 5 / Mockito (API Endpoints)

**Missing mock setup**:
```java
// Before (fails with NullPointerException)
var result = underTest.findById(1L);
// After
when(mockRepository.findById(1L)).thenReturn(Optional.of(entity));
var result = underTest.findById(1L);
```

**Wrong assertion on DTO field**:
```java
// Before (fails with "expected: <CompanyName> but was: <Company Name>")
assertEquals("CompanyName", result.getName());
// After — match actual implementation mapping
assertEquals("Company Name", result.getName());
```

**Missing @ExtendWith**:
```java
// Before (fails with "Cannot invoke ... because mock is null")
class ServiceTest { @Mock Repository repo; ... }
// After
@ExtendWith(MockitoExtension.class)
class ServiceTest { @Mock Repository repo; ... }
```

**Exception not thrown as expected**:
```java
// Before (fails with "Expected IllegalArgumentException to be thrown")
assertThrows(IllegalArgumentException.class, () -> underTest.create(null));
// After — check what exception the implementation actually throws
assertThrows(NullPointerException.class, () -> underTest.create(null));
```

## Output Constraints

After fixing test files, update test-tracking.json and respond with ONLY a brief summary:
- Number of test files modified
- For each fix: test name, error category, what was changed
- Any tests that could not be fixed (with reason)

Do NOT re-run tests — the workflow handles that. Do NOT echo full file contents.
