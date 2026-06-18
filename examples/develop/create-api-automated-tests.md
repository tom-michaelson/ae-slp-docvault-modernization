# Create API Automated Tests (Java APIRequestContext)

> **CRITICAL — LANGUAGE AND DIRECTORY**
>
> - **Language**: JAVA. All generated test files MUST be `.java` files.
> - **Output directory**: `passage-api/src/test/apirequestcontext/` — NEVER generate files in `passage-ui/`.
> - **Self-verification**: After generating, run:
>   ```bash
>   # MUST find .java files
>   find passage-api/src/test/apirequestcontext -name "*.java" -newer /tmp/api-gen-marker | head -20
>   # MUST find NOTHING new
>   find passage-ui/e2e -name "*.ts" -newer /tmp/api-gen-marker 2>/dev/null | head -5
>   ```
>   If any `.ts` files appear under `passage-ui/e2e/`, you have generated in the WRONG directory. Delete them and regenerate.
> - **Before starting**: `touch /tmp/api-gen-marker` to set the timestamp baseline.

You are a QE Automation Engineer specializing in creating Java APIRequestContext E2E tests in Java from comprehensive API test cases.

## V1 Restriction — Read-Only (GET) Endpoints Only

<!-- TODO: Remove this restriction when stateful tests are enabled (follow-up story) -->

**CRITICAL:** Do NOT generate automated tests for data-modifying API endpoints.

| Allowed                              | NOT Allowed                            |
|--------------------------------------|----------------------------------------|
| GET requests (read/select)           | POST, PUT, PATCH, DELETE requests      |
| Querying existing data               | Creating, updating, or deleting records|
| Verifying response shapes and data   | Any endpoint that modifies the database|

Only generate test classes for **read-only endpoints** — `{Feature}ListApiTest.java` and `{Feature}GetByIdApiTest.java`. Do NOT generate `{Feature}CreateApiTest.java`, `{Feature}UpdateApiTest.java`, or `{Feature}DeleteApiTest.java`.

If test cases for POST/PUT/PATCH/DELETE are present in the input, **skip them** and note in the coverage report: "X mutation test cases skipped (V1 read-only restriction)".

## V1 Restriction — No Authorization/Authentication Tests

<!-- TODO: Remove this restriction when RBAC/auth is implemented (follow-up story) -->

**CRITICAL:** Do NOT generate automated tests for authorization or authentication scenarios. The application does not yet have role-based access control or authentication enforcement implemented.

| Skip                                         | Reason                                         |
|----------------------------------------------|-------------------------------------------------|
| 401 Unauthorized response tests              | Auth not implemented yet                        |
| 403 Forbidden response tests                 | RBAC not implemented yet                        |
| Role-based access test classes               | No role enforcement exists                      |
| Permission-denied scenarios                  | No permission model exists                      |
| Token/session expiry tests                   | Auth infrastructure not in place                |

Do NOT generate `{Feature}AuthorizationApiTest.java` or any test class focused on auth. If test cases for authorization or authentication are present in the input, **skip them** and note in the coverage report: "X auth/authz test cases skipped (V1 — auth not implemented)".

## Context

You will be provided with an **entry point folder path** (e.g., "docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany").

An optional **test_tracking_file** argument may be provided (path to a `test-tracking.json` file). When present, only generate automated tests for test cases with `"testType": "e2e"` in the tracking file. Skip any test cases classified as `"testType": "unit"` — those are handled separately by the unit test workflow.

An optional **api_traffic_file** argument may be provided (path to an `api-traffic.json` file from the CaptureAPITrafficWorkflow). When present, read the file to extract real captured API traffic — actual endpoint paths, request payload structures, response shapes, and HTTP methods — to inform more accurate test implementation. This file contains real request/response data captured from the legacy system.

