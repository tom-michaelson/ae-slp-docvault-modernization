# Create Functional Specification - API

You are a Business Analyst specializing in extracting pure functional requirements from API implementation documentation.

## Common Foundation

@create-functional-spec-common.md

## API-Specific Context

This specification type is for **API endpoints** (REST, JSON-RPC, or other service interfaces). Focus on the request/response contract and data exchange patterns.

## Input Document

The user will provide the location of a `functional-description.md` file for an API entry point. Read this file and extract the functional requirements.

## Output Location

Create a `functional-spec.md` file in the same directory as the functional-description.md file.

## API-Specific Output Sections

In addition to the common sections, include these API-specific sections:

### API Contract Section

```markdown
## API Contract

### Operation Identification

**Operation Name**: [Business-friendly name for the operation]

**Operation Type**: [Query (read-only) | Command (modifies data) | Query+Command]

**Idempotency**: [Idempotent (safe to retry) | Non-idempotent | Conditionally idempotent]

### Request Data

#### Required Request Data

| Data Element | Business Meaning | Format/Constraints | Validation Rules |
|--------------|------------------|-------------------|------------------|
| | | | |

#### Optional Request Data

| Data Element | Business Meaning | Default if Omitted | Format/Constraints |
|--------------|------------------|-------------------|-------------------|
| | | | |

### Response Data

#### Success Response

| Data Element | Business Meaning | Format | Conditions |
|--------------|------------------|--------|------------|
| | | | |

#### Response Variations

| Condition | Response Description | Business Meaning |
|-----------|---------------------|------------------|
| No matching data found | Empty collection or null indicator | No data matches criteria |
| Partial results available | Subset of data with indicator | Query exceeded limits |
| | | |

### Business Error Responses

| Error Condition | Business Description | Recoverability |
|-----------------|---------------------|----------------|
| Data not found | Requested item does not exist | Retry with valid identifier |
| Validation failure | Submitted data does not meet business rules | Correct input and retry |
| Authorization denied | User lacks permission for this operation | Contact administrator |
| | | |

> **Authorization Guidance:** Distinguish between **UI menu visibility** (controlled by `menu_func`, does NOT require API-level enforcement) and **explicit API-level permission checks** (must be verified in legacy service code). Note which applies. Do NOT assume "Authorization denied" responses exist unless legacy explicitly enforced API-level checks. See `docs/target-architecture/security-architecture.md`.
```

### Data Transformation Section

```markdown
## Data Transformations

### Input Transformations

| Source Data | Transformed To | Business Rule |
|-------------|----------------|---------------|
| | | |

### Output Transformations

| Internal Data | Presented As | Business Rule |
|---------------|--------------|---------------|
| | | |

### Data Enrichment

| Base Data | Enriched With | Source | Business Purpose |
|-----------|---------------|--------|------------------|
| | | | |
```

### Database Operations Section

> **CRITICAL**: This section contains precise technical details about database tables and queries.
> The database schema is a contract that will remain largely unchanged in the new implementation.
> All other sections are technology-agnostic, but this section preserves exact table/column names and SQL operations.

#### DDL Verification (CRITICAL)

**You MUST verify all table schemas against the DDL source of truth**: `legacy/database/ddl-tables-and-views.sql`

Do NOT rely solely on the functional-description.md for column information - it only lists "Key Columns Used", not all columns.

For each table or view:
1. **Find the object in DDL**: Search `legacy/database/ddl-tables-and-views.sql` for the `CREATE TABLE` statement
2. **If no CREATE TABLE found, search for CREATE VIEW**: If no `CREATE TABLE [dbo].[object_name]` match exists, search for `CREATE VIEW [dbo].[object_name]`. If found, document it as a **View** (see View template below) instead of reporting it as missing.
3. **Count ALL columns**: Document the exact count in the table header (e.g., "33 columns per DDL source of truth")
4. **List ALL columns**: Include every column from the DDL, not just those used by the query
5. **Use exact SQL Server types**: Use precise types like `varchar(30)`, `datetime2(3)`, `int`, `tinyint`, `char(8)`, `numeric(10,5)` - not generic types like "Text", "Date", "Integer"
6. **Include Nullable column**: Mark each column as `NOT NULL` or `NULL` per DDL
7. **Mark unused columns**: Use "Not used" in the "Used In" column for columns not referenced by the query

