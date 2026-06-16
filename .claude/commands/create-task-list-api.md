---
model: sonnet
---

# Create Task List — API endpoint

Break the approved `implementation-plan.md` into an ordered, check-offable list
the implement step can march through.

**This command writes `{entry_point_folder_path}/task-list.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | API endpoint key |
| `item_type` | `api-endpoint` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/plan-review.md` (fold required changes into tasks)
- `{entry_point_folder_path}/functional-spec.md` (for AC cross-refs)
- `{entry_point_folder_path}/relationship-discovery.json`

## Process

1. Fold any "Required changes" from `plan-review.md` into the relevant section
   of the plan before writing tasks.
2. Produce an ordered checklist. Order bottom-up so each task can be verified
   by tests before the next begins:
   1. Entities (if new)
   2. Repository
   3. Service
   4. DTOs
   5. Controller
   6. Exception / error mapping
   7. Cache / cross-cutting
   8. Unit tests (service-level)
   9. MockMvc / slice tests
3. Each task gets a filename and a short acceptance check the implementer can
   verify locally (e.g. `./gradlew compileJava`).

## Output — `task-list.md`

Required headings:

```markdown
# Task List — {item_key}

## Tasks

- [ ] **1. Entity: `Basket`** — create/extend at
      `target_repo/source/api/src/main/java/com/slalom/modernization/basket/Basket.java`.
      Acceptance: `./gradlew :api:compileJava` passes.
- [ ] **2. Repository: `BasketRepository`** — …
- [ ] **3. DTO: `BasketResponse`** — …
- [ ] **4. Service: `BasketService`** — …
- [ ] **5. Controller: `BasketController`** — …
- [ ] **6. Error mapping** — …
- [ ] **7. Cache config** — …
- [ ] **8. Unit tests (service)** — acceptance: `./gradlew :api:test --tests '*BasketServiceTest'` passes.
- [ ] **9. MockMvc slice** — acceptance: passes.

## Mapping to acceptance criteria

| AC from functional-spec.md | Covered by task(s) |
| --- | --- |
| Add new item to empty basket | 4, 8, 9 |
| ... | ... |
```

## Rules

- Checklist items MUST start with `- [ ]` (unchecked) and be numbered.
- Every item MUST have a concrete file path and a mechanical acceptance check.
- Every AC from the functional spec MUST appear at least once in the mapping table.

## Success criteria

- [ ] `task-list.md` exists.
- [ ] At least one task per section listed in `implementation-plan.md`.
- [ ] Acceptance mapping table covers every AC.

## Error handling

- **Plan missing:** fail fast.
- **Review flagged REJECTED:** fail fast with a message telling the caller to
  redo the plan.
