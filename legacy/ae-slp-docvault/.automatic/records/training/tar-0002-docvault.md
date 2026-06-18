# Training Assessment Report: [TAR-0002] — Project B — DocVault

<!--
  ============================================================================
  TRAINING ASSESSMENT REPORT — ITERATION 2

  Decomposition note: The answer key contains compound bullets. Each
  independently identifiable problem has been decomposed into its own row.
  The same 18-issue decomposition used in TAR-0001 is applied here for
  direct comparability across iterations.

  Severity multipliers: Critical=4, High=3, Medium=2, Low=1
  Total weight: 36
  ============================================================================
-->

**Report ID**: TAR-0002
**Project**: Project B — DocVault
**Answer Key**: `broken-project-docvault.md`
**Student Submissions**: All markdown files under `analysis/` (anti_pattern/, bug/, code_smell/, repo_hygiene/, knowledge_gap/, runtime_verification/, user_flow/, architecture_diagram/, document_drift/, priority_matrix/, roadmap/, todo/)
**Attempt Log**: `.automatic/records/training/tal-0002-docvault.md`
**Previous Report**: `.automatic/records/training/tar-0001-docvault.md`
**Date Assessed**: 2026-05-05
**Status**: Complete

## Score Summary *(mandatory)*

| Metric | Value |
|--------|:-----:|
| **Total known issues** | 18 |
| **Issues found** | 17 |
| **Issues partially found** | 1 |
| **Issues missed** | 0 |
| **Additional findings (beyond answer key)** | 9 |
| **Detection rate (raw)** | 97.2% |
| **Detection rate (weighted by severity)** | 95.8% |

<!--
  Detection rate (raw)      = (17 + 0.5 × 1) / 18 × 100 = 97.2%
  Detection rate (weighted) = 34.5 / 36 × 100 = 95.8%
  where weight = severity multiplier (Critical=4, High=3, Medium=2, Low=1)

  Iteration-over-iteration comparison vs TAR-0001 (2026-04-22):
    Raw:      80.6% → 97.2%  (+16.6pp)
    Weighted: 83.3% → 95.8%  (+12.5pp)
    Missed:   3     → 0      (all previously-missed issues now found or partial)
-->

## Issue Detection Matrix *(mandatory)*

### It Runs, But…

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 1 | High | Login crashes the frontend — `POST /api/auth/refresh` returns `{ session: {...} }` instead of `{ token, refreshToken }`, causing `TypeError: Cannot read properties of undefined (reading 'split')` in `AuthContext` | ✅ Found | Root cause + fix | `analysis/bug/auth_refresh_returns_session_object.md` | Full root-cause trace: identified the exact line (`auth.js:80`), the wrong response shape, the null-dereference crash site in `AuthContext.jsx`, and provided the correct JWT-signing fix with code. Runtime verification doc corroborated the prediction from static analysis. |

