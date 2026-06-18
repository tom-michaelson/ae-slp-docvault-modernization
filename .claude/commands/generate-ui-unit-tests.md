---
model: opus
---

# Generate Unit Tests — UI

Generate and run component + service tests for an Angular feature. Owns its own
internal fix loop.

**This command writes tests under
`{target_repo_dir}/source/ui/src/app/...` and
`{entry_point_folder_path}/test-tracking.json`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | UI feature key |
| `item_type` | `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/functional-spec.md`
- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/task-list.md`
- Existing specs + code under `{target_repo_dir}/source/ui/src/app/`.

## Process

1. Generate `*.component.spec.ts` and `*.service.spec.ts` files next to the
   code under test.
2. Cover render, bindings, user interactions, and error/loading states.
3. Use `provideHttpClientTesting()` + `HttpTestingController` for service tests
   (no real network).
4. Use `ComponentFixture` + `TestBed` for components. Prefer
   `fixture.componentInstance` + signal reads over querying DOM for unit
   assertions; DOM queries for interaction assertions.
5. Run `npm test -- --watch=false --browsers=ChromeHeadless` from
   `{target_repo_dir}/source/ui`.
6. Failures → fix (test or code), re-run. Max **5 internal attempts**.
7. Write `test-tracking.json` at the end regardless of pass/fail.

## Rules

- One `describe` per spec file, named after the class under test.
- One `it` per behavior; name it after the AC it covers.
- Stub services via `TestBed.overrideProvider()` — never mock a service with
  `jasmine.createSpyObj()` if the service itself has a reasonable in-memory
  implementation.

## Output — `test-tracking.json`

Same shape as the API variant:

```json
{
  "itemKey": "homepage-catalog-list",
  "generatedAt": "2026-04-24T10:00:00Z",
  "attempts": 1,
  "passed": true,
  "testFiles": [
    "target_repo/source/ui/src/app/pages/home/home.component.spec.ts",
    "target_repo/source/ui/src/app/pages/home/catalog.service.spec.ts"
  ],
  "acCoverage": [
    {"scenario": "Shopper lands on homepage with no filters", "test": "HomeComponent should render 10 products on page 1"},
    {"scenario": "Shopper filters by brand", "test": "HomeComponent should filter by selected brand"}
  ],
  "failingTests": []
}
```

## Success criteria

- [ ] `test-tracking.json` exists.
- [ ] Every AC mapped to at least one test.
- [ ] `attempts <= 5`.

## Error handling

- **Still failing after 5 attempts:** `"passed": false` + populate `failingTests`.