This command uses an **orchestrator + subagent pattern** to handle endpoints with many test cases. You (the main agent) read the test cases, create shared scaffolding (base classes, fixtures, payloads), then spawn Task subagents to generate test classes in parallel — each subagent gets a fresh context window with only its assigned test cases.

**IMPORTANT**: Process ONLY the single specified directory. Do NOT glob for other directories matching the endpoint ID.

## Architecture Principle

**CRITICAL**: Follow the Playwright Java APIRequestContext test patterns:

- **API E2E Tests** (`passage-api/src/test/java/.../apitests/`): Full end-to-end tests using Playwright APIRequestContext in Java
- **API Fixtures** (`passage-api/src/test/java/.../apifixtures/`): Reusable fixtures and payload builders
- **API Utilities** (`passage-api/src/test/java/.../apiutils/`): Request/response helpers and assertion utilities
- **Test Data** (`passage-api/src/test/resources/testdata/`): YAML test data files

This architecture ensures:
- Maximum code reuse across all tests
- Consistent behavior for common operations
- Easy maintenance when patterns change
- Clear separation between test specs, fixtures, and utilities
- Tests written in same language as the API code (Java)

---

## Process — Orchestrator + Subagent Pattern

### Phase A: Read, Plan, and Scaffold (Main Agent)

Complete these steps yourself before launching any subagents.

#### A1. Read Test Cases File

Use the provided entry point folder path directly. Do NOT search for additional directories.

Verify that `api-test-cases.md` exists in the specified directory:
- If found, proceed to read and process
- If not found, report that the test cases file is missing

Extract:
1. **API Endpoint** from the document header
2. **Feature name** from the document header
3. All **Test Cases** including:
   - Test ID
   - Test Name
   - Priority (Critical, High, Medium, Low)
   - Category (Success Path, Validation, Authorization, Error Handling, etc.)
   - Business Context
   - Preconditions
   - Request Details (HTTP Method, URL, Headers, Body)
   - Expected Response (Status Code, Body, Headers)
   - Test Data (if applicable)
   - Validation Points

**Build a test case inventory**: Create a list of ALL test case IDs with their categories. You will use this in Phase C to verify coverage.

**If `test_tracking_file` was provided**: Read the JSON file and filter your test case inventory to only include test cases whose IDs match entries with `"testType": "e2e"` in the tracking file. Log how many test cases were filtered out (unit tests skipped).

**If `api_traffic_file` was provided**: Read the JSON file. It contains:
- `captureMetadata`: page key, menu path, features list
- `apiCalls[]`: Array of captured API calls, each with:
  - `endpoint`: Service path (e.g., `service/public/security/preauth`)
  - `methodName`: RPC method name (may be null)
  - `httpMethod`: HTTP method (POST, GET, etc.)
  - `capturePhase`: Which UI interaction triggered this call (e.g., `page-load`, `retrieve`, `tab:details`)
  - `request.url`: Full URL
  - `request.body.data.methodName`: RPC method name
  - `request.body.data.args`: Request arguments array
  - `request.body.data.argTypes`: Java type names for arguments
  - `response.status`: HTTP status code
  - `response.body`: Response payload (may be null or truncated)

Build a **traffic summary** mapping each unique endpoint+methodName to its request/response shapes. You will include this in the subagent prompts.

#### A2. Analyze Existing Test Infrastructure

Check the existing test directory structure at `passage-api/src/test/`:
1. Review existing API tests in `java/.../apitests/`
2. Review existing fixtures in `java/.../apifixtures/`
3. Review existing utilities in `java/.../apiutils/`
4. Review test data in `resources/testdata/`
5. Identify reusable patterns - DO NOT duplicate existing utilities

#### A3. Analyze Related Source Code

Locate and read the related source files to understand:
1. **API Endpoint Structure**: Find the controller handling the API endpoint
2. **Request/Response DTOs**: Find request/response data structures
3. **Validation Rules**: Identify validation constraints
4. **Business Logic**: Understand the expected behavior
5. **Captured Traffic Reference** (if `api_traffic_file` provided): Cross-reference the captured API calls with the source code analysis. Use the real request payload shapes (`args`, `argTypes`) and response structures to validate your understanding of the DTOs and build more accurate payload builders.

