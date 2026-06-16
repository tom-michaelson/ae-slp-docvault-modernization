---
model: sonnet
---

# Create Task List — UI feature

Break the approved `implementation-plan.md` into an ordered checklist for an
Angular feature.

**This command writes `{entry_point_folder_path}/task-list.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | UI feature key |
| `item_type` | `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/plan-review.md`
- `{entry_point_folder_path}/functional-spec.md`
- `{entry_point_folder_path}/api-usage.json`

## Task ordering

Bottom-up so each task is verifiable before the next:

1. Types / interfaces (mirror API response shapes)
2. Service (`*.service.ts`) wrapping the REST calls
3. Presentational components (no side effects)
4. Container component (wires service → template)
5. Reactive form + validators (if applicable)
6. Route entry in `app.routes.ts`
7. Styling / brand token wiring
8. Component spec tests
9. Interaction / error-state tests

## Output — `task-list.md`

```markdown
# Task List — {item_key}

## Tasks

- [ ] **1. Types** — create
      `target_repo/source/ui/src/app/pages/home/catalog-item.model.ts`.
      Acceptance: `npm run build` passes.
- [ ] **2. Service** — `catalog.service.ts` exposing `listCatalogItems(...)`.
- [ ] **3. Presentational: product tile** — …
- [ ] **4. Container: HomeComponent** — …
- [ ] **5. Route wiring** — append to `app.routes.ts`.
- [ ] **6. Styling** — extend `styles.scss` or component scss (tokens only).
- [ ] **7. Tests — render** — acceptance: `npm test -- --watch=false` passes.
- [ ] **8. Tests — interaction** — filter + pagination paths covered.

## Mapping to acceptance criteria

| AC from functional-spec.md | Covered by task(s) |
| --- | --- |
| Shopper lands on homepage with no filters | 4, 7 |
| Shopper filters by brand | 4, 5, 8 |
| ... | ... |
```

## Rules

- Same as API variant — `- [ ]` + numbering + concrete paths + mechanical
  acceptance checks.
- Every AC in the spec appears in the mapping.

## Success criteria

- [ ] `task-list.md` exists.
- [ ] Acceptance mapping table covers every AC.

## Error handling

- **Plan missing:** fail fast.
- **Review REJECTED:** fail fast.
