# Training Assessment Report: [TAR-0001] — Project B — DocVault

**Report ID**: TAR-0001
**Project**: Project B — DocVault
**Answer Key**: `broken-project-docvault.md`
**Student Submissions**: All markdown files under `analysis/` (anti_pattern/, bug/, code_smell/, repo_hygiene/, knowledge_gap/, document_drift/, architecture_diagram/, runtime_verification/, user_flow/)
**Date Assessed**: 2026-04-22
**Status**: Complete

## Score Summary *(mandatory)*

| Metric | Value |
|--------|:-----:|
| **Total known issues** | 18 |
| **Issues found** | 14 |
| **Issues partially found** | 1 |
| **Issues missed** | 3 |
| **Additional findings (beyond answer key)** | 8 |
| **Detection rate (raw)** | 80.6% |
| **Detection rate (weighted by severity)** | 83.3% |

<!--
  Detection rate (raw)      = (14 + 0.5 × 1) / 18 × 100 = 80.6%
  Detection rate (weighted) = 30 / 36 × 100 = 83.3%
  where weight = severity multiplier (Critical=4, High=3, Medium=2, Low=1)
-->

## Issue Detection Matrix *(mandatory)*

<!--
  Decomposition note: the answer key contains compound bullets. Each independently
  identifiable problem has been decomposed into its own row. The 5 answer-key bullets
  in "Sloppy" yielded 10 rows; the 3 "Overengineered" bullets yielded 7 rows.
  Total decomposed issues: 18.
-->

### It Runs, But…

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 1 | High | Login crashes the frontend — `POST /api/auth/refresh` returns `{ session: {...} }` instead of `{ token, refreshToken }`, causing `TypeError: Cannot read properties of undefined (reading 'split')` in `AuthContext` | ✅ Found | Root cause + fix | `analysis/bug/auth_refresh_wrong_response_shape.md` | Traced the full crash path from `auth.js` return value through `AuthContext.jsx` line ~77. Provided correct JWT-shaped fix. Also corroborated by `runtime_verification/auth_login_and_refresh.md`. |

### Overengineered Where It Shouldn't Be

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 2 | Medium | Three auth systems coexisting on the same pipeline (JWT, session, API key) with no authoritative identity — each checks different headers, fails differently, and the final check accepts whichever one happened to set a value | ✅ Found | Root cause + fix | `analysis/anti_pattern/fractured_authentication.md` | Excellent analysis. Named the "Conflicting Abstractions / Multiple Personalities" anti-pattern, inventoried all three middlewares, explained `req.auth \|\| req.user \|\| req.session.user` ambiguity, and proposed consolidating to JWT-only. |
| 3 | High | API key auth middleware is a stub — `apiKeyAuth.js` always returns HTTP 401 for any request that includes an `X-API-Key` header regardless of the key's value; the `api_keys` table was never created | ✅ Found | Root cause + fix | `analysis/bug/api_key_auth_always_rejects.md` | Correctly identified the stub, the missing table, and the side effect that legitimate JWT clients accidentally sending an API key header are blocked. Provided both remove and implement resolution options. |
| 4 | Medium | Frontend Redux store uses 12 reducers for 4 actual state domains (user, documents, filters, UI) — 3 reducers are redundant and 5 are completely unused by any component | ✅ Found | Root cause + fix | `analysis/anti_pattern/redux_state_overengineering.md` | Identified all 12 reducers by name, classified which are active (4), redundant (3), and unused (5). Named "Speculative Generality" anti-pattern and proposed collapsing to a 4-reducer store. |
| 5 | Medium | `ActionCreatorFactory` — an 80+ line class that generates Redux action creators for a pattern that requires one line per creator; the `_meta` registry it writes is never read | ✅ Found | Root cause + fix | `analysis/anti_pattern/action_creator_factory.md` | Inventoried exactly what the factory adds (`_meta`, registry, `createMulti`), confirmed registry is never read, noted timestamp duplication with `customLogger`. Recommended deleting and replacing with RTK `createAction`. |
| 6 | Low | `store.js` contains a large commented-out "abandoned refactor" block (the file is 200 lines with most of it inactive) | ✅ Found | Root cause + fix | `analysis/code_smell/abandoned_refactor_dead_code_store.md` | Identified the specific block, explained the "Lava Flow" anti-pattern, and recommended deleting the dead code. |
| 7 | Medium | Document search routes every query through a 3-class pipeline (`SearchOrchestrator` → `IndexManager` → `FallbackSearchProvider`) that always ends with a single `ILIKE` SQL query — the intermediate layers add zero observable behavior | ✅ Found | Root cause + fix | `analysis/anti_pattern/unjustified_search_pipeline.md` | Traced each class's contribution, confirmed `IndexManager.isIndexAvailable()` always returns `false`, and confirmed the pipeline is a no-op wrapper around one query. Recommended deleting `IndexManager` and `SearchOrchestrator`. Also produced a comprehensive custom-abstraction inventory covering factory, middleware, and search layers in a single finding. |
| 8 | Low | `SearchOrchestrator.rerank()` sets every result's `score` to `1.0` — the re-ranking step is a no-op that never executes meaningful logic | ✅ Found | Root cause | `analysis/anti_pattern/unjustified_search_pipeline.md` | Explicitly noted that `rerank()` always returns `1.0`, and additionally observed that `FallbackSearchProvider` also sets `score: 1.0`, so two no-ops compound each other. |

