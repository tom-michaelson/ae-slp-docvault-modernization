# Repository Hygiene Finding: Committed .env Files with Credential-Shaped Keys

## Severity

High

## Description

Four environment files containing credential-shaped secret keys are tracked in the repository and committed to version control:

- `backend/.env` — contains `SESSION_SECRET`, `JWT_SECRET`, `DATABASE_URL`, and `DEV_SKIP_AUTH=true`
- `backend/.env.development` — contains `SESSION_SECRET`, `JWT_SECRET`, `DATABASE_URL`
- `frontend/.env` — contains `REACT_APP_API_URL`
- `frontend/.env.development` — contains `REACT_APP_API_URL`

The `backend/.env` file is the most dangerous: it commits `DEV_SKIP_AUTH=true`, which means anyone who clones this repo and starts the backend without overriding this value will run with authentication completely bypassed. The values `docvault-session-secret-change-me` and `docvault-jwt-secret-change-me` are placeholder text but any developer who forgets to replace them ships a predictable, well-known JWT signing secret to production.

The `.gitignore` protects only `.env.local`, leaving `.env` and `.env.development` unprotected.

## Evidence

```
backend/.env:
  PORT=3001
  DATABASE_URL=postgresql://localhost:5432/docvault
  SESSION_SECRET=docvault-session-secret-change-me
  JWT_SECRET=docvault-jwt-secret-change-me
  UPLOAD_DIR=./uploads
  DEV_SKIP_AUTH=true

backend/.env.development:
  PORT=4000
  DATABASE_URL=postgresql://localhost:5432/docvault_dev
  SESSION_SECRET=dev-session-secret
  JWT_SECRET=dev-jwt-secret
  UPLOAD_DIR=./uploads
  NODE_ENV=development
```

Git confirms these are tracked:
```
git ls-files | grep ".env"
→ backend/.env
→ backend/.env.development
→ frontend/.env
→ frontend/.env.development
```

## Recommended Resolution

1. Remove the committed env files from tracking immediately:
   ```bash
   git rm --cached backend/.env backend/.env.development frontend/.env frontend/.env.development
   ```
2. Add to `.gitignore`:
   ```
   .env
   .env.*
   !.env.example
   !.env.local.example
   ```
3. Create `.env.example` files for each package with placeholder values and no real secrets, and commit those instead.
4. Rotate `SESSION_SECRET` and `JWT_SECRET` on any environment where the committed values were ever used.
5. Set `DEV_SKIP_AUTH` only via a local `.env.local` file, never committed.

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Verification Method

Static Analysis

## Notes or Next Steps

- `DEV_SKIP_AUTH=true` in a committed `.env` means the default developer experience runs with no authentication. Any team member who forgets to set their own `.env.local` will have a falsely passing test environment.
- Check CI/CD secrets configuration to ensure these values are not also stored as plain text in pipeline config files.
