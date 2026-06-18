# Validate Call Tree Command

You are tasked with validating an extracted call tree for a single entry point by verifying it against the actual source code. ULTRATHINK

## Input Parameters

You will receive two pieces of information:

1. **Entry Point Payload** - A JSON object describing the entry point:
   ```json
   {
     "key": "01-some-entry-point",
     "location": "path/to/file.ext, ClassName.method_name() or function_name()",
     "type": "entry-point-type-slug"
   }
   ```

2. **Type** - The entry point type (e.g., "api-endpoints", "job-handlers", etc.)

## Task Overview

Validate the accuracy of an already-extracted call tree by verifying each branch against the actual source code using parallel call-tree-validator subagents.

**Prerequisites**: The `/extract-call-tree` command must have been run first to create:
- `./docs/entry-points/<type>/<key>/call-tree.txt`
- `./docs/entry-points/<type>/<key>/functions-to-extract.txt`
- `./docs/entry-points/<type>/<key>/code/` (extracted function bodies)

**Goal**: Ensure the call tree is complete, accurate, and reflects the actual code execution paths.

## Execution Steps

### Step 1: Parse Input

Extract the following from the entry point payload:
- `key` - Unique identifier for the entry point
- `location` - Location description (file path and function/method name)
- `type` - Entry point type slug

### Step 2: Determine Project Root

Based on the file path in the `location` field, determine which project root to use:

- If path contains `northwest-passage` → use `./legacy/northwest-passage`
- If path contains `portal` → use `./legacy/portal`
- If path contains `database` → use `./legacy/database`

**Default**: If unclear, use `./legacy/northwest-passage`

### Step 3: Validate Call Tree

#### 3.1: Parse Call Tree Structure

Read and analyze the `./docs/entry-points/<type>/<key>/call-tree.txt` file to identify validation units.

**Identify Major Branches:**
- Parse the tree structure to identify the entry point's direct children (first-level branches)
- Each first-level branch represents a logical sub-tree that can be validated independently
- Group related branches if they form cohesive validation units

**Example Analysis:**
```
invoke() - passage-java/src/rest/TariffRatesServiceRS.java:45
├── processRequest() - passage-java/src/services/TariffService.java:120  [Branch 1]
│   ├── validateInput() - passage-java/src/services/TariffService.java:145
│   ├── getTariffRates() - passage-java/src/dao/TariffDAO.java:67
│   │   └── sp_get_tariff_rates() - database/procedures/tariff_mgmt.sql:234
│   └── formatResponse() - passage-java/src/util/ResponseFormatter.java:89
└── logRequest() - passage-java/src/util/AuditLogger.java:34              [Branch 2]
    └── writeAuditLog() - passage-java/src/dao/AuditDAO.java:56
```

In this example, we have 2 major branches to validate in parallel:
1. The `processRequest()` branch with its entire sub-tree
2. The `logRequest()` branch with its sub-tree

#### 3.2: Extract Branch Sub-Trees

For each major branch identified, extract its complete sub-tree into a separate validation unit.

**Create Working Files:**

For each branch, create a temporary sub-tree file:
```
./docs/entry-points/<type>/<key>/validation/branch-<n>.txt
```

**Example - Branch 1:**
```
processRequest() - passage-java/src/services/TariffService.java:120
├── validateInput() - passage-java/src/services/TariffService.java:145
├── getTariffRates() - passage-java/src/dao/TariffDAO.java:67
│   └── sp_get_tariff_rates() - database/procedures/tariff_mgmt.sql:234
└── formatResponse() - passage-java/src/util/ResponseFormatter.java:89
```

**Example - Branch 2:**
```
logRequest() - passage-java/src/util/AuditLogger.java:34
└── writeAuditLog() - passage-java/src/dao/AuditDAO.java:56
```

#### 3.3: Launch Validators in Batches

**IMPORTANT**: To reduce memory usage and prevent timeouts, process validators in SMALL BATCHES of at most 2 at a time.

