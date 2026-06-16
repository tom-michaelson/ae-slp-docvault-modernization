# Review Implementation

Review an implementation against the implementation plan and functional specification to verify functional completeness and correctness through **code analysis only**.

## Scope

This command performs a **static code review** - analyzing source code for functional correctness. It does NOT:
- Execute tests (that's a separate verification step)
- Measure code coverage (requires test execution)
- Run build/lint/quality tools (requires execution environment)
- Start the application (requires runtime)

**Focus**: Does the implementation code correctly implement what was specified?

## Usage

```
/review-implementation key: [key] type: [type]
```

**Examples:**
```
/review-implementation key: 1075-spring-filterservice-load type: api-endpoints
```

```
/review-implementation key: 2105-infrastructure-company-company-maintenance type: ui-features
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

Use `type` and `key` to locate the entry point directory:
```
./docs/entry-points/{type}/{key}/
```

## What This Command Reviews

This command performs **functional correctness review** by analyzing:

1. **Code Existence**: All files specified in the implementation plan exist
2. **Code Completeness**: All required methods, fields, and logic are implemented
3. **Code Correctness**: Implementation matches implementation plan specifications
4. **Business Logic**: Business rules from functional spec are correctly implemented
5. **API Contract**: Endpoints, DTOs, and responses match specifications
6. **Architecture Compliance**: Code follows required patterns and conventions

**Output**: `implementation-review-result.json` with validation status and functional issues.

## What This Command Does NOT Review

The following are **out of scope** for this review (handled by separate verification steps):

- ❌ Test execution results (tests passing/failing)
- ❌ Code coverage percentages
- ❌ Build success/failure
- ❌ Linting/formatting results
- ❌ Type checking results
- ❌ Security audit results
- ❌ Application startup verification
- ❌ Manual API testing via Swagger UI
- ❌ Regression testing execution

## Input Structure

The entry point directory at `./docs/entry-points/{type}/{key}/` contains:

```
{entry-point-directory}/
├── metadata.json                           # Entry point metadata
├── functional-spec.md                      # Functional specification (reference)
├── implementation-plan.md                       # Technical implementation plan (validation source)
├── task-list.md                            # Task list (progress tracking)
├── api.openapi.json                        # OpenAPI spec (if applicable)
└── implementation-review-result.json       # OUTPUT FILE
```

**Required files for review**:
- `implementation-plan.md` - What should have been implemented
- `functional-spec.md` - Functional requirements to validate against

## Output Structure

The command creates:

```
{entry-point-directory}/
├── ... (existing files)
└── implementation-review-result.json    # Review results
```

## Output JSON Schema

```typescript
interface ImplementationReview {
  /**
   * Whether the implementation passes functional review
   * true = Implementation code is complete and correct
   * false = Implementation has functional issues
   */
  validated: boolean;

  /**
   * Optional notes about the implementation review
   * Use for: positive observations, minor suggestions, context
   */
  notes?: string | null;

  /**
   * Description of functional issues found
   * REQUIRED if validated = false
   */
  remaining_issues?: string | null;
}
```

### Example Outputs

**Successful Review (validated: true)**:
```json
{
  "validated": true,
  "notes": "Implementation is functionally complete. All required files exist. Code matches implementation plan specifications. Business logic correctly implements functional requirements. Architecture patterns followed correctly.",
  "remaining_issues": null
}
```

**Failed Review (validated: false)**:
```json
{
  "validated": false,
  "notes": "Core implementation present but has functional gaps.",
  "remaining_issues": "FUNCTIONAL ISSUES:\n\n1. MISSING CODE (P0 - BLOCKING)\n   - CompanyRepositoryTest.java does not exist\n   - Technical plan tasks 8.3.1-8.3.7 specify this file\n\n2. INCOMPLETE IMPLEMENTATION (P0 - BLOCKING)\n   - AddressService.findByCompany() missing null validation\n   - Technical plan section 4.2 requires: \"Validate companyId is not null\"\n\n3. BUSINESS LOGIC ERROR (P1 - HIGH)\n   - CompanyMapper maps effectiveDate incorrectly\n   - Functional spec: date should be normalized to start of day\n   - Implementation: no date normalization present\n\n4. API CONTRACT MISMATCH (P1 - HIGH)\n   - Controller returns 500 for not-found case\n   - Technical plan specifies 404 with ResourceNotFoundException"
}
```

## Review Process

### Phase 0: Initial Setup

1. **Read all reference documents**:
   - [ ] Read `implementation-plan.md` - What should exist and how it should work
   - [ ] Read `functional-spec.md` - Functional requirements
   - [ ] Read `api.openapi.json` (if exists) - API contracts
   - [ ] Optionally scan `task-list.md` for context on what was planned

2. **Read target architecture documentation**:
   - [ ] Read `./docs/target-architecture/backend-architecture.md`
   - [ ] Read `./docs/target-architecture/api-design.md` (if API)
   - [ ] Read `./docs/target-architecture/frontend-architecture.md` (if UI)

3. **Create review checklist** using TodoWrite

### Phase 1: Code Existence Verification

**Objective**: Verify all code files specified in implementation-plan.md exist

#### 1.1. Identify Expected Files from Technical Plan

**Parse implementation-plan.md to extract**:
- DTOs (from "API Design" section)
- Entities (from "Domain Model" section)
- Repositories (from "Data Access Layer" section)
- Services (from "Service Layer Design" section)
- Controllers (from "API Design" section)
- Test files (from "Testing Strategy" section)
- Frontend components (if UI feature)

#### 1.2. Verify Each File Exists

```
For each file mentioned in implementation plan:
- Use Glob to check file exists
- Record if missing
```

#### 1.3. Record Findings

```
✅ PASS: All expected files exist

❌ FAIL: Missing files detected
  Backend:
  - Missing: ./passage-api/.../CompanyRepositoryTest.java
  - Missing: ./passage-api/.../CompanyGetIntegrationTest.java

  Frontend:
  - Missing: ./passage-ui/.../CompanyList.tsx
```

**Mark as FAIL if**: Any expected file is missing

### Phase 2: Code Completeness Verification

**Objective**: Verify implemented code has all required elements

#### 2.1. DTO/Model Completeness

**For each DTO in implementation-plan.md**:

1. **Read the DTO file**
2. **Compare against implementation plan**:
   - [ ] All fields defined in plan are present
   - [ ] Field types match plan specifications
   - [ ] Required vs. optional fields match plan
   - [ ] Annotations/decorators present as specified

#### 2.2. Entity Completeness

**For each entity in implementation-plan.md**:

1. **Read the entity file**
2. **Compare against implementation plan**:
   - [ ] All fields from plan are present
   - [ ] Database column mappings are correct
   - [ ] Primary key defined correctly
   - [ ] Foreign keys/relationships defined
   - [ ] Table name matches plan

#### 2.3. Repository Method Completeness

**For each repository in implementation-plan.md**:

1. **Read the repository file**
2. **Compare against implementation plan**:
   - [ ] All methods from plan are implemented
   - [ ] Method signatures match plan (parameters, return types)
   - [ ] Query patterns match plan specifications

#### 2.4. Service Method Completeness

**For each service in implementation-plan.md**:

1. **Read the service file**
2. **Compare against implementation plan**:
   - [ ] All methods from plan are implemented
   - [ ] Method signatures match plan
   - [ ] Dependencies properly injected
   - [ ] Business rules from plan are implemented
   - [ ] Error handling implemented

#### 2.5. Controller Endpoint Completeness

**For each API endpoint in implementation-plan.md**:

1. **Read the controller file**
2. **Compare against implementation plan**:
   - [ ] All endpoints implemented
   - [ ] HTTP methods match (GET, POST, PUT, DELETE)
   - [ ] Route paths match
   - [ ] Request/response DTOs used correctly
   - [ ] Annotations/decorators present

#### 2.6. Record Findings

```
✅ PASS: All code elements present and complete

❌ FAIL: Missing or incomplete code elements
  DTOs:
  - CompanyRequest.dto: Missing 'effectiveDate' field (plan section 3.2)

  Services:
  - CompanyService.findById(): Missing implementation (plan section 4.1)
  - CompanyService.validate(): Missing null check per plan section 4.2
```

**Mark as FAIL if**: Any required code element missing or incomplete

### Phase 3: Business Logic Verification

**Objective**: Verify business rules from functional spec are correctly implemented

#### 3.1. Map Business Rules to Code

**For each business rule in functional-spec.md**:

```
Rule: [Description from functional spec]
Expected Location: [Where it should be implemented per implementation plan]
Actual Implementation: [What code exists]
Status: ✅ Correct / ❌ Missing / ⚠️ Incorrect

Example:
Rule: "Effective date defaults to current date if not provided"
Expected Location: CompanyQueryService.findById() per plan section 4.3
Actual Implementation: Line 45-47 checks for null and uses Clock.instant()
Status: ✅ Correct - matches specification exactly

Rule: "Return 404 if no company record exists for the effective date"
Expected Location: CompanyQueryService.findById() per plan section 4.4
Actual Implementation: Not found - returns Optional.empty() but no exception thrown
Status: ❌ Missing - should throw ResourceNotFoundException
```

#### 3.2. Verify Edge Cases

**Check handling of**:
- Null/empty inputs
- Invalid data formats
- Boundary conditions
- Error cases

#### 3.3. Record Findings

```
✅ PASS: All business rules correctly implemented

❌ FAIL: Business logic issues found
  1. Missing rule implementation:
     - "Effective date defaults to current date" not implemented
     - Location: CompanyQueryService.java
     - Expected: null check with Clock fallback

  2. Incorrect rule implementation:
     - "Company ID validation" incorrect
     - Location: CompanyController.java:52
     - Expected: Validate format before service call
     - Actual: Validation happens after service call
```

**Mark as FAIL if**: Any business rule missing or incorrectly implemented

### Phase 4: API Contract Verification

**Objective**: Verify API implementation matches contract specification

#### 4.1. Endpoint Verification

**For each endpoint**:
- [ ] Path matches specification
- [ ] HTTP method matches
- [ ] Query/path parameters match
- [ ] Request body structure matches
- [ ] Response body structure matches
- [ ] Status codes match specification

#### 4.2. Error Response Verification

**Verify error handling**:
- [ ] 404 returned for not-found cases
- [ ] 400 returned for bad request cases
- [ ] Error response format matches specification
- [ ] Exception handlers properly configured

#### 4.3. Record Findings

```
✅ PASS: API contract correctly implemented

❌ FAIL: API contract mismatches
  1. Endpoint path mismatch:
     - Spec: GET /api/v1/companies/{id}
     - Actual: GET /api/v1/company/companies/{id}
     - Note: May be intentional for consistency with existing endpoints

  2. Missing status code handling:
     - Spec: Return 404 when company not found
     - Actual: Returns 500 (no exception handler)
```

**Mark as FAIL if**: Critical API contract violations (path ok if consistent with existing patterns)

### Phase 5: Test Code Review

**Objective**: Verify test files exist and cover required scenarios (code review only, NOT execution)

#### 5.1. Test File Existence

**For each test file specified in implementation plan**:
- [ ] File exists
- [ ] Has test methods/cases for required scenarios

#### 5.2. Test Coverage Analysis (by code inspection)

**For each service/repository/controller**:
- [ ] Unit test file exists
- [ ] Test methods cover happy path
- [ ] Test methods cover error cases
- [ ] Test methods cover edge cases as specified

**Note**: This is code inspection to verify test FILES exist and appear comprehensive. Actual test execution is a separate verification step.

#### 5.3. Record Findings

```
✅ PASS: All required test files exist with appropriate coverage

❌ FAIL: Missing or incomplete test files
  Missing test files:
  - CompanyRepositoryTest.java - NOT FOUND
    Required tests per plan 8.3.1-8.3.7:
    * findByIdAndEffectiveDate happy path
    * findByIdAndEffectiveDate date boundary cases
    * findByIdAndEffectiveDate not found cases

  - CompanyControllerTest.java - EXISTS but incomplete
    Missing test methods:
    * GET /companies/{id} 404 case
    * GET /companies/{id} with effectiveDate parameter
```

**Mark as FAIL if**: Required test files missing or clearly incomplete

### Phase 6: Architecture Compliance

**Objective**: Verify code follows required patterns

#### 6.1. Layer Separation

- [ ] Controllers only handle HTTP concerns (no business logic)
- [ ] Services contain business logic
- [ ] Repositories handle data access only
- [ ] Entities are clean domain objects

#### 6.2. Pattern Compliance

- [ ] Dependency injection used correctly
- [ ] Error handling follows standard pattern
- [ ] Naming conventions followed
- [ ] Package/module structure correct

#### 6.3. Domain Placement Validation

Read `docs/target-architecture/domain-registry.json` and verify:

- [ ] All new Java classes in `passage-api` are placed under a registered domain package in `com.williams.api.{domain}/`
- [ ] No new top-level packages were created under `com.williams.api/` that are not in the registry's `domains` array or `allowedNonDomainPackages` array
- [ ] Sub-packages used (if any) are listed in the `subDomains` array of the relevant domain entry
- [ ] Cross-cutting utilities (logging, auth, caching) are placed in `common`, not in a domain package

```
✅ PASS: All classes placed in registered domain packages

❌ FAIL: Domain placement violations
  1. Unregistered package created:
     - com.williams.api.newpackage.SomeClass
     - This package is not in domain-registry.json
     - Should be placed in: com.williams.api.[correct-domain]/
```

**Mark as FAIL if**: Any class is placed in an unregistered top-level package under `com.williams.api/`

#### 6.4. Record Findings

```
✅ PASS: Architecture patterns followed correctly

❌ FAIL: Architecture violations
  1. Business logic in controller:
     - CompanyController.java:45-67
     - Date validation logic should be in service

  2. Direct repository usage in controller:
     - CompanyController.java:23
     - Should go through service layer
```

**Mark as FAIL if**: Significant architecture violations

### Security Anti-Pattern Check

- [ ] Service classes do NOT contain `UserContext.hasPermission()` calls for authorization
- [ ] Service classes do NOT contain hardcoded func_id constants (e.g., `"ALLWIN"`, `"IT INQ"`, `"SEC FUN"`)
- [ ] If API-level security is needed, it uses `@SecuredByMenuItem` on the controller
- [ ] No invented permission checks — verify against legacy behavior
- [ ] If `@SecuredByMenuItem` is present, item_id is correct (verified against `menu_func` table)
- Reference: `docs/target-architecture/security-architecture.md`

### Phase 7: Generate Review Report

#### 7.1. Determine Validation Status

```
validated = true IF AND ONLY IF ALL of the following are true:
✅ All expected code files exist
✅ All code elements are complete (fields, methods, etc.)
✅ All business rules correctly implemented
✅ API contract correctly implemented (or minor deviations documented)
✅ All required test files exist
✅ No significant architecture violations

validated = false IF ANY of the following are true:
❌ Expected files missing
❌ Code elements incomplete
❌ Business logic errors
❌ Critical API contract violations
❌ Required test files missing
❌ Significant architecture violations
```

#### 7.2. Compile Remaining Issues

**Format for `remaining_issues`** (if validated = false):

```
FUNCTIONAL ISSUES:

1. MISSING FILES (P0 - BLOCKING)
   [List each missing file and what it should contain]

2. INCOMPLETE IMPLEMENTATION (P0 - BLOCKING)
   [List each incomplete element with specific location and what's missing]

3. BUSINESS LOGIC ERRORS (P1 - HIGH)
   [List each error with location, expected behavior, actual behavior]

4. API CONTRACT ISSUES (P1 - HIGH)
   [List each mismatch with specification reference]

5. MISSING TEST FILES (P1 - HIGH)
   [List each missing test file and required test scenarios]

6. ARCHITECTURE VIOLATIONS (P2 - MEDIUM)
   [List each violation with location and correct pattern]

REQUIRED ACTIONS:
[Concrete steps to fix each issue]
```

#### 7.3. Write JSON Output

Create `implementation-review-result.json` with:
- `validated`: boolean based on criteria above
- `notes`: summary of review findings
- `remaining_issues`: structured list of functional issues (if any)

### Phase 8: Report to User

**If validated = true**:
```
✅ Implementation Functionally Complete

Review file created: ./docs/entry-points/{type}/{key}/implementation-review-result.json

The implementation code correctly implements the implementation plan and functional specification.

Next Steps:
- Run tests to verify behavior: mvn test
- Run build to verify compilation: mvn verify
- Manual verification via Swagger UI (optional)
```

**If validated = false**:
```
❌ Functional Issues Found

Review file created: ./docs/entry-points/{type}/{key}/implementation-review-result.json

[Summary of issues]

Next Steps:
1. Address the functional issues listed in remaining_issues
2. Re-run /review-implementation to verify fixes
```

## Critical Guidelines

### Focus on Functional Correctness

**This review answers**: "Does the code correctly implement what was specified?"

**DO NOT flag as issues**:
- "Tests not executed" - out of scope
- "Coverage not measured" - out of scope
- "Build not verified" - out of scope
- "Code quality checks not run" - out of scope
- "Application startup not tested" - out of scope

**DO flag as issues**:
- Missing files that should exist
- Missing methods/fields that should be implemented
- Business logic that doesn't match specification
- API contracts that don't match specification
- Test files that don't exist when they should
- Architecture violations in the code

### Be Specific

When flagging issues:
- Cite the specific file and line number
- Reference the implementation plan section that specifies the requirement
- Describe exactly what's wrong
- Describe exactly what should be there instead

### Review Test Code, Don't Execute

For test verification:
- ✅ Check test files exist
- ✅ Check test methods cover required scenarios (by reading code)
- ❌ Don't try to run tests
- ❌ Don't flag "tests not executed" as an issue

## Success Criteria

**Review is Complete When**:
- [ ] All specified files checked for existence
- [ ] All code elements verified against implementation plan
- [ ] Business logic verified against functional spec
- [ ] API contract verified against specification
- [ ] Test files verified (existence and coverage by inspection)
- [ ] Architecture compliance verified
- [ ] JSON output file created with correct schema
- [ ] User notified of results

**Review is Focused When**:
- [ ] Only functional issues flagged
- [ ] No execution-dependent issues flagged
- [ ] Each issue has specific location and reference
- [ ] Each issue has clear remediation action

---

## Related Resources

- **Architecture Standards:** `passage-api-architect` agent defines API layer patterns and quality standards
- **Review Mode:** When used in remediation validation, `passage-api-architect` can be launched in review mode with `Mode: REVIEW` to validate implementations against its domain-specific criteria

---

**End of Command Specification**