#### A4. Create Shared Scaffolding

Create these shared files yourself (they must exist before subagents run):

1. **Base API Test Class** (`BaseApiTest.java`) — if not already present:
   - Playwright setup/teardown, APIRequestContext, ObjectMapper
   - See Base API Test Class reference below

2. **Request/Response Helpers** (`RequestHelpers.java`, `ResponseHelpers.java`) — if not already present:
   - HTTP request utilities, response assertion utilities
   - See reference sections below

3. **Payload Builder** (`{Feature}Payloads.java`):
   - Factory methods for valid/invalid request payloads
   - Based on the DTOs and validation rules from source code analysis
   - **If `api_traffic_file` provided**: Use the captured request/response data to populate realistic field names and value shapes in the payload builder. For example, if captured traffic shows `args: [{"companyId": 123}]` with `argTypes: ["java.util.HashMap"]`, use these real field names and types.

4. **Test Data YAML** (`passage-api/src/test/resources/testdata/api/{feature}.yml`):
   - Valid/invalid data scenarios

#### A5. Group Test Cases by Test Class

Group ALL test case IDs by their target output test class. Use these categories:

| Test Class | Test Categories |
|------------|----------------|
| `{Feature}ListApiTest.java` | GET list/search — pagination, filtering, sorting |
| `{Feature}GetByIdApiTest.java` | GET by ID — success, not found, invalid ID |
| ~~`{Feature}CreateApiTest.java`~~ | ~~POST create~~ — **V1: SKIP (read-only restriction)** |
| ~~`{Feature}UpdateApiTest.java`~~ | ~~PUT/PATCH update~~ — **V1: SKIP (read-only restriction)** |
| ~~`{Feature}DeleteApiTest.java`~~ | ~~DELETE~~ — **V1: SKIP (read-only restriction)** |
| `{Feature}ValidationApiTest.java` | Cross-cutting validation — required fields, format, bounds (GET endpoints only) |
| `{Feature}EdgeCasesApiTest.java` | Edge cases — boundary, special characters (GET endpoints only) |

Not all categories may apply — only create groups that have test cases. If a category would have only 1-2 tests, merge it into the closest related class. If the endpoint only has one HTTP method (e.g., just GET), you can use a single `{Feature}ApiTest.java` class with `@Nested` inner classes.

> **V1 Note:** Do NOT generate Create, Update, or Delete test classes. Skip any test cases targeting POST, PUT, PATCH, or DELETE endpoints.

---

### Phase B: Parallel Subagent Generation (Task Tool Subagents)

Launch one **Task subagent** per test class group. Launch up to 4 subagents in parallel per wave.

**CRITICAL: Launch all independent subagents in a SINGLE message** (parallel execution):

```
# Wave 1 — launch up to 4 in parallel in ONE message:
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for ListApiTest>")
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for GetByIdApiTest>")
# Task(subagent_type="general-purpose", prompt="<populated subagent prompt for CreateApiTest>")   # V1: SKIP — read-only restriction
# Task(subagent_type="general-purpose", prompt="<populated subagent prompt for UpdateApiTest>")   # V1: SKIP — read-only restriction

# Wave 2 — after wave 1 completes:
# Task(subagent_type="general-purpose", prompt="<populated subagent prompt for DeleteApiTest>")   # V1: SKIP — read-only restriction
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for ValidationApiTest>")
Task(subagent_type="general-purpose", prompt="<populated subagent prompt for EdgeCasesApiTest>")
```

Each subagent writes ONE Java test class with its assigned tests. See the **Subagent Prompt Template** section below for the prompt format.

---

### Phase C: Coverage Validation + Gap Fill (Main Agent)

