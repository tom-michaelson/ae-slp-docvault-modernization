---
model: opus
---

# Implement (API)

Execute the task list for an API endpoint. Writes Java code directly under
`target_repo/source/api/...`.

**This command edits source files; it does NOT write validation artifacts — the
companion `/review-implementation` is responsible for that.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | API endpoint key |
| `item_type` | `api-endpoint` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |
| `legacy_dir` | Absolute path to the legacy source (reference reads only) |
| `target_stack` | `angular-java` |
| `prior_feedback` *(optional)* | Review feedback from the previous attempt |

## Input sources

- `{entry_point_folder_path}/task-list.md` — the source of truth for ordering.
- `{entry_point_folder_path}/implementation-plan.md` — technical design.
- `{entry_point_folder_path}/functional-spec.md` — authoritative behavior.
- `{entry_point_folder_path}/research.md`, `relationship-discovery.json`,
  `database-dependencies.json`, `call-tree.json` — supporting context.
- Existing code in `{target_repo_dir}/source/api/`.

If `prior_feedback` is provided, read it first — it's the delta you're
correcting.

## Process

1. Work through the task list in order. After each task:
   - Run `./gradlew :api:compileJava` from `{target_repo_dir}/source/api` in
     your head (don't actually shell out — the verify phase does that later).
   - If the acceptance check for the task is a test, write the test and mark
     the task complete by flipping `- [ ]` → `- [x]` in `task-list.md`.
2. Don't skip around — if a task is blocked, stop and document why in the
   research notes; do NOT silently move on.
3. Reuse existing classes and packages when sensible; create new packages only
   for new aggregates.

## Rules (Spring Boot)

- Package base: `com.slalom.modernization.<aggregate>`.
- Controllers return concrete DTOs, never entities.
- Services wrap writes in `@Transactional`; reads in
  `@Transactional(readOnly = true)`.
- Use Bean Validation (`@Valid`, `@NotNull`, `@Size`, custom constraints).
- Map domain errors to HTTP responses via `@ControllerAdvice`, not in-controller `try/catch`.
- Prefer Spring Data repositories over custom JPA code; only drop to
  `EntityManager` when the plan called for it.
- Cache names defined once in `CacheConfig`; reference by constant.

## Files expected under `source/api/src/main/java/com/slalom/modernization/<aggregate>/`

- `<Aggregate>Controller.java`
- `<Aggregate>Service.java`
- `<Aggregate>Repository.java`
- Entities (if new)
- DTOs under `<aggregate>/dto/`

Tests go under `source/api/src/test/java/com/slalom/modernization/<aggregate>/`.

## Success criteria

- [ ] Every checkbox in `task-list.md` is `- [x]`, or the file documents why
      a task was skipped/blocked.
- [ ] Files created / modified match the plan's "Files to create / modify"
      table (any deviations are noted in the task list).

## Error handling

- **Conflicting existing code:** prefer extending over replacing. If replacement
  is unavoidable, note the decision in `task-list.md` under the relevant task.
- **Spec ambiguity:** stop and emit a question in `task-list.md`; do NOT guess.