```markdown
## Database Operations

### Tables and Views Involved

#### Table: [TABLE_NAME] ([N] columns per DDL source of truth)

**Business Purpose**: [What this table represents in business terms]

**Operations**: [SELECT | INSERT | UPDATE | DELETE | Multiple]

**Columns Used**:

| Column Name | Data Type | Nullable | Business Meaning | Used In | Constraints |
|-------------|-----------|----------|------------------|---------|-------------|
| [COLUMN_NAME] | [exact SQL type, e.g., varchar(30)] | [NOT NULL or NULL] | [Business meaning] | [WHERE/SELECT/INSERT/Not used] | [PK/FK/Max N chars/etc] |

> **Note**: Query uses [X] of [N] columns. [List which columns are used vs not used if helpful.]

**Primary Key**: [List composite key columns if applicable]

**Foreign Keys**:
- [COLUMN_NAME] references [OTHER_TABLE]([OTHER_COLUMN]) - [Business relationship]

**Indexes Used**: [Any specific indexes relevant to queries]

---

#### View: [VIEW_NAME]

**View Type**: DATABASE VIEW

**Business Purpose**: [What this view represents in business terms]

**View Definition** (from DDL):
```sql
[The SELECT statement from the CREATE VIEW definition]
```

**Underlying Tables**: [List the base tables referenced in the view's SELECT]

**Operations**: [SELECT — views are typically read-only]

**Columns Exposed**:

| Column Name | Data Type | Source Table.Column | Business Meaning | Used In |
|-------------|-----------|---------------------|------------------|---------|
| [COLUMN_NAME] | [type from view definition or source table] | [SOURCE_TABLE].[SOURCE_COLUMN] | [Business meaning] | [WHERE/SELECT/Not used] |

> **Note**: This is a database VIEW, not a table. Column types are derived from the underlying source tables. The view exposes [X] columns.

---

### Query Operations

#### Operation: [Business Operation Name]

**SQL Operation Type**: [SELECT | INSERT | UPDATE | DELETE]

**Purpose**: [Business purpose of this database operation]

**Query Pattern**:
```sql
[Exact SQL or SQL pattern from legacy system]
```

**Parameters**:
- `?` → [Parameter name / business meaning]

**Expected Result**: [What the query returns or affects]

**Business Rule Enforced**: [Which business rule this query enforces]

**Performance Notes**: [Any important performance considerations]

---

### Data Integrity Rules (Database Level)

**Composite Keys**:
1. **[Table Name]**: Unique record identified by [list all key columns]
   - **Business Meaning**: [Why these fields together form identity]

**Foreign Key Constraints**:
1. **[Constraint Name]**: [TABLE.COLUMN] references [OTHER_TABLE.COLUMN]
   - **Business Meaning**: [What this relationship represents]
   - **On Delete**: [CASCADE | RESTRICT | SET NULL] - [Business impact]
   - **On Update**: [CASCADE | RESTRICT | SET NULL] - [Business impact]

### Database Transaction Requirements

**Transaction Scope**: [Which database operations must occur in same transaction]

**Isolation Level Required**: [READ_UNCOMMITTED | READ_COMMITTED | REPEATABLE_READ | SERIALIZABLE]
- **Business Reason**: [Why this level is needed]

**Rollback Conditions**: [What conditions should trigger rollback]

**Commit Conditions**: [When transaction should commit]
```

### API-Specific Gherkin Patterns

When creating Gherkin scenarios for APIs, include the standard scenarios from the common template PLUS these API-specific scenario types:

