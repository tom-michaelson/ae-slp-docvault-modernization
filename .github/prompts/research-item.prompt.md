---
model: opus
---

# Research Item (JIT)

Gather everything downstream steps will need for a single inventory item before
any code is written. Reads the legacy source, the Discover outputs, and the
current target-repo state, then writes a `research.md` summary.

**This command writes `{entry_point_folder_path}/research.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | Inventory item key |
| `item_type` | `api-endpoint` or `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the Angular + .NET target repo |
| `legacy_dir` | Absolute path to the legacy React/Node.js source |
| `target_stack` | `angular-dotnet` by default |

## Input sources

- Entry point folder: `{entry_point_folder_path}/`
  - `metadata.json`, `functional-spec.md`, `call-tree.json`, `database-dependencies.json`
- Legacy source referenced by `call-tree.json` (look at exact files + line numbers)
- Current state of the target repo:
  - API: `{target_repo_dir}/source/api/src/...` (ASP.NET Core project structure)
  - UI: `{target_repo_dir}/source/ui/src/app/...`

## Process

1. Load every file in `{entry_point_folder_path}/` that exists.
2. From `call-tree.json`, open the 3–5 most important legacy files and note the
   actual behavior (validations, return shapes, error handling, guards).
3. From `database-dependencies.json`, list the tables touched + the operations.
4. Scan the target repo for anything that already implements the item (method
   names, controllers, components, existing tests) — don't rewrite what's
   there; extend or replace intentionally.
5. Assemble the notes into `research.md`.

## Output — `research.md`

Write to `{entry_point_folder_path}/research.md`. Required sections:

```markdown
# Research — {item_key} ({item_type})

## Purpose

One paragraph restatement of what this item does, in plain English.

## Legacy behavior of interest

- File refs with `path:line` for each important behavior you inspected.
- Call order, branches, edge cases.

## Data surface

- Tables read / written, with operations (select/insert/update/delete).
- Any business-rule invariants that show up in the entity layer.

## Target repo state today

- What (if anything) already exists for this item in the target repo.
- Classes, components, or conventions the plan should align with.

## Open questions / risks

- Unknowns to flag for the plan reviewer.

## Source refs

- `legacy/src/...:line`
- `target_repo/source/api/...` or `target_repo/source/ui/...`
```

## Success criteria

- [ ] `research.md` exists, non-empty, contains the required sections above.
- [ ] Every assertion about legacy behavior has a `path:line` citation.
- [ ] If the target repo already has a partial implementation, it's explicitly named.

## Error handling

- **Entry point folder missing:** fail fast with the expected path.
- **Legacy files referenced by `call-tree.json` missing:** note the missing path in the "Open questions" section and continue.
