# Anti-Pattern: God Component — DocumentGrid

## Description

`DocumentGrid.jsx` is a single React class component of approximately 800 lines that violates the Single Responsibility Principle across at least five dimensions:

1. **API calls**: Directly calls `fetchDocuments`, `searchDocuments`, `uploadDocument`, and `updateTags` from `utils/api.js`.
2. **State management**: Manages its own state for documents, search query, upload progress, view mode (grid/list), tag editor visibility, and pagination — bypassing the Redux store entirely.
3. **CSS-in-JS styles**: Contains approximately 30 style objects defined inline (a large CSS block), rather than using a stylesheet or styled-components.
4. **Exported utility function**: Exports `formatFileSize()`, which is imported by `DocumentCard.jsx` and `PreviewPanel.jsx`. This means two other components have a hard dependency on this 800-line file for a 5-line utility function.
5. **Tag editor logic**: Implements a full inline tag editor (open/close state, input handling, save logic) that duplicates the purpose of `TagEditor.jsx` (a component that exists but is never used).

The god component pattern creates coupling in all directions: it imports from the duplicate `lib/` utilities as well as `utils/`, making it dependent on both parallel utility trees.

## Category

Design, Code Quality

## Occurrences

| File | Line | Code Snippet | Description |
|------|------|--------------|-------------|
| `frontend/src/components/DocumentGrid.jsx` | 1–800 | Entire file | ~800-line god component |
| `frontend/src/components/DocumentGrid.jsx` | 21–22 | `export function formatFileSize(bytes)` | Utility function exported from a component file |
| `frontend/src/components/DocumentGrid.jsx` | 33–350 | `const styles = { ... }` | ~30 CSS-in-JS style objects embedded in component |
| `frontend/src/components/DocumentGrid.jsx` | 617–660 | `handleOpenTagEditor`, `handleCloseTagEditor` | Tag editor state/logic reimplemented inline |
| `frontend/src/components/DocumentGrid.jsx` | 519–540 | `constructor() { this.state = { ..., tagEditorVisible, ... } }` | 10+ state fields in one component |
| `frontend/src/components/DocumentCard.jsx` | 5 | `import { formatFileSize } from './DocumentGrid'` | Depends on god component for utility |
| `frontend/src/components/PreviewPanel.jsx` | 5 | `import { formatFileSize } from './DocumentGrid'` | Depends on god component for utility |

## Impact

- **Coupling**: `DocumentCard` and `PreviewPanel` cannot be used without importing the entire 800-line `DocumentGrid` module.
- **Testability**: Every unit test for document display must instantiate the god component with all its API call dependencies.
- **Dead code**: `TagEditor.jsx` was written specifically to handle tag editing but was never integrated because `DocumentGrid` already handles it internally.
- **Maintainability**: Changes to styling, tag behavior, upload logic, or document listing logic all require touching the same file.

## Recommended Resolution

1. Move `formatFileSize()` to `utils/fileHelpers.js` (it already exists there as a near-identical implementation). Remove the export from `DocumentGrid.jsx`.
2. Extract CSS-in-JS styles to a `DocumentGrid.module.css` file or a dedicated `DocumentGrid.styles.js`.
3. Extract the tag editor inline implementation and replace it with the existing `TagEditor.jsx` component.
4. Extract the upload logic to an `UploadButton` or `useUpload` hook.
5. Extract API data fetching to a `useDocuments` hook.
6. Convert from class component to functional component with hooks.

## Verification Method

Static Analysis

## Date Analyzed

2026-05-27

## Notes or Next Steps

- `TagEditor.jsx` is a functional component that fully implements the tag UI. It only needs to be imported and connected to avoid duplicating the inline tag editor in `DocumentGrid`.
- See `analysis/code_smell/unused_tag_editor_component.md` for the dead component finding.
