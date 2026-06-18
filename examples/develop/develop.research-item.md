# Research Item

Perform JIT (Just-In-Time) research phase for a single implementation item.

**This command gathers context and analyzes the current state before planning and implementing an item.**

## Input Parameters

You will receive:
- **entry_point_folder_path**: Path to the entry point analysis folder
- **item_key**: The item's unique key
- **item_type**: Type of entry point (api-endpoint, ui-feature, batch-job, trigger)
- **pattern_registry_path** (optional): Path to pattern registry (defaults to `docs/patterns/`)

Example invocation:
```
/develop.research-item entry_point_folder_path: docs/entry-points/api-endpoints/get-company-list item_key: get-company-list item_type: api-endpoint
```

## Purpose

The research phase ensures we understand:
1. What has already been analyzed (Discover outputs)
2. What code currently exists (implementation state)
3. What patterns are available and applicable
4. What dependencies and blockers exist

This information feeds into the planning phase for informed decision-making.

## Sub-Agent Strategy

Research tracks are independent and **SHOULD be launched as parallel sub-agents** when multiple areas need investigation. This reduces total research time by running independent investigations concurrently.

> **Agent Invocation**: Agents in `.claude/agents/` are registered Claude Code agents with specific tools.
> Invoke them by name using the Task tool: `Task(subagent_type="target-api-searcher", prompt="Find company endpoints")`

### Research Agents

**Legacy-Focused (understand what exists in legacy):**

| Agent | Purpose | Use For |
|-------|---------|---------|
| `legacy-documentation-searcher` | Search docs/ for entry point analysis, entity docs | Step 1: Reading existing analysis |
| `legacy-code-searcher` | Search legacy/ for implementations | Deep legacy code investigation |
| `legacy-architect` | C4 diagrams and architectural context | Understanding system boundaries |
| `java-db-query-analyzer` | Map database operations from Java | Database dependency analysis |
| `symbol-body-extractor` | Extract symbol bodies via Serena MCP | Specific code extraction |

**Target-Focused (understand what exists in target):**

| Agent | Purpose | Use For |
|-------|---------|---------|
| `target-api-searcher` | Search passage-api/ for Spring Boot code | Step 2: API code state |
| `target-ui-searcher` | Search passage-ui/ for Angular code | Step 2: UI code state |
| `target-db-searcher` | Search passage-db/ DDL scripts | Schema verification |
| `pattern-registry-researcher` | Search all 4 pattern registries | Step 3: Pattern identification |

### Architect Agents (for design questions)

When research reveals complex design decisions, consult domain-specific architects:

| Agent | Domain | When to Use |
|-------|--------|-------------|
| `passage-api-architect` | API | Controller/service design, DTO contracts |
| `passage-ui-architect` | UI | Component architecture, Kendo configs |
| `passage-db-architect` | Database | Schema design, migration planning |
| `batch-architect` | Batch | Job structure, step design |
| `trigger-architect` | Trigger | Modernization strategy |

### Parallelization by Item Type

| Item Type | Parallel Research Agents |
|-----------|-------------------------|
| **api-endpoint** | `legacy-documentation-searcher`, `target-api-searcher`, `pattern-registry-researcher` |
| **ui-feature** | `legacy-documentation-searcher`, `target-ui-searcher`, `pattern-registry-researcher` |
| **batch-job** | `legacy-documentation-searcher`, `target-api-searcher`, `pattern-registry-researcher` |
| **trigger** | `legacy-documentation-searcher`, `target-api-searcher`, `target-db-searcher` |

Launch the appropriate agents in parallel (single message, multiple Task calls), then synthesize results in Steps 4-6.

## Process

### Step 1: Read Existing Analysis

From the entry point folder, read:
- `functional-spec.md` - What the item should do
- `implementation-plan.md` - Implementation approach (if exists from previous iteration)
- `database-dependencies.json` - Database objects used
- `api-usage.json` (for UI features) - APIs this UI depends on
- `metadata.json` - Entry point metadata
- `call-tree.json` - Legacy code call tree

