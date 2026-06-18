---
model: opus
argument-hint: <pageKey> <screenshot_name> [base_dir]
---

# Compare Screenshot Pair

Compares ONE pair of legacy/new screenshots for a page using six functional
heuristics. Writes a structured JSON result. Run once per `name` in the page's
`page-capture-plan.json`.

## Arguments

- `$0` — page key (folder under `docs/entry-points/ui-pages/`).
- `$1` — screenshot name (filename stem, no `.png`). Examples: `main-view`, `flow-update`.
- `$2` — *(optional)* base dir override. When provided:
  - `LEGACY_DIR = $2/legacy/`
  - `NEW_DIR = $2/new/`
  - `ANALYSIS_DIR = $2/analysis/`

When `$2` is not provided, defaults are:

- `LEGACY_DIR = docs/entry-points/ui-pages/$0/visual-comparison/legacy/`
- `NEW_DIR = docs/entry-points/ui-pages/$0/visual-comparison/new/`
- `ANALYSIS_DIR = docs/entry-points/ui-pages/$0/visual-comparison/analysis/`

Pair files:
- Legacy: `LEGACY_DIR/$1.png`
- New: `NEW_DIR/$1.png`
- Output: `ANALYSIS_DIR/$1.json`

## What This Does

1. Reads context — the page's capture plan + every relevant feature spec.
2. Reads both screenshots (you are multimodal — view them directly).
3. Applies the 6 functional heuristics. **Ignores** styling.
4. Writes a structured JSON to `ANALYSIS_DIR/$1.json`.
5. Reports the verdict in chat.

## Step 1: Read Context

Read these for context (skip what doesn't exist):

- `docs/entry-points/ui-pages/$0/visual-comparison/page-capture-plan.json` —
  find the entry where `name == $1`. Use its `description`, `navigationHint`,
  and `expectedElements` as the success criteria for this comparison.
- `docs/entry-points/ui-pages/$0/inventory.json` — UI element list for the
  page.
- For every page-feature `key` referenced from the inventory, read
  `docs/entry-points/ui-features/{key}/functional-spec.md` — gives expected
  fields, actions, and behaviors.

## Step 2: Read Both Screenshots

```
Read: LEGACY_DIR/$1.png
Read: NEW_DIR/$1.png
```

If either file is missing, write an `ERROR` JSON (see Step 7) and stop. Do not
attempt the heuristics.

## Step 3: Apply the 6 Heuristics

For each, choose `PASS` / `WARN` / `FAIL`.

### 1. Field Presence (Critical)

Every field/column visible in legacy is also visible in new.

- **PASS** — all legacy fields present
- **WARN** — minor label differences but functionally equivalent ("Co. Name" vs
  "Company Name")
- **FAIL** — one or more legacy fields missing in new

Record `legacy_fields`, `new_fields`, `missing_fields`.

### 2. Field Grouping (Important)

Fields are grouped/organized similarly.

- **PASS** — consistent grouping
- **WARN** — present but grouped differently
- **FAIL** — grouping so different the user struggles to find info

### 3. Data Completeness (Critical)

Same data/records visible.

- **PASS** — same (or equivalent sample) data
- **WARN** — present but presented differently (e.g. row count differs)
- **FAIL** — data visible in legacy is missing in new

### 4. Functional Equivalence (Critical)

Same component types serving the same purpose.

- **PASS** — equivalent components throughout
- **WARN** — minor type changes that don't change workflow (radio → dropdown)
- **FAIL** — change alters user workflow (editable field became read-only)

### 5. Navigation/Actions (Critical)

Same action buttons, links, navigation present.

- **PASS** — all actions present
- **WARN** — present but accessed differently (toolbar vs context menu)
- **FAIL** — one or more actions missing

Record `legacy_actions`, `new_actions`, `missing_actions`.

### 6. Validation Indicators (Important)

Required-field markers, error patterns, constraints.

- **PASS** — consistent
- **WARN** — minor presentation differences
- **FAIL** — required-field indicators or validation patterns missing

## Step 4: Explicitly IGNORE

Don't flag any of:
- Font family / size / weight
- Color scheme
- Spacing, padding, margin
- Borders, shadow effects
- Icon set differences
- Framework-specific styling (Razor + Bootstrap vs Angular + custom CSS)
- Scrollbar appearance
- Header/footer chrome
- Theme/skin differences

The new and legacy apps are deliberately styled differently. We're checking
*function*, not look.

## Step 5: Determine Overall Status

- **FAIL** — any Critical (Field Presence, Data Completeness, Functional
  Equivalence, Navigation/Actions) is FAIL
- **WARN** — no Critical fails, but at least one Important (Field Grouping,
  Validation Indicators) is FAIL or WARN
- **PASS** — all heuristics PASS (or only minor WARNs on Important)

## Step 6: Write Analysis JSON

```bash
mkdir -p ANALYSIS_DIR
```

Write `ANALYSIS_DIR/$1.json`:

```json
{
  "screenshot_name": "$1",
  "status": "PASS|WARN|FAIL",
  "heuristic_results": {
    "field_presence": {
      "status": "PASS|WARN|FAIL",
      "legacy_fields": ["..."],
      "new_fields": ["..."],
      "missing_fields": [],
      "details": "..."
    },
    "field_grouping": {
      "status": "PASS|WARN|FAIL",
      "details": "..."
    },
    "data_completeness": {
      "status": "PASS|WARN|FAIL",
      "details": "..."
    },
    "functional_equivalence": {
      "status": "PASS|WARN|FAIL",
      "details": "..."
    },
    "navigation_actions": {
      "status": "PASS|WARN|FAIL",
      "legacy_actions": ["..."],
      "new_actions": ["..."],
      "missing_actions": [],
      "details": "..."
    },
    "validation_indicators": {
      "status": "PASS|WARN|FAIL",
      "details": "..."
    }
  },
  "issues_found": [],
  "summary": "Brief narrative summary of the comparison."
}
```

## Step 7: Error Output (Missing/Unreadable Screenshot)

If a file is missing, blank, or unreadable, write:

```json
{
  "screenshot_name": "$1",
  "status": "ERROR",
  "error": "legacy file missing | new file missing | unreadable image | both missing",
  "summary": "What was observed and what to recapture."
}
```

## Step 8: Report

Print to chat:

```
## $1

**Status:** PASS | WARN | FAIL

| Heuristic | Status | Notes |
|---|---|---|
| Field Presence | ... | ... |
| Field Grouping | ... | ... |
| Data Completeness | ... | ... |
| Functional Equivalence | ... | ... |
| Navigation/Actions | ... | ... |
| Validation Indicators | ... | ... |

**Issues:**
- ...
- (or "None")

**Analysis:** `ANALYSIS_DIR/$1.json`
```

## Success Criteria

- [ ] Both screenshot files located and read
- [ ] Page + feature context loaded
- [ ] All 6 heuristics evaluated
- [ ] Styling differences ignored
- [ ] Overall status correctly derived from per-heuristic verdicts
- [ ] JSON written to `ANALYSIS_DIR/$1.json`
- [ ] Human-readable summary printed
