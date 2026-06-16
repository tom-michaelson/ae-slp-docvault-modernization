---
model: opus
---

# Review Implementation — UI

Verify the Angular code under `target_repo/source/ui/` against the plan + task
list. Same JSON contract as the API review so the workflow parses both the same
way.

**This command writes `{entry_point_folder_path}/implementation-review-result.json`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | UI feature key |
| `item_type` | `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/task-list.md`
- `{entry_point_folder_path}/plan-review.md`
- `{entry_point_folder_path}/functional-spec.md`
- `{entry_point_folder_path}/api-usage.json`
- Code under `{target_repo_dir}/source/ui/src/app/`

## Review checks

All **PASS / FAIL**.

1. **Plan adherence.** Files in plan exist and do what was described.
2. **Task list completion.** All tasks `- [x]` or documented exceptions.
3. **Required changes honored.** Items from `plan-review.md` present in code.
4. **Angular 19 conventions.**
   - Standalone components; no NgModules.
   - OnPush everywhere.
   - Signals for state.
   - `inject()` over constructor DI where component code is involved.
5. **Service-layer HTTP.** Components never call `HttpClient` directly.
6. **Reactive forms + validators.** Match the validators the backend expects.
7. **Routes.** New routes appended; `** → ''` catch-all still last.
8. **Tests exist.** Component spec + interaction spec covers the ACs listed in
   the task list.
9. **Layout untouched.** Unless the task list called for it, `app/layout/*`
   files are unchanged.
10. **No stray edits.**

## Output — same JSON shape as `/review-implementation`

```json
{
  "itemKey": "homepage-catalog-list",
  "validated": true,
  "feedback": "",
  "checks": [
    {"id": "plan-adherence", "verdict": "PASS"},
    {"id": "task-list", "verdict": "PASS"},
    {"id": "required-changes", "verdict": "PASS"},
    {"id": "angular-conventions", "verdict": "PASS"},
    {"id": "service-layer-http", "verdict": "PASS"},
    {"id": "reactive-forms", "verdict": "PASS"},
    {"id": "routes", "verdict": "PASS"},
    {"id": "tests-present", "verdict": "PASS"},
    {"id": "layout-untouched", "verdict": "PASS"},
    {"id": "no-stray-edits", "verdict": "PASS"}
  ]
}
```

## Success criteria

- [ ] JSON parses, every check has a verdict.
- [ ] `validated` is true iff all checks PASS.
- [ ] Failed runs have actionable `feedback` (file paths + specific diff).

## Error handling

- **Implementation missing:** `validated=false` + list missing files in feedback.