```gherkin
Feature: [API Operation Name]
  As a [consumer/role]
  I want to [use this API operation]
  So that [business value/goal]

  # Background: Common setup for all scenarios
  Background:
    Given the system is operational
    And the user is authenticated
    And [any common data setup]

  #──────────────────────────────────────────────────────────────
  # API REQUEST/RESPONSE SCENARIOS
  #──────────────────────────────────────────────────────────────

Scenario: Successful data retrieval with complete request
  # Business Context: [Standard API query with all parameters]

  Given the system contains [relevant business data]
  And the user is authorized to access this data
  When a request is submitted with [specific parameters]
  Then the response contains [expected business data]
  And all requested data elements are present
  And the data reflects the current system state

Scenario: Request with optional parameters omitted
  # Business Context: [Using defaults for optional data]

  Given the system contains [relevant business data]
  When a request is submitted without optional parameters
  Then default values are applied for [list defaults]
  And the response reflects the default behavior

Scenario: Partial data available
  # Business Context: [When some requested data exists but not all]

  Given some of the requested data exists
  But other requested data does not exist
  When the request is submitted
  Then available data is returned
  And missing data is indicated appropriately

#──────────────────────────────────────────────────────────────
# DATA MODIFICATION API SCENARIOS
#──────────────────────────────────────────────────────────────

Scenario: Successful data creation
  # Business Context: [Creating new business entity via API]

  Given all required data is provided
  And the data meets all business validation rules
  And no conflicting data exists
  When the creation request is submitted
  Then the new entity is created in the system
  And a confirmation with entity identifier is returned
  And the entity is immediately available for retrieval

Scenario: Successful data update
  # Business Context: [Modifying existing business entity]

  Given the target entity exists
  And the user is authorized to modify it
  And the update data is valid
  When the update request is submitted
  Then the entity is modified as requested
  And the response confirms the update
  And subsequent retrievals show the updated data

Scenario: Duplicate creation attempt
  # Business Context: [Preventing duplicate business entities]

  Given an entity with the same identifying data already exists
  When an attempt is made to create a duplicate
  Then the creation is rejected
  And the error identifies the conflict
  And no new entity is created

#──────────────────────────────────────────────────────────────
# API ERROR HANDLING SCENARIOS
#──────────────────────────────────────────────────────────────

Scenario: Malformed request data
  # Business Context: [Request cannot be understood]

  Given request data is incomplete or malformed
  When the request is submitted
  Then processing is rejected before business logic
  And a clear error indicates the data problem

Scenario: Request exceeds size limits
  # Business Context: [Protecting system from oversized requests]

  Given request contains more data than allowed
  When the request is submitted
  Then the request is rejected
  And the error indicates size constraints

  #──────────────────────────────────────────────────────────────
  # PAGINATION AND FILTERING SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: Paginated results - first page
    # Business Context: [Large result sets are returned in pages]

    Given data exists that would return more than one page
    When the first page is requested
    Then only the first page of results is returned
    And indication of total available records is provided
    And ability to retrieve next page is indicated

  Scenario: Filtered query with results
    # Business Context: [Narrowing results to match criteria]

    Given data exists matching the filter criteria
    When a filtered query is submitted
    Then only matching records are returned
    And the count reflects filtered results

  Scenario: Sorted results
    # Business Context: [Ordering results for business needs]

    Given multiple records exist
    When results are requested with sort criteria
    Then records are returned in the specified order
    And sort order is consistent across pages

  #──────────────────────────────────────────────────────────────
  # BOUNDARY CONDITION SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: Minimum parameter values accepted
    # Business Context: [Testing minimum acceptable values]

    Given parameters at minimum boundary values
    When the request is submitted
    Then the request is processed successfully
    And boundary values are handled correctly

  Scenario: Maximum parameter values accepted
    # Business Context: [Testing maximum acceptable values]

    Given parameters at maximum boundary values
    When the request is submitted
    Then the request is processed successfully
    And boundary values are handled correctly

  Scenario: Parameter below minimum rejected
    # Business Context: [Enforcing minimum constraints]

    Given a parameter below its minimum value
    When the request is submitted
    Then validation fails
    And error indicates the minimum constraint

  #──────────────────────────────────────────────────────────────
  # TEMPORAL SCENARIOS (for date-based APIs)
  #──────────────────────────────────────────────────────────────

  Scenario: Query with valid date range
    # Business Context: [Retrieving data for a time period]

    Given data exists within the requested date range
    When a query with date range is submitted
    Then only data within the range is returned

  Scenario: Query for future effective date
    # Business Context: [Handling not-yet-effective data]

    Given data with future effective dates exists
    When querying for future-dated items
    Then appropriate handling per business rules occurs

  #──────────────────────────────────────────────────────────────
  # CONCURRENT OPERATION SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: Concurrent modification conflict
    # Business Context: [Two users modifying same data]

    Given entity was retrieved by user A
    And entity was modified by user B
    When user A submits modification
    Then conflict is detected
    And appropriate conflict resolution occurs

  Scenario: Idempotent retry
    # Business Context: [Safe to retry after network failure]

    Given a request was submitted but response was lost
    When the same request is retried
    Then the result is the same as the first submission
    And no duplicate side effects occur

  #──────────────────────────────────────────────────────────────
  # DATA VARIATION SCENARIOS (Scenario Outlines)
  #──────────────────────────────────────────────────────────────

  Scenario Outline: Query with various filter combinations
    # Business Context: [Testing different filter permutations]

    Given data exists matching <filter_criteria>
    When a query is submitted with <filter_criteria>
    Then <expected_count> results are returned
    And results match <validation_rule>

    Examples: Common filter combinations
      | filter_criteria | expected_count | validation_rule |
      | [criteria1]     | [count1]       | [rule1]         |
      | [criteria2]     | [count2]       | [rule2]         |
```

