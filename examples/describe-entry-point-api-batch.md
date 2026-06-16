# Describe Entry Point - API & Batch

Create a detailed functional description of an API endpoint or batch job entry point by analyzing its code, call tree, database dependencies, and business logic.

## Common Foundation

@describe-entry-point-common.md

## Usage

```
/describe-entry-point-api-batch path: <path-to-entry-point-analysis-folder>
```

**Examples:**
```
/describe-entry-point-api-batch path: ./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/
/describe-entry-point-api-batch path: ./docs/entry-points/batch-jobs/nightly-data-sync/
```

## API & Batch-Specific Context

This command is for analyzing **backend entry points** including:
- REST API endpoints
- JSON-RPC services
- Scheduled batch jobs
- Event handlers/listeners
- Message queue consumers

The analysis focuses on **server-side processing, database operations, and system integrations**.

## Input Structure

The API/Batch entry point analysis folder contains:

```
{entry_point_analysis}/
├── metadata.json              # Entry point metadata (key, location, type, notes)
├── call-tree.txt              # Complete call tree from entry point
├── code/                      # Extracted code tree matching call-tree.txt
│   └── [package/file.java.md] # Markdown files with extracted function bodies
├── database-dependencies.json # Database objects used (tables, stored procs)
└── database-dependencies/     # (Optional) Stored procedure sub-analyses
    └── {proc-name}/           # Same structure as parent for each proc
        ├── call-tree.txt
        ├── code/
        └── ...
```

## Output Structure

The command creates files in the entry point analysis folder:

**During Analysis (In Progress)**:
```
{entry_point_analysis}/functional-description.in-progress.md
```

**After Completion**:
```
{entry_point_analysis}/functional-description.md
```

**Status Indication**:
- `.in-progress.md` suffix indicates analysis is actively running or crashed mid-way
- `.md` (no suffix) indicates analysis completed successfully
- This allows easy identification of incomplete analyses for recovery or restart

The markdown file contains the complete functional analysis following the template defined below.

## Analysis Process

### Phase 1: Context Gathering and Initial Setup

1. **Read metadata.json** to understand entry point type, location, and key context
2. **Read call-tree.txt** to understand the complete execution flow
3. **Read database-dependencies.json** to identify all database interactions
4. **Scan code/ directory** to understand available extracted functions
5. **CHECK SHARED PATTERNS**: Read `docs/shared-functional-descriptions/index.md`
   - Determine if this entry point follows a documented shared pattern
   - Note which steps are shared vs. unique
   - Plan to reference shared documentation instead of duplicating
6. **Create initial todo list** for tracking analysis progress
7. **WRITE: Create functional-description.in-progress.md with template structure**
8. **WRITE: Executive Summary section**
   - **If shared pattern detected**: Mention the pattern in the summary

### Phase 2: Code Analysis and Input/Output Documentation

1. **Read extracted code files** from the code/ directory in call-tree order
2. **ANALYZE AND WRITE: Identify all inputs**
   - Method parameters and their types
   - Database SELECT queries and the data they retrieve
   - File read operations
   - External API/service calls for data retrieval
   - Session/context variables accessed
   - **WRITE to functional-description.in-progress.md**: Update Inputs section as discovered
   - **If shared pattern detected**: Reference shared Context/Session Inputs
3. **ANALYZE AND WRITE: Identify all outputs**
   - Return values and their types
   - Database INSERT/UPDATE/DELETE operations
   - File write operations
   - External API/service calls for data submission
   - Side effects (emails sent, events published, etc.)
   - **WRITE to functional-description.in-progress.md**: Update Outputs section as discovered
4. **Map business logic** (collect for later workflow writing)
5. **WRITE: Key Business Rules section** as discovered
6. **WRITE: Data Validation Rules section** as discovered
7. **WRITE: Transaction Boundaries section** if transaction logic found
8. **WRITE: Security Considerations section** if security logic found

### Phase 3: Database Dependency Analysis and Documentation

