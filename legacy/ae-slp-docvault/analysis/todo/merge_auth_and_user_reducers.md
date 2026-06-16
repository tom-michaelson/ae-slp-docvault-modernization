# TODO: Merge Auth and User Reducers

## Description

Three TODO comments in `frontend/src/store.js` track the intent to merge `authReducer` into `userReducer`, `uploadReducer` into `documentsReducer`, and `searchReducer` into `filtersReducer`. These were left as action items during an abandoned refactor with a vague timeline of "sprint 14, maybe?"

## Original Comment

```
// TODO: check which components read from state.auth
// TODO: check which components read from state.user
// TODO: merge them (sprint 14, maybe?)
```

## Location

- **File**: `frontend/src/store.js`
- **Line**: 72–74

## Priority

Medium

## Estimated Effort

Medium (1–4 hours)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- A grep for `state.auth` and `state.user` in component files would resolve the first two TODOs quickly. No components currently connect to Redux for auth state — `AuthContext.jsx` manages auth independently.
- The merge is straightforward once the dependency audit is done: `authReducer` tracks `isAuthenticated` and `token`; `userReducer` tracks `currentUser` and `isLoggedIn`. They can be consolidated into one.
- See `analysis/anti_pattern/state_overengineering_12_reducers.md`.
