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
            --file-pattern "*implementation-plan.md"
            --contains '## Executive Summary'
            --contains '## JIT Research Findings'
            --contains '## Code Reusability Analysis'
            --contains '## Architecture Overview'
            --contains '## Testing Strategy'
            --contains '## Trigger Metadata'
            --contains '## TriggerEntity Registration'
            --contains '## Auto-Publish Configuration'
            --contains '## Handler Design'
            --contains '## Column Mapping'
            --contains '## Circular Publishing'
            --contains '## Parallelization Strategy'
  Stop:
    - hooks:
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_new_file.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*implementation-plan.md"
        - type: command
          command: >-
            uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py
            --log
            --directory docs/entry-points --extension .md --file-pattern "*implementation-plan.md"
            --contains '## Executive Summary'
            --contains '## JIT Research Findings'
            --contains '## Code Reusability Analysis'
            --contains '## Architecture Overview'
            --contains '## Testing Strategy'
            --contains '## Trigger Metadata'
            --contains '## TriggerEntity Registration'
            --contains '## Auto-Publish Configuration'
            --contains '## Handler Design'
            --contains '## Column Mapping'
            --contains '## Circular Publishing'
            --contains '## Parallelization Strategy'
---

# Plan Trigger

Create a comprehensive technical plan for converting a legacy database trigger to the **ServiceBus handler pattern**, incorporating JIT research findings and analyzing existing code patterns for reusability.

## Common Foundation

@plan-common.md

---

## Architect Agents

**Primary:** `trigger-architect` - Use for trigger modernization strategy

**Cross-domain consultation:**
- `passage-api-architect` - For service layer replacement design
- `passage-db-architect` - For constraint-based alternatives

See @plan-common.md for full architect agent documentation.

---

## Trigger-Specific Context

This specification type is for **Database Triggers** being converted to the **ServiceBus handler pattern**. All legacy triggers follow the same modernization strategy: Hibernate auto-publishes entity changes to Azure Service Bus, and handler classes consume those events to replicate the trigger's logic in the application layer.

There are two handler categories:
- **Regular handlers** — implement `TriggerEventHandler<Map<String, Object>>` directly (business logic, sync, validation, cascades)
- **History handlers** — extend `AbstractHistoryHandler` (audit trail / history tracking)

The trigger's entry point key prefix determines the category:
- `h-triggers-*` → History handler (AbstractHistoryHandler pattern)
- `triggers-*` → Regular handler (TriggerEventHandler pattern)

## Input

You will receive:
- **entry_point_folder_path**: Path to the entry point folder (e.g., `docs/entry-points/database-triggers/triggers-trd-company-date-eff`)

Example invocation:
```
/plan-trigger entry_point_folder_path: docs/entry-points/database-triggers/triggers-trd-company-date-eff
```

---

## Mandatory Context to Load

Before planning, you MUST read the following files:

### Pattern Files (source of truth)
- `docs/target-architecture/patterns/trigger-patterns/servicebus-send-event.v1.md`
- `docs/target-architecture/patterns/trigger-patterns/servicebus-receive-event.v1.md`

### Guide Docs
- `docs/target-architecture/servicebus-send.md`
- `docs/target-architecture/servicebus-receive.md` — especially the "Implementation Checklist" and "Handler Categories" sections

### Infrastructure (check current state)
- `passage-api/src/main/java/com/williams/api/common/trigger/TriggerEntity.java` — check existing registrations
- `passage-api/src/main/java/com/williams/api/common/trigger/TriggerEventHandler.java` — handler interface
- `passage-api/src/main/java/com/williams/api/common/trigger/TriggerHandler.java` — annotation
- `passage-api/src/main/java/com/williams/api/common/trigger/TriggerPublisher.java` — publisher annotation
- `passage-api/src/main/java/com/williams/api/common/trigger/AbstractHistoryHandler.java` — history base class

### Reference Implementations
- `passage-api/src/main/java/com/williams/api/company/handler/CoAnlysCmContactSyncHandler.java` — reference regular handler
- `passage-api/src/main/java/com/williams/api/company/handler/CmContactHistHandler.java` — reference history handler

### Additional Context
- Read the legacy trigger source file from the location in `metadata.json` (typically at `./legacy/database/TRIGGERS/{TRIGGER_NAME}.tri`)
- Read `docs/target-architecture/domain-registry.json` — for handler package placement

---

## Trigger Analysis

### Trigger Naming Convention Analysis

Legacy triggers follow naming conventions that indicate their purpose:

| Prefix | Event | Description |
|--------|-------|-------------|
| `TRI_` | INSERT | Fires after INSERT |
| `TRU_` | UPDATE | Fires after UPDATE |
| `TRD_` | DELETE | Fires after DELETE |
| `TRIU_` | INSERT, UPDATE | Fires after INSERT or UPDATE |
| `TRIUD_` | INSERT, UPDATE, DELETE | Fires after any DML operation |
| `TRID_` | INSERT, DELETE | Fires after INSERT or DELETE |

### Find Existing Implementations

Search for existing modernized trigger handlers:

```bash
# Find existing trigger handlers
grep -r "@TriggerHandler" passage-api/src --include="*.java" -l | head -10

# Find TriggerEntity registrations
grep -r "TriggerEntity\." passage-api/src --include="*.java" | head -20

# Find history handlers
grep -r "AbstractHistoryHandler" passage-api/src --include="*.java" -l | head -10
```

**Reusable Components:** Existing handlers, `AbstractHistoryHandler` base class, type conversion utilities (`toInteger()`, `toLocalDateTime()`, etc.)

---

## Technical Plan Output Sections

The `implementation-plan.md` must include these sections:

```markdown
# Technical Plan: [Trigger Name]

## Executive Summary
[Brief overview: what the trigger does and the conversion approach using the ServiceBus handler pattern]

## JIT Research Findings

### Key Insights from Research
[Summarize findings from research-summary.json]

### Legacy Trigger Analysis
[Analysis of the legacy trigger behavior, SQL logic, tables affected]

## Trigger Metadata

| Property | Value |
|----------|-------|
| **Trigger Name** | [dbo.TRIGGER_NAME] |
| **Target Table** | [dbo.TABLE_NAME] |
| **Trigger Events** | INSERT / UPDATE / DELETE |
| **Category** | [Regular / History] |
| **Handler Base Class** | [TriggerEventHandler / AbstractHistoryHandler] |

## Code Reusability Analysis

### Direct Reuse Components
| Component | Location | Usage |
|-----------|----------|-------|
| [Component] | [Path] | [How it will be used] |

### New Components Required
| Component | Type | Rationale |
|-----------|------|-----------|
| [Component] | [Type] | [Why needed] |

## TriggerEntity Registration

| Field | Value |
|-------|-------|
| **Entity Key** | [Must match @Table(name) exactly, e.g., "CO_ANLYS"] |
| **Legacy Triggers** | [List: "tri_co_anlys", "tru_co_anlys"] |
| **Description** | [What this entity represents] |
| **Already Registered** | [Yes/No — check TriggerEntity.java] |

## Auto-Publish Configuration

- **Source entity JPA class**: [Path to the entity class]
- **@Table(name)**: [Verify it matches the TriggerEntity key]
- **Auto-publish behavior**: @TriggerHandler annotation on the handler is sufficient — no @TriggerPublisher needed on domain services (but can be added for documentation)

## Handler Design

| Field | Value |
|-------|-------|
| **Handler Class** | [e.g., CmContactHistHandler] |
| **Package** | [Derived from source entity's package, e.g., com.williams.api.company.handler] |
| **Base Class** | [AbstractHistoryHandler<HistEntity, Integer> or TriggerEventHandler<Map<String, Object>>] |
| **Operations** | [CREATE, UPDATE, DELETE — from trigger events] |
| **@TriggerHandler entity** | [TriggerEntity.XXX] |

### For History Handlers:
- **History Table**: [dbo.TABLE_HIST]
- **mapToHistory()**: Maps entity state snapshot to history entity
- **hasTrackedColumnChange()**: [Yes/No — does legacy trigger have WHERE EXISTS diff check?]
- **getRecordIdentifier()**: [Which field to use for logging, e.g., "contactId"]

### For Regular Handlers:
- **Business Logic**: [What the handle() method needs to do]
- **Required Dependencies**: [Repositories, services to inject]

## Column Mapping

| SQL Column | Java Property | Type | Conversion |
|------------|--------------|------|------------|
| [COLUMN_NAME] | [propertyName] | [String/Integer/LocalDateTime/etc.] | [see available conversions below] |

**IMPORTANT**: Map keys in the ServiceBus payload are **camelCase Java property names** (from @Column mapping), NOT SQL column names.

**Available type conversion utilities** (from `AbstractHistoryHandler`):
- `toString(Object)` — null-safe String conversion
- `toInteger(Object)` — handles Number subtypes via `intValue()`
- `toLong(Object)` — handles Number subtypes via `longValue()`
- `toDouble(Object)` — handles Number subtypes via `doubleValue()`
- `toShort(Object)` — handles Number subtypes via `shortValue()`
- `toByte(Object)` — handles Number subtypes via `byteValue()`
- `toBoolean(Object)` — null-safe Boolean conversion
- `toLocalDateTime(Object)` — parses ISO-8601 strings via `LocalDateTime.parse()`
- Direct cast — for `String`, `BigDecimal`, or when the type is guaranteed

## Circular Publishing Analysis

- **Handler writes to**: [List tables the handler writes to]
- **Are any in TriggerEntity enum?**: [Yes/No]
- **Chain terminates?**: [Yes — explain / No — BLOCKED]

## Architecture Overview
[How the handler fits into the overall ServiceBus trigger architecture]

## Testing Strategy

### Unit Tests (Mockito-based)
| Test Case | Scenario | Expected Outcome |
|-----------|----------|-----------------|
| [test_handle_create] | [CREATE event with valid data] | [Handler processes correctly] |
| [test_handle_update_with_changes] | [UPDATE event with tracked column changes] | [History row written / sync performed] |
| [test_handle_update_no_changes] | [UPDATE event with no tracked changes] | [Skipped — no action] |
| [test_handle_delete] | [DELETE event] | [Handler processes correctly] |

## Parallelization Strategy
[See template below]
```

