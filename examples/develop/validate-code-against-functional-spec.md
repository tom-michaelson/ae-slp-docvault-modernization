---
model: opus
---

<THINKHARD>
Think deeply and thoroughly about each acceptance criterion. For each AC, carefully analyze the code
to determine whether it truly implements the expected behavior. Do not assume — look for concrete evidence.
</THINKHARD>

# Validate Code Against Functional Spec

Systematically validate that implemented code covers all acceptance criteria (Gherkin scenarios) and business rules defined in the functional specification. This is a **static code analysis** command — it reads code, it does NOT execute tests, build, or run the application.

## Usage

```
/validate-code-against-functional-spec entry_point_folder_path: [path]
```

**Examples:**
```
/validate-code-against-functional-spec entry_point_folder_path: docs/entry-points/api-endpoints/1075-spring-filterservice-load
```

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `entry_point_folder_path` | Yes | Path to the entry point directory containing `functional-spec.md` |
| `previous_ac_result` | No | Path to a previous `ac-validation-result.json` from a prior validation attempt. When provided, only FAIL and PARTIAL criteria are re-validated; PASS, UNABLE TO VERIFY, and DEFERRED ratings are carried forward. |

## Output

Writes `{entry_point_folder_path}/ac-validation-result.json` matching the `ImplementationReview` schema:

```json
{
  "validated": true | false,
  "notes": "Summary of validation results — counts of ACs and BRs checked, pass/fail breakdown.",
  "remaining_issues": "Detailed list of FAIL and PARTIAL items with specific file paths and expected behavior."
}
```

- **`validated: true`** — All ACs and BRs are PASS, UNABLE TO VERIFY, or DEFERRED (no FAILs or PARTIALs)
- **`validated: false`** — At least one AC or BR is FAIL or PARTIAL

The output file is named `ac-validation-result.json` (distinct from `implementation-review-result.json`) so both results can coexist in the entry point directory.

---

## Validation Process

### Phase 0: Read Inputs

1. **Read the functional spec**: `{entry_point_folder_path}/functional-spec.md` — the source of acceptance criteria
2. **Read the implemented code** by scanning the git diff between current branch and main:
   ```
   git diff main...HEAD -- .
   ```
3. If the git diff is empty or not meaningful, **fall back** to reading source files referenced in the entry point directory:
   - Read `{entry_point_folder_path}/implementation-plan.md` for context on what files were planned
   - Read `{entry_point_folder_path}/task-list.md` for file paths
   - Use Glob/Grep to locate the implemented files
4. Read `{entry_point_folder_path}/implementation-plan.md` for additional context on planned structure
5. **If `previous_ac_result` is provided**, read the previous validation result JSON file:
   - Parse `remaining_issues` to identify which **AC-N** and **BR-N** were rated FAIL or PARTIAL — these are the **only criteria that need re-validation**
   - All criteria NOT listed in `remaining_issues` were previously PASS, UNABLE TO VERIFY, or DEFERRED — **carry those ratings forward** without re-analyzing the code
   - This significantly reduces validation time on retry attempts

### Phase 1: Extract Acceptance Criteria

Parse `functional-spec.md` to extract all testable criteria:

1. **Gherkin Scenarios**: All `Scenario` and `Scenario Outline` blocks with their `Given`/`When`/`Then` steps
2. **Background sections**: Any `Background` that applies globally to scenarios
3. **Business Rules**: All numbered `BR-N` rules with descriptions
4. **Feature context**: The `Feature` name and `As a / I want / So that` description

Create a numbered checklist:
```
ACCEPTANCE CRITERIA:
AC-1: [Scenario name] — [brief summary from Given/When/Then]
AC-2: [Scenario name] — [brief summary]
...

BUSINESS RULES:
BR-1: [Rule name] — [description]
BR-2: [Rule name] — [description]
...

Total: {n} ACs + {m} BRs = {n+m} criteria to validate
```

### Phase 2: Systematic Per-AC Validation

**Incremental mode** (when `previous_ac_result` is provided): For each AC-N that was previously rated **PASS**, **UNABLE TO VERIFY**, or **DEFERRED**, carry that rating and its notes forward directly — do NOT re-analyze the code for these. Only re-validate ACs that were previously rated **FAIL** or **PARTIAL**.

For **each** acceptance criterion (AC-N) that needs validation:

1. **Identify the expected behavior** from the Given/When/Then steps:
   - **Given** → What preconditions/setup must exist
   - **When** → What action triggers the behavior
   - **Then** → What observable outcome is expected

2. **Search the code** for evidence of implementation:
   - Map **Given** preconditions to setup/validation logic, test fixtures, or configuration
   - Map **When** actions to controller endpoints, service methods, event handlers, or UI interactions
   - Map **Then** outcomes to response structures, state changes, error handling, or assertions

