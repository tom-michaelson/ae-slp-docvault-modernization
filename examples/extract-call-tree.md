# Extract Call Tree Command

You are tasked with extracting the complete call tree for a single entry point. Use **Serena MCP** tools for efficient code navigation. ULTRATHINK

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

Extract the full call tree for this entry point and save it to the appropriate directory structure.

**Note**: This command extracts the call tree but does NOT validate it.

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

### Step 3: Create Output Directory Structure

Create the directory structure if it doesn't exist:
```
./docs/entry-points/<type>/<key>/
```

For example:
```
./docs/entry-points/api-endpoints/01-user-login-endpoint/
```

### Step 4: Save Entry Point Metadata

Save the original entry point payload to:
```
./docs/entry-points/<type>/<key>/metadata.json
```

This should be the exact JSON object that was provided as input:
```json
{
  "key": "01-some-entry-point",
  "location": "path/to/file.ext, ClassName.method_name() or function_name()",
  "type": "entry-point-type-slug"
}
```

### Step 5: Extract Call Tree

#### 5.1 Trace Call Tree

Trace the complete call hierarchy from the entry point through all meaningful code branches.

**IMPORTANT - Use Serena MCP Tools:**

Prefer Serena MCP tools over the Read tool for code navigation. Serena provides LSP-powered symbol lookup which is faster and more accurate:

| Task | Serena Tool | Usage |
|------|-------------|-------|
| Find symbol definition | `mcp__serena__find_symbol` | `symbol="ClassName.methodName"`, `include_body=True` |
| Find callers/references | `mcp__serena__find_referencing_symbols` | Find where a symbol is used |
| Read specific lines | `mcp__serena__read_file` | Use `start_line`/`end_line` for targeted reads |
| Switch projects | `mcp__serena__activate_project` | Switch between northwest-passage, portal, database |

**Serena Workflow for Call Tree Extraction:**

1. **Activate the correct project** first:
   ```
   mcp__serena__activate_project(project_root="./legacy/northwest-passage")
   ```

2. **Find the entry point symbol:**
   ```
   mcp__serena__find_symbol(symbol="ClassName.methodName", include_body=True)
   ```

3. **For each method call found, recursively find its definition:**
   ```
   mcp__serena__find_symbol(symbol="CalledClass.calledMethod", include_body=True)
   ```

4. **If you need to find all callers of a method:**
   ```
   mcp__serena__find_referencing_symbols(symbol="ClassName.methodName")
   ```

**Fallback to Read Tool**: Only use the Read tool if:
- Serena cannot find the symbol (e.g., dynamic/reflection calls)
- The file is not supported by Serena's LSP (e.g., SQL stored procedures)
- You need to read non-code files

**Parse the Entry Point Location:**

From the `location` field in the metadata, extract:
- File path (relative to project root)
- Class name (if applicable)
- Function/method name

**Examples:**
- `passage-java/src/rest/TariffRatesServiceRS.java, TariffRatesServiceRS.invoke()`
  - File: `passage-java/src/rest/TariffRatesServiceRS.java`
  - Class: `TariffRatesServiceRS`
  - Method: `invoke`
- `database/procedures/user_mgmt.sql, get_user_details()`
  - File: `database/procedures/user_mgmt.sql`
  - Function: `get_user_details`

**IMPORTANT - Spring REST Reflection Endpoints:**

If the metadata `notes` field contains "Spring REST reflection endpoint" or mentions "Bean ID" and "JSON-RPC style", the entry point location will reference a service method (e.g., `CompanyMaintenanceService.updateCompany()`), but the ACTUAL call tree entry point is the REST controller.

**For Spring REST Reflection Endpoints, you MUST:**

1. **Find the REST Controller:**
   - Look for the REST controller in `passage-java/src-common/com/williams/rest/` that matches the endpoint path
   - The controller will extend `APassageRestService` or `AInvokableServiceRS`
   - It will have a `@RequestMapping` annotation matching the endpoint path
   - Example: For `/service/company/companyMaint`, find `CompanyMaintenanceServiceRS.java`

