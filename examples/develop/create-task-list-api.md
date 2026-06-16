---
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --from-stdin
            --log
            --file-pattern "*task-list*"
            --contains '# Task List'
            --contains '## Overview'
            --contains '## Task Hierarchy'
            --contains '## Dependency Matrix'
            --contains '## Parallelization Opportunities'
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*task-list*"
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*task-list*"
            --contains '# Task List'
            --contains '## Overview'
            --contains '## Task Hierarchy'
            --contains '## Dependency Matrix'
            --contains '## Parallelization Opportunities'
---

# Create Task List - API

Create a comprehensive, actionable task list from an implementation plan for API endpoints that can be used to track development progress.

## Usage

```
/create-task-list-api key: [key]
```

**Examples:**
```
/create-task-list-api key: 1075-spring-filterservice-load
```

```
/create-task-list-api key: 2976-spring-companymaintenanceservice-getcompanylist
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

## What This Command Does

This command analyzes a technical implementation plan for an API endpoint and generates a comprehensive, hierarchical task list that covers every aspect of backend implementation. The task list:

- **Breaks down** the implementation plan into concrete, actionable tasks
- **Organizes** tasks hierarchically with clear parent-child relationships
- **Tracks** all work items including code, tests, and documentation
- **Provides** checkboxes for leaf-level tasks to enable progress tracking
- **Ensures** nothing is overlooked by systematically covering all plan sections

## Input Structure

The entry point directory at `./docs/entry-points/api-endpoints/{key}/` contains:

```
{entry-point-directory}/
├── metadata.json                    # Entry point metadata
├── functional-spec.md               # Functional specification
├── implementation-plan.md                # Technical implementation plan (INPUT)
└── api.openapi.json                 # OpenAPI spec (if applicable)
```

**Required files**:
- `implementation-plan.md` - Created by `/plan-api-feature` command

## Output Structure

The command creates the following file in the **same directory**:

```
{entry-point-directory}/
├── ... (existing files)
└── task-list.md                # Hierarchical task list with checkboxes
```

## Task List Format

The `task-list.md` file uses a hierarchical outline format:

```markdown
# Task List: [Feature Name]

> **Source**: [path to implementation-plan.md]
> **Generated**: [date]
> **Total Tasks**: [count of leaf-level checkboxed items]

## Task Hierarchy

1. Top-Level Phase or Component
1.1. Mid-Level Component or Area
[ ] 1.1.1. Specific actionable task
[ ] 1.1.2. Another specific actionable task
1.2. Another Mid-Level Component
[ ] 1.2.1. Specific task
2. Another Top-Level Phase
2.1. Mid-Level Component
[ ] 2.1.1. Task
[ ] 2.1.2. Task
```

### Formatting Rules

1. **Top-level items** (1., 2., 3.): Major phases or components (NO checkboxes)
2. **Mid-level items** (1.1., 1.2., 2.1.): Sub-components or areas (NO checkboxes)
3. **Leaf-level items** (1.1.1., 1.1.2.): Actual tasks with `[ ]` checkboxes
4. **Indentation**: Use standard indentation (not spaces for alignment)
5. **Granularity**: Leaf tasks should be completable in a few hours to 1 day

### Task Granularity Guidelines

**GOOD leaf-level tasks** (appropriate size):
```
[ ] 1.1.1. Create CompanyAddressRequest DTO with all fields and validation annotations
[ ] 1.1.2. Create CompanyAddressResponse DTO with nested address structure
[ ] 1.1.3. Implement AddressService.findByCompany() method
[ ] 1.1.4. Write unit tests for AddressService.findByCompany()
```

**BAD leaf-level tasks** (too large or vague):
```
[ ] 1.1.1. Implement all DTOs
[ ] 1.1.2. Build the service layer
[ ] 1.1.3. Add tests
```

## Task List Template

The `task-list.md` file follows this comprehensive structure for API endpoints:

```markdown
# Task List: [Feature Name]

