---
model: opus
---

# Fix Build Errors

Fix compilation/build errors in passage-api and/or passage-ui. Make minimal, targeted changes only.

## Usage

```
/fix-build-errors error_files: [file paths] task_list: [path]
```

## Input

- `error_files`: Comma-separated file paths containing build errors (e.g., `docs/e2e-testing/results/{page_id}/api-build-errors.txt`, `docs/e2e-testing/results/{page_id}/ui-build-errors.txt`)
- `task_list`: Path to task list for context on what was being implemented

**First step**: Read the error file(s) to understand what needs to be fixed. Empty files indicate no errors for that project.

## Critical Guidelines

**DO:**
- Read the specific file(s) with errors
- Fix type errors, import errors, syntax errors
- Make the minimal change to pass build
- Commit each fix with a descriptive message

**DO NOT:**
- Refactor or restructure code
- Add new functionality
- Change working code that isn't causing errors
- Make speculative improvements
- Touch files unrelated to the errors
- Rewrite large sections of code

## Process

### 1. Read Error Files

Read each error file provided in `error_files`. Skip any empty files (they indicate that project built successfully).

### 2. Parse Errors

For each non-empty error file, identify:
- Which project has errors (`passage-api`, `passage-ui`, or both)
- Which file(s) have errors
- What type of error:
  - `TS2345`, `TS2339`, etc. - TypeScript type errors
  - `TS2307` - Cannot find module (import errors)
  - `SyntaxError` - Syntax issues
  - Other compilation errors
- The specific line numbers

### 3. Analyze Each Error

For each file with errors:

1. **Read the file** at the error location
2. **Understand the error** - what is the compiler complaining about?
3. **Identify the minimal fix**:
   - Missing import? Add the import
   - Type mismatch? Fix the type or add proper casting
   - Missing property? Add the property or fix the reference
   - Syntax error? Fix the syntax

### 4. Apply Fixes

For each fix:

1. Make the smallest possible change that resolves the error
2. Ensure you don't introduce new errors
3. Do NOT change the logic or behavior of working code

### 5. Commit

Commit with a message describing what was fixed:

```
fix: resolve build errors in [project]

- Fixed [brief description of fix 1]
- Fixed [brief description of fix 2]
```

## Common Error Patterns

### Angular / TypeScript (passage-ui)

#### TypeScript Type Errors (TS2345, TS2322, etc.)

```typescript
// Error: Type 'string' is not assignable to type 'number'
// Fix: Ensure correct type or add proper conversion
const value: number = parseInt(stringValue, 10);
```

#### Missing Module (TS2307)

```typescript
// Error: Cannot find module './SomeComponent'
// Fix: Check path, add missing export, or create the file
import { SomeComponent } from './SomeComponent';
```

#### Missing Property (TS2339)

```typescript
// Error: Property 'foo' does not exist on type 'Bar'
// Fix: Add the property to the interface or use correct property name
interface Bar {
  foo: string;  // Add missing property
}
```

#### Angular-Specific (NG0xxx errors)

```typescript
// Error: NG0100 - Expression has changed after it was checked
// Fix: Use ChangeDetectorRef or restructure async logic

// Error: NG0200 - Circular dependency
// Fix: Break circular imports, use forwardRef if needed
```

#### Angular CLI Build Errors

```
// Error: ERROR in src/app/component.ts - Module not found
// Fix: Check import paths, ensure module is exported in index.ts
```

### Spring Boot / Java (passage-api)

#### Maven Compilation Errors

```java
// Error: cannot find symbol
// Fix: Add missing import or check spelling
import com.example.MissingClass;

// Error: incompatible types
// Fix: Cast correctly or change method signature
String result = (String) someObject;
```

#### Spring Context Errors

```java
// Error: No qualifying bean of type 'X' available
// Fix: Add @Component, @Service, or @Bean annotation

// Error: BeanCreationException
// Fix: Check constructor parameters, ensure dependencies exist
```

#### Maven Build Commands

```bash
# If Maven build fails, the error will show:
# [ERROR] Failed to execute goal org.apache.maven.plugins:maven-compiler-plugin
# Look for "cannot find symbol" or "incompatible types" in the output
```

## Output

After fixing, describe:
1. Which project(s) had errors
2. What specific errors were fixed
3. What changes were made

Example:
```
Fixed build errors in passage-api:
- Added missing import for `CompanyDto` in company.service.ts
- Fixed type mismatch in company.controller.ts:45 (changed string to number)

Fixed build errors in passage-ui:
- Added missing export in components/index.ts
```
