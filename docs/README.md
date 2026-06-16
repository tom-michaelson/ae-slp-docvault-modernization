# `docs/`

Output directory for the `awa-discover` workflow. Everything here is generated —
no hand-written content lives in this tree.

## Layout

```
docs/
└── entry-points/
    ├── ui-features/
    │   ├── inventory.{domain}.json
    │   └── {feature-key}/
    │       ├── metadata.json
    │       ├── call-tree.json
    │       ├── api-usage.json
    │       ├── functional-description.md
    │       ├── functional-spec.md
    │       ├── technical-plan.md
    │       └── screenshots/
    └── api-endpoints/
        ├── inventory.{domain}.json
        └── {endpoint-key}/
            ├── metadata.json
            ├── call-tree.json
            ├── functional-description.md
            ├── functional-spec.md
            └── technical-plan.md
```

## How it gets populated

Run the discover workflow against the legacy codebase in
[`../legacy/`](../legacy/README.md):

```bash
uv run python -m awa workflow start awa-discover --input '{}'
```

The workflow's `docs_dir` input defaults to this directory, so no override is
needed. Re-runs are idempotent — per-item marker files (e.g.
`screenshots/SCREENSHOTS_COMPLETE`) let phases skip already-completed work.

## Consumers

- The modernization engineer reads `functional-spec.md` + `technical-plan.md`
  per entry point to understand scope and implementation approach.
- Downstream code-gen workflows read `technical-plan.md` to drive the Java
  implementation under [`../target_repo/`](../target_repo/README.md).
- Screenshots under each `ui-features/{feature-key}/screenshots/` folder are
  the visual source of truth for UI parity reviews.