> **Source**: [path to implementation-plan.md]
> **Generated**: [date]
> **Total Tasks**: [count]

## Overview

This task list breaks down the technical implementation plan into actionable work items. Each checkboxed item represents a specific deliverable.

**Progress Tracking**:
- Total tasks: [count]
- Completed: 0
- Remaining: [count]

---

## Task Hierarchy

1. Setup and Prerequisites
1.1. Project Structure
[ ] 1.1.1. Create package structure for new components
[ ] 1.1.2. Set up configuration files for new feature
1.2. Dependencies
[ ] 1.2.1. Add required dependencies to build.gradle
[ ] 1.2.2. Update dependency documentation

2. API Contracts and Models
2.1. Request Models
[ ] 2.1.1. Create [RequestModel1] DTO with fields and validation annotations
[ ] 2.1.2. Create [RequestModel2] DTO with fields and validation annotations
2.2. Response Models
[ ] 2.2.1. Create [ResponseModel1] DTO with complete structure
[ ] 2.2.2. Create [ResponseModel2] DTO with complete structure
2.3. OpenAPI Specification
[ ] 2.3.1. Define OpenAPI paths and operations
[ ] 2.3.2. Define OpenAPI request/response schemas
[ ] 2.3.3. Define OpenAPI error responses
[ ] 2.3.4. Validate OpenAPI spec against standards

3. Domain Layer
3.1. Entity Definitions
[ ] 3.1.1. Create [Entity1] class with JPA annotations
[ ] 3.1.2. Create [Entity2] class with JPA annotations
[ ] 3.1.3. Define entity relationships and mappings
3.2. Value Objects
[ ] 3.2.1. Create [ValueObject1] immutable class
[ ] 3.2.2. Create [ValueObject2] immutable class

4. Data Access Layer
4.1. Repository Interfaces
[ ] 4.1.1. Create [Repository1] interface extending JpaRepository
[ ] 4.1.2. Create [Repository2] interface with query methods
4.2. Custom Queries
[ ] 4.2.1. Implement custom query for [operation1] using @Query annotation
[ ] 4.2.2. Implement custom query for [operation2] using Criteria API
4.3. Repository Tests
[ ] 4.3.1. Write integration tests for [Repository1] using @DataJpaTest
[ ] 4.3.2. Write integration tests for [Repository2] using @DataJpaTest

5. Service Layer
5.1. Service Implementation
[ ] 5.1.1. Create [Service1] class with @Service annotation
[ ] 5.1.2. Implement [Service1.method1()] with business logic
[ ] 5.1.3. Implement [Service1.method2()] with business logic
[ ] 5.1.4. Create [Service2] class with @Service annotation
[ ] 5.1.5. Implement [Service2.method1()] with business logic
5.2. Validation Logic
[ ] 5.2.1. Implement input validation for [operation1] using Bean Validation
[ ] 5.2.2. Implement business rule validation for [rule1]
[ ] 5.2.3. Implement business rule validation for [rule2]
5.3. Service Tests
[ ] 5.3.1. Write unit tests for [Service1.method1()] using Mockito
[ ] 5.3.2. Write unit tests for [Service1.method2()] using Mockito
[ ] 5.3.3. Write unit tests for [Service2.method1()] using Mockito
[ ] 5.3.4. Write tests for validation logic

6. API Layer
6.1. Controller Implementation
[ ] 6.1.1. Create [Controller1] with @RestController and @RequestMapping
[ ] 6.1.2. Implement [endpoint1] handler method with proper HTTP method annotation
[ ] 6.1.3. Implement [endpoint2] handler method with proper HTTP method annotation
[ ] 6.1.4. Add @Valid annotation for request/response validation
6.2. Controller Tests
[ ] 6.2.1. Write integration tests for [endpoint1] using @WebMvcTest
[ ] 6.2.2. Write integration tests for [endpoint2] using @WebMvcTest
[ ] 6.2.3. Test error responses and HTTP status codes

