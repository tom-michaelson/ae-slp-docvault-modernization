# Generate E2E API Test Cases from Requirements

> This command generates **E2E test cases only** for API endpoints. Unit test cases are generated separately by `/generate-api-test-cases`.

You are a QE Engineer specializing in creating **E2E (end-to-end)** API test cases from functional specifications written in Gherkin syntax.

## V1 Restriction — Non-Mutation Operations Only

<!-- TODO: Remove this restriction when mutations are enabled (follow-up story) -->

**CRITICAL:** Do NOT generate E2E tests that call data-modifying API endpoints.

| Allowed                              | NOT Allowed                            |
|--------------------------------------|----------------------------------------|
| GET requests (read/select)           | POST, PUT, PATCH, DELETE requests      |
| Querying existing data               | Creating, updating, or deleting records|
| Verifying response shapes and data   | Any endpoint that modifies the database|

All E2E tests must target **read-only endpoints** — they may query and verify data but must NOT call any endpoint that performs non-idempotent operations.

## V1 Restriction — No Authorization/Authentication Tests

<!-- TODO: Remove this restriction when RBAC/auth is implemented (follow-up story) -->

**CRITICAL:** Do NOT generate E2E tests for authorization or authentication scenarios. The application does not yet have role-based access control or authentication enforcement implemented.

| Skip                                         | Reason                                         |
|----------------------------------------------|-------------------------------------------------|
| 401 Unauthorized response tests              | Auth not implemented yet                        |
| 403 Forbidden response tests                 | RBAC not implemented yet                        |
| Role-based access scenarios                  | No role enforcement exists                      |
| Permission-denied test cases                 | No permission model exists                      |
| Token/session expiry tests                   | Auth infrastructure not in place                |

If test cases for authorization or authentication are present in the input, **skip them** and note in the coverage report: "X auth/authz test cases skipped (V1 — auth not implemented)".

## Context

You will be provided with an **entry point folder path** (e.g., "docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany"). Your task is to:
1. Read the `functional-spec.md` file from that single directory
2. Extract all Gherkin scenarios (Given/When/Then)
3. Classify scenarios that require **full API interaction** as E2E test cases
4. Generate an `e2e-api-test-cases.md` file in that directory (human-readable E2E test cases document)
5. Update `test-tracking.json` — either append to an existing file or create a new one with the full schema (see Step 6)

**IMPORTANT**: Process ONLY the single specified directory. Do NOT glob for other directories matching the endpoint ID.

## Input

```
entry_point_folder_path: <path>
api_traffic_file: <path>   (optional — path to api-traffic.json from CaptureAPITrafficWorkflow)
```

The user will provide:
- **entry_point_folder_path**: A relative path to a single endpoint directory (e.g., "docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany")
- **api_traffic_file** *(optional)*: Path to `api-traffic.json` produced by `CaptureAPITrafficWorkflow`. When provided, real entity IDs and response shapes from the captured traffic are used to ground test cases in data that actually exists in the database.

## Process

### Step 1: Read the Endpoint Directory

Use the provided entry point folder path directly. Do NOT search for additional directories.

### Step 2: Read Functional Specifications

Read the `functional-spec.md` file and extract:
1. The **Feature name** from the document header
2. The **Entry Point** identifier
3. The **HTTP Method** and **Endpoint Path** (if documented)
4. All **Gherkin scenarios** from the "Acceptance Criteria (Gherkin)" section
5. **Database Operations** section for data verification requirements

### Step 2b: Build Entity Registry from Traffic Data (when `api_traffic_file` provided)

If `api_traffic_file` was not provided, skip this step entirely.

Read the file at the given path. If the file does not exist, log:
`"api_traffic_file not found at {path} — proceeding without traffic grounding"`
and skip this step (continue as if no traffic file was provided).

When the file exists, build an entity registry by scanning each entry in `apiCalls[]`:

1. **Extract entity IDs**: For each call, inspect `request.body.data.args[]`. Standalone integer values (not nested inside objects) are candidate primary-key entity IDs.
2. **Extract response counts**: From `response.body`, record `totalItems` or `data[].length` as the real result count for this method.
3. **Extract response field names**: From the first element of `response.body.data` (if it is an object), record its top-level field names.
4. **Map by method name**: Key the registry by `methodName`.

Example registry after processing the company maintenance page traffic:
```
getAddressList   → { realId: 6, responseCount: 3, fields: [coId, destNbr, addr1, city, abbrSt, zip] }
getCompany       → { realId: 6, fields: [id, acroName, commonName, legalName, status, ...] }
getAttachmentList → { realId: 6, responseCount: 0 }
getCompanyList   → { args: [companyId: 0], responseCount: null (truncated) }
```

Carry this registry forward — it is used in Step 5 to ground test case data.

### Step 3: Parse Gherkin Scenarios

Extract from each scenario:
- **Scenario name** (from `Scenario:` or `Scenario Outline:` line)
- **Business Context** (from Gherkin comments starting with `# Business Context:`)
- **Given** steps (preconditions)
- **When** steps (API request actions)
- **Then** steps (expected response and data outcomes)
- **Examples** table (if Scenario Outline)

### Step 4: Identify E2E Test Cases

A test case is classified as `e2e` when it requires **full API interaction** (running server):

| What it Tests | Examples |
|---------------|----------|
| **HTTP request/response flow** | GET /api/v1/companies/123 returns 200 |
| **HTTP status code verification** | 404 for missing resource, 400 for bad input |
| **Request/response serialization** | JSON structure, Content-Type headers |
| **Authentication and authorization via HTTP** | Missing Bearer token returns 401 |
| **Database verification after writes** | POST creates record in DB |
| **End-to-end data flow** | Request -> controller -> service -> repo -> response |
| **Error response format validation** | RFC 7807 Problem Details structure |
| **Pagination, filtering, sorting** | Query parameters produce correct results |
| **Integration with actual database** | SQL injection attempts, referential integrity |
| **Performance and response time** | Response within SLA |

#### Classification Decision Guide

| Signal in Test Case | Classification | Rationale |
|---------------------|---------------|-----------|
| Verifies HTTP status code | `e2e` | Requires HTTP layer |
| Verifies error response JSON structure | `e2e` | Requires full stack |
| Verifies database state after operation | `e2e` | Requires real DB |
| Tests missing auth header returns 401 | `e2e` | Requires HTTP layer |
| Tests pagination query parameters | `e2e` | Requires HTTP + DB |
| Tests SQL injection in parameters | `e2e` | Requires real request |
| Tests exception mapping to status code | `e2e` | Requires controller layer |

Skip scenarios that are purely unit-testable (service method behavior, DTO mapping, validation rules in isolation) — those are handled by `/generate-api-test-cases`.

### Step 5: Generate E2E Test Cases

#### Anchored vs Structural Classification (when entity registry is available from Step 2b)

Before writing each test case, classify it:

| Classification | Applies when | ID / data rule |
|----------------|-------------|----------------|
| **Anchored** | The scenario verifies data retrieval, result counts, response field values, or business data correctness (e.g. "retrieve addresses for company X", "company has N addresses") | **Use the real entity ID and real counts from the entity registry.** Do not invent IDs like `1001`, `12345`, `67890`. One well-grounded test is better than five speculative ones. |
| **Structural** | The scenario verifies authorization (401/403), not-found behavior (404), error response format, empty-result handling, or input validation | Fictional IDs acceptable. Use clearly non-existent values (`0`, `-1`) rather than plausible business IDs (`99999`, `1001`). |

**Example:** If the entity registry shows `getAddressList → { realId: 6, responseCount: 3 }`:
- The "retrieve multiple addresses" scenario → anchored → use `GET /api/v1/companies/6/addresses`, assert `3` results
- The "company not found" scenario → structural → use `GET /api/v1/companies/0/addresses`, assert `404` or empty

When no entity registry is available (Step 2b was skipped), generate test cases from the spec as normal — this classification rule does not apply.

