# Review Technical Plan - API

Review a technical implementation plan for API endpoints, validating quality, accuracy, completeness, and adherence to target architecture standards.

## Common Foundation

@review-technical-plan-common.md

## API-Specific Context

This review type is for **API Endpoints** (REST services, backend operations, data retrieval/modification endpoints). Focus on RESTful API design, request/response contracts, data access patterns, and OpenAPI specifications.

## Usage

```
/review-technical-plan-api key: [key]
```

**Examples:**
```
/review-technical-plan-api key: 1075-spring-filterservice-load
```

```
/review-technical-plan-api key: 3003-spring-companycontactservice-getcompanycontactlist
```

## Input

The command receives an inventory item JSON payload:

```json
{
  "key": "1075-spring-filterservice-load",
  "name": null,
  "location": "./legacy/northwest-passage/passage-java/src-common/com/williams/gridServices/services/FilterService.java, FilterService.load() method (line 93)",
  "type": "api-endpoints",
  "notes": [
    "Spring REST reflection endpoint: POST /service/gridServices",
    "Bean ID: filterService",
    "Client specifies methodName in POST body (JSON-RPC style)"
  ]
}
```

Use `key` to locate the entry point directory:
```
./docs/entry-points/api-endpoints/{key}/
```

## API-Specific Review Checklist

In addition to the common review checklist, verify the following API-specific items.

**CRITICAL - Target Architecture Documents**: Before reviewing, YOU MUST READ these target architecture documents:
- `./docs/target-architecture/api-design.md` - REST conventions, controller patterns, DTO patterns, error handling
- `./docs/target-architecture/backend-architecture.md` - Service layer patterns, Spring Boot patterns
- `./docs/target-architecture/data-access-migration.md` - Repository patterns, JPA patterns
- `./docs/target-architecture/tech-stack.md` - Approved frameworks and versions

Verify the technical plan aligns with patterns documented in these files.

---

### API-1. RESTful API Design Compliance (CRITICAL)

**Goal**: Ensure the API design follows modern RESTful conventions, NOT legacy patterns.

**CRITICAL - Reject Legacy Patterns**:

The technical plan must design MODERN RESTful APIs. Flag and correct any of these legacy patterns:

| Legacy Pattern (REJECT) | Modern Pattern (REQUIRE) |
|------------------------|--------------------------|
| Single endpoint with `methodName` in body | Multiple endpoints with HTTP verbs |
| `POST /service/gridServices` | `GET/POST/PUT/DELETE /api/v1/{resource}` |
| JSON-RPC style routing | Resource-based URLs |
| All operations via POST | Proper HTTP verb semantics |
| Front-controller patterns | Direct resource routing |

**Verify RESTful Design** (per `api-design.md`):

- [ ] Resource-based URL paths (`/api/v1/{domain}/{resource}`)
- [ ] Proper HTTP verbs (GET for reads, POST for creates, PUT for updates, DELETE for deletes)
- [ ] Path parameters for resource identifiers (`/api/v1/companies/{companyId}`)
- [ ] Query parameters for filtering (`?status=active&state=TX`)
- [ ] Proper HTTP status codes documented
- [ ] No `methodName` parameter in request bodies
- [ ] No single-endpoint-for-all-operations pattern

**Verify API Design Patterns** (per `api-design.md`):

- [ ] Controller layer follows documented patterns
- [ ] Controller layer contains ONLY HTTP concerns (no business logic, no data transformation, no date parsing, no conditional routing) — Spring Security annotations (`@PreAuthorize`, `@Secured`) are valid controller concerns
- [ ] All business logic, orchestration, and data transformation is in the service layer
- [ ] Request/response DTO patterns align with standards
- [ ] Mapper implementation patterns followed
- [ ] Error response format matches standard structure
- [ ] Caching strategy follows documented approach (if applicable)

**ACTION**: If legacy patterns are found, redesign the API following RESTful conventions. This is a CRITICAL issue that must be corrected.

---

### API-2. OpenAPI Specification Validation (CRITICAL)

