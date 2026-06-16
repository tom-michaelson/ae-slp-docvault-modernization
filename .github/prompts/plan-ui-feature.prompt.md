---
model: opus
---

# Plan UI Feature (Angular)

Produce the implementation plan for one UI feature targeting the Angular side of
the target repo. Uses the shell + layout already defined under
`target_repo/source/ui/src/app/layout/` — do not replan the shell.

**This command writes `{entry_point_folder_path}/implementation-plan.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | UI feature key |
| `item_type` | Should be `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the Angular + .NET target repo |
| `legacy_dir` | Absolute path to the legacy React/Node.js source |
| `target_stack` | Typically `angular-dotnet` |

## Input sources

1. `{entry_point_folder_path}/functional-spec.md`
2. `{entry_point_folder_path}/research.md`
3. `{entry_point_folder_path}/api-usage.json` — which REST endpoints this feature calls
4. Any screenshots in `{entry_point_folder_path}/screenshots/`
5. Existing Angular layout + routes:
   - `{target_repo_dir}/source/ui/src/app/app.routes.ts`
   - `{target_repo_dir}/source/ui/src/app/layout/`
   - `{target_repo_dir}/source/ui/src/app/pages/`

## Content the plan MUST cover

- **Route** — path in `app.routes.ts`, route params, lazy-loading if warranted.
- **Components** — component tree for this feature (standalone components,
  OnPush change detection, which ones are presentational vs. container).
- **Template structure** — major blocks (use plain words, not HTML dumps).
- **Services** — which `*.service.ts` to create/extend; what REST endpoints
  they hit (reference keys from `api-usage.json`).
- **State** — component `signal()`s, derived `computed()`s, `input()`/`output()`
  contracts; any shared state via a service with `signal()`s.
- **Forms** — reactive form schema + validators (Data Annotations-equivalent on the .NET side; Angular Validators on the Angular side).
- **Styling** — which brand tokens apply (reference existing CSS variables in the target repo); new SCSS files only if the feature needs non-layout styling.
- **Error + loading states** — visual design language per functional spec.
- **Test strategy** — component unit tests (`*.spec.ts`) and the ACs each covers.

## Output — `implementation-plan.md`

```markdown
# Implementation Plan — {item_key}

## Overview

What the feature is, which route, which APIs it wires up.

## Route

- Path, guards, lazy-load y/n.

## Component tree

- Standalone components; mark container vs. presentational.

## Template structure

- Bullet list per component describing the major UI regions.

## Services + data flow

- Service classes with methods that hit REST endpoints.
- Endpoint refs: e.g., `list-documents-paged`, `upload-document`, etc. (from `api-usage.json`).

## State

- Signals, computed values, inputs/outputs.
- Loading + error signals.

## Forms

- Reactive form controls + validators (only if the feature has forms).

## Styling

- Brand tokens used; new SCSS files (if any).

## Business rules

- Numbered list, each mapped back to the functional spec / ACs.

## Test plan

- Component specs + the ACs each covers.

## Files to create / modify

| Path | Action |
| --- | --- |
| `target_repo/source/ui/src/app/pages/documents/document-list.component.ts` | create |
| `target_repo/source/ui/src/app/pages/documents/document.service.ts` | create |
| ... | ... |
```

## Rules

- **Angular 19 standalone components** — no NgModules.
- **OnPush** change detection everywhere.
- **Signals** for component state; `input()` / `output()` / `model()` for binding.
- Reuse the layout in `app/layout/*` — do **not** replan header/hero/footer.
- Extend `app.routes.ts` rather than rewriting it.

## Success criteria

- [ ] File exists at `{entry_point_folder_path}/implementation-plan.md`.
- [ ] Contains every `##` heading above.
- [ ] Every API in `api-usage.json` appears somewhere in the "Services" section.
- [ ] Every AC from `functional-spec.md` appears in the test plan.

## Error handling

- **No `functional-spec.md`:** fail fast.
- **No `api-usage.json`:** treat as "no API dependencies" and emit a warning.
