# Validate Call Tree (UI) Command

You are tasked with validating an already-extracted UI call tree for accuracy and completeness. This command assumes the call tree has been extracted using the `extract-call-tree-ui` command.

## Input Parameters

You will receive the **Entry Point Payload** - A JSON object describing the UI entry point:
```json
{
  "key": "01-some-ui-feature",
  "location": "path/to/file.mxml or path/to/file.as, ComponentName or function_name()"
}
```

## Task Overview

Validate the UI-layer call tree that was previously extracted for this entry point. The validation ensures:
- All function calls are accurate and exist in the source code
- No meaningful calls were missed
- All API boundaries are properly marked as terminal nodes
- Line numbers are accurate
- Parent-child relationships are correct
- Result/fault handlers for service calls are traced

## Execution Steps

### Step 1: Parse Input

Extract the following from the entry point payload:
- `key` - Unique identifier for the UI feature
- `location` - Location description (file path and component/function name)

### Step 2: Determine Project Root

Based on the file path in the `location` field, determine which project root to use:

- If path contains `portal` → use `./legacy/portal`
- If path contains `northwest-passage` → use `./legacy/northwest-passage`

**Default**: Use `./legacy/portal` for UI features

### Step 3: Locate Call Tree Files

Verify that the call tree files exist at:
```
./docs/entry-points/ui-features/<key>/
```

**Required Files:**
- `metadata.json` - Entry point metadata
- `call-tree.txt` - The call tree to validate
- `functions-to-extract.txt` - List of functions in the tree
- `api-calls.txt` - List of API boundaries

If these files don't exist, the extraction command must be run first.

### Step 4: Validate Call Tree

After extracting the UI call tree, validate its accuracy by verifying each branch against the actual source code using parallel call-tree-validator subagents.

**Goal**: Ensure the call tree is complete, accurate, reflects the actual UI code execution paths, and properly stops at API boundaries.

#### 4.1: Parse Call Tree Structure

Read and analyze the `./docs/entry-points/ui-features/<key>/call-tree.txt` file to identify validation units.

**Identify Major Branches:**
- Parse the tree structure to identify the entry point's direct children (first-level branches)
- Each first-level branch represents a logical sub-tree that can be validated independently
- Group related branches if they form cohesive validation units

**Example Analysis:**
```
CompanyMaintenanceGrid.creationComplete() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:45
├── initializeGrid() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:89    [Branch 1]
│   ├── setupColumns() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:112
│   └── loadCompanies() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:156
│       └── [API] companyService.getCompanyList() - Java REST endpoint at /service/company/list
├── bindEventHandlers() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:203  [Branch 2]
└── applyPermissions() - portal-flex/src/main/flex/com/williams/util/SecurityHelper.as:67                  [Branch 3]
```

In this example, we have 3 major branches to validate in parallel:
1. The `initializeGrid()` branch with its entire sub-tree
2. The `bindEventHandlers()` branch
3. The `applyPermissions()` branch

#### 4.2: Extract Branch Sub-Trees

For each major branch identified, extract its complete sub-tree into a separate validation unit.

**Create Working Files:**

For each branch, create a temporary sub-tree file:
```
./docs/entry-points/ui-features/<key>/validation/branch-<n>.txt
```

**Example - Branch 1:**
```
initializeGrid() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:89
├── setupColumns() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:112
└── loadCompanies() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:156
    └── [API] companyService.getCompanyList() - Java REST endpoint at /service/company/list
```

#### 4.3: Launch Validators in Batches

**IMPORTANT**: To reduce memory usage and prevent timeouts, process validators in SMALL BATCHES of at most 2 at a time.

**Batching Strategy:**
1. Group branches into batches of 2
2. Launch each batch, wait for completion, then launch the next batch
3. This prevents memory exhaustion from too many concurrent file reads

For each branch sub-tree, use the Task tool with the following parameters:
- `subagent_type`: `"call-tree-validator"`
- `description`: `"Validate UI call tree branch <n>"`
- `model`: `"haiku"` (for cost efficiency on validation tasks)
- `prompt`: Detailed validation instructions (see template below)

