---
model: opus
---

# Validate Code Against Functional Spec

After `/implement` and `/review-implementation` pass, run one more pass that
answers a different question: **does the code actually satisfy every acceptance
criterion in `functional-spec.md`?**

This is separate from plan-adherence review — a plan-adherent implementation
can still miss ACs if the plan missed them.

**This command writes `{entry_point_folder_path}/ac-validation-result.json`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | Item key |
| `item_type` | `api-endpoint` or `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |
| `prior_feedback` *(optional)* | Previous validation feedback, fed back for retries |

## Input sources

- `{entry_point_folder_path}/functional-spec.md` — source of truth for ACs.
- Code + tests under `{target_repo_dir}/source/api` (for api-endpoint) or
  `{target_repo_dir}/source/ui` (for ui-feature).

## Process

1. Extract every Gherkin-like scenario + business rule from `functional-spec.md`.
2. For each AC, check that the implementation demonstrably satisfies it:
   - A test asserts the behavior, OR
   - The behavior is a trivial static consequence of the code (rare — prefer test).
3. For each AC, record PASS or FAIL with evidence (file + line range OR test name).

## Output — `ac-validation-result.json`

```json
{
  "itemKey": "add-item-to-basket",
  "validated": true,
  "feedback": "",
  "acs": [
    {
      "scenario": "Add new item to empty basket",
      "verdict": "PASS",
      "evidence": "BasketServiceTest.addItem_createsBasketLazily"
    },
    {
      "scenario": "Unknown catalog item",
      "verdict": "FAIL",
      "evidence": "No test found covering catalogItemId=9999; handler returns 500 instead of 404."
    }
  ]
}
```

- `validated: true` iff every AC is PASS.
- `feedback` (when `validated=false`) enumerates failed ACs with file paths and
  what needs to change. The workflow feeds this back into the next
  `/implement` attempt as `prior_feedback`.

## Rules

- **Testability bias.** If an AC can be tested and isn't, it FAILs — tell the
  author to add a test.
- **Don't double-count.** Coverage of an AC by one unit test is sufficient; don't
  require redundant tests.
- **Don't rewrite the ACs.** Use the scenarios verbatim from
  `functional-spec.md`.

## Success criteria

- [ ] JSON parses.
- [ ] Every AC in the spec is represented exactly once in `acs`.
- [ ] `validated` true iff all ACs PASS.
- [ ] When not validated, `feedback` lists each failure with a concrete fix pointer.

## Error handling

- **No `functional-spec.md`:** the workflow already skips this command in that
  case. If invoked anyway, return `validated: true` + note in feedback.
