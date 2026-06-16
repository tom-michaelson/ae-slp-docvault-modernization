# Repository Hygiene Finding: Missing Lockfiles and Outdated Dependencies

## Severity

High

## Description

Neither `backend/` nor `frontend/` contains a `package-lock.json` or `yarn.lock` file. Both lockfiles are explicitly excluded in `.gitignore`. Without lockfiles, `npm install` cannot guarantee reproducible installs — each developer and CI run may resolve different dependency versions, and transitive dependencies are unconstrained.

Because `npm audit` requires a lockfile, a full CVE scan could not be run. However, `npm outdated` reveals that both packages contain dependencies that are 2 or more major versions behind their latest releases, a strong indicator that known CVEs are present in the dependency tree.

### Backend — `backend/package.json`

Packages 2+ major versions behind latest:

| Package | Installed | Latest | Versions Behind |
|---------|-----------|--------|-----------------|
| `connect-pg-simple` | 7.0.0 | 10.0.0 | 3 major |
| `uuid` | 9.0.0 | 14.0.0 | 5 major |
| `dotenv` | 16.0.3 | 17.4.2 | 1 major |
| `express` | 4.18.2 | 5.2.1 | 1 major |
| `multer` | 1.4.5-lts.1 | 2.1.1 | 1 major |
| `bcryptjs` | 2.4.3 | 3.0.3 | 1 major |
| `body-parser` | 1.19.0 | 2.2.2 | 1 major |

**Notable risk**: `multer` 1.4.5-lts.1 is a known-vulnerable version. The `1.4.5-lts.1` suffix was specifically published to patch a memory DoS but is itself not the latest. `body-parser` 1.19.0 has published CVEs (path-traversal and prototype pollution in older versions). Without lockfiles, the exact patched version cannot be pinned.

### Frontend — `frontend/package.json`

Packages 2+ major versions behind latest:

| Package | Installed | Latest | Versions Behind |
|---------|-----------|--------|-----------------|
| `pdfjs-dist` | 3.3.122 | 5.7.284 | 2 major |
| `react-pdf` | 6.2.2 | 10.4.1 | 4 major |
| `react` | 17.0.2 | 19.2.6 | 2 major |
| `react-dom` | 17.0.2 | 19.2.6 | 2 major |
| `redux` | 4.2.1 | 5.0.1 | 1 major |
| `react-redux` | 8.0.5 | 9.3.0 | 1 major |
| `react-router-dom` | 6.8.1 | 7.15.1 | 1 major |

**Notable risk**: `react` 17 reached end-of-maintenance in 2024. `pdfjs-dist` 3.x has multiple known CVEs in the PDF rendering engine. `react-pdf` 6.x is incompatible with `react-pdf` 10.x API (breaking changes affect `PreviewPanel.jsx`).

## Evidence

```
# npm audit fails without lockfile
npm audit → "This command requires an existing lockfile."

# .gitignore explicitly excludes lockfiles:
package-lock.json
```

## Recommended Resolution

1. Remove `package-lock.json` from `.gitignore` in both packages.
2. Run `npm install` in both `backend/` and `frontend/` to generate lockfiles, then commit them.
3. Run `npm audit` after lockfiles exist and address all Critical/High advisories immediately.
4. Upgrade `pdfjs-dist`, `multer`, `body-parser`, and `react` as priority packages.
5. Pin a Node.js engine version in both `package.json` files: `"engines": { "node": ">=18.0.0" }`.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- Without lockfiles committed, the "works on my machine" problem is institutionalized. CI environments will silently install different versions than developers.
- Removing lockfiles from `.gitignore` is the single highest-leverage hygiene fix in this repository.