## API Extraction Instructions

Follow these steps for API specifications:

1. **Read the functional-description.md file** completely

2. **Identify the API operation type**:
   - Is this a query (read-only) or command (modifies data)?
   - What is the primary business purpose?
   - Who are the consumers of this API?

3. **Extract request/response contract**:
   - Document all input parameters with business meaning
   - Document the response structure with business meaning
   - Identify required vs optional data
   - Note any default values or behaviors

4. **Classify authorization rules**:
   - For each authorization rule, determine if it describes **UI menu visibility** or **API-level enforcement**
   - UI menu visibility (most common): user can/cannot see the menu item — does NOT imply API returns 403
   - API-level enforcement (rare): legacy code explicitly checked permissions at the REST endpoint level — verify in legacy source
   - Do NOT generate "Authorization denied" error responses or 403 Gherkin scenarios unless legacy actually enforced API-level checks

5. **Apply common extraction steps** (business rules, database operations, Gherkin scenarios)

6. **Add API-specific scenarios**:
   - Request/response variations
   - Pagination or batch handling (if applicable)
   - Filtering and sorting options (if applicable)
   - Error response scenarios

7. **Document data transformations**:
   - How input data maps to internal processing
   - How internal data maps to response format
   - Any data enrichment that occurs

8. **Write the functional-spec.md file** following all common and API-specific sections

## API Scenario Coverage Checklist

In addition to the common Scenario Coverage Checklist (from @create-functional-spec-common.md), ensure you have API-specific scenarios for:

**Request/Response**:
- [ ] Successful request with all parameters
- [ ] Request with optional parameters omitted (defaults applied)
- [ ] Partial data available response
- [ ] Empty result set response

**Data Modification APIs** (if applicable):
- [ ] Successful creation
- [ ] Successful update
- [ ] Successful deletion
- [ ] Duplicate creation rejected
- [ ] Update of non-existent entity

**Pagination/Filtering** (if applicable):
- [ ] First page of paginated results
- [ ] Middle/last page of paginated results
- [ ] Filtered query with results
- [ ] Filtered query with no results
- [ ] Sorted results
- [ ] Combined filter and sort

**Boundary Conditions**:
- [ ] Minimum parameter values
- [ ] Maximum parameter values
- [ ] Below minimum rejected
- [ ] Above maximum rejected
- [ ] Empty/null handling