1. **For each database dependency** in database-dependencies.json:
   - Identify whether it's a table, view, stored procedure, or function
   - Determine the operation type (SELECT, INSERT, UPDATE, DELETE, EXECUTE)
   - Extract parameters passed to stored procedures/functions
   - Understand the data being read or written
   - **WRITE to functional-description.in-progress.md**: Add entry to Database Dependencies Detail section
   - **WRITE incrementally**: Complete each database object documentation before moving to next
2. **If database-dependencies/ subfolder exists**:
   - Recursively analyze stored procedure call trees
   - Incorporate stored procedure inputs/outputs into main analysis
   - Document nested database operations
   - **WRITE**: Add stored procedure details with references to their sub-analysis folders
3. **VERIFY**: Database Dependencies Detail section is complete before proceeding

### Phase 4: Workflow Synthesis and Documentation

**CRITICAL: Write each workflow as you complete it!**

**CRITICAL: If this entry point follows a shared pattern, reference the shared steps instead of duplicating them!**

1. **Identify major execution paths**:
   - Main happy path workflow
   - Alternative paths based on significant conditional logic
   - Error handling and exception paths
2. **For EACH workflow** (write one at a time):
   - **If shared pattern detected**: Reference shared steps with links
   - **If no shared pattern**: Create full step-by-step business logic narrative
   - Note decision points and their business meaning
   - Document data transformations at each step
   - Include database operations in context
   - **WRITE to functional-description.in-progress.md**: Complete workflow BEFORE moving to next
3. **VERIFY**: All workflows written before proceeding to use cases

### Phase 5: Use Case Extraction and Documentation

1. **Identify business use cases** from workflow analysis
2. **Frame as user stories** where appropriate
3. **WRITE to functional-description.in-progress.md**: Add each use case
4. **WRITE: Integration Points section**
5. **WRITE: Analysis Notes section**

### Phase 6: Final Review and Completion

1. **Final review**: Verify entire document for completeness
2. **RENAME FILE**: `mv functional-description.in-progress.md functional-description.md`
3. **Mark todo as completed**

## API & Batch-Specific Output Template

