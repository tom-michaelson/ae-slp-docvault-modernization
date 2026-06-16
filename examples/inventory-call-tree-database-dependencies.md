# Inventory Call Tree Database Dependencies Command

You are tasked with analyzing a call tree to extract all database dependencies (stored procedures, tables, views, functions, etc.).

## Input Parameters

You will receive the same JSON input as the extract-call-tree command:

**Entry Point Payload** - A JSON object describing the entry point:
```json
{
  "key": "01-some-entry-point",
  "location": "path/to/file.ext, ClassName.method_name() or function_name()",
  "type": "entry-point-type-slug"
}
```

Extract the following from the entry point payload:
- `key` - Unique identifier for the entry point
- `location` - Location description (file path and function/method name) - *for reference only*
- `type` - Entry point type slug

## Task Overview

Analyze the call tree to find every database object used within it, including:
- Stored procedures
- Database tables
- Database views
- Database functions (custom/user-defined functions only - NOT built-in SQL Server functions)
- Any other database objects

Output all database dependencies to a single file: `./docs/entry-points/<type>/<key>/database-dependencies.json`

**CRITICAL**: The output file MUST be a JSON array (starting with `[` and ending with `]`) containing DatabaseDependency objects. Each object must have at minimum: `type`, `key`, and `name` fields. Do NOT create alternative structures with fields like `entryPoint`, `serviceMethod`, or `databaseOperations`.

## Execution Steps

### Step 1: Locate Call Tree File

Determine which call tree file to analyze (in order of preference):

1. `./docs/entry-points/<type>/<key>/code-disambiguated.md` (if exists - preferred format)
2. `./docs/entry-points/<type>/<key>/code.md` (if exists - preferred format)
3. `./docs/entry-points/<type>/<key>/call-tree-disambiguated.json` (fallback to JSON)
4. `./docs/entry-points/<type>/<key>/call-tree.json` (fallback to JSON)

**Rationale**: The markdown code files provide the same source code in a more readable format organized by file with clear headers. The JSON format is used as a fallback for backward compatibility.

If none of these files exist, report an error and suggest running the extract-call-tree command first.

### Step 2: Load Project Root from Metadata

Read `./docs/entry-points/<type>/<key>/metadata.json` to determine which project root is being analyzed. This will be needed for resolving file paths.

### Step 3: Read Data Access Patterns Documentation

**IMPORTANT**: Before analyzing the call tree, read `./docs/data-access-patterns.md` to understand the specific database access patterns used in the Northwest Passage legacy system.

This document provides comprehensive information about:
- **iBATIS SQL Mapping**: Primary data access pattern with XML-based SQL mappings
- **Direct JDBC Access**: Connection pooling, stored procedure helpers, JSP scriptlets
- **Stored Procedure Calls**: Various invocation patterns (iBATIS, CallableStatement, etc.)
- **Transaction Management**: Spring-managed vs. manual transaction control
- **Common DAO Patterns**: Specific examples from the codebase with file references

The patterns documented there are specific to this codebase and will help you accurately identify database dependencies. Pay special attention to:
- How iBATIS namespace.statementId references map to XML files
- The PassageClientDaoSupport base class pattern
- Portal application's direct JDBC patterns
- Dynamic SQL construction patterns

### Step 4: Analyze Call Tree for Database Dependencies

#### Analysis Strategy

The call tree is available in two formats:

**A. Markdown Code Format (Preferred)**

The markdown files (`code.md` or `code-disambiguated.md`) contain:
- Source code organized by file with headers
- Clear file path headers (e.g., `## legacy/northwest-passage/src/main/java/com/example/Service.java`)
- Function/method code blocks with their names as subheaders
- Deduplicated source code (each function appears once)

To analyze the markdown format:
1. Parse the file to extract code blocks and their associated file paths
2. For each code block, extract the file path from the markdown header
3. Analyze the code block for database access patterns
4. Track the file path as the location (line numbers may not be available in markdown; use the file path only)

**B. JSON Format (Fallback)**

The JSON structure contains:
- **Nodes**: Functions/methods with their source code in the `body` field
- **Edges**: Relationships between functions (CALLS, POSSIBLE_CALL, etc.)

