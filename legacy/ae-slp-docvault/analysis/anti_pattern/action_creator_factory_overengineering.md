# Anti-Pattern: ActionCreatorFactory — Unnecessary Abstraction Over Arrow Functions

## Description

`ActionCreatorFactory` is a class that generates Redux action creators by wrapping the trivial arrow function pattern in a factory class with a registry, metadata injection, and multiple method variants. 

Instead of writing the standard Redux pattern:
```js
const setDocuments = (docs) => ({ type: 'SET_DOCUMENTS', payload: docs });
```

A developer must now write:
```js
const factory = new ActionCreatorFactory('documents');
const setDocuments = factory.create('SET_DOCUMENTS', 'documents');
```

And every action created by the factory includes `_meta: { createdBy: 'ActionCreatorFactory', timestamp: Date.now(), payloadKey }` — metadata that is never read by any reducer, middleware, or component in the codebase.

The factory is imported in `store.js` but its instances (`documentActions`, `userActions`, `uiActions`, `filterActions`) are never used to dispatch actual actions — the reducers define their own action type constants locally, and components dispatch plain objects or call those local constants directly.

**Standard equivalent for a single action creator:** `(value) => ({ type: 'SET_DOCUMENTS', documents: value })` — 1 line.
**ActionCreatorFactory equivalent:** 100+ lines of class definition + 1 factory instantiation + 1 method call.

**Verdict: unjustified overengineering.**

## Category

Design, Code Quality

## Occurrences

| File | Line | Code Snippet | Description |
|------|------|--------------|-------------|
| `frontend/src/ActionCreatorFactory.js` | 1–100 | `class ActionCreatorFactory { ... }` | Entire factory class definition |
| `frontend/src/ActionCreatorFactory.js` | 94–98 | `export const documentActions = new ActionCreatorFactory('documents')` | Pre-configured factory instances exported but never used |
| `frontend/src/store.js` | 30 | `import ActionCreatorFactory from './ActionCreatorFactory';` | Imported in store.js but the factory is not called to create any actions used by reducers |
| `frontend/src/ActionCreatorFactory.js` | 37–42 | `_meta: { createdBy: 'ActionCreatorFactory', timestamp: ... }` | Metadata injected into every action; never consumed anywhere |

## Impact

- **Discoverability**: Action types cannot be grepped easily — `factory.create('SET_DOCUMENTS', 'documents')` is harder to trace than `const SET_DOCUMENTS = 'SET_DOCUMENTS'`.
- **Debugging**: The `_meta` fields add noise to every action in Redux DevTools.
- **Onboarding**: A new developer must read and understand the factory class before modifying any Redux state.
- **Dead code**: The exported factory instances (`documentActions`, `userActions`, etc.) are never used to dispatch any action, making the entire module effectively dead code in the current codebase.

## Recommended Resolution

1. Delete `ActionCreatorFactory.js`.
2. Define action type constants as simple string constants in each reducer file (already the pattern in `userReducer.js`, `authReducer.js`, etc.).
3. Write action creators as plain arrow functions where needed.
4. If Redux Toolkit is adopted (recommended), use `createSlice` which generates action creators automatically.

## Verification Method

Static Analysis

## Date Analyzed

2026-05-27

## Notes or Next Steps

- The factory's exported instances are imported by `store.js` but no dispatch site in any component uses them. They can be safely deleted.
