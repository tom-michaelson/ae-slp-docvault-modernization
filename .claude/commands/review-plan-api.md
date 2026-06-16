---
model: opus
---

# Review Plan — API endpoint

Critique `implementation-plan.md` for a Spring Boot API endpoint. Produces a
review document (no JSON) that the author can react to before implementation
starts.

**This command writes `{entry_point_folder_path}/plan-review.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | Item key |
| `item_type` | `api-endpoint` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/functional-spec.md`
- `{entry_point_folder_path}/database-dependencies.json`
- `{entry_point_folder_path}/relationship-discovery.json`
- Existing code under `{target_repo_dir}/source/api/`

## Review checklist

Score each checklist item as **PASS / CONCERN / FAIL** and justify.

1. **Spec coverage.** Every AC in `functional-spec.md` has a corresponding
   item in the plan's test section. Missing ACs → FAIL.
2. **Contract correctness.** HTTP method + path match the functional spec
   and the in-project REST convention. Path params and query params present.
3. **Layered architecture.** Controller → Service → Repository; no shortcuts
   (e.g. controllers hitting repositories directly).
4. **Transactions.** Reads marked `readOnly=true`; writes wrap everything the
   aggregate needs in one `@Transactional`.
5. **Data integrity.** Server-authoritative where the spec says so (e.g.
   prices looked up server-side). Validates inputs at the boundary.
6. **Entities.** Plan only references entities in `relationship-discovery.json`
   or explicitly flags new ones with justification.
7. **Cross-cutting.** Cache / auth / logging decisions are explicit, not
   implicit.
8. **Reuse.** Plan extends existing classes where reasonable instead of
   inventing new ones.
9. **Testability.** Each assertion in the plan maps to a testable behavior.
10. **Risk/unknowns.** Anything the plan glosses over that should be called out.

## Output — `plan-review.md`

```markdown
# Plan Review — {item_key}

Reviewed against: `implementation-plan.md`
Reviewer: Claude (`/review-plan-api`)
Date: {ISO 8601}

## Summary

Overall verdict: **APPROVED** | **APPROVED WITH CONCERNS** | **REJECTED**

One-paragraph rationale.

## Checklist

| # | Item | Verdict | Notes |
| --- | --- | --- | --- |
| 1 | Spec coverage | PASS | |
| 2 | Contract correctness | CONCERN | Missing 409 case on duplicate add. |
| ... | | | |

## Required changes

Numbered list — each MUST be addressed before implementation.

## Suggestions

Numbered list — nice-to-haves the author can ignore.

## Open questions

List (optional).
```

## Success criteria

- [ ] Every checklist item has a verdict.
- [ ] Each CONCERN / FAIL has a concrete "required change" entry.
- [ ] Summary verdict is one of the three listed values.

## Error handling

- **`implementation-plan.md` missing:** fail fast and request it.
- **`functional-spec.md` missing:** review in degraded mode and flag explicitly.