**Temporal** (if date parameters):
- [ ] Valid date range query
- [ ] Future effective dates
- [ ] Past/expired dates
- [ ] Invalid date range (end before start)

**Concurrency** (if modifies data):
- [ ] Concurrent modification conflict
- [ ] Idempotent retry behavior
- [ ] Optimistic locking (if applicable)

**Error Handling**:
- [ ] Malformed request data
- [ ] Request exceeds size limits
- [ ] Rate limiting (if applicable)
- [ ] Service unavailable handling

## API Quality Checklist

In addition to the common quality checklist, verify:

**API Contract**:
- [ ] API contract is fully documented (request and response)
- [ ] All input parameters have business meaning explained
- [ ] All response fields have business meaning explained
- [ ] Required vs optional parameters are clearly distinguished
- [ ] Default values are documented for optional parameters
- [ ] Error responses are mapped to business conditions
- [ ] Data transformation rules are documented
- [ ] Pagination/batching behavior is documented (if applicable)
- [ ] Rate limiting or quota rules are documented (if applicable)
- [ ] Caching/freshness behavior is documented (if applicable)

**Database Operations** (Critical - Preserve Exactly):
- [ ] Database Operations section exists and is complete
- [ ] ALL table names are exact (e.g., PT_CO_XREF, not "point company table")
- [ ] ALL column names are exact (e.g., PT_ID_NBR, not "point ID")
- [ ] SQL queries are preserved verbatim from the source
- [ ] WHERE clauses are exact and complete
- [ ] JOIN conditions are documented if present
- [ ] Composite keys are fully documented
- [ ] Foreign key relationships are captured
- [ ] Each database operation is mapped to its business purpose
- [ ] Transaction boundaries are documented if specified in source

**DDL Verification** (Critical - Must Complete):
- [ ] Each table schema verified against `legacy/database/ddl-tables-and-views.sql`
- [ ] If no CREATE TABLE found, searched for CREATE VIEW before reporting as missing
- [ ] Views documented using the View template (with underlying tables and view definition)
- [ ] Column count documented in table header (e.g., "33 columns per DDL source of truth")
- [ ] ALL columns from DDL are listed (not just "Key Columns Used" from functional-description)
- [ ] Exact SQL Server data types used (varchar(30), datetime2(3), int, char(8), etc.)
- [ ] Nullable column included for each column (NOT NULL or NULL)
- [ ] "Not used" marked for columns not referenced by the query
- [ ] Length constraints documented (e.g., "Max 30 chars" for varchar(30))

## Example Transformations

### Example 1: Technical API Endpoint → Business API Contract

**From functional-description.md** (technical):
```
### Method Parameters

| Parameter | Type | Description | Required | Business Meaning |
|-----------|------|-------------|----------|------------------|
| request | CompanyContactListRequest | DTO with filter/sort criteria | Yes | Query parameters |
| userContext | UserContext | Session context with user info | Yes | Authentication context |

### Return Values

| Type | Description | Business Meaning | Conditions |
|------|-------------|------------------|------------|
| CompanyContactListResponse | Paginated list of contacts | Contact list with metadata | Always |

The response contains:
- List<CompanyContactDto> contacts - The actual contact records
- int totalCount - Total matching records
- int pageNumber - Current page (0-based)
- int pageSize - Records per page
```