### Overengineered Where It Shouldn't Be

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 2 | Medium | Three auth systems coexisting on the same pipeline (JWT, session, API key) with no authoritative identity — each checks different headers, fails differently, and the enforcement check accepts whichever one happened to set a value | ✅ Found | Root cause + fix | `analysis/anti_pattern/fractured_authentication.md` | Named "Fractured Authentication." Inventoried all three systems in a table (header, `req` property set, status), identified `req.auth \|\| req.user \|\| req.session.user` ambiguity in `index.js`, and traced the security consequence (JWT-authenticated upload silently writes `uploaded_by = null`). Five-step resolution proposed. |
| 3 | High | API key auth middleware is a stub — `apiKeyAuth.js` always returns HTTP 401 for any request that includes an `X-API-Key` header regardless of key value; the `api_keys` table was never created | ✅ Found | Root cause + fix | `analysis/bug/api_key_auth_always_rejects.md` | Correctly identified the unconditional early return at line 16, the missing backing table, and the side effect that a caller sending both `X-API-Key` AND `Authorization: Bearer` will be blocked before JWT is checked. Provided both a short-term fallthrough fix and a long-term table schema. Runtime verification tested this path. |
| 4 | Medium | Frontend Redux store uses 12 reducers for 4 actual state domains — 3 are redundant duplicates of active reducers and 5 manage features that do not exist | ✅ Found | Root cause + fix | `analysis/anti_pattern/state_overengineering_12_reducers.md` | Produced a full reducer inventory classifying all 12 as Active (4), Redundant (3), or Unused (5) with reasons for each. Named the `state.auth` / `state.user` overlap confusion explicitly. Recommended RTK `configureStore` replacement. |
| 5 | Medium | `ActionCreatorFactory` — a 100-line class generating Redux action creators that deviates from standard `action.payload` convention by using per-creator `payloadKey` fields; the registry it maintains is never read | ✅ Found | Root cause + fix | `analysis/anti_pattern/action_creator_factory_overengineering.md` | Confirmed the factory is effectively dead code (no component dispatches factory-created actions), identified the non-standard payload key convention that breaks RTK reducer compatibility, and confirmed the four pre-configured instances are never imported. Recommended deletion. |
| 6 | Low | `store.js` contains a large commented-out "abandoned refactor" block (~130 lines, roughly half the file is inactive code) | ✅ Found | Root cause + fix | `analysis/code_smell/store_dead_code_abandoned_refactor.md` | Identified the exact block delimiters (`START/END ABANDONED REFACTOR`), noted the three buried TODO markers inside dead code that are easy to miss, and flagged the misleading signal it sends to new developers. Recommended extracting TODOs and deleting the block. |
| 7 | Medium | Document search routes every query through a 3-class pipeline (`SearchOrchestrator` → `IndexManager` → `FallbackSearchProvider`) that always ends with a single `ILIKE` SQL query; the intermediate layers add no observable behavior | ✅ Found | Root cause + fix | `analysis/anti_pattern/search_pipeline_overengineering.md` | Traced the full call chain with line-by-line annotation. Confirmed `IndexManager.isIndexAvailable()` always returns `false` (the "index available" branch is unreachable dead code that would crash the app). 120 lines of custom code vs a 10-line equivalent shown. Recommended deleting both intermediate classes. |
| 8 | Low | `SearchOrchestrator.rerank()` sets every result's `score` to `1.0` — the re-ranking step is a no-op; `FallbackSearchProvider` also sets `score: 1.0`, so two no-op scoring passes compound each other | ✅ Found | Root cause | `analysis/anti_pattern/search_pipeline_overengineering.md` | Explicitly observed the double `score: 1.0` assignment in the same finding file. |

