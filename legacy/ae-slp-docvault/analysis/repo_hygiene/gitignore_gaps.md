# Repository Hygiene Finding: .gitignore Missing Patterns for .env Files

## Severity

High

## Description

The `.gitignore` at the repository root protects `.env.local` but does not exclude `.env` or `.env.development`. This allowed all four environment files — `backend/.env`, `backend/.env.development`, `frontend/.env`, and `frontend/.env.development` — to be committed to the repository.

The current `.gitignore` relevant section:
```
# Environment files (local overrides)
.env.local
```

This is insufficient. A developer creating a new `.env` file (the default name for environment config in Node.js projects) will not be warned that it is about to be committed.

Additionally, the `.gitignore` does not exclude `package-lock.json`. While lockfiles are typically committed in application repos, their absence here combined with their gitignore entry means reproducible builds are impossible — `npm install` cannot guarantee consistent package resolution. Separately, there are no entries protecting against accidentally committing IDE state files like `.idea/` (only `.idea/` is listed for JetBrains), but `.vscode/` user-specific files are not excluded.

## Evidence

`.gitignore` current content (relevant sections):
```gitignore
# Dependencies
node_modules/
package-lock.json

# Environment files (local overrides)
.env.local

# Build output
frontend/build/
```

Cross-referenced against committed files:
- `backend/.env` — tracked despite containing secrets
- `backend/.env.development` — tracked despite containing secrets
- `frontend/.env` — tracked despite containing API URLs

## Recommended Resolution

Replace the environment files section of `.gitignore` with:
```gitignore
# Environment files — only commit .example files
.env
.env.*
!.env.example
!.env.*.example
```

Additionally, remove `package-lock.json` from the gitignore if the team decides to commit lockfiles (recommended for reproducible builds), or keep it excluded and document that explicitly.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- Fixing the gitignore alone does not remove the already-committed files; `git rm --cached` must be run first.
- After updating gitignore, verify with `git check-ignore -v backend/.env` to confirm the pattern matches.
