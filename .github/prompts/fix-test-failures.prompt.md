---
model: opus
---

# Fix Test Failures

Resolve test failures for the current batch. Called by the verify step after
`dotnet test` (API) or `npm test` (UI) fails.

**This command edits source or test files to get tests green.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `error_file` | Absolute path to captured test failure output |
| `domain` | Domain label |
| `batch_id` | Batch currently being verified |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{error_file}` — raw test runner output.
- .NET test result XML (if present) under
  `{target_repo_dir}/source/api/TestResults/*.trx` or `**/TestResults/*.xml`.
- Source + tests under `{target_repo_dir}/source/api/` and
  `{target_repo_dir}/source/ui/`.
- `docs/entry-points/*/{item}/functional-spec.md` — authoritative behavior
  for ACs.

## Process

1. Parse `{error_file}` (and JUnit XML if available); list each failing test
   with its assertion + stack.
2. For each failure, decide:
   - **Test is wrong** — when the implementation matches the functional spec
     and the test encodes a stale assumption. Fix the test.
   - **Code is wrong** — when the test matches the spec but the code has a
     real bug. Fix the code.
   - **Spec is ambiguous** — flag it (see error handling); do NOT guess.
3. Apply minimal fixes. Prefer adjusting assertions over rewriting tests.
4. Re-run just the failing tests locally (in your head) to sanity-check.

## Rules

- Never `[Skip]` / `[Fact(Skip="...")]` / `xit()` your way to green.
- Never delete a test just because it's red.
- When the fix is in the code, update any tests that become stale as a
  side-effect — don't leave the suite in a half-updated state.
- If a failure exposes a missing AC test, add the missing test (and fix the
  code if needed).

## Success criteria

- [ ] `dotnet test` (API) and/or `npm test -- --watch=false` (UI) pass.
- [ ] No tests disabled or deleted to hit green.
- [ ] Spec-derived ACs still covered by at least one test.

## Error handling

- **Spec ambiguous:** write
  `{target_repo_dir}/source/BATCH_{batch_id}_SPEC_QUESTION.md` with the
  specific scenario and the options, then stop. The workflow retries up to
  its max; the file surfaces the question to the human.