### Sloppy Where It Shouldn't Be

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 9 | Low | Dependencies in both packages are 2+ years out of date | ✅ Found | Root cause + fix | `analysis/repo_hygiene/dependency_health.md` | Identified multiple packages 1–3 major versions behind across both `backend/package.json` and `frontend/package.json`. Provided a prioritized upgrade plan with near-term and long-term actions. |
| 10 | High | Three packages have known CVEs visible in `npm audit` | 🔶 Partial | Symptom only | `analysis/repo_hygiene/dependency_health.md` | Student correctly identified that outdated dependencies carry CVE risk and explicitly noted "npm audit could not be run" due to the missing lockfile (excluded by `.gitignore`). The specific 3 CVE-bearing packages were not enumerated. Notably, the student independently identified the root cause of the audit gap (see `gitignore_gaps.md`) — making this a self-diagnosed partial. |
| 11 | Low | One deprecated package logs a deprecation warning on every backend request | ✅ Found | Root cause + fix | `analysis/repo_hygiene/dependency_health.md` | Identified both `body-parser` (missing `extended` option) and `express-session` (missing `resave`/`saveUninitialized`) deprecation warnings as firing on every request. Provided one-line fixes for each. Also identified CRA/react-scripts as a deprecated project — broader coverage than the answer key. |
| 12 | Medium | Half-completed DB migration: both `documents` and `documents_v2` tables exist with no migration plan, no documentation, and no clear end-state | ✅ Found | Root cause + fix | `analysis/knowledge_gap/two_table_document_architecture.md` | Identified the split read/write pattern (upload → `documents`; list → `documents_v2`), the undocumented trigger, and the complete absence of rationale. Recommended documenting the migration intent and adding a consolidation migration. |
| 13 | High | The `trg_sync_to_v2` trigger copies rows from `documents` to `documents_v2` but deliberately omits the `tags` column — tags submitted at upload time are silently dropped and never reach the frontend | ✅ Found | Root cause + fix | `analysis/bug/upload_trigger_drops_tags.md` | Exact trigger SQL identified, data path traced (upload route → `documents` insert → trigger → `documents_v2` without tags), root cause confirmed. Provided the one-line SQL fix and a data backfill query for existing rows. Runtime verification designed a test confirming the drop. |
| 14 | Medium | Env var configuration is fragmented across `.env`, `.env.development`, `.env.local` (not committed), and hardcoded fallbacks in three different files | ✅ Found | Root cause + fix | `analysis/knowledge_gap/config_system_unused_complexity.md`; `analysis/bug/port_value_conflict.md` | `config_system_unused_complexity.md` identifies `.env.development` as never actually loaded (no `NODE_ENV`-based dotenv path), `pool.js` bypassing `config.js` entirely (dual dotenv loads), and the dangling `databaseUrl` in `config.js` that has no effect. `port_value_conflict.md` documents the 4-way port discrepancy. Together these cover the full env fragmentation picture. |
| 15 | High | The port number is defined in four places (`backend/.env`=3001, `backend/.env.development`=4000, `config.js` fallback=3002, `index.js` fallback=8080) and they do not all agree — when `.env` is not loaded, the backend starts on 3002 while the frontend hardcodes 3001, silently breaking all API calls | ✅ Found | Root cause + fix | `analysis/bug/port_value_conflict.md` | Precise table of all four port values and their resolution conditions. Identified the `|| 8080` in `index.js` as unreachable dead code (because `config.port` always resolves to something first). Recommended "fail fast" approach: no fallbacks, error if PORT missing. |
| 16 | Medium | `DocumentGrid.jsx` is a ~800-line god component containing its own API calls, state management, CSS-in-JS, and a utility function imported by two other components — violating Single Responsibility in at least five distinct ways | ✅ Found | Root cause + fix | `analysis/anti_pattern/god_component_document_grid.md` | Dedicated full analysis. Listed all five violations with line numbers: utility function export (line 1–28), ~400 lines of CSS-in-JS (line 30–430), direct API calls (line 460–510), full tag editor state/logic (line 560–640), complete drag-and-drop upload (line 645–710). Noted `TagEditor.jsx` already exists but is unused. Six-step refactor plan provided. |
| 17 | Low | A utility function (`formatFileSize`) is defined inside `DocumentGrid.jsx` and imported by `DocumentCard.jsx` and `PreviewPanel.jsx`, creating an architectural dependency on a component file for a utility | ✅ Found | Root cause + fix | `analysis/anti_pattern/god_component_document_grid.md` | Explicitly identified in the occurrence table: `DocumentCard.jsx` and `PreviewPanel.jsx` import `formatFileSize` from `DocumentGrid`. Correctly noted this creates a circular-style dependency and recommended moving to `utils/fileHelpers.js` (which already has a version of the function). |
| 18 | Medium | Two separate utility directories (`src/utils/` and `src/lib/`) contain overlapping helper functions with slightly different implementations — different unit bases (1024 vs 1000), different function names, and a second API client with different HTTP library and method names | ✅ Found | Root cause + fix | `analysis/anti_pattern/duplicate_utility_directories.md` | Produced a detailed inventory table of all duplicates across both directories (date formatting, file helpers, API client) with the specific behavioral differences noted. Identified `DocumentGrid.jsx` as a third copy. Recommended deleting `src/lib/` and consolidating to `src/utils/`. |

## Coverage by Category *(mandatory)*

| Category | Total Issues | Found | Partial | Missed | Detection Rate (raw) | Detection Rate (weighted) |
|----------|:-----------:|:-----:|:-------:|:------:|:--------------------:|:-------------------------:|
| It Runs, But… | 1 | 1 | 0 | 0 | 100.0% | 100.0% |
| Overengineered Where It Shouldn't Be | 7 | 7 | 0 | 0 | 100.0% | 100.0% |
| Sloppy Where It Shouldn't Be | 10 | 9 | 1 | 0 | 95.0% | 92.5% |
| **Total** | **18** | **17** | **1** | **0** | **97.2%** | **95.8%** |

