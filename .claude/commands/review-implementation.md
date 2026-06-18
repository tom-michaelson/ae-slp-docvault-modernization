---
model: opus
---

# Review Implementation — API

Verify that the actual code under `target_repo/source/api/` matches the
implementation plan + task list. Produces a machine-readable result the
workflow can branch on.

**This command writes `{entry_point_folder_path}/implementation-review-result.json`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | API endpoint key |
| `item_type` | `api-endpoint` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/task-list.md`
- `{entry_point_folder_path}/plan-review.md` (if present — required changes there must be honored)
- `{entry_point_folder_path}/functional-spec.md`
- Code under `{target_repo_dir}/source/api/src/main/java/com/slalom/modernization/...`
- Tests under `{target_repo_dir}/source/api/src/test/java/...`

## Review checks

Score each: **PASS / FAIL** (no "CONCERN" tier — this gates the workflow).

1. **Plan adherence.** Every file listed in `implementation-plan.md` exists and implements what the plan said.
2. **Task list completion.** Every task is `- [x]`, or a documented exception.
3. **Required changes from plan review honored.** Verbatim items from `plan-review.md` Required Changes are present in code.
4. **Spring Boot conventions.**
   - Package base correct.
   - Controllers return DTOs, not entities.
   - `@Transactional` boundaries right.
   - Bean Validation present where the spec called for it.
5. **No raw `Entity` leakage.** Controllers and public service methods expose only DTOs.
6. **Error handling.** `@ControllerAdvice` maps domain errors; controllers don't swallow.
7. **Tests exist.** Service-level + MockMvc slice tests per the task list.
8. **Dead code / stray edits.** No unrelated edits in the diff.

## Output — `implementation-review-result.json`

Exactly this shape (the workflow parses it):

```json
{
  "itemKey": "add-item-to-basket",
  "validated": true,
  "feedback": "",
  "checks": [
    {"id": "plan-adherence", "verdict": "PASS"},
    {"id": "task-list", "verdict": "PASS"},
    {"id": "required-changes", "verdict": "PASS"},
    {"id": "spring-conventions", "verdict": "PASS"},
    {"id": "dto-boundary", "verdict": "PASS"},
    {"id": "error-handling", "verdict": "PASS"},
    {"id": "tests-present", "verdict": "PASS"},
    {"id": "no-stray-edits", "verdict": "PASS"}
  ]
}
```

- `validated: true` requires ALL checks PASS.
- `feedback` MUST be non-empty when `validated: false`; it's fed back into the
  next `/implement` attempt verbatim as `prior_feedback`, so make it
  actionable and specific (file paths + what needs to change).

## Success criteria

- [ ] JSON file exists and parses.
- [ ] Every check has a verdict.
- [ ] `validated` true iff all checks PASS.
- [ ] `feedback` is a concrete, actionable diff description when `validated=false`.

## Error handling

- **No implementation found:** set `validated=false`, list the missing files
  in `feedback`.