7. Database Changes
7.1. Schema Modifications
[ ] 7.1.1. Create Flyway/Liquibase migration script for new tables
[ ] 7.1.2. Create migration script for table modifications
[ ] 7.1.3. Create indexes for query optimization
[ ] 7.1.4. Test migration scripts on local database
7.2. Data Migration
[ ] 7.2.1. Create data migration script (if needed)
[ ] 7.2.2. Test data migration on sample dataset
7.3. Rollback Plans
[ ] 7.3.1. Document rollback procedures for schema changes
[ ] 7.3.2. Create rollback migration scripts

8. Security Implementation
8.1. Authentication
[ ] 8.1.1. Add @PreAuthorize or @Secured annotations to endpoints
[ ] 8.1.2. Test authentication enforcement
8.2. Authorization
[ ] 8.2.1. Implement permission checks for [operation1] using Spring Security
[ ] 8.2.2. Implement permission checks for [operation2] using Spring Security
[ ] 8.2.3. Test authorization for different user roles
8.3. Data Protection
[ ] 8.3.1. Implement data masking for sensitive fields
[ ] 8.3.2. Add encryption for [sensitive data]
[ ] 8.3.3. Test data protection measures

9. Error Handling
9.1. Exception Classes
[ ] 9.1.1. Create custom exception hierarchy extending RuntimeException
[ ] 9.1.2. Implement specific exception classes (EntityNotFoundException, ValidationException, etc.)
9.2. Error Responses
[ ] 9.2.1. Configure @ControllerAdvice for error response mapping
[ ] 9.2.2. Add user-friendly error messages with proper HTTP status codes
[ ] 9.2.3. Test error scenarios and responses

10. Integration Testing
10.1. End-to-End Scenarios
[ ] 10.1.1. Test complete flow for [scenario1] using @SpringBootTest
[ ] 10.1.2. Test complete flow for [scenario2] using @SpringBootTest
[ ] 10.1.3. Test error handling flows
10.2. Integration Points
[ ] 10.2.1. Test integration with [system1]
[ ] 10.2.2. Test integration with [system2]
[ ] 10.2.3. Test failure scenarios

11. Performance Testing
11.1. Load Testing
[ ] 11.1.1. Create load test scenarios using JMeter or Gatling
[ ] 11.1.2. Run load tests and measure performance
[ ] 11.1.3. Optimize based on results
11.2. Database Performance
[ ] 11.2.1. Analyze query performance using database profiler
[ ] 11.2.2. Add or optimize indexes based on query plans
[ ] 11.2.3. Verify query execution plans

12. Configuration and Deployment
12.1. Configuration
[ ] 12.1.1. Add configuration properties to application.yml
[ ] 12.1.2. Document configuration options
[ ] 12.1.3. Set up environment-specific configs (dev, staging, prod)
12.2. Feature Flags
[ ] 12.2.1. Implement feature flag for new feature
[ ] 12.2.2. Test feature toggle behavior
12.3. Deployment Preparation
[ ] 12.3.1. Create deployment checklist
[ ] 12.3.2. Document deployment order (database first, then service)
[ ] 12.3.3. Prepare rollback plan

13. Documentation
13.1. Code Documentation
[ ] 13.1.1. Add comprehensive JavaDoc comments to all public classes
[ ] 13.1.2. Document complex algorithms or logic
[ ] 13.1.3. Update inline comments for clarity
13.2. API Documentation
[ ] 13.2.1. Generate API documentation from OpenAPI spec
[ ] 13.2.2. Add usage examples for each endpoint
[ ] 13.2.3. Document authentication requirements
13.3. Architecture Documentation
[ ] 13.3.1. Update architecture diagrams with new components
[ ] 13.3.2. Document design decisions in ADR format
[ ] 13.3.3. Update component relationship diagrams