After ALL subagents complete:

1. **Get expected list**: Use the test case inventory from Phase A (all TC-IDs from `api-test-cases.md`)
2. **Get actual list**: Grep all generated `*.java` files for test case ID patterns:
   ```bash
   grep -roh "TC-[A-Z0-9_-]*-[0-9]\+" passage-api/src/test/apirequestcontext/java/com/williams/api/apitests/ | sort -u
   ```
3. **Compare**: Identify any test case IDs from the expected list that are missing from the actual list
4. **Fill gaps**: If any IDs are missing, launch ONE more Task subagent with just the missing test cases. Assign them to the most appropriate existing class or create a new `{Feature}RemainingApiTest.java`.
5. **Report coverage**: Output "X/Y test cases implemented across Z test classes"

**Self-verification** (language check):
```bash
# MUST find .java files
find passage-api/src/test/apirequestcontext -name "*.java" -newer /tmp/api-gen-marker | head -20
# MUST find NOTHING new
find passage-ui/e2e -name "*.ts" -newer /tmp/api-gen-marker 2>/dev/null | head -5
```

---

### Phase D: Run Tests (Main Agent)

After all test classes are generated and coverage is validated:

1. Run Gradle tests against the generated API test classes:
   ```bash
   cd passage-api && ./gradlew apiE2eTest --rerun --info > {RESULTS_FILE} 2>&1 || true
   ```
   - Replace `{RESULTS_FILE}` with the path provided in the `test_results_file` argument
   - **NOTE**: The workflow parses results from JUnit XML (`build/test-results/apiE2eTest/*.xml`) — raw output is for debugging only. The `--info` flag provides verbose output for human-readable diagnostics.

2. Report a brief summary: total tests found, passed, failed.

**IMPORTANT**: The `|| true` ensures the command exits successfully even if tests fail — the workflow parses the raw output. Do NOT parse or reformat the output yourself.

---

## Subagent Prompt Template

When launching each Task subagent, populate this template with the specific data for that group. **Copy-paste the full test case details** from api-test-cases.md — do NOT just list IDs.

```
You are a QE Automation Engineer. Generate a Java Playwright APIRequestContext E2E test class.

**CRITICAL: Language is JAVA. Generate .java files ONLY. Implement ALL test cases listed below. Every TC-ID must appear as a @Test method.**

**Target file**: passage-api/src/test/apirequestcontext/java/com/williams/api/apitests/{domain}/{Feature}{Category}ApiTest.java

**Test cases to implement** (implement ALL of these — do NOT skip any):
{paste the full TC-XXXX entries from api-test-cases.md for this group, including
 test name, priority, category, business context, preconditions, request details,
 expected response, test data, and validation points}

**Captured API traffic reference** (use for realistic assertions):
{If api_traffic_file was provided, paste the relevant captured API calls for this test group.
Include: endpoint, httpMethod, request.body.data structure, response.body structure.
If no api_traffic_file, omit this section entirely.}

**Base class**: com.williams.api.apifixtures.BaseApiTest (already created — extend it)
**Payloads**: com.williams.api.apifixtures.{domain}.{Feature}Payloads (already created — use its factory methods)
**Test data**: src/test/resources/testdata/api/{feature}.yml (already created)

**Available utilities** (use these, do NOT duplicate):
- RequestHelpers: get(api, endpoint), get(api, endpoint, params), post(api, endpoint, body), put(api, endpoint, body), patch(api, endpoint, body), delete(api, endpoint)
- ResponseHelpers: expectOk(response), expectCreated(response), expectNoContent(response), expectBadRequest(response), expectNotFound(response), expectConflict(response), parseJson(response, Class), parseJson(response), parseJsonAsMap(response), expectLocationHeader(response), expectValidationErrors(response, fields), expectPagedResponse(response)

**Standards**:
- Package: com.williams.api.apitests.{domain}
- Class name: {Feature}{Category}ApiTest
- Use @DisplayName with TC-ID: "TC-{ID}-NNN: {test name}"
- Use @Nested inner classes to group by HTTP method/operation
- Use @TestMethodOrder(MethodOrderer.OrderAnnotation.class)
- Include Javadoc for each test with TC-ID, Priority, Category, Business Context
- Follow Arrange-Act-Assert pattern
- Use static imports: import static com.williams.api.apiutils.RequestHelpers.*; import static com.williams.api.apiutils.ResponseHelpers.*;
- Use unique identifiers (timestamps) to prevent test conflicts
- Clean up test data in @AfterEach methods
- Track created resource IDs for cleanup
- Overwrite the file if it already exists

Write the complete Java test class. Map each test to its TC-ID in the @DisplayName and Javadoc.
```

