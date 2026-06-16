Analyze API E2E test failures and apply targeted, minimal fixes using task-list-driven parallel sub-agent orchestration with upfront API source inspection.

## Arguments

You will receive named arguments: $ARGUMENTS

- `error_file` — Path to API E2E test results JSON (output from `/run-api-e2e-tests`)
- `feature_name` — Feature name (matches test directory/class under `apitests/`)
- `entry_point_folder_path` — Path to the entry point folder for implementation context

## Pre-Flight Validation

Before processing any failures, verify tests are in the correct location:

```bash
# Tests MUST be Java files in passage-api — NOT TypeScript in passage-ui
find passage-api/src/test/apirequestcontext -name "*ApiTest.java" | head -10
```

If no `.java` test files exist in `passage-api/src/test/apirequestcontext/`, the tests were generated in the wrong location. Report this as a generation error — do NOT attempt to fix TypeScript files in `passage-ui/`.

## Architecture

You are the **orchestrator**. You do NOT fix code yourself — you delegate ALL fixing to sub-agents and focus on task management. The workflow is:

1. Parse failures → create task list (you do this)
2. API source inspection → delegate to one sub-agent, read only the summary
3. Launch 2 parallel fix sub-agents at a time (each fixes AND runs its own test class)
4. Monitor results, commit successes, retry failures
5. Final regression check + summary

## Instructions

### Phase 1: Parse Failures and Create Task List

Read the JSON from `error_file`. Extract the `failureDetails` array — each entry has format `ClassName.methodName - error message`.

Group failures by test class. Create one task per failure group:

```
TaskCreate:
  subject: "Fix {ClassName} failures ({N} tests)"
  description: |
    Failing tests:
    - {methodName1}: {error message}
    - {methodName2}: {error message}
    Likely category: {http-status|payload|auth|schema|data-dependency}
  activeForm: "Fixing {ClassName} failures"
```

Create a final task blocked by all fix tasks:
```
TaskCreate:
  subject: "Run full API regression suite"
  description: "Run all API tests as final regression gate"
  activeForm: "Running final API regression suite"
  addBlockedBy: [all fix task IDs]
```

### Phase 2: API Source Inspection (Delegated to Sub-Agent)

Spawn a single sub-agent (via Task tool) with this prompt:

> You are an API Source Inspector. Your job is to analyze the API source code relevant to the failing tests.
>
> 1. Read the controller files for the endpoints under test:
>    - Look in `passage-api/src/main/java/com/williams/passage/` for controllers
>    - Extract: endpoint paths, HTTP methods, request/response DTOs
>
> 2. Read the relevant service and entity files:
>    - Extract: field names, validation rules, required fields
>
> 3. Read the test infrastructure:
>    - `passage-api/src/test/apirequestcontext/java/com/williams/api/` for base test classes
>    - Extract: auth setup, base URL config, common utilities
>
> 4. Write a clean, structured analysis to `/tmp/api-source-analysis.md`:
>    - Table mapping endpoint path → HTTP method → request DTO → response DTO
>    - Required fields and validation rules per endpoint
>    - Auth configuration (headers, tokens)
>    - Test data setup patterns
>    - Any field name mismatches between DTOs and test fixtures

Wait for this sub-agent to finish. Read ONLY `/tmp/api-source-analysis.md` — do NOT read raw source code.

### Phase 3: Parallel Fix Execution (2 Sub-Agents at a Time)

Pick the first 2 pending fix tasks from the task list. For each, launch a sub-agent (via Task tool) with this prompt:

> You are an API Fix Agent. Fix the failures in `{ClassName}` and verify them.
>
> **Context:**
> - Feature: {feature_name}
> - Failing tests: {list from task description}
> - API analysis: Read `/tmp/api-source-analysis.md` for endpoint details
>
> **Steps:**
> 1. Read `/tmp/api-source-analysis.md` for endpoint paths, schemas, auth config
> 2. Read the failing test class: `passage-api/src/test/apirequestcontext/java/com/williams/api/apitests/{ClassName}.java`
> 3. Read its fixture/payload class under `apifixtures/`
> 4. Read test data YAML under `resources/testdata/api/`
> 5. Apply minimal fixes:
>    - Fix request payloads (missing fields, wrong types, invalid values)
>    - Fix response assertions to match actual API response structure
>    - Fix auth setup if tests get 401
>    - Fix test data if 404 on expected resources
>    - Do NOT modify API source code to make tests pass
>    - Do NOT rewrite large sections or change test structure
>    - Prefer fixing fixtures/payloads over test logic
> 6. Run ONLY this test class:
>    ```bash
>    cd passage-api && ./gradlew apiE2eTest --tests "com.williams.api.apitests.{ClassName}" --rerun --info 2>&1 | tee /tmp/api-fix-{ClassName}.txt
>    ```
> 7. Report results: which tests now pass, which still fail, files changed

**Launch 2 sub-agents in parallel** in a single Task tool message. Wait for both to return.

**Evaluate results for each:**
- Tests improved + no regressions → commit fix, mark task completed:
  ```
  fix(e2e): resolve API E2E test failure in {feature_name}

  - Fixed: {brief description}
  - Category: {http-status|payload|auth|schema|data-dependency}
  - Tests: {X} now passing (was {Y})
  ```
- No improvement → mark task as needs-retry (max 3 retries per task)
- After 3 failed retries → mark task completed with note "unfixable"

**Repeat**: Pick next 2 pending tasks, launch 2 more sub-agents. Continue until all fix tasks are done.

### Phase 4: Final Regression Check + Summary

Once all fix tasks are complete:

1. Run the **full API test suite ONCE**:
   ```bash
   cd passage-api && ./gradlew apiE2eTest --rerun --info 2>&1 | tee /tmp/api-final.txt
   ```

2. If any test that was passing before now fails (regression), revert the offending commit:
   ```bash
   git revert --no-edit {commit-sha}
   ```

3. Write summary to `passage-api/api-e2e-fix-summary.md`:

   | Metric | Count |
   |--------|-------|
   | Total failures | {N} |
   | Fixed | {N} |
   | Remaining | {N} |
   | Regressions | {N} |

   For each fix: test name, root cause, category, what changed.
   For remaining failures: why they couldn't be fixed.

4. Commit the summary.

## Common Root Causes

### HTTP Status Mismatch
```
Expected status 201 but got 400
```
**Fix**: Check request payload — missing required fields, wrong data types, or invalid values.

### Payload Mismatch
```
Expected response to contain "companyName" but field was missing
```
**Fix**: Update response assertions to match actual API response structure.

### Auth Issues
```
Expected status 200 but got 401
```
**Fix**: Verify test setup includes proper auth headers. Check BaseApiTest auth configuration.

### Data Dependencies
```
Expected to find company with ID 1001 but got 404
```
**Fix**: Ensure test data YAML has the required seed data, or adjust test to use data that exists.

### Wrong Test Location
```
Tests generated as TypeScript in passage-ui/ instead of Java in passage-api/
```
**Fix**: This is a generation error. Report it — the `/create-api-automated-tests` command needs to be re-run.
