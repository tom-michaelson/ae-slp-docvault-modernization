---
model: opus
---

# Fix Entity Schema Errors

Fix Hibernate entity mapping errors detected by `EntitySchemaValidationTest` and `EntityRelationshipValidationTest`. Uses the validation error output and repo DDL as sources of truth.

## Usage

```
/fix-entity-schema-errors error_file: [path] domain: [domain]
```

## Input

- `error_file`: Path to file containing Gradle test output with schema/relationship validation errors
- `domain`: Domain name (e.g., `infrastructure`, `company`, `agency`) — used to locate entity files

**First step**: Read the error file to understand what needs to be fixed.

## Critical Guidelines

**DO:**
- Read the error file and parse the specific validation failures
- Cross-reference each error with the repo DDL in `passage-db/ddl-scripts/`
- Fix only the entity fields that are causing validation failures
- Update both the Java type and `@Column` annotations as needed
- Add or update imports when changing types (e.g., `BigDecimal` needs `java.math.BigDecimal`)

**DO NOT:**
- Refactor or restructure entity code beyond what's needed to fix the error
- Change fields that are not causing validation failures
- Modify the database DDL or test code
- Add new fields or relationships
- Change entity class structure (inheritance, annotations, etc.) unless directly related to the error

## Priority Rule — Error Output Trumps DDL

The validation error message tells you what the **actual database** has. The repo DDL tells you the **intended** column definition. If they conflict:

- **Trust the validation error** — it reflects the real Azure SQL schema
- Use the DDL for supplementary details (precision, scale, length) when the error doesn't specify them
- If the DDL disagrees with the error about the column type, the error wins

## Process

### 1. Read Error File

Read the error file and identify all schema validation failures. There are two types of errors:

#### Type A: Schema Mapping Errors (from `ddl-auto=validate`)

These appear during Spring context startup. Pattern:
```
SchemaManagementException: Schema-validation: wrong column type encountered
in column [COLUMN_NAME] in table [SCHEMA.TABLE_NAME];
found [db_type (Types#JDBC_TYPE)], but expecting [entity_type (Types#JDBC_TYPE)]
```

Example:
```
wrong column type encountered in column [REQUEST_ID] in table [dbo.BA_RQST_COMPANY_INFO];
found [numeric (Types#NUMERIC)], but expecting [int (Types#INTEGER)]
```

This tells you:
- **Table**: `BA_RQST_COMPANY_INFO`
- **Column**: `REQUEST_ID`
- **Database has**: `numeric` (JDBC type `NUMERIC`)
- **Entity expects**: `int` (JDBC type `INTEGER`)
- **Fix**: Change entity field from `Integer` to `BigDecimal` (since `numeric` maps to `BigDecimal`)

#### Type B: Query Execution Errors (from `validateEntity` dynamic tests)

These appear when a `SELECT TOP 1` query fails at runtime. Pattern:
```
Entity [EntityName] failed query execution: [error message]
```

These may indicate runtime mapping issues not caught by `ddl-auto=validate`.

#### Type C: Relationship Join Errors (from `EntityRelationshipValidationTest`)

These appear when a `LEFT JOIN FETCH` query fails at runtime. Pattern:
```
Relationship [EntityName].[fieldName] failed JOIN FETCH: [error message]
```

This tells you:
- **Entity**: The entity class with the relationship annotation
- **Field**: The specific relationship field (`@ManyToOne`, `@OneToMany`, etc.) that failed
- **Error**: The join/mapping error details

Common sub-patterns in the error message:

| Error Pattern | Root Cause | Fix |
|---|---|---|
| `could not resolve property: fieldName` | `mappedBy` references a field that doesn't exist on the target entity | Add or rename the `@ManyToOne` field on the target entity to match the `mappedBy` value |
| `Unable to find column with logical name: COLUMN_NAME in table: TABLE_NAME` | `@JoinColumn(name = "COL")` references a non-existent column | Change `name` in `@JoinColumn` to match actual column in the FK table |
| `Unable to find column with logical name` (referencedColumnName) | `referencedColumnName` references a non-existent column on the target | Change `referencedColumnName` to match actual PK/unique column in the target table |
| Type conversion errors | FK column type doesn't match referenced PK type | Align the FK column Java type with the referenced entity's PK type |
| `Cannot join to attribute of basic type` | Relationship annotation on a non-entity field | Remove the relationship annotation or fix the field type |

### 2. For Each Error — Find the Entity and DDL

For each failed table/column:

1. **Find the entity file** at `passage-api/src/main/java/com/williams/api/{domain}/entity/`
   - Search for the `@Table(name = "TABLE_NAME")` annotation to find the right file
   - If not found in the given domain, search all entity directories under `com/williams/api/`

2. **Find the DDL** in `passage-db/ddl-scripts/`
   - Grep for `CREATE TABLE.*\[TABLE_NAME\]` (case-insensitive)
   - Read the full CREATE TABLE statement to get the column definition

### 3. Determine the Correct Fix

Use the SQL-to-Java type mapping table below, combined with the validation error, to determine the correct Java type:

| SQL Server Type | Java Type | Hibernate Annotation Notes |
|-----------------|-----------|---------------------------|
| `int`, `integer` | `Integer` | Use `Long` if values exceed Integer.MAX_VALUE |
| `bigint` | `Long` | |
| `smallint` | `Short` | Or `Integer` for convenience |
| `tinyint` | `Byte` | Or `Integer` for convenience |
| `bit` | `Boolean` | |
| `decimal(p,s)`, `numeric(p,s)` | `BigDecimal` | Use `@Column(precision=p, scale=s)` |
| `numeric` (identity/PK, no precision) | `Integer` or `Long` | Use `@Column(columnDefinition = "numeric")`. BigDecimal not needed for identity PKs. |
| `money`, `smallmoney` | `BigDecimal` | |
| `float` | `Double` | |
| `real` | `Float` | |
| `char(n)`, `nchar(n)` | `String` | **Use `@Column(length=n, columnDefinition="char(n)")`** |
| `varchar(n)`, `nvarchar(n)` | `String` | Use `@Column(length=n)` |
| `varchar(max)` | `String` | Use `@Column(columnDefinition = "varchar(max)")` |
| `nvarchar(max)` | `String` | Use `@Column(columnDefinition = "nvarchar(max)")` |
| `text`, `ntext` | `String` | Use `@Column(columnDefinition = "nvarchar(max)")` (deprecated types, treat as nvarchar(max)) |
| `date` | `LocalDate` | |
| `time` | `LocalTime` | |
| `datetime`, `datetime2`, `datetime2(3)` | `LocalDateTime` | Target DDL uses `datetime2(3)` as standard |
| `datetimeoffset` | `OffsetDateTime` | |
| `binary(n)`, `varbinary(n)` | `byte[]` | |
| `image` | `byte[]` | Use `@Lob` |
| `uniqueidentifier` | `UUID` | |

**ROWVERSION/timestamp columns**: Do NOT map `timestamp` or `rowversion` database columns in entity classes. These are database-managed columns not used by the application. Simply omit them from the entity.

**CRITICAL - char vs varchar Distinction**:
- `char(n)` is **fixed-length** and **space-padded** — use `columnDefinition="char(n)"`
- `varchar(n)` is **variable-length** without padding — use only `length=n`

### Common Mismatch Patterns

| Validation Error | Likely Root Cause | Fix |
|---|---|---|
| `found [numeric], expecting [int]` | `NUMERIC(p,0)` mapped as `Integer` | Change to `BigDecimal` with `@Column(precision=p, scale=0)` |
| `found [numeric], expecting [bigint]` | `NUMERIC(p,0)` mapped as `Long` | Change to `BigDecimal` with `@Column(precision=p, scale=s)` |
| `found [varchar], expecting [char]` | `varchar` column with `columnDefinition="char(n)"` | Remove `columnDefinition`, keep `length=n` |
| `found [char], expecting [varchar]` | `char` column without `columnDefinition` | Add `columnDefinition="char(n)"` |
| `found [nvarchar], expecting [varchar]` | `nvarchar` column treated as `varchar` | Usually OK; add `columnDefinition="nvarchar(n)"` if needed |
| `found [datetime2], expecting [timestamp]` | Wrong temporal type | Use `LocalDateTime` |

### 4. Apply Fixes

#### For Schema Errors (Type A/B)

For each fix:

1. **Change the Java field type** (e.g., `Integer` → `BigDecimal`)
2. **Update `@Column` annotation** — add/update `precision`, `scale`, `columnDefinition`, or `length` as appropriate
3. **Update imports** — add any new imports needed (e.g., `java.math.BigDecimal`)
4. **Preserve existing annotations** — don't remove `@Id`, `@GeneratedValue`, `@EqualsAndHashCode.Include`, etc.
5. If changing an `@Id` field type, also update any `@EmbeddedId` or `@IdClass` that references it

#### For Relationship Errors (Type C)

1. **Parse the error** to identify entity, field, and failure cause
2. **Find the entity file** and locate the relationship field
3. **Cross-reference with DDL** to find the actual FK constraint:
   - Grep for `FOREIGN KEY.*COLUMN_NAME.*REFERENCES` in `passage-db/ddl-scripts/`
   - Identify the actual column name, referenced table, and referenced column
4. **Apply the fix:**
   - For wrong column names: update `@JoinColumn(name = "ACTUAL_COLUMN")`
   - For wrong referenced column: update `referencedColumnName = "ACTUAL_REF_COLUMN"`
   - For invalid `mappedBy`: find the correct field name on the owning entity
   - For type mismatches: align the FK field Java type with the referenced entity PK type
5. **Check both sides** of bidirectional relationships if present

### 5. Format Code

Run spotless to fix formatting (from the project root):

```bash
cd passage-api && ./gradlew spotlessApply -x checkstyleMain -x checkstyleTest
```

## Output

After fixing, describe each fix applied:

```
Fixed entity schema errors for domain [domain]:

1. BaRqstCompanyInfo.requestId: Integer → BigDecimal
   - Column: BA_RQST_COMPANY_INFO.REQUEST_ID
   - DB type: numeric(9,0) → BigDecimal with @Column(precision=9, scale=0)

2. SomeOtherEntity.someField: String (varchar) → String (char)
   - Column: SOME_TABLE.SOME_FIELD
   - Added columnDefinition="char(10)"
```