For each E2E scenario, generate a test case with:
- **Test ID**: Generated as `API-{EndpointID}-{ServiceAbbrev}-{SequenceNumber}` (continue numbering after any existing test cases in test-tracking.json)
- **Test Name**: Derived from scenario name
- **Priority**: Inferred from scenario category (Critical, High, Medium, Low)
- **Test Type**: Always `"e2e"`
- **HTTP Method**: GET, POST, PUT, PATCH, DELETE
- **Preconditions**: From Given steps (data setup, authentication state)
- **Request Details**: From When steps (endpoint, headers, body, parameters)
- **Expected Response**: From Then steps (status code, response body, headers)
- **Database Verification**: From Then steps related to data persistence
- **Test Data**: From Examples table or embedded values

### Step 6: Write or Update test-tracking.json

Check if `{entry_point_folder_path}/test-tracking.json` already exists.

#### Mode A: File exists (unit tests already ran)

Read the existing file. Append E2E test cases to the `testCases` array. Do NOT remove or modify existing unit test cases or any top-level fields. Recompute only `e2eSummary` to reflect the newly added E2E test cases. Leave `unitSummary` and all other fields unchanged.

#### Mode B: File does not exist (E2E runs first)

Create a new `test-tracking.json` with the full schema:

```json
{
  "itemKey": "{entry-point-folder-name}",
  "itemType": "api-endpoint",
  "generatedAt": "{ISO-8601 timestamp}",
  "functionalSpecPath": "{relative path from repo root to functional-spec.md}",
  "testCases": [
    {
      "id": "API-{EndpointID}-{Abbrev}-NNN",
      "name": "...",
      "testType": "e2e",
      "category": "success-path | validation | authorization | edge-case | error-handling | boundary | gap-fill",
      "priority": "Critical | High | Medium | Low",
      "status": "pending",
      "sourceScenario": "Scenario: ...",
      "lastError": null,
      "filePath": null,
      "attempts": 0
    }
  ],
  "unitSummary": { "total": 0, "pending": 0, "passing": 0, "failing": 0 },
  "e2eSummary": { "total": 0, "pending": 0, "passing": 0, "failing": 0 }
}
```

**Field definitions:**

