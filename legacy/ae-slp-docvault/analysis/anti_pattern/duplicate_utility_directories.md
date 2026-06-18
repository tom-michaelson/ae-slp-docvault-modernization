# Anti-Pattern: Duplicate Utility Directories

## Description

The frontend contains two parallel utility directories — `src/utils/` and `src/lib/` — each containing near-identical implementations of the same three utilities: API client, date formatting, and file helpers. The implementations differ in subtle, incompatible ways that create correctness risks when the wrong version is used.

**`src/utils/api.js`** uses axios with interceptors.
**`src/lib/apiClient.js`** uses the native `fetch` API with different error handling and different function names.

**`src/utils/formatDate.js`** formats dates using `toLocaleDateString` (locale-aware, e.g., "May 27, 2026").
**`src/lib/formatDate.js`** formats dates using ISO string construction (e.g., "2026-05-27 14:30").

**`src/utils/fileHelpers.js`** computes file sizes using binary units (1024-base: 1 KB = 1024 bytes).
**`src/lib/fileHelpers.js`** computes file sizes using SI units (1000-base: 1 kB = 1000 bytes).

The `DocumentGrid.jsx` god component imports from both directories simultaneously, using `utils/` for its primary operations and `lib/` for secondary imports that may not be used at all. Two imported functions from `lib/` (`libFormatDate`, `categorizeFile`, `libGetDocuments`) are imported but their usage within the 800-line component is unclear.

**Verdict: unjustified duplication.**

## Category

Design, Code Quality

## Occurrences

| File | Line | Code Snippet | Description |
|------|------|--------------|-------------|
| `frontend/src/utils/api.js` | 1–45 | axios-based API client | Primary API client |
| `frontend/src/lib/apiClient.js` | 1–65 | fetch-based API client | Duplicate API client with different function names |
| `frontend/src/utils/formatDate.js` | 1–50 | `toLocaleDateString` formatting | Locale-aware date format |
| `frontend/src/lib/formatDate.js` | 1–55 | ISO YYYY-MM-DD HH:mm format | Different date format — incompatible output |
| `frontend/src/utils/fileHelpers.js` | 1–60 | Binary (1024) file size | 1 KB = 1024 bytes |
| `frontend/src/lib/fileHelpers.js` | 1–70 | SI (1000) file size | 1 kB = 1000 bytes — silently different result |
| `frontend/src/components/DocumentGrid.jsx` | 9–15 | `import { formatDate as libFormatDate } from '../lib/formatDate'` | Imports from both directories in same component |

## Impact

- **Correctness risk**: A file size shown as "1.5 MB" using one helper vs "1.6 MB" using the other for the same file is a silent data display inconsistency.
- **Developer confusion**: There is no documented convention for which directory to use. New contributors will pick the wrong one or add a third location.
- **Dead code risk**: The `lib/` imports in `DocumentGrid.jsx` may not be exercised, meaning those code paths are tested less.
- **Bundle size**: Both implementations are bundled, doubling the utility code in the production build.

## Recommended Resolution

1. Pick one canonical utility directory (`src/utils/` is the better choice — it uses the more established axios and locale-aware date formatting).
2. Delete `src/lib/apiClient.js`, `src/lib/formatDate.js`, and `src/lib/fileHelpers.js`.
3. Update all imports that reference `src/lib/` to point to `src/utils/`.
4. Add an ESLint rule or barrel export to prevent future creation of parallel utility trees.

## Verification Method

Static Analysis

## Date Analyzed

2026-05-27

## Notes or Next Steps

- The file size discrepancy (binary vs SI) could affect user-visible file size display if both are rendered in the same session. Audit which components use which helper before removing one.
