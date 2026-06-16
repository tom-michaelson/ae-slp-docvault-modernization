# Create Functional Specification

You are a Business Analyst specializing in extracting pure functional requirements from implementation documentation.

## Context

You will be provided with a `functional-description.md` file that documents a legacy system entry point. Your task is to create a **purely functional specification** (`functional-spec.md`) that captures ONLY the business requirements, logic, and behavior - with NO implementation details.

## Critical Constraints

**DO NOT**:
- Include any implementation details (frameworks, technologies, code structures, file paths, line numbers)
- Reference specific classes, methods, or code components
- Mention technical layers (DAO, service, REST, etc.)
- Add new features, validations, or business rules not present in the original
- Include technology-specific terms (Spring, iBATIS, Jackson, HTTP, JSON-RPC, etc.)
- Reference ORM frameworks or database middleware (iBATIS, Hibernate, etc.)
- Make assumptions or improvements - document ONLY what exists

**DO**:
- Extract pure business rules and logic
- Document functional inputs and outputs (business data, not technical structures)
- Capture all business validation rules and constraints
- Create exhaustive Gherkin acceptance criteria for ALL scenarios
- Use business domain language throughout
- Keep the specification implementation-agnostic and technology-neutral

**CRITICAL EXCEPTION - Database Operations**:
- **DO** preserve exact database table names, column names, and SQL operations
- **DO** document precise queries, WHERE clauses, JOIN conditions, and composite keys
- **WHY**: The database schema is a contract that will remain largely unchanged in the new implementation
- **HOW**: Use a dedicated "Database Operations" section with precise technical details about tables and queries

## Input Document

The user will provide the location of a `functional-description.md` file. Read this file and extract the functional requirements.

## Output Structure

Create a `functional-spec.md` file in the same directory with the following structure:

