---
model: opus
---

# Review Plan — UI feature

Critique `implementation-plan.md` for an Angular feature.

**This command writes `{entry_point_folder_path}/plan-review.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | Item key |
| `item_type` | `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/functional-spec.md`
- `{entry_point_folder_path}/api-usage.json`
- Any `screenshots/*.png` in the folder
- Existing Angular code under `{target_repo_dir}/source/ui/src/app/`

## Review checklist

Score each item **PASS / CONCERN / FAIL**.

1. **Spec coverage.** Every AC has a corresponding spec entry in the test
   section.
2. **Route.** New route added to `app.routes.ts`; no duplicates; lazy-loaded if
   the feature is non-default.
3. **Standalone + OnPush.** All components declared standalone; change
   detection set to OnPush.
4. **Layout reuse.** Uses header/hero/footer from `app/layout/*`; does not
   re-implement the shell.
5. **State primitives.** Uses Signals (`signal`, `computed`, `input`,
   `output`) — no legacy `BehaviorSubject` in component state.
6. **Service layer.** Every API in `api-usage.json` is wired through a service
   class; no raw `HttpClient` calls from components.
7. **Forms.** Reactive forms with validators; the validators match the backend
   constraints from the functional spec.
8. **Error + loading UX.** Explicit loading + error states covered.
9. **Accessibility.** Headings, labels, aria-* attributes considered.
10. **Test plan.** Every AC mapped to a component spec; user-interaction paths
    covered (not just rendering snapshots).

## Output — `plan-review.md`

```markdown
# Plan Review — {item_key}

Reviewed against: `implementation-plan.md`
Reviewer: Claude (`/review-plan-ui`)
Date: {ISO 8601}

## Summary

Overall verdict: **APPROVED** | **APPROVED WITH CONCERNS** | **REJECTED**

## Checklist

| # | Item | Verdict | Notes |
| --- | --- | --- | --- |
| 1 | Spec coverage | PASS | |
| ... | | | |

## Required changes

Numbered list.

## Suggestions

Numbered list.

## Open questions

(optional)
```

## Success criteria

- [ ] Every checklist item has a verdict.
- [ ] Each CONCERN / FAIL has a required-change entry.
- [ ] Summary verdict is one of the three listed values.

## Error handling

- **Plan or spec missing:** same fail-fast pattern as the API review.