2. **Start the Call Tree from the REST Controller:**
   - Entry point: `CompanyMaintenanceServiceRS.invoke()` (inherited from parent)
   - NOT `CompanyMaintenanceService.updateCompany()` (that's a child call)

3. **Trace the Full Reflection Call Chain:**
   The call chain for Spring REST reflection endpoints is:
   ```
   CompanyMaintenanceServiceRS.invoke()          (REST controller entry point)
   ├── checkSecurity()                            (APassageRestService)
   ├── invoke(InvokeValue)                        (AInvokableServiceRS)
   │   └── RemotingService.invoke()               (Reflection service)
   │       └── [reflective call to service method]
   ├── doFilterSortingPaging()                    (APassageRestService)
   └── [actual service method and its children]
   ```

4. **The service method mentioned in the metadata:**
   - Is NOT the entry point
   - IS a child call invoked via reflection by `RemotingService.invoke()`
   - Should be included in the tree as a descendant

**Example Correction:**

❌ **WRONG** (starting from service method):
```
updateCompany() - CompanyMaintenanceService.java:107
├── updateCompany() - CompanyMaintenanceDAO.java:58
└── getPrevCompany() - CompanyMaintenanceDAO.java:242
```

✓ **CORRECT** (starting from REST controller):
```
invoke() - com/williams/rest/company/companyMaint/CompanyMaintenanceServiceRS.java:28 [inherited from APassageRestService]
├── checkSecurity() - com/williams/rest/APassageRestService.java:62
├── invoke() - com/williams/rest/AInvokableServiceRS.java:25
│   └── invoke() - com/williams/flexUtils/RemotingService.java:25
│       └── [reflection] CompanyMaintenanceService.updateCompany() - CompanyMaintenanceService.java:107
│           ├── updateCompany() - CompanyMaintenanceDAO.java:58
│           └── getPrevCompany() - CompanyMaintenanceDAO.java:242
└── doFilterSortingPaging() - com/williams/rest/APassageRestService.java:37
```

**Find the Entry Point Source:**

1. Use `mcp__serena__find_symbol` with `include_body=True` to find and read the entry point
2. If the method is inherited:
   - Use `mcp__serena__find_symbol` to find the parent class method
   - Serena's LSP will resolve inherited methods automatically

**Trace Function Calls:**

From the entry point function body, identify all function/method calls:

1. **Direct function calls** - `functionName(args)`
2. **Method calls** - `object.methodName(args)` or `ClassName.staticMethod(args)`
3. **Stored procedure calls** - SQL EXECUTE, CALL statements
4. **Constructor calls** - `new ClassName(args)`

**For each called function, recursively trace using Serena:**

1. Use `mcp__serena__find_symbol(symbol="ClassName.methodName", include_body=True)` to find and read the called function
2. Identify all function calls within that function
3. Add to the tracing queue
4. Continue until all branches reach terminal nodes (functions that make no further meaningful calls)

**Fallback approach** (only if Serena cannot find the symbol):
1. Check imports/includes at the top of the file
2. Search for class definitions using Grep or Glob tools
3. Use Read tool to read the file

**What to Include:**

Trace all meaningful code:
- Business logic functions
- Service/DAO method calls
- Database operations (stored procedures, queries)
- Utility functions with significant logic
- Cross-file/cross-module calls

**What to Exclude:**

Skip trivial operations:
- Simple getters/setters without logic
- Basic property access
- External library calls (outside the project)
- Framework/infrastructure code
- Logging statements
- Basic constructors with no logic

**Track Your Progress:**

Maintain a working document as you trace to avoid infinite loops and duplication:

**Create: `./docs/entry-points/<type>/<key>/call-tree.txt`**

Use a tree structure format to document the hierarchy:

```
invoke() - passage-java/src/rest/TariffRatesServiceRS.java:45
├── processRequest() - passage-java/src/services/TariffService.java:120
│   ├── validateInput() - passage-java/src/services/TariffService.java:145
│   ├── getTariffRates() - passage-java/src/dao/TariffDAO.java:67
│   │   └── sp_get_tariff_rates() - database/procedures/tariff_mgmt.sql:234
│   └── formatResponse() - passage-java/src/util/ResponseFormatter.java:89
└── logRequest() - passage-java/src/util/AuditLogger.java:34
    └── writeAuditLog() - passage-java/src/dao/AuditDAO.java:56
```

**Include location information:**
- Function name
- File path (relative to project root)
- Line number where function begins

**Handle Multiple Branches:**

- If a function calls multiple functions, trace all branches
- Use proper tree indentation to show hierarchy
- Mark each level of depth clearly

**Handle Recursive Calls:**

If you encounter a function that has already been traced:
```
processItems() - com/example/Processor.java:45
├── processItem() - com/example/Processor.java:78
└── processItems() - [RECURSIVE] (already traced above)
```

**Handle Conditional/Loop Calls:**

Trace all possible execution paths:
```
processOrder() - com/example/OrderService.java:34
├── [if premium] calculatePremiumDiscount() - com/example/PricingService.java:67
├── [if standard] calculateStandardDiscount() - com/example/PricingService.java:89
└── [always] finalizePrice() - com/example/PricingService.java:112
```

**Create a Functions List:**

After completing the trace, extract all unique functions to a list:

**Create: `./docs/entry-points/<type>/<key>/functions-to-extract.txt`**

```
passage-java/src/rest/TariffRatesServiceRS.java:invoke:45
passage-java/src/services/TariffService.java:processRequest:120
passage-java/src/services/TariffService.java:validateInput:145
passage-java/src/dao/TariffDAO.java:getTariffRates:67
database/procedures/tariff_mgmt.sql:sp_get_tariff_rates:234
passage-java/src/util/ResponseFormatter.java:formatResponse:89
passage-java/src/util/AuditLogger.java:logRequest:34
passage-java/src/dao/AuditDAO.java:writeAuditLog:56
```

Each line should contain: `file_path:function_name:line_number`

This list will be used in step 5.2 to systematically extract each function body.

**Document Challenges:**

If you encounter difficulties during tracing, document them:

**Create: `./docs/entry-points/<type>/<key>/extraction-notes.md`**

```markdown
# Extraction Notes

## Ambiguous Calls
- Line 156: Call to `process()` - multiple implementations found, traced all variants

## External Dependencies
- Line 203: Call to `Apache Commons StringUtils.trim()` - external library, not traced

## Missing Implementations
- Line 178: Reference to `calculateTax()` - implementation not found in codebase
```

#### 5.2: Extract Function Bodies

For each meaningful function in the call tree, use the `symbol-body-extractor` subagent to extract the complete function body.

**CRITICAL**: Do NOT attempt to extract function bodies directly. Use the Task tool to launch the `symbol-body-extractor` subagent.

Use the Task tool with the following parameters:
- `subagent_type`: `"symbol-body-extractor"`
- `description`: `"Extract function body from source code"`
- `prompt`: Detailed instructions for the symbol-body-extractor agent

**Prompt Template**:
```
Extract the complete function body for the following symbol:

**Project Root**: <project_root>
**File Path**: <file_path>
**Symbol**: <class_name>.<function_name> or <function_name>
**Node ID** (if available): <node_id>

**IMPORTANT - Use Serena MCP:**
1. First, activate the project: mcp__serena__activate_project(project_root="<project_root>")
2. Use mcp__serena__find_symbol(symbol="<class_name>.<function_name>", include_body=True) to extract the function
3. Only fall back to Read tool if Serena cannot find the symbol

Return the complete function body including:
- Function signature
- Docstrings/comments
- Full implementation
- Original line numbers (start and end)

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
./docs/entry-points/<type>/<key>/code/
```

**Directory Structure Rules**:
1. Replicate the original source file's directory structure
2. Convert source file names to markdown files (e.g., `MyClass.java` → `MyClass.java.md`)
3. Group multiple functions from the same file into a single markdown file

**Example Structure**:
```
./docs/entry-points/api-endpoints/01-user-login/code/
  ├── com/
  │   └── example/
  │       ├── AuthController.java.md
  │       └── service/
  │           └── AuthService.java.md
  └── util/
      └── SecurityHelper.java.md
```

#### 5.4: Format Extracted Code

Each markdown file should contain ONLY:

1. **File Header** - A single-line comment indicating the original source file path
2. **Function Blocks** - For each function from this file:
   - A markdown heading (`##`) with the function name
   - A single line indicating the original line range
   - A markdown code block with the complete function body (including docstrings/comments)
   - Language-specific syntax highlighting in the code block

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
# Source: com/example/AuthController.java

## login

**Lines: 45-78**

```java
/**
 * Authenticates a user with username and password
 */
public LoginResponse login(LoginRequest request) {
    if (request == null) {
        throw new IllegalArgumentException("Request cannot be null");
    }

    User user = userService.findByUsername(request.getUsername());
    if (user == null || !passwordEncoder.matches(request.getPassword(), user.getPasswordHash())) {
        throw new AuthenticationException("Invalid credentials");
    }

    String token = tokenService.generateToken(user);
    return new LoginResponse(token, user);
}
```

## logout

**Lines: 120-145**

```java
/**
 * Logs out the current user session
 */
public void logout(String sessionId) {
    Session session = sessionService.findById(sessionId);
    if (session != null) {
        sessionService.invalidate(session);
        auditLog.record("User logged out: " + session.getUserId());
    }
}
```
````

#### 5.5: Handle Edge Cases

- **Missing Functions**: If a function cannot be found or extracted, document this in a `./docs/entry-points/<type>/<key>/extraction-notes.md` file
- **External Dependencies**: Only extract functions from the project itself, not from external libraries
- **Duplicate Functions**: If the call tree contains the same function multiple times, only extract it once
- **Meaningfulness**: Focus on functions that contain significant business logic; skip trivial getters/setters unless they contain important logic; skip external library calls