**Goal**: Ensure OpenAPI spec is valid, complete, and consistent with plan.

**Verify OpenAPI file exists**:
- [ ] `api.openapi.json` file exists in the directory
- [ ] File contains valid OpenAPI 3.0+ JSON syntax

**Verify OpenAPI completeness**:

#### Structure:
- Info section complete (title, description, version)
- Servers defined
- Security schemes declared

#### Paths:
- All endpoints from plan documented
- Correct HTTP methods
- Operation IDs present and unique
- Tags for logical grouping
- Descriptions for all operations

#### Request/Response:
- Request bodies with complete schemas
- All responses defined (success and errors)
- Schema references ($ref) resolve correctly
- Required fields marked
- Examples present

#### Consistency:
- Models in OpenAPI match models in technical-plan.md
- Field names consistent between documents
- Types consistent between documents
- No orphaned schema definitions

**ACTION**: Correct OpenAPI errors, add missing definitions, ensure consistency with plan.

---

### API-3. API Contract Completeness

**Goal**: Ensure all API contracts are fully specified.

**Verify for each endpoint**:

#### Endpoint Definition:
- [ ] HTTP method specified
- [ ] URL path with any path parameters
- [ ] Query parameters documented with types and defaults
- [ ] Request body schema (if applicable)
- [ ] Response schema for all status codes

#### Request Models:
- [ ] All fields have types
- [ ] All fields have descriptions
- [ ] Required fields marked
- [ ] Validation constraints documented (min/max, patterns, enums)
- [ ] Examples provided

#### Response Models:
- [ ] All fields have types
- [ ] All fields have descriptions
- [ ] Nested objects fully defined
- [ ] Null handling documented

#### Pagination (if list endpoint):
- [ ] Pagination approach documented (page/size or cursor)
- [ ] Pagination response wrapper defined
- [ ] Default page size specified
- [ ] Maximum page size specified

**ACTION**: Add missing contract details, ensure all fields documented.

---

### API-4. Error Response Design

**Goal**: Ensure comprehensive error response design.

**Verify error responses**:

#### Standard Error Format:
- [ ] Consistent error response structure defined
- [ ] Error code field present
- [ ] Error message field present
- [ ] Details/validation errors array (for 400 errors)

#### HTTP Status Mapping:
| Status | When Used | Verified |
|--------|-----------|----------|
| 200 OK | Successful GET/PUT | [ ] |
| 201 Created | Successful POST | [ ] |
| 204 No Content | Successful DELETE | [ ] |
| 400 Bad Request | Validation errors | [ ] |
| 401 Unauthorized | Authentication required | [ ] |
| 403 Forbidden | Insufficient permissions | [ ] |
| 404 Not Found | Resource not found | [ ] |
| 409 Conflict | Business rule conflict | [ ] |
| 500 Internal Server Error | Unexpected errors | [ ] |

#### Error Codes:
- [ ] Unique error codes for each error type
- [ ] Error codes documented with descriptions
- [ ] Error codes follow naming convention

**ACTION**: Add missing error responses, ensure consistent format.

---

### API-5. API Security Design

**Goal**: Ensure API security is thoroughly designed.

**Verify security coverage**:

#### Authentication:
- [ ] Authentication mechanism specified (JWT, session, etc.)
- [ ] Token handling documented
- [ ] Unauthenticated endpoint behavior defined

#### Authorization:
- [ ] Each endpoint has permission requirements
- [ ] Permission check implementation approach
- [ ] Role-based or permission-based access documented
- [ ] Resource-level authorization if needed

#### Input Security:
- [ ] Input validation for all parameters
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention for any HTML content
- [ ] Size limits for request bodies
- [ ] Rate limiting considerations

**ACTION**: Add missing security specifications.

---

### API-6. API Versioning

**Goal**: Ensure API versioning strategy is documented.

**Verify versioning**:

- [ ] API version in URL path (`/api/v1/...`)
- [ ] Version strategy documented (URL path vs header)
- [ ] Breaking change handling approach
- [ ] Deprecation strategy if applicable

