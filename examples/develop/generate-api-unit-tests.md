---
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "cd $CLAUDE_PROJECT_DIR/passage-api && ./gradlew spotlessApply 2>&1 | tail -5"
---

# Generate API Unit Tests

Generate API unit tests for modified/added Java files in the current branch. Uses git diff to discover changed files, reads test-tracking.json for pending test cases, runs JaCoCo coverage analysis to identify gaps, generates JUnit 5 + Mockito tests following project patterns, runs tests in a fix loop (max 5 attempts), and verifies the 85% coverage threshold is met.

## Common Foundation

@generate-unit-tests-common.md

## Usage

```
/generate-api-unit-tests entry_point_folder_path: $ARGUMENTS
```

## Input

| Parameter | Description |
|-----------|-------------|
| `entry_point_folder_path` | Relative path to the entry point folder (e.g., `docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany`). The result JSON will be written here. |

---

## Phase 0: Discover Modified API Files

**Purpose:** Identify Java source files changed in the current branch that need test coverage.

**Steps:**

1. Run `git diff main...HEAD --name-only -- passage-api/src/main/java/` to find committed changes
2. Run `git diff --name-only -- passage-api/src/main/java/` to find uncommitted staged changes
3. Run `git diff --name-only HEAD -- passage-api/src/main/java/` (fallback) to find unstaged changes
4. Merge and deduplicate all results
5. Filter to only `.java` files under `passage-api/src/main/java/com/williams/api/`
6. Exclude files that match JaCoCo exclusion patterns:
   - `**/dto/**` (DTOs)
   - `**/entity/**` or `**/entities/**` (JPA entities)
   - `**/mapper/**` (MapStruct mappers)
   - `**/specification/**` or `**/spec/**` (JPA specifications)
   - `**/config/**` (configuration classes)
   - `**/security/**` (security infrastructure)
   - `**/exception/**` (exception classes)
   - Files with `@Builder` or Lombok-heavy classes (read each file and check for `@Builder` annotation)

**Output:** List of Java source files requiring test coverage analysis.

**Early exit:** If no modified API files are found AND no pending test cases in test-tracking.json, write success result and exit:

```json
{
  "validated": true,
  "notes": "No modified API files found requiring test coverage.",
  "remaining_issues": ""
}
```

Write this to `{entry_point_folder_path}/api-unit-test-result.json` and stop.

---

## Phase 1: Read Tracking File and Merge Targets

**Purpose:** Read test-tracking.json for pending unit test cases and merge with modified file list.

**Steps:**

1. Read `{entry_point_folder_path}/test-tracking.json`
2. Filter `testCases` where `testType` is `unit` AND `status` is `pending`
3. Build combined target list:
   - Files from Phase 0 git diff (coverage gap targets)
   - Source files referenced by pending test cases from test-tracking.json
4. Deduplicate the merged list

---
## Phase 2: Run Existing Tests and Generate Coverage Report

**Purpose:** Establish baseline coverage for the modified files.

**Steps:**

1. For each modified file from Phase 0, check if a corresponding test file exists:
   - Source: `src/main/java/com/williams/api/{domain}/service/XxxService.java`
   - Test:  `src/test/java/com/williams/api/{domain}/service/XxxServiceTest.java`
2. If NO existing test files are found for any modified files:
   - Skip Phase 2 entirely — there is no baseline coverage to measure
   - Log: "No existing tests found for modified files, skipping baseline coverage"
   - Proceed directly to Phase 3 (all files will show 0% coverage)
3. If existing test files ARE found:
   - Run ONLY those test classes (not the full suite):
     `cd passage-api && ./gradlew test --tests "ExistingTestClass1" --tests "ExistingTestClass2" jacocoTestReport`
   - This generates JaCoCo coverage data for just the relevant classes
4. Locate the XML report at `passage-api/build/reports/jacoco/test/jacocoTestReport.xml`

**Error handling:** If Gradle build fails (compilation error), write failure result.
```json
{
  "validated": false,
  "notes": "Build failed before coverage analysis. Fix compilation errors first.",
  "remaining_issues": "Compilation errors prevent test execution."
}
```

Write this to `{entry_point_folder_path}/api-unit-test-result.json` and stop.

---

## Phase 3: Analyze Coverage Gaps

**Purpose:** Parse JaCoCo XML report and identify classes/methods below the 85% threshold in the modified files.

**Steps:**