```markdown
# Functional Description: [Entry Point Name]

> **Entry Point**: [key from metadata.json]
> **Location**: [location from metadata.json]
> **Type**: [API | Batch | Event Handler]

## Executive Summary

[2-3 paragraph overview of this entry point's purpose, key functionality, and business context]

## Inputs

### Method Parameters

| Parameter | Type | Description | Required | Business Meaning |
|-----------|------|-------------|----------|------------------|
| param1 | String | Description | Yes | What this represents in business terms |
| param2 | Object | Description | No | Business significance |

### Database Inputs

| Operation | Database Object | Purpose | Data Retrieved |
|-----------|----------------|---------|----------------|
| SELECT | TABLE_NAME | Description | What data and why |
| EXECUTE | SP_GET_DATA | Description | What stored proc returns |

### File Inputs

| File Path/Pattern | Format | Purpose | When Used |
|-------------------|--------|---------|-----------|
| /path/to/file | CSV | Description | Conditions |

### External System Inputs

| System/API | Endpoint/Method | Data Retrieved | Purpose |
|------------|-----------------|----------------|---------|
| SystemName | /api/endpoint | Description | Why called |

### Context/Session Inputs

| Variable/Attribute | Source | Purpose |
|-------------------|--------|---------|
| userId | Session | Current user context |
| tenantId | Context | Multi-tenant isolation |

## Outputs

### Return Values

| Type | Description | Business Meaning | Conditions |
|------|-------------|------------------|------------|
| String | Description | What success/failure means | When returned |
| Object | Description | What data represents | Usage |

### Database Outputs

| Operation | Database Object | Data Written | Business Impact | Conditions |
|-----------|----------------|--------------|-----------------|------------|
| INSERT | TABLE_NAME | Description | Why important | When occurs |
| UPDATE | TABLE_NAME | Fields modified | Business effect | Conditions |
| DELETE | TABLE_NAME | What removed | Impact | When happens |
| EXECUTE | SP_UPDATE_DATA | Description | Effect | Conditions |

### File Outputs

| File Path/Pattern | Format | Content | Purpose | Conditions |
|-------------------|--------|---------|---------|------------|
| /path/to/output | JSON | Description | Why created | When |

### External System Outputs

| System/API | Endpoint/Method | Data Sent | Purpose | Conditions |
|------------|-----------------|-----------|---------|------------|
| SystemName | /api/endpoint | Description | Why called | When |

### Side Effects

| Effect | Description | Business Impact | Conditions |
|--------|-------------|-----------------|------------|
| Email sent | Notification email | Alerts user | After success |
| Event published | Domain event | Triggers downstream | On change |
| Cache invalidated | Clear cache | Ensures consistency | Always |

## Workflows

### Workflow 1: [Primary Business Scenario Name]

**Use Case**: [High-level business purpose for this workflow]

**Actors**: [Who uses/triggers this workflow]

**Steps**:

1. **[Step Name]** - [Detailed description of business logic]
   - **Code Reference**: [file.java:123]
   - **Business Rule**: [Specific rule applied]
   - **Validation**: [Any validation logic]
   - **Data**: [Data involved in this step]
   - **Branch**: If [condition], then [alternative action]

2. **[Step Name]** - [Detailed description]
   - **Database Operation**: SELECT from [table] to [purpose]
   - **Transformation**: [How data is transformed]
   - **Business Logic**: [Key business rule]
   - **Exception Handling**: If [error], then [action]

3. **[Step Name]** - [Detailed description]
   - **Calculation**: [Business calculation performed]
   - **Validation Rule**: [Specific validation]
   - **Side Effect**: [Email/event/etc.]

[Continue for all steps in this workflow]

**Outcome**: [Business outcome when workflow completes successfully]

**Error Conditions**:
- [Error scenario 1]: [How handled]
- [Error scenario 2]: [How handled]

---

### Workflow 2: [Alternative Business Scenario Name]

[Same structure as Workflow 1]

---

### Workflow 3: [Error Handling Path]

[Same structure as Workflow 1]

## Use Cases

### UC-1: [Use Case Title]

**Description**: [High-level business use case description]

**User Story**: As a [role], I need to [action] so that [business value]

**Workflow**: Workflow 1 (reference above)

**Frequency**: [How often this occurs - if known]

**Business Priority**: [High/Medium/Low - if apparent from code/context]

---

## Database Dependencies Detail

### Table: [TABLE_NAME]

**Operations**: SELECT, UPDATE

**Business Purpose**: [What this table represents]

**Key Columns Used**:
- `COLUMN_1`: [Business meaning]
- `COLUMN_2`: [Business meaning]

**Access Patterns**:
- **Read**: [When and why table is queried]
- **Write**: [When and why table is modified]

**Relationships**: [Related tables and foreign keys]

---

### Stored Procedure: [SP_NAME]

**Purpose**: [Business function of this stored procedure]

**Parameters**:
- `@param1`: [Type] - [Business meaning]
- `@param2`: [Type] - [Business meaning]

**Returns**: [What the stored procedure returns]

**Called From**: [Which step in workflows]

**Nested Operations**: [If this proc calls others]

**Note**: See `database-dependencies/[sp-name]/` for detailed call tree analysis

---

## Key Business Rules

[Bulleted list of critical business rules discovered in the analysis]

1. [Business rule 1 with code reference]
2. [Business rule 2 with code reference]
3. ...

## Data Validation Rules

[Bulleted list of validation logic]

1. [Validation rule 1 with code reference]
2. [Validation rule 2 with code reference]
3. ...

## Transaction Boundaries

[Description of transaction scope and consistency guarantees]

- **Transaction Start**: [Where transaction begins]
- **Transaction Scope**: [What operations are included]
- **Commit Conditions**: [When transaction commits]
- **Rollback Conditions**: [When transaction rolls back]

## Security Considerations

### Authentication

- **Required**: [Yes/No]
- **Method**: [Session, Token, API Key, etc.]
- **Validation Point**: [Where in code]

### Authorization

- **Permission Required**: [Permission name/code]
- **Check Location**: [Where in code]
- **Failure Behavior**: [What happens if unauthorized]

### Data Access Controls

- **Row-Level Security**: [If applicable]
- **Data Filtering**: [User-specific data access]
- **Sensitive Data**: [PII, financial data handling]

## Integration Points

### Upstream Dependencies

| System/Service | Purpose | Failure Impact |
|----------------|---------|----------------|
| [System name] | [What it provides] | [What happens if unavailable] |

### Downstream Systems

| System/Service | What Sent | Trigger |
|----------------|-----------|---------|
| [System name] | [Data/Events] | [When triggered] |

### External Systems

| System | Integration Type | Purpose |
|--------|-----------------|---------|
| [System name] | [API/File/Queue] | [Business purpose] |

## Analysis Notes

[Any additional observations, uncertainties, or areas requiring further investigation]

- [Note 1]
- [Note 2]
```