To analyze the JSON format:
1. Extract the `body` field (function source code) from each node
2. Extract the `file_path` and `line_number` fields for location tracking
3. Analyze the body for database access patterns

**Common Analysis for Both Formats**:
- Scan source code for database access patterns (detailed below)
- Track locations where database objects are referenced
- Deduplicate findings across all code analyzed

#### When to Use legacy-code-searcher Subagent

The call tree provides function bodies, but you may need additional codebase context in these scenarios:

**Use the legacy-code-searcher subagent when:**

1. **Missing Configuration/Constants**: Database object names are referenced via constants or configuration
   - Example: `String tableName = ConfigConstants.USER_TABLE;`
   - Search for: The constant definition to find the actual table name

2. **Interface/Abstract Implementations**: The call tree shows an interface method, but the actual SQL is in implementations
   - Example: Call tree shows `UserRepository.findById()` but not the implementation
   - Search for: Concrete implementations or ORM mapping files

3. **ORM Mapping Files**: Database mappings are in XML or annotation files not included in the call tree
   - Example: MyBatis mapper XML files, Hibernate HBM files
   - Search for: Mapper files associated with DAO/Repository classes

4. **Inherited Database Access**: Base classes or mixins contain database logic not captured in the call tree
   - Example: A base repository class with common CRUD operations
   - Search for: Parent class definitions and their database access patterns

5. **Dynamic Schema/Object Resolution**: Code references schema registries or metadata tables
   - Example: `String schema = SchemaResolver.getSchema(tenantId);`
   - Search for: Schema resolution logic or metadata tables

6. **External Configuration**: Database object names come from properties files, YAML, or environment variables
   - Example: `@Value("${database.tableName}")`
   - Search for: Configuration files referenced in the code

7. **Database DDL Verification**: Verify database object types or get additional context about database objects
   - Example: You found a reference to `dbo.user_summary` but aren't sure if it's a table or view
   - Search for: The object definition in `./legacy/database` directory (DDL scripts, schema files)
   - This helps resolve ambiguity about object types and can reveal additional dependencies

**Example Usage:**

**For application code searches:**
```
Use the Task tool with:
- subagent_type: "legacy-code-searcher"
- description: "Find UserRepository implementations"
- prompt: "I'm analyzing database dependencies and found a reference to UserRepository.findByUsername()
           but the call tree doesn't include the implementation. Search the codebase at
           ./legacy/northwest-passage to find:
           1. All classes that implement or extend UserRepository
           2. The actual SQL queries or ORM mappings used
           Return the file paths and relevant code snippets showing the database access."
```

**For database DDL verification:**
```
Use the Task tool with:
- subagent_type: "legacy-code-searcher"
- description: "Verify user_summary is table or view"
- prompt: "I found a reference to 'dbo.user_summary' in the application code but cannot determine
           if it's a table or view. Search the database DDL in ./legacy/database to find:
           1. The CREATE statement for user_summary
           2. Whether it's defined as a table, view, or other object type
           3. Any dependencies it might have (e.g., tables referenced in a view definition)
           Return the file path and relevant DDL showing the object definition."
```

**Important Guidelines:**

- **Be Specific**: Provide the project root (application code or `./legacy/database` for DDL) and clear search criteria
- **Targeted Searches**: Search for specific patterns, not broad concepts
- **Document Findings**: Add notes to the dependency entry indicating it was found via additional search
- **One Search at a Time**: If you need multiple searches, consider whether they can run in parallel
- **Time vs. Accuracy Trade-off**: Use the subagent when the additional context is likely to reveal missed dependencies, not for every minor uncertainty
- **Database DDL is searchable**: The `./legacy/database` directory contains schema definitions that can help resolve ambiguities about database object types

#### Database Access Patterns to Detect

**Reference**: `./docs/data-access-patterns.md` contains comprehensive pattern documentation specific to this codebase.

**Primary Patterns for Northwest Passage System**:

