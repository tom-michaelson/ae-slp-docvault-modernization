---
model: opus
---

# Fix Test Failures

Fix failing tests in passage-api and/or passage-ui. Make minimal, targeted changes only.

## Usage

```
/fix-test-failures error_files: [file paths] task_list: [path] technical_plan: [path]
```

## Input

- `error_files`: Comma-separated file paths containing test failures (e.g., `docs/e2e-testing/results/{page_id}/api-test-failures.txt`, `docs/e2e-testing/results/{page_id}/ui-test-failures.txt`)
- `task_list`: Path to task list for implementation context
- `technical_plan`: Path to technical plan for expected behavior reference

**First step**: Read the error file(s) to understand what tests are failing. Empty files indicate no test failures for that project.

## Critical Guidelines

**DO:**
- Read the specific test file(s) that failed
- Read the implementation file(s) being tested
- Identify the root cause (usually implementation bug, not test bug)
- Make the minimal fix to pass the test
- Commit each fix with a descriptive message

**DO NOT:**
- Rewrite large sections of code
- Change test expectations unless the test is clearly wrong
- Add new features or refactor
- Make speculative changes
- Touch files unrelated to the failure
- "Fix" tests by making them less strict

## Process

### 1. Read Error Files

Read each error file provided in `error_files`. Skip any empty files (they indicate that project's tests passed).

### 2. Parse Failures

For each non-empty error file, identify:
- Which project has failures (`passage-api`, `passage-ui`, or both)
- Which test file(s) failed
- Which test case(s) failed (look for `describe` and `it` block names)
- The assertion/error message:
  - `Expected X but received Y`
  - `TypeError: Cannot read property...`
  - `toEqual`, `toBe`, `toHaveBeenCalled` failures

### 3. Analyze Each Failure

For each failing test:

1. **Read the test file** to understand:
   - What is being tested?
   - What is the expected behavior?
   - What inputs are being used?

2. **Read the implementation** being tested to understand:
   - What is the actual behavior?
   - Where is the discrepancy?

3. **Consult the technical plan** if needed:
   - What was the intended behavior?
   - Is the test correct or is the implementation wrong?

### 4. Determine Root Cause

The issue is usually one of:

| Symptom | Likely Cause | Fix Location |
|---------|--------------|--------------|
| Wrong return value | Implementation logic error | Implementation |
| Missing function call | Implementation missing step | Implementation |
| Type mismatch | Implementation returns wrong type | Implementation |
| Test expects old behavior | Implementation changed correctly | Test (rare) |
| Mock not set up correctly | Test setup issue | Test |

**Default assumption**: The implementation is wrong, not the test.

### 5. Apply Minimal Fix

For implementation fixes:
- Fix only the specific logic causing the failure
- Do not refactor surrounding code
- Do not add unrelated improvements

For test fixes (only if test is clearly wrong):
- Fix incorrect expectations
- Fix incorrect mock setup
- Do NOT weaken assertions just to pass

### 6. Commit

Commit with a message describing what was fixed:

```
fix: resolve test failures in [project]

- Fixed [brief description of what was wrong]
- Test: [name of test that now passes]
```

## Common Failure Patterns

### Angular / Karma / Jasmine (passage-ui)

#### Jasmine Assertion Failures

```
Expected 'actual value' to equal 'expected value'.
Expected undefined to be defined.
Expected spy someMethod to have been called.
```
**Fix**: Check component logic, ensure correct values are being set.

#### Component Not Rendering

```
'app-some-component' is not a known element
```
**Fix**: Add component to test module declarations or import the module.

#### Service Injection Failures

```
NullInjectorError: No provider for SomeService!
```
**Fix**: Add service to test module providers or provide a mock.

#### Async Test Failures

```
Error: Timeout - Async function did not complete within 5000ms
```
**Fix**: Ensure async operations complete, use `fakeAsync`/`tick` or `waitForAsync`.

#### Karma-Specific Output

```
Chrome Headless 120.0.6099.129: Executed 45 of 50 (5 FAILED)
```
Look for the specific `✗` or `FAILED` markers above this summary.

### Spring Boot / JUnit / Maven (passage-api)

#### JUnit Assertion Failures

```
org.junit.ComparisonFailure: expected:<[expected]> but was:<[actual]>
java.lang.AssertionError: Expected X but got Y
```
**Fix**: Implementation returns wrong value, check business logic.

#### Mock Not Called (Mockito)

```
Wanted but not invoked: someRepository.save()
Actually, there were zero interactions with this mock.
```
**Fix**: Implementation is not calling the repository/service as expected.

#### Spring Context Failures

```
Failed to load ApplicationContext
Caused by: NoSuchBeanDefinitionException
```
**Fix**: Missing bean configuration, check @Component/@Service annotations.

#### NullPointerException in Tests

```
java.lang.NullPointerException: Cannot invoke method on null
    at com.example.SomeService.doSomething(SomeService.java:45)
```
**Fix**: Implementation not handling null case, or test setup missing mock.

#### Maven Surefire Output

```
Tests run: 10, Failures: 2, Errors: 1, Skipped: 0
<<< FAILURE! - in com.example.SomeServiceTest
```
Look for the specific test method name and stack trace above this summary.

### General Patterns

#### Assertion Failures

```
Expected: { id: 1, name: "Test" }
Received: { id: 1, name: undefined }
```
**Fix**: Implementation is not setting `name` property correctly.

#### Mock Not Called

```
Expected mock function to have been called with [args]
But it was not called
```
**Fix**: Implementation is not calling the expected dependency.

#### Type Errors in Tests

```
TypeError: Cannot read property 'map' of undefined
```
**Fix**: Implementation is returning undefined instead of an array.

#### Async Timing Issues

```
Received promise rejected instead of resolved
```
**Fix**: Implementation has async error or returns rejected promise.

## Output

After fixing, describe:
1. Which project(s) had failures
2. Which test(s) were failing
3. What the root cause was
4. What changes were made

Example:
```
Fixed test failures in passage-api:
- Test: CompanyService.findById should return company data
- Root cause: Repository was not being called with correct ID parameter
- Fix: Changed repository.findOne({ id }) to repository.findOne({ where: { id } })

Fixed test failures in passage-ui:
- Test: CompanyList should render company names
- Root cause: Component was accessing data.companies instead of data.items
- Fix: Updated property access to match API response structure
```