**To functional-spec.md** (business):
```markdown
## API Contract

### Operation Identification

**Operation Name**: Retrieve Company Contacts

**Operation Type**: Query (read-only)

**Idempotency**: Idempotent (safe to retry)

### Request Data

#### Required Request Data

| Data Element | Business Meaning | Format/Constraints | Validation Rules |
|--------------|------------------|-------------------|------------------|
| Company Identifier | The company whose contacts to retrieve | Numeric ID | Must reference existing company |

#### Optional Request Data

| Data Element | Business Meaning | Default if Omitted | Format/Constraints |
|--------------|------------------|-------------------|-------------------|
| Name Filter | Filter contacts by name | No filter (all contacts) | Partial match supported |
| Function Filter | Filter by contact's business function | No filter | Must be valid function code |
| Page Number | Which page of results to return | First page (0) | Non-negative integer |
| Page Size | How many contacts per page | 20 | 1-100 |

### Response Data

#### Success Response

| Data Element | Business Meaning | Format | Conditions |
|--------------|------------------|--------|------------|
| Contact List | The contacts matching criteria | List of contact records | Always present (may be empty) |
| Total Count | Total contacts matching filter | Integer | Always present |
| Page Number | Current page returned | Integer | Always present |
| Page Size | Records per page | Integer | Always present |

#### Response Variations

| Condition | Response Description | Business Meaning |
|-----------|---------------------|------------------|
| No matching contacts | Empty list with totalCount = 0 | No contacts match the criteria |
| More pages available | List with totalCount > current page | Additional pages can be requested |
```

### Example 2: Technical Workflow → Gherkin Scenario

**From functional-description.md** (technical workflow):
```
### Workflow 1: Retrieve Company Contacts

**Steps**:
1. HTTP Request Reception - POST to /service/CompanyContactService
2. Bean ID Assignment - remotingService extracts beanId
3. Security Validation - PermissionChecker validates VIEW permission
4. Method Invocation - RemotingService calls getCompanyContactList via reflection
5. Database Query - iBATIS executes queryForList with CO_ANLYS_FCN query
6. Result Mapping - Maps ResultSet to CompanyContactDto objects
7. Client-Side Filtering - RemotingService applies additional filters
8. Client-Side Sorting - RemotingService applies sort criteria
9. Client-Side Paging - RemotingService extracts requested page
10. Response Construction - Wraps result in CompanyContactListResponse

**Error Conditions**:
- SecurityException: User lacks VIEW permission
- SQLException: Database query failure
```

**To functional-spec.md** (Gherkin with business context):
```gherkin
Scenario: Retrieve contacts for a company
  # Business Context: User needs to view all contacts associated with
  # a company to manage relationships and communication.
  # Frequency: Multiple times per day per user
  # Business Value: Enables effective customer relationship management

  Given the user is authorized to view company contacts
  And the company has contacts on file
  When the user requests the contact list for the company
  Then all contacts for the company are returned
  And contact information includes name, function, and contact details
  And the total count of contacts is provided

Scenario: Retrieve contacts with filtering
  # Business Context: User needs to find specific contacts quickly

  Given the company has multiple contacts with different functions
  When the user requests contacts filtered by function "Sales Representative"
  Then only contacts with the sales function are returned
  And the count reflects the filtered results

Scenario: Retrieve contacts with pagination
  # Business Context: Companies may have many contacts

  Given the company has more contacts than fit on one page
  When the user requests page 2 with page size 10
  Then contacts 11-20 are returned
  And the total count indicates more contacts exist
  And the current page number is indicated

Scenario: User lacks permission to view contacts
  # Business Context: Contact information is sensitive

  Given the user is not authorized to view company contacts
  When the user requests the contact list
  Then access is denied
  And no contact information is disclosed
```

### Example 3: Database Query → Database Operations Section

**From functional-description.md** (technical):
```
### Stored Procedure: CO_ANLYS_FCN Query

**SQL Statement**:
SELECT a.ANLYS_ID, a.ANLYS_NM, a.ANLYS_FCN_CD, f.FCN_DESC,
       a.ANLYS_PHONE, a.ANLYS_EMAIL, a.LST_UPDT_USER_ID, a.LST_UPDT_TS
FROM CO_ANLYS a
JOIN CO_ANLYS_FCN f ON a.ANLYS_FCN_CD = f.ANLYS_FCN_CD
WHERE a.CO_ID = ?
ORDER BY a.ANLYS_NM
```

