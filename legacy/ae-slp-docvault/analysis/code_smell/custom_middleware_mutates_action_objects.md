# Code Smell: Custom Logger Middleware Mutates Redux Action Objects

## Description

The `customLogger` middleware in `frontend/src/middleware/customMiddleware.js` mutates incoming action objects directly before passing them to reducers:

```js
action._timestamp = Date.now();
action._sequence = actionCount;
const result = next(action);
```

Mutating Redux actions is a violation of the immutability contract that Redux depends on. While Redux does not enforce action immutability at runtime, mutating actions:
- Breaks time-travel debugging in Redux DevTools (replayed actions will have the wrong timestamps).
- Pollutes the action type contract — reducers and middleware that inspect action shape see unexpected `_timestamp` and `_sequence` fields.
- Creates subtle bugs if an action object is reused or dispatched multiple times.

Additionally, the `errorBoundary` middleware silently swallows reducer errors by catching exceptions and returning `undefined`:
```js
} catch (err) {
  console.error('[DocVault Redux] Error in reducer for action:', action.type, err);
  return undefined; // Swallows the error
}
```

Returning `undefined` from a middleware causes the Redux store state to become `undefined` for all keys, which will crash every connected component on the next render. Silently swallowing an error is more dangerous than letting it propagate.

## Recommended Resolution

1. Remove `action._timestamp = ...` and `action._sequence = ...` mutations from `customLogger`. If timestamps are needed, create a new action object: `const timestampedAction = { ...action, _timestamp: Date.now() }; return next(timestampedAction);`
2. Remove the `errorBoundary` middleware entirely — React's error boundaries handle component render errors, and reducer errors should not be swallowed.
3. Replace `customLogger` with the `redux-devtools-extension` (already configured in `store.js`) which provides superior logging without mutation.

## Location

- **File**: `frontend/src/middleware/customMiddleware.js`
- **Line**: 26–27 (mutation), 47–52 (error swallowing)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- The `analyticsTracker` middleware writes to `window.__docvault_action_log` but this array is never consumed by any analytics service (see `analysis/todo/connect_analytics_middleware.md`). It adds overhead on every action dispatch.