### Sloppy Where It Shouldn't Be

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 9 | Low | Dependencies in both packages are 2+ years out of date | ❌ Missed | — | — | No dependency-audit finding was produced. The student did not run or reference `npm audit` output or inspect `package.json` dependency versions. |
| 10 | High | Three packages have known CVEs visible in `npm audit` | ❌ Missed | — | — | No CVE finding was produced. This is the most consequential miss — known security vulnerabilities in dependencies are High severity and require no deep code reading to discover. |
| 11 | Low | One deprecated package logs a warning on every backend request | ❌ Missed | — | — | Not mentioned in any submission. Would be visible from server startup output or `npm install` warnings. |
| 12 | Medium | Half-completed DB migration: both a `documents` and a `documents_v2` table exist with no migration plan, no documentation, and no clear end-state | ✅ Found | Root cause | `analysis/knowledge_gap/dual_table_architecture_rationale.md` | Identified the dual-table split, enumerated all the questions it leaves unanswered (why it exists, end-state, column addition strategy), and recommended an ADR. The focus was on documentation gap rather than risk categorization, but the structural problem was clearly understood. |
| 13 | High | The `trg_sync_to_v2` trigger that copies rows from `documents` to `documents_v2` deliberately omits the `tags` column — tags submitted at upload time are silently dropped and never surface to the frontend | ✅ Found | Root cause + fix | `analysis/bug/upload_tags_silently_dropped.md` | Identified the exact trigger SQL, traced the data path from upload route through trigger to read endpoints, confirmed the silent data loss. Provided the one-line fix and the better long-term solution (collapse dual-table architecture). Corroborated by `runtime_verification/upload_endpoint.md` and `user_flow/upload_document.md`. |
| 14 | Medium | Env var configuration is fragmented across `.env`, `.env.development`, `.env.local` (not committed), and hardcoded fallbacks in three different files — the `.env` files containing `JWT_SECRET`, `SESSION_SECRET`, and `DATABASE_URL` are committed to version control | ✅ Found | Root cause + fix | `analysis/repo_hygiene/committed_env_files.md` § Evidence; `analysis/knowledge_gap/config_load_precedence.md` | Committed secrets were identified and elevated to Critical severity by the student. Config fragmentation (independent dotenv loads in `pool.js` vs `config.js`) was separately documented in `config_load_precedence.md`. Together these fully cover the answer key's env config issue. |
| 15 | High | The port number is defined in four places (`config.js` fallback=3002, `.env` PORT=3001, README, `index.js` fallback) and they do not all agree — when `.env` is not loaded, the backend starts on 3002 while the frontend expects 3001, silently breaking all API calls | ✅ Found | Root cause + fix | `analysis/bug/config_port_fallback_mismatch.md` | Precisely identified the 3002 vs 3001 conflict, the condition under which it manifests, and the fix. Also noted `pool.js` loading dotenv independently as a compounding factor. |
| 16 | Medium | `DocumentGrid.jsx` is a god component at ~800 lines — it contains its own API calls, state management, CSS-in-JS, and a utility function imported by two other components | 🔶 Partial | Symptom only | `analysis/code_smell/duplicate_utility_directories.md` § Notes | The student noted that `DocumentGrid.jsx` exports a utility function used elsewhere, but only in a footnote within the duplicate-utilities finding. The broader god-component problem (API calls, state management, CSS-in-JS colocated in one 800-line component) was not identified as a distinct finding. |
| 17 | Low | A utility function is defined inside `DocumentGrid.jsx` and imported by two other components — leaking internal logic out of a component file | ✅ Found | Root cause | `analysis/code_smell/duplicate_utility_directories.md` § Notes | Noted explicitly: "The NOTE comment in `utils/fileHelpers.js` says the function is also exported from `DocumentGrid.jsx` — this is an additional duplication (God Component pattern) that should be addressed when consolidating." |
| 18 | Medium | Two separate utility directories (`src/utils/` and `src/lib/`) contain overlapping helper functions with slightly different implementations — `fileHelpers.js` uses binary units (1024) in one and SI units (1000) in the other, creating silent behavioral divergence | ✅ Found | Root cause + fix | `analysis/code_smell/duplicate_utility_directories.md`; `analysis/code_smell/duplicate_api_client_modules.md` | Both the helper-function duplication (with the 1024 vs 1000 behavioral difference noted) and the API client duplication were identified in separate focused findings. Recommended deleting the entire `lib/` directory. |

