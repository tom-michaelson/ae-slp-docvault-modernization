# Repository Hygiene Finding: No Test Infrastructure

## Severity

High

## Description

There is no automated test infrastructure of any kind in this repository. No test files, no test runner configuration, no CI pipeline that runs tests. The `frontend/package.json` includes `react-scripts test` as a script, but there are no test files in the project for it to discover and run.

A search across all source files found zero files matching any common test naming convention:
- No `*.test.js` / `*.test.jsx` / `*.test.ts` / `*.test.tsx`
- No `*.spec.js` / `*.spec.jsx`
- No `__tests__/` directories
- No `jest.config.*`, `vitest.config.*`, or `mocha.opts`
- No `.github/workflows/` CI configuration
- No `Makefile` with a test target

The three highest-risk untested behaviors in this codebase are:

1. **Authentication flow** — The login-to-token-refresh pipeline contains a confirmed crash bug (POST /api/auth/refresh returns a session-shaped object instead of a JWT, causing a null reference crash in AuthContext). There is no test to catch this regression.

2. **Document upload + tag persistence** — The upload route writes to the `documents` table; a trigger syncs to `documents_v2` but deliberately omits the `tags` column. Tags submitted during upload are silently lost. No test validates that tags survive the upload flow end-to-end.

3. **Search** — The SearchOrchestrator → IndexManager → FallbackSearchProvider pipeline always falls back to a PostgreSQL ILIKE query and re-ranks with a constant score of 1.0. The re-rank function and index-availability check are dead code paths with no test coverage.

## Evidence

```bash
# No test files found
find . -name "*.test.*" -o -name "*.spec.*" | grep -v node_modules
# → (empty)

# No CI workflow
ls .github/workflows/
# → (directory does not exist)

# frontend/package.json has test script but no test files
"scripts": {
  "test": "react-scripts test"
}
```

## Recommended Resolution

1. Add Jest (backend) and React Testing Library + Jest (frontend) to each package.
2. Write at minimum:
   - An integration test for `POST /api/auth/login` → `POST /api/auth/refresh` that asserts the response contains `{ token, refreshToken }`.
   - A unit test for the upload flow that verifies tags are persisted to `documents_v2`.
   - A unit test for `SearchOrchestrator.search()` that verifies results are returned.
3. Add a GitHub Actions workflow (`.github/workflows/test.yml`) that runs both test suites on every push.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- The three untested behaviors listed above are all currently broken or contain known bugs. This is not a coincidence — absent test coverage and bug accumulation are correlated.
- The broken-project-docvault.md confirms `DEV_SKIP_AUTH=true` is the default running mode, which means even manual testing rarely exercises the authentication code path.