<!--
  Sloppy weighted: total weight = 1+3+1+2+3+2+3+2+1+2 = 20
  Scored: 1+1.5+1+2+3+2+3+2+1+2 = 18.5  →  18.5/20 = 92.5%

  Overengineered weighted: total weight = 2+3+2+2+1+2+1 = 13  →  13/13 = 100%

  Total: 34.5 / 36 = 95.8%
-->

## Additional Findings *(student reported findings beyond the answer key)*

| # | Student-Reported Finding | Source in Submission | Classification |
|---|-------------------------|---------------------|----------------|
| 1 | `backend/.env` and `backend/.env.development` are committed to version control with credential-shaped secrets (`JWT_SECRET`, `SESSION_SECRET`, `DATABASE_URL`, `DEV_SKIP_AUTH=true`). Any developer with repo read access can forge JWT tokens and session cookies using these values. | `analysis/repo_hygiene/committed_env_files.md` | Legitimate issue |
| 2 | `.gitignore` only excludes `.env.local` — it does not protect `backend/.env` or `backend/.env.development`, which is the direct root cause of finding #1. The file also incorrectly excludes `package-lock.json` (lock files should be committed for reproducible installs). | `analysis/repo_hygiene/gitignore_gaps.md` | Legitimate issue |
| 3 | The repository contains zero test infrastructure: no test files, no test runner config, no CI pipeline. The three highest-risk untested behaviors are the auth refresh flow, upload-to-`documents_v2` trigger tag persistence, and auth middleware stack behavior. The absence of tests is the likely root cause of both the auth-refresh bug and the trigger-drops-tags bug. | `analysis/repo_hygiene/no_test_infrastructure.md` | Legitimate issue |
| 4 | `admin@docvault.local` credentials with the plaintext password `docvault123` are hardcoded as module-level constants in `auth.js`. `bcrypt.hashSync` is called at module load time, adding 100–300ms to every server restart. The credentials cannot be changed without a code deploy. | `analysis/code_smell/hardcoded_admin_credentials_in_auth_route.md` | Legitimate issue |
| 5 | Three Redux middleware issues in `customMiddleware.js`: (a) `customLogger` mutates action objects directly (`action._timestamp = Date.now()`), breaking Redux immutability and DevTools time-travel; (b) `analyticsTracker` writes to `window.__docvault_action_log`, a global growing array never sent to any analytics service; (c) `errorBoundary` middleware catches all reducer errors and returns `undefined`, silently hiding bugs. | `analysis/code_smell/custom_middleware_mutates_action_objects.md` | Legitimate issue |
| 6 | `frontend/src/components/TagEditor.jsx` is a fully implemented standalone tag-editor component that is never imported anywhere. `DocumentGrid.jsx` contains a parallel inline implementation that is actually used. The extraction was started but never completed. | `analysis/code_smell/unused_tag_editor_component.md` | Legitimate issue |
| 7 | Auth middleware writes to three different `req` properties (`req.auth`, `req.user`, `req.session.user`) with no documented contract for which route handlers should read. The upload route uses `req.user?.email`, which is only populated by session auth and `DEV_SKIP_AUTH` — JWT-authenticated uploads silently produce `uploaded_by = null`. | `analysis/knowledge_gap/auth_middleware_precedence_and_req_user_contract.md` | Legitimate issue |
| 8 | `pool.js` reads `process.env.DATABASE_URL` directly, bypassing `config.js` entirely. This means `config.databaseUrl` is loaded but never consumed. `.env.development` is never programmatically loaded (no `NODE_ENV`-based dotenv path in `config.js`), making it a misleading no-op file. | `analysis/knowledge_gap/config_system_unused_complexity.md` | Legitimate issue |
| 9 | `DEV_SKIP_AUTH=true` is committed as the default value in `backend/.env`, meaning any developer who clones the repo and runs `npm start` immediately runs with all authentication checks disabled. There is no startup warning, no production guard (`NODE_ENV !== 'production'` assertion), and the README's documented default (`false`) contradicts the committed file. | `analysis/knowledge_gap/dev_skip_auth_scope_and_risk.md` | Legitimate issue |

