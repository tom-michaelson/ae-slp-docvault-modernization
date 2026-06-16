---
model: opus
---

# Generate Unit Tests — API

Generate and run unit tests for an API endpoint. This command owns its full
internal fix loop — the calling workflow dispatches it once and does NOT retry.

**This command writes tests under
`{target_repo_dir}/source/api/src/test/java/...` and a summary at
`{entry_point_folder_path}/test-tracking.json`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | API endpoint key |
| `item_type` | `api-endpoint` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |

## Input sources

- `{entry_point_folder_path}/functional-spec.md` — ACs become tests.
- `{entry_point_folder_path}/implementation-plan.md` — "Test plan" section.
- `{entry_point_folder_path}/task-list.md` — test-related tasks.
- Existing tests + code under
  `{target_repo_dir}/source/api/src/{main,test}/java/...`.

## Process (owns its own fix loop)

1. Generate tests covering every AC in `functional-spec.md`:
   - Service-level tests using plain JUnit 5 + Mockito.
   - MockMvc slice tests (`@WebMvcTest`) for the controller contract.
   - Use `@SpringBootTest` only when integration is genuinely needed.
2. Run the test subset: `./gradlew :api:test --tests '...'` from
   `{target_repo_dir}/source/api`.
3. If failures:
   - Read the failures, fix either the test or the implementation (preferring
     the test when the spec's intent is unambiguous).
   - Re-run. Max **5 internal attempts**.
4. On the final attempt, write `test-tracking.json` regardless of pass/fail.

## Rules

- Test class name mirrors subject: `BasketServiceTest`, `BasketControllerTest`.
- No network, no real DB. Use H2 in-memory for slice tests that need JPA.
- Use `@ParameterizedTest` for similar ACs that differ only by input.
- Name each `@Test` method after the scenario it covers, using
  lowerCamelCase with underscore-separated context (`addItem_createsBasketLazily`).

## Output — `test-tracking.json`

```json
{
  "itemKey": "add-item-to-basket",
  "generatedAt": "2026-04-24T10:00:00Z",
  "attempts": 1,
  "passed": true,
  "testFiles": [
    "target_repo/source/api/src/test/java/com/slalom/modernization/basket/BasketServiceTest.java",
    "target_repo/source/api/src/test/java/com/slalom/modernization/basket/BasketControllerTest.java"
  ],
  "acCoverage": [
    {"scenario": "Add new item to empty basket", "test": "BasketServiceTest.addItem_createsBasketLazily"},
    {"scenario": "Unknown catalog item", "test": "BasketControllerTest.unknownItem_returns404"}
  ],
  "failingTests": []
}
```

If the final run still fails, populate `failingTests` with
`{"name": "...", "output": "..."}` entries and set `"passed": false`. The
parent workflow treats this as non-blocking but visible.

## Success criteria

- [ ] `test-tracking.json` exists.
- [ ] Every AC maps to at least one test in `acCoverage`.
- [ ] `attempts <= 5`.

## Error handling

- **Tests still failing after 5 attempts:** emit `"passed": false` with
  `failingTests` populated; do NOT silently report success.