3. **Rate the AC** as one of:

   | Rating | Meaning | When to use |
   |--------|---------|-------------|
   | **PASS** | Clear evidence the code implements this AC | You can point to specific code that handles the Given/When/Then |
   | **PARTIAL** | Some aspects implemented but others missing | Part of the scenario is covered but a specific step is missing |
   | **FAIL** | No evidence of implementation found | Cannot find code that addresses this scenario |
   | **UNABLE TO VERIFY** | AC is ambiguous or requires runtime verification | Static analysis cannot determine compliance (e.g., timing, concurrency, external system behavior) |
   | **DEFERRED** | Functionality is intentionally deferred or stubbed | Code contains a stub, TODO, hardcoded placeholder, or documented deferral (e.g., auth stubs, feature flags for future phases) |

4. For **PARTIAL** and **FAIL** ratings, document:
   - **Specifically what is missing** (which Given/When/Then step)
   - **File path** where the code should exist
   - **Expected behavior** that is not implemented

### Phase 3: Business Rules Validation

**Incremental mode** (when `previous_ac_result` is provided): Carry forward BRs previously rated **PASS**, **UNABLE TO VERIFY**, or **DEFERRED**. Only re-validate BRs that were previously **FAIL** or **PARTIAL**.

For **each** business rule (BR-N) that needs validation:

1. **Locate the code** that implements the rule
2. **Verify the rule logic** matches the specification exactly
3. **Rate as** PASS / PARTIAL / FAIL / UNABLE TO VERIFY / DEFERRED
4. **Document discrepancies** — what the spec says vs. what the code does

### Authorization Rule Validation

When the functional spec has authorization BRs (e.g., "CHANGE permission required"):
- [ ] Accept `@SecuredByMenuItem` on controller as valid implementation
- [ ] Accept "no security needed" if legacy didn't enforce API-level checks (with documented justification)
- [ ] Do NOT require `hasPermission()` in service code to satisfy authorization BRs
- [ ] Do NOT flag missing `hasPermission()` as a gap — this is the old (incorrect) pattern
- Reference: `docs/target-architecture/security-architecture.md`

### Phase 4: Generate Validation Result

1. **Aggregate results**:
   ```
   PASS:               {count}
   PARTIAL:            {count}
   FAIL:               {count}
   UNABLE TO VERIFY:   {count}
   DEFERRED:           {count}
   Total:              {count}
   ```

2. **Determine `validated` status**:
   - `true` — ALL ACs and BRs are **PASS**, **UNABLE TO VERIFY**, or **DEFERRED** (zero FAILs and zero PARTIALs)
   - `false` — ANY AC or BR is **FAIL** or **PARTIAL**

3. **Generate `remaining_issues`** with specific, actionable details for each FAIL or PARTIAL AC/BR (do NOT include DEFERRED items in remaining_issues):

   ```
   ACCEPTANCE CRITERIA GAPS:

   1. AC-{n}: {FAIL|PARTIAL} - Scenario: {scenario name}
      Expected: {description from Given/When/Then}
      Found: {what the code actually does, or "No implementation found"}
      File: {file path where code should exist}

   2. AC-{m}: {FAIL|PARTIAL} - ...

   BUSINESS RULE GAPS:

   1. BR-{n}: {FAIL|PARTIAL} - Rule: {rule description}
      Expected: {what the spec requires}
      Found: {what the code does}
      File: {file path}
   ```

4. **Write** `{entry_point_folder_path}/ac-validation-result.json`:

   ```json
   {
     "validated": false,
     "notes": "Validated 15 acceptance criteria and 8 business rules. 13/15 ACs pass, 7/8 BRs pass. 2 ACs and 1 BR need attention.",
     "remaining_issues": "ACCEPTANCE CRITERIA GAPS:\n\n1. AC-7: FAIL - Scenario: User submits empty company name\n   Expected: Validation error with message 'Company name is required'\n   Found: No validation logic in CompanyService.create() for empty name\n   File: passage-api/src/.../service/CompanyService.java\n\nBUSINESS RULE GAPS:\n\n1. BR-5: FAIL - Rule: Effective date must be normalized to start of day\n   Found: No date normalization in CompanyMapper\n   File: passage-api/src/.../dto/CompanyMapper.java"
   }
   ```

---

## Key Principles

### Err on the Side of Flagging

For ambiguous ACs where static analysis cannot definitively confirm implementation, rate as **UNABLE TO VERIFY** rather than false-passing. Only rate as **PASS** when there is clear code evidence.

### Static Analysis Only

This command reads code. It does **NOT**:
- Execute tests
- Run the build
- Start the application
- Measure code coverage

This aligns with the constraint that tests may or may not exist at this point.

### Focus on Code, Not Tests

Validate that the **production code** implements the AC, not that **tests** cover the AC. Test coverage is a separate concern.

### Be Specific in Failure Reports

When rating FAIL or PARTIAL:
- Cite the specific file path
- Reference the specific AC/BR number
- Describe exactly what is missing
- Describe what should be there instead

This specificity enables the fix loop to address issues precisely.

---

## Success Criteria

- [ ] `functional-spec.md` read and all ACs/BRs extracted
- [ ] Every AC systematically validated against the code
- [ ] Every BR systematically validated against the code
- [ ] Each criterion rated as PASS/PARTIAL/FAIL/UNABLE TO VERIFY/DEFERRED
- [ ] Non-passing criteria have specific, actionable details
- [ ] `ac-validation-result.json` written with correct schema
- [ ] `validated` status correctly reflects aggregate results
