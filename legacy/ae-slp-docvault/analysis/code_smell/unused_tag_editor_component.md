# Code Smell: Unused TagEditor Component

## Description

`frontend/src/components/TagEditor.jsx` is a complete, functional React component that implements tag add/remove/save UI. It is never imported by any other file in the codebase.

A search across all frontend source files finds zero `import TagEditor` statements. Instead, `DocumentGrid.jsx` reimplements equivalent tag editor logic inline (approximately 50 lines for state management and 40 lines of JSX render logic), while `TagEditor.jsx` sits unused.

This creates two problems:
1. **Dead code**: `TagEditor.jsx` adds bundle size to the production build while providing no user value.
2. **Duplicate logic**: The tag editor behavior exists in two places — `TagEditor.jsx` (clean, reusable, functional component) and `DocumentGrid.jsx` (embedded in an 800-line god component), with the worse version being the one actually used.

## Recommended Resolution

1. Import `TagEditor` into `DocumentGrid.jsx` and replace the inline tag editor state/logic with the `TagEditor` component.
2. Delete the inline tag editor state fields (`tagEditorVisible`, `tagEditorDocId`, `tagEditorTags`, `tagEditorInput`) and their associated methods from `DocumentGrid`.
3. If `TagEditor` genuinely should not be used, delete the file.

## Location

- **File**: `frontend/src/components/TagEditor.jsx`
- **Line**: 1 (entire file is unused)

## Verification Method

Static Analysis

## Dates

- **Date Identified**: 2026-05-27
- **Date Resolved**: 

## Notes or Next Steps

- This dead component is a direct consequence of the `DocumentGrid` god component anti-pattern. The component was written to extract logic from `DocumentGrid`, but the extraction was never completed.
- See `analysis/anti_pattern/god_component_document_grid.md` for the broader pattern.
