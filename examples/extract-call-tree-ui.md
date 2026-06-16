# Extract Call Tree (UI) Command

You are tasked with extracting the call tree for a UI page/component/feature. This command is specialized for UI analysis and **STOPS at the Java API layer** - you do NOT need to trace into Java service/DAO implementations.

## Input Parameters

You will receive the **Entry Point Payload** - A JSON object describing the UI entry point:
```json
{
  "key": "01-some-ui-feature",
  "location": "path/to/file.mxml or path/to/file.as, ComponentName or function_name()"
}
```

## Task Overview

Extract the UI-layer call tree for this entry point. The analysis **stops at Java API boundaries** - when you encounter calls to Java REST endpoints or services, you mark them as terminal nodes and do NOT trace into the Java implementation.

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

### Step 3: Create Output Directory Structure

Create the directory structure if it doesn't exist:
```
./docs/entry-points/ui-features/<key>/
```

For example:
```
./docs/entry-points/ui-features/01-company-maintenance-grid/
```

### Step 4: Save Entry Point Metadata

Save the original entry point payload to:
```
./docs/entry-points/ui-features/<key>/metadata.json
```

This should be the exact JSON object that was provided as input:
```json
{
  "key": "01-some-ui-feature",
  "location": "path/to/file.mxml, ComponentName",
  "type": "ui-features"
}
```

### Step 5: Extract UI Call Tree

#### 5.1 Trace UI Call Tree

**Manually** trace the UI-layer call hierarchy from the entry point through all meaningful UI code branches by reading and analyzing the source code.

**Parse the Entry Point Location:**

From the `location` field in the metadata, extract:
- File path (relative to project root)
- Component name (for MXML files)
- Function/method name (for ActionScript files)

**Examples:**
- `portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml, CompanyMaintenanceGrid`
  - File: `portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml`
  - Component: `CompanyMaintenanceGrid`
- `portal-flex/src/main/flex/com/williams/util/GridHelper.as, handleGridEvent()`
  - File: `portal-flex/src/main/flex/com/williams/util/GridHelper.as`
  - Function: `handleGridEvent`

**Read the Entry Point Source:**

1. Use the Read tool to open the entry point file
2. For MXML files:
   - Identify event handlers in the markup (e.g., `click="handleClick(event)"`)
   - Locate the `<mx:Script>` section containing ActionScript code
   - Read inline functions and imports
3. For ActionScript files:
   - Locate the specified function/method/class
   - Identify all function calls within

**Trace UI Function Calls:**

Read through the entry point and identify all UI-layer function/method calls:

1. **ActionScript function calls** - `functionName(args)`
2. **Method calls** - `object.methodName(args)` or `ClassName.staticMethod(args)`
3. **Event handler calls** - Functions called in response to user interactions
4. **Binding expressions** - Data binding calls
5. **Service calls** - RemoteObject, HTTPService, WebService calls
6. **Constructor calls** - `new ClassName(args)`

**For each called function, recursively trace ONLY UI-layer code:**

1. Determine the file location:
   - Check imports at the top of the file
   - Search for class definitions using Grep or Glob tools
   - Follow package structure
2. Read the called function's source code
3. Identify all function calls within that function
4. Add to the tracing queue
5. **STOP at Java API boundaries** (see below)

**CRITICAL - Stop at Java API Boundaries:**

When you encounter calls to Java APIs, mark them as **terminal nodes** and do NOT trace into Java code.

**Java API Boundary Markers:**

1. **RemoteObject calls** - ActionScript calling Java services:
   ```actionscript
   var remoteObject:RemoteObject = new RemoteObject("myService");
   remoteObject.getOperation("methodName").send(args);
   ```
   Mark as: `[API] myService.methodName() - Java REST endpoint`

2. **HTTPService calls** - HTTP requests to REST endpoints:
   ```actionscript
   var http:HTTPService = new HTTPService();
   http.url = "/service/company/companyMaint";
   http.send(params);
   ```
   Mark as: `[API] POST /service/company/companyMaint - Java REST endpoint`

3. **WebService calls** - SOAP service invocations:
   ```actionscript
   var ws:WebService = new WebService();
   ws.loadWSDL("http://example.com/service?wsdl");
   ws.operationName.send(args);
   ```
   Mark as: `[API] operationName - SOAP service`

