# TODO: Implement Batch Operations

## Description

Three commented-out TODO items in `DocumentGrid.jsx` indicate that batch delete, batch tagging, and batch export were planned features. The code stubs are commented out entirely, suggesting they were never started.

## Original Comment

```
//   // TODO: implement batch delete
//   // TODO: implement batch tagging
//   // TODO: implement batch export
```

## Location

- **File**: `frontend/src/components/DocumentGrid.jsx`
- **Line**: 761–771

## Priority

Low

## Estimated Effort

Large (4+ hours)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- These features require backend API support (no batch endpoints exist). Each would need: a backend route, a frontend selection state mechanism, and UI controls.
- Given the current state of the codebase (login crash, tag loss bug, overengineered state management), batch operations should be deferred until core functionality is stable.
