---
model: opus
hooks:
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --from-stdin
            --log
            --file-pattern "*implementation-plan-review*"
            --contains '# Implementation Plan Review Report'
            --contains 'Status:'
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*implementation-plan-review*"
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*implementation-plan-review*"
            --contains '# Implementation Plan Review Report'
            --contains 'Status:'
---

# Review Implementation Plan - Database Triggers

Review an implementation plan for database trigger modernization, validating quality, accuracy, completeness, and adherence to target architecture standards.

## Common Foundation

@develop.review-plan-common.md

## Trigger-Specific Context

This review type is for **Database Triggers** (INSERT/UPDATE/DELETE triggers, audit triggers, cascade triggers, business rule enforcement triggers). Focus on trigger analysis accuracy, modernization strategy selection, business rule extraction, data synchronization patterns, migration planning, and rollback procedures.

## Open Questions Policy

**Resolve questions — do not defer them.** When reviewing, you will identify questions and concerns. For each one:

1. **Check the pattern files first** (`servicebus-send.md`, `servicebus-receive.md`) — project-wide decisions like `transaction_user`, migration strategy (parallel operation with legacy triggers enabled), type conversion utilities, and auto-publish behavior are already decided here
2. **Check the functional spec and legacy trigger source** — business logic details are documented
3. **Check the implementation plan itself** — it may address the concern in another section
4. **Implementation details are not open questions** — if the answer is "follow the existing pattern" or "add it like the other utilities," resolve it with a recommendation, do not ask a human

**Mark a question as resolved** with the source that answers it. Strike it through and note the resolution.

**The only legitimate open questions** are ones that require information not available in any loaded document — such as production data characteristics or business stakeholder decisions that have no documented precedent. Even then, note whether the question blocks implementation or is deferrable.

**Questions about patterns that already exist** (e.g., "should we add `toLong()` to the base class that already has `toInteger()`?") are implementation decisions, not open questions — resolve them with the obvious answer.

## Usage

```
/develop.review-plan-trigger key: [key]
```

**Examples:**
```
/develop.review-plan-trigger key: triggers-trd-discount
```

```
/develop.review-plan-trigger key: triggers-tri-cm-contact
```

## Input

The command receives an inventory item JSON payload:

```json
{
  "key": "triggers-trd-discount",
  "name": "dbo.TRD_DISCOUNT",
  "location": "./legacy/database/TRIGGERS/TRD_DISCOUNT.tri",
  "type": "database-triggers",
  "table": "dbo.discount",
  "notes": []
}
```

Use `key` to locate the entry point directory:
```
./docs/entry-points/database-triggers/{key}/
```

## Trigger-Specific Review Checklist

In addition to the common review checklist, verify the following trigger-specific items.

**CRITICAL - Target Architecture Documents**: Before reviewing, YOU MUST READ these target architecture documents:
- `./docs/target-architecture/servicebus-send.md` — Send-side pattern, TriggerEntity registration, auto-publish
- `./docs/target-architecture/servicebus-receive.md` — Receive-side pattern, handler categories, implementation checklist
- `./docs/target-architecture/patterns/trigger-patterns/servicebus-send-event.v1.md` — Send pattern file
- `./docs/target-architecture/patterns/trigger-patterns/servicebus-receive-event.v1.md` — Receive pattern file
- `./docs/target-architecture/backend-architecture.md` - Service layer patterns, Spring Boot patterns
- `./docs/target-architecture/tech-stack.md` - Approved frameworks and versions

Verify the implementation plan aligns with the ServiceBus handler pattern documented in these files.

---

### Trigger-1. Trigger Analysis Completeness (CRITICAL)

**Goal**: Ensure the trigger analysis accurately captures all trigger behavior.

**Verify trigger metadata**:

#### Trigger Identification:
- [ ] Trigger name correctly identified
- [ ] Target table correctly identified
- [ ] Trigger events documented (INSERT, UPDATE, DELETE, or combination)
- [ ] Trigger timing documented (BEFORE, AFTER, INSTEAD OF)
- [ ] Row-level vs statement-level behavior documented
- [ ] Source location correctly referenced