1. **iBATIS SQL Mapping** (most common):
   - Method calls like `getSqlMapClientTemplate().queryForList("namespace.statementId", params)`
   - References point to XML files co-located with DAO classes
   - Look for namespace.statementId patterns in Java code
   - Find corresponding `<select>`, `<insert>`, `<update>`, `<delete>`, `<procedure>` tags in XML files

2. **Stored Procedure Calls**:
   - iBATIS: `<procedure>` tags with `{call dbo.proc_name(...)}`
   - JDBC: `CallableStatement cs = connection.prepareCall("{call dbo.my_proc(?, ?)}")`
   - Generic DAO: String-based procedure name passed to `doProcedureCall()`

3. **Direct SQL in XML Files**:
   - Table references in `<select>`, `<insert>`, `<update>`, `<delete>` statements
   - JOIN clauses, FROM clauses, INTO clauses
   - Schema typically prefixed as `dbo.table_name`

4. **Direct JDBC (Portal Application)**:
   - `CallableStatement` with SQL strings
   - Inline SQL in JSP scriptlets
   - String variables containing SQL queries

5. **Dynamic SQL Construction**:
   - String concatenation: `"dbo." + prefix + "_process"`
   - String.format() with table/procedure names
   - Mark these as `"dynamic": true`

**Detection Strategy**:

1. Scan for iBATIS template method calls and extract namespace.statementId
2. When you find a reference to an XML mapping, note that you need to search for the XML file
3. Look for JDBC CallableStatement patterns
4. Search for SQL keywords (SELECT, FROM, INSERT, UPDATE, DELETE, EXEC, CALL) in string literals
5. Extract database object names from SQL statements
6. Mark dynamic construction patterns appropriately

#### Excluding Built-in SQL Server Functions

**CRITICAL**: When capturing database functions, ONLY include custom/user-defined functions. DO NOT include built-in SQL Server functions.

**Common Built-in Functions to EXCLUDE**:

**Date/Time Functions**:
- `GETDATE`, `GETUTCDATE`, `SYSDATETIME`, `SYSDATETIMEOFFSET`, `SYSUTCDATETIME`
- `DATEADD`, `DATEDIFF`, `DATEDIFF_BIG`, `DATENAME`, `DATEPART`, `DATEFROMPARTS`, `DATETIMEFROMPARTS`
- `EOMONTH`, `ISDATE`, `YEAR`, `MONTH`, `DAY`

**String Functions**:
- `LEN`, `LEFT`, `RIGHT`, `SUBSTRING`, `CHARINDEX`, `PATINDEX`
- `CONCAT`, `CONCAT_WS`, `REPLACE`, `REPLICATE`, `REVERSE`, `STUFF`
- `LTRIM`, `RTRIM`, `TRIM`, `UPPER`, `LOWER`
- `CHAR`, `NCHAR`, `ASCII`, `UNICODE`, `STR`

**Conversion Functions**:
- `CAST`, `CONVERT`, `TRY_CAST`, `TRY_CONVERT`, `PARSE`, `TRY_PARSE`
- `FORMAT`, `STR`

**Aggregate Functions**:
- `SUM`, `AVG`, `COUNT`, `COUNT_BIG`, `MIN`, `MAX`
- `STDEV`, `STDEVP`, `VAR`, `VARP`
- `GROUPING`, `GROUPING_ID`

**Mathematical Functions**:
- `ABS`, `CEILING`, `FLOOR`, `ROUND`, `POWER`, `SQRT`, `SQUARE`
- `EXP`, `LOG`, `LOG10`, `SIGN`, `RAND`
- `PI`, `SIN`, `COS`, `TAN`, `ASIN`, `ACOS`, `ATAN`, `ATN2`

**Logical/Conditional Functions**:
- `ISNULL`, `COALESCE`, `NULLIF`, `IIF`, `CHOOSE`

**System Functions**:
- `NEWID`, `NEWSEQUENTIALID`, `SCOPE_IDENTITY`, `IDENT_CURRENT`, `@@IDENTITY`
- `USER_NAME`, `SUSER_NAME`, `SYSTEM_USER`, `SESSION_USER`, `CURRENT_USER`
- `DB_NAME`, `OBJECT_ID`, `OBJECT_NAME`, `SCHEMA_NAME`, `TYPE_NAME`
- `@@ROWCOUNT`, `@@ERROR`, `@@TRANCOUNT`