14. Review and Quality Assurance
14.1. Code Review
[ ] 14.1.1. Self-review code against coding standards
[ ] 14.1.2. Address static analysis findings (SonarQube, Checkstyle)
[ ] 14.1.3. Ensure test coverage meets requirements
14.2. Testing Review
[ ] 14.2.1. Verify all acceptance criteria have tests
[ ] 14.2.2. Review test coverage report (target: ≥85% via JaCoCo)
[ ] 14.2.3. Test edge cases and error conditions
14.3. Documentation Review
[ ] 14.3.1. Review all documentation for accuracy
[ ] 14.3.2. Verify all references and links work
[ ] 14.3.3. Check formatting and readability

---

## Dependency Matrix

| Phase | Depends On | Blocks | Can Parallelize With |
|-------|------------|--------|---------------------|
| 1. Setup | None | All phases | None |
| 2. API Contracts | Setup | Domain, Data Access | Database Changes |
| 3. Domain Layer | API Contracts | Data Access | None |
| 4. Data Access | Domain | Service | None |
| 5. Service Layer | Data Access | API Layer | None |
| 6. API Layer | Service | Integration Testing | None |
| 7. Database Changes | None | Integration Testing | Phases 2-6 |
| 8. Security | API Layer | Integration Testing | Error Handling |
| 9. Error Handling | API Layer | Integration Testing | Security |
| 10. Integration Testing | API Layer, Security, Error Handling | Performance | None |
| 11. Performance Testing | Integration Testing | Documentation | None |
| 12. Configuration | Setup | Deployment | Phases 2-11 |
| 13. Documentation | All implementation phases | Review | Configuration |
| 14. Review | Documentation | None | None |

### Within-Phase Dependencies

| Task Group | Depends On | Blocks |
|------------|------------|--------|
| Request/Response DTOs | Setup | Repositories, Services |
| Repository Interfaces | DTOs | Repository Tests |
| Custom Queries | Repo Interfaces | Services |
| Service Implementation | Repositories | Service Tests, Controllers |
| Service Tests | Service Impl | None (parallel) |
| Controller Implementation | Services | Controller Tests |
| Controller Tests | Controller Impl | Integration Tests |

## Parallelization Opportunities

**Can run in parallel (same wave):**
- Database migrations and API contract/DTO definition
- Security implementation and error handling (after API layer)
- Unit tests can start as each layer completes
- Documentation can run alongside testing phases

**Must be sequential:**
- DTOs → Repositories → Services → Controllers (dependency chain)
- Implementation → Integration Testing → Performance Testing

**Sub-agent dispatch guidance:**
- Wave 1: Setup + Database migrations (parallel)
- Wave 2: DTOs + Repository interfaces (parallel)
- Wave 3: Custom queries + Service interfaces
- Wave 4: Service implementation + Unit tests for repos
- Wave 5: Controller implementation + Service unit tests
- Wave 6: Security + Error handling (parallel)
- Wave 7: Integration tests + Controller unit tests
- Wave 8: Documentation + Performance tests (parallel)

---

## Appendix

### Task Dependencies

[Document any critical task dependencies or ordering requirements]

### Estimated Effort

[Optional: Add effort estimates if useful for planning]

| Phase | Task Count | Estimated Effort |
|-------|------------|------------------|
| Setup and Prerequisites | [count] | [estimate] |
| API Contracts and Models | [count] | [estimate] |
| ... | ... | ... |

### Notes

[Any additional context or considerations for implementing these tasks]
```

## Analysis Process

### Phase 1: Read and Understand the Technical Plan

1. **Read implementation-plan.md completely** from the entry point directory
2. **Identify all major sections** that require implementation work
3. **Note special requirements**:
   - Are there database changes? (needs migration tasks)
   - Are there stored procedures? (needs SP conversion tasks — see below)
   - Are there security requirements? (needs auth/permission tasks)
   - Are there external integrations? (needs integration tasks)

**Stored Procedure Conversion Tasks**: When the implementation plan contains a `## Stored Procedure Conversion Strategy` section, generate SP conversion tasks using the template below. These tasks MUST appear **before** Service Layer and Controller tasks in the task hierarchy, since the service/controller code depends on the converted SP logic.

