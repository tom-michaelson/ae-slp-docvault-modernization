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

# Review Implementation Plan - Batch

Review an implementation plan for batch jobs, validating quality, accuracy, completeness, and adherence to target architecture standards.

## Common Foundation

@develop.review-plan-common.md

## Batch-Specific Context

This review type is for **Batch Jobs and Scheduled Processes** (nightly jobs, data imports/exports, periodic processing, scheduled reports). Focus on job execution design, scheduling, error recovery, monitoring, and data processing patterns.

## Usage

```
/develop.review-plan-batch key: [key]
```

**Examples:**
```
/develop.review-plan-batch key: nightly-order-sync
```

```
/develop.review-plan-batch key: monthly-billing-calculation
```

## Input

The command receives an inventory item JSON payload:

```json
{
  "key": "nightly-order-sync",
  "name": "Nightly Order Synchronization",
  "location": "./legacy/batch/src/jobs/OrderSyncJob.java",
  "type": "batch-jobs",
  "notes": [
    "Spring Batch job",
    "Runs at 2 AM nightly",
    "Processes previous day's orders"
  ]
}
```

Use `key` to locate the entry point directory:
```
./docs/entry-points/batch-jobs/{key}/
```

## Batch-Specific Review Checklist

In addition to the common review checklist, verify the following batch-specific items.

**CRITICAL - Target Architecture Documents**: Before reviewing, YOU MUST READ these target architecture documents:
- `./docs/target-architecture/batch-job-design.md` - Batch processing approach and Quartz usage
- `./docs/target-architecture/backend-architecture.md` - Service layer patterns, Spring Boot patterns
- `./docs/target-architecture/data-access-migration.md` - Repository patterns, JPA patterns
- `./docs/target-architecture/tech-stack.md` - Approved frameworks and versions

Verify the implementation plan aligns with patterns documented in these files.

---

### Batch-1. Job Architecture Completeness (CRITICAL)

**Goal**: Ensure job structure is well-designed and complete.

**Verify job architecture**:

#### Job Flow:
- [ ] Job flow diagram present
- [ ] All steps identified
- [ ] Step sequence documented
- [ ] Conditional flows documented (if any)
- [ ] Error paths shown

#### Job Definition:
- [ ] Job name specified
- [ ] Job type documented (Spring Batch, Quartz, Custom)
- [ ] Execution mode specified (single instance, parallel allowed)
- [ ] Job parameters documented with types and defaults

#### Step Configuration:
- [ ] Each step defined
- [ ] Step type specified (Chunk, Tasklet)
- [ ] Reader/Processor/Writer for chunk steps
- [ ] Chunk size specified
- [ ] Transaction boundaries defined

**ACTION**: Add missing job architecture details, complete step configurations.

---

### Batch-2. Scheduling Design Completeness (CRITICAL)

**Goal**: Ensure scheduling is properly designed.

**Verify scheduling**:

#### Schedule Configuration:
- [ ] Schedule type documented (Cron, Fixed Rate, Event-Driven)
- [ ] Cron expression or interval specified
- [ ] Timezone documented
- [ ] Schedule explained in human terms

#### Dependencies:
- [ ] Job dependencies documented
- [ ] Must-run-after relationships specified
- [ ] Must-complete-before relationships specified
- [ ] Mutual exclusion rules documented

#### Business Calendar:
- [ ] Business day rules documented (if applicable)
- [ ] Holiday handling specified
- [ ] Month-end handling specified (if applicable)

#### SLA Requirements:
- [ ] Start time SLA documented
- [ ] Completion time SLA documented
- [ ] Maximum duration specified
- [ ] Escalation procedures documented

**ACTION**: Complete scheduling documentation, add missing SLA requirements.

---

### Batch-3. Data Processing Design (CRITICAL)

**Goal**: Ensure data processing is well-designed.

**Verify data processing**:

#### Data Flow:
- [ ] Data flow diagram present
- [ ] Source systems identified
- [ ] Target systems identified
- [ ] Intermediate storage (if any) documented

#### Reader Design:
- [ ] Reader type specified
- [ ] Data source documented
- [ ] Selection criteria/query documented
- [ ] Batch/fetch size specified
- [ ] Cursor vs paging strategy documented

#### Processor Design:
- [ ] Processor purpose documented
- [ ] Input/output types specified
- [ ] Transformation rules documented
- [ ] Validation rules documented
- [ ] Filter conditions documented (items to skip)

#### Writer Design:
- [ ] Writer type specified
- [ ] Target destination documented
- [ ] Operation documented (insert/update/upsert)
- [ ] Batch size specified
- [ ] Transaction boundary documented

**ACTION**: Complete data processing documentation.

---