## Batch Job-Specific Additions

For batch jobs, also include:

```markdown
## Batch Job Configuration

### Scheduling

- **Schedule Pattern**: [Cron expression or description]
- **Typical Run Time**: [Duration]
- **Business Calendar**: [Holiday handling, etc.]

### Job Parameters

| Parameter | Type | Source | Purpose |
|-----------|------|--------|---------|
| runDate | Date | Scheduler | Processing date |
| batchSize | Integer | Config | Records per batch |

### Processing Scope

- **Data Scope**: [What data set is processed]
- **Volume**: [Typical/Max record counts]
- **Partitioning**: [How work is divided if applicable]

### Error Recovery

- **Restart Capability**: [Yes/No - how]
- **Checkpoint Strategy**: [How progress is tracked]
- **Failure Notification**: [Who is alerted]

### Dependencies

- **Must Run After**: [Prerequisite jobs]
- **Must Complete Before**: [Dependent jobs]
- **Concurrent Execution**: [Can multiple instances run?]
```

## Example Execution

```
User: /describe-entry-point-api-batch path: ./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/

Agent Response (Iterative Approach):

Phase 1 - Initial Setup:
1. Creates comprehensive todo list for analysis phases
2. Reads metadata.json to understand entry point context
3. Reads call-tree.txt to map execution flow
4. Reads database-dependencies.json overview
5. CHECKS docs/shared-functional-descriptions/index.md for patterns
6. DETECTS: This is a Bean JSON-RPC API endpoint (APassageRestService pattern)
7. WRITES functional-description.in-progress.md with template structure
8. WRITES Executive Summary section mentioning Bean JSON-RPC pattern

Phase 2 - Inputs and Outputs:
9. Reads extracted code files from code/ directory
10. Analyzes method parameters
11. WRITES Method Parameters table to Inputs section
12. WRITES Context/Session Inputs with REFERENCE to shared pattern documentation
13. Analyzes database SELECT operations
14. WRITES Database Inputs table to Inputs section
15. Analyzes return values and database updates
16. WRITES Return Values and Database Outputs tables to Outputs section
17. Identifies side effects (if any)
18. WRITES Side Effects table to Outputs section

Phase 3 - Database Dependencies:
19. Analyzes co_addr table usage
20. WRITES co_addr entry to Database Dependencies Detail section
21. Analyzes co_anlys table usage
22. WRITES co_anlys entry to Database Dependencies Detail section

Phase 4 - Workflows (WITH SHARED PATTERN REFERENCES):
23. Identifies main workflow: Retrieve company addresses with sales reps
24. Maps business-specific logic (database query - Step 6)
25. WRITES Workflow 1 with:
    - Reference to shared steps 1-5 (request handling, security, invocation)
    - Full documentation of Step 6 (business-specific database query)
    - Reference to shared steps 7-10 (filtering, sorting, paging, response)
26. WRITES Business Rules section with REFERENCE to shared rules
27. WRITES Validation Rules section as discovered

Phase 5 - Use Cases and Finalization:
28. Extracts business use cases from workflows
29. WRITES Use Cases section with UC-1, UC-2, etc.
30. WRITES Integration Points section
31. WRITES Security Considerations if applicable
32. WRITES Analysis Notes for any uncertainties
33. Final review and polish of complete document
34. RENAMES file: mv functional-description.in-progress.md functional-description.md
35. Marks all todos as completed

Result: Complete functional description created iteratively at:
./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/functional-description.md

Note:
- File was built section-by-section during analysis, not dumped all at once at the end
- The .in-progress.md suffix was used during analysis, then renamed to .md upon completion
- Shared pattern (Bean JSON-RPC API) was detected and referenced instead of duplicated
- Only the unique business logic (Step 6 - database query) was fully documented
- Result: Concise, focused documentation highlighting what's unique about this endpoint
```