4. **Direct REST calls** - URLLoader or similar:
   ```actionscript
   var loader:URLLoader = new URLLoader();
   var request:URLRequest = new URLRequest("/api/endpoint");
   loader.load(request);
   ```
   Mark as: `[API] GET /api/endpoint - REST endpoint`

**Example - Stopping at API Boundary:**

❌ **WRONG** (tracing into Java):
```
handleSave() - CompanyMaintenanceGrid.mxml:156
├── validateForm() - CompanyMaintenanceGrid.mxml:203
└── saveCompany() - CompanyMaintenanceGrid.mxml:234
    └── companyService.updateCompany() - CompanyMaintenanceService.java:107  ← DON'T GO HERE
        ├── updateCompany() - CompanyMaintenanceDAO.java:58
        └── getPrevCompany() - CompanyMaintenanceDAO.java:242
```

✓ **CORRECT** (stopping at API boundary):
```
handleSave() - CompanyMaintenanceGrid.mxml:156
├── validateForm() - CompanyMaintenanceGrid.mxml:203
└── saveCompany() - CompanyMaintenanceGrid.mxml:234
    └── [API] companyService.updateCompany() - Java REST endpoint at /service/company/companyMaint
```

**What to Include:**

Trace all meaningful UI code:
- Event handlers (click, change, initialize, etc.)
- Data binding expressions
- Validation logic
- UI state management
- ActionScript utility functions
- Custom UI components
- Service call setup (but not the Java implementation)
- Result/fault handlers for service calls

**What to Exclude:**

Skip trivial operations:
- Simple getters/setters without logic
- Basic property access
- Flex framework calls (built-in components)
- External library calls (outside the project)
- Logging statements
- Basic constructors with no logic

**Track Your Progress:**

Maintain a working document as you trace to avoid infinite loops and duplication:

**Create: `./docs/entry-points/ui-features/<key>/call-tree.txt`**

Use a tree structure format to document the hierarchy:

```
CompanyMaintenanceGrid.creationComplete() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:45
├── initializeGrid() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:89
│   ├── setupColumns() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:112
│   └── loadCompanies() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:156
│       └── [API] companyService.getCompanyList() - Java REST endpoint at /service/company/list
├── bindEventHandlers() - portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:203
└── applyPermissions() - portal-flex/src/main/flex/com/williams/util/SecurityHelper.as:67
```

**Include location information:**
- Function/handler name
- File path (relative to project root)
- Line number where function begins
- For API calls: mark with `[API]` and include endpoint path

**Handle Result/Fault Handlers:**

Service calls have result and fault handlers - trace these as well:

```
saveCompany() - CompanyMaintenanceGrid.mxml:234
├── [API] companyService.updateCompany() - Java REST endpoint at /service/company/companyMaint
├── handleSaveResult() - CompanyMaintenanceGrid.mxml:267 [result handler]
│   ├── showSuccessMessage() - CompanyMaintenanceGrid.mxml:289
│   └── refreshGrid() - CompanyMaintenanceGrid.mxml:298
└── handleSaveFault() - CompanyMaintenanceGrid.mxml:312 [fault handler]
    └── showErrorMessage() - CompanyMaintenanceGrid.mxml:334
```

**Handle Multiple Branches:**

- If a function calls multiple functions, trace all branches
- Use proper tree indentation to show hierarchy
- Mark each level of depth clearly

**Handle Recursive Calls:**

If you encounter a function that has already been traced:
```
processItems() - com/williams/util/ItemProcessor.as:45
├── processItem() - com/williams/util/ItemProcessor.as:78
└── processItems() - [RECURSIVE] (already traced above)
```

**Handle Conditional/Loop Calls:**

Trace all possible execution paths:
```
handleButtonClick() - CompanyMaintenanceGrid.mxml:156
├── [if editMode] saveChanges() - CompanyMaintenanceGrid.mxml:178
├── [if !editMode] enterEditMode() - CompanyMaintenanceGrid.mxml:203
└── [always] updateStatus() - CompanyMaintenanceGrid.mxml:223
```

**Create a Functions List:**

After completing the trace, extract all unique functions to a list:

**Create: `./docs/entry-points/ui-features/<key>/functions-to-extract.txt`**