**To functional-spec.md** (Database Operations - PRESERVED EXACTLY):
```markdown
## Database Operations

### Tables and Views Involved

#### Table: CO_ANLYS (10 columns per DDL source of truth)

**Business Purpose**: Company Analyst/Contact table storing individuals associated with companies

**Operations**: SELECT

**Columns Used**:

| Column Name | Data Type | Nullable | Business Meaning | Used In | Constraints |
|-------------|-----------|----------|------------------|---------|-------------|
| ANLYS_ID | int | NOT NULL | Unique contact identifier | SELECT | PK |
| CO_ID | int | NOT NULL | Company this contact belongs to | WHERE | FK → CO |
| ANLYS_NM | varchar(50) | NOT NULL | Contact's full name | SELECT, ORDER BY | Max 50 chars |
| ANLYS_FCN_CD | char(8) | NOT NULL | Contact's business function code | SELECT, JOIN | FK → CO_ANLYS_FCN |
| ANLYS_PHONE | varchar(20) | NULL | Contact's phone number | SELECT | Max 20 chars |
| ANLYS_EMAIL | varchar(100) | NULL | Contact's email address | SELECT | Max 100 chars |
| LST_UPDT_USER_ID | varchar(30) | NOT NULL | Last user to modify | SELECT | Max 30 chars |
| LST_UPDT_TS | datetime2(3) | NOT NULL | Last modification time | SELECT | Millisecond precision |
| CREATED_BY | varchar(30) | NOT NULL | User who created record | Not used | Max 30 chars |
| CREATED_DATE | datetime2(3) | NOT NULL | Record creation timestamp | Not used | Millisecond precision |

> **Note**: Query uses 8 of 10 columns. CREATED_BY and CREATED_DATE are not used.

#### Table: CO_ANLYS_FCN (4 columns per DDL source of truth)

**Business Purpose**: Reference table of contact function codes (e.g., Sales Rep, Billing Contact)

**Operations**: SELECT (via JOIN)

**Columns Used**:

| Column Name | Data Type | Nullable | Business Meaning | Used In | Constraints |
|-------------|-----------|----------|------------------|---------|-------------|
| ANLYS_FCN_CD | char(8) | NOT NULL | Function code | JOIN | PK; Exactly 8 chars |
| FCN_DESC | varchar(50) | NOT NULL | Human-readable function description | SELECT | Max 50 chars |
| LST_UPDT_USER_ID | varchar(30) | NOT NULL | Last user to modify | Not used | Max 30 chars |
| LST_UPDT_TS | datetime2(3) | NOT NULL | Last modification timestamp | Not used | Millisecond precision |

> **Note**: Query uses 2 of 4 columns. Audit columns not used.

### Query Operations

#### Operation: Retrieve Company Contacts

**SQL Operation Type**: SELECT with JOIN

**Purpose**: Retrieve all contacts for a company with their function descriptions

**Query Pattern**:
```sql
SELECT a.ANLYS_ID, a.ANLYS_NM, a.ANLYS_FCN_CD, f.FCN_DESC,
       a.ANLYS_PHONE, a.ANLYS_EMAIL, a.LST_UPDT_USER_ID, a.LST_UPDT_TS
FROM CO_ANLYS a
JOIN CO_ANLYS_FCN f ON a.ANLYS_FCN_CD = f.ANLYS_FCN_CD
WHERE a.CO_ID = ?
ORDER BY a.ANLYS_NM
```

**Parameters**:
- `?` → CO_ID (Company identifier)

**Expected Result**: List of contact records with function descriptions, ordered by name

**Business Rule Enforced**: Contacts are always retrieved with their function description for display
```

**Key points in API transformations**:
- ✅ Technical terms removed (no "DTO", "iBATIS", "reflection", "ResultSet")
- ✅ Implementation layers abstracted (no "service layer", "DAO", "Bean ID")
- ✅ HTTP/REST details removed (no "POST", "endpoint path", "JSON")
- ✅ Focus on business data and its meaning
- ✅ Database operations PRESERVED exactly (table names, column names, SQL)
- ✅ Error conditions translated to business scenarios

## Begin

Ask the user for the path to the API functional-description.md file, then create the functional-spec.md file following all instructions above.
