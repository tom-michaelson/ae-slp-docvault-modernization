# Document Drift: README

## Drifted Items

| # | Expected State | Actual State | Date Identified | Date Resolved |
|---|---------------|--------------|-----------------|---------------|
| 1 | README states "The backend runs on port 3001" | `backend/.env.development` sets PORT=4000; `config.js` defaults to 3002; `index.js` falls back to 8080. Port is 3001 only if `backend/.env` loads first and is not overridden. | 2026-05-27 | |
| 2 | README states "Session-based auth — Carried over from v1. Still works and some internal routes rely on it. Plan is to phase this out eventually." | Implied to be optional/legacy. In reality `sessionAuth` is registered globally (`app.use(sessionAuth)`) and cannot be bypassed. It is not optional. | 2026-05-27 | |
| 3 | README states "API key auth — Added for service account integrations. Headers are checked on all `/api` routes." | The API key middleware is a stub that returns 401 for any key. No service account can authenticate. "Integration docs coming soon" implies this is believed to work. | 2026-05-27 | |
| 4 | README states "The middleware stack figures out which one [auth method] is active and sets `req.user` accordingly." | There is no coordination logic. JWT sets `req.auth`; session sets `req.user`; API key always rejects. The auth enforcer ORs all three states with no resolution strategy. | 2026-05-27 | |
| 5 | README states "There's also a custom middleware layer and an `ActionCreatorFactory` that standardizes how we dispatch actions — this saves a lot of boilerplate once you get used to the pattern." | ActionCreatorFactory is imported in `store.js` but its exported instances are never used to dispatch any action in the codebase. The "boilerplate saving" claim is unfounded. | 2026-05-27 | |
| 6 | README states search "Re-ranks results with a pluggable scoring function" | The re-ranking function always sets `score: 1.0` for every result. It is not pluggable and provides no real ranking. | 2026-05-27 | |
| 7 | README states "See `.env.development` for defaults" | `.env.development` has PORT=4000, but the stated default in the README is 3001 (`backend/.env`). The two files have different values. | 2026-05-27 | |
| 8 | README states "You can override locally with `.env.local` (gitignored)" | `.env.local` is in `.gitignore`. However, `backend/.env` and `backend/.env.development` (which contain actual secrets) are NOT in `.gitignore` and ARE committed. | 2026-05-27 | |

## Verification Method

Static Analysis

## Notes or Next Steps

- Items 3 and 4 are particularly dangerous: external integrators reading the README may believe API key auth works and session auth is transparent, neither of which is true.
- The README was likely written before the authentication bugs were introduced and was not updated when the code changed.
