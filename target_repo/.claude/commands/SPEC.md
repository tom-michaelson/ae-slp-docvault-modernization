# Develop Workflow Slash Command Spec

This document is the contract between `awa-develop` and the 19 slash commands it
invokes. Each command lives as a `.md` file under this directory (e.g.
`research-item.md`) and is responsible for:

1. Reading its declared **inputs**
2. Writing the declared **outputs** at the declared paths
3. Being **idempotent** — re-running with the same inputs MUST NOT corrupt the
   output (safe to re-run; cheap to short-circuit if the workflow didn't delete
   the prior output)

All commands run with **cwd = `target_repo_dir`**. The legacy code path is
always passed as `legacy_dir=…` when relevant.

The **target stack is Angular + Spring Boot (Java 25)**. Commands should assume
that target unless `target_stack=…` is overridden in the input.

---

## Command index

| Phase | # | Command | Applies to |
| --- | - | --- | --- |
| Planning | 1 | [`/develop.analyze-page-components`](#developanalyze-page-components) | per page |
| Planning | 2 | [`/develop.generate-page-plan`](#developgenerate-page-plan) | per page |
| Item | 3 | [`/research-item`](#research-item) | per item |
| Item | 4 | [`/discover-entity-relationships`](#discover-entity-relationships) | per item |
| Item | 5 | [`/plan-api-endpoint`](#plan-api-endpoint) | api-endpoint |
| Item | 6 | [`/plan-ui-feature`](#plan-ui-feature) | ui-feature |
| Item | 7 | [`/review-plan-api`](#review-plan-api) | api-endpoint |
| Item | 8 | [`/review-plan-ui`](#review-plan-ui) | ui-feature |
| Item | 9 | [`/create-task-list-api`](#create-task-list-api) | api-endpoint |
| Item | 10 | [`/create-task-list-ui`](#create-task-list-ui) | ui-feature |
| Item | 11 | [`/implement`](#implement) | api-endpoint |
| Item | 12 | [`/implement-ui`](#implement-ui) | ui-feature |
| Item | 13 | [`/review-implementation`](#review-implementation) | api-endpoint |
| Item | 14 | [`/review-ui-implementation`](#review-ui-implementation) | ui-feature |
| Item | 15 | [`/validate-code-against-functional-spec`](#validate-code-against-functional-spec) | per item |
| Tests | 16 | [`/generate-api-unit-tests`](#generate-api-unit-tests) | api-endpoint |
| Tests | 17 | [`/generate-ui-unit-tests`](#generate-ui-unit-tests) | ui-feature |
| Verify | 18 | [`/fix-build-errors`](#fix-build-errors) | per batch |
| Verify | 19 | [`/fix-test-failures`](#fix-test-failures) | per batch |

---

## Conventions

- **Arg format:** `key=value`, space-separated. Values that contain spaces must
  be quoted by the caller.
- **Paths:** Absolute paths. The workflow never passes relative paths.
- **Entry-point folder:** Discover-produced folder for an item, e.g.
  `{docs_dir}/entry-points/ui-features/{item-key}/` or
  `.../api-endpoints/{item-key}/`. Contains `metadata.json`, `functional-spec.md`,
  `technical-plan.md`, etc.
- **Validation result JSON shape** (used by steps 13–15):

  ```json
  { "validated": true, "feedback": "..." }
  ```

  When `validated=false`, `feedback` is passed back into the next retry as
  `prior_feedback=…`.

---

## Planning commands

### `/develop.analyze-page-components`

Break a page into its constituent UI pieces (forms, grids, buttons, nav, data
bindings) from the Discover analysis files.

**Inputs**

| Arg | Purpose |
| --- | --- |
| `page_key` | Discover page identifier |
| `docs_dir` | Root of the Discover outputs |
| `output_path` | Destination JSON file |

**Reads**

- `{docs_dir}/entry-points/ui-pages/{page_key}/screen-analysis.json`
- `{docs_dir}/entry-points/ui-pages/{page_key}/field-mappings.json`
- `{docs_dir}/entry-points/ui-pages/{page_key}/db-operations.json`
- `{docs_dir}/entry-points/ui-pages/{page_key}/business-rules.json`

**Writes**

- `{output_path}` — JSON array of components with fields at minimum:
  `id`, `type` (`form|grid|button|nav|…`), `label`, `bindings[]`.

**Idempotency:** Workflow skips the call if `{output_path}` exists.

---

### `/develop.generate-page-plan`

Turn the component breakdown into an implementation plan: typed items,
dependencies, E2E batches.

**Inputs**

| Arg | Purpose |
| --- | --- |
| `page_key` | — |
| `domain` | Namespaces output files |
| `page_analysis_path` | Input from the previous command |
| `output_json_path` | Plan JSON destination |
| `output_md_path` | Human-readable plan destination |

**Writes**

- `{output_json_path}` — array of E2E batches:

  ```json
  [
    {
      "batchId": "batch-1",
      "items": [
        { "key": "0001-get-catalog-items", "type": "api-endpoint", "dependencies": [] },
        { "key": "0002-catalog-list-page", "type": "ui-feature", "dependencies": ["0001-get-catalog-items"] }
      ]
    }
  ]
  ```
- `{output_md_path}` — human summary of the same.

**Rules**

- Each item's `type` must be one of `api-endpoint` or `ui-feature`.
- `dependencies` lists `key`s of items that MUST be implemented first.
- Items within a batch are independent; batches are strictly serialized.
- Every UI item must have a `functionalSpecPath` pointing at an existing
  `functional-spec.md` under the entry-point folder.

**Idempotency:** Workflow skips if `{output_json_path}` exists.

---

## Per-item commands

All per-item commands receive these core args:

| Arg | Purpose |
| --- | --- |
| `item_key` | — |
| `item_type` | `api-endpoint` or `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's Discover folder |
| `target_repo_dir` | Implementation root |
| `legacy_dir` | Legacy source (for reference reads) |
| `target_stack` | `angular-java` by default |

Extra args and outputs differ per command below.

### `/research-item`

Gather context before planning — legacy call tree, target-repo current state,
relevant conventions.

**Writes:** `{entry_point_folder_path}/research.md`

**Idempotency:** Skip if file exists.

### `/discover-entity-relationships`

Infer JPA relationships for the item based on DDL + Discover DB operations.

**Writes:** `{entry_point_folder_path}/relationship-discovery.json`

**Idempotency:** Skip if file exists.

### `/plan-api-endpoint`

Produce an implementation plan for an API endpoint (Spring Boot controller +
service + repository + DTOs).

**Writes:** `{entry_point_folder_path}/implementation-plan.md`

**Idempotency:** Skip if file exists.

### `/plan-ui-feature`

Produce an implementation plan for a UI feature (Angular component + service +
template + styles + routing).

**Writes:** `{entry_point_folder_path}/implementation-plan.md`

**Idempotency:** Skip if file exists.

### `/review-plan-api`, `/review-plan-ui`

Validate the implementation plan against target-repo conventions.

**Writes:** `{entry_point_folder_path}/plan-review.md`

**Idempotency:** Skip if file exists.

### `/create-task-list-api`, `/create-task-list-ui`

Break the plan into an ordered checklist of actionable tasks.

**Writes:** `{entry_point_folder_path}/task-list.md`

**Idempotency:** Skip if file exists.

### `/implement`, `/implement-ui`

Write the code per the plan + task list.

**Extra args (on retry)**

| Arg | Purpose |
| --- | --- |
| `prior_feedback` | Review feedback from the previous attempt |

**Writes**

- Source + test files under `{target_repo_dir}/source/...`
- Nothing in the entry-point folder beyond possible working notes

**Idempotency:** Commands SHOULD detect already-written files and no-op where
possible. The workflow's gate is `implementation-review-result.json` with
`validated: true`.

### `/review-implementation`, `/review-ui-implementation`

Validate implementation matches plan + target-repo conventions.

**Writes:** `{entry_point_folder_path}/implementation-review-result.json`
(validation result shape; see conventions).

**Idempotency:** The workflow re-runs until the file shows `validated:true` or
max attempts exhausted. Commands should overwrite.

### `/validate-code-against-functional-spec`

Validate that the code covers every Gherkin AC / business rule in the
functional spec. Separate from plan-adherence review.

**Extra args (on retry)**

| Arg | Purpose |
| --- | --- |
| `prior_feedback` | Previous validation feedback |

**Writes:** `{entry_point_folder_path}/ac-validation-result.json` (same shape as
above).

**Skip:** If `functional-spec.md` doesn't exist, the workflow skips this step
entirely.

---

## Test commands

### `/generate-api-unit-tests`, `/generate-ui-unit-tests`

Generate, run, and fix unit tests for the item. The command owns the full
test-fix loop internally (up to 5 internal attempts). Non-blocking — failures
are logged but don't block item completion.

**Writes**

- Test files under `{target_repo_dir}/source/src/test/...`
- `{entry_point_folder_path}/test-tracking.json` — summary of generated tests
  and run results

**Idempotency:** Workflow skips if `test-tracking.json` exists.

---

## Verification commands

Run after *all* items in an E2E batch are implemented. They receive bundled
error context and are responsible for producing commits that resolve the build
or test failures.

### `/fix-build-errors`

**Inputs**

| Arg | Purpose |
| --- | --- |
| `error_file` | Path to captured build error log |
| `domain` | — |
| `batch_id` | Batch being verified |

**Writes**

- Edits to source under `{target_repo_dir}/source/...`

**Loop:** The workflow re-runs the build after this command and retries up to
5 times.

### `/fix-test-failures`

**Inputs**

| Arg | Purpose |
| --- | --- |
| `error_file` | Path to captured test failure log |
| `domain` | — |
| `batch_id` | Batch being verified |

**Writes**

- Edits to source or tests under `{target_repo_dir}/source/...`

**Loop:** Same 5-attempt pattern as build.

---

## Notes for command authors

1. **Write atomically.** Prefer "write to temp path, rename" for outputs the
   workflow checks for existence.
2. **Fail loud.** If you can't produce the declared output, raise — don't write
   a placeholder.
3. **Leave breadcrumbs.** A short prose summary at the top of each artifact
   helps humans pick up where the agent left off.
4. **Assume the workflow might retry.** Retries happen when validation returns
   `validated:false`. Read the prior output + feedback before redoing work.
5. **Respect `target_stack`.** If an override is passed, shape the output
   accordingly. Defaults to Angular + Spring Boot.