1. Read `passage-api/build/reports/jacoco/test/jacocoTestReport.xml`
2. For each modified file from Phase 0:
   - Find the corresponding `<package>` and `<class>` elements in the XML
   - Extract line coverage counters: `<counter type="LINE" missed="X" covered="Y"/>`
   - Calculate coverage percentage: `covered / (covered + missed) * 100`
   - If coverage >= 85%, mark file as adequately covered
   - If coverage < 85%, add to the "needs tests" list with:
     - Current coverage percentage
     - List of uncovered methods (from `<method>` elements with missed > 0)
     - Lines that are not covered
3. If all modified files are adequately covered (>= 85%) AND no pending test cases, write success result:

```json
{
  "validated": true,
  "notes": "All N modified files already meet 85% coverage threshold.",
  "remaining_issues": ""
}
```

Write this to `{entry_point_folder_path}/api-unit-test-result.json` and stop.

**Output:** List of files needing additional test coverage, with specific method-level coverage data.

---

## Phase 4: Generate Unit Tests

<THINKHARD>
Think deeply about each file that needs test coverage. Analyze the source code structure, dependencies, business logic, and edge cases before generating any test code.
</THINKHARD>

**Purpose:** Create JUnit 5 + Mockito tests for under-covered code AND pending test cases from test-tracking.json, following the project's established patterns.

**For each file needing tests:**

### Step 1: Read and Analyze Source

Read the source file completely to understand its structure, dependencies, and business logic.

### Step 2: Identify File Type and Test Pattern

| Source File Type | Test Pattern | Annotations | Location |
|-----------------|-------------|-------------|----------|
| Service class (`*Service.java`) | `@ExtendWith(MockitoExtension.class)` | `@Mock` repos/mappers, `@InjectMocks` service | `src/test/java/.../service/` |
| Controller class (`*Controller.java`) | `@WebMvcTest(Controller.class)` | `@MockBean` services, `MockMvc` | `src/test/java/.../controller/` |
| Repository class (`*Repository.java`) | `@DataJpaTest`, `@ActiveProfiles("test")` | `TestEntityManager`, H2 in-memory | `src/test/java/.../repository/` |
| Other classes | Pure JUnit 5 (no Spring) | Direct instantiation | `src/test/java/.../` |

### Step 3: Check for Existing Tests

If a test file already exists for this class:
- Read the existing test file
- Identify which methods are already tested
- Only generate tests for uncovered methods
- Add new test methods to the existing test class (do NOT create a duplicate file)

### Step 4: Generate Test Methods

For each uncovered method and pending test case, generate test methods that:
- Follow the Arrange/Act/Assert pattern
- Test the happy path
- Test error conditions (null inputs, not-found, validation failures)
- Test edge cases (empty collections, boundary values)
- Use `when().thenReturn()` for mocking
- Use `verify()` to confirm interactions
- Use descriptive test method names: `shouldDoXWhenY`
- **Include TC-ID in `@DisplayName`** for tracking-sourced tests: `"TC-{ID}-NNN: should {expected behavior}"`

### Step 5: Service Test Template

```java
@ExtendWith(MockitoExtension.class)
class XxxServiceTest {
    @Mock
    private XxxRepository repository;
    @InjectMocks
    private XxxService service;

    /** TC-{ID}-001: {Test Name} */
    @Test
    @DisplayName("TC-{ID}-001: should return entity when found by id")
    void shouldReturnEntityWhenFoundById() {
        // Arrange
        var entity = new XxxEntity();
        when(repository.findById(1L)).thenReturn(Optional.of(entity));
        // Act
        var result = service.findById(1L);
        // Assert
        assertNotNull(result);
        verify(repository).findById(1L);
    }
}
```

### Step 6: Controller Test Template

```java
@WebMvcTest(XxxController.class)
class XxxControllerTest {
    @Autowired
    private MockMvc mockMvc;
    @MockBean
    private XxxService service;

    @Test
    @DisplayName("TC-{ID}-001: should return OK when get by id")
    void shouldReturnOkWhenGetById() throws Exception {
        when(service.findById(1L)).thenReturn(new XxxDto());
        mockMvc.perform(get("/api/xxx/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").exists());
    }
}
```

---

## Phase 5: Run Tests and Fix Loop

**Purpose:** Execute generated tests and fix any failures in a loop.

**Loop structure (max 5 attempts):**