**Prompt Template:**
```
Validate the following UI call tree branch by tracing through the actual source code.

**Entry Point Metadata:**
- Key: <key>
- Location: <location>

**Project Root:** <project_root>

**Branch to Validate:**
```
<paste the branch sub-tree here>
```

**UI-Specific Validation Tasks:**

**IMPORTANT - Memory Optimization**: Use TARGETED file reads to minimize memory usage:
- Use Grep to search for function names instead of reading entire files
- Use Read with offset/limit to read only ~50 lines around a function, not the whole file
- Avoid loading large files (>500 lines) entirely into context

1. **Verify Function Existence:**
   - Use Grep to search for the function signature in the source file (MXML or ActionScript)
   - Use Read with offset to read only ~20 lines around the expected line number
   - For MXML files, check both inline <mx:Script> blocks and event handlers
   - Confirm the function exists at the specified line number (exact match required)
   - Example: `Read file_path offset=<line-10> limit=30` to check a specific function

2. **Verify UI Calls:**
   - Use Grep to search for the child function name within the parent function's file
   - Read only the function body (~50 lines) to confirm the call exists
   - Check for ActionScript method calls, event handler bindings, and service invocations
   - Check that the call is not commented out

3. **Verify API Boundaries:**
   - Confirm that all RemoteObject/HTTPService/WebService calls are marked with `[API]` and are terminal nodes
   - Ensure NO Java code is traced beyond these API boundaries

4. **Skip Exhaustive Call Discovery:**
   - Do NOT read entire files to "identify ALL calls"
   - Only verify the calls that are already listed in the tree
   - If you notice an obvious missing call during verification, note it, but don't search exhaustively

5. **Verify Result/Fault Handlers:**
   - For each service call, verify that result/fault handlers are traced (if listed in the tree)
   - Don't exhaustively search for handlers that aren't already listed

6. **Verify Hierarchy:**
   - Confirm that the parent-child relationships are correct based on the targeted reads
   - Ensure the indentation accurately reflects the call stack

7. **Check Line Numbers:**
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
- API boundaries verified: <count>

## Detailed Findings

### Function: <function-name> (<file>:<line>)
- Status: ✓ Valid / ⚠ Warning / ✗ Invalid
- Issues:
  - [List any issues found]
- Obvious missing calls (if any noticed during verification):
  - [List any obvious calls noticed - not exhaustive]

[Repeat for each function with findings]

## API Boundary Verification

### API Call: <service-call> (<file>:<line>)
- Status: ✓ Properly marked as terminal / ✗ Java code traced beyond boundary
- Endpoint: <endpoint-path>
- Result handler traced: Yes/No
- Fault handler traced: Yes/No

[Repeat for each API boundary]

## Recommendations
- [List any recommended corrections to the call tree]
- [List any functions that need to be added]
- [List any false positives that should be removed]
- [List any API boundaries that need correction]
```

**Important Notes:**
- Focus on accuracy over speed
- When in doubt, read the source code carefully
- Use Grep/Glob tools to locate files if needed
- Pay special attention to MXML inline scripts vs. external ActionScript files
- Document ambiguities clearly
- Ensure no Java code is traced beyond API boundaries
- If you launch recursive validators, wait for their results before completing your report
```

**Example - Launching Validators in Batches:**

```
I have 3 branches to validate. Processing in batches of 2:

Batch 1 (launching now):
- Branch 1: initializeGrid() and its sub-tree
- Branch 2: bindEventHandlers() and its sub-tree

[Wait for Batch 1 to complete]

Batch 2 (launching after Batch 1 completes):
- Branch 3: applyPermissions() and its sub-tree
```

For each batch, make a SINGLE message with at most 2 Task tool calls.
Wait for the batch to complete before launching the next batch.

#### 4.4: Validate Entry Point Root

In addition to validating branches, validate the entry point itself:

**Launch Entry Point Validator:**
- Use the Task tool with `subagent_type: "call-tree-validator"`
- Validate that the entry point function/component exists
- Verify that its direct children (first-level branches) are all present and correct
- Check for any missing first-level calls
- For MXML components, verify creationComplete and other lifecycle handlers are traced

#### 4.5: Collect and Analyze Validation Reports

**Aggregate Results:**
After all validators complete, collect their reports and analyze findings.

**Create Validation Summary:**

Save to: `./docs/entry-points/ui-features/<key>/validation/summary.md`

```markdown
# UI Call Tree Validation Summary

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
- API boundaries verified: <count>

### Branch 2: <branch-name>
- Status: <status>
- Functions validated: <count>
- Issues: <count>
- API boundaries verified: <count>