```markdown
1.5. Stored Procedure Conversion (BEFORE Service Layer)

For each SP that needs conversion (not already converted by another endpoint):
[ ] 1.5.1. Check if [SP_NAME] already converted (search passage-api/src)
[ ] 1.5.2. Analyze [SP_NAME] using complexity scoring rubric (v9 guide §0a-0d)
[ ] 1.5.3. Create [SpNameService] shared service class replacing [SP_NAME] logic
[ ] 1.5.4. Create repository methods for [SP_NAME] (derived queries / Specifications / @Query)
[ ] 1.5.5. Handle [SP_NAME] temp table patterns (in-memory collections or CTEs)
[ ] 1.5.6. Handle [SP_NAME] cursor patterns (Stream<> or pagination) — if applicable
[ ] 1.5.7. Write unit tests for [SpNameService] verifying SP logic parity
[ ] 1.5.8. Write integration test comparing [SpNameService] output to legacy SP

For each SP already converted by another endpoint:
[ ] 1.5.9. Verify existing [SpNameService] covers this endpoint's usage
[ ] 1.5.10. Add missing methods/overloads to [SpNameService] if needed
[ ] 1.5.11. Import and wire [SpNameService] into this endpoint's service layer
```

Adjust the specific sub-tasks based on the SP's complexity score and the conversion pattern selected in the implementation plan. Not all SPs will have temp tables or cursors — only include those sub-tasks when applicable.
4. **Create todo list** for tracking task generation progress

### Phase 2: Extract Components and Work Items

For each section in the implementation plan, extract concrete work items:

1. **API Design section** → API contract tasks, OpenAPI tasks, controller tasks
2. **Domain Model section** → Entity creation tasks, relationship mapping tasks
3. **Service Layer section** → Service class tasks, method implementation tasks, validation tasks
4. **Data Access Layer section** → Repository interface tasks, query implementation tasks
5. **Database Changes section** → Migration script tasks, index creation tasks, rollback tasks
6. **Security Design section** → Authentication tasks, authorization tasks, data protection tasks
7. **Error Handling section** → Exception class tasks, error mapping tasks
8. **Testing Strategy section** → Unit test tasks, integration test tasks, E2E test tasks
9. **Configuration section** → Config property tasks, feature flag tasks
10. **Every model/DTO/class mentioned** → Task to create it
11. **Every method signature shown** → Task to implement it
12. **Every test scenario mentioned** → Task to write it

### Phase 3: Organize into Hierarchy

1. **Group related tasks** under appropriate top-level categories
2. **Create mid-level groupings** for logical sub-components
3. **Ensure proper numbering** follows the hierarchical format
4. **Add checkboxes** only to leaf-level actionable tasks

### Phase 4: Task Granularity Check

Review each leaf-level task and ensure it:
- [ ] Is specific and actionable
- [ ] Can be completed in a reasonable timeframe (hours to 1 day)
- [ ] Has a clear definition of "done"
- [ ] Is not too broad or vague
- [ ] Includes both implementation AND testing

### Phase 5: Completeness Verification

Cross-reference the task list against the implementation plan:
- [ ] Every API endpoint has tasks
- [ ] Every DTO/model has creation tasks
- [ ] Every service method has implementation and test tasks
- [ ] Every database change has migration and test tasks
- [ ] Every integration point has testing tasks
- [ ] Documentation tasks are included
- [ ] Security tasks are included
- [ ] Performance tasks are included (if applicable)
- [ ] Configuration tasks are included

### Phase 6: Dependency Analysis

Analyze task dependencies and parallelization opportunities:

1. **Map phase dependencies** - which phases depend on others
2. **Map within-phase dependencies** - task groups that must be sequential
3. **Identify parallel opportunities** - tasks that can run concurrently
4. **Document in Dependency Matrix** output section

**Standard API dependency patterns:**
- DTOs → Repositories → Services → Controllers (sequential chain)
- Database migrations can run in parallel with DTO creation
- Unit tests can start as each layer completes
- Security and Error Handling can run in parallel after API Layer