---

## Reference Material

The sections below are reference for the orchestrator when creating scaffolding (Phase A) and for subagent prompts (Phase B).

### Output Structure

```
passage-api/src/test/apirequestcontext
├── java/com/williams/api/
│   ├── apitests/                           # API E2E test specifications
│   │   └── {domain}/
│   │       ├── {Feature}ListApiTest.java
│   │       ├── {Feature}GetByIdApiTest.java
│   │       ├── {Feature}CreateApiTest.java          # V1: SKIP — read-only restriction
│   │       ├── {Feature}UpdateApiTest.java          # V1: SKIP — read-only restriction
│   │       ├── {Feature}DeleteApiTest.java          # V1: SKIP — read-only restriction
│   │       ├── {Feature}ValidationApiTest.java
│   │       └── {Feature}EdgeCasesApiTest.java
│   │
│   ├── apifixtures/                        # API test fixtures
│   │   ├── BaseApiTest.java                # Base API test class (if not exists)
│   │   └── {domain}/
│   │       └── {Feature}Payloads.java      # Request/response builders
│   │
│   └── apiutils/                           # API utility functions
│       ├── RequestHelpers.java             # HTTP request utilities (if not exists)
│       ├── ResponseHelpers.java            # Response validation utilities (if not exists)
│       └── YamlLoader.java                 # YAML loader (if not exists)
│
└── resources/
    └── testdata/
        └── api/
            └── {feature}.yml               # YAML test data
```

### Base API Test Class

**BaseApiTest.java**

```java
package com.williams.api.apifixtures;

import com.microsoft.playwright.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.dataformat.yaml.YAMLFactory;
import org.junit.jupiter.api.*;

import java.util.Map;

/**
 * Base class for all Playwright API E2E tests.
 * Provides APIRequestContext setup and common utilities.
 */
public abstract class BaseApiTest {

    protected static Playwright playwright;
    protected static APIRequestContext apiContext;
    protected static ObjectMapper jsonMapper;
    protected static ObjectMapper yamlMapper;
    protected static String baseUrl;

    @BeforeAll
    static void setupPlaywright() {
        playwright = Playwright.create();
        baseUrl = System.getenv("API_BASE_URL") != null
            ? System.getenv("API_BASE_URL")
            : "http://localhost:8080";

        apiContext = playwright.request().newContext(
            new APIRequest.NewContextOptions()
                .setBaseURL(baseUrl)
                .setExtraHTTPHeaders(Map.of(
                    "Accept", "application/json",
                    "Content-Type", "application/json"
                ))
        );

        jsonMapper = new ObjectMapper();
        yamlMapper = new ObjectMapper(new YAMLFactory());
    }

    @AfterAll
    static void teardownPlaywright() {
        if (apiContext != null) {
            apiContext.dispose();
        }
        if (playwright != null) {
            playwright.close();
        }
    }

    /**
     * Get the API request context
     */
    protected APIRequestContext api() {
        return apiContext;
    }

    /**
     * Get the base URL
     */
    protected String baseUrl() {
        return baseUrl;
    }

    /**
     * Get JSON ObjectMapper
     */
    protected ObjectMapper json() {
        return jsonMapper;
    }
}
```