**Batching Strategy:**
1. Group branches into batches of 2
2. Launch each batch, wait for completion, then launch the next batch
3. This prevents memory exhaustion from too many concurrent file reads

For each branch sub-tree, use the Task tool with the following parameters:
- `subagent_type`: `"call-tree-validator"`
- `description`: `"Validate call tree branch <n>"`
- `model`: `"haiku"` (for cost efficiency on validation tasks)
- `prompt`: Detailed validation instructions (see template below)

**Prompt Template:**
```
Validate the following call tree branch by tracing through the actual source code.

**Entry Point Metadata:**
- Key: <key>
- Type: <type>
- Location: <location>

**Project Root:** <project_root>

**Branch to Validate:**
```
<paste the branch sub-tree here>
```

**Validation Tasks:**

**IMPORTANT - Memory Optimization**: Use TARGETED file reads to minimize memory usage:
- Use Grep to search for function names instead of reading entire files
- Use Read with offset/limit to read only ~50 lines around a function, not the whole file
- Avoid loading large files (>500 lines) entirely into context

1. **Verify Function Existence:**
   - Use Grep to search for the function signature in the source file
   - Use Read with offset to read only ~20 lines around the expected line number
   - Confirm the function exists at the specified line number (exact match required)
   - Example: `Read file_path offset=<line-10> limit=30` to check a specific function

2. **Verify Calls:**
   - Use Grep to search for the child function name within the parent function's file
   - Read only the function body (~50 lines) to confirm the call exists
   - Check that the call is not commented out

3. **Skip Exhaustive Call Discovery:**
   - Do NOT read entire files to "identify ALL calls"
   - Only verify the calls that are already listed in the tree
   - If you notice an obvious missing call during verification, note it, but don't search exhaustively

4. **Verify Hierarchy:**
   - Confirm that the parent-child relationships are correct based on the targeted reads
   - Ensure the indentation accurately reflects the call stack

5. **Check Line Numbers:**
   - Verify line numbers during your targeted reads
   - Report any discrepancies found

**Recursive Validation:**
**AVOID recursive sub-agent spawning when possible** - it causes memory issues.
- Only spawn sub-validators if a branch has MORE than 15 functions AND more than 7 nesting levels
- If you must spawn, spawn only 1 sub-validator at a time (sequential, not parallel)
- Prefer to validate functions yourself using targeted reads rather than spawning sub-agents

**Output Format:**
Provide a structured validation report in the following format:

```markdown
# Validation Report: <branch-name>

## Status
- ✓ VALID / ⚠ WARNINGS / ✗ INVALID

## Summary
- Total functions validated: <count>
- Issues found: <count>
- Obvious missing calls noted: <count> (not exhaustive)

## Detailed Findings

### Function: <function-name> (<file>:<line>)
- Status: ✓ Valid / ⚠ Warning / ✗ Invalid
- Issues:
  - [List any issues found]
- Obvious missing calls (if any noticed during verification):
  - [List any obvious calls noticed - not exhaustive]

[Repeat for each function with findings]

## Recommendations
- [List any recommended corrections to the call tree]
- [List any functions that need to be added]
- [List any false positives that should be removed]
```

**Important Notes:**
- Focus on accuracy over speed
- When in doubt, read the source code carefully
- Use Grep/Glob tools to locate files if needed
- Document ambiguities clearly
- If you launch recursive validators, wait for their results before completing your report
```

**Example - Launching Validators in Batches:**

```
I have 4 branches to validate. Processing in batches of 2:

Batch 1 (launching now):
- Branch 1: processRequest() and its sub-tree
- Branch 2: logRequest() and its sub-tree

[Wait for Batch 1 to complete]

Batch 2 (launching after Batch 1 completes):
- Branch 3: handleError() and its sub-tree
- Branch 4: cleanup() and its sub-tree
```

For each batch, make a SINGLE message with at most 2 Task tool calls.
Wait for the batch to complete before launching the next batch.

#### 3.4: Validate Entry Point Root

In addition to validating branches, validate the entry point itself:

