# Review Meta Implementation Plan

Review and validate an existing meta implementation plan to ensure completeness and correct sequencing according to the rules defined in `/create-meta-plan`. This command can fix issues directly.

---

## Usage

```
/review-meta-plan domain: <domain>
```

**Parameters**:
- `domain` (required): The domain name (e.g., "company", "tariff", "policy")

This command validates the meta plan at `./docs/plan/meta-plan.{domain}.md` against all existing technical plans on disk.

## Purpose

This command validates that a meta implementation plan:

1. **Completeness**: Includes ALL existing technical plans from disk
2. **Sequencing**: Follows proper dependency-based sequencing rules
3. **Pattern Analysis**: Correctly identifies pattern-establishing vs pattern-following plans
4. **Phase Structure**: Contains no extraction-based phases (only plan-based phases)
5. **Consistency**: Flowchart, phase descriptions, and inventory tables are consistent

**Validation Scope**: This command compares the meta plan against the actual technical plans on disk and the sequencing rules from `/create-meta-plan`.

## Validation Checklist

The command validates the following aspects:

### 1. Discovery Completeness

- [ ] All entry point types are represented (api-endpoints, ui-features, quartz-batch-jobs)
- [ ] Every technical-plan.md file on disk is in the meta plan inventory
- [ ] Executive summary shows correct breakdown by entry point type
- [ ] Plan inventory tables include all discovered plans
- [ ] No phantom plans (plans in meta plan that don't exist on disk)

### 2. Sequencing Constraints

- [ ] Every phase contains ONLY existing plans (no extracted components)
- [ ] No phase titled "Shared Infrastructure", "Common Components", or "Foundation Verification"
- [ ] No deliverables listed that aren't complete existing plans
- [ ] Dependencies reference existing plans, not extracted components (e.g., "depends on Plan 2984", not "depends on CompanyRepository")
- [ ] Shared functionality documented with "Implemented by Plan X" not "Create Component Y"
- [ ] Flowchart nodes are existing plans, not repositories/entities/services

### 3. Phase Validation

- [ ] Every phase contains at least one existing plan
- [ ] No phase has "Deliverables" list without "Plans" list
- [ ] No phase describes creating extracted components
- [ ] Phase descriptions focus on implementing plans, not creating infrastructure
- [ ] All phases have clear "Plans in this phase/tier" sections

### 4. Pattern-Based Sequencing

- [ ] Pattern-establishing plans (GET operations, creates entities) are in Tier X.1 or earlier phases
- [ ] Pattern-following plans (POST/PUT/DELETE, reuses entities) are in Tier X.2 or later phases
- [ ] CRUD order is correct: GET operations before POST/PUT/DELETE operations on same entity
- [ ] Plans that create entities come before plans that use those entities
- [ ] Dependencies are properly identified between plans

### 5. Dependency Consistency

- [ ] Dependency Matrix matches the flowchart
- [ ] Plans listed as "depends on" actually exist in earlier phases
- [ ] Plans listed as "required by" actually exist in later phases
- [ ] Parallel groups don't have hidden dependencies
- [ ] Critical path is accurately identified

### 6. Flowchart Validation

- [ ] Every plan in inventory appears in the flowchart
- [ ] Flowchart shows existing plans only (no extracted components)
- [ ] Dependency arrows match the dependency descriptions in phases
- [ ] Node styling matches phase assignments
- [ ] Legend accurately describes the color scheme

## Validation Process

### Step 1: Discover All Existing Technical Plans

Use the same discovery logic as `/create-meta-plan`:

```typescript
const plans = [
  ...glob('./docs/entry-points/**/technical-plan.md'),  // ALL entry point types
  ...glob('./docs/plan/common/**/technical-plan.md')     // Common plans if any
];
```

**Output**: Complete inventory of all technical plans on disk with:
- File path
- Plan key (extracted from directory name)
- Entry point type (api-endpoints, ui-features, quartz-batch-jobs, common)
- Plan title (extracted from markdown)

### Step 2: Read the Meta Plan

Read `./docs/plan/meta-plan.{domain}.md` and extract:

- **Executive Summary**: Total plans count, breakdown by type
- **Implementation Phases**: All phases, tiers, and the plans assigned to each
- **Flowchart**: Extract plan node IDs from the Mermaid diagram
- **Dependency Matrix**: Cross-reference table
- **Plan Inventory**: Tables listing all plans by type
- **Common Dependencies Analysis**: Which plans implement shared functionality

### Step 3: Completeness Validation

Compare discovered plans vs. plans in meta plan:

```typescript
interface ComparisonResult {
  discovered: string[];      // Plans found on disk
  documented: string[];      // Plans in meta plan
  missing: string[];         // In discovered but not documented
  phantom: string[];         // In documented but not discovered
  correctCount: boolean;     // Total count matches
  byType: {
    type: string;
    discovered: number;
    documented: number;
    matches: boolean;
  }[];
}
```

**Validation Rules**:
- `missing.length === 0` (no plans on disk are missing from meta plan)
- `phantom.length === 0` (no plans in meta plan don't exist on disk)
- `correctCount === true` (totals match)
- All `byType[].matches === true` (counts by type match)

**If Validation Fails**:
- Report missing plans with their paths and types
- Report phantom plans that should be removed
- **Fix**: Add missing plans to appropriate phases, remove phantom plans

### Step 4: Sequencing Validation

For each plan in the meta plan, validate its phase assignment:

```typescript
interface SequencingValidation {
  planKey: string;
  assignedPhase: string;      // e.g., "Phase 0 Tier 1"
  dependsOn: string[];        // Plan keys this plan depends on
  issues: SequencingIssue[];
}

interface SequencingIssue {
  type: 'dependency_violation' | 'pattern_violation' | 'crud_order_violation';
  description: string;
  suggestedFix: string;
}
```

**Validation Rules**:

1. **Dependency Rule**: If Plan A depends on Plan B, Plan B must be in an earlier phase/tier than Plan A
2. **Pattern Rule**: If Plan A is pattern-establishing (GET, creates entities) and Plan B is pattern-following (POST/PUT, reuses entities) on the same domain entity, Plan A must come before Plan B
3. **CRUD Order Rule**: For plans on the same entity: GET → POST/PUT/DELETE
4. **Tier Rule**: Within a phase, pattern-establishing plans should be in Tier X.1, pattern-following in Tier X.2

**If Validation Fails**:
- Report sequencing issues
- **Fix**: Reassign plans to correct phases/tiers

### Step 5: Phase Structure Validation

For each phase, validate:

```typescript
interface PhaseValidation {
  phaseName: string;
  issues: PhaseIssue[];
}

interface PhaseIssue {
  type: 'extraction_detected' | 'no_plans' | 'deliverables_without_plans' | 'bad_naming';
  description: string;
  suggestedFix: string;
}
```

**Validation Rules**:

1. **No Extraction**: Phase should NOT have:
   - Titles like "Shared Infrastructure", "Common Components", "Foundation Verification"
   - "Deliverables" lists with items like "CompanyRepository", "AccessControlService"
   - Descriptions about "creating common components" or "establishing infrastructure"

2. **Has Plans**: Every phase must have:
   - At least one existing plan listed
   - A "Plans in this phase/tier" section with a table or list

3. **Correct Descriptions**: Phase descriptions should:
   - Refer to implementing existing plans
   - Not describe extracting or creating components separately
   - Focus on the plans themselves, not their internal components

**If Validation Fails**:
- Report phase structure issues
- **Fix**: Rewrite phase descriptions, remove extraction language, ensure plans are listed

### Step 6: Dependency Consistency Validation

Validate that dependencies are consistent across all sections:

```typescript
interface DependencyConsistency {
  inconsistencies: DependencyInconsistency[];
}

interface DependencyInconsistency {
  planKey: string;
  section: 'flowchart' | 'phases' | 'dependency_matrix' | 'common_dependencies';
  issue: string;
  actualValue: string;
  expectedValue: string;
}
```

**Validation Rules**:

1. **Flowchart Consistency**: Dependencies shown in flowchart arrows must match "Depends On" in phase tables
2. **Matrix Consistency**: Dependency Matrix "Depends On" column must match phase descriptions
3. **Common Dependencies**: If a plan is listed as "Implemented By" in Common Dependencies, it must be in an earlier phase than "Depended On By" plans

**If Validation Fails**:
- Report inconsistencies
- **Fix**: Update the inconsistent section to match the authoritative source (phase assignments)

### Step 7: Pattern Analysis Validation

For plans at the same dependency level, validate tier assignments:

```typescript
interface PatternValidation {
  level: number;
  tier1Plans: string[];  // Pattern-establishing
  tier2Plans: string[];  // Pattern-following
  issues: PatternIssue[];
}

interface PatternIssue {
  planKey: string;
  assignedTier: string;
  suggestedTier: string;
  reason: string;
}
```

**Validation Rules**:

1. **GET Operations**: Plans with GET/read operations should typically be in Tier X.1 (pattern-establishing)
2. **POST/PUT/DELETE Operations**: Plans with mutations should typically be in Tier X.2 (pattern-following)
3. **Entity Creation**: Plans that create entities should be in Tier X.1
4. **Entity Reuse**: Plans that reuse entities should be in Tier X.2

**If Validation Fails**:
- Report tier assignment issues
- **Fix**: Reassign plans to correct tiers within their level

### Step 8: Generate Validation Report

Create a comprehensive report:

```markdown
# Meta Plan Validation Report: {domain}

**Generated**: {timestamp}
**Meta Plan**: ./docs/plan/meta-plan.{domain}.md
**Status**: {PASS | FAIL}

## Summary

- **Total Plans Discovered**: {count}
- **Total Plans Documented**: {count}
- **Missing Plans**: {count}
- **Phantom Plans**: {count}
- **Sequencing Issues**: {count}
- **Phase Structure Issues**: {count}
- **Dependency Inconsistencies**: {count}
- **Pattern Issues**: {count}

## Completeness Validation {PASS/FAIL}

### Missing Plans (not in meta plan)
{list of missing plans with paths}

### Phantom Plans (in meta plan but not on disk)
{list of phantom plans}

### Entry Point Type Breakdown
| Type | Discovered | Documented | Status |
|------|------------|------------|--------|
| ... | ... | ... | ✅/❌ |

## Sequencing Validation {PASS/FAIL}

### Dependency Violations
{list of plans assigned to wrong phases}

### Pattern Violations
{list of plans in wrong tiers}

### CRUD Order Violations
{list of plans not following GET → POST/PUT/DELETE order}

## Phase Structure Validation {PASS/FAIL}

### Extraction Detected
{list of phases with extraction language}

### Phases Without Plans
{list of phases with no plans}

### Bad Phase Names
{list of phases with problematic names}

## Dependency Consistency {PASS/FAIL}

### Flowchart Inconsistencies
{list of mismatches between flowchart and phases}

### Matrix Inconsistencies
{list of mismatches in dependency matrix}

## Fixes Applied

{list of all fixes that were applied to the meta plan}

## Recommendations

{any recommendations that require manual review}
```

### Step 9: Apply Fixes

If `--fix` is implied (or always), automatically fix issues:

**Fixable Issues**:
1. **Missing Plans**: Add to appropriate phase based on dependency analysis
2. **Phantom Plans**: Remove from meta plan
3. **Sequencing Issues**: Move plans to correct phases/tiers
4. **Phase Structure**: Rewrite phase descriptions, remove extraction language
5. **Dependency Inconsistencies**: Update flowchart, matrix, and phase tables to be consistent
6. **Incorrect Counts**: Update executive summary with correct totals

**Non-Fixable Issues** (require manual review):
1. Complex circular dependencies
2. Ambiguous pattern classification (neither clearly establishing nor following)
3. Missing dependency information in technical plans

### Step 10: Write Updated Meta Plan

If fixes were applied:
1. Update the meta plan file with corrections
2. Preserve the structure and formatting
3. Update the "Generated" timestamp
4. Add a note at the bottom: "Last validated and updated: {timestamp}"

## Task Subagent Usage (Optional)

This command can leverage Task subagents:

**When to Use Task Subagents**:

1. **Discovery Phase** (Step 1):
   - Use `Explore` subagent to discover all technical plans
   - Benefit: Thorough discovery across all entry point types

2. **Plan Reading** (Step 1):
   - If more than 5 discovered plans, use parallel `general-purpose` subagents
   - Each reads a subset and extracts metadata
   - Benefit: Faster parallel processing

**When NOT to Use Task Subagents**:
- Validation logic (Steps 3-7) - requires holistic view
- Report generation (Step 8) - requires integrated analysis
- Applying fixes (Step 9) - requires careful coordination
- Writing updated meta plan (Step 10) - requires coherent narrative

## Output

The command produces:

1. **Validation Report** (printed to console or written to file):
   ```
   ./docs/plan/meta-plan.{domain}.validation-report.md
   ```

2. **Updated Meta Plan** (if fixes applied):
   ```
   ./docs/plan/meta-plan.{domain}.md
   ```

3. **Console Summary**:
   ```
   ✅ Meta Plan Validation: PASS
   - All 27 plans accounted for
   - Sequencing correct
   - No extraction detected
   - 0 fixes applied

   OR

   ❌ Meta Plan Validation: FAIL
   - 3 missing plans added to Phase 2
   - 1 phantom plan removed
   - 2 plans moved to correct phases
   - Phase 0 description rewritten to remove extraction
   - 6 fixes applied

   📄 Updated meta plan written to: ./docs/plan/meta-plan.company.md
   📋 Validation report: ./docs/plan/meta-plan.company.validation-report.md
   ```

## Execution Instructions

### Step-by-Step Execution

1. **Parse Domain Parameter**:
   ```typescript
   const domain = extractParameter('domain');
   const metaPlanPath = `./docs/plan/meta-plan.${domain}.md`;
   ```

2. **Discover All Technical Plans** (same as `/create-meta-plan`):
   ```typescript
   const discoveredPlans = discoverTechnicalPlans();
   // Returns: { path, key, type, title }[]
   ```

3. **Read and Parse Meta Plan**:
   ```typescript
   const metaPlan = parseMetaPlan(metaPlanPath);
   // Extract: phases, flowchart, inventory, dependencies
   ```

4. **Validate Completeness**:
   ```typescript
   const completeness = validateCompleteness(discoveredPlans, metaPlan);
   ```

5. **Validate Sequencing**:
   ```typescript
   const sequencing = validateSequencing(metaPlan, discoveredPlans);
   ```

6. **Validate Phase Structure**:
   ```typescript
   const phases = validatePhaseStructure(metaPlan);
   ```

7. **Validate Dependency Consistency**:
   ```typescript
   const consistency = validateDependencyConsistency(metaPlan);
   ```

8. **Generate Report**:
   ```typescript
   const report = generateValidationReport({
     completeness,
     sequencing,
     phases,
     consistency
   });
   ```

9. **Apply Fixes**:
   ```typescript
   const fixes = applyFixes(metaPlan, {
     completeness,
     sequencing,
     phases,
     consistency
   });
   ```

10. **Write Outputs**:
    ```typescript
    writeMetaPlan(metaPlanPath, metaPlan);
    writeReport(`${metaPlanPath}.validation-report.md`, report);
    printSummary(report, fixes);
    ```

## Quality Criteria

The validation is successful if:

**Completeness**:
- [ ] All discovered plans are in the meta plan
- [ ] No phantom plans in the meta plan
- [ ] Entry point type counts match

**Sequencing**:
- [ ] All dependencies are satisfied (dependent plans in later phases)
- [ ] Pattern-establishing plans before pattern-following plans
- [ ] CRUD order correct (GET before POST/PUT/DELETE)

**Phase Structure**:
- [ ] No extraction-based phases
- [ ] Every phase has at least one plan
- [ ] Phase descriptions focus on implementing plans

**Consistency**:
- [ ] Flowchart matches phase assignments
- [ ] Dependency Matrix matches phase descriptions
- [ ] Common Dependencies section is accurate

**Fixability**:
- [ ] All identified issues were automatically fixed
- [ ] Or, issues requiring manual review are clearly reported

## Edge Cases

### Meta Plan Does Not Exist

If `./docs/plan/meta-plan.{domain}.md` does not exist:
- Report: "Meta plan not found. Run `/create-meta-plan domain: {domain}` first."
- Do NOT create a new meta plan (that's the job of `/create-meta-plan`)

### No Technical Plans Found

If discovery finds 0 technical plans:
- Report: "No technical plans found for domain '{domain}'. Check that technical plans exist."
- If meta plan exists with plans, report all as phantom plans

### Meta Plan Has Extraction Phases

If "Phase 0: Shared Infrastructure" or similar is detected:
- Report: "CRITICAL: Meta plan contains extraction-based phases (violates constraints)"
- Attempt to fix by:
  1. Identifying which existing plan implements the "extracted" functionality
  2. Rewriting the phase to reference that plan instead
  3. If cannot determine, report for manual review

### Circular Dependencies

If circular dependencies are detected:
- Report: "Circular dependency detected: Plan A → Plan B → Plan A"
- Do NOT attempt automatic fix
- Recommend manual review and suggest breaking strategies from `/create-meta-plan`

### Ambiguous Pattern Classification

If a plan is unclear (neither clearly establishing nor following):
- Use heuristics from `/create-meta-plan`:
  - HTTP method (GET = establishing, POST/PUT/DELETE = following)
  - Technical plan keywords ("implements", "creates" = establishing; "uses", "requires" = following)
  - Domain entity analysis (first operation on entity = establishing)
- If still ambiguous, report for manual review

## Use Cases

### Pre-Implementation Validation

Run this command after creating a meta plan to ensure it's correct before beginning implementation.

### Post-Modification Validation

If technical plans are added or removed, run this command to update the meta plan.

### Quality Assurance

Run periodically to ensure meta plan remains accurate as technical plans evolve.

### Migration Validation

When migrating from old meta plan format to new format, validate the migrated plan is correct.

---

**End of Command Specification**