```
portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:creationComplete:45
portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:initializeGrid:89
portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:setupColumns:112
portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:loadCompanies:156
portal-flex/src/main/flex/com/williams/ui/company/CompanyMaintenanceGrid.mxml:bindEventHandlers:203
portal-flex/src/main/flex/com/williams/util/SecurityHelper.as:applyPermissions:67
```

Each line should contain: `file_path:function_name:line_number`

**Do NOT include Java API calls in this list** - they are terminal nodes.

This list will be used in step 5.2 to systematically extract each function body.

**Document API Boundaries:**

Track all Java API calls encountered:

**Create: `./docs/entry-points/ui-features/<key>/api-calls.txt`**

```
[API] companyService.getCompanyList() - Java REST endpoint at /service/company/list
[API] companyService.updateCompany() - Java REST endpoint at /service/company/companyMaint
[API] companyService.deleteCompany() - Java REST endpoint at /service/company/delete
[API] securityService.checkPermission() - Java REST endpoint at /service/security/checkPermission
```

This list documents the Java APIs invoked by this UI feature, which can be analyzed separately.

**Document Challenges:**

If you encounter difficulties during tracing, document them:

**Create: `./docs/entry-points/ui-features/<key>/extraction-notes.md`**

```markdown
# Extraction Notes

## Ambiguous Calls
- Line 156: Call to `process()` - multiple implementations found, traced all variants

## External Dependencies
- Line 203: Call to `mx.controls.Alert.show()` - Flex framework, not traced

## API Boundaries
- Line 234: RemoteObject call to `companyService.updateCompany()` - marked as API boundary
- Line 267: HTTPService call to `/service/company/list` - marked as API boundary

## Missing Implementations
- Line 178: Reference to `validateAddress()` - implementation not found in codebase
```

#### 5.2: Extract Function Bodies

For each meaningful function in the call tree, use the `symbol-body-extractor` subagent to extract the complete function body.

**CRITICAL**: Do NOT attempt to extract function bodies directly. Use the Task tool to launch the `symbol-body-extractor` subagent.

Use the Task tool with the following parameters:
- `subagent_type`: `"symbol-body-extractor"`
- `description`: `"Extract UI function body from source code"`
- `prompt`: Detailed instructions for the symbol-body-extractor agent

**Prompt Template**:
```
Extract the complete function body for the following UI symbol:

**Project Root**: <project_root>
**File Path**: <file_path>
**Symbol**: <component_name>.<function_name> or <function_name>
**Language**: ActionScript/MXML

Return the complete function body including:
- Function signature
- Comments/documentation
- Full implementation
- Original line numbers (start and end)

For MXML files with inline <mx:Script> blocks, extract the script content.

IMPORTANT: Return ONLY the raw code. Do NOT include:
- Summaries or descriptions
- Method behavior analysis
- Dependency lists
- Context explanations
- Structured metadata (Return Type, Method Signature, Parameters as separate sections)
- Any analysis or commentary

Output ONLY the function source code with line number references.

If disambiguation is needed, provide the list of candidates and I will select the correct one.
```

**Handling Disambiguation**: If the subagent asks you to disambiguate between multiple candidates, review the list and select the most appropriate one based on the call tree context, then make another request with the specific choice.

#### 5.3: Organize Extracted Code

Save extracted function code to:
```
./docs/entry-points/ui-features/<key>/code/
```

**Directory Structure Rules**:
1. Replicate the original source file's directory structure
2. Convert source file names to markdown files (e.g., `CompanyGrid.mxml` → `CompanyGrid.mxml.md`)
3. Group multiple functions from the same file into a single markdown file

**Example Structure**:
```
./docs/entry-points/ui-features/01-company-maintenance/code/
  └── com/
      └── williams/
          └── ui/
              └── company/
                  ├── CompanyMaintenanceGrid.mxml.md
                  └── CompanyValidator.as.md
```

#### 5.4: Format Extracted Code

Each markdown file should contain ONLY:

1. **File Header** - A single-line comment indicating the original source file path
2. **Function Blocks** - For each function from this file:
   - A markdown heading (`##`) with the function name
   - A single line indicating the original line range
   - A markdown code block with the complete function body (including comments)
   - Language-specific syntax highlighting (`actionscript` or `mxml`)