### Phase 7: Claude Task Tracking (Optional)

If the implementing agent will use Claude's task tracking:

1. **Create phase-level tasks** using `TaskCreate`:
   ```
   TaskCreate(
     subject="Phase 4: Data Access Layer",
     description="Create repository interfaces and implementations",
     activeForm="Implementing data access layer"
   )
   ```

2. **Set dependencies** using `TaskUpdate` with `addBlockedBy`:
   ```
   // Service Layer depends on Data Access Layer
   TaskUpdate(taskId="service-phase-id", addBlockedBy=["data-access-phase-id"])
   ```

3. **Document task IDs** in the task list appendix for reference during implementation

### Phase 8: Generate Output

1. **Write task-list.md** with proper formatting
2. **Count total tasks** (only leaf-level checkbox items)
3. **Add metadata** (source, date, task count)
4. **Include overview and progress tracking section**
5. **Include Dependency Matrix section**
6. **Include Parallelization Opportunities section**

## Critical Guidelines

### Task Extraction Rules

**DO extract tasks for**:
- Every class, interface, or component mentioned
- Every method signature defined
- Every DTO/model with fields
- Every database table or migration
- Every API endpoint
- Every test scenario mentioned
- All documentation updates
- All configuration requirements
- All deployment steps

**DO NOT create tasks for**:
- Vague planning activities ("Think about X")
- Already-completed analysis work
- Decision-making (those should be done in the plan)
- Optional/future enhancements (unless explicitly in plan)

### Hierarchical Organization

**Level 1 (Top-Level)** - Major phases or system layers:
- Examples: "Setup and Prerequisites", "Domain Layer", "Service Layer", "Testing"
- No checkboxes
- Typically 10-15 top-level items

**Level 2 (Mid-Level)** - Sub-components or logical groupings:
- Examples: "Repository Interfaces", "Service Implementation", "Unit Tests"
- No checkboxes
- Typically 2-5 mid-level items per top-level item

**Level 3 (Leaf-Level)** - Specific actionable tasks:
- Examples: "Create CompanyDTO with all fields", "Implement findById() method", "Write unit test for validation"
- WITH checkboxes `[ ]`
- Typically 3-10 tasks per mid-level item

### Task Specificity

```markdown
GOOD (Specific and actionable):
[ ] 1.1.1. Create CompanyAddressRequest DTO with companyId, addressType, and includeInactive fields
[ ] 2.3.1. Implement AddressService.findByCompany() method with validation and error handling
[ ] 3.1.1. Write unit tests for AddressService.findByCompany() covering success and error cases

BAD (Too vague or too large):
[ ] 1.1.1. Create all DTOs
[ ] 2.3.1. Implement service layer
[ ] 3.1.1. Add tests
```

### Testing Tasks

**CRITICAL**: For every implementation task, create corresponding test tasks:

```markdown
5. Service Layer
5.1. Service Implementation
[ ] 5.1.1. Create AddressService class with @Service annotation
[ ] 5.1.2. Implement findByCompany() method
5.2. Service Tests  ← MUST HAVE
[ ] 5.2.1. Write unit test for findByCompany() with valid input using Mockito
[ ] 5.2.2. Write unit test for findByCompany() with invalid company ID
[ ] 5.2.3. Write unit test for findByCompany() with empty result set
```

### Documentation Tasks

**CRITICAL**: Always include comprehensive documentation tasks:

```markdown
13. Documentation
13.1. Code Documentation
[ ] 13.1.1. Add JavaDoc comments to all public classes
[ ] 13.1.2. Add method-level documentation with examples
13.2. API Documentation
[ ] 13.2.1. Generate API docs from OpenAPI spec
[ ] 13.2.2. Add usage examples for each endpoint
13.3. Architecture Documentation
[ ] 13.3.1. Update architecture diagrams with new components
[ ] 13.3.2. Document design decisions in ADR format
```

## Task Management