## Missed Issues Detail *(mandatory)*

| # | Category | Severity | Known Issue | Why It Matters |
|---|----------|:--------:|-------------|---------------|
| 1 | Sloppy | High | Three packages in the dependency tree have known CVEs visible via `npm audit` | Known CVEs are documented, actively tracked attack vectors. A single exploitable CVE in a direct dependency requires no custom code to leverage. This is the highest-signal, lowest-effort check in any codebase audit — it requires one command and returns actionable results. The student correctly identified the prerequisite blocker (lockfile excluded from git) but did not cross-reference the CVE databases manually for the specific installed versions. |

*Note: The student self-diagnosed the root cause of this miss in `analysis/repo_hygiene/gitignore_gaps.md` — `package-lock.json` is excluded from `.gitignore`, preventing `npm audit` from running in a fresh clone. This is an unusually self-aware outcome: the student found the reason they couldn't find the issue.*

## Qualitative Assessment *(mandatory)*

### Strengths

- **Near-complete coverage.** 17 of 18 answer-key issues found with zero missed and one self-diagnosed partial. This is the highest detection rate achievable without the lockfile CVE audit, and the student correctly identified why the CVE scan was blocked.
- **Dramatic iteration-over-iteration improvement.** Previous attempt (TAR-0001) missed the entire dependency-health category (3 issues) and partially detected `DocumentGrid`. This iteration closed both gaps — the dependency health analysis is thorough across both package files, and `DocumentGrid` received a dedicated 800-line god-component analysis with line-specific evidence.
- **Root-cause depth throughout.** Every finding includes the exact file and line, the mechanism of failure, and a concrete fix. The search pipeline, fractured authentication, port conflict, and upload trigger findings are all particularly rigorous.
- **High-value additional findings.** 9 legitimate findings beyond the answer key, including two that have direct security implications (committed `.env` secrets, hardcoded admin credentials with sync bcrypt at startup) and one that explains why the student couldn't fully complete the CVE audit (lockfile excluded from git). Finding the cause of your own gap is notable.
- **Methodology breadth.** The analysis covered anti-patterns, bugs, code smells, repo hygiene, knowledge gaps, runtime verification attempts, user flows, architecture diagrams, priority matrix, and roadmap — every category in the analysis framework.

### Areas for Improvement

- **CVE enumeration without a lockfile.** The student correctly noted that `npm audit` couldn't run, but the CVE scan can be completed without a lockfile: install the packages in a scratch environment, or manually cross-reference the specific installed version ranges against the npm advisory database (https://www.npmjs.com/advisories) or NVD. For future iterations, this should be a fallback when `npm audit` is blocked.
- **Runtime verification didn't start the app.** The student self-flagged this in their TAL: "figure out why the verification step is not actually running the app." The runtime verification artifacts are high-quality static predictions but not live tests. Static analysis correctly identified all three behavioral bugs in this codebase — in a harder codebase, timing-sensitive or environment-dependent bugs would be invisible without actually running the server. Resolving this blocker is the highest-leverage improvement for future iterations.
- **Suggested next step:** Restore `package-lock.json` to version control (remove from `.gitignore`), run `npm audit`, and document the specific CVE packages. This closes the only remaining gap.

### Overall Assessment

This is an outstanding second iteration — 97.2% raw / 95.8% weighted, up from 80.6% / 83.3% in the first attempt. The student closed every previously-missed issue, produced a complete god-component analysis that was only partial before, and added nine legitimate findings beyond the answer key. The single remaining gap (CVE enumeration) is notable primarily because the student already found its root cause: the lockfile exclusion in `.gitignore`. With one targeted fix — restoring `package-lock.json` and running `npm audit` — this submission would reach 100% of answer key coverage. The primary development priority for the next iteration is resolving the runtime verification startup blocker, which will become essential as the training exercises increase in complexity.

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-05-05 | automated | TAR-0002 created — grade assessment for tom's second DocVault attempt (TAL-0002, iteration 2) |
