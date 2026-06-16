---
description: Inventory all API endpoints invoked by a UI feature and write results to ./docs/entry-points/ui-features/<key>/api-usage.json
argument-hint: "UI feature from inventory.json"
---

# Inventory UI Feature API Dependencies

You are an expert codebase investigator tasked with identifying all API endpoints that a specific UI feature depends on.

**IMPORTANT**: You will receive a JSON object representing a single UI feature from `./docs/entry-points/ui-features/inventory.json`. This object will include:
- `key` - The unique identifier for the UI feature
- `location` - The file path and line number of the UI element
- `elementType` - The type of UI element (ui-page, ui-panel-data-table, ui-menu-action, etc.)
- Other metadata about the UI feature

## Objective
Identify all API endpoints that this UI feature directly invokes or depends on for loading/operation. Record only direct HTTP calls made by this feature's code, not calls made by parent/child features.

> **⚠️ CRITICAL REMINDER**: Before completing this task, you MUST run `node .claude/tools/validate-ui-api-usage.js` on your output file and fix any errors. Do not exit until validation passes. See "Final Output - MANDATORY STEPS" section at the end.

## Pre-Analysis: Check for Existing Call Tree Analysis

**IMPORTANT**: Before beginning your analysis, check if a UI call tree has already been extracted for this feature:

Check for: `./docs/entry-points/ui-features/<key>/`

If this directory exists and contains call tree analysis artifacts, you should leverage them:

### Available Artifacts from UI Call Tree Extraction

1. **`call-tree.txt`** - The complete UI call tree with all function calls traced
   - Shows the hierarchy of function calls in the UI layer
   - **CRITICAL**: Contains `[API]` markers indicating Java API boundaries
   - Each API call is marked as: `[API] serviceName.methodName() - Java REST endpoint at /endpoint/path`
   - Use this to quickly identify all API calls without re-tracing the code

2. **`api-calls.txt`** - A deduplicated list of all Java API calls found
   - Format: `[API] serviceName.methodName() - Java REST endpoint at /endpoint/path`
   - This is a quick reference list extracted from the call tree
   - Use this as your primary source for API endpoints to inventory

3. **`api-integration.md`** - Detailed documentation of API integration points
   - Lists each REST endpoint with:
     - Endpoint path
     - Which function invokes it (file and line number)
     - Purpose of the call
     - Parameters passed
     - Result and fault handlers
   - Use this to get the `invokedFrom` details for your output

4. **`code/`** - Extracted source code for all UI functions
   - Contains the actual ActionScript/MXML source code
   - Use this if you need to verify details about an API call
   - Organized by directory structure matching the original source

5. **`extraction-notes.md`** - Any challenges or notes from the extraction process
   - May document ambiguous calls or missing implementations
   - Check this for context about API calls that might be conditional or unclear

### How to Use Call Tree Artifacts

If call tree artifacts exist for this UI feature:

1. **Start with `api-calls.txt`**: Get the complete list of API endpoints invoked
2. **Reference `api-integration.md`**: Get detailed information about each endpoint
3. **Cross-reference `call-tree.txt`**: Verify the context and calling hierarchy
4. **Use `code/` if needed**: Look up exact source code if details are unclear

**Example workflow with artifacts:**
```
1. Read ./docs/entry-points/ui-features/<key>/api-calls.txt
   → Find: [API] companyService.updateCompany() - Java REST endpoint at /service/company/companyMaint

2. Read ./docs/entry-points/ui-features/<key>/api-integration.md
   → Find: Invoked from saveCompany() in CompanyMaintenanceGrid.mxml:234

3. Match against API inventory
   → Find: 3029-spring-companyservice-updatecompany

4. Build output entry with all details
```

This approach is **significantly faster and more accurate** than manually tracing through UI code.

### If No Call Tree Artifacts Exist

If the directory doesn't exist or doesn't contain call tree artifacts, proceed with the manual analysis approach described below.

## High-Level Approach

### 1. Understand the UI Feature Scope
- Parse the input JSON to extract `key`, `location`, `elementType`, and other relevant fields
- Determine the scope of code to analyze based on `elementType`:
  - **ui-page**: The entire page and its initialization code
  - **ui-panel-data-table**: The specific panel/grid component and its data loading
  - **ui-panel-form**: The form component and its submit/load handlers
  - **ui-menu-action**: The specific action handler code
  - **ui-panel-display**: The display panel and its data loading

### 2. Locate the Relevant UI Code
- Use the `location` field to find the primary file
- For AngularJS applications (typical in this codebase):
  - Find the controller file referenced in the HTML (look for `ng-controller`)
  - Find associated service files that the controller depends on
  - Find the directive/component files if applicable
- For other frameworks, adapt the search accordingly

### 3. Identify HTTP Call Patterns
This codebase uses several patterns for making API calls:

#### Pattern A: Direct Service Layer Calls (Most Common)
```javascript
// Service file (e.g., agencyService.js)
var updateAgent = function(param, callback) {
    var postData = {...};
    return remoteService.post(endpoint, postData, null, callback);
};
```
Look for:
- `remoteService.post()` / `remoteService.get()` / etc.
- `$http.post()` / `$http.get()` / etc.
- `fetch()` calls
- `axios()` calls

#### Pattern B: JSON-RPC Style Calls
```javascript
remoteService.post("service/company/agency", {
    methodName: "updateAgentDelegation",
    param: data
}, null, callback);
```
The endpoint is `/service/company/agency` and the method is `updateAgentDelegation`.

#### Pattern C: Report Service Calls
```javascript
reportService.createDbReport(reportFile, reportFilter, reportGenerator, ...)
reportService.createReportWithParams(...)
```
These typically call reporting endpoints.

#### Pattern D: Download/File Service Calls
```javascript
downloadService.openFile(serviceName, param)
```

### 4. Extract Endpoint Information
For each HTTP call found:
- Extract the endpoint path (e.g., `"service/company/agency"`)
- Extract the method name if using JSON-RPC style (e.g., `"updateAgentDelegation"`)
- Extract the HTTP method (POST, GET, etc.) if determinable
- Note the service layer file and line number

### 5. Match Against API Inventory
Load `./docs/entry-points/api-endpoints/inventory.json` and match each discovered call to an entry:

**Matching Logic**:
- For Spring endpoints with JSON-RPC pattern:
  - The inventory key follows pattern: `NNNN-spring-servicename-methodname`
  - Match based on the endpoint path and method name
  - Example: `/service/company/agency` + `updateAgentDelegation` � look for `*-spring-agencyservice-updateagentdelegation`

- For Portal JSP endpoints:
  - The inventory key follows pattern: `NNN-portal-pagename-method`
  - Match based on the URI/action name
  - Example: `contact.action` � look for `*-portal-contact-get` or `*-portal-contact-post`

- Matching rules:
  - Service names in endpoints often map to bean IDs (case-insensitive)
  - Method names should match exactly (case-insensitive)
  - If the HTTP method is known, prefer the matching method (GET/POST)

### 6. Handle Scope Boundaries
**CRITICAL**: Only record API calls that are directly made by THIS specific UI feature:

- **For ui-page**: Include calls in page initialization and page-level actions
- **For ui-panel-***: Include only calls made by that specific panel's controller/logic
- **For ui-menu-action**: Include only the API call triggered by that action
  - If the action opens a modal, DO NOT include the modal's API calls (those belong to the modal feature)
  - If the action directly makes an API call (e.g., delete, toggle flag), include it

Example exclusions:
- A "New" button that opens a modal � the modal's save call belongs to the modal feature, not the button
- A parent page � child panel's data calls belong to the child panel feature
- Service layer utility calls that aren't triggered by this feature

### 7. Build Output Structure
For each matched API endpoint, create an entry with:
```json
{
  "apiKey": "the-key-from-api-inventory",
  "endpoint": "the/endpoint/path",
  "methodName": "methodName or null",
  "httpMethod": "POST/GET/etc or null",
  "invokedFrom": {
    "file": "relative/path/to/service/file.js",
    "line": 123,
    "functionName": "nameOfServiceFunction"
  }
}
```

## Output Location
**CRITICAL**: Write the output JSON to:
```
./docs/entry-points/ui-features/<key>/api-usage.json
```

Where `<key>` is the key from the input UI feature JSON.

Create the directory structure if it doesn't exist.

## Output Format

**JSON Schema**: The output must conform to `.claude/schemas/ui-feature-api-usage.schema.json`

**⚠️ MANDATORY VALIDATION ⚠️**: After creating the file, you MUST run the validation script:
```bash
node .claude/tools/validate-ui-api-usage.js ./docs/entry-points/ui-features/<key>/api-usage.json
```

**YOU MUST NOT EXIT THIS TASK UNTIL VALIDATION PASSES.** If the validation script reports any errors:
1. Read the error message carefully
2. Fix the issues in the api-usage.json file
3. Re-run the validation script
4. Repeat until validation passes with no errors

The file must contain a JSON object with this structure:
```json
{
  "uiFeatureKey": "the-ui-feature-key",
  "uiFeatureLocation": "the-ui-feature-location",
  "apiDependencies": [
    {
      "apiKey": "3016-spring-agencyservice-updateagentdelegation",
      "endpoint": "service/company/agency",
      "methodName": "updateAgentDelegation",
      "httpMethod": "POST",
      "invokedFrom": {
        "file": "legacy/northwest-passage/passage-java/web/modules/agency/delegation/services/agency_delegationService.js",
        "line": 45,
        "functionName": "updateAgentDelegation"
      }
    }
  ]
}
```

- `uiFeatureKey`: The key of the UI feature being analyzed
- `uiFeatureLocation`: The location of the UI feature
- `apiDependencies`: Array of API dependencies (empty array if none found)
  - `apiKey`: The key from `./docs/entry-points/api-endpoints/inventory.json`
  - `endpoint`: The API endpoint path
  - `methodName`: The method name for JSON-RPC style calls, or `null`
  - `httpMethod`: The HTTP method (GET, POST, etc.) or `null` if unknown
  - `invokedFrom`: Location of the actual HTTP call
    - `file`: Repository-relative path to the service file
    - `line`: 1-based line number of the HTTP call
    - `functionName`: Name of the service function making the call