[Repeat for each branch]

## Aggregated Issues

### Missing Calls
- <file>:<function>:<line> - Missing call to <target-function>
- [List all missing calls from all validators]

### Incorrect Calls
- <file>:<function>:<line> - Call to <target-function> not found in source
- [List all incorrect calls]

### API Boundary Issues
- <file>:<line> - API call not properly marked as terminal
- <file>:<line> - Java code traced beyond API boundary
- <file>:<line> - Missing result/fault handler
- [List all API boundary issues]

### Line Number Discrepancies
- <file>:<function> - Listed at line <X>, actually at line <Y>
- [List significant line number issues]

## Corrections Needed
1. [List required corrections in priority order]
2. [Include file paths and specific changes needed]

## Validation Coverage
- Total functions in call tree: <count>
- Functions validated: <count>
- API boundaries validated: <count>
- Coverage: <percentage>%
```

#### 4.6: Apply Corrections

If validation identified issues, update the call tree:

**Update call-tree.txt:**
- Add any missing calls identified by validators
- Remove any incorrect calls
- Correct line numbers if significantly wrong
- Update hierarchy if needed
- Fix API boundary markers if needed

**Update functions-to-extract.txt:**
- Add any newly discovered functions
- Remove any invalid entries

**Update api-calls.txt:**
- Add any newly discovered API boundaries
- Remove any incorrect API markers

**Extract Missing Functions:**
- For any new functions added to the tree, the extraction command should be re-run for step 5.2 (Extract Function Bodies)
- Ensure the code/ directory is updated with all newly discovered functions

**Document Changes:**
Update `extraction-notes.md` with validation findings:
```markdown
## Validation Corrections

### Validation Date: <timestamp>

### Missing Calls Added:
- Added call from `initializeGrid()` to `configureDataProvider()` (line 125)
- Added result handler from `loadCompanies()` to `handleLoadResult()` (line 178)

### Incorrect Calls Removed:
- Removed call from `setupColumns()` to `refreshDisplay()` (not found in source)

### API Boundary Corrections:
- Updated `companyService.updateCompany()` to properly mark as `[API]` terminal node
- Added missing fault handler `handleSaveFault()` for save operation

### Line Number Corrections:
- Updated `bindEventHandlers()` from line 203 to line 206
```

#### 4.7: Re-validate if Necessary

**When to Re-validate:**
- If significant corrections were made (more than 10% of the tree changed)
- If validators reported ambiguous findings that were resolved by updates
- If new functions were added that have complex sub-trees
- If API boundaries were corrected

**Re-validation Process:**
- Repeat steps 4.1-4.5 for the updated call tree
- Focus validation on corrected branches only (not the entire tree)
- Document the re-validation in `validation/summary.md`

#### 4.8: Mark Validation Complete

**Create Validation Marker:**
Save to: `./docs/entry-points/ui-features/<key>/validation/VALIDATED`

```
Validation completed: <timestamp>
Status: <VALID/VALID_WITH_CORRECTIONS>
Validators used: <count>
Total functions validated: <count>
API boundaries validated: <count>
Corrections applied: <count>
```

**Update extraction-notes.md:**
Add a final validation section:
```markdown
## Validation Status

- ✓ UI call tree validated on <date>
- Validators: <count> parallel validators
- Coverage: <percentage>%
- Status: VALIDATED
- Issues found: <count>
- Corrections applied: <count>
- API boundaries verified: <count>
```

**Success Criteria:**
The UI call tree is considered validated when:
- All branches have been validated by call-tree-validator subagents
- All identified issues have been addressed
- Validation coverage is ≥95% of functions in the tree
- No critical errors remain (missing calls, incorrect calls, API boundary violations, etc.)
- All validation reports show ✓ VALID or ⚠ WARNINGS (not ✗ INVALID)
- All API boundaries are properly marked and no Java code is traced beyond them
- All result/fault handlers for service calls are traced

## Summary

This command validates previously-extracted UI-layer call trees by:

1. **Locating** the extracted call tree files
2. **Parsing** the call tree structure into validation units
3. **Launching** parallel call-tree-validator subagents for each branch
4. **Collecting** and analyzing validation reports
5. **Applying** necessary corrections to the call tree
6. **Re-validating** if significant changes were made
7. **Marking** the call tree as validated when complete

The result is a verified, accurate call tree that can be trusted for documentation and analysis purposes.
