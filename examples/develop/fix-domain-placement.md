# Fix Domain Placement

Move Java classes that are in invalid domain packages to the correct domain, updating all package declarations and imports across the codebase.

## Usage

```
/fix-domain-placement validation_result_file: [path] domain_registry_file: [path]
```

## Input

- `validation_result_file`: Path to `domain-validation-result.json` containing the violations to fix
- `domain_registry_file`: Path to `domain-registry.json` containing the list of valid domains with descriptions

**First step**: Read both files to understand what needs to be fixed and what domains are available.

## Critical Guidelines

**DO:**
- Read the domain registry to understand each domain's purpose and when to use it
- For each violation, analyze the class (imports, annotations, what it extends, its business purpose) to determine the correct domain
- Move the file to the correct domain package directory
- Update the `package` declaration in the moved file
- Find and update ALL import statements across the entire `passage-api/src` tree that reference the old package
- Run `grep -rl --include="*.java" "old.package.ClassName" passage-api/src/` to find all references before and after fixing
- Update the `domain-validation-result.json` with `suggestedDomain`, `confidence`, and `reason` for each violation
- Run spotless after all moves: `cd passage-api && ./gradlew spotlessApply -x checkstyleMain -x checkstyleTest`
- Commit changes with a descriptive message

**DO NOT:**
- Create new domain packages that are not in the domain registry
- Refactor or restructure code beyond moving it to the correct package
- Change class names, method signatures, or business logic
- Split a class across multiple domains — move the whole file
- Move files that are already in valid domains
- Guess randomly — if you genuinely cannot determine the correct domain, mark it as unresolved

## Process

### 1. Read Input Files

Read the `validation_result_file` to get the list of violations. Read the `domain_registry_file` to understand:
- What domains exist and their purpose (the `description` field)
- What sub-domains are valid under each domain
- What non-domain packages are allowed (`allowedNonDomainPackages`)

### 2. Analyze Each Violation

For each violation in the `violations` array:

1. **Read the class file** at `filePath`
2. **Understand its purpose** by examining:
   - Class name and annotations (`@Service`, `@Repository`, `@Controller`, `@Entity`, etc.)
   - What it imports — which other domain packages does it depend on?
   - Its business logic — what data/operations does it deal with?
   - Its relationships — what entities, services, or repositories does it use?
3. **Match to a domain** by comparing the class's purpose against each domain's `description` in the registry
4. **Assess confidence**:
   - **high**: The class clearly belongs to one domain (e.g., a `NominationService` belongs in `nominations`)
   - **medium**: The class could fit 2 domains but one is a better fit
   - **low**: The class touches multiple domains and placement is ambiguous

### 3. Move Files (High/Medium Confidence Only)

For each violation where you determined a domain with high or medium confidence:

1. **Create the target directory** if it doesn't exist:
   ```
   passage-api/src/main/java/com/williams/api/{correct_domain}/{layer}/
   ```
   Where `{layer}` is the architectural layer (service, entity, repository, dto, etc.)

2. **Move the file** (ensure the target directory exists first):
   ```bash
   mkdir -p $(dirname {new_path})
   git mv {old_path} {new_path}
   ```
   Verify `git mv` succeeded (exit code 0). If it fails, check that the source file exists and the target directory was created.

3. **Update the package declaration** in the moved file:
   ```java
   // OLD: package com.williams.api.wrongdomain.service;
   // NEW: package com.williams.api.correctdomain.service;
   ```

4. **Find and update all imports** referencing the old package:
   ```bash
   grep -rl --include="*.java" "com.williams.api.wrongdomain.ClassName" passage-api/src/
   ```
   Update each file's import statement to use the new package.

5. **Check for Spring component scanning** — if the application uses package-specific `@ComponentScan`, ensure the new package is covered.

### 4. Handle Low Confidence / Unresolved

For violations where you cannot confidently determine the domain:

1. **Do NOT move the file**
2. **Update the validation result** with:
   - `suggestedDomain`: Your best guess (or null if truly uncertain)
   - `confidence`: "low"
   - `reason`: Explanation of why placement is ambiguous (e.g., "Class handles both billing calculations and contract rate lookups — could belong in 'billing' or 'contracts'")

### 5. Update Validation Result

Rewrite the `validation_result_file` with updated fields for each violation:
- Set `suggestedDomain` to the domain you moved the file to (or your best guess)
- Set `confidence` to "high", "medium", or "low"
- Set `reason` to your analysis
- Remove violations that were successfully resolved (file moved to valid domain)
- Keep violations that are unresolved
- Update `unresolvedCount` to reflect remaining violations
- Set `valid` to `true` if no violations remain

### 6. Format Code

Run spotless to fix any formatting issues from the moves:

```bash
cd passage-api && ./gradlew spotlessApply -x checkstyleMain -x checkstyleTest
```

### 7. Commit

Commit with a descriptive message:

```
fix: move misplaced classes to correct domain packages

- Moved FooService from 'wrongdomain' to 'correctdomain'
- Moved BarRepository from 'wrongdomain' to 'correctdomain'
- Updated N import references across the codebase
```

## Domain Selection Guide

When analyzing a class to determine its domain, consider:

| Signal | What it tells you |
|--------|-------------------|
| Entity annotations (`@Table`, `@Entity`) | Look at the table name — which business area owns this data? |
| Service dependencies | What repositories/services does it inject? Follow the data. |
| Controller URL paths | `/api/v1/nominations/...` → nominations domain |
| Business terms in class/method names | "Nomination", "Confirm", "Invoice", "Tariff" → obvious domain |
| Cross-cutting concerns | Logging, auth, caching, error handling → `common` package |

**When in doubt**: Follow the data. The domain that owns the primary entity/table being operated on is usually the correct domain.

## Output

After fixing, update the `domain-validation-result.json` and describe what was done:

```
Fixed domain placement violations:

1. NominationService.java: moved from 'foobar' to 'nominations' (high confidence)
   - Reason: Service operates on NOM_CYCLE and NOM_DETAIL tables
   - Updated 5 import references

2. UnknownHelper.java: UNRESOLVED (low confidence)
   - Best guess: 'general'
   - Reason: Utility class used by both billing and scheduling — ambiguous ownership

Resolved: 1 of 2 violations
Remaining: 1 violation needs human review
```
