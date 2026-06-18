---
model: opus
---

<THINKHARD>
Think deeply and thoroughly about each target section. False positives corrupt specs that downstream code generators will consume — an incorrect fix propagates into ~1500 lines of generated DTO, controller, service, and test code. Err toward escalation when the signal is ambiguous: it is always cheaper for a human to confirm than for the pipeline to ship wrong validation code.

Specifically think about:
- Is "exactly N" here referring to **character length** or something else (cardinality like "exactly one", counts like "exactly 3 rows", time like "exactly 24 hours")?
- Does the DDL actually have the column as char(N)/varchar(N), or might the spec have invented a constraint that doesn't exist in the schema?
- Is there a CHECK constraint or documented format pattern that legitimately requires exact length? If yes, the claim is correct — escalate, do not fix.
- Are "too short" Gherkin scenarios testing actual validation logic that will exist (e.g., a min-length business rule), or are they testing a constraint the database itself doesn't enforce?
</THINKHARD>

# Spec Audit: char(N) / varchar(N) Column Length Constraints

Audits a functional spec for the class of defect where `char(N)` or `varchar(N)` database columns are documented as requiring input of **exactly N characters**, when SQL Server actually enforces only a maximum (and right-pads `char` columns with spaces).

**Input:** `entry_point_folder_path: <relative path, e.g. docs/entry-points/api-endpoints/216-spring-userpermission-getpermissions>`

**Output:** writes JSON to `{entry_point_folder_path}/spec-audit-char-column-lengths-result.json` matching the `SpecAuditResult` schema. Also edits `{entry_point_folder_path}/functional-spec.md` in place when `status=fixed`.

---

## Phase 1 — Investigate

### 1.1 Read the spec
- Read `{entry_point_folder_path}/functional-spec.md` in full.
- Locate and parse the `## Database Operations` section. Build a list of `(table_name, column_name, ddl_type, length)` tuples for every column documented with a `char(N)` or `varchar(N)` type. Ignore other types.

### 1.2 Cross-check every column against the DDL source of truth
Source of truth: `passage-modernization/legacy/database/ddl-tables-and-views.sql`.

For each `(table, column, type, length)` tuple from §1.1:
- Search the DDL for the column definition (`[table]` and `[column]` with the declared type).
- Confirm the type matches (`[char](N)` or `[varchar](N)`).
- Record any mismatches — **these are a different defect class and must be flagged as `escalated`**, not auto-fixed by this command.
- While scanning the table's DDL block, look for any `CONSTRAINT ... CHECK (...)` clauses that reference the column. A CHECK constraint enforcing a minimum length or a specific format pattern (e.g., `LEN(col) = 8`, `col LIKE '[A-Z][A-Z][A-Z][A-Z][0-9][0-9][0-9][0-9]'`) means the exact-length claim may be legitimate — record this as an escalation signal.

### 1.3 Scan five target sections for exact-length claims

For each `char(N)`/`varchar(N)` column confirmed in §1.2, search these sections for exact-length claims:

1. **Database Operations → Columns Used table** — the `Constraints` column. Pattern: `"Exactly N char"`, `"Exactly N chars"`, `"Exactly N character"`, `"Exactly N characters"`. These describe storage width and are often transcribed verbatim into input-validation code downstream; rewrite them to express max-with-padding semantics.
2. **Functional Inputs → Required Business Data / Optional Business Data tables** — the `Constraints/Format` column.
3. **Data Validation Requirements → Format Validations** — numbered list items.
4. **Business Rules / Data Rules / Business Context** — any prose depending on exact length.
5. **Acceptance Criteria (Gherkin)** — scenarios where a "too short" input (shorter than N but non-empty) is asserted to fail. These often live under `# VALIDATION FAILURES` or `# BOUNDARY CONDITIONS` section dividers.

Detection patterns (case-insensitive, regex-oriented):
- `\bexactly\s+\d+\s+char(acter)?s?\b`
- `\bmust\s+be\s+exactly\s+\d+\s+char`
- `\bthe\s+\d+-character\s+[a-z_\s]+\s+exactly\b`
- `\bmust\s+match\s+the\s+\d+-character\s+\w+\s+exactly\b`
- In Gherkin: scenario titles or `Given`/`When` steps containing `"too short"`, `"shorter than"`, `"less than N"` where the assertion is rejection. Also scenarios with inputs like `"a "` or `"x"` that assert the input is invalid specifically because of length.