**Ranking Functions**:
- `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`

**Detection Guidelines**:

1. **Case-insensitive matching**: Built-in functions can appear in any case (`GETDATE`, `GetDate`, `getdate`)
2. **Schema prefix check**: Custom functions typically have schema prefixes (e.g., `dbo.calculate_discount`), while built-ins rarely do
3. **Context matters**: If a function appears without a schema prefix and matches a known built-in name, exclude it
4. **When in doubt**: If you're unsure whether a function is built-in or custom:
   - Check if it has a schema prefix (e.g., `dbo.`, `custom.`) - likely custom
   - Search the database DDL in `./legacy/database` to verify if it's user-defined
   - If you cannot verify and it has no schema prefix, assume it's built-in and exclude it

**Examples**:

✅ **INCLUDE (Custom Functions)**:
- `dbo.calculate_discount(price, discount_pct)` - has schema prefix
- `custom.get_customer_status(customer_id)` - has schema prefix
- `fn_compute_tax(amount)` - naming convention suggests custom function (fn_ prefix)

❌ **EXCLUDE (Built-in Functions)**:
- `GETDATE()` - built-in date function
- `CONVERT(varchar, date_column, 101)` - built-in conversion function
- `DATEADD(day, -1, start_date)` - built-in date arithmetic
- `ISNULL(column, 0)` - built-in null handling
- `LEN(name)` - built-in string function

#### Handling Ambiguity

When you encounter ambiguous cases:
- **Unknown schema**: If schema is not specified, record without schema prefix (e.g., "users" instead of "dbo.users")
- **Unclear type**: If you cannot determine if something is a table vs. view:
  - Consider searching the database DDL in `./legacy/database` using the legacy-code-searcher subagent
  - If unable to resolve, default to "table" and add a note explaining the ambiguity
- **Dynamic names**: For dynamic construction, record as much as possible with `"dynamic": true` flag
- **Parameterized queries**: Focus on the structure, not the parameter values

### Step 5: Deduplicate and Normalize Dependencies

After collecting all dependencies:

1. **Normalize names**:
   - Convert to lowercase for comparison
   - Handle schema prefixes consistently (keep if present, don't add if absent)
   - Remove quotes and brackets: `[dbo].[users]` → `dbo.users`

2. **Deduplicate**:
   - Same database object found in multiple locations? Keep all locations but consolidate into one entry
   - Merge duplicate entries with same `type` and `name`

3. **Generate keys**:
   - Create URL-safe keys: `dbo.my_stored_proc` → `my-stored-proc`
   - Ensure keys are unique within the dependency list

### Step 6: Create Output Structure

Create `./docs/entry-points/<type>/<key>/database-dependencies.json` as **an array of DatabaseDependency objects**:

```json
[
  {
    "type": "stored-procedure",
    "key": "get-user-by-id",
    "name": "dbo.get_user_by_id",
    "locations": [
      "./legacy/northwest-passage/src/main/java/com/example/UserService.java:45"
    ],
    "dynamic": false,
    "notes": []
  },
  {
    "type": "table",
    "key": "users",
    "name": "dbo.users",
    "locations": [
      "./legacy/northwest-passage/src/main/java/com/example/UserRepository.java:23",
      "./legacy/northwest-passage/src/main/java/com/example/UserService.java:67"
    ],
    "dynamic": false,
    "notes": []
  },
  {
    "type": "stored-procedure",
    "key": "dynamic-process-proc",
    "name": "dbo.<dynamic>_process",
    "locations": [
      "./legacy/northwest-passage/src/main/java/com/example/ProcessService.java:89"
    ],
    "dynamic": true,
    "notes": [
      "Stored procedure name is constructed at runtime: 'dbo.' + prefix + '_process'"
    ]
  },
  {
    "type": "view",
    "key": "user-summary",
    "name": "dbo.vw_user_summary",
    "locations": [
      "./legacy/northwest-passage/src/main/java/com/example/ReportService.java:12"
    ],
    "dynamic": false,
    "notes": []
  },
  {
    "type": "function",
    "key": "calculate-discount",
    "name": "dbo.calculate_discount",
    "locations": [
      "./legacy/northwest-passage/src/main/java/com/example/PricingService.java:34"
    ],
    "dynamic": false,
    "notes": [
      "Custom user-defined function for calculating discounts"
    ]
  }
]
```

**CRITICAL OUTPUT FORMAT REQUIREMENTS**:

1. **The output MUST be a JSON array** at the root level (starting with `[` and ending with `]`)
2. **Each element in the array MUST be a DatabaseDependency object** conforming to the schema below
3. **DO NOT wrap the array in any other object** (no `entryPoint`, `serviceMethod`, `databaseOperations`, etc.)
4. **DO NOT create alternative structures** - the output must match the schema exactly

**CRITICAL**: The file `database-dependencies.json` MUST be a JSON array where each element adheres to this DatabaseDependency schema:

**JSON Schema for DatabaseDependency** (each array element must conform to this):
```json
{
  "description": "Represents a discovered database dependency in the codebase.",
  "properties": {
    "type": {
      "description": "Type of database object",
      "examples": ["table", "view", "stored-procedure", "function", "trigger"],
      "title": "Type",
      "type": "string"
    },
    "key": {
      "description": "Unique identifier for the database dependency",
      "examples": ["pt-co-xref", "customer-table", "order-view"],
      "title": "Key",
      "type": "string"
    },
    "name": {
      "description": "Fully-qualified name of the database object, including the schema (if known)",
      "examples": ["dbo.PT_CO_XREF", "my_schema.CUSTOMER", "xyz.ORDER_VIEW"],
      "title": "Name",
      "type": "string"
    },
    "locations": {
      "description": "List of file paths and line numbers where this dependency is referenced",
      "examples": [
        ["./legacy/northwest-passage/passage-java/src-common/com/williams/infrastructure/pointMaintenance/dao/PointMaintenance
.xml:373-381"]
      ],
      "items": {"type": "string"},
      "title": "Locations",
      "type": "array"
    },
    "dynamic": {
      "default": false,
      "description": "Whether the name of the dependency is dynamically referenced, for example if a stored procedure name is constructed at runtime: 'dbo.' + prefix + '_process'",
      "title": "Dynamic",
      "type": "boolean"
    },
    "notes": {
      "description": "List of additional notes or observations about the dependency",
      "examples": [
        [
          "Point Company Cross-Reference table",
          "iBATIS delete statement with composite key: PT_ID_NBR, CO_ID, CO_ROLE_CD, EFF_START_DATE, EFF_END_DATE",
          "Found via additional search: XML mapping file co-located with DAO class",
          "Custom user-defined function for calculating discounts",
          "Stored procedure name is constructed at runtime: 'dbo.' + prefix + '_process'"
        ]
      ],
      "items": {"type": "string"},
      "title": "Notes",
      "type": "array"
    }
  },
  "required": ["type", "key", "name"],
  "title": "DatabaseDependency",
  "type": "object"
}
```

**IMPORTANT: The complete file structure is an ARRAY of these objects**:

```json
[
  {
    "type": "...",
    "key": "...",
    "name": "...",
    "locations": [...],
    "dynamic": false,
    "notes": [...]
  },
  {
    "type": "...",
    "key": "...",
    "name": "...",
    "locations": [...],
    "dynamic": false,
    "notes": [...]
  }
]
```

**DO NOT** create output like this (WRONG):
```json
{
  "entryPoint": "...",
  "serviceMethod": "...",
  "databaseOperations": [...]
}
```

**Example: Converting database operations to dependency array**

If you found these database operations:
- Query `infrastructureBiz.retrieveBARequestCompanyInfoSaved` accesses table `company_ba_rqst_edit`
- Query `infrastructureBiz.retrieveBARequestCompanyInfo` accesses table `ba_rqst_company_info`

The correct output would be:
```json
[
  {
    "type": "table",
    "key": "company-ba-rqst-edit",
    "name": "company_ba_rqst_edit",
    "locations": [
      "./legacy/northwest-passage/passage-java/src-common/com/williams/infrastructureBiz/dao/Infrastructure.xml:2072"
    ],
    "dynamic": false,
    "notes": [
      "iBATIS query: infrastructureBiz.retrieveBARequestCompanyInfoSaved",
      "Retrieve saved BA request company information edits"
    ]
  },
  {
    "type": "table",
    "key": "ba-rqst-company-info",
    "name": "ba_rqst_company_info",
    "locations": [
      "./legacy/northwest-passage/passage-java/src-common/com/williams/infrastructureBiz/dao/Infrastructure.xml:1974"
    ],
    "dynamic": false,
    "notes": [
      "iBATIS query: infrastructureBiz.retrieveBARequestCompanyInfo",
      "Retrieve original BA request company information",
      "Conditionally called if retrieveBARequestCompanyInfoSaved returns null"
    ]
  }
]
```

#### Field Descriptions

- **type**: One of: `"stored-procedure"`, `"table"`, `"view"`, `"function"`, `"unknown"`
  - **IMPORTANT**: `"function"` type is for custom/user-defined database functions ONLY - NOT for built-in SQL Server functions like `GETDATE`, `CONVERT`, `DATEADD`, etc.
- **key**: URL-safe identifier (lowercase, hyphenated)
- **name**: The actual database object name as it appears in code (preserve casing and schema)
- **locations**: Array of file paths and optionally line numbers where this dependency is used
  - When analyzing markdown format: May contain only file paths (line numbers not always available)
  - When analyzing JSON format: Will typically include both file path and line number (e.g., `path/to/file.java:45`)
- **dynamic**: Boolean indicating if the name is constructed dynamically at runtime
- **notes**: Array of strings with additional context (especially for dynamic dependencies and additional searches performed)

**Note on Additional Searches**: If a dependency was found or resolved using the legacy-code-searcher subagent, add a note like:
- `"Resolved via additional search: found constant definition in config/Constants.java"`
- `"Found via interface implementation search in repository/UserRepositoryImpl.java"`
- `"Type verified via database DDL: confirmed as VIEW in database/schemas/dbo/views/user_summary.sql"`

### Step 7: Validate Output

After creating the `database-dependencies.json` file, validate it using the validation tool:

```bash
node .claude/tools/validate-database-dependencies.js ./docs/entry-points/<type>/<key>/database-dependencies.json
```

**Validation Requirements**:
- The file must pass validation before the task is considered complete
- Fix any errors reported by the validator
- Review warnings and address if appropriate

**Common Validation Errors**:
- Root element is not an array (wrapped in object with `entryPoint`, `databaseOperations`, etc.)
- Missing required fields (`type`, `key`, `name`)
- Duplicate keys
- Invalid field types (e.g., `locations` not an array)

**Iterating on Validation**:
1. Run the validator
2. If errors are reported, fix them and re-validate
3. Continue until the validator reports success
4. Review any warnings and address as needed

### Step 8: Handle Edge Cases

**No Call Tree Found**:
- Report an error with clear instructions to run extract-call-tree first
- Provide the exact command the user should run

**Empty Call Tree**:
- Create an empty database-dependencies.json: `[]`
- Note in your output summary that no dependencies were found

**No Database Access**:
- Create an empty database-dependencies.json: `[]`
- Note in your output summary that the call tree does not appear to access any database objects

**Parsing Errors**:
- For markdown format: If you cannot parse a section, skip it but note it in your output summary
- For JSON format: If you cannot parse a node's body, skip it but note it in your output summary
- Do not fail the entire analysis due to one unparseable section/node

## Output Summary

At completion, provide a summary showing:
- Entry point key and type
- Call tree file analyzed (specify format and variant):
  - Format: Markdown (code.md/code-disambiguated.md) or JSON (call-tree.json/call-tree-disambiguated.json)
  - Variant: Disambiguated or regular
- Total code sections/nodes analyzed
- Total dependencies found (breakdown by type)
- Dynamic dependencies found (count)
- Output file path:
  - `./docs/entry-points/<type>/<key>/database-dependencies.json`
- Validation result: Pass/Fail (with error count if failed)
- Any warnings or issues encountered

**CRITICAL REMINDER**: The output file MUST be a JSON array of DatabaseDependency objects. Each dependency must have at minimum: `type`, `key`, and `name` fields. Do NOT create a wrapper object with fields like `entryPoint`, `serviceMethod`, or `databaseOperations`.

**Note**: If the legacy-code-searcher subagent was used to resolve dependencies, this information is captured in the "notes" field of individual dependencies.

## Important Notes

### Prerequisites

**CRITICAL**: Read `./docs/data-access-patterns.md` before beginning analysis (as specified in Step 3). This document contains:
- Comprehensive database access pattern documentation for Northwest Passage
- Technology stack details (iBATIS 2.x, Spring JDBC, direct JDBC)
- Code examples with file references
- Common DAO patterns and anti-patterns
- Configuration file locations

Understanding these patterns is essential for accurate dependency detection.

### Analysis Depth

- **Analyze all code sections**: Whether working with markdown or JSON format, examine all functions/methods provided, not just the entry point
- **Follow the full tree**: Dependencies may appear deep in the call stack
- **Format agnostic**: The analysis approach is the same regardless of whether you're working with markdown or JSON files
- **Prefer markdown when available**: Markdown files are easier to parse and more readable, but the JSON fallback provides additional metadata (line numbers, graph structure)
- **Include all available code**: Analyze all source code provided in the file, whether organized by markdown headers or JSON nodes
- **Go beyond the call tree**: Use the legacy-code-searcher subagent when you need additional codebase context (see Step 3 for specific scenarios)
- **Verify with database DDL**: The database schema definitions are available in `./legacy/database` and can be searched to resolve ambiguities about object types or to discover additional context

### Pattern Recognition

- **Be generous with detection**: It's better to over-report potential dependencies than miss them
- **Mark uncertainty**: Use the "notes" field to indicate when you're not 100% certain
- **Learn from context**: Variable names like `tableName`, `procName`, `viewName` are strong hints
- **Filter built-in functions**: ALWAYS exclude built-in SQL Server functions (GETDATE, CONVERT, DATEADD, etc.) - only capture custom/user-defined functions

### Dynamic Dependencies

- **Record what you can**: Even partial information is valuable (e.g., "dbo.<dynamic>_process")
- **Document the pattern**: Explain in notes how the name is constructed
- **Mark clearly**: Always set `"dynamic": true` for runtime-constructed names

### Performance

- **Efficient parsing**: Work directly from the call tree file (markdown or JSON); don't read original source files
- **Markdown is more efficient**: The markdown format is typically easier and faster to parse than JSON for text analysis
- **Reasonable limits**: If a call tree has thousands of functions, you may need to process in batches
- **Progress feedback**: For large call trees, provide progress updates

### Technology-Specific Notes

**For Northwest Passage Legacy System**:

The system uses **iBATIS 2.x** (not JPA/Hibernate) as documented in `./docs/data-access-patterns.md`. Key technologies:
- **iBATIS SQL Mapping**: Primary data access framework
- **Spring JDBC**: Transaction management
- **Direct JDBC**: Portal application and some legacy code
- **No ORM**: Manual object-relational mapping

When analyzing this codebase:
1. Focus on iBATIS patterns (namespace.statementId references)
2. Look for XML mapping files co-located with DAO classes
3. Check for PassageClientDaoSupport base class usage
4. Watch for stored procedure calls via CallableStatement
5. Be aware of JSP scriptlets with embedded SQL (portal application)

**For Other Technology Stacks** (if analyzing different codebases):
- **Java**: JDBC, JPA, Hibernate, MyBatis, Spring Data
- **C#**: ADO.NET, Entity Framework, Dapper
- **Python**: SQLAlchemy, Django ORM, psycopg2
- **JavaScript/TypeScript**: Sequelize, TypeORM, Knex, raw SQL

Always refer to the data access patterns documentation if available for the specific system being analyzed.
