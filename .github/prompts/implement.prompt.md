---
model: opus
---

# Implement (API)

Execute the task list for an API endpoint. Writes C# code directly under
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
| `target_stack` | `angular-dotnet` |
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
   - Run `dotnet build` from `{target_repo_dir}/source/api` in
     your head (don't actually shell out — the verify phase does that later).
   - If the acceptance check for the task is a test, write the test and mark
     the task complete by flipping `- [ ]` → `- [x]` in `task-list.md`.
2. Don't skip around — if a task is blocked, stop and document why in the
   research notes; do NOT silently move on.
3. Reuse existing classes and packages when sensible; create new packages only
   for new aggregates.

## Rules (ASP.NET Core)

- Namespace base: established project namespace under `<Aggregate>` folder.
- Controllers return concrete DTOs, never entities. Decorate with `[ApiController]` and `[Route]`.
- Services wrap writes in an EF Core transaction where needed; read-only queries need no explicit transaction.
- Use Data Annotations or FluentValidation (`[Required]`, `[MaxLength]`, custom validators); `[ApiController]` auto-returns 400 on model validation failure.
- Map domain errors to HTTP responses via global exception handler middleware or `IExceptionHandler`, not in-controller `try/catch`.
- Prefer repository pattern over direct `DbContext` access in controllers; only use `DbContext` directly when the plan called for it.
- Cache configuration defined once in `Program.cs` or `CacheConfig`; reference cache keys by constant.

## Files expected under `source/api/src/<Aggregate>/`

- `<Aggregate>Controller.cs`
- `<Aggregate>Service.cs`
- `I<Aggregate>Service.cs` (interface, if the plan calls for it)
- `<Aggregate>Repository.cs` / `I<Aggregate>Repository.cs`
- Entities (if new) under `<Aggregate>/Models/`
- DTOs under `<Aggregate>/Dtos/`

Tests go under `source/api/tests/<Aggregate>/`.

## Success criteria

- [ ] Every checkbox in `task-list.md` is `- [x]`, or the file documents why
      a task was skipped/blocked.
- [ ] Files created / modified match the plan's "Files to create / modify"
      table (any deviations are noted in the task list).

## Error handling

- **Conflicting existing code:** prefer extending over replacing. If replacement
  is unavoidable, note the decision in `task-list.md` under the relevant task.
- **Spec ambiguity:** stop and emit a question in `task-list.md`; do NOT guess.