#### Trigger Flow:
- [ ] Trigger flow diagram present (Mermaid or equivalent)
- [ ] All decision points shown
- [ ] All error paths shown
- [ ] Cursor-based processing documented (if applicable)
- [ ] Savepoint/rollback behavior documented

#### Column Dependencies (for UPDATE triggers):
- [ ] UPDATE triggers list specific columns monitored
- [ ] Column change detection logic documented
- [ ] If-column-changed logic accurately represented

#### Tables Accessed:
- [ ] All tables READ by trigger listed with purpose
- [ ] All tables WRITTEN by trigger listed with operation and condition
- [ ] Pseudo-tables (INSERTED, DELETED) usage documented
- [ ] Join conditions documented for complex queries

#### Error Handling:
- [ ] All error conditions documented
- [ ] Error codes/messages captured
- [ ] Rollback behavior documented
- [ ] RAISERROR statements captured

**ACTION**: Complete missing trigger metadata, correct flow diagram, add missing table dependencies.

---

### Trigger-2. Trigger Purpose Classification (CRITICAL)

**Goal**: Ensure trigger purpose is correctly classified for appropriate modernization strategy.

**Verify purpose classification**:

#### Primary Purpose Identification:
- [ ] Primary purpose clearly stated (one of the following):
  - **Business Rule Enforcement** - Validates data, enforces constraints
  - **Data Synchronization** - Keeps related tables in sync
  - **Audit Trail** - Logs changes for compliance/history
  - **Cascade Operations** - Propagates changes to related entities
  - **Computed Values** - Calculates and stores derived values
  - **Notifications** - Triggers alerts or messages
  - **Data Transformation** - Transforms data on write

#### Secondary Purposes:
- [ ] Secondary purposes listed (if any)
- [ ] Purpose priorities correct (primary vs secondary)

#### Purpose Implications:
- [ ] Modernization approach aligns with purpose
- [ ] Sync vs async processing decision appropriate for purpose
- [ ] Transactional requirements match purpose criticality

**ACTION**: Correct purpose classification if incorrect, update modernization approach accordingly.

---

### Trigger-3. ServiceBus Handler Pattern (CRITICAL)

**Goal**: Ensure the plan uses the ServiceBus handler pattern and all required sections are present.

**Verify send side**:

#### TriggerEntity Registration:
- [ ] `## TriggerEntity Registration` section present
- [ ] Entity key specified and matches `@Table(name)` on the JPA entity (case-insensitive)
- [ ] Legacy trigger names listed
- [ ] Existing TriggerEntity entries were checked for duplicates
- [ ] If already registered, plan notes this and skips registration

#### Auto-Publish Configuration:
- [ ] Plan confirms `@TriggerHandler` annotation is sufficient for auto-publish
- [ ] No unnecessary `@TriggerPublisher` added unless justified for documentation

**Verify receive side**:

#### Handler Design:
- [ ] `## Handler Design` section present
- [ ] Correct base class selected:
  - `h-triggers-*` → `AbstractHistoryHandler` pattern
  - `triggers-*` → `TriggerEventHandler<Map<String, Object>>` pattern