## Validation and Quality Assurance

After creating functional description:

1. **Completeness check**: All inputs, outputs, workflows documented
2. **Accuracy check**: Cross-reference with extracted code
3. **Business perspective check**: Written for business analysts, not just developers
4. **Spec-ready check**: Sufficient detail to write system specifications
5. **Missing context check**: Identify any gaps requiring further investigation

## API & Batch-Specific Success Criteria

In addition to common success criteria:

**API/Batch Analysis Completeness**:
- [ ] Database dependencies completely documented
- [ ] All stored procedures analyzed (including sub-trees)
- [ ] Transaction boundaries understood
- [ ] External system integrations documented

**Database Documentation Quality**:
- [ ] All tables have business purpose documented
- [ ] All columns used have business meaning explained
- [ ] Stored procedure parameters and returns documented
- [ ] Foreign key relationships noted

**For Batch Jobs**:
- [ ] Schedule and timing documented
- [ ] Error recovery approach documented
- [ ] Job dependencies (before/after) documented
- [ ] Volume and performance characteristics noted

## Shared Pattern Avoidance

**CRITICAL: Do not duplicate shared patterns that are already documented!**

- **Always check** `docs/shared-functional-descriptions/index.md` during Phase 1
- **Reference shared steps** with markdown links instead of re-documenting them
- **Focus your effort** on the unique business logic specific to this entry point
- **When in doubt**: If 5+ other entry points have the same processing step, it should probably be shared
- **Quality over quantity**: A 20-line workflow with references is better than a 200-line workflow with duplication

## API & Batch-Specific Shared Patterns

Common patterns to check for:

1. **Bean JSON-RPC API Endpoint** pattern
   - **Applies To**: Spring REST services using APassageRestService with bean-based method invocation
   - **Shared Steps**: 1-5 (request handling, security, invocation) and 7-10 (filtering, sorting, paging, response)
   - **Unique Step**: Step 6 (business-specific operation/database query)
   - **Indicators**:
     - Entry point extends APassageRestService
     - POST to `/service/{serviceName}` with beanId and methodName
     - Uses RemotingService for reflection-based invocation

2. **Standard REST CRUD** pattern
   - GET/POST/PUT/DELETE operations
   - Standard response formatting
   - Common validation patterns

3. **ETL Batch Job** pattern
   - Extract from source
   - Transform data
   - Load to destination
   - Standard error handling

4. **Report Generation** pattern
   - Query data
   - Format output
   - Deliver report

## Advanced Features

### Recursive Stored Procedure Analysis

When entry points call stored procedures that have their own call trees:

1. The `database-dependencies/` folder contains sub-analyses for each stored procedure
2. Each stored procedure sub-folder has the same structure (call-tree.txt, code/, etc.)
3. Incorporate stored procedure analysis into main functional description
4. Document nested database operations and their business purpose
5. Trace data flow through multiple database layers

### Handling Complex Branching

For entry points with complex conditional logic:

1. **Identify major vs minor branches**:
   - Major: Different business scenarios (create vs update vs delete)
   - Minor: Simple validation or null checks
2. **Create separate workflows for major branches**
3. **Document minor variations within workflow steps**
4. **Use decision trees for complex logic** if helpful

### Complex Stored Procedures

**Problem**: Stored procedure logic is intricate with many paths

**Solutions**:
1. Read the stored procedure call tree in database-dependencies/ subfolder
2. Analyze extracted stored procedure code in database-dependencies/code/
3. Break down stored procedure into logical sections
4. Document stored procedure as mini-workflow within main workflow
5. Reference database-dependencies/ folder for full detail

---

**End of Command Specification**