## Coverage by Category *(mandatory)*

| Category | Total Issues | Found | Partial | Missed | Detection Rate (raw) | Detection Rate (weighted) |
|----------|:-----------:|:-----:|:-------:|:------:|:--------------------:|:-------------------------:|
| It Runs, But… | 1 | 1 | 0 | 0 | 100% | 100% |
| Overengineered Where It Shouldn't Be | 7 | 7 | 0 | 0 | 100% | 100% |
| Sloppy Where It Shouldn't Be | 10 | 6 | 1 | 3 | 65% | 70% |
| **Total** | **18** | **14** | **1** | **3** | **80.6%** | **83.3%** |

<!--
  Overengineered weighted: (3+2+2+2+1+2+1) earned / (3+2+2+2+1+2+1) total = 13/13 = 100%
  Sloppy weighted: (2+3+2+3+1+2 found + 0.5×2 partial) / (1+3+1+2+3+2+3+2+1+2 total) = 14/20 = 70%
-->

## Additional Findings *(student reported findings beyond the answer key)*

| # | Student-Reported Finding | Source in Submission | Classification |
|---|-------------------------|---------------------|----------------|
| 1 | `backend/.env` and `backend/.env.development` are committed to version control with credential-shaped secrets: `JWT_SECRET`, `SESSION_SECRET`, `DATABASE_URL`, and `DEV_SKIP_AUTH=true`. If these files are ever populated with real production values and pushed, secrets are permanently in git history. | `analysis/repo_hygiene/committed_env_files.md` | Legitimate issue |
| 2 | `.gitignore` only excludes `.env.local` — it does not exclude `.env` or `.env.development`, which is the direct cause of the committed secrets in finding #1. Recommended negation-based `.gitignore` patterns to protect all env files while preserving `.env.example`. | `analysis/repo_hygiene/gitignore_missing_env_patterns.md` | Legitimate issue |
| 3 | Neither the `backend/` nor `frontend/` package has any test files, test runner configuration, or CI pipeline. The three highest-risk untested behaviors are auth/authorization, file upload (path traversal, MIME bypass), and the search fallback chain. | `analysis/repo_hygiene/no_test_infrastructure.md` | Legitimate issue |
| 4 | `App.jsx` and `AuthContext.jsx` are implemented as React class components in a React 17/hooks-dominant codebase. The class component pattern cannot use hooks directly and is significantly more boilerplate-heavy. `App.jsx` uses the clunky `static contextType` API instead of `useContext`. | `analysis/code_smell/app_jsx_class_component.md` | Legitimate issue |
| 5 | `customLogger` Redux middleware directly mutates the action object (`action._timestamp = Date.now()`), violating Redux immutability conventions and breaking DevTools time-travel. The `errorBoundary` middleware silently swallows all reducer errors (`catch (err) { return undefined }`), hiding bugs in production. The `analyticsTracker` middleware writes to an in-memory log that is never sent anywhere. | `analysis/code_smell/custom_middleware_action_mutation.md` | Legitimate issue |
| 6 | README documents at least 6 behaviors that contradict the actual codebase: API key auth described as working (always 401), JWT login described as end-to-end functional (crashes on refresh), search described as having an index fallback path (index is never available), `npm start` described as distinct from `npm run dev` (identical scripts), and session auth described as being phased out (no plan exists). | `analysis/document_drift/README.md` | Legitimate issue |
| 7 | `multer` file-type validation in the upload route relies solely on the client-reported MIME type (`file.mimetype`). A malicious client can send any file with a spoofed MIME type and bypass the allowlist. No magic-bytes (file signature) check is performed. The student correctly noted the risk is limited because the stored MIME type also becomes `image/jpeg`, reducing XSS risk. | `analysis/runtime_verification/upload_endpoint.md` | Legitimate issue |
| 8 | `config.js` falls back to hardcoded strings `'fallback-session-secret'` and `'fallback-jwt-secret'` if the environment variables are not set. These are weak, predictable secrets — if the app is deployed without a `.env` file, it will start with insecure JWT and session signing keys without any warning or startup failure. | `analysis/knowledge_gap/config_load_precedence.md` | Legitimate issue |