- [ ] Handler class name and package specified
- [ ] Handler placed in correct domain package (derived from source entity's package)
- [ ] Operations listed (CREATE/UPDATE/DELETE) match the legacy trigger events

#### Column Mapping:
- [ ] `## Column Mapping` section present with table
- [ ] Map keys use **camelCase Java property names** (NOT SQL column names)
- [ ] Type conversion methods specified for each field (`toInteger()`, `toLocalDateTime()`, `toString()`, etc.)
- [ ] For history handlers: `transactionType`, `transactionDate`, `transactionUser` fields mapped
- [ ] `transaction_user` uses `LAST_MOD_USER_ID` (not `suser_name()`)

#### Circular Publishing Analysis:
- [ ] `## Circular Publishing Analysis` section present
- [ ] Handler's write targets listed
- [ ] Confirmed write targets are NOT in `TriggerEntity` enum (or chain terminates if they are)

**ACTION**: If any section is missing or uses a generic modernization strategy instead of the ServiceBus handler pattern, flag as FAIL and specify what needs correction.

---

### Trigger-4. Business Rules Extraction (CRITICAL)

**Goal**: Ensure all business rules embedded in trigger are extracted and documented.

**Verify business rules**:

#### Rules Extraction:
- [ ] Each business rule has unique ID (BR-001, BR-002, etc.)
- [ ] Rule description is clear and complete
- [ ] Source line reference provided
- [ ] Criticality assigned (Critical, High, Medium, Low)

#### Rule Implementation Design:
- [ ] Current implementation (trigger) code shown
- [ ] Modern implementation (Java/TypeScript) code shown
- [ ] Validation placement documented (service layer, event handler, constraint)
- [ ] Edge cases handled

#### Rule Completeness:
- [ ] All conditional logic (IF statements) captured as rules
- [ ] All validation checks captured as rules
- [ ] All filtering logic captured as rules
- [ ] All error conditions captured as rules

#### Rule Accuracy:
- [ ] Modern implementation preserves exact rule behavior
- [ ] No rule logic lost in translation
- [ ] No rule logic added beyond original trigger

**ACTION**: Add missing business rules, correct rule implementations, ensure completeness.

---

### Trigger-5. Data Synchronization Design (for sync triggers)

**Goal**: Ensure data synchronization is properly designed for triggers that sync data between tables.

**Verify data sync design** (if trigger purpose is Data Synchronization):

#### Sync Behavior Documentation:
- [ ] Source table identified
- [ ] Target table(s) identified
- [ ] Operation per target (INSERT, UPDATE, DELETE)
- [ ] Conditions for sync documented
- [ ] Data transformation documented

#### Event Design:
- [ ] Domain event class defined with all necessary fields
- [ ] Event published within same transaction
- [ ] Correlation ID for traceability
- [ ] Event immutability ensured

#### Event Handler Design:
- [ ] Event handler class defined
- [ ] Handler runs within correct transaction phase
- [ ] Error handling preserves atomicity
- [ ] Idempotency considered

#### Transactional Outbox (if applicable):
- [ ] Outbox entity defined
- [ ] Outbox repository defined
- [ ] Outbox processor implemented
- [ ] Processing interval documented
- [ ] Retry and dead-letter logic documented

**ACTION**: Complete data sync design, ensure transactional consistency maintained.

---

### Trigger-6. Transaction Handling Design (CRITICAL)

**Goal**: Ensure transaction boundaries and atomicity are correctly designed.

**Verify transaction design**:

#### Atomicity Requirements:
- [ ] Original trigger's atomicity documented
- [ ] Modern implementation preserves atomicity
- [ ] All-or-nothing semantics maintained (especially for batch operations)
- [ ] Savepoint behavior replicated or explicitly changed

#### Transaction Boundaries:
- [ ] `@Transactional` annotations correct
- [ ] Propagation settings appropriate
- [ ] Rollback conditions documented
- [ ] Exception handling triggers appropriate rollbacks

#### Event Listener Phases:
- [ ] `@TransactionalEventListener` phase correct:
  - `BEFORE_COMMIT` for sync within transaction
  - `AFTER_COMMIT` for async after transaction
- [ ] Phase selection justified based on requirements

#### Batch Processing:
- [ ] Batch operation atomicity documented
- [ ] All-or-nothing vs partial-success explicitly chosen
- [ ] Batch size considerations documented

**ACTION**: Correct transaction handling issues, ensure atomicity preserved.

---

### Trigger-7. Error Handling and Rollback Design (CRITICAL)

**Goal**: Ensure comprehensive error handling matches or improves upon trigger behavior.

**Verify error handling**:

#### Error Classification:
- [ ] All error types from trigger identified
- [ ] Error mapping to exceptions documented
- [ ] Exception hierarchy designed

#### Error Messages:
- [ ] Original error messages captured
- [ ] Modern error messages user-friendly
- [ ] Error codes maintained for compatibility

#### Rollback Behavior:
- [ ] Trigger rollback behavior documented
- [ ] Modern rollback behavior matches or explicitly differs
- [ ] Partial rollback scenarios handled

#### Exception Handling:
- [ ] Service layer catches and handles exceptions appropriately
- [ ] Event handler exceptions cause transaction rollback
- [ ] Logging captures sufficient context for debugging

**ACTION**: Complete error mapping, ensure rollback behavior correct.

---

### Trigger-8. Performance Design

**Goal**: Ensure performance is adequately considered in the modernization plan.

**Verify performance design**:

#### Current Impact Assessment:
- [ ] Trigger latency impact documented per event type
- [ ] Lock duration documented
- [ ] Known performance issues documented

#### Modern Implementation Performance:
- [ ] Expected latency for sync approach documented
- [ ] Expected latency for async approach documented (if applicable)
- [ ] Comparison with current trigger performance

#### Optimization Strategies:
- [ ] Batch repository operations used where appropriate
- [ ] Query optimization documented
- [ ] Index requirements identified
- [ ] Connection pooling considerations

#### Performance Testing Plan:
- [ ] Baseline measurement plan defined
- [ ] Benchmark scenarios defined
- [ ] Acceptance criteria specified (latency thresholds)
- [ ] Load testing scenarios defined

**ACTION**: Complete performance documentation, add missing optimization strategies.

---

### Trigger-9. Testing Strategy Completeness (CRITICAL)

**Goal**: Ensure testing strategy adequately validates trigger migration.

**Verify testing coverage**:

#### Unit Tests:
- [ ] Service layer unit tests defined
- [ ] Event handler unit tests defined
- [ ] Mocking strategy documented
- [ ] Edge cases covered

#### Integration Tests:
- [ ] Full workflow tests defined
- [ ] Transaction rollback tests defined
- [ ] Batch operation tests defined
- [ ] Database integration tests defined

#### Regression Tests (CRITICAL):
- [ ] **Trigger parity tests** defined - comparing trigger vs app behavior
- [ ] Test scenarios cover all trigger behaviors
- [ ] Expected results match legacy trigger behavior
- [ ] Side-by-side comparison mechanism documented

#### Test Data Strategy:
- [ ] Test fixtures documented
- [ ] Test data covers all scenarios (GRANTED vs PENDING, single vs batch, etc.)
- [ ] SQL test data scripts referenced

**ACTION**: Complete testing strategy, ensure regression tests for trigger parity.

---

### Trigger-10. Migration and Deployment Plan (CRITICAL)

**Goal**: Ensure migration plan is complete and rollback procedures are clear.

**Verify migration plan**:

#### Pre-Migration Checklist:
- [ ] Checklist present with all prerequisites
- [ ] All dependencies identified
- [ ] Backup strategy documented

#### Migration Phases:
- [ ] Each phase has clear goals
- [ ] Each phase has specific tasks
- [ ] Each phase has success criteria
- [ ] Each phase has rollback plan

#### Parallel Operation Phase:
- [ ] Feature flag implementation documented
- [ ] Traffic percentage ramping plan
- [ ] Discrepancy monitoring plan
- [ ] Duration adequate (minimum 2 weeks recommended)

#### Cutover Phase:
- [ ] `DISABLE TRIGGER` command documented
- [ ] Monitoring requirements for 48-72 hours
- [ ] Success criteria defined

#### Cleanup Phase:
- [ ] `DROP TRIGGER` command documented
- [ ] Feature flag removal documented
- [ ] Documentation update requirements

#### Rollback Procedures:
- [ ] Immediate rollback (during parallel phase) documented
- [ ] Emergency rollback (after cutover) documented
- [ ] Data recovery procedure (if queue entries missed) documented
- [ ] Recovery time estimates provided

**ACTION**: Complete migration phases, ensure rollback procedures are thorough.

---

### Trigger-11. Risk Assessment Completeness

**Goal**: Ensure risks are thoroughly identified and mitigated.

**Verify risk assessment**:

#### Technical Risks:
- [ ] Logic divergence risk addressed
- [ ] Performance degradation risk addressed
- [ ] Event delivery failure risk addressed
- [ ] Transaction timeout risk addressed
- [ ] Deadlock risk addressed

#### Operational Risks:
- [ ] Direct SQL bypass risk addressed
- [ ] Incomplete testing risk addressed
- [ ] Insufficient monitoring risk addressed
- [ ] Rollback readiness risk addressed

#### Business Risks:
- [ ] Data integrity risk addressed
- [ ] Customer impact risk addressed
- [ ] Compliance risk addressed

#### Risk Documentation:
- [ ] Each risk has probability and impact
- [ ] Each risk has mitigation strategy
- [ ] Each risk has contingency plan

**ACTION**: Add missing risks, complete mitigation and contingency plans.

---

### Trigger-12. Monitoring and Observability Design

**Goal**: Ensure monitoring is adequately designed for the migrated logic.

**Verify monitoring design**:

#### Metrics:
- [ ] Key metrics identified (deletion count, duration, errors, queue entries)
- [ ] Alert thresholds defined
- [ ] Metric collection mechanism specified

#### Logging Strategy:
- [ ] Structured logging format documented
- [ ] Key log events identified
- [ ] Correlation ID strategy documented
- [ ] Log levels appropriate

#### Dashboards:
- [ ] Dashboard requirements documented
- [ ] Migration progress dashboard (for parallel phase) defined
- [ ] Operational dashboard defined

**ACTION**: Complete monitoring design, ensure adequate observability.

---

### Trigger-13. Open Questions Quality

**Goal**: Ensure open questions are actionable and appropriately categorized.

**Verify open questions**:

#### Question Categories:
- [ ] Technical questions present
- [ ] Business questions present
- [ ] Data questions present

#### Question Quality:
- [ ] Each question has "Why" context
- [ ] Each question has recommended action
- [ ] Each question has owner assigned
- [ ] No questions that should have been answered during analysis

#### Critical Questions Flagged:
- [ ] Questions that block implementation identified
- [ ] Questions that affect architecture identified

**ACTION**: Improve question quality, assign owners, remove already-answered questions.

---

## Trigger-Specific Report Sections

Add these sections to the review report for trigger plans:

```markdown
## Trigger Analysis

| Aspect | Status | Notes |
|--------|--------|-------|
| Trigger Metadata | ✓/Corrected | [Details] |
| Flow Diagram | ✓/Corrected | [Details] |
| Purpose Classification | ✓/Corrected | [Details] |
| Tables Accessed | ✓/Corrected | [Details] |
| Error Handling | ✓/Corrected | [Details] |

## Modernization Strategy

| Aspect | Status | Notes |
|--------|--------|-------|
| Strategy Selection | ✓/Corrected | [Details] |
| Strategy Justification | ✓/Corrected | [Details] |
| Migration Path | ✓/Corrected | [Details] |
| Parallel Operation Plan | ✓/Corrected | [Details] |

## Business Rules Extraction

| Aspect | Status | Notes |
|--------|--------|-------|
| Rules Identified | [N] rules extracted | [Details] |
| Rules Complete | ✓/Corrected | [Details] |
| Modern Implementations | ✓/Corrected | [Details] |
| Validation Placement | ✓/Corrected | [Details] |

## Transaction Handling

| Aspect | Status | Notes |
|--------|--------|-------|
| Atomicity Preserved | ✓/Corrected | [Details] |
| Transaction Boundaries | ✓/Corrected | [Details] |
| Event Listener Phases | ✓/Corrected | [Details] |
| Batch Processing | ✓/Corrected/N/A | [Details] |

## Testing Strategy

| Aspect | Status | Notes |
|--------|--------|-------|
| Unit Tests | ✓/Corrected | [Details] |
| Integration Tests | ✓/Corrected | [Details] |
| Regression Tests (Parity) | ✓/Corrected | [Details] |
| Test Data | ✓/Corrected | [Details] |

## Migration Plan

| Aspect | Status | Notes |
|--------|--------|-------|
| Migration Phases | ✓/Corrected | [Details] |
| Parallel Operation | ✓/Corrected | [Details] |
| Rollback Procedures | ✓/Corrected | [Details] |
| Monitoring | ✓/Corrected | [Details] |

## Risk Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Technical Risks | ✓/Corrected | [Details] |
| Operational Risks | ✓/Corrected | [Details] |
| Business Risks | ✓/Corrected | [Details] |
| Mitigations Complete | ✓/Corrected | [Details] |
```

---

## Trigger-Specific Success Criteria

In addition to common success criteria:

**Trigger Analysis**:
- [ ] Trigger metadata complete and accurate
- [ ] Flow diagram accurately represents trigger behavior
- [ ] Purpose classification correct
- [ ] All table dependencies documented

**Modernization Strategy**:
- [ ] Appropriate strategy selected for trigger purpose
- [ ] Strategy follows target architecture patterns
- [ ] Migration path clearly defined
- [ ] Parallel operation phase included

**Business Rules**:
- [ ] All business rules extracted
- [ ] Modern implementations preserve rule behavior
- [ ] Validation placement appropriate

**Transaction Handling**:
- [ ] Atomicity preserved
- [ ] Transaction boundaries correct
- [ ] Event listener phases appropriate

**Testing**:
- [ ] Comprehensive test coverage
- [ ] **Regression tests for trigger parity**
- [ ] Test data strategy defined

**Migration**:
- [ ] All phases defined with clear tasks
- [ ] Rollback procedures thorough
- [ ] Monitoring adequate for parallel phase

**Risk Assessment**:
- [ ] All risk categories covered
- [ ] Mitigations and contingencies defined

---

## Trigger-Specific Execution Instructions

1. **Parse the key parameter** from the command invocation

2. **Construct the directory path**: `./docs/entry-points/database-triggers/{key}/`

3. **Read all relevant files from the directory**:
   - `implementation-plan.md` (required)
   - `functional-spec.md` (required for traceability)
   - `functional-description.md` (for additional context)
   - `metadata.json` (for context, includes target table)
   - `database-dependencies.json` (if exists)
   - `call-tree.txt` (for stored procedure dependencies)
   - Target architecture documents (backend-architecture, data-access-migration, tech-stack)

4. **Systematically work through each review check** (common + trigger-specific)

5. **Make corrections directly** to implementation-plan.md as you find issues

6. **Track all findings** for the report

7. **Generate the review report** as `implementation-plan-review.md` in the same directory

8. **Provide brief summary** to user of review outcome

---

## Trigger-Specific Troubleshooting

### Strategy Mismatch

**Problem**: Selected strategy doesn't fit trigger purpose

**Solutions**:
1. Re-evaluate trigger purpose classification
2. Review target architecture patterns
3. Consider data synchronization needs (sync vs async)
4. Consider transaction requirements (atomicity critical?)
5. Document rationale for strategy change in review report

### Business Rule Complexity

**Problem**: Trigger contains complex business logic difficult to extract

**Solutions**:
1. Break complex logic into multiple atomic rules
2. Ensure each rule is independently testable
3. Preserve exact behavior, don't optimize during extraction
4. Add comprehensive test cases for complex rules
5. Consider staged migration for very complex triggers

### Transaction Boundary Challenges

**Problem**: Modern implementation can't preserve exact transaction semantics

**Solutions**:
1. Use `@TransactionalEventListener(phase = BEFORE_COMMIT)` for sync
2. Use transactional outbox for reliable async
3. Document any semantic changes explicitly
4. Extend parallel operation phase to validate behavior
5. Add specific tests for atomicity scenarios

### Parallel Operation Complexity

**Problem**: Running trigger and app logic simultaneously causes issues

**Solutions**:
1. Use feature flag to control app logic execution
2. Design for idempotency (both can run safely)
3. Monitor for discrepancies between trigger and app results
4. Start with very low traffic percentage (5-10%)
5. Extend parallel phase duration if discrepancies found

### Stored Procedure Dependencies

**Problem**: Trigger calls complex stored procedures

**Solutions**:
1. Extract stored procedure logic to Java services
2. Document stored procedure dependencies in call tree
3. Consider migrating stored procedures first
4. Ensure event handlers replicate stored procedure behavior
5. Test against stored procedure outputs for parity

### Direct SQL Access

**Problem**: External systems modify table directly, bypassing application layer

**Solutions**:
1. Document all direct SQL access patterns
2. Keep trigger enabled during entire parallel phase
3. Plan for migrating all access to API-based approach
4. Consider extended transition period
5. Flag as operational risk with mitigation plan

### Performance Regression

**Problem**: Modern implementation slower than trigger

**Solutions**:
1. Profile and identify bottlenecks
2. Optimize repository queries
3. Add missing database indexes
4. Consider async processing if acceptable
5. Document performance trade-offs vs maintainability

### Audit Trail Requirements

**Problem**: Trigger provides audit logging that must be preserved

**Solutions**:
1. Implement equivalent audit logging in event handlers
2. Use structured logging with correlation IDs
3. Ensure audit records written within same transaction
4. Verify audit completeness in regression tests
5. Consult compliance team for requirements

---

**End of Command Specification**