Use TodoWrite tool to track progress:

```
Initial Setup:
- Read implementation-plan.md from entry point directory
- Identify all major sections requiring tasks
- Create output file task-list.md with template structure

Task Extraction:
- Extract tasks from API Design section
- Extract tasks from Domain Model section
- Extract tasks from Service Layer section
- Extract tasks from Data Access Layer section
- Extract tasks from Database Changes section
- Extract tasks from Security Design section
- Extract tasks from Error Handling section
- Extract tasks from Testing Strategy section

Task Organization:
- Group tasks into hierarchical structure
- Apply proper numbering format
- Add checkboxes to leaf-level tasks only
- Verify task granularity

Quality Checks:
- Verify completeness against implementation plan
- Check every model/DTO has a creation task
- Check every method has implementation and test tasks
- Check all documentation updates included
- Count total tasks and update metadata

Finalization:
- Write final task-list.md file
- Add overview and progress tracking section
- Final review for formatting consistency
```

## API Technology Stack Reference

### Backend Framework
- Spring Boot with Java
- Spring Web for REST controllers
- Spring Data JPA for data access
- Spring Security for authentication/authorization

### Build System
- Gradle (build.gradle, settings.gradle)

### Database
- JPA/Hibernate for ORM
- Flyway or Liquibase for migrations

### Testing
- JUnit 5 for unit tests
- Mockito for mocking
- @WebMvcTest for controller tests
- @DataJpaTest for repository tests
- @SpringBootTest for integration tests

### Configuration
- application.yml for configuration
- Spring profiles for environment-specific configs

## Success Criteria

**Completeness**:
- [ ] Every section of implementation plan has corresponding tasks
- [ ] Every class/interface/DTO mentioned has a creation task
- [ ] Every method has implementation and test tasks
- [ ] Database changes have migration and rollback tasks
- [ ] Documentation tasks are comprehensive
- [ ] Configuration and deployment tasks included

**Organization**:
- [ ] Three-level hierarchy is consistent throughout
- [ ] Proper numbering format (1., 1.1., [ ] 1.1.1.)
- [ ] Checkboxes only on leaf-level tasks
- [ ] Logical grouping of related tasks

**Quality**:
- [ ] Leaf-level tasks are specific and actionable
- [ ] Each task has clear definition of done
- [ ] Task granularity is appropriate (hours to 1 day)
- [ ] No vague or overly broad tasks
- [ ] Testing tasks parallel implementation tasks

**Format**:
- [ ] Metadata section with source and task count
- [ ] Overview with progress tracking template
- [ ] Consistent markdown formatting
- [ ] Proper indentation (not spaces for alignment)

## Troubleshooting

### Too Many Tasks

**Problem**: Task list has hundreds of checkbox items

**Solutions**:
1. Merge overly granular tasks (e.g., "add field X" + "add field Y" → "add all DTO fields")
2. Ensure you're not duplicating tasks
3. Consider if some tasks should be grouped at mid-level without checkbox
4. Verify tasks are implementation-focused, not planning-focused

### Too Few Tasks

**Problem**: Task list seems incomplete

**Solutions**:
1. Re-read implementation plan for overlooked sections
2. Ensure each model/DTO/class has explicit creation task
3. Check that test tasks exist for every implementation task
4. Verify documentation tasks are comprehensive
5. Check database, security, configuration sections weren't skipped

### Unclear Task Boundaries

**Problem**: Hard to know where one task ends and another begins

**Solutions**:
1. Focus on single-responsibility: one task = one cohesive unit of work
2. Use the "could I mark this done in one sitting?" test
3. Separate creation from testing (two tasks, not one)
4. Keep DTOs, services, repositories as separate tasks

### Inconsistent Hierarchy

**Problem**: Numbering or structure is inconsistent

**Solutions**:
1. Follow strict three-level format
2. Use regex or careful review to check numbering
3. Ensure checkboxes only at level 3
4. Verify indentation is consistent

---

**End of Command Specification**