**IMPORTANT**: Do NOT include:
- Summaries or descriptions
- Method behavior analysis
- Dependency lists
- Context explanations
- Structured metadata (Return Type, Method Signature, Parameters, etc.)
- Any analysis or commentary

**Output ONLY the raw source code with line number references.**

**Example Format**:
````markdown
# Source: com/williams/ui/company/CompanyMaintenanceGrid.mxml

## creationComplete

**Lines: 45-67**

```actionscript
private function creationComplete():void {
    // Initialize grid on component creation
    initializeGrid();
    bindEventHandlers();
    applyPermissions();
}
```

## initializeGrid

**Lines: 89-134**

```actionscript
private function initializeGrid():void {
    // Setup grid columns and data provider
    setupColumns();
    loadCompanies();

    // Configure grid behavior
    companyGrid.editable = true;
    companyGrid.sortableColumns = true;
}
```

## loadCompanies

**Lines: 156-189**

```actionscript
private function loadCompanies():void {
    // Call Java API to load company list
    var remoteObject:RemoteObject = new RemoteObject("companyService");
    remoteObject.getOperation("getCompanyList").send();

    // Set result handler
    remoteObject.addEventListener(ResultEvent.RESULT, handleLoadResult);
    remoteObject.addEventListener(FaultEvent.FAULT, handleLoadFault);
}
```
````

#### 5.5: Handle Edge Cases

- **Missing Functions**: If a function cannot be found or extracted, document this in `./docs/entry-points/ui-features/<key>/extraction-notes.md`
- **External Dependencies**: Only extract functions from the project itself, not from Flex framework or external libraries
- **Duplicate Functions**: If the call tree contains the same function multiple times, only extract it once
- **Meaningfulness**: Focus on functions that contain significant UI logic; skip trivial event handlers that just call a single function
- **MXML vs ActionScript**: Handle both file types appropriately - MXML may have inline scripts or reference external AS files

### Step 6: Document API Integration Points

Since we stop at the Java API layer, it's important to document all integration points.

**Create: `./docs/entry-points/ui-features/<key>/api-integration.md`**

```markdown
# API Integration Points

This document lists all Java APIs invoked by this UI feature.

## REST Endpoints

### GET /service/company/list
- **Called from**: `loadCompanies()` in `CompanyMaintenanceGrid.mxml:156`
- **Purpose**: Load list of companies for grid display
- **Parameters**: None
- **Result Handler**: `handleLoadResult()` at line 203

### POST /service/company/companyMaint
- **Called from**: `saveCompany()` in `CompanyMaintenanceGrid.mxml:234`
- **Purpose**: Update company record
- **Parameters**: Company object with modified fields
- **Result Handler**: `handleSaveResult()` at line 267
- **Fault Handler**: `handleSaveFault()` at line 312

### DELETE /service/company/delete
- **Called from**: `deleteCompany()` in `CompanyMaintenanceGrid.mxml:356`
- **Purpose**: Delete company record
- **Parameters**: Company ID
- **Result Handler**: `handleDeleteResult()` at line 389
- **Fault Handler**: `handleDeleteFault()` at line 412

## RemoteObject Services

### companyService
- **Bean ID**: `companyService`
- **Operations Used**:
  - `getCompanyList()` - Retrieve all companies
  - `updateCompany(company)` - Update single company
  - `deleteCompany(id)` - Delete company by ID

### securityService
- **Bean ID**: `securityService`
- **Operations Used**:
  - `checkPermission(permission)` - Verify user permission

## Notes

- All API calls use Spring BlazeDS remoting
- Result/fault handlers implement standard error handling patterns
- API boundaries documented in `call-tree.txt` with `[API]` markers
```

## Summary

This command extracts UI-layer call trees that:

1. **Start** at UI entry points (MXML components, ActionScript classes)
2. **Trace through** all ActionScript/MXML UI code
3. **Stop** at Java API boundaries (RemoteObject, HTTPService, etc.)
4. **Document** API integration points for separate analysis
5. **Extract** function bodies for all UI functions
6. **Do NOT** trace into Java service/DAO implementations

The result is a complete picture of the UI-layer logic and a clear list of backend APIs it depends on, without getting into the Java implementation details.
