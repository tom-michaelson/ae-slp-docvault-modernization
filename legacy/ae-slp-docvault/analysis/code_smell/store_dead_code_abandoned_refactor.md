# Code Smell: store.js — Massive Commented-Out Dead Code Block from Abandoned Refactor

## Description

`frontend/src/store.js` is approximately 215 lines long. Of those, roughly 130 lines (lines 55–185) are commented-out code from an abandoned refactor that attempted to simplify the 12-reducer store down to 4 domains using Redux Toolkit. The refactor was never completed and was left in place with TODO comments referencing "sprint 14, maybe?"

The dead code block contains:
- A `simplifiedReducer` definition that was the intended replacement.
- Three `mergedXReducer` function definitions intended to consolidate redundant reducers.
- An almost-complete RTK (`@reduxjs/toolkit`) implementation with 4 slices and a `configureStore` call.
- A comment explaining the decision not to adopt RTK because "we don't want to add another dependency" — despite RTK being bundled with `create-react-app` and being the official Redux recommendation.
- Three TODOs (`// TODO: check which components read from state.auth`, etc.) that have accumulated without being acted on.

The commented-out code is not documentation — it is ambiguous implementation intent that creates confusion about whether these patterns are aspirational, deprecated, or merely parked.

## Recommended Resolution

1. Delete all commented-out code from `store.js` (lines 55–185 approximately).
2. Either proceed with the RTK migration (recommended) or commit to the current 12-reducer approach and document that decision explicitly.
3. If RTK migration is the goal, create a tracking ticket rather than leaving the half-finished implementation in source.

## Location

- **File**: `frontend/src/store.js`
- **Line**: 55–185

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The commented-out code also serves as unintentional documentation that the current architecture is known to be wrong by the team that wrote it.
- See `analysis/anti_pattern/state_overengineering_12_reducers.md` for the broader pattern issue.
