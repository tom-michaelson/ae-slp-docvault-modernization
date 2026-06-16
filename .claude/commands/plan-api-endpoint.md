---
model: opus
---

# Plan API Endpoint (Spring Boot)

Produce the implementation plan for one API endpoint targeting the Spring Boot
side of the target repo.

**This command writes `{entry_point_folder_path}/implementation-plan.md`.**

## Input parameters

| Arg | Purpose |
| --- | --- |
| `item_key` | API endpoint key |
| `item_type` | Should be `api-endpoint` |
| `entry_point_folder_path` | Absolute path to the item's docs folder |
| `target_repo_dir` | Absolute path to the target repo |
| `legacy_dir` | Absolute path to the legacy source |
| `target_stack` | Typically `angular-java`; adjust if overridden |

## Input sources

Prefer these in order when drafting the plan:

1. `{entry_point_folder_path}/functional-spec.md`
2. `{entry_point_folder_path}/research.md` (from `/research-item`)
3. `{entry_point_folder_path}/relationship-discovery.json` (from `/discover-entity-relationships`)
4. `{entry_point_folder_path}/call-tree.json`, `database-dependencies.json`, `metadata.json`

Also check the current target repo state under
`{target_repo_dir}/source/api/src/main/java/com/slalom/modernization/` so the
plan reuses existing classes instead of duplicating them.

## Content the plan MUST cover

- **REST contract** — method, path, query params, path params, request body,
  response body, error responses (status codes + shape).
- **Controller** — class name + package, methods, request/response DTOs.
- **Service** — class name + package, dependencies, methods, transactionality.
- **Repository** — Spring Data interface + queries; note any custom impl.
- **Entities** — reference the entities and relationships from
  `relationship-discovery.json`. Note NEW entities vs. reuse of existing.
- **Cache strategy** — `@Cacheable` / `@CacheEvict` if any of the functional
  requirements call for caching (e.g. Caffeine cache name + key + TTL).
- **Validation** — Bean Validation annotations, custom validators.
- **Security** — auth requirements, user identification (e.g. Basket uses cookie
  guid fallback for anonymous users).
- **Error handling** — mapping domain errors → HTTP responses.
- **Test strategy** — what will be unit-tested via MockMvc vs. service-layer,
  plus a list of the ACs that become test cases.

## Output — `implementation-plan.md`

Required headings (a validator looks for these):

```markdown
# Implementation Plan — {item_key}

## Overview

One-paragraph summary: what will be built, against which REST contract, over which DB tables.

## REST Contract

| Method | Path | Request | Response | Error modes |
| --- | --- | --- | --- | --- |

## Controller

- Class + package
- Method signatures (Java)
- DTOs (name + fields)

## Service

- Class + package
- Constructor dependencies
- Public methods with preconditions / postconditions
- Transactionality (`@Transactional(readOnly = ?)`)

## Persistence

- Repository interface + custom methods
- Entities touched (reuse vs. new; point at `relationship-discovery.json`)

## Caching / cross-cutting

- Cache names, keys, TTLs (or "none")
- Validation / security / logging concerns

## Business rules

- Numbered list, each mapped back to the functional spec / ACs.

## Test plan

- List of unit + slice tests with the exact ACs they cover.

## Files to create / modify

| Path | Action |
| --- | --- |
| `target_repo/source/api/src/main/java/.../XController.java` | create |
| ... | ... |
```

## Rules

- **Never** invent a DB column or FK not in `database-dependencies.json` or
  `relationship-discovery.json`.
- If `functional-spec.md` specifies server-authoritative behavior (e.g. "price
  is looked up server-side"), the plan MUST carry that forward.
- Prefer existing classes under `com.slalom.modernization.*` when adding new
  endpoints; only create new packages for new aggregates.

## Success criteria

- [ ] File exists at `{entry_point_folder_path}/implementation-plan.md`.
- [ ] Contains every `##` heading listed above.
- [ ] Every AC from `functional-spec.md` is covered in the test plan.
- [ ] Referenced entities exist in `relationship-discovery.json` (or are flagged as new).

## Error handling

- **Missing `functional-spec.md`:** fail fast and ask for it — cannot plan without it.
- **Missing `research.md` / `relationship-discovery.json`:** emit a warning and
  do a best-effort plan using only the spec + call tree.