## Quality Checks
- **MANDATORY - DO NOT SKIP**: Run `node .claude/tools/validate-ui-api-usage.js <output-file>` and ensure it passes with zero errors
- Verify that each API key exists in `./docs/entry-points/api-endpoints/inventory.json`
- Ensure the scope is correct (only direct dependencies of THIS feature)
- Validate JSON structure matches schema exactly (use `uiFeatureKey` not `feature_key`, `apiDependencies` not `api_calls`, etc.)
- Handle cases where no API dependencies are found (empty array)
- Deduplicate identical entries
- Ensure proper null values (use `null` not empty strings for methodName/httpMethod when unknown)

## Special Cases

### Generic Table Pages
If `isGenericTablePage: true`, the page loads data from a database table directly without a specific API endpoint. In this case, the `apiDependencies` should be empty, but add a note:
```json
{
  "uiFeatureKey": "...",
  "uiFeatureLocation": "...",
  "apiDependencies": [],
  "notes": ["Generic table page - loads directly from database table: <tableName>"]
}
```

### Report/Print Actions
For report actions, try to identify the report generation endpoint. If it's a generic report service, document it as:
```json
{
  "apiKey": "report-service-generic",
  "endpoint": "service/report/generate",
  "methodName": null,
  "httpMethod": "POST",
  "invokedFrom": {...}
}
```

### Unknown/Unmatched Endpoints
If you find an API call but cannot match it to an entry in the API inventory:
```json
{
  "apiKey": "UNMATCHED",
  "endpoint": "the/endpoint/path",
  "methodName": "methodName or null",
  "httpMethod": "POST/GET/etc or null",
  "invokedFrom": {...},
  "notes": ["Could not find matching entry in API inventory"]
}
```

## Common Mistakes to Avoid

❌ **WRONG** - Using old field names:
```json
{
  "feature_key": "...",          // Wrong: should be "uiFeatureKey"
  "api_calls": [...]             // Wrong: should be "apiDependencies"
}
```

❌ **WRONG** - Empty strings instead of null:
```json
{
  "methodName": "",              // Wrong: should be null
  "httpMethod": ""               // Wrong: should be null
}
```

❌ **WRONG** - Including controller layer calls:
```json
{
  "invokedFrom": {
    "file": "controllers/fooController.js",  // Wrong: this is controller, not service
    "functionName": "save"                    // Wrong: this calls the service, doesn't make HTTP call
  }
}
```

❌ **WRONG** - Adding extra fields:
```json
{
  "apiKey": "...",
  "purpose": "...",              // Wrong: not in schema
  "trigger": "...",              // Wrong: not in schema
  "parameters": {...}            // Wrong: not in schema
}
```

✓ **CORRECT** - Service layer HTTP call with proper null values:
```json
{
  "apiKey": "131-spring-tabledefnservice-gettabledefn",
  "endpoint": "service/tables",
  "methodName": "getTableDefn",
  "httpMethod": "POST",
  "invokedFrom": {
    "file": "legacy/northwest-passage/passage-java/web/modules/tables/services/tableService.js",
    "line": 6,
    "functionName": "getTableDefn"
  }
}
```

✓ **CORRECT** - Unknown HTTP method:
```json
{
  "apiKey": "...",
  "endpoint": "...",
  "methodName": "someMethod",
  "httpMethod": null,            // Correct: use null when unknown
  "invokedFrom": {...}
}
```

## Final Output - MANDATORY STEPS

Write ONLY the JSON object to the output file -- no narrative explanation or markdown formatting.

### ⚠️ REQUIRED: Validation Before Completion ⚠️

**YOU MUST COMPLETE THESE STEPS BEFORE EXITING. THIS IS NOT OPTIONAL.**

1. **Write the api-usage.json file** to `./docs/entry-points/ui-features/<key>/api-usage.json`

2. **Run the validation script**:
   ```bash
   node .claude/tools/validate-ui-api-usage.js ./docs/entry-points/ui-features/<key>/api-usage.json
   ```

3. **Check the validation result**:
   - If validation **PASSES**: You may complete the task
   - If validation **FAILS**: You MUST fix the errors and re-validate

4. **If validation fails, you MUST**:
   - Read the error message from the validation script
   - Edit the api-usage.json file to fix the reported issues
   - Run the validation script again
   - Repeat until validation passes

**DO NOT EXIT WITH A FAILING VALIDATION. Fix all errors first.**

Common validation errors and fixes:
- "Missing required field 'uiFeatureKey'" → Add the uiFeatureKey field
- "Invalid type for 'apiDependencies'" → Ensure it's an array, not null or object
- "Additional properties not allowed" → Remove any fields not in the schema
- "methodName should be null, not empty string" → Change "" to null