**ACTION**: Add versioning details if missing.

---

## API-Specific Report Sections

Add these sections to the review report for API plans:

```markdown
## API Design Compliance

| Aspect | Status | Notes |
|--------|--------|-------|
| RESTful Design | ✓/Corrected | [Details] |
| No Legacy Patterns | ✓/Corrected | [Details] |
| HTTP Verbs | ✓/Corrected | [Details] |
| URL Structure | ✓/Corrected | [Details] |

## OpenAPI Validation

| Aspect | Status | Notes |
|--------|--------|-------|
| File Exists | ✓/Missing | [Details] |
| Valid Syntax | ✓/Corrected | [Details] |
| All Endpoints | ✓/Corrected | [Details] |
| Complete Schemas | ✓/Corrected | [Details] |
| Consistency with Plan | ✓/Corrected | [Details] |

## API Contract Completeness

| Contract Area | Status | Issues | Corrections |
|---------------|--------|--------|-------------|
| Endpoints | ✓/Corrected | [N] | [Summary] |
| Request Models | ✓/Corrected | [N] | [Summary] |
| Response Models | ✓/Corrected | [N] | [Summary] |
| Error Responses | ✓/Corrected | [N] | [Summary] |
| Pagination | ✓/Corrected/N/A | [N] | [Summary] |
```

---

## API-Specific Success Criteria

In addition to common success criteria:

**API Design**:
- [ ] RESTful design followed (no legacy patterns)
- [ ] All endpoints use appropriate HTTP verbs
- [ ] URL structure follows `/api/v1/{domain}/{resource}` pattern
- [ ] No JSON-RPC or front-controller patterns

**OpenAPI Specification**:
- [ ] `api.openapi.json` exists and is valid
- [ ] All endpoints documented
- [ ] All schemas complete
- [ ] Consistent with technical-plan.md

**API Contracts**:
- [ ] All request models complete
- [ ] All response models complete
- [ ] Error responses documented
- [ ] Pagination design documented (if applicable)

**API Security**:
- [ ] Authentication mechanism specified
- [ ] Authorization requirements per endpoint
- [ ] Input validation documented

---

## API-Specific Execution Instructions

1. **Parse the key parameter** from the command invocation

2. **Construct the directory path**: `./docs/entry-points/api-endpoints/{key}/`

3. **Read all relevant files from the directory**:
   - `technical-plan.md` (required)
   - `functional-spec.md` (required for traceability)
   - `api.openapi.json` (required for API plans)
   - `metadata.json` (for context)
   - Target architecture documents (tech-stack, backend-architecture, api-design, data-access)

4. **Systematically work through each review check** (common + API-specific)

5. **Make corrections directly** to technical-plan.md and api.openapi.json as you find issues

6. **Track all findings** for the report

7. **Generate the review report** as `technical-plan-review.md` in the same directory

8. **Provide brief summary** to user of review outcome

---

## API-Specific Troubleshooting

### Legacy Pattern Conversion

**Problem**: Plan preserves legacy JSON-RPC or front-controller patterns

**Solutions**:
1. Identify the resource being operated on
2. Identify the operation type (CRUD)
3. Map to appropriate HTTP verb and URL pattern
4. Redesign API following RESTful conventions
5. Update both technical-plan.md and api.openapi.json
6. Document the transformation in review report

### OpenAPI Inconsistencies

**Problem**: OpenAPI spec doesn't match technical plan

**Solutions**:
1. Use technical-plan.md as source of truth for design
2. Update api.openapi.json to match
3. Ensure field names, types, and structures align
4. Validate JSON syntax after changes

### Complex Query Requirements

**Problem**: Endpoint requires complex filtering that's hard to express in query params

**Solutions**:
1. For simple filters: Use query parameters
2. For complex filters: Consider POST with filter body to a `/search` endpoint
3. Document the approach in architectural decisions
4. Ensure OpenAPI reflects the chosen approach

---

**End of Command Specification**