---

## Implementation Constraints

Embed these constraints in the plan — they are critical for correct handler implementation:

- **Entity key must match `@Table(name)` exactly** — `HibernateEntityChangeListener.resolveTableName()` reads `@Table(name)` and compares with `equalsIgnoreCase()`
- **Payload uses camelCase Java property names**, NOT SQL column names — e.g., `data.get("anlysFunc")` not `data.get("ANLYS_FUNC")`
- **Temporal types arrive as ISO-8601 strings** — use `LocalDateTime.parse()` to convert
- **Number types are polymorphic** — use `Number.intValue()` / `.longValue()` for safe conversion (or `AbstractHistoryHandler.toInteger()`)
- **UPDATE diff check** — replicate legacy WHERE EXISTS with `Objects.equals()` on each tracked field in `hasTrackedColumnChange()`
- **`transaction_user`** — use `LAST_MOD_USER_ID` from entity data, NOT `suser_name()` (no HTTP context on consumer thread)
- **`@TriggerHandler` alone is sufficient** for auto-publish — no need for `@TriggerPublisher` per handler
- **`@Modifying` JPQL bypasses Hibernate listener** — if the handler uses bulk updates, convert to load-modify-save through JPA lifecycle

---

## Domain Placement Rules

Before deciding where to place new Java classes, read the domain registry at `docs/target-architecture/domain-registry.json`.

**All new Java classes in `passage-api` MUST be placed under one of the registered domain packages in `com.williams.api.{domain}/`.** Do NOT create new top-level packages under `com.williams.api/` that are not in the registry.

**For trigger handlers**: the domain is derived from the source entity's package. If the entity is in `com.williams.api.company`, the handler goes in `com.williams.api.company.handler`.

Valid domain packages and their purposes are defined in the registry's `domains` array. The `allowedNonDomainPackages` array lists technical packages (like `common`) that are also valid.

**Sub-domains:** Some domains have valid sub-packages (e.g., `security.contactmanager`). These are listed in the `subDomains` array of each domain entry.

---

## Parallelization Strategy Section

**CRITICAL**: Every trigger implementation plan must include a `## Parallelization Strategy` section that documents:

1. **Task Dependencies** - Which tasks depend on others within this trigger conversion
2. **Parallel Execution** - Which tasks can run concurrently during implementation
3. **Sub-agent Dispatch Plan** - How sub-agents should be launched for maximum parallelization

### Template for Trigger Implementation Plans

Include this section in every `implementation-plan.md`:

```markdown
## Parallelization Strategy

### Task Dependencies

| Task Group | Depends On | Blocks |
|------------|------------|--------|
| TriggerEntity Registration | None | Handler Implementation |
| Handler Implementation | TriggerEntity Registration | Unit Tests |
| Unit Tests | Handler Implementation | None (parallel with circular publishing check) |
| Circular Publishing Check | Handler Implementation | None (parallel with unit tests) |

### Parallel Execution Opportunities

**Can run in parallel (same wave):**
- Unit tests and circular publishing verification
- TriggerEntity registration and reading reference implementations

**Must be sequential:**
- TriggerEntity Registration → Handler Implementation → Unit Tests

### Sub-Agent Dispatch Plan

| Wave | Sub-Agents | Tasks |
|------|------------|-------|
| 1 | `trigger-developer` | TriggerEntity registration (if needed) |
| 2 | `trigger-developer` | Handler class implementation |
| 3 | `trigger-developer` x2 | Unit tests, Circular publishing check (parallel) |
```

### Generating the Strategy

When creating the implementation plan:

1. **Identify all components** that need to be built (TriggerEntity entry, handler, tests)
2. **Map dependencies** between components
3. **Group independent tasks** that can run in parallel
4. **Document wave dispatch** showing which sub-agents handle which tasks