**Reject these false-positive patterns** (do not treat as defects):
- `"exactly one"`, `"exactly two"` — these are cardinality words, not length claims.
- `"Maximum length: N characters"`, `"up to N characters"`, `"no more than N characters"` — these are correct.
- Gherkin comments referencing a column type as context (e.g., `# varchar(30) database constraint`) without actually asserting too-short inputs fail.
- Claims on columns whose DDL type is NOT `char`/`varchar` (e.g., `int`, `numeric`, `datetime2`).

### 1.4 Determine escalation

Return `status=escalated` without editing the spec if **any** of these conditions hold:

- **CHECK constraint found** in §1.2 that enforces a minimum length or format pattern on a column the spec claims exact length for.
- **Format-pattern justification** in the spec text (e.g., `"codes follow the format XXXX9999"`, `"always 8 digits because..."`, `"is a fixed-format identifier"`). Look especially in Business Domain Concepts, Business Rules, and Glossary sections.
- **DDL type mismatch** — the spec says one type and the DDL says another. Out of scope for this audit.
- **Ambiguous semantic context** — if you cannot confidently determine whether an "exactly N" phrase refers to char length vs. something else (cardinality, row counts, time duration) after reading surrounding context, escalate.

Set `escalation_reason` to a human-readable explanation covering: which column, which section, and which escalation trigger fired.

### 1.5 Determine status

- No `char(N)`/`varchar(N)` columns AND no exact-length claims → `status=passed`, empty issues, empty fixes.
- Columns exist but no exact-length claims found → `status=passed`.
- Exact-length claims found AND escalation triggers hit → `status=escalated`, populate `issues_found`, empty `fixes_applied`.
- Exact-length claims found AND no escalation triggers → proceed to Phase 2, final `status=fixed`.

---

## Phase 2 — Fix

**Only run this phase if Phase 1 concluded `status=fixed`.**

Edit `{entry_point_folder_path}/functional-spec.md` with targeted, minimal changes. Touch **only** the sections listed in §1.3. Do not reformat, reorganize, or "improve" anything else.

### 2.1 Database Operations → Columns Used tables

Find the affected rows in the `Columns Used` table under each affected table's section. In the `Constraints` column:
- `"Exactly N chars"` / `"Exactly N char"` / `"Exactly N character"` / `"Exactly N characters"` → `"Max N chars (char column, space-padded on storage)"` (for `char(N)`)
- For `varchar(N)`: `"Exactly N chars"` → `"Max N chars"`

Preserve all other content in the row (column name, data type, business meaning, used-in flag, FK/PK annotations).

### 2.2 Functional Inputs → Required/Optional Business Data tables

In the `Constraints/Format` column of the affected row:
- `"Must be exactly N characters"` → `"Maximum N characters"`
- `"Must be exactly N characters if provided"` → `"Maximum N characters (when provided)"`
- `"Exactly N chars"` / `"Exactly N characters"` → `"Up to N characters"`

Leave the `Business Rules` column untouched unless that column itself contains an exact-length claim (§2.4).

### 2.3 Format Validations

In the numbered list under `## Data Validation Requirements` → `### Format Validations`:
- `"Must be exactly N characters"` → `"Must be no more than N characters"`
- `"must be exactly N characters if provided"` → `"must be no more than N characters when provided"`

Preserve the `**Business Reason**` / rationale line that follows. If the rationale said something like `"Database field constraint; prevents lookup failures"`, rewrite to `"Database column stores up to N characters; values shorter than N are padded on storage and trimmed on read"`.

### 2.4 Business Rules / Data Rules / Business Context

Rewrite rule text that assumes exact length:
- `"the value must match the N-character {field} exactly"` → `"the value must match a registered {field}, which can be up to N characters"`
- `"{Field} must be exactly N characters"` → `"{Field} accepts up to N characters"`

Preserve the `Rationale` / `Business Impact` lines when they don't depend on the exact-length claim; rewrite them when they do.

### 2.5 Gherkin scenarios

In the `## Acceptance Criteria (Gherkin)` section, find scenarios under `# VALIDATION FAILURES` or `# BOUNDARY CONDITIONS` whose sole invalidity signal is "input shorter than N but non-empty". For each such scenario:

- **Delete the entire `Scenario:` block**, including its Business Context / Frequency / Business Value comments, `Given`/`When`/`Then` steps, and any trailing blank line that belongs to the scenario.
- Do **not** touch scenarios that test empty-input rejection, null rejection, wrong-type rejection, wrong-format rejection (FK lookup failure, pattern mismatch), or other orthogonal validation. Those remain valid.
- Do **not** touch `Scenario Outline` blocks with example tables that include both valid short and valid long inputs — those are boundary tests that correctly assert max-length rejection only.

### 2.6 Running diff discipline

As you apply edits, maintain a running list of section names you have modified. This will be reported in the output as `modified_sections` and used by Phase 3 as a scope guard. Allowed values:
- `"Database Operations - Columns Used"`
- `"Required Business Data"` / `"Optional Business Data"`
- `"Format Validations"`
- `"Business Rules"` / `"Data Rules"` / `"Business Context"`
- `"Acceptance Criteria (Gherkin)"`

Any edit outside this list is a bug in this command — stop, do not write the output file, and return `status=escalated` with `escalation_reason` explaining the out-of-scope edit you almost made.

---

## Phase 3 — Validate

Run this phase after any edits, **including when `status=passed` or `status=escalated`** (it also serves as the final-result guard).

### 3.1 Re-scan for residual exact-length claims

Re-read the post-edit `functional-spec.md`. Run the §1.3 detection patterns again. For each hit, confirm it is either:
- On a column whose DDL type is **not** `char`/`varchar`
- A false-positive pattern (`"exactly one"`, `"Maximum N"`, etc.)
- Legitimately preserved because it was flagged for escalation

If any residual unexplained hit remains, set `status=escalated` with `escalation_reason` explaining what was missed.

### 3.2 Scope guard

Compare the set of sections actually edited to the §2.6 allowed list. If any unauthorized section was touched, **revert the edit** (rewrite the file to its pre-edit state) and return `status=escalated` with `escalation_reason="Out-of-scope edit prevented: <section>"`.

### 3.3 Gherkin sanity check

If Gherkin scenarios were deleted in §2.5, confirm:
- At least one `Scenario:` remains in the file (deleting every scenario is a bug).
- Section dividers (`#──────...`) are still structurally intact.
- Coverage Checklist (`### Scenario Coverage Checklist`) was not modified — if deleting scenarios invalidates a checkbox (e.g., `- [x] Validation Failures (one per rule)`), leave the checkbox as-is; a human will reconcile on review.

### 3.4 Emit result

Write `{entry_point_folder_path}/spec-audit-char-column-lengths-result.json`:

```json
{
  "audit_id": "char-column-lengths",
  "status": "fixed | passed | escalated",
  "ran_at": "<ISO 8601 UTC timestamp>",
  "issues_found": [
    {
      "description": "USER_LOGON_ID claimed exactly 8 characters (Format Validations)",
      "section": "Format Validations",
      "severity": "medium"
    }
  ],
  "fixes_applied": [
    {
      "section": "Format Validations",
      "before_summary": "Must be exactly 8 characters if provided",
      "after_summary": "Must be no more than 8 characters when provided"
    }
  ],
  "escalation_reason": null,
  "summary": "Rewrote 4 exact-length claims on char(8) columns (USER_LOGON_ID, USER_TYPE) across 3 sections.",
  "modified_sections": [
    "Database Operations - Columns Used",
    "Format Validations",
    "Business Rules"
  ]
}
```

Rules for the JSON:
- `severity`: `"low"` for a single table-cell phrase; `"medium"` for Format Validations or Business Rules text; `"high"` if a Gherkin scenario was asserting shortness as invalid (that directly drives test generation).
- `issues_found` must be populated whenever Phase 1 found defects, regardless of whether they were fixed or escalated.
- `fixes_applied` must be empty when `status != "fixed"`.
- `escalation_reason` must be non-null when `status == "escalated"`.
- `modified_sections` must be empty when `status != "fixed"`.
- `summary` is a single sentence for human triage.

If writing the JSON fails, leave the markdown spec untouched (revert if necessary) and re-raise.

---

## Escalation trigger summary

Return `status=escalated` for any of:
- DDL-defined CHECK constraint enforces min-length or format on the column
- Spec text includes a format-pattern justification ("XXXX9999", "always 8 digits", "fixed-format identifier")
- DDL type disagrees with spec type
- Semantic ambiguity about what "exactly N" refers to
- Attempted out-of-scope edit during Phase 2

On escalation: no spec edits persist; the tracking file records the reason; a human reviews and either edits the spec (re-run unblocks) or marks the audit `passed` manually.