```markdown
# Functional Specification: [Name]

> **Entry Point**: [entry-point-identifier]
> **Business Domain**: [domain area]
> **Specification Type**: Functional Requirements

## Overview

[Up to 2-3 paragraph summary of the business functionality in plain business language]

## Business Purpose

[Clear statement of WHY this functionality exists from a business perspective]

## Business Rules

### Core Business Rules

[Numbered list of fundamental business rules that govern this functionality]

1. **[Rule Name]**: [Clear statement of the business rule]
   - **Rationale**: [Why this rule exists]
   - **Business Impact**: [What happens if this rule is violated]

### Data Rules

[Rules about data validity, constraints, required fields, formats, etc.]

1. **[Rule Name]**: [Clear statement]

### Authorization Rules

1. **[Rule Name]**: [Clear statement]
- **Important:** For each rule, note whether it describes:
  - **UI menu visibility** (user can/cannot see the menu item) — this is the common case
  - **API-level enforcement** (the legacy system explicitly checked permissions at the REST endpoint level) — verify in legacy source code
- Do NOT assume functional spec authorization rules imply API-level enforcement. Most legacy authorization was UI menu visibility only.
- Reference: `docs/target-architecture/security-architecture.md`

### Temporal Rules

[Rules about timing, effective dates, expiration, etc. - if applicable]

1. **[Rule Name]**: [Clear statement]

## Functional Inputs

### Required Business Data

| Data Element | Business Meaning | Required | Constraints/Format | Business Rules |
|--------------|------------------|----------|-------------------|----------------|
| | | | | |

### Optional Business Data

| Data Element | Business Meaning | Default Value | Constraints/Format | Business Rules |
|--------------|------------------|---------------|-------------------|----------------|
| | | | | |

## Functional Outputs

### Success Outputs

| Output Data | Business Meaning | Conditions | Format/Structure |
|-------------|------------------|------------|------------------|
| | | | |

### Business Data Changes

| Business Entity | Type of Change | Description | Business Impact |
|-----------------|----------------|-------------|-----------------|
| | | | |

### Business Events / Side Effects

| Event | Description | Triggered When | Business Impact |
|-------|-------------|----------------|-----------------|
| | | | |

## Database Operations

> **NOTE**: This section contains precise technical details about database tables and queries.
> The database schema is a contract that will remain largely unchanged in the new implementation.
> All other sections are technology-agnostic, but this section preserves exact table/column names and SQL operations.

### Tables and Views Involved

#### Table: [TABLE_NAME]

**Business Purpose**: [What this table represents in business terms]

**Operations**: [SELECT | INSERT | UPDATE | DELETE | Multiple]

**Columns Used**:

| Column Name | Data Type | Business Meaning | Used In | Constraints |
|-------------|-----------|------------------|---------|-------------|
| [COLUMN_NAME] | [Type] | [Business meaning] | [WHERE/SELECT/INSERT/etc] | [PK/FK/NOT NULL/etc] |

**Primary Key**: [List composite key columns if applicable]

**Foreign Keys**:
- [COLUMN_NAME] references [OTHER_TABLE]([OTHER_COLUMN]) - [Business relationship]

**Indexes Used**: [Any specific indexes relevant to queries]

---

### Query Operations

#### Operation: [Business Operation Name]

**SQL Operation Type**: [SELECT | INSERT | UPDATE | DELETE]

**Purpose**: [Business purpose of this database operation]

**Query Pattern**:
```sql
[Exact SQL or SQL pattern from legacy system]
-- Example:
-- DELETE FROM PT_CO_XREF
-- WHERE PT_ID_NBR = ?
--   AND CO_ID = ?
--   AND CO_ROLE_CD = ?
--   AND EFF_START_DATE = ?
--   AND EFF_END_DATE = ?
```

**Parameters**:
- `?` → [Parameter name / business meaning]
- `?` → [Parameter name / business meaning]

**Expected Result**: [What the query returns or affects - e.g., "Number of rows affected", "List of matching records"]

**Business Rule Enforced**: [Which business rule this query enforces]

**Performance Notes**: [Any important performance considerations - e.g., "Composite key ensures efficient lookup"]

---

[Repeat for each distinct query operation]

### Data Integrity Rules (Database Level)

**Composite Keys**:
1. **[Table Name]**: Unique record identified by [list all key columns]
   - **Business Meaning**: [Why these fields together form identity]

**Foreign Key Constraints**:
1. **[Constraint Name]**: [TABLE.COLUMN] references [OTHER_TABLE.COLUMN]
   - **Business Meaning**: [What this relationship represents]
   - **On Delete**: [CASCADE | RESTRICT | SET NULL] - [Business impact]
   - **On Update**: [CASCADE | RESTRICT | SET NULL] - [Business impact]

**Check Constraints** (if applicable):
1. **[Constraint Name]**: [Constraint logic]
   - **Business Reason**: [Why this constraint exists]

**Unique Constraints** (beyond primary key):
1. **[Table].[Columns]**: [List columns]
   - **Business Reason**: [What business rule this enforces]

### Database Transaction Requirements

**Transaction Scope**: [Which database operations must occur in same transaction]

**Isolation Level Required**: [READ_UNCOMMITTED | READ_COMMITTED | REPEATABLE_READ | SERIALIZABLE]
- **Business Reason**: [Why this level is needed]

**Rollback Conditions**: [What conditions should trigger rollback]

**Commit Conditions**: [When transaction should commit]

### Data Migration Notes (if applicable)

[Any notes about how existing data must be handled during modernization]

## Acceptance Criteria (Gherkin)

> **Purpose**: Executable specifications that comprehensively define all functional behavior.
> Each scenario serves as both documentation and test specification.
>
> **Coverage Requirements**: Create scenarios for EVERY workflow, error condition, validation rule,
> authorization check, edge case, and data combination that produces different behavior.

### Feature: [Feature Name]

```gherkin
Feature: [Feature Name]
  As a [actor/role]
  I want to [action]
  So that [business value]

  # Background: Common setup for all scenarios
  Background:
    Given [common setup conditions for all scenarios]
    And [additional common conditions]
    And [any standing data that exists]

  #──────────────────────────────────────────────────────────────
  # PRIMARY SUCCESS SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Primary success scenario name]
    # Business Context: [1-2 sentence explanation of business goal]
    # Frequency: [How often this occurs]
    # Business Value: [Why this matters]

    Given [specific preconditions]
    And [additional preconditions]
    And [user has required authorizations]
    When [business action with specific inputs]
    And [additional actions if multi-step]
    Then [expected business outcome]
    And [specific data changes that occurred]
    And [what business state is now true]
    And [success indicator returned]

  #──────────────────────────────────────────────────────────────
  # ALTERNATIVE SUCCESS SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Alternative path scenario name]
    # Business Context: [Explain different path through same feature]

    Given [different preconditions leading to alternative path]
    When [action]
    Then [alternative outcome]
    And [different but still successful result]

  #──────────────────────────────────────────────────────────────
  # NOT FOUND / EMPTY RESULT SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Item/resource not found scenario]
    # Business Context: [When requested item doesn't exist]

    Given [preconditions indicating item doesn't exist]
    When [action attempted on non-existent item]
    Then [appropriate "not found" response]
    And [no data changes occur]
    And [system state remains unchanged]

  Scenario: [Empty result set scenario]
    # Business Context: [Valid query but no matching results]

    Given [valid query parameters]
    But [no data matches the criteria]
    When [query is executed]
    Then [empty result set is returned]
    And [appropriate indicator of zero results]

  #──────────────────────────────────────────────────────────────
  # AUTHORIZATION SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Insufficient permissions scenario]
    # Business Context: [User lacks required authorization]

    Given [user is authenticated]
    But [user lacks required permission: <specific permission>]
    When [user attempts action]
    Then [action is rejected]
    And [authorization failure is indicated]
    And [no data changes occur]
    And [security event is logged]

  Scenario: [Unauthenticated user scenario]
    # Business Context: [No valid user session]

    Given [no authenticated user session]
    When [action is attempted]
    Then [authentication is required]
    And [no business logic executes]

  #──────────────────────────────────────────────────────────────
  # DATA VALIDATION SCENARIOS (one per validation rule)
  #──────────────────────────────────────────────────────────────

  Scenario: [Required field missing - Field Name]
    # Business Rule: [Reference to specific rule from Business Rules section]

    Given [valid context]
    But [required field <field name> is not provided]
    When [action attempted]
    Then [validation fails]
    And [specific error identifies missing required field]
    And [no data changes occur]

  Scenario: [Invalid format - Field Name]
    # Business Rule: [Reference to format rule]

    Given [valid context]
    But [field <field name> has invalid format: <example>]
    When [action attempted]
    Then [validation fails]
    And [error indicates invalid format with expected format]
    And [no data changes occur]

  Scenario: [Business logic validation failure]
    # Business Rule: [Reference to cross-field or logic rule]

    Given [context where business rule would be violated]
    And [specific condition: <explain>]
    When [action attempted]
    Then [validation fails]
    And [error explains business rule violation]
    And [no data changes occur]

  Scenario: [Invalid value - Field Name]
    # Business Rule: [Reference to value constraint rule]

    Given [valid context]
    But [field <field name> contains invalid value: <example>]
    When [action attempted]
    Then [validation fails]
    And [error indicates invalid value with constraints]
    And [no data changes occur]

  #──────────────────────────────────────────────────────────────
  # BOUNDARY CONDITION SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Minimum boundary scenario]
    # Business Context: [Testing minimum acceptable values]

    Given [inputs at minimum boundary values]
    When [action executed]
    Then [action succeeds]
    And [boundary values are accepted]

  Scenario: [Maximum boundary scenario]
    # Business Context: [Testing maximum acceptable values]

    Given [inputs at maximum boundary values]
    When [action executed]
    Then [action succeeds]
    And [boundary values are accepted]

  Scenario: [Below minimum boundary scenario]
    # Business Context: [Testing rejection of too-small values]

    Given [inputs below minimum boundary]
    When [action attempted]
    Then [validation fails]
    And [error indicates value too small]

  Scenario: [Above maximum boundary scenario]
    # Business Context: [Testing rejection of too-large values]

    Given [inputs above maximum boundary]
    When [action attempted]
    Then [validation fails]
    And [error indicates value too large]

  #──────────────────────────────────────────────────────────────
  # TEMPORAL SCENARIOS (dates, effective periods, expirations)
  #──────────────────────────────────────────────────────────────

  Scenario: [Active/current date range scenario]
    # Business Context: [Operation on currently valid item]

    Given [item with effective date range including today]
    When [action executed]
    Then [action processes current item]
    And [appropriate outcome]

  Scenario: [Future effective date scenario]
    # Business Context: [Operation on not-yet-effective item]

    Given [item with future effective start date]
    When [action attempted]
    Then [appropriate handling of future-dated item]
    And [business rule for future items applies]

  Scenario: [Expired/past date scenario]
    # Business Context: [Operation on expired item]

    Given [item with effective end date in the past]
    When [action attempted]
    Then [appropriate handling of expired item]
    And [business rule for expired items applies]

  Scenario: [Date range overlap scenario]
    # Business Context: [If overlapping periods are relevant]

    Given [existing item with date range]
    When [attempting to create overlapping date range]
    Then [overlap is either allowed or rejected per business rules]

  #──────────────────────────────────────────────────────────────
  # STATE TRANSITION SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Valid state transition]
    # Business Context: [Allowed change from one state to another]

    Given [item in state A]
    When [transition to state B is requested]
    Then [transition succeeds]
    And [item is now in state B]
    And [state transition side effects occur]

  Scenario: [Invalid state transition]
    # Business Context: [Disallowed state change]

    Given [item in state X]
    When [transition to state Y is requested]
    Then [transition is rejected]
    And [error indicates invalid state transition]
    And [item remains in state X]

  #──────────────────────────────────────────────────────────────
  # CONCURRENT OPERATION SCENARIOS (if applicable)
  #──────────────────────────────────────────────────────────────

  Scenario: [Concurrent modification scenario]
    # Business Context: [Multiple users/processes acting on same data]

    Given [item exists with version/timestamp]
    And [user A retrieves item]
    When [user B modifies item]
    And [user A attempts to modify the now-stale item]
    Then [appropriate concurrency handling occurs]
    And [either last-write-wins OR optimistic lock failure]

  #──────────────────────────────────────────────────────────────
  # DATA VARIATION SCENARIOS (Scenario Outlines)
  #──────────────────────────────────────────────────────────────

  Scenario Outline: [Multiple input combinations]
    # Business Context: [Testing various data combinations]

    Given [context with <parameter>]
    And [additional context <param2>]
    When [action with <input>]
    Then [outcome is <result>]
    And [data change is <change>]

    Examples: [Category of examples]
      | parameter | param2 | input | result | change |
      | [value1]  | [val1] | [in1] | [out1] | [chg1] |
      | [value2]  | [val2] | [in2] | [out2] | [chg2] |
      | [value3]  | [val3] | [in3] | [out3] | [chg3] |

  Scenario Outline: [Different category of variations]
    # Business Context: [Different aspect being tested]

    Given [different scenario structure]
    When [action with <variable>]
    Then [expected <outcome>]

    Examples:
      | variable | outcome |
      | [v1]     | [o1]    |
      | [v2]     | [o2]    |

  #──────────────────────────────────────────────────────────────
  # EDGE CASES
  #──────────────────────────────────────────────────────────────

  Scenario: [Specific edge case description]
    # Business Context: [Unusual but valid scenario]

    Given [edge case conditions]
    When [action executed]
    Then [expected edge case handling]

  # [Continue with additional edge cases...]

  #──────────────────────────────────────────────────────────────
  # ERROR RECOVERY SCENARIOS
  #──────────────────────────────────────────────────────────────

  Scenario: [Partial failure scenario]
    # Business Context: [What happens when operation partially fails]

    Given [conditions leading to partial failure]
    When [action attempted]
    Then [appropriate error response]
    And [rollback or cleanup occurs]
    And [system state is consistent]

  Scenario: [Retry after failure scenario]
    # Business Context: [Idempotency or retry behavior]

    Given [previous attempt failed]
    When [action is retried with same inputs]
    Then [appropriate retry behavior]
    And [idempotent outcome if applicable]
```

### Scenario Coverage Checklist

Ensure you have created scenarios for:

**Success Paths** (✓ Must have at least one):
- [ ] Primary happy path with all required inputs
- [ ] Alternative success paths with optional inputs
- [ ] Edge cases that still succeed

**Authorization** (✓ If function has authorization rules):
- [ ] User with correct permissions
- [ ] User with insufficient permissions
- [ ] Unauthenticated user
- [ ] Different permission levels if applicable

**Validation Failures** (✓ One scenario per validation rule):
- [ ] Each required field when missing
- [ ] Each field format validation
- [ ] Each business logic validation rule
- [ ] Each cross-field validation
- [ ] Each value constraint

**Not Found / Empty Results**:
- [ ] Requested item doesn't exist
- [ ] Query returns no results
- [ ] Parent entity doesn't exist (if hierarchical)

**Boundary Conditions** (✓ If numeric/size constraints exist):
- [ ] Minimum acceptable value
- [ ] Maximum acceptable value
- [ ] Below minimum (should fail)
- [ ] Above maximum (should fail)
- [ ] Zero/empty if applicable
- [ ] Null/undefined handling

**Temporal Scenarios** (✓ If dates/periods are involved):
- [ ] Current/active date ranges
- [ ] Future effective dates
- [ ] Past/expired dates
- [ ] Date range overlaps
- [ ] Invalid date relationships (end before start, etc.)

**State Transitions** (✓ If entity has states):
- [ ] Each valid state transition
- [ ] Invalid state transitions
- [ ] Initial state creation
- [ ] Terminal state handling

**Concurrent Operations** (✓ If shared data):
- [ ] Concurrent reads
- [ ] Concurrent modifications
- [ ] Optimistic locking scenarios

**Data Variations**:
- [ ] Different valid input combinations (use Scenario Outlines)
- [ ] Optional vs required parameter combinations
- [ ] Different roles/types of actors

**Error Handling**:
- [ ] Partial failures
- [ ] Retry behavior
- [ ] Rollback scenarios
- [ ] Error message clarity

**Business Rule Coverage** (✓ CRITICAL):
- [ ] Every rule in "Core Business Rules" has scenario(s)
- [ ] Every rule in "Data Rules" has scenario(s)
- [ ] Every rule in "Authorization Rules" has scenario(s)
- [ ] Every rule in "Temporal Rules" has scenario(s)

## Use Cases

### UC-[ID]: [Use Case Name]

**Actor**: [Business role performing this action]

**Goal**: [What the actor wants to achieve]

**Frequency**: [How often this occurs]

**Business Priority**: [High/Medium/Low with justification]

**Preconditions**: [Business conditions required]

**Main Success Scenario**:
1. [Actor action]
2. [System response]
3. [Outcome]

**Alternative Flows**:
- **[Alt-ID]**: [Alternative description]
  - [Steps for this alternative]

**Exceptions**:
- **[Exc-ID]**: [Exception description]
  - [How it's handled]

**Postconditions**: [Resulting business state]

**Business Rules Applied**: [List of business rules from the Business Rules section]

---

[Create use cases for ALL significant usage patterns]

## Business Domain Concepts

### [Concept 1 Name]

**Definition**: [Clear business definition]

**Business Significance**: [Why this concept matters]

**Attributes**: [Key business attributes]

**Relationships**: [How it relates to other business concepts]

**Business Rules**: [Rules governing this concept]

---

[Define ALL key business concepts referenced in this specification]

## Functional Dependencies

### Required Business Data From Other Sources

| Data/Function | Business Purpose | Required When |
|---------------|------------------|---------------|
| | | |

### Business Data/Events Provided to Other Functions

| Data/Event | Business Purpose | Consumed By |
|------------|------------------|-------------|
| | | |

## Data Validation Requirements

[Extract ALL validation rules in business terms]

### Required Field Validations

1. **[Field Name]**: Must be provided because [business reason]

### Format Validations

1. **[Field Name]**: Must conform to [format] because [business reason]

### Business Logic Validations

1. **[Validation Name]**: [Description in business terms]
   - **Example of Valid**: [Example]
   - **Example of Invalid**: [Example]
   - **Business Reason**: [Why this validation exists]

### Cross-Field Validations

1. **[Validation Name]**: [Relationship between fields that must be validated]

## Error Conditions & Business Responses

| Error Condition | Business Description | Expected Response | Data Impact |
|-----------------|---------------------|-------------------|-------------|
| | | | |

## Questions for Business Clarification

> **IMPORTANT - For Business Stakeholders**: This section should typically be **empty or minimal**.
>
> This is a modernization project. Our goal is to preserve the **exact current behavior** of the system. We determine how the system works by analyzing the existing system - we do not make changes or improvements.
>
> **Only include questions when:**
> - The current system behaves inconsistently in different situations
> - It's unclear what the system is supposed to do in a specific case
> - There appears to be unused or conflicting functionality
>
> **Never include:**
> - Suggestions for improvements ("Should we add...")
> - Preferences for how things "should" work
> - Questions about new capabilities or features
> - Questions unrelated to how the current system behaves

[If no genuine ambiguities exist, state: "No clarification needed - all behavior determined from existing system analysis."]

**Appropriate question example:**
1. **Inconsistent Date Handling**: The system sometimes treats missing end dates as "ongoing" and other times as errors. Which behavior should the modernized system preserve?

**Inappropriate questions (DO NOT include):**
- ❌ "Should we add the ability to filter by status?" (If it doesn't exist today, don't suggest adding it)
- ❌ "What order would users prefer to see results?" (Document the current order - don't ask for changes)
- ❌ "Should we add notifications when data changes?" (New feature suggestion - out of scope)

## Glossary

| Term | Business Definition | Synonyms |
|------|---------------------|----------|
| | | |

---

## Extraction Instructions

Follow these steps:

1. **Read the functional-description.md file** completely

2. **Extract business rules** from:
   - Key Business Rules section
   - Data Validation Rules section
   - Workflows (the business logic, not the technical steps)
   - Database Dependencies (translate to business entity rules)
   - Security Considerations (translate to authorization rules)

3. **Extract database operations** (CRITICAL - preserve exact technical details):
   - From "Database Dependencies Detail" section in functional-description.md
   - Copy exact table names, column names, and SQL queries
   - Document composite keys, foreign keys, and constraints
   - Preserve WHERE clauses, JOIN conditions, and query patterns
   - Map each database operation to its business purpose
   - Document transaction boundaries and isolation levels if specified
   - This is the ONE exception to "no technical details" - be precise here

4. **Transform OTHER technical details to business language** (except database):
   - "Returns boolean true/false" → "Indicates success or failure of the operation"
   - "PointCompanyDO parameter" → "Point-company relationship data"
   - "CHANGE permission required" → "User must be authorized to modify point relationships"
   - "HTTP POST request" → "User submits request"
   - "Service layer calls DAO" → [Remove - not in spec]
   - But KEEP: "DELETE FROM PT_CO_XREF WHERE..." → [Keep exact SQL in Database Operations section]

5. **Create comprehensive Gherkin scenarios**:
   - Review EVERY workflow in the source document
   - Transform each workflow into one or more Gherkin scenarios
   - Extract business context, goals, and frequency from workflows
   - Use Gherkin comments to capture business context that was in workflow narratives
   - Create a Gherkin scenario for EACH workflow path (success and error paths)
   - Cover ALL error conditions mentioned in the source
   - Include ALL validation rules as scenarios
   - Add scenario outlines for data variations
   - Use the scenario organization structure (PRIMARY SUCCESS, AUTHORIZATION, VALIDATION, etc.)
   - Reference business rules in Gherkin comments

6. **Extract business concepts**:
   - Identify key domain entities (e.g., Point, Company, Relationship, Role, Effective Period)
   - Define each in business terms
   - Document their relationships

7. **Ensure completeness**:
   - Every business rule from the source should appear in Business Rules section
   - Every database operation should appear in Database Operations section with exact SQL
   - Every validation rule should have a corresponding Gherkin scenario
   - Every workflow should be transformed into Gherkin scenario(s)
   - Every error condition should have a Gherkin scenario
   - Use the Scenario Coverage Checklist to verify completeness

8. **Verify technology neutrality (except database)**:
   - Read through your specification
   - Remove any remaining technical terms (EXCEPT in Database Operations section)
   - Database Operations section SHOULD contain exact table/column names and SQL
   - All other sections should use business language only
   - Ensure a business stakeholder could understand everything (except database details)
   - Verify no assumptions or additions beyond the original documentation

9. **Write the functional-spec.md file** in the same directory as the functional-description.md

## Quality Checklist

Before completing, verify:

**Business Requirements**:
- [ ] No implementation details remain (no code references, frameworks, technologies) - EXCEPT Database Operations section
- [ ] All business rules from source are captured
- [ ] Gherkin scenarios cover ALL workflows (each workflow becomes scenarios)
- [ ] All validation rules have Gherkin scenarios
- [ ] All error conditions from source have Gherkin scenarios
- [ ] Scenario Coverage Checklist is satisfied
- [ ] Business language used throughout (no technical jargon) - except Database Operations
- [ ] No new features or logic added beyond the original
- [ ] Business concepts are clearly defined
- [ ] A business stakeholder could read and validate most sections (except database details)
- [ ] The specification is implementation-agnostic (could be implemented in any technology)

**Database Operations** (Critical Exception):
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

## Example Transformations

### Example 1: Technical Implementation → Business Rule

**From functional-description.md** (technical):
```
DELETE PT_CO_XREF
WHERE PT_ID_NBR = ?
  AND CO_ID = ?
  AND CO_ROLE_CD = ?
  AND EFF_START_DATE = ?
  AND EFF_END_DATE = ?
Returns true if rows affected > 0, false otherwise
```

**To functional-spec.md** (business):
```
Business Rule: Complete Relationship Identifier Required
- To remove a point-company relationship, all identifying components must be specified:
  - Point identifier
  - Company identifier
  - Company's role in the relationship
  - Relationship validity start date
  - Relationship validity end date
- If a matching relationship is found and removed, the operation succeeds
- If no matching relationship exists, the operation indicates no change was made
```

### Example 2: Workflow → Gherkin Scenario

**From functional-description.md** (technical workflow):
```
### Workflow 1: Successful Point-Company Deletion

**Use Case**: Remove an expired or invalid point-company relationship from the system

**Actors**:
- Authorized user with CHANGE permissions for Point Maintenance functionality
- System administrator or data maintenance personnel

**Steps**:
1. HTTP Request Reception - Client sends POST request
2. Security Authorization Check - Verify user has permission
3. Parameter Type Auto-Conversion - Convert JSON to Java objects
4. Service Method Invocation - Call business service layer
5. Service Layer Delegation - Forward to DAO layer
6. Database Delete Execution - Execute SQL DELETE
7. Result Interpretation - Convert database result to boolean
8. Response Wrapping - Package return value
9. HTTP Response - Return to client

**Outcome**: Record removed from PT_CO_XREF table, client receives confirmation

**Error Conditions**:
- Security Exception: User lacks CHANGE permission
- Record Not Found: No matching record exists
```

**To functional-spec.md** (Gherkin with business context):
```gherkin
Scenario: Successfully remove expired point-company relationship
  # Business Context: Data maintenance personnel regularly remove expired
  # relationships to keep the system clean and accurate. This is typically
  # part of regular data hygiene processes.
  # Frequency: Daily/Weekly maintenance tasks
  # Business Value: Maintains data accuracy and prevents confusion

  Given a point-company relationship exists with all identifiers
  And the relationship is expired or no longer valid
  And the user is authorized to modify point relationships
  When the user requests removal of the relationship
  Then the relationship is removed from the system
  And a success confirmation is provided
  And the relationship no longer appears in any queries

Scenario: Unauthorized user attempts to remove relationship
  # Business Context: Ensures only authorized personnel can modify
  # critical master data relationships

  Given a point-company relationship exists
  But the user lacks authorization to modify point relationships
  When the user attempts to remove the relationship
  Then the request is rejected
  And an authorization failure is indicated
  And the relationship remains unchanged
  And no data modifications occur

Scenario: Attempt to remove non-existent relationship
  # Business Context: Handles cases where relationship was already
  # removed or never existed (idempotent operation)

  Given no matching point-company relationship exists
  And the user is authorized to modify point relationships
  When the user requests removal with specific identifiers
  Then the system indicates no change was made
  And no error is raised
  And the system state remains consistent
```

**Key points in this transformation**:
- Technical layers (HTTP, DAO, Service) are removed
- Implementation details (POST, JSON, SQL) are removed
- Business context is preserved in comments
- Actor information becomes Given conditions
- Steps are consolidated into business-level Given/When/Then
- Each error condition becomes its own scenario
- Frequency and business value are captured in comments

### Example 3: Database Operations → Preserved Exactly

**From functional-description.md** (Database Dependencies Detail section):
```
### Table: PT_CO_XREF

**Operations**: DELETE

**Business Purpose**: Point-Company Cross-Reference table that maintains the many-to-many
relationships between transportation points and companies...

**Key Columns Used**:
- PT_ID_NBR: Point ID Number - Primary key component
- CO_ID: Company ID - Primary key component
- CO_ROLE_CD: Company Role Code - Primary key component
- EFF_START_DATE: Effective Start Date - Primary key component
- EFF_END_DATE: Effective End Date - Primary key component

**SQL Statement**:
DELETE PT_CO_XREF
WHERE PT_CO_XREF.PT_ID_NBR = ?
  AND PT_CO_XREF.CO_ID = ?
  AND PT_CO_XREF.CO_ROLE_CD = ?
  AND PT_CO_XREF.EFF_START_DATE = ?
  AND PT_CO_XREF.EFF_END_DATE = ?

**Foreign Key Implications**: If foreign key constraints exist on tables referencing
PT_CO_XREF, deletion may fail with constraint violation errors.
```

**To functional-spec.md** (Database Operations section - PRESERVED EXACTLY):
```markdown
## Database Operations

### Tables and Views Involved

#### Table: PT_CO_XREF

**Business Purpose**: Point-Company Cross-Reference table that maintains the many-to-many
relationships between transportation points and companies, including the role each company
plays and the time period during which the relationship is valid.

**Operations**: DELETE

**Columns Used**:

| Column Name | Data Type | Business Meaning | Used In | Constraints |
|-------------|-----------|------------------|---------|-------------|
| PT_ID_NBR | Number | Point identifier | WHERE | PK, FK → PT |
| CO_ID | Number | Company identifier | WHERE | PK, FK → CO |
| CO_ROLE_CD | Code | Company's role (shipper, receiver, carrier, etc.) | WHERE | PK, FK → SYS_CD_CO_ROLE |
| EFF_START_DATE | Date | Start of relationship validity period | WHERE | PK |
| EFF_END_DATE | Date | End of relationship validity period | WHERE | PK |

**Primary Key**: (PT_ID_NBR, CO_ID, CO_ROLE_CD, EFF_START_DATE, EFF_END_DATE)

**Foreign Keys**:
- PT_ID_NBR references PT(PT_ID_NBR) - Links to Points master table
- CO_ID references CO(CO_ID) - Links to Companies master table
- CO_ROLE_CD references SYS_CD_CO_ROLE(CODE) - Links to Company Role system codes

---

### Query Operations

#### Operation: Delete Point-Company Relationship

**SQL Operation Type**: DELETE

**Purpose**: Remove a specific point-company relationship record identified by all five
composite key fields

**Query Pattern**:
```sql
DELETE FROM PT_CO_XREF
WHERE PT_CO_XREF.PT_ID_NBR = ?
  AND PT_CO_XREF.CO_ID = ?
  AND PT_CO_XREF.CO_ROLE_CD = ?
  AND PT_CO_XREF.EFF_START_DATE = ?
  AND PT_CO_XREF.EFF_END_DATE = ?
```

**Parameters**:
- `?` → PT_ID_NBR (Point identifier)
- `?` → CO_ID (Company identifier)
- `?` → CO_ROLE_CD (Company role code)
- `?` → EFF_START_DATE (Effective start date)
- `?` → EFF_END_DATE (Effective end date)

**Expected Result**: Number of rows affected (1 if deleted, 0 if not found)

**Business Rule Enforced**: Complete Relationship Identifier Required - all five key
components must match exactly for deletion to occur

**Performance Notes**: Composite primary key ensures efficient lookup by all five fields

---

### Data Integrity Rules (Database Level)

**Composite Keys**:
1. **PT_CO_XREF**: Unique record identified by (PT_ID_NBR, CO_ID, CO_ROLE_CD,
   EFF_START_DATE, EFF_END_DATE)
   - **Business Meaning**: Same point-company pair can have multiple relationships with
     different roles or different effective date ranges

**Foreign Key Constraints**:
1. **PT_CO_XREF.PT_ID_NBR → PT.PT_ID_NBR**
   - **Business Meaning**: Relationship must reference a valid point
   - **On Delete**: RESTRICT - Cannot delete relationship if point doesn't exist

2. **PT_CO_XREF.CO_ID → CO.CO_ID**
   - **Business Meaning**: Relationship must reference a valid company
   - **On Delete**: RESTRICT - Cannot delete relationship if company doesn't exist

3. **PT_CO_XREF.CO_ROLE_CD → SYS_CD_CO_ROLE.CODE**
   - **Business Meaning**: Role must be a valid system code value
   - **On Delete**: RESTRICT - Cannot delete relationship with invalid role code
```

**Key points in this transformation**:
- ✅ Table name PT_CO_XREF is preserved exactly (not "point company table")
- ✅ Column names PT_ID_NBR, CO_ID, etc. are preserved exactly (not translated to business terms)
- ✅ SQL query is copied verbatim
- ✅ WHERE clause is complete and exact
- ✅ Composite key is fully documented with all five columns
- ✅ Foreign key relationships are captured with referenced tables
- ✅ Business purpose is ADDED to provide context
- ✅ This is the ONE section where technical precision is required

## Begin

Ask the user for the path to the functional-description.md file, then create the functional-spec.md file following all instructions above.