**Launch Entry Point Validator:**
- Use the Task tool with `subagent_type: "call-tree-validator"`
- Validate that the entry point function exists
- Verify that its direct children (first-level branches) are all present and correct
- Check for any missing first-level calls

#### 3.5: Collect and Analyze Validation Reports

**Aggregate Results:**
After all validators complete, collect their reports and analyze findings.

**Create Validation Summary:**

Save to: `./docs/entry-points/<type>/<key>/validation/summary.md`

```markdown
# Call Tree Validation Summary

**Entry Point:** <key>
**Validation Date:** <timestamp>
**Validators Launched:** <count>

## Overall Status
- ✓ VALID / ⚠ NEEDS CORRECTIONS / ✗ INVALID

## Branch Validation Results

### Branch 1: <branch-name>
- Status: <status>
- Functions validated: <count>
- Issues: <count>

### Branch 2: <branch-name>
- Status: <status>
- Functions validated: <count>
- Issues: <count>

[Repeat for each branch]

## Aggregated Issues

### Missing Calls
- <file>:<function>:<line> - Missing call to <target-function>
- [List all missing calls from all validators]

### Incorrect Calls
- <file>:<function>:<line> - Call to <target-function> not found in source
- [List all incorrect calls]

### Line Number Discrepancies
- <file>:<function> - Listed at line <X>, actually at line <Y>
- [List significant line number issues]

## Corrections Needed
1. [List required corrections in priority order]
2. [Include file paths and specific changes needed]

## Validation Coverage
- Total functions in call tree: <count>
- Functions validated: <count>
- Coverage: <percentage>%
```

#### 3.6: Apply Corrections

If validation identified issues, update the call tree:

**Update call-tree.txt:**
- Add any missing calls identified by validators
- Remove any incorrect calls
- Correct line numbers if significantly wrong
- Update hierarchy if needed

**Update functions-to-extract.txt:**
- Add any newly discovered functions
- Remove any invalid entries

**Extract Missing Functions:**
- For any new functions added to the tree, run the `/extract-call-tree` command's step 5.2 (Extract Function Bodies)
- Ensure the code/ directory is updated with all newly discovered functions

**Document Changes:**
Update `extraction-notes.md` with validation findings:
```markdown
## Validation Corrections

### Validation Date: <timestamp>

### Missing Calls Added:
- Added call from `processRequest()` to `checkPermissions()` (line 125)
- Added call from `validateInput()` to `sanitizeInput()` (line 156)

### Incorrect Calls Removed:
- Removed call from `getTariffRates()` to `cacheResults()` (not found in source)

### Line Number Corrections:
- Updated `formatResponse()` from line 89 to line 92
```

#### 3.7: Re-validate if Necessary

**When to Re-validate:**
- If significant corrections were made (more than 10% of the tree changed)
- If validators reported ambiguous findings that were resolved by updates
- If new functions were added that have complex sub-trees

**Re-validation Process:**
- Repeat steps 3.1-3.5 for the updated call tree
- Focus validation on corrected branches only (not the entire tree)
- Document the re-validation in `validation/summary.md`

#### 3.8: Mark Validation Complete

**Create Validation Marker:**
Save to: `./docs/entry-points/<type>/<key>/validation/VALIDATED`

```
Validation completed: <timestamp>
Status: <VALID/VALID_WITH_CORRECTIONS>
Validators used: <count>
Total functions validated: <count>
Corrections applied: <count>
```

**Update extraction-notes.md:**
Add a final validation section:
```markdown
## Validation Status

- ✓ Call tree validated on <date>
- Validators: <count> parallel validators
- Coverage: <percentage>%
- Status: VALIDATED
- Issues found: <count>
- Corrections applied: <count>
```

**Success Criteria:**
The call tree is considered validated when:
- All branches have been validated by call-tree-validator subagents
- All identified issues have been addressed
- Validation coverage is ≥95% of functions in the tree
- No critical errors remain (missing calls, incorrect calls, etc.)
- All validation reports show ✓ VALID or ⚠ WARNINGS (not ✗ INVALID)
