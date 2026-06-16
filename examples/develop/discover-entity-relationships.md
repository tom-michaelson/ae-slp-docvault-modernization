# Discover Entity Relationships

Discover FK-based relationships relevant to a page's table set from DDL constraints. Produces actionable JPA relationship recommendations.

**Use during JIT Research** to identify which relationships an implementing agent should add.

## Usage

**Option A — Page key (resolves tables automatically):**
```
/discover-entity-relationships page_key: [key] entry_point_folder_path: [path]
```

**Option B — Direct table names (no page-plan.json required):**
```
/discover-entity-relationships tables: [TABLE1, TABLE2, ...] output_path: [path] domain: [domain]
```

## Input

**Option A:**
- `page_key`: Page key (e.g., `2014-line`)
- `entry_point_folder_path`: Path to the page's entry point folder (e.g., `docs/entry-points/ui-pages/2014-line`)

**Option B:**
- `tables`: Comma-separated list of table names (e.g., `COMPANY_DATE_EFF, CO_ADDR, CO_ANLYS`)
- `output_path`: Directory to write `relationship-discovery.json` (e.g., `docs/entry-points/ui-pages/2014-line`)
- `domain` (optional): Domain name (e.g., `company`, `infrastructure`) — used to find `erd.{domain}.relationships.json` for enrichment. If omitted, enrichment is skipped.

If `tables` is provided, skip Step 1 (page key resolution) and use the provided table names directly (uppercased). The `page_key` field in the output JSON will be set to `"direct"`.

## Process

### 1. Resolve Page Key → Table Set

**If `tables` parameter is provided:** Use those table names directly (uppercase them), skip the resolution below, and proceed to Step 2.

**Otherwise:** Read `{entry_point_folder_path}/page-plan.json` and extract all items.

For each item, resolve its database tables:

#### API Endpoint Items (`componentType: "api-endpoint"`)

Read `docs/entry-points/api-endpoints/{componentKey}/database-dependencies.json`:
- Filter for entries with `"type": "table"`
- Collect the `name` field (uppercase it)

#### UI Feature Items (`componentType: "ui-feature"`)

The UI feature folder name is `{menuId}-{componentKey}` where `menuId` is extracted from the page key (the numeric prefix, e.g., `2014` from `2014-line`).

1. Read `docs/entry-points/ui-features/{menuId}-{componentKey}/api-usage.json`
2. For each `apiDependencies[].apiKey`, read `docs/entry-points/api-endpoints/{apiKey}/database-dependencies.json`
3. Filter for `"type": "table"`, collect `name` (uppercased)

#### Result

Deduplicated set of table names used by this page. Print the table set for transparency.

**If a database-dependencies.json file is missing** for an item, log a warning and continue — don't fail the entire discovery.

### 2. Parse DDL FK Constraints

Scan **all** `V*.sql` files in `passage-db/ddl-scripts/` for FK constraint definitions.

The ALTER TABLE...FOREIGN KEY pattern spans multiple lines. Two common formats:

**Format A** (single-line ALTER TABLE):
```sql
ALTER TABLE [dbo].[CO_ANLYS] WITH NOCHECK ADD CONSTRAINT [CO_ANLYS_FK1]
    FOREIGN KEY([ACCTG_CO_ID])
    REFERENCES [dbo].[ACCTG_CO] ([ACCTG_CO_ID])
```

**Format B** (multi-line ALTER TABLE):
```sql
ALTER TABLE [dbo].[GA_LINE]
    ADD CONSTRAINT [GA_LINE_FK1] FOREIGN KEY ([PARENT_LINE_ID_NBR])
    REFERENCES [dbo].[GA_LINE] ([LINE_ID_NBR]);
```

**Parsing approach:**

Read each DDL file and use multiline matching to extract:
- **Source table**: The table in `ALTER TABLE [dbo].[TABLE]`
- **Constraint name**: The name in `ADD CONSTRAINT [NAME]`
- **FK columns**: Column list in `FOREIGN KEY([COL1], [COL2], ...)`
- **Target table**: The table in `REFERENCES [dbo].[TABLE]`
- **Referenced columns**: Column list in `REFERENCES ... ([COL1], [COL2], ...)`

Strip brackets from all names. Uppercase table names for matching.

**Filter**: Keep only FK constraints where the source table OR target table is in the page's table set.

### 3. Cross-Reference with JPA Entities

Build an entity index by scanning `passage-api/src/main/java/com/williams/api/*/entity/*.java`:

1. For each `.java` file, extract the table name from `@Table(name = "TABLE_NAME")` annotation
2. Extract the entity class name from the file name
3. Build map: `UPPER(table_name)` → `{ entityName, filePath }`

For each discovered FK constraint:

1. Look up source table and target table in entity index
2. Determine entity availability:
   - **Both exist**: Can add bidirectional relationship (`@ManyToOne` + `@OneToMany`)
   - **Source only**: Can add `@ManyToOne` on source entity
   - **Target only**: Can add `@OneToMany` on target entity (if source becomes an entity later)
   - **Neither**: Note as informational only (no entity to annotate)

3. **Check already-applied**: If the source entity exists, grep its file for:
   - `@JoinColumn` with matching `name = "FK_COLUMN"` — indicates `@ManyToOne` already applied
   - If the target entity exists, grep for `@OneToMany` with matching `mappedBy` — indicates inverse already applied

### 4. Suggest JPA Annotations

For each FK constraint where at least one entity exists:

**Single-column FK → `@ManyToOne` suggestion:**
```java
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumn(name = "FK_COLUMN", referencedColumnName = "REF_COLUMN",
    insertable = false, updatable = false)
private TargetEntity fieldName;
```

**Inverse side → `@OneToMany` suggestion:**
```java
@OneToMany(mappedBy = "fieldName", fetch = FetchType.LAZY)
@ToString.Exclude
private List<SourceEntity> inverseFieldName;
```

**Multi-column FK → `@ManyToOne` with `@JoinColumns`:**
```java
@ManyToOne(fetch = FetchType.LAZY)
@JoinColumns({
    @JoinColumn(name = "FK_COL1", referencedColumnName = "REF_COL1",
        insertable = false, updatable = false),
    @JoinColumn(name = "FK_COL2", referencedColumnName = "REF_COL2",
        insertable = false, updatable = false)
})
private TargetEntity fieldName;
```

**Field naming rules:**
| Relationship | `fieldName` Rule | Example |
|---|---|---|
| `@ManyToOne` | camelCase of target entity name | `pipeline`, `company`, `acctgCo` |
| `@OneToMany` | plural camelCase of source entity name | `lines`, `addresses`, `coAnlysList` |

**Self-referencing FK:** Use `parent` prefix for the `@ManyToOne` field (e.g., `parentLine`) and `children` or `childLines` for the `@OneToMany` inverse.

### 5. Optional Enrichment from relationships.json

Check if `docs/erd.{domain}.relationships.json` exists, where `domain` comes from:
- **Option A:** `page-plan.json`'s `domain` field
- **Option B:** The explicit `domain` parameter (if provided)

If it exists:
- For each discovered FK, search the relationships JSON for a matching entry (match on `fromTable`/`toTable` and `joinColumn`)
- If found, prefer its `fieldName` and `inverseField` over auto-generated names
- Include any `evidence` array from the JSON entry
- Flag JSON relationships that have NO backing DDL FK constraint (potential stale data)

If it does not exist, skip this step entirely. **The command must work without it.**

### 6. Write Output

Write `relationship-discovery.json` to:
- **Option A:** `{entry_point_folder_path}/relationship-discovery.json`
- **Option B:** `{output_path}/relationship-discovery.json`

Structure:

```json
{
  "pageKey": "2014-line",
  "discoveredAt": "2026-03-04T00:00:00Z",
  "domain": "infrastructure",
  "tables": ["LINE", "PIPELINE", "POINT"],
  "relationships": [
    {
      "constraintName": "LINE_FK1",
      "sourceTable": "LINE",
      "sourceColumns": ["PL_ID"],
      "targetTable": "PIPELINE",
      "targetColumns": ["PL_ID"],
      "ddlFile": "V1.06__Create_Tables_PointPipelineDomain.sql",
      "sourceEntity": {
        "name": "Line",
        "filePath": "passage-api/src/main/java/com/williams/api/infrastructure/entity/Line.java",
        "exists": true
      },
      "targetEntity": {
        "name": "Pipeline",
        "filePath": "passage-api/src/main/java/com/williams/api/infrastructure/entity/Pipeline.java",
        "exists": true
      },
      "suggestedAnnotations": {
        "manyToOne": {
          "onEntity": "Line",
          "fieldName": "pipeline",
          "joinColumns": [
            { "name": "PL_ID", "referencedColumnName": "PL_ID" }
          ]
        },
        "oneToMany": {
          "onEntity": "Pipeline",
          "fieldName": "lines",
          "mappedBy": "pipeline"
        }
      },
      "alreadyApplied": {
        "manyToOne": false,
        "oneToMany": false
      },
      "enrichment": {
        "fromRelationshipsJson": false,
        "fieldNameOverride": null,
        "inverseFieldOverride": null,
        "evidence": []
      }
    }
  ],
  "summary": {
    "totalFksFound": 5,
    "bothEntitiesExist": 3,
    "sourceEntityOnly": 1,
    "targetEntityOnly": 0,
    "neitherEntityExists": 1,
    "alreadyApplied": 1,
    "actionable": 2
  }
}
```

### 7. Print Console Summary

After writing the JSON, print a concise summary:

```
Relationship Discovery for page 2014-line
==========================================
Tables resolved: 8 (LINE, PIPELINE, POINT, ...)
FK constraints found: 5
  - Both entities exist: 3 (actionable)
  - Source entity only:  1
  - Neither exists:      1
  - Already applied:     1

Actionable relationships:
  1. LINE → PIPELINE via PL_ID (@ManyToOne on Line)
  2. LINE → POINT via PT_ID (@ManyToOne on Line)

Output: docs/entry-points/ui-pages/2014-line/relationship-discovery.json
```

## Critical Guidelines

**DO:**
- Parse DDL as the primary and required source of truth
- Handle missing database-dependencies.json files gracefully (warn, don't fail)
- Handle missing relationships.json gracefully (skip enrichment)
- Uppercase all table names for consistent matching
- Strip SQL brackets `[` `]` from all names
- Mark multi-column FKs with all columns in the output
- Suggest `insertable = false, updatable = false` on all `@JoinColumn` annotations

**DO NOT:**
- Fail if `erd.{domain}.relationships.json` does not exist
- Fail if some items in page-plan.json have no database-dependencies.json
- Apply any annotations — this is discovery only, not application
- Modify any entity files or DDL files
- Assume all tables have entities — many won't

## Output

The JSON file at `{entry_point_folder_path}/relationship-discovery.json` plus a console summary.
