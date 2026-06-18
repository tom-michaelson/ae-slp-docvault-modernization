# Extract Linear Implementation Plan

Extract a linear, flat implementation order from `./docs/plan/meta-plan.{domain}.md` and output as a simple JSON array at `./docs/plan/meta-plan.linear.{domain}.json`.

## Usage

```
/extract-meta-plan-linear domain: <domain>
```

**Parameters**:
- `domain` (required): The domain name (e.g., "company", "tariff", "policy")

## Purpose

This command extracts the implementation plan into a **simple, linear JSON array** for easy processing and tracking. Each item represents one thing to be implemented in dependency order.

## Input

```
./docs/plan/meta-plan.{domain}.md
```

The markdown meta plan created by `/create-meta-plan domain: <domain>`.

## Output

```
./docs/plan/meta-plan.linear.{domain}.json
```

A simple JSON array with one item per implementation unit.

## JSON Structure

The output is a **flat JSON array** where each object has:

```typescript
[
  {
    "sequence": number,              // Sequential number (1, 2, 3, ...) for deterministic sorting
    "key": string,                   // The plan key from directory structure (e.g., "2001-tariff-calculation-service")
    "type": string,                  // "api-endpoint" | "ui-feature" | "quartz-batch-job" | "common"
    "functionalSpecPath": string,    // Relative path to functional-spec.md (or functional-description.md)
    "technicalPlanPath": string      // Relative path to technical-plan.md
  },
  ...
]
```

### Example

```json
[
  {
    "sequence": 1,
    "key": "common-database-schema",
    "type": "common",
    "functionalSpecPath": "./docs/entry-points/common/common-database-schema/functional-spec.md",
    "technicalPlanPath": "./docs/entry-points/common/common-database-schema/technical-plan.md"
  },
  {
    "sequence": 2,
    "key": "2001-tariff-rates-api",
    "type": "api-endpoint",
    "functionalSpecPath": "./docs/entry-points/api-endpoints/2001-tariff-rates-api/functional-spec.md",
    "technicalPlanPath": "./docs/entry-points/api-endpoints/2001-tariff-rates-api/technical-plan.md"
  },
  {
    "sequence": 3,
    "key": "3001-tariff-calculator-ui",
    "type": "ui-feature",
    "functionalSpecPath": "./docs/entry-points/ui-features/3001-tariff-calculator-ui/functional-description.md",
    "technicalPlanPath": "./docs/entry-points/ui-features/3001-tariff-calculator-ui/technical-plan.md"
  }
]
```

## Extraction Process

### Step 1: Parse Meta Plan

Read `./docs/plan/meta-plan.{domain}.md` and extract the implementation order.

**Primary source for plan data**: The **Plan Inventory** section contains authoritative plan metadata:
- The **Key** column contains the exact directory name (e.g., `2976-spring-companymaintenanceservice-getcompanylist`)
- The section header indicates the plan type (`api-endpoint`, `ui-feature`, `quartz-batch-job`, `common`)

**Sources for implementation order**:
1. **Implementation Phases** section - Contains tables with plans listed in dependency order
2. **Execution Order** section - If present, contains the sequential order
3. **Plan Inventory** section - Lists all plans by type (and tier within phase)

The plans should be extracted in **dependency order** - items that have no dependencies first, then items that depend on them, etc.

### Step 2: Identify Plan Type and Paths

For each plan, determine:

1. **Type**: From the Plan Inventory section header:
   - `api-endpoint` - From "### API Endpoints" section
   - `ui-feature` - From "### UI Features" section
   - `quartz-batch-job` - From "### Quartz Batch Jobs" section
   - `common` - From "### Common Functionality" section

2. **Key**: Read directly from the "Key" column of the Plan Inventory tables.

   > **⚠️ CRITICAL: Key Format Expectation**
   >
   > The key **MUST** be the exact directory name as it appears on disk.
   > The meta plan (created by `/create-meta-plan`) should contain keys like:
   > - `2976-spring-companymaintenanceservice-getcompanylist` (correct)
   > - `2105-infrastructure-company-company-maintenance-address` (correct)
   >
   > If the meta plan contains incorrect key formats like:
   > - `2976` (numeric only) - **WRONG**
   > - `2976-infrastructure-company-company-maintenance-list-companies` (fabricated) - **WRONG**
   >
   > Then the meta plan needs to be regenerated with `/create-meta-plan` before extraction.

3. **Functional spec path**: Construct using the key from the Plan Inventory:
   - For `api-endpoint`: `./docs/entry-points/api-endpoints/{key}/functional-spec.md`
   - For `ui-feature`: `./docs/entry-points/ui-features/{key}/functional-description.md`
   - For `quartz-batch-job`: `./docs/entry-points/quartz-batch-jobs/{key}/functional-spec.md`
   - For `common`: `./docs/entry-points/common/{key}/functional-spec.md`

4. **Technical plan path**: Construct as:
   - `./docs/entry-points/{type-plural}/{key}/technical-plan.md`

Where `{type-plural}` is:
- `api-endpoints` for type `api-endpoint`
- `ui-features` for type `ui-feature`
- `quartz-batch-jobs` for type `quartz-batch-job`
- `common` for type `common`

### Step 3: Assign Sequence Numbers

Assign sequential numbers starting from 1, following the dependency order extracted from the meta plan. Items with no dependencies get lower sequence numbers, items that depend on others get higher numbers.

### Step 4: Validate Paths

For each item, verify that the files exist:
- Check if `functionalSpecPath` exists (or `functional-description.md` for UI features)
- Check if `technicalPlanPath` exists
- If a path doesn't exist, include it anyway but add a note to stderr

### Step 5: Write JSON

1. Sort array by `sequence` number (should already be in order)
2. Format as pretty-printed JSON with 2-space indentation
3. Write to `./docs/plan/meta-plan.linear.{domain}.json`

## Implementation Notes

### Handling Different Functional Spec Names

UI features typically use `functional-description.md` instead of `functional-spec.md`. Check for both:

1. First check for `functional-spec.md`
2. If not found, check for `functional-description.md`
3. Use whichever exists

### Preserving Order

The sequence numbers must reflect the dependency-respecting implementation order from the meta plan. This ensures:

- Items can be sorted by sequence for deterministic ordering
- Dependencies are implemented before dependents
- The array can be processed sequentially from first to last

### Stored Procedure Sharing and Ordering

Many stored procedures are shared across multiple API endpoints (e.g., utility SPs like `xsyp_track_time` can be used by 200+ endpoints). When ordering items:

- When multiple endpoints depend on the same stored procedure, prefer ordering the endpoint with the **simplest SP usage first**. This endpoint establishes the shared service class for the SP conversion.
- Subsequent endpoints that call the same SP will detect the existing conversion during JIT research and reuse it rather than re-converting.
- This is a soft preference, not a hard constraint — other dependency factors (like API dependencies between endpoints) take priority.

### Handling Missing Plans

If a plan is mentioned in the meta plan but its directory/files don't exist yet:

- Still include it in the array
- Use the expected/conventional paths
- The validation step will note which files are missing

---

**End of Command Specification**