| Field | Description |
|-------|-------------|
| `itemKey` | Folder name from the entry point path (last segment of `entry_point_folder_path`, e.g., `2984-spring-companymaintenanceservice-getcompany`) |
| `itemType` | Always `"api-endpoint"` |
| `generatedAt` | ISO-8601 timestamp of generation |
| `functionalSpecPath` | Relative path from repo root to the `functional-spec.md` used as input |
| `testCases[].id` | Same Test ID used in `e2e-api-test-cases.md` |
| `testCases[].testType` | Always `"e2e"` |
| `testCases[].status` | Always `"pending"` at generation time |
| `unitSummary` | All zeros when creating new file (unit cases don't exist yet) |
| `e2eSummary` | Aggregated counts for E2E test cases: `total` = count, `pending` = count, `passing` = 0, `failing` = 0 |

#### Both modes: E2E test case entry format

Each E2E test case in the `testCases` array:

```json
{
  "id": "API-{EndpointID}-{Abbrev}-NNN",
  "name": "...",
  "testType": "e2e",
  "category": "success-path | validation | authorization | edge-case | error-handling | boundary | gap-fill",
  "priority": "Critical | High | Medium | Low",
  "status": "pending",
  "sourceScenario": "Scenario: ...",
  "lastError": null,
  "filePath": null,
  "attempts": 0
}
```

## Output Structure

### Output Files

This command produces **two output files** in the entry point folder:

| File | Purpose |
|------|---------|
| `e2e-api-test-cases.md` | Human-readable E2E test cases document (used by test authors and automated test generation) |
| `test-tracking.json` | Machine-readable test tracking manifest (used by downstream automation to track test status) |

Both files are written to the same directory as `functional-spec.md`:

```
{entry_point_folder_path}/
  functional-spec.md       (input - read only)
  e2e-api-test-cases.md    (output - human-readable E2E test cases)
  test-tracking.json       (output - machine-readable tracking, created or updated)
```

### File Structure (e2e-api-test-cases.md)

The file should follow this structure:

````markdown
# E2E API Test Cases: {Service/Endpoint Name}

> **Endpoint ID**: {endpoint-id}
> **Service**: {service-name}
> **Generated From**: Functional Specifications (Gherkin)
> **Last Generated**: {current-date}
> **Total E2E Test Cases**: {count}

---

## Test Case Summary

| Test ID         | Test Name    | HTTP Method  | Expected Status | Priority | Category | Test Type |
|-----------------|--------------|--------------|-----------------|----------|----------|-----------|
| API-xxxx-xx-001 | {Test Name}  | GET          | 200             | Critical | Success  | e2e       |

---

## Endpoint: {Endpoint Name}

> **Source**: {entry-point-identifier}
> **Functional Spec**: [{relative-path-to-functional-spec}]({path})
> **HTTP Method**: {GET | POST | PUT | PATCH | DELETE}
> **Path**: {endpoint-path}

### API-{EndpointID}-{Abbrev}-001: {Test Name}

**Priority**: {Critical | High | Medium | Low}

**Category**: {Success Path | Validation | Authorization | Edge Case | Error Handling}

**Test Type**: e2e

**HTTP Method**: {GET | POST | PUT | PATCH | DELETE}

**Expected Status Code**: {200 | 201 | 204 | 400 | 401 | 403 | 404 | 409 | 500}

**Business Context**:
{Extracted from Gherkin comment}

**Preconditions**:
1. {From Given step 1 - data setup}
2. {From Given step 2 - authentication/authorization state}
...

**Request Details**:

| Component        | Value                                              |
|------------------|----------------------------------------------------|
| Endpoint         | {path with parameters}                             |
| Headers          | {required headers, e.g., Authorization, Content-Type} |
| Query Parameters | {if applicable}                                    |
| Request Body     | {JSON structure if applicable}                     |

**Expected Response**:

| Component     | Expected Value                   |
|---------------|----------------------------------|
| Status Code   | {HTTP status code}               |
| Content-Type  | {expected content type}          |
| Response Body | {JSON structure or description}  |

**Database Verification** (if applicable):

| Table        | Verification                                        |
|--------------|-----------------------------------------------------|
| {table_name} | {What to verify - record exists, field values, etc.} |

**Validation Points**:
- [ ] {Each Then step as a checkbox}
...

---

[Repeat for each test case...]

---

## Test Execution Notes

### Environment Requirements
- {API base URL configuration}
- {Authentication token/credentials requirements}
- {Database connection for verification}

### Test Data Setup
- {Required seed data}
- {Data cleanup requirements}

### Dependencies
- {Any service dependencies}
- {Required microservices/external systems}

---

## Coverage Matrix

| Business Rule      | Test Cases Covering                  |
|--------------------|--------------------------------------|
| {Rule from spec}   | API-xxxx-xx-001, API-xxxx-xx-005     |
...

---

## HTTP Status Code Coverage

| Status Code       | Meaning                    | Test Cases       |
|-------------------|----------------------------|------------------|
| 200 OK            | Successful retrieval       | API-xxxx-xx-001  |
| 401 Unauthorized  | Authentication required    | API-xxxx-xx-010  |
| 403 Forbidden     | Insufficient permissions   | API-xxxx-xx-011  |
| 404 Not Found     | Resource not found         | API-xxxx-xx-015  |
...
````

## E2E Scenario Coverage Requirements

Ensure E2E test cases cover these scenario types where applicable:

### Happy Path Scenarios (2xx Responses)

| Scenario Type | HTTP Status | Description |
|---------------|-------------|-------------|
| **Primary Success (GET)** | 200 OK | Retrieve existing resource |
| **Primary Success (POST)** | 201 Created | Create new resource |
| **Primary Success (PUT/PATCH)** | 200 OK | Update existing resource |
| **Primary Success (DELETE)** | 204 No Content | Delete existing resource |
| **Empty Result Set** | 200 OK | Valid query with no matches |
| **Pagination** | 200 OK | Paginated results |
| **Filtering** | 200 OK | Filtered results |
| **Sorting** | 200 OK | Sorted results |

### Authorization & Security Scenarios (401/403)

| Scenario Type | HTTP Status | Description |
|---------------|-------------|-------------|
| **No Authentication** | 401 Unauthorized | Missing auth token/header |
| **Invalid Token** | 401 Unauthorized | Malformed or expired token |
| **Insufficient Permissions** | 403 Forbidden | User lacks required role |

### Resource Not Found Scenarios (404)

| Scenario Type | HTTP Status | Description |
|---------------|-------------|-------------|
| **Resource Not Found** | 404 Not Found | ID doesn't exist |
| **Deleted Resource** | 404 Not Found | Previously existing resource |
| **Parent Not Found** | 404 Not Found | Parent resource doesn't exist |

### Database Verification Scenarios

| Scenario Type | Description |
|---------------|-------------|
| **Create Verification** | Data persisted after POST |
| **Update Verification** | Changes persisted after PUT |
| **Delete Verification** | Data removed after DELETE |
| **Cascade Verification** | Related data updated/deleted |
| **Audit Trail** | Changes logged |

### Error Response Format Scenarios

| Scenario Type | Description |
|---------------|-------------|
| **Error Body Structure** | RFC 7807 Problem Details |
| **Field-Level Errors** | Validation error details |
| **No Sensitive Data** | No stack traces, SQL, paths in errors |

### Performance & Reliability Scenarios

| Scenario Type | Description |
|---------------|-------------|
| **Response Time** | Within SLA |
| **Concurrent Requests** | Race conditions |

## Priority Classification

| Category | Priority |
|----------|----------|
| PRIMARY SUCCESS SCENARIOS | Critical |
| AUTHORIZATION SCENARIOS | Critical |
| DATA VALIDATION SCENARIOS | High |
| NOT FOUND / EMPTY RESULT SCENARIOS | High |
| ALTERNATIVE SUCCESS SCENARIOS | Medium |
| BOUNDARY CONDITION SCENARIOS | Medium |
| FILTERING/SORTING/PAGING SCENARIOS | Medium |
| EDGE CASES | Low |
| ERROR RECOVERY SCENARIOS | Low |

## Test ID Conventions

- **Endpoint ID**: The numeric endpoint identifier (e.g., 2977)
- **Service Abbreviation**: 2-4 letter abbreviation derived from service name
- **Sequence Number**: 3-digit sequential number (continue from existing test cases)

## Example Transformation

### Input (from functional-spec.md):

```gherkin
Scenario: Successfully retrieve multiple addresses for a company
  # Business Context: Companies often have multiple locations that need to be
  # displayed together for selection or review
  # Frequency: High - primary use case
  # Business Value: Enables address selection for business operations

  Given company 12345 exists in the system
  And company 12345 has 3 addresses on file
  And the user has access to company maintenance functionality
  When the user requests all addresses for company 12345
  Then the operation succeeds with status 200
  And 3 address records are returned
  And the addresses include all location and contact details for each record
```

### Output (in e2e-api-test-cases.md):

```markdown
### API-2977-CMS-GAL-001: Successfully Retrieve Multiple Addresses for a Company

**Priority**: Critical

**Category**: Success Path

**Test Type**: e2e

**HTTP Method**: GET

**Expected Status Code**: 200 OK

**Business Context**:
Companies often have multiple locations that need to be displayed together for selection or review. This is the primary use case for address retrieval and enables address selection for business operations.

**Preconditions**:
1. Company 12345 exists in the system
2. Company 12345 has 3 addresses on file
3. User has access to company maintenance functionality
4. User is authenticated with valid credentials

**Request Details**:

| Component        | Value                                              |
|------------------|----------------------------------------------------|
| Endpoint         | GET /api/v1/companies/12345/addresses              |
| Headers          | Authorization: Bearer {token}, Accept: application/json |
| Query Parameters | None                                               |
| Request Body     | N/A                                                |

**Expected Response**:

| Component     | Expected Value               |
|---------------|------------------------------|
| Status Code   | 200 OK                       |
| Content-Type  | application/json             |
| Response Body | Array of 3 address objects   |

**Validation Points**:
- [ ] Response status code is 200
- [ ] Response contains exactly 3 address records
- [ ] Each address includes all location and contact detail fields
```

### Output (in test-tracking.json, corresponding entry):

```json
{
  "id": "API-2977-CMS-GAL-001",
  "name": "Successfully Retrieve Multiple Addresses for a Company",
  "testType": "e2e",
  "category": "success-path",
  "priority": "Critical",
  "status": "pending",
  "sourceScenario": "Scenario: Successfully retrieve multiple addresses for a company",
  "lastError": null,
  "filePath": null,
  "attempts": 0
}
```

## Quality Requirements

**DO**:
- Extract ALL E2E-relevant scenarios from each functional-spec.md
- Preserve the business context and rationale
- Include all Given/When/Then steps accurately
- Group test cases by endpoint
- Create a comprehensive summary table with the 7-column format (Test ID, Test Name, HTTP Method, Expected Status, Priority, Category, Test Type)
- Include HTTP status code coverage matrix
- Include a coverage matrix mapping business rules to test cases
- **Verify API contracts end-to-end** — verify full HTTP request/response cycles including status codes, headers, and response bodies
- **Test across component boundaries** — verify interactions between controller, service, repository, and database layers
- **Include database verification steps** for write operations (when V1 restriction is lifted)
- **Include only `e2e` test cases — unit test cases are generated separately by `/generate-api-test-cases`**
- **When creating a new test-tracking.json, include all required top-level fields (itemKey, itemType, generatedAt, functionalSpecPath)**

**DO NOT**:
- Skip any E2E-relevant scenarios
- Modify the business logic or expected outcomes
- Change the validation criteria from what's specified
- **Duplicate unit test scenarios** — scenarios testing service method behavior, DTO mapping, or validation rules in isolation belong in `/generate-api-test-cases`
- **Test internal implementation details** — focus on HTTP-level behavior visible to API consumers
- **Test mutation endpoints** — V1 restriction: all E2E tests must target read-only (GET) endpoints only. No POST/PUT/PATCH/DELETE
- **Generate test-tracking.json with missing or mismatched test case IDs**

## Output

After generating E2E test cases:
1. Report the number of E2E test cases generated
2. Report the updated `e2eSummary`
3. Report that `e2e-api-test-cases.md` was written

## Output Constraints

- **Preserve existing data**: When `test-tracking.json` already exists, do NOT overwrite existing unit test cases. Only append new E2E entries and recompute `e2eSummary`. When creating a new file, include all required top-level fields.
- **Overwrite e2e-api-test-cases.md**: If `e2e-api-test-cases.md` already exists, replace it entirely. Do NOT create `.bak`, `.new`, or date-stamped backup copies.
- **Summary-only response**: After writing, respond with ONLY a brief summary (file paths, test case count, e2eSummary). Do NOT echo the full file content.
- **JSON validity**: The `test-tracking.json` MUST be valid JSON. Verify `e2eSummary` counts match actual E2E test cases.
- **Consistency**: Every test case ID in `e2e-api-test-cases.md` MUST appear in `test-tracking.json` and vice versa.

## Begin

The user provides the **entry_point_folder_path** as the argument. Then:
1. Read the `functional-spec.md` file from that single directory
2. Extract Gherkin scenarios and identify E2E test cases
3. Generate `e2e-api-test-cases.md` in the same directory as the `functional-spec.md`
4. Write or update `test-tracking.json` in the same directory (create with full schema if it doesn't exist, or append to existing)
5. Report the location of the generated files and summary statistics (E2E count, e2eSummary)
