---
model: opus
---

# Fix Build Errors

Resolve compile / build failures for the current batch. Called by the verify
step after `dotnet build` (API) or `npm run build` (UI) fails.

**This command edits source files to get the build green. It does not write
validation artifacts.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `error_file` | Absolute path to captured build error output |
| `domain` | Domain label for logging context |
| `batch_id` | Batch currently being verified |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{error_file}` — full build output from the failed attempt.
- Source under `{target_repo_dir}/source/api/` (C#) and
  `{target_repo_dir}/source/ui/` (Angular).
- Docs under `docs/entry-points/*/{item}/` for items in the current batch,
  especially `implementation-plan.md` and `task-list.md`.

## Process

1. Read `{error_file}`; extract each distinct failure.
2. For each:
   - Identify the offending file + line.
   - Understand the error category (missing using directive, type mismatch, missing
     package reference, null reference, Angular template type error, etc.).
   - Apply the minimal fix that preserves the intent of the plan. Prefer
     fixing the broken file over rewriting adjacent files.
3. Do NOT disable build options to mask errors (`--allow-errors`, `@ts-ignore`,
   `@SuppressWarnings("unchecked")` on everything, etc.).
4. If a failure indicates the plan / spec was wrong, stop and emit a clear
   note in the batch directory; do not make up behavior.

## Rules

- No scope creep. Touch only files that cause compile failures or files the
  fix requires.
- Don't remove unrelated tests to dodge failures — fix them properly.
- Keep commits implicit (the workflow handles commit later); your job is to
  leave the tree building.

## Success criteria

- [ ] After your edits, `dotnet build` (API) and/or
      `npm run build` (UI) pass locally.
- [ ] No new lint / typecheck warnings introduced.
- [ ] No scope-creep edits.

## Error handling

- **Error class indicates a deeper plan mistake:** write
  `{target_repo_dir}/source/BATCH_{batch_id}_PLAN_ISSUE.md` describing the
  mismatch and stop. The workflow will retry up to its max and surface the
  file to the human.