### Batch-4. Error Handling and Recovery (CRITICAL)

**Goal**: Ensure comprehensive error handling and recovery design.

**Verify error handling**:

#### Error Classification:
- [ ] Error types identified
- [ ] Severity levels assigned
- [ ] Actions for each error type documented
- [ ] Retry eligibility determined

#### Skip Policy:
- [ ] Skippable exceptions defined
- [ ] Skip limit specified
- [ ] Skip logging documented
- [ ] Skip review process documented

#### Retry Policy:
- [ ] Retryable exceptions defined
- [ ] Maximum retries specified
- [ ] Backoff strategy documented
- [ ] Backoff parameters (initial, multiplier, max)

#### Restart and Resume:
- [ ] Restartable flag documented
- [ ] Checkpoint strategy documented
- [ ] Resume behavior documented
- [ ] Already-processed item handling documented

#### Idempotency:
- [ ] Each operation's idempotency assessed
- [ ] Idempotency strategy for non-idempotent operations
- [ ] Correlation ID tracking (if needed)

**ACTION**: Complete error handling specifications, ensure recovery strategy.

---

### Batch-5. Monitoring and Alerting Design

**Goal**: Ensure proper monitoring and alerting design.

**Verify monitoring**:

#### Job Metrics:
- [ ] Metrics to collect documented
- [ ] Collection mechanism specified
- [ ] Metrics exposed to monitoring system

#### Alerting Rules:
- [ ] Alert conditions defined
- [ ] Severity levels assigned
- [ ] Notification channels specified
- [ ] Escalation procedures documented

#### Logging Strategy:
- [ ] Log levels defined
- [ ] What to log at each level documented
- [ ] Log retention requirements

#### Dashboard Integration:
- [ ] Dashboard requirements documented
- [ ] Key metrics to display identified

**ACTION**: Add missing monitoring specifications.

---

### Batch-6. Performance Design

**Goal**: Ensure performance is properly considered.

**Verify performance**:

#### Volume Expectations:
- [ ] Typical volume documented
- [ ] Peak volume documented
- [ ] Growth rate estimated
- [ ] Execution time expectations

#### Optimization Strategies:
- [ ] Reading optimization documented
- [ ] Processing optimization documented
- [ ] Writing optimization documented
- [ ] Memory optimization documented

#### Parallel Processing:
- [ ] Parallelization strategy documented (if applicable)
- [ ] Partition configuration specified
- [ ] Thread pool sizing documented

#### Resource Limits:
- [ ] Memory limits specified
- [ ] Database connection limits specified
- [ ] Thread pool limits specified
- [ ] File handle limits (if file processing)

**ACTION**: Add missing performance specifications.

---

### Batch-7. Configuration Design

**Goal**: Ensure configuration is properly designed.

**Verify configuration**:

#### Environment-Specific Configuration:
- [ ] Configuration by environment documented (Dev/Test/Prod)
- [ ] Chunk sizes per environment
- [ ] Skip limits per environment
- [ ] Thread pool sizes per environment
- [ ] Timeout values per environment

#### Feature Flags:
- [ ] Enable/disable flag documented
- [ ] Parallel processing flag (if applicable)
- [ ] Dry-run flag documented

#### External Configuration:
- [ ] Properties files documented
- [ ] Environment variable overrides
- [ ] Secrets handling (connection strings, credentials)

**ACTION**: Complete configuration documentation.

---

### Batch-8. Batch Technology Compliance

**Goal**: Ensure plan follows batch technology standards.

**Verify technology choices**:

#### Framework Compliance:
- [ ] Spring Batch 5+ (or approved alternative)
- [ ] Spring Boot 3+
- [ ] Proper batch patterns used

#### Scheduling Compliance:
- [ ] Approved scheduler used (Spring Scheduler, Quartz, K8s CronJob)
- [ ] Scheduler configuration follows standards

#### Database Access Compliance:
- [ ] JdbcTemplate or Spring Data JPA used
- [ ] Connection pooling configured
- [ ] Transaction management appropriate

**ACTION**: Correct technology choices that don't align with standards.

---

## Batch-Specific Report Sections

Add these sections to the review report for batch plans:

```markdown
## Job Architecture

| Aspect | Status | Notes |
|--------|--------|-------|
| Job Flow Diagram | ✓/Missing/Corrected | [Details] |
| Steps Defined | ✓/Corrected | [Details] |
| Reader/Processor/Writer | ✓/Corrected | [Details] |
| Chunk Sizes | ✓/Corrected | [Details] |

## Scheduling Design

| Aspect | Status | Notes |
|--------|--------|-------|
| Schedule Configuration | ✓/Corrected | [Details] |
| Dependencies | ✓/Corrected/N/A | [Details] |
| SLA Requirements | ✓/Corrected | [Details] |
| Business Calendar | ✓/Corrected/N/A | [Details] |

## Data Processing

| Aspect | Status | Notes |
|--------|--------|-------|
| Data Flow Diagram | ✓/Missing/Corrected | [Details] |
| Reader Design | ✓/Corrected | [Details] |
| Processor Design | ✓/Corrected | [Details] |
| Writer Design | ✓/Corrected | [Details] |

## Error Handling and Recovery

| Aspect | Status | Notes |
|--------|--------|-------|
| Error Classification | ✓/Corrected | [Details] |
| Skip Policy | ✓/Corrected | [Details] |
| Retry Policy | ✓/Corrected | [Details] |
| Restart/Resume | ✓/Corrected | [Details] |
| Idempotency | ✓/Corrected | [Details] |

## Monitoring and Alerting

| Aspect | Status | Notes |
|--------|--------|-------|
| Job Metrics | ✓/Corrected | [Details] |
| Alerting Rules | ✓/Corrected | [Details] |
| Logging Strategy | ✓/Corrected | [Details] |

## Performance Design

| Aspect | Status | Notes |
|--------|--------|-------|
| Volume Expectations | ✓/Corrected | [Details] |
| Parallel Processing | ✓/Corrected/N/A | [Details] |
| Resource Limits | ✓/Corrected | [Details] |
```

---

## Batch-Specific Success Criteria

In addition to common success criteria:

**Job Architecture**:
- [ ] Job flow diagram present
- [ ] All steps defined with Reader/Processor/Writer
- [ ] Chunk sizes specified
- [ ] Transaction boundaries documented

**Scheduling**:
- [ ] Schedule pattern defined
- [ ] Dependencies documented
- [ ] SLA requirements specified
- [ ] Business calendar rules documented (if applicable)

**Data Processing**:
- [ ] Data flow documented
- [ ] Reader fully specified
- [ ] Processor fully specified
- [ ] Writer fully specified

**Error Handling**:
- [ ] Error classification complete
- [ ] Skip policy configured
- [ ] Retry policy configured
- [ ] Restart/resume strategy documented
- [ ] Idempotency considered

**Monitoring**:
- [ ] Job metrics defined
- [ ] Alerting rules configured
- [ ] Logging strategy documented

**Performance**:
- [ ] Volume expectations documented
- [ ] Parallel processing strategy designed (if applicable)
- [ ] Resource limits defined

---

## Batch-Specific Execution Instructions

1. **Parse the key parameter** from the command invocation

2. **Construct the directory path**: `./docs/entry-points/batch-jobs/{key}/`

3. **Read all relevant files from the directory**:
   - `implementation-plan.md` (required)
   - `functional-spec.md` (required for traceability)
   - `metadata.json` (for context)
   - `database-dependencies.json` (if exists)
   - Target architecture documents (batch-job-design, backend-architecture, data-access)

4. **Systematically work through each review check** (common + batch-specific)

5. **Make corrections directly** to implementation-plan.md as you find issues

6. **Track all findings** for the report

7. **Generate the review report** as `implementation-plan-review.md` in the same directory

8. **Provide brief summary** to user of review outcome

---

## Batch-Specific Troubleshooting

### Complex Data Dependencies

**Problem**: Job requires data from multiple sources with complex joins

**Solutions**:
1. Design multi-step job with intermediate staging
2. Use Java service layers for complex transformations (convert legacy SPs, do not create new ones)
3. Consider pre-processing step to materialize data
4. Document data flow clearly
5. Note performance implications

### Idempotency Challenges

**Problem**: Job operations are not naturally idempotent

**Solutions**:
1. Use upsert patterns (INSERT ON CONFLICT UPDATE)
2. Track processed items with correlation IDs
3. Use timestamp-based change detection
4. Design compensation mechanisms
5. Document idempotency strategy clearly

### Long-Running Job Concerns

**Problem**: Job may run longer than expected

**Solutions**:
1. Design with checkpoints for restartability
2. Consider partitioning for parallel processing
3. Implement progress monitoring
4. Set up duration alerts
5. Document timeout and SLA handling

### Recovery Complexity

**Problem**: Job failure recovery is complex

**Solutions**:
1. Design clear checkpoint strategy
2. Document manual intervention procedures
3. Create runbook for common failure scenarios
4. Test recovery procedures
5. Document in operations section

### Volume Scaling Concerns

**Problem**: Job must handle growing data volumes

**Solutions**:
1. Document volume growth expectations
2. Design for parallel processing from start
3. Identify scaling bottlenecks
4. Plan capacity upgrades
5. Consider partitioning strategy

---

**End of Command Specification**