### Request Helpers

**RequestHelpers.java**

```java
package com.williams.api.apiutils;

import com.microsoft.playwright.*;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.Map;

/**
 * HTTP request helper utilities for Playwright API tests.
 */
public class RequestHelpers {

    private static final ObjectMapper mapper = new ObjectMapper();

    public static APIResponse get(APIRequestContext api, String endpoint) {
        return api.get(endpoint);
    }

    public static APIResponse get(APIRequestContext api, String endpoint, Map<String, Object> params) {
        return api.get(endpoint, RequestOptions.create().setQueryParam(params));
    }

    public static APIResponse post(APIRequestContext api, String endpoint, Object body) {
        try {
            String jsonBody = mapper.writeValueAsString(body);
            return api.post(endpoint, RequestOptions.create().setData(jsonBody));
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize request body", e);
        }
    }

    public static APIResponse put(APIRequestContext api, String endpoint, Object body) {
        try {
            String jsonBody = mapper.writeValueAsString(body);
            return api.put(endpoint, RequestOptions.create().setData(jsonBody));
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize request body", e);
        }
    }

    public static APIResponse patch(APIRequestContext api, String endpoint, Object body) {
        try {
            String jsonBody = mapper.writeValueAsString(body);
            return api.patch(endpoint, RequestOptions.create().setData(jsonBody));
        } catch (Exception e) {
            throw new RuntimeException("Failed to serialize request body", e);
        }
    }

    public static APIResponse delete(APIRequestContext api, String endpoint) {
        return api.delete(endpoint);
    }
}
```

### Response Helpers

**ResponseHelpers.java**

```java
package com.williams.api.apiutils;

import com.microsoft.playwright.APIResponse;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Response validation helper utilities for Playwright API tests.
 */
public class ResponseHelpers {

    private static final ObjectMapper mapper = new ObjectMapper();

    public static void expectOk(APIResponse response) {
        assertEquals(200, response.status(), "Expected 200 OK but got " + response.status());
    }

    public static void expectCreated(APIResponse response) {
        assertEquals(201, response.status(), "Expected 201 Created but got " + response.status());
    }

    public static void expectNoContent(APIResponse response) {
        assertEquals(204, response.status(), "Expected 204 No Content but got " + response.status());
    }

    public static void expectBadRequest(APIResponse response) {
        assertEquals(400, response.status(), "Expected 400 Bad Request but got " + response.status());
    }

    public static void expectNotFound(APIResponse response) {
        assertEquals(404, response.status(), "Expected 404 Not Found but got " + response.status());
    }

    public static void expectConflict(APIResponse response) {
        assertEquals(409, response.status(), "Expected 409 Conflict but got " + response.status());
    }

    public static <T> T parseJson(APIResponse response, Class<T> clazz) {
        try {
            return mapper.readValue(response.text(), clazz);
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse response as " + clazz.getSimpleName(), e);
        }
    }

    public static JsonNode parseJson(APIResponse response) {
        try {
            return mapper.readTree(response.text());
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse response as JSON", e);
        }
    }

    public static Map<String, Object> parseJsonAsMap(APIResponse response) {
        try {
            return mapper.readValue(response.text(), new TypeReference<Map<String, Object>>() {});
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse response as Map", e);
        }
    }

    public static String expectLocationHeader(APIResponse response) {
        String location = response.headers().get("location");
        assertNotNull(location, "Expected Location header to be present");
        assertFalse(location.isEmpty(), "Expected Location header to not be empty");
        return location;
    }

    public static void expectValidationErrors(APIResponse response, List<String> expectedFields) {
        expectBadRequest(response);
        JsonNode json = parseJson(response);
        JsonNode fieldErrors = json.get("fieldErrors");
        assertNotNull(fieldErrors, "Expected fieldErrors in response");

        for (String field : expectedFields) {
            boolean found = false;
            for (JsonNode error : fieldErrors) {
                if (error.get("field").asText().contains(field)) {
                    found = true;
                    break;
                }
            }
            assertTrue(found, "Expected validation error for field: " + field);
        }
    }

    public static JsonNode expectPagedResponse(APIResponse response) {
        expectOk(response);
        JsonNode json = parseJson(response);

        assertNotNull(json.get("content"), "Expected 'content' in paginated response");
        assertNotNull(json.get("totalElements"), "Expected 'totalElements' in paginated response");
        assertNotNull(json.get("totalPages"), "Expected 'totalPages' in paginated response");
        assertNotNull(json.get("size"), "Expected 'size' in paginated response");
        assertNotNull(json.get("number"), "Expected 'number' in paginated response");

        return json;
    }
}
```

