# Anti-Pattern: State Overengineering — 12 Reducers for 4 State Domains

## Description

The Redux store for DocVault combines 12 reducers via `combineReducers`, while the application's actual state needs are 4 domains: current user, document list, active filters, and UI state. The remaining 8 reducers are either redundant duplicates of an active reducer or completely unused by any component.

**Active reducers (4):** `userReducer`, `documentsReducer`, `filtersReducer`, `uiReducer`
**Redundant reducers (3):** `authReducer` (duplicates `userReducer`), `uploadReducer` (duplicates part of `documentsReducer`), `searchReducer` (duplicates part of `filtersReducer`)
**Unused reducers (5):** `notificationsReducer`, `settingsReducer`, `paginationReducer`, `cacheReducer`, `metadataReducer`

In addition, `store.js` contains approximately 130 lines of commented-out code from an abandoned refactor that attempted to consolidate reducers. The comments include three TODO items and explored Redux Toolkit (RTK) as an alternative — a decision that was explicitly rejected because "we don't want to add another dependency" even though RTK is the officially recommended way to use Redux and is bundled with `create-react-app`.

The ActionCreatorFactory, three custom middleware layers, and the 12-reducer structure add approximately 400 lines of infrastructure code that provides no behavior the standard Redux library does not already provide.

**Standard equivalent for this app's needs:**

```js
// RTK — the official Redux recommendation
import { configureStore, createSlice } from '@reduxjs/toolkit';
// 4 slices, ~80 lines total, replaces 12 reducers + ActionCreatorFactory + custom middleware
```

**Verdict: unjustified overengineering.**

## Category

Architecture, Design

## Occurrences

| File | Line | Code Snippet | Description |
|------|------|--------------|-------------|
| `frontend/src/store.js` | 14–25 | 12 import statements for reducers | All 12 reducers imported regardless of usage |
| `frontend/src/store.js` | 40–51 | `combineReducers({ user, documents, ..., metadata })` | 12 reducers combined; comments note which are redundant/unused |
| `frontend/src/store.js` | 55–185 | Commented-out code block | Entire abandoned RTK refactor left in file |
| `frontend/src/reducers/authReducer.js` | 1–55 | `const initialState = { isAuthenticated, token, ... }` | Duplicates user state already in `userReducer.js` |
| `frontend/src/reducers/notificationsReducer.js` | — | entire file | Unused; no component reads `state.notifications` |
| `frontend/src/reducers/settingsReducer.js` | — | entire file | Unused; no component reads `state.settings` |
| `frontend/src/reducers/paginationReducer.js` | — | entire file | Unused; no component reads `state.pagination` |
| `frontend/src/reducers/cacheReducer.js` | — | entire file | Unused; no component reads `state.cache` |
| `frontend/src/reducers/metadataReducer.js` | — | entire file | Unused; no component reads `state.metadata` |

## Impact

- **Bundle size**: All 12 reducer files are bundled even though 8 are unused or redundant.
- **Performance**: All 12 reducers execute on every dispatched action, including actions they do not handle.
- **Cognitive overhead**: A new developer reading `store.js` must understand all 12 reducers plus the abandoned refactor commentary to confidently modify state.
- **Debugging confusion**: `state.auth` and `state.user` both exist and contain overlapping user data — it is unclear which one is authoritative.
- **Redux DevTools noise**: 12 state keys appear in DevTools for an app with 4 meaningful state domains.

## Recommended Resolution

1. Migrate to Redux Toolkit (`@reduxjs/toolkit`). Delete `customMiddleware.js`, `ActionCreatorFactory.js`, and 8 of the 12 reducer files.
2. Create 4 RTK slices: `userSlice`, `documentsSlice`, `filtersSlice`, `uiSlice`.
3. Remove all commented-out dead code from `store.js`.
4. If RTK adoption is blocked, at minimum: delete the 5 unused reducers, merge `authReducer` into `userReducer`, and remove `store.js` dead code.

## Verification Method

Static Analysis

## Date Analyzed

2026-05-27

## Notes or Next Steps

- The abandoned refactor in `store.js` (lines 55–185 of commented code) is documented separately as a code smell: `analysis/code_smell/store_dead_code_abandoned_refactor.md`.
- `ActionCreatorFactory` is documented separately: `analysis/anti_pattern/action_creator_factory_overengineering.md`.