## Missed Issues Detail *(mandatory)*

| # | Category | Severity | Known Issue | Why It Matters |
|---|----------|:--------:|-------------|---------------|
| 1 | Sloppy | Low | Both `backend/` and `frontend/` have dependencies that are 2+ years out of date | Outdated dependencies accumulate breaking changes, drift from security patches, and impose large upgrade costs if left unaddressed. Easily caught with `npm outdated`. |
| 2 | Sloppy | High | Three packages in the dependency tree have known CVEs, visible via `npm audit` | Known CVEs are by definition documented attack vectors. A High-severity CVE in a direct dependency can be exploited without any custom code. This is the most critical miss — it requires no code reading at all, just running `npm audit`. |
| 3 | Sloppy | Low | One deprecated package logs a deprecation warning on every backend request | Deprecated packages receive no security patches and will eventually be removed from npm. A warning on every request also pollutes production logs, masking real errors. Visible from `npm install` or `npm start` output. |

## Qualitative Assessment *(mandatory)*

### Strengths

- **Full sweep of architectural complexity.** Every overengineering issue was found and well-analyzed. The `fractured_authentication.md`, `redux_state_overengineering.md`, `unjustified_search_pipeline.md`, and `action_creator_factory.md` findings are thorough, correctly name the underlying patterns (Conflicting Abstractions, Speculative Generality, unjustified abstraction), and propose concrete resolutions.
- **Root-cause depth across all functional bugs.** All four bug findings (`auth_refresh_wrong_response_shape`, `api_key_auth_always_rejects`, `config_port_fallback_mismatch`, `upload_tags_silently_dropped`) traced the failure from symptom through to the exact line of code responsible, and each included a working fix. The upload tags finding was also corroborated by runtime verification and a user flow diagram — good use of multi-artifact evidence.
- **Discovery beyond the answer key.** The student found 8 legitimate issues not explicitly listed in the answer key, including committed secrets (elevated correctly to Critical), missing `.gitignore` patterns, no test infrastructure, class component migration debt, and MIME type spoofing. These demonstrate analysis depth beyond surface-level code reading.
- **Well-organized, self-contained artifacts.** Each finding file is independently readable with location, evidence, recommended resolution, and cross-references. The priority matrix and architecture diagram are high-quality supplementary deliverables.

### Areas for Improvement

- **Dependency audit was entirely skipped.** The three missed issues (outdated deps, CVEs, deprecated warnings) all come from the same source: running `npm audit` and `npm outdated`. This is one of the fastest, highest-signal checks available — it takes seconds and surfaces known security vulnerabilities without any code reading. Future analyses should treat `npm audit` as a mandatory Phase 0 step alongside repo hygiene.
- **`DocumentGrid.jsx` god component was only partially identified.** The student noticed the utility-function leak but did not investigate the file holistically. An ~800-line React component containing its own API calls, state management, CSS-in-JS, and exported utilities is a significant maintainability issue. The partial detection suggests the analysis workflow may not include a step to flag unusually large single-file components.
- **Prompts not reviewed before submission.** The TAL notes that the `analyze-all` skill was ported from a prior project (ClinicFlow) without review, and the student deferred artifact review until after grading. Two of the three missed issues are the kind that a quick human scan of the generated artifacts would have caught (the priority matrix mentions no CVEs; `npm audit` is not referenced anywhere).

### Overall Assessment

This is a strong submission — 80.6% raw and 83.3% weighted detection with 8 legitimate additional findings is well above average for a first attempt using AI-assisted analysis. The student demonstrated genuine understanding of architectural anti-patterns, correctly identified every overengineering issue, and produced thorough root-cause analysis for all four planted bugs. The primary gap is the complete omission of dependency-health analysis (`npm audit`, `npm outdated`), which is a fast, standardized check that should be part of every codebase assessment regardless of tooling. Adding a dependency-audit step to the Phase 0 analysis workflow would likely push the weighted score above 90%.

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-04-22 | automated | TAR-0001 created — initial grade assessment for tom's first DocVault attempt (TAL-0001) |