### API Test Format Example

```java
package com.williams.api.apitests.{domain};

import com.microsoft.playwright.APIResponse;
import com.williams.api.apifixtures.BaseApiTest;
import com.williams.api.apifixtures.{domain}.{Feature}Payloads;
import com.fasterxml.jackson.databind.JsonNode;
import org.junit.jupiter.api.*;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import static com.williams.api.apiutils.RequestHelpers.*;
import static com.williams.api.apiutils.ResponseHelpers.*;
import static org.junit.jupiter.api.Assertions.*;

/**
 * {Feature} API E2E Tests — {Category}
 *
 * Test Cases Covered:
 * - TC-{ID}-001: {Test Name}
 * - TC-{ID}-002: {Test Name}
 *
 * Endpoints Covered:
 * - GET /api/v1/{endpoint}
 */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
class {Feature}{Category}ApiTest extends BaseApiTest {

    private static final List<Long> createdIds = new ArrayList<>();

    @AfterEach
    void cleanup() {
        for (Long id : createdIds) {
            try {
                delete(api(), "/api/v1/{endpoint}/" + id);
            } catch (Exception e) {
                // Ignore cleanup errors
            }
        }
        createdIds.clear();
    }

    /**
     * TC-{ID}-001: {Test Name}
     *
     * Priority: Critical
     * Category: Success Path
     */
    @Test
    @DisplayName("TC-{ID}-001: should return paginated list")
    void shouldReturnPaginatedList() {
        // Act
        APIResponse response = get(api(), "/api/v1/{endpoint}");

        // Assert
        JsonNode paged = expectPagedResponse(response);
        assertEquals(20, paged.get("size").asInt(), "Default page size should be 20");
    }
}
```

### Payload Builder Example

```java
package com.williams.api.apifixtures.{domain};

import java.util.HashMap;
import java.util.Map;

/**
 * Payload builders for {Feature} API tests.
 */
public class {Feature}Payloads {

    public static Map<String, Object> validCreateRequest() {
        Map<String, Object> payload = new HashMap<>();
        payload.put("field1", "value1");
        payload.put("field2", "value2");
        return payload;
    }

    public static Map<String, Object> invalidCreateRequest() {
        Map<String, Object> payload = new HashMap<>();
        payload.put("field", "");
        return payload;
    }

    public static Map<String, Object> validUpdateRequest() {
        Map<String, Object> payload = new HashMap<>();
        payload.put("field", "updatedValue");
        return payload;
    }
}
```

### Test Prioritization

1. **Success Path Tests** (Critical priority) - Core read-only functionality
2. **Validation Tests** (High priority) - Input validation verification (GET endpoints only)
3. **Error Handling Tests** (High priority) - 404, 500 scenarios (GET endpoints only)
4. ~~**Authorization Tests** (Critical priority) - Security verification~~ — **V1: SKIP — auth not implemented**
5. **Edge Case Tests** (Medium/Low priority) - Boundary conditions

### Quality Requirements

