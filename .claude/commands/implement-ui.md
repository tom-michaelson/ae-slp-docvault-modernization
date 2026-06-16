---
model: opus
---

# Implement (UI)

Execute the task list for an Angular feature. Writes TypeScript + HTML + SCSS
under `target_repo/source/ui/src/app/...`.

**This command edits source files; validation artifacts come from
`/review-ui-implementation` and `/validate-code-against-functional-spec`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | UI feature key |
| `item_type` | `ui-feature` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |
| `legacy_dir` | Absolute path to legacy source (reference reads) |
| `target_stack` | `angular-java` |
| `prior_feedback` *(optional)* | Review feedback from the previous attempt |

## Input sources

- `{entry_point_folder_path}/task-list.md`
- `{entry_point_folder_path}/implementation-plan.md`
- `{entry_point_folder_path}/functional-spec.md`
- `{entry_point_folder_path}/api-usage.json`
- Screenshots in `{entry_point_folder_path}/screenshots/`
- Existing Angular code:
  - `{target_repo_dir}/source/ui/src/app/layout/*`
  - `{target_repo_dir}/source/ui/src/app/app.routes.ts`
  - `{target_repo_dir}/source/ui/src/styles.scss`

If `prior_feedback` is provided, read it first.

## Process

Same march-through-the-task-list discipline as the API variant. Mark tasks
`- [x]` as you go.

## Rules (Angular 19)

- **Standalone components only.** No NgModules.
- **OnPush** change detection on every component.
- **Signals everywhere:** `signal()`, `computed()`, `input()`, `output()`,
  `model()`. No `BehaviorSubject` in components.
- Services use `inject()` and `HttpClient` with typed response models; no raw
  `any`.
- Reactive forms (`FormBuilder.group`) — no template-driven forms.
- Brand tokens (`--eshop-teal`, `--eshop-green`, etc.) from `styles.scss`; new
  CSS custom properties only if the feature introduces a genuinely new
  design token.
- Reuse `app/layout/*` — do not touch `HeaderComponent`, `HeroBannerComponent`,
  `FooterComponent` unless the task list explicitly calls for it.
- Add routes by appending to `app.routes.ts`, preserving the `** → ''`
  catch-all at the bottom.

## Files expected

Per feature, typically:

```
source/ui/src/app/pages/<feature>/
├── <feature>.component.ts
├── <feature>.component.html  (or inline template)
├── <feature>.component.scss  (if needed)
├── <feature>.component.spec.ts
├── <feature>.service.ts       (if it calls APIs)
├── <feature>.service.spec.ts
└── <feature>.model.ts         (response / request types)
```

## Success criteria

- [ ] Every task in `task-list.md` is `- [x]`, or the reason is documented.
- [ ] Files created / modified match the plan; deviations noted in the task list.

## Error handling

- **Conflict with existing code:** extend > replace. Note replacements.
- **Spec ambiguity:** stop + document the question. Do NOT guess.
