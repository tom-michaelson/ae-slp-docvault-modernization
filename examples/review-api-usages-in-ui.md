---
description: Review and validate UI API usage inventory output at ./docs/entry-points/api-endpoints/<key>/usages/ui.json
argument-hint: "key: [key] location: [location]"
---

# Review API Usages in UI

You are a quality assurance validator tasked with reviewing and correcting the output file from the `inventory-api-usages-in-ui` command.

**IMPORTANT**: You will receive two inputs (matching the inventory command):
1. **key** - A unique slug-style identifier for this endpoint (e.g., "01-my-endpoint")
2. **location** - The location in code of the entry point for this API endpoint

## Objective
Validate that the output file at `./docs/entry-points/api-endpoints/<key>/usages/ui.json` adheres to the expected JSON schema. If violations are found, correct them directly.

## Expected Schema

The file must contain **only** a valid JSON array. Each element must be an object with this exact shape:

```json
[
  {
    "file": "relative/path/to/file.ext",
    "class": "ComponentOrScreenName | null",
    "line": 123
  }
]
```

### Field Requirements

1. **file** (required, string)
   - Must be a repository-relative path to a UI source file
   - Must not contain leading `./`
   - Path separators must be `/` (forward slash)
   - Must point to an actual source file (not generated output like `dist/`, `build/`, `node_modules/`)

2. **class** (required, string or null)
   - Must be either a string containing the class/component/screen name, or `null`
   - Must not be `undefined`, empty string, or missing
   - When present, should represent the nearest enclosing class/component/function/module

3. **line** (required, number)
   - Must be a positive integer (1-based line number)
   - Must not be 0, negative, or non-integer
   - Must not be a string representation of a number

### Additional Validation Rules

4. **JSON validity**
   - File must be valid JSON that can be parsed
   - No trailing commas
   - Proper quote escaping
   - No comments

5. **Uniqueness**
   - No duplicate entries (same file, class, and line)
   - If duplicates exist, keep only one instance

6. **Array structure**
   - Must be a top-level array, not an object or other type
   - Empty results must be represented as `[]`, not `null` or missing file

## Review Process

1. **Read the output file**
   - Load `./docs/entry-points/api-endpoints/<key>/usages/ui.json`
   - If the file doesn't exist, report an error and exit

2. **Validate JSON parsing**
   - Attempt to parse as JSON
   - If parsing fails, report the error and attempt to fix common issues:
     - Trailing commas
     - Unescaped quotes
     - Missing brackets/braces

3. **Validate structure**
   - Ensure root is an array
   - Check each element is an object with exactly the required fields

4. **Validate field types and values**
   - `file`: string, non-empty, valid path format
   - `class`: string or null (not undefined, not empty string)
   - `line`: positive integer

5. **Check for duplicates**
   - Identify entries with identical file, class, and line values
   - Remove duplicates, keeping first occurrence

6. **Normalize paths**
   - Remove leading `./` from file paths
   - Ensure forward slashes are used

7. **Apply corrections**
   - If any violations are found, write the corrected JSON back to the file
   - Preserve 2-space indentation
   - Ensure proper formatting

8. **Report results**
   - If no issues found: "✓ Validation passed: <count> entries are valid"
   - If issues corrected: List each type of issue fixed and write the corrected file
   - If unfixable issues: Report the problems in detail

## Output Format

Provide a clear validation report:

```
Reviewing: ./docs/entry-points/api-endpoints/<key>/usages/ui.json

Issues found:
- [Issue type]: [count] instances
  - [specific details if helpful]

Corrections applied:
- [What was fixed]

Result: ✓ File validated and corrected
Total entries: <count>
```

Or if no issues:

```
Reviewing: ./docs/entry-points/api-endpoints/<key>/usages/ui.json

✓ Validation passed
Total entries: <count>
All entries conform to schema
```

## Critical Notes

- **Directly modify the file** if corrections are needed - do not create a separate report file
- **Preserve the original data** as much as possible - only fix schema violations
- **Do not add or remove legitimate entries** - only fix formatting and type issues
- Use 2-space indentation when writing JSON
- Ensure the file ends with a newline character