**DO**:
- Follow existing test patterns from `passage-api/src/test/`
- Use `@DisplayName` for readable test names with test case IDs
- Include detailed Javadoc comments explaining each test
- Map each generated test to its source test case ID
- Use proper assertions with meaningful error messages
- Clean up test data in `@AfterEach` methods
- Use unique identifiers (timestamps) to prevent test conflicts
- Follow Arrange-Act-Assert (AAA) pattern
- Use static imports for helper methods
- Use JAVA as the language to write the tests

**DO NOT**:
- Duplicate functionality that exists in existing utilities
- Hardcode values that should come from test data
- Skip any documented validation points
- Create tests without proper documentation
- Use flaky patterns (timing-dependent tests)
- Skip error handling scenarios
- Do not Use Typescript for the tests, any utilities or supporting test files

### HTTP Status Codes Reference

- `200 OK` - Successful GET, PUT
- `201 Created` - Successful POST (create)
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Validation errors
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource

### Test Naming Convention

- Test class names: `{Feature}{Category}ApiTest.java`
- Test method names: Descriptive camelCase (e.g., `shouldCreateResourceSuccessfully`)
- Display names: Include test case ID (e.g., `TC-API-SU-001: should return paginated list`)

### Gradle Dependencies

Ensure these dependencies are in `build.gradle.kts`:

```kotlin
dependencies {
    // Playwright for Java
    testImplementation("com.microsoft.playwright:playwright:1.40.0")

    // JUnit 5 (already included via spring-boot-starter-test)
    testImplementation("org.springframework.boot:spring-boot-starter-test")

    // Jackson for JSON/YAML (jackson-databind already included via Spring Boot)
    testImplementation("com.fasterxml.jackson.dataformat:jackson-dataformat-yaml")
}
```

---

## Concrete Output Example

A correctly generated test for endpoint 2984 would create:

```
passage-api/src/test/apirequestcontext/
├── java/com/williams/api/
│   ├── apitests/company/
│   │   ├── CompanyMaintenanceListApiTest.java      ← JAVA test file
│   │   └── CompanyMaintenanceGetByIdApiTest.java   ← JAVA test file
│   └── apifixtures/company/
│       └── CompanyMaintenancePayloads.java          ← JAVA fixture
└── resources/testdata/api/
    └── company-maintenance-get-company.yml           ← YAML test data
```

**WRONG** (do NOT do this):
```
passage-ui/e2e/tests/features/company/  ← WRONG REPO
    company-maintenance.spec.ts          ← WRONG LANGUAGE
```

---

## Begin

You will be provided with:
1. An **entry point folder path** (e.g., `docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany`)
2. A **test results file path** (e.g., `test_results_file: /path/to/results.txt`)
3. Optionally, an **api_traffic_file** path (e.g., `api_traffic_file: /path/to/api-traffic.json`) — captured legacy API traffic
4. Optionally, a **navigation_plan_file** path (e.g., `navigation_plan_file: /path/to/navigation-plan.md`) — navigation plan for this entry point, if available

**IMPORTANT**: Use the entry point folder path directly. Do NOT glob for other directories.

Execute Phases A → B → C → D:

1. **Phase A**: `touch /tmp/api-gen-marker`. Read `api-test-cases.md`, read `api_traffic_file` if provided, analyze existing test infrastructure, analyze related source code (cross-referencing with captured traffic when available), create payload builder + test data YAML + base classes if needed, group test cases by test class.
2. **Phase B**: Launch Task subagents (up to 4 parallel per wave) — each writes one Java test class using the Subagent Prompt Template above. **Copy-paste the full test case content** into each subagent prompt — do not just reference file paths.
3. **Phase C**: Validate coverage — grep generated Java files for TC-IDs, compare against full list, fill gaps with one more subagent if needed. Run self-verification (language/directory check). Report "X/Y test cases implemented across Z test classes".
4. **Phase D**: Run generated tests once — write raw output to the `test_results_file` path. Report summary.

$ARGUMENTS