```
for attempt in 1..5:
    1. Run tests: cd passage-api && ./gradlew test --tests "ClassName" 2>&1 | tee {entry_point_folder_path}/unit-test-results-raw.txt || true
       (run only the specific test classes that were generated/modified)
    2. The raw output file is required for AWA fix loop compatibility
    3. If all tests pass → break loop, proceed to Phase 6
    4. If tests fail:
       a. Capture the failure output
       b. Read the failing test and the source under test
       c. Analyze the failure root cause:
          - Wrong mock setup → fix mock expectations
          - Wrong assertion → fix assertion to match actual behavior
          - Missing dependency mock → add the missing @Mock
          - Compilation error → fix imports, types, method signatures
       d. Apply the fix (edit the test file)
       e. Continue loop
```

**Fix strategy prioritization:**
1. Fix the test (most common — generated test had wrong assumptions)
2. Only fix production code if the test reveals a genuine bug

**If max attempts exhausted and tests still fail:**
- Log which tests still fail and why
- Continue to Phase 6 with partial results

---

## Phase 6: Verify Coverage and Write Result

**Purpose:** Confirm the 85% threshold is met after test generation.

**Steps:**

1. Collect the list of test classes generated/modified in Phase 4 (e.g., `LineServiceTest`, `LineMapperTest`)
2. Run a single combined Gradle command scoped to only those test classes:
   `cd passage-api && ./gradlew test --tests "TestClass1" --tests "TestClass2" jacocoTestReport checkstyleTest`
   - `test --tests`: Runs only the generated/modified test classes (not the full suite)
   - `jacocoTestReport`: Regenerates coverage data
   - `checkstyleTest`: Verifies generated tests comply with Checkstyle rules
3. Parse the JaCoCo XML report for the modified source files
4. Calculate final coverage percentages
5. If checkstyle violations are found, set `validated: false` with details in `remaining_issues`

**Note:** `jacocoTestCoverageVerification` is NOT needed here — Phase 3 already parses coverage XML and checks the 85% threshold manually. Running the Gradle verification task is redundant.

**Update test-tracking.json** per common Phase 5:
- Match TC-IDs in test output to test case entries
- Update status (`passing`/`failing`), `filePath`, and `lastError` for each test case
- Update `unitSummary` counts

**Write result file** to `{entry_point_folder_path}/api-unit-test-result.json`:

```json
{
  "validated": true|false,
  "notes": "Coverage summary — X files checked, Y tests generated, Z% average coverage achieved",
  "remaining_issues": "List of files still under threshold with details (or empty string)"
}
```

**`validated: true`** when:
- All generated tests pass (last test run output contains "BUILD SUCCESSFUL"), AND
- All modified files meet or exceed the 85% threshold
- OR: No modified API files were found (nothing to do)

**`validated: false`** when:
- Any generated tests are still failing after max fix attempts (even if coverage threshold is met)
- One or more modified files are still below 85% after max fix attempts
- Build/compilation errors prevented test execution

---

## Success Criteria

- [ ] Modified API files correctly identified via git diff
- [ ] Pending test cases read from test-tracking.json
- [ ] JaCoCo coverage report generated and parsed
- [ ] Coverage gaps identified for modified files only
- [ ] Unit tests generated following project patterns (service, controller, repository)
- [ ] TC-ID included in @DisplayName for tracking-sourced tests
- [ ] Tests pass after generation (or after fix loop, max 5 attempts)
- [ ] Coverage threshold (85%) verified
- [ ] Result JSON written to `api-unit-test-result.json`
- [ ] test-tracking.json updated with TC-ID results
- [ ] No existing tests broken by new test additions
- [ ] Generated tests pass Spotless formatting (via PostToolUse hook) and Checkstyle (`./gradlew checkstyleTest`)

## Error Handling

| Scenario | Behavior |
|----------|----------|
| No modified files | Early success exit (`validated: true`) |
| Build/compilation failure | Early failure exit (`validated: false`) with message |
| JaCoCo report missing | Run `./gradlew jacocoTestReport` to generate; fail if still missing |
| Fix loop exhaustion | Report partial success with `remaining_issues` listing still-failing tests |
| Existing test failures | Note them but don't block — only newly generated tests must pass |
| H2 compatibility | For repository tests, use only SQL constructs compatible with H2 MSSQLServer mode |

## Logging

- Log each phase start/end with summary
- Log file-level coverage analysis results
- Log each test generation action (created new file vs. added to existing)
- Log each fix loop attempt with the specific failure and fix applied