Extract key information:
- Business requirements
- Technical requirements
- Database tables and stored procedures
- API dependencies
- Legacy behavior details

**Stored Procedure Detection**: When `database-dependencies.json` contains entries with `"type": "stored-procedure"`, extract the SP names and note them explicitly. These will drive the SP conversion strategy during planning.

### Step 2: Check Current Code State

Examine the target project to understand what's already implemented:

**For API Endpoints:**
- Check `passage-api/src/main/java/` for existing controllers/services
- Look for entities related to database dependencies
- Check if endpoint already exists

**For UI Features:**
- Check `passage-ui/src/app/` for existing components
- Look for related services and models
- Check if component already exists

**Search for:**
- Files with matching names or patterns
- Imports of related entities
- Existing tests

### Security Research (when applicable)

When researching features that involve permissions or authorization:
- Cross-reference legacy source code for actual API-level permission checks:
  - Check the service class for `hasPermission()` calls
  - Check `menu_endpoint` table for endpoint-level security configuration
  - Check the legacy controller/REST service for `checkSecurity()` calls
- Distinguish between:
  - **UI menu visibility** (controlled by `menu_func` + permission tables)
  - **API-level enforcement** (controlled by `menu_endpoint` — likely empty/unused)
- Document findings in research output: "Legacy API-level enforcement: Yes/No"
- Read `docs/target-architecture/security-architecture.md` for context

### Step 3: Identify Available Patterns

Check the pattern registry for applicable patterns:
- Read `docs/patterns/ui-patterns/registry.json`
- Read `docs/patterns/api-patterns/registry.json`
- Read `docs/patterns/batch-patterns/registry.json`
- Read `docs/patterns/trigger-patterns/registry.json`

Match patterns to requirements:
- Which patterns fit this item's needs?
- What versions are available?
- Are reference implementations available?

**Stored Procedure Conversion Pattern**: When stored procedures were detected in Step 1, automatically include the `"Stored Procedure Conversion Pattern"` (v9) from `docs/target-architecture/patterns/api-patterns/stored-procedure-conversion.v9.md` in the applicable patterns. Also **search `passage-api/src` for existing conversions** of each detected SP — another endpoint may have already converted it into a Java service class. Record which SPs are already converted and which still need conversion.

### Step 4: Analyze Dependencies

Check if dependencies are satisfied:
- For UI features: Are required APIs implemented?
- For APIs: Are required entities available?
- Are database migrations in place?

Identify blockers:
- Missing dependencies
- Conflicting implementations
- Version mismatches

### Step 5: Check Pattern Usage Files

If page planning has run, check pattern usage files:
- `docs/plan/page-plan.{domain}.{page-key}.ui-patterns.json`
- `docs/plan/page-plan.{domain}.{page-key}.api-patterns.json`

These files specify which patterns should be used for this item.

### Step 6: Assess Implementation Needs

Based on research, identify:
- Files to create
- Files to modify
- Patterns to apply
- Configuration needed
- Tests to write

## Output Format

Write research summary to `{entry_point_folder_path}/research-summary.json`:

```json
{
  "itemKey": "get-company-list",
  "itemType": "api-endpoint",
  "researchedAt": "2024-01-15T10:00:00Z",
  "existingAnalysis": {
    "hasFunc tionalSpec": true,
    "hasTechnicalPlan": true,
    "hasDatabaseDeps": true,
    "hasCallTree": true,
    "summary": "API to retrieve paginated list of companies with filtering"
  },
  "currentCodeState": {
    "alreadyImplemented": false,
    "partiallyImplemented": false,
    "relatedFilesFound": [
      "passage-api/src/main/java/com/williams/nwp/entity/Company.java"
    ],
    "existingTests": [],
    "conflicts": []
  },
  "dependencies": {
    "entitiesAvailable": ["Company", "CompanyAddress"],
    "entitiesMissing": [],
    "apisRequired": [],
    "apisAvailable": [],
    "databaseReady": true
  },
  "patterns": {
    "applicable": [
      {
        "name": "Paginated List API",
        "type": "api",
        "version": "1.0.0",
        "registryPath": "docs/patterns/api-patterns/paginated-list-api/"
      }
    ],
    "recommended": ["Paginated List API"],
    "fromPagePlan": ["Paginated List API v1.0.0"]
  },
  "implementationNeeds": {
    "filesToCreate": [
      "passage-api/src/main/java/com/williams/nwp/controller/CompanyController.java",
      "passage-api/src/main/java/com/williams/nwp/service/CompanyService.java",
      "passage-api/src/main/java/com/williams/nwp/dto/CompanyListRequest.java",
      "passage-api/src/main/java/com/williams/nwp/dto/CompanyListResponse.java"
    ],
    "filesToModify": [],
    "patternsToApply": ["Paginated List API"],
    "configurationNeeded": [
      "Add endpoint mapping to SecurityConfig"
    ],
    "testsToWrite": [
      "CompanyControllerTest",
      "CompanyServiceTest"
    ]
  },
  "storedProcedures": {
    "detected": ["dbo.sp_name_1", "dbo.sp_name_2"],
    "alreadyConverted": [
      {
        "spName": "dbo.sp_name_1",
        "serviceClass": "passage-api/src/main/java/com/williams/nwp/service/SpName1Service.java"
      }
    ],
    "needsConversion": ["dbo.sp_name_2"],
    "conversionGuideApplies": true,
    "conversionGuideRef": "docs/target-architecture/patterns/api-patterns/stored-procedure-conversion.v9.md"
  },
  "potentialIssues": [],
  "recommendations": [
    "Use existing Company entity - no modifications needed",
    "Follow Paginated List API pattern for consistency",
    "Add sorting by CO_COMN_NAME as default"
  ],
  "readyForPlanning": true
}
```

## Console Output

```
Researching item: get-company-list (api-endpoint)
  Entry point: docs/entry-points/api-endpoints/get-company-list/

Reading existing analysis...
  ✓ Functional spec found
  ✓ Technical plan found
  ✓ Database dependencies found
  ✓ Call tree found

Checking current code state...
  Related files found: 1
  - passage-api/src/main/java/com/williams/nwp/entity/Company.java
  Not yet implemented

Checking dependencies...
  ✓ Entities available: Company, CompanyAddress
  ✓ Database ready

Identifying patterns...
  Applicable patterns: 1
  - Paginated List API (v1.0.0)
  Recommended: Paginated List API

Assessing implementation needs...
  Files to create: 4
  Files to modify: 0
  Patterns to apply: 1
  Tests to write: 2

Research complete!
  Ready for planning: Yes
  Summary saved to: docs/entry-points/api-endpoints/get-company-list/research-summary.json
```

## Error Handling

**Missing Functional Spec:**
```
Warning: Functional spec not found
  Expected: docs/entry-points/api-endpoints/get-company-list/functional-spec.md
  Suggestion: Run Discover workflow for this entry point
```

**Missing Dependencies:**
```
Warning: Required entities not found
  Missing: CompanyContact
  This may block implementation
  Suggestion: Run entity generation first
```

**Already Implemented:**
```
Info: Item appears to be already implemented
  Found: passage-api/src/main/java/com/williams/nwp/controller/CompanyController.java
  Review existing implementation before proceeding
```

## Success Criteria

- [ ] All available analysis files read
- [ ] Current code state assessed
- [ ] Dependencies checked
- [ ] Applicable patterns identified
- [ ] Implementation needs listed
- [ ] Potential issues flagged
- [ ] Research summary written

## Notes

- This command is the first step in the JIT implementation cycle
- Output feeds directly into type-specific plan commands (`/plan-api-endpoint`, `/plan-ui-feature`, `/plan-batch-job`, `/plan-trigger`)
- Research is lightweight - gather info, don't make changes
- Focus on identifying blockers early
- Pattern recommendations come from registry and page plan
