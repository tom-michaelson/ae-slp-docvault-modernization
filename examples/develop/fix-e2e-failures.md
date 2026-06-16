Analyze Playwright E2E test failures and apply targeted, minimal fixes using task-list-driven parallel sub-agent orchestration with upfront DOM inspection.

## Arguments

You will receive named arguments: $ARGUMENTS

- `error_file` — Path to E2E test results JSON (output from `/run-e2e-tests`)
- `feature_name` — Feature name (matches test directory under `e2e/tests/features/`)
- `entry_point_folder_path` — Path to the entry point folder for implementation context

## Architecture

You are the **orchestrator**. You do NOT fix code yourself — you delegate ALL fixing to sub-agents and focus on task management. The workflow is:

1. Parse failures → create task list (you do this)
2. DOM inspection → delegate to one sub-agent, read only the summary
3. Launch 2 parallel fix sub-agents at a time (each fixes AND runs its own spec)
4. Monitor results, commit successes, retry failures
5. Final regression check + summary

## Instructions

### Phase 1: Parse Failures and Create Task List

Read the JSON from `error_file`. Extract the `failureDetails` array — each entry has format `file:line - error message`.

Group failures by spec file name. Create one task per failure group:

```
TaskCreate:
  subject: "Fix {spec-file} failures ({N} tests)"
  description: |
    Failing tests:
    - {test name 1}: {error message}
    - {test name 2}: {error message}
    Likely category: {selector|timing|assertion|navigation}
  activeForm: "Fixing {spec-file} failures"
```

Create a final task blocked by all fix tasks:
```
TaskCreate:
  subject: "Run full regression suite"
  description: "Run all feature tests as final regression gate"
  activeForm: "Running final regression suite"
  addBlockedBy: [all fix task IDs]
```

### Phase 2: DOM Inspection (Delegated to Sub-Agent)

Spawn a single sub-agent (via Task tool) with this prompt:

> You are a DOM Inspector. Your job is to capture and analyze the live DOM for E2E test debugging.
>
> 1. Navigate to the feature page using Playwright:
>    ```bash
>    cd passage-ui && node -e "
>    const { chromium } = require('playwright');
>    (async () => {
>      const browser = await chromium.launch();
>      const page = await browser.newPage();
>      await page.goto('http://localhost:4200/{route}');
>      await page.waitForLoadState('networkidle');
>      await page.waitForTimeout(2000);
>      const html = await page.content();
>      require('fs').writeFileSync('/tmp/e2e-debug-dom.html', html);
>      await browser.close();
>    })();
>    "
>    ```
>    (Determine the route from the feature's Angular routing config or test files)
>
> 2. Extract all data-testid values:
>    ```bash
>    grep -oP 'data-testid="[^"]*"' /tmp/e2e-debug-dom.html | sort -u > /tmp/e2e-selectors.txt
>    ```
>
> 3. Read relevant Angular component `.ts` files for `dataTestId` configs
>
> 4. Write a clean, structured analysis to `/tmp/e2e-dom-analysis.md`:
>    - Table mapping component → actual `data-testid` value
>    - Kendo component structure notes (e.g., menu items use `role="menuitem"`)
>    - Grid class names, dialog selectors, and other DOM patterns
>    - List of ALL selectors found in `/tmp/e2e-selectors.txt`

Wait for this sub-agent to finish. Read ONLY `/tmp/e2e-dom-analysis.md` — do NOT read the raw HTML.

### Phase 3: Parallel Fix Execution (2 Sub-Agents at a Time)

Pick the first 2 pending fix tasks from the task list. For each, launch a sub-agent (via Task tool) with this prompt:

> You are an E2E Fix Agent. Fix the failures in `{spec-file}` and verify them.
>
> **Context:**
> - Feature: {feature_name}
> - Failing tests: {list from task description}
> - DOM analysis: Read `/tmp/e2e-dom-analysis.md` for correct selectors
>
> **Steps:**
> 1. Read `/tmp/e2e-dom-analysis.md` for the actual DOM selectors
> 2. Read the failing spec file: `passage-ui/e2e/tests/features/{feature_name}/{spec-file}.spec.ts`
> 3. Read its page object (find via imports in the spec file)
> 4. Apply minimal fixes:
>    - Use `[data-testid="value"]` — NOT `[data-test-id="value"]` (the correct attribute has no extra hyphen)
>    - Match selectors to actual DOM values from the analysis
>    - Use smart waits: `waitForSelector`, `waitForLoadState`, `waitForResponse`
>    - NEVER use `waitForTimeout()` — always use smart waits
>    - Prefer fixing page objects over spec files
>    - Do NOT rewrite large sections or change test structure
> 5. Run ONLY this spec file:
>    ```bash
>    cd passage-ui && npx playwright test --config=e2e/playwright.config.ts --project=chromium e2e/tests/features/{feature_name}/{spec-file}.spec.ts 2>&1 | tee /tmp/e2e-fix-{spec-file}.txt
>    ```
> 6. Report results: which tests now pass, which still fail, files changed

**Launch 2 sub-agents in parallel** in a single Task tool message. Wait for both to return.

**Evaluate results for each:**
- Tests improved + no regressions → commit fix, mark task completed:
  ```
  fix(e2e): resolve E2E test failure in {feature_name}

  - Fixed: {brief description}
  - Category: {selector|timing|assertion|navigation}
  - Tests: {X} now passing (was {Y})
  ```
- No improvement → mark task as needs-retry (max 3 retries per task)
- After 3 failed retries → mark task completed with note "unfixable"

**Repeat**: Pick next 2 pending tasks, launch 2 more sub-agents. Continue until all fix tasks are done.

### Phase 4: Final Regression Check + Summary

Once all fix tasks are complete:

1. Run the **full feature test suite ONCE**:
   ```bash
   cd passage-ui && npx playwright test --config=e2e/playwright.config.ts --project=chromium e2e/tests/features/{feature_name}/ 2>&1 | tee /tmp/e2e-final.txt
   ```

2. If any test that was passing before now fails (regression), revert the offending commit:
   ```bash
   git revert --no-edit {commit-sha}
   ```

3. Write summary to `passage-ui/e2e/e2e-fix-summary.md`:

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

### Selector Issues (Most Common)
The Angular app uses `[attr.data-testid]` which renders as `data-testid` in the DOM. Tests using `data-test-id` (with an extra hyphen) will ALWAYS fail.

**Fix**: Use `[data-testid="..."]` selectors in page objects — this is the correct attribute rendered by the Angular components.

### Timing Issues
```
Timeout 15000ms exceeded waiting for selector
```
**Fix**: Add `waitForSelector` with correct state, or `waitForLoadState('networkidle')` before interactions.

### Kendo Grid Issues
```
Expected grid to have N rows but found 0
```
**Fix**: Wait for grid data: `waitForSelector('kendo-grid .k-grid-content tr')`.

### Navigation Issues
```
page.goto: net::ERR_CONNECTION_REFUSED
```
**Fix**: Infrastructure issue — report, don't fix.
