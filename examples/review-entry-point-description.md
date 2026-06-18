# Review Entry Point Description

Perform a comprehensive quality review of a functional description document, validating completeness, accuracy, and adherence to template standards. Make necessary edits, additions, or corrections to ensure the description accurately represents the entry point.

## Usage

```
/review-entry-point-description path: <path-to-entry-point-analysis-folder>
```

**Example:**
```
/review-entry-point-description path: ./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/
```

## What This Command Does

This command performs a comprehensive quality review of an existing `functional-description.md` file, verifying:

- **Template Compliance**: All required sections present and properly structured
- **Content Completeness**: No missing information, placeholders, or TODO markers
- **Technical Accuracy**: Code references accurate, business logic correctly represented
- **Business Perspective**: Consistent business-focused language throughout
- **Specification Readiness**: Sufficient detail for creating system specifications
- **Cross-Reference Validation**: Inputs/outputs match workflows, database deps documented

The review makes **direct edits** to fix issues, ensuring the final description is production-ready.

## Input Structure

The entry point analysis folder must contain:

```
{entry_point_analysis}/
├── metadata.json              # Entry point metadata
├── call-tree.txt              # Complete call tree
├── code/                      # Extracted code files
├── database-dependencies.json # Database objects used
├── database-dependencies/     # (Optional) Stored proc sub-analyses
└── functional-description.md  # EXISTING description to review
```

**CRITICAL**: This command requires an **existing** `functional-description.md` file. If the file doesn't exist, instruct the user to run `/describe-entry-point` first.

## Output Structure

The command produces the following files:

```
{entry_point_analysis}/
├── functional-description.md           # Reviewed and corrected (modified in place)
├── functional-description.backup.md    # Backup of original before review
└── functional-description-review.md    # Review summary report (NEW)
```

**File Details**:

1. **functional-description.md** - The corrected functional description (modified in place)
2. **functional-description.backup.md** - Backup of original created before any edits
3. **functional-description-review.md** - Comprehensive review report documenting:
   - Issues found during review
   - Actions taken to fix issues
   - Quality metrics (completeness, accuracy, readiness scores)
   - Remaining gaps and uncertainties
   - Recommendations for follow-up

## Review Process

### Phase 1: Pre-Review Setup

1. **Verify file existence**:
   - Check for `functional-description.md`
   - If missing, error and instruct user to run `/describe-entry-point` first
   - If found, create backup: `cp functional-description.md functional-description.backup.md`
2. **Create comprehensive todo list** for review phases
3. **Read supporting files**:
   - metadata.json
   - call-tree.txt
   - database-dependencies.json
   - Scan code/ directory structure
4. **Read existing functional-description.md** in full

### Phase 2: Structural Validation

**Goal**: Ensure document structure matches template exactly

**Validation Checks**:

1. **File Header**:
   - [ ] Title format: `# Functional Description: [Entry Point Name]`
   - [ ] Metadata block present with key, location, type
   - [ ] Metadata values match metadata.json
   - [ ] Proper markdown formatting (blockquote for metadata)

2. **Required Sections Present**:
   - [ ] Executive Summary
   - [ ] Inputs (with all subsections)
   - [ ] Outputs (with all subsections)
   - [ ] Workflows (at least one workflow)
   - [ ] Use Cases (at least one use case)
   - [ ] Database Dependencies Detail
   - [ ] Key Business Rules
   - [ ] Data Validation Rules
   - [ ] Integration Points
   - [ ] Analysis Notes

3. **Optional Sections** (if applicable):
   - [ ] Transaction Boundaries (if transactions exist)
   - [ ] Security Considerations (if security logic exists)
   - [ ] File Inputs/Outputs (if file operations exist)
   - [ ] External System Inputs/Outputs (if external calls exist)
   - [ ] Context/Session Inputs (if session/context used)

4. **Section Ordering**:
   - [ ] Sections appear in template order
   - [ ] Subsections properly nested
   - [ ] Consistent heading levels (## for main, ### for sub)

**Actions**:
- Add missing sections with placeholder content
- Reorder sections to match template
- Fix heading levels and formatting
- Correct metadata discrepancies

### Phase 3: Content Completeness Review

**Goal**: Ensure all sections have substantive content

**Validation Checks**:

1. **No Placeholder Text**:
   - [ ] No "TODO" markers
   - [ ] No "[Description]" placeholders
   - [ ] No empty tables
   - [ ] No "TBD" or "To be determined"
   - [ ] No generic filler like "more details needed"

2. **Executive Summary**:
   - [ ] 2-3 paragraphs minimum
   - [ ] Describes purpose, key functionality, business context
   - [ ] Written in business language, not technical jargon
   - [ ] Provides high-level overview understandable to non-developers

3. **Inputs/Outputs Tables**:
   - [ ] All relevant input types documented (parameters, database, files, external, context)
   - [ ] All relevant output types documented (returns, database, files, external, side effects)
   - [ ] Each table has at least one row (or marked "None")
   - [ ] Tables properly formatted with consistent columns
   - [ ] Business meaning provided for each entry

4. **Workflows**:
   - [ ] At least one workflow present
   - [ ] Each workflow has: Use Case, Actors, Steps, Outcome, Error Conditions
   - [ ] Steps are detailed and business-focused
   - [ ] Steps include code references where helpful
   - [ ] Branching logic documented clearly
   - [ ] Workflows numbered and titled descriptively

5. **Use Cases**:
   - [ ] At least one use case present
   - [ ] Each use case has: Description, User Story, Workflow reference
   - [ ] User stories follow "As a [role], I need to [action] so that [value]" format
   - [ ] Use cases reference specific workflows

6. **Database Dependencies**:
   - [ ] All database objects from database-dependencies.json documented
   - [ ] Each table/view has: Operations, Business Purpose, Key Columns, Access Patterns
   - [ ] Each stored proc has: Purpose, Parameters, Returns, Called From
   - [ ] References to database-dependencies/ subfolder if applicable

7. **Business Rules and Validation**:
   - [ ] Key Business Rules section has substantive content
   - [ ] Data Validation Rules section has substantive content
   - [ ] Each rule references code location
   - [ ] Rules written in business language

**Actions**:
- Fill in missing content by analyzing code/ files
- Replace placeholders with actual descriptions
- Add missing table rows
- Expand thin sections with detail from code analysis
- Cross-reference database-dependencies.json to ensure all DB objects covered

### Phase 4: Technical Accuracy Validation

**Goal**: Verify code references, data flow, and logic are correct

**Validation Checks**:

1. **Code References**:
   - [ ] All code references use format `file.java:line`
   - [ ] Referenced files exist in code/ directory
   - [ ] Line numbers are accurate (or reasonable if approximate)
   - [ ] References point to relevant code for the claim

2. **Call Tree Alignment**:
   - [ ] Workflows follow execution order in call-tree.txt
   - [ ] All major functions in call tree appear in workflows
   - [ ] No significant branches in call tree omitted from workflows
   - [ ] Stored procedure calls documented in workflows

3. **Database Operations**:
   - [ ] Database inputs match SELECT operations in code
   - [ ] Database outputs match INSERT/UPDATE/DELETE operations in code
   - [ ] Stored procedure calls match EXECUTE operations in code
   - [ ] Parameters passed to stored procs documented correctly

4. **Input/Output Consistency**:
   - [ ] Method parameters match actual method signature
   - [ ] Return values match actual return types
   - [ ] Data flow: inputs → processing → outputs makes sense
   - [ ] No undocumented inputs or outputs in code

5. **Business Logic Accuracy**:
   - [ ] Validation rules match actual code logic
   - [ ] Calculations described accurately
   - [ ] Conditional branches described correctly
   - [ ] Error handling paths documented

**Actions**:
- Read code files to verify claims
- Correct inaccurate code references
- Fix misrepresented business logic
- Add missing database operations
- Reconcile discrepancies between description and code

### Phase 5: Business Perspective Review

**Goal**: Ensure document is written for business analysts, not just developers

**Validation Checks**:

1. **Language and Terminology**:
   - [ ] Business terminology used over technical jargon
   - [ ] "Customer" not "object instance"
   - [ ] "Validate address" not "regex pattern match"
   - [ ] "Calculate discount" not "apply arithmetic operator"
   - [ ] Technical terms explained when necessary

2. **Focus on "Why" Not Just "What"**:
   - [ ] Business rules explain business rationale when clear
   - [ ] Workflows describe business purpose of each step
   - [ ] Database operations explain business significance
   - [ ] Validation rules note business impact of violations

3. **User-Centric Framing**:
   - [ ] Use cases framed from user perspective
   - [ ] Workflows describe user journey
   - [ ] Inputs/outputs related to business scenarios
   - [ ] Outcomes stated in business terms

4. **Appropriate Abstraction Level**:
   - [ ] Not too technical (avoid low-level implementation details)
   - [ ] Not too vague (sufficient detail for specs)
   - [ ] Balance between business view and technical accuracy
   - [ ] Code references for verification, not primary explanation

**Actions**:
- Rewrite technical language in business terms
- Add business context to technical operations
- Reframe workflows from business perspective
- Simplify overly technical explanations
- Add "why" rationale to "what" descriptions

### Phase 6: Specification Readiness Assessment

**Goal**: Verify document has sufficient detail for creating system specifications

**Validation Checks**:

1. **Input Specifications**:
   - [ ] All inputs have: type, description, required/optional, business meaning
   - [ ] Parameter constraints documented (formats, ranges, valid values)
   - [ ] Database query conditions documented (WHERE clauses, JOIN logic)
   - [ ] External system contracts documented

2. **Output Specifications**:
   - [ ] All outputs have: type, description, business meaning, conditions
   - [ ] Success/failure conditions clear
   - [ ] Database write operations specify data values
   - [ ] Side effects completely enumerated

3. **Workflow Completeness**:
   - [ ] Each step has sufficient detail to implement
   - [ ] All branching conditions specified
   - [ ] Error handling paths documented
   - [ ] Data transformations described precisely
   - [ ] Transaction boundaries clear

4. **Business Rules as Requirements**:
   - [ ] Each business rule is testable
   - [ ] Validation rules have pass/fail criteria
   - [ ] Rules are unambiguous
   - [ ] Sufficient detail for QA test cases

5. **Integration Contracts**:
   - [ ] Database schema assumptions documented
   - [ ] External system interfaces specified
   - [ ] File formats documented
   - [ ] API contracts clear

**Actions**:
- Add missing detail to inputs/outputs
- Specify conditions and constraints
- Expand workflow steps with implementation detail
- Clarify ambiguous business rules
- Document integration assumptions

### Phase 7: Cross-Reference Consistency

**Goal**: Ensure internal consistency across all sections

**Validation Checks**:

1. **Input/Output to Workflow Mapping**:
   - [ ] All inputs in Inputs section appear in at least one workflow
   - [ ] All outputs in Outputs section appear in at least one workflow
   - [ ] Database operations in Inputs/Outputs match workflow steps
   - [ ] No orphaned inputs/outputs

2. **Use Case to Workflow Mapping**:
   - [ ] Each use case references a specific workflow
   - [ ] Referenced workflows exist
   - [ ] Use case description aligns with workflow description
   - [ ] No workflows without corresponding use cases

3. **Database Dependencies Consistency**:
   - [ ] All tables in Database Dependencies Detail appear in Inputs or Outputs
   - [ ] All database operations in Inputs/Outputs have corresponding detail section
   - [ ] Stored procedures documented in both workflows and detail section
   - [ ] database-dependencies.json objects all documented

4. **Code Reference Consistency**:
   - [ ] Code references in workflows match code/ directory structure
   - [ ] Same code file referenced consistently (same path format)
   - [ ] No broken references to non-existent files
   - [ ] References align with call-tree.txt structure

5. **Business Rules Integration**:
   - [ ] Business rules referenced in relevant workflow steps
   - [ ] Validation rules appear in appropriate workflows
   - [ ] Security considerations reflected in workflows
   - [ ] Transaction boundaries referenced in workflows

**Actions**:
- Add missing cross-references
- Fix mismatched references
- Remove orphaned content
- Ensure bidirectional consistency
- Link related sections

### Phase 8: Formatting and Polish

**Goal**: Professional presentation and readability

**Validation Checks**:

1. **Markdown Formatting**:
   - [ ] Tables properly formatted with aligned columns
   - [ ] Consistent heading styles (## vs ### vs ###)
   - [ ] Proper list formatting (ordered vs unordered)
   - [ ] Code references in backticks: `file.java:123`
   - [ ] Blockquotes for metadata
   - [ ] Horizontal rules between workflows: `---`

2. **Table Formatting**:
   - [ ] All tables have headers
   - [ ] Consistent column count in rows
   - [ ] Proper alignment markers in header separator
   - [ ] No broken table syntax
   - [ ] Consistent use of N/A, None, or "Not applicable"

3. **Writing Quality**:
   - [ ] No spelling errors
   - [ ] No grammatical errors
   - [ ] Consistent terminology (don't switch between terms)
   - [ ] Clear, concise sentences
   - [ ] Active voice preferred over passive

4. **Document Flow**:
   - [ ] Logical progression from section to section
   - [ ] Transitions between major sections
   - [ ] No jarring topic switches
   - [ ] Executive summary accurately previews content

**Actions**:
- Fix markdown syntax errors
- Align table columns
- Correct spelling and grammar
- Improve sentence clarity
- Ensure consistent terminology

### Phase 9: Gap Identification

**Goal**: Identify areas requiring additional investigation

**Validation Checks**:

1. **Missing Context**:
   - Are there code files in call-tree.txt not extracted to code/?
   - Are there database objects referenced in code but not in database-dependencies.json?
   - Are there external systems called but not documented?
   - Are there configuration files or constants not explained?

2. **Uncertain Business Logic**:
   - Are there complex algorithms without clear business purpose?
   - Are there "magic numbers" or hardcoded values unexplained?
   - Are there error codes or status values without business meaning?
   - Are there validation rules without clear rationale?

3. **Incomplete Workflows**:
   - Are there significant code branches not covered by any workflow?
   - Are there error handling paths not documented?
   - Are there async operations or background processes not explained?
   - Are there edge cases not addressed?

**Actions**:
- Document gaps in Analysis Notes section
- Flag areas needing SME review
- Note assumptions made
- Suggest follow-up investigations
- Mark uncertain content for validation

### Phase 10: Final Review and Reporting

**Goal**: Ensure review is complete and document is production-ready

**Final Checks**:

1. **Template Compliance**: All sections present and correctly formatted
2. **No Placeholders**: All content is substantive and complete
3. **Technical Accuracy**: Code references verified, logic correct
4. **Business Perspective**: Consistent business-focused language
5. **Specification Ready**: Sufficient detail for implementation specs
6. **Internal Consistency**: Cross-references valid, no contradictions
7. **Professional Quality**: Well-formatted, clear, readable

**Actions**:

1. **Calculate final quality metrics**:
   - Completeness score
   - Accuracy score
   - Specification readiness score
2. **Compile review findings**:
   - Count issues found by category
   - List major edits made
   - Document remaining gaps
3. **⚡ CREATE: functional-description-review.md**:
   - Write comprehensive review report (see template below)
   - Include all issues found, actions taken, metrics
   - Document recommendations and follow-up items
4. **Verify all deliverables**:
   - functional-description.md updated and complete
   - functional-description.backup.md preserved
   - functional-description-review.md created
5. **Provide summary to user**:
   - Overview of review results
   - File locations
   - Next steps if any

**Deliverables**:

1. **Updated functional-description.md**: Production-ready description
2. **Backup preserved**: functional-description.backup.md for comparison
3. **Review report created**: functional-description-review.md with detailed findings

## Quality Metrics

### Completeness Score

Calculate completeness based on:
- [ ] All required sections present (20%)
- [ ] All inputs documented (15%)
- [ ] All outputs documented (15%)
- [ ] At least one workflow (10%)
- [ ] At least one use case (10%)
- [ ] All database dependencies documented (15%)
- [ ] Business rules documented (10%)
- [ ] No placeholder text (5%)

**Target**: 100% completeness

### Accuracy Score

Assess accuracy through:
- [ ] Code references verified against code/ files (30%)
- [ ] Database operations match database-dependencies.json (25%)
- [ ] Workflows align with call-tree.txt (25%)
- [ ] Business logic correctly represented (20%)

**Target**: 100% accuracy

### Specification Readiness Score

Evaluate readiness via:
- [ ] Sufficient detail for implementation (40%)
- [ ] All business rules testable (30%)
- [ ] Integration contracts specified (20%)
- [ ] No ambiguous requirements (10%)

**Target**: ≥90% readiness

## Review Report Template

The `functional-description-review.md` file should be created at the end of Phase 10 with this structure:

```markdown
# Functional Description Review Report

> **Entry Point**: [key from metadata.json]
> **Review Date**: [current date]
> **Reviewer**: Claude Code Review Agent

## Executive Summary

[2-3 paragraph summary of review findings, overall quality assessment, and major improvements made]

## Quality Metrics

### Before Review

- **Completeness Score**: [score]%
- **Accuracy Score**: [score]%
- **Specification Readiness**: [score]%

### After Review

- **Completeness Score**: [score]%
- **Accuracy Score**: [score]%
- **Specification Readiness**: [score]%

### Overall Assessment

**Status**: [Production Ready / Needs Minor Fixes / Needs Significant Work]

**Readiness for Modernization**: [Ready / Partially Ready / Not Ready]

## Issues Found and Fixed

### Phase 2: Structural Validation

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Missing section: Context/Session Inputs | Medium | Added subsection, marked "None" |
| Incorrect section order: Use Cases before Workflows | Low | Reordered sections |
| [Additional issues...] | | |

### Phase 3: Content Completeness Review

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Placeholder text in Data Validation Rules | High | Analyzed code, added 3 validation rules |
| Executive Summary only 1 paragraph | Medium | Expanded to 3 paragraphs with business context |
| Missing database table in Inputs | High | Added PT_CO_ADDR_XREF documentation |
| [Additional issues...] | | |

### Phase 4: Technical Accuracy Validation

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Incorrect code reference: LookupsService.java:123 | High | Corrected to :125 |
| Missing function in workflow: DataAccessHelper.executeQuery() | Medium | Added workflow step |
| Incorrect database operation: UPDATE vs SELECT | High | Corrected to SELECT only |
| Wrong parameter type: Integer vs String | High | Corrected to String |
| [Additional issues...] | | |

### Phase 5: Business Perspective Review

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Technical jargon: "Instantiate DTO object" | Medium | Changed to business language |
| Missing business rationale for validation | Low | Added business reasoning |
| [Additional issues...] | | |

### Phase 6: Specification Readiness Assessment

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Missing parameter constraints | High | Added format constraints |
| Incomplete error handling documentation | Medium | Added Workflow 2 for error scenario |
| [Additional issues...] | | |

### Phase 7: Cross-Reference Consistency

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Orphaned database input not in workflows | Medium | Added to Workflow 1, Step 4 |
| Broken workflow reference in UC-2 | High | Corrected reference |
| [Additional issues...] | | |

### Phase 8: Formatting and Polish

**Issues Found**: [count]

| Issue | Severity | Action Taken |
|-------|----------|--------------|
| Table alignment issues | Low | Realigned table columns |
| Inconsistent terminology | Medium | Standardized on "company" |
| [Additional issues...] | | |

## Summary Statistics

| Category | Issues Found | Issues Fixed | Remaining |
|----------|--------------|--------------|-----------|
| Structural | [count] | [count] | [count] |
| Content Completeness | [count] | [count] | [count] |
| Technical Accuracy | [count] | [count] | [count] |
| Business Perspective | [count] | [count] | [count] |
| Specification Readiness | [count] | [count] | [count] |
| Cross-Reference | [count] | [count] | [count] |
| Formatting | [count] | [count] | [count] |
| **TOTAL** | **[count]** | **[count]** | **[count]** |

## Major Improvements

### Sections Added

1. [Section name] - [Brief description of why added]
2. [Section name] - [Brief description]
3. ...

### Sections Significantly Expanded

1. **[Section name]**:
   - **Before**: [Brief description of original state]
   - **After**: [Brief description of improved state]
   - **Impact**: [Why this matters]

2. **[Section name]**:
   - **Before**: [Description]
   - **After**: [Description]
   - **Impact**: [Why this matters]

### Critical Corrections

1. **[Issue description]**:
   - **Problem**: [What was wrong]
   - **Fix**: [What was corrected]
   - **Impact**: [Why critical]

2. **[Issue description]**:
   - **Problem**: [What was wrong]
   - **Fix**: [What was corrected]
   - **Impact**: [Why critical]

## Remaining Gaps and Uncertainties

### Items Requiring SME Review

1. **[Topic]**: [Description of uncertainty and what needs clarification]
2. **[Topic]**: [Description]
3. ...

### Missing Context

1. **[Missing item]**: [What's missing and why it's needed]
2. **[Missing item]**: [Description]
3. ...

### Assumptions Made

1. **[Assumption]**: [What was assumed and why]
2. **[Assumption]**: [Description]
3. ...

## Recommendations

### Immediate Actions

1. [Recommendation for immediate follow-up]
2. [Recommendation]
3. ...

### Future Improvements

1. [Suggestion for long-term improvement]
2. [Suggestion]
3. ...

### Follow-Up Analysis Needed

1. **[Analysis type]**: [What additional analysis would be helpful]
2. **[Analysis type]**: [Description]
3. ...

## Files Modified

| File | Modification Type | Description |
|------|-------------------|-------------|
| functional-description.md | Updated | Comprehensive review and corrections |
| functional-description.backup.md | Created | Backup of original |
| functional-description-review.md | Created | This review report |

## Code Files Referenced

| Code File | Purpose | Validation Status |
|-----------|---------|-------------------|
| LookupsService.java | Primary entry point | ✓ Verified |
| DataAccessHelper.java | Database operations | ✓ Verified |
| [Additional files...] | | |

## Database Dependencies Validated

| Database Object | Type | Validation Status |
|-----------------|------|-------------------|
| PT_CO_XREF | Table | ✓ Verified |
| PT_CO_ADDR_XREF | Table | ✓ Verified |
| SP_GET_COMPANY_ADDR | Stored Procedure | ✓ Verified |
| [Additional objects...] | | |

## Review Completion Checklist

- [x] All 9 review phases completed
- [x] Structural validation passed
- [x] Content completeness verified
- [x] Technical accuracy validated
- [x] Business perspective ensured
- [x] Specification readiness confirmed
- [x] Cross-references validated
- [x] Formatting polished
- [x] Gaps documented
- [x] Review report created

## Conclusion

[Final paragraph summarizing the review outcome, document quality, and readiness for use in modernization planning]

---

**Review completed by Claude Code Review Agent**
```

## Review Guidelines

### Scope Management

**Stay Within Scope**:
- Review only the provided functional-description.md
- Use only materials in the entry point analysis folder
- Don't re-analyze the entire codebase from scratch
- Focus on validation and correction, not complete rewrite

**Out of Scope**:
- Adding entirely new entry points
- Analyzing code not in the call tree
- Redesigning the functional description template
- Creating new analysis artifacts

### Edit Philosophy

**When to Edit Directly**:
- Fixing obvious errors (spelling, grammar, formatting)
- Adding missing content that's clearly derivable from existing materials
- Correcting inaccurate code references
- Filling placeholder text with content from code/ files
- Improving business language and clarity

**When to Flag for Review**:
- Contradictions between code and description that aren't easily resolved
- Missing context that requires domain expertise
- Ambiguous business logic that needs SME clarification
- Significant gaps in extracted code
- Complex business rules that need validation

### Incremental Editing

**IMPORTANT**: Make edits incrementally throughout review, not all at once

1. **Edit as you validate**: Fix issues as you encounter them
2. **Save frequently**: Update file after each phase
3. **Track changes**: Use todo list to note edits made
4. **Verify edits**: Re-read edited sections to ensure quality
5. **Preserve original**: Keep backup for comparison

## Subagent Usage

**When to use subagents**:

- **legacy-code-searcher**: Missing code context not in code/ directory
- **symbol-body-extractor**: Need specific function body to verify accuracy
- **code-reference-validator**: Verify code reference accuracy

**Do NOT use subagents for**:
- Re-reading files already in code/ directory
- Re-extracting call tree (already provided)
- Searching for entry point (already identified)

## Task Management

**CRITICAL**: Use TodoWrite tool extensively throughout review:

1. **Initial Review Plan**:
   ```
   - Create backup of functional-description.md
   - Phase 1: Structural validation
   - Phase 2: Content completeness review
   - Phase 3: Technical accuracy validation
   - Phase 4: Business perspective review
   - Phase 5: Specification readiness assessment
   - Phase 6: Cross-reference consistency check
   - Phase 7: Formatting and polish
   - Phase 8: Gap identification
   - Phase 9: Final review
   - Calculate quality metrics
   - Create functional-description-review.md report
   - Validation complete
   ```

2. **Progress Tracking**:
   - Mark each phase as `in_progress` when starting
   - Mark as `completed` when finished
   - Add sub-tasks for specific issues found
   - Track edits made in each phase

3. **Quality Gates**:
   - Verify completeness score after Phase 2
   - Verify accuracy score after Phase 4
   - Verify specification readiness after Phase 6
   - Verify all checks pass before Phase 10

## Success Criteria

**Review Completeness**:
- [ ] All 9 review phases completed
- [ ] All structural validation checks passed
- [ ] All content completeness checks passed
- [ ] All technical accuracy checks passed
- [ ] All business perspective checks passed
- [ ] All specification readiness checks passed
- [ ] All cross-reference consistency checks passed
- [ ] All formatting checks passed
- [ ] All gaps documented

**Document Quality**:
- [ ] Completeness score: 100%
- [ ] Accuracy score: 100%
- [ ] Specification readiness score: ≥90%
- [ ] No placeholder text remaining
- [ ] All required sections present and substantive
- [ ] Professional formatting and presentation

**Output Quality**:
- [ ] functional-description.md updated and production-ready
- [ ] functional-description.backup.md preserved for comparison
- [ ] functional-description-review.md created with comprehensive findings
- [ ] Review report includes all issues found, actions taken, and metrics
- [ ] Remaining gaps clearly documented in both Analysis Notes and review report

## Example Execution

```
User: /review-entry-point-description path: ./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/

Agent Response:

Phase 1 - Pre-Review Setup:
1. Creates comprehensive todo list for review phases
2. Verifies functional-description.md exists
3. Creates backup: functional-description.backup.md
4. Reads metadata.json, call-tree.txt, database-dependencies.json
5. Reads existing functional-description.md
6. Scans code/ directory structure

Phase 2 - Structural Validation:
7. Validates file header and metadata block
   - FOUND: Metadata missing "Type" field
   - FIXED: Added type from metadata.json
8. Validates all required sections present
   - FOUND: Missing "Context/Session Inputs" subsection
   - FIXED: Added subsection (marked "None" - no session inputs found)
9. Validates section ordering
   - FOUND: "Use Cases" section before "Workflows"
   - FIXED: Reordered to match template
10. Validates heading levels
    - ALL CORRECT: No changes needed

Phase 3 - Content Completeness Review:
11. Checks for placeholder text
    - FOUND: "TODO: Add validation rules" in Data Validation Rules
    - FIXED: Analyzed code, added 3 validation rules from LookupsService.java:45-67
12. Reviews Executive Summary
    - FOUND: Only 1 paragraph, too technical
    - FIXED: Expanded to 3 paragraphs, added business context
13. Reviews Inputs/Outputs tables
    - FOUND: Database Inputs table missing PT_CO_ADDR_XREF table
    - FIXED: Added row for PT_CO_ADDR_XREF with business description
14. Reviews Workflows
    - FOUND: Workflow 1 steps lack code references
    - FIXED: Added code references to all 7 steps
15. Reviews Use Cases
    - FOUND: UC-1 missing user story format
    - FIXED: Reformulated as "As a customer service rep, I need to..."
16. Reviews Database Dependencies
    - FOUND: Stored procedure SP_GET_COMPANY_ADDR not documented
    - FIXED: Added full stored proc section with parameters and purpose

Phase 4 - Technical Accuracy Validation:
17. Validates code references
    - FOUND: Reference to LookupsService.java:123 incorrect (should be :125)
    - FIXED: Corrected line number
18. Validates call tree alignment
    - FOUND: DataAccessHelper.executeQuery() in call tree but not in workflow
    - FIXED: Added step in Workflow 1 documenting this operation
19. Validates database operations
    - FOUND: Database Outputs claims UPDATE on PT_CO_XREF, but code only SELECTs
    - FIXED: Removed incorrect UPDATE claim, corrected to SELECT only
20. Validates input/output consistency
    - FOUND: Method parameter "companyCode" documented as Integer, actually String
    - FIXED: Corrected type to String in Inputs table

Phase 5 - Business Perspective Review:
21. Reviews language and terminology
    - FOUND: "Instantiate DTO object" in workflow
    - FIXED: Changed to "Create company address record"
22. Reviews focus on "why"
    - FOUND: Validation rule states "Check length" without business rationale
    - FIXED: Added "to ensure compatibility with legacy system field size limits"
23. Reviews user-centric framing
    - FOUND: Use case states technical outcome "returns JSON"
    - FIXED: Changed to "provides customer address information for display"

Phase 6 - Specification Readiness Assessment:
24. Validates input specifications
    - FOUND: Parameter constraints not documented
    - FIXED: Added format constraints (e.g., "5-digit numeric string")
25. Validates workflow completeness
    - FOUND: Error handling path "invalid company code" mentioned but not detailed
    - FIXED: Added Workflow 2 for error scenario with full steps

Phase 7 - Cross-Reference Consistency:
26. Validates input/output to workflow mapping
    - FOUND: Database input "PT_CO_ADDR_XREF" not mentioned in any workflow
    - FIXED: Added to Workflow 1, Step 4
27. Validates use case to workflow mapping
    - FOUND: UC-2 references "Workflow 3" which doesn't exist
    - FIXED: Corrected to "Workflow 2"
28. Validates database dependencies consistency
    - ALL CORRECT: All DB objects in database-dependencies.json documented

Phase 8 - Formatting and Polish:
29. Validates markdown formatting
    - FOUND: Table alignment issues in Outputs section
    - FIXED: Realigned table columns
30. Reviews writing quality
    - FOUND: Inconsistent terminology ("company" vs "organization")
    - FIXED: Standardized on "company" throughout
31. Reviews document flow
    - ALL GOOD: Logical progression maintained

Phase 9 - Gap Identification:
32. Identifies missing context
    - NOTED: Error code "ERR_404" referenced but meaning not documented
    - ADDED TO ANALYSIS NOTES: "Error codes need business meaning documentation"
33. Identifies uncertain business logic
    - NOTED: Magic number "90" in date calculation - unclear business rule
    - ADDED TO ANALYSIS NOTES: "Clarify 90-day business rule with SME"

Phase 10 - Final Review and Reporting:
34. Performs all final checks
    - Template Compliance: ✓ PASS
    - No Placeholders: ✓ PASS
    - Technical Accuracy: ✓ PASS
    - Business Perspective: ✓ PASS
    - Specification Ready: ✓ PASS
    - Internal Consistency: ✓ PASS
    - Professional Quality: ✓ PASS
35. Calculates quality metrics
    - Completeness: 85% → 100%
    - Accuracy: 90% → 100%
    - Specification Readiness: 75% → 95%
36. Creates functional-description-review.md with:
    - Executive summary of review
    - Quality metrics before/after
    - All 23 issues found and fixed by phase
    - Summary statistics table
    - Major improvements made
    - 2 remaining gaps documented
    - Recommendations for follow-up

Result: Functional description reviewed and corrected at:
./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/functional-description.md

Backup preserved at:
./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/functional-description.backup.md

Review report created at:
./docs/entry-points/api-endpoints/789-spring-lookupsservice-getcompanyaddrs/functional-description-review.md

Review Summary:
- Completeness Score: 100% (was 85%)
- Accuracy Score: 100% (was 90%)
- Specification Readiness: 95% (was 75%)
- Issues Fixed: 23
  - Structural: 4
  - Content: 8
  - Accuracy: 6
  - Business Perspective: 3
  - Cross-Reference: 2
- Gaps Identified: 2 (documented in Analysis Notes and review report)
```

## Advanced Features

### Diff Generation

For transparency, consider generating a diff report:

```bash
# After review, show changes made
diff functional-description.backup.md functional-description.md > review-changes.diff
```

This helps users understand what was changed.

### Progressive Quality Improvement

For very poor quality initial descriptions:

1. **First pass**: Fix critical structural and completeness issues
2. **Second pass**: Address accuracy and business perspective
3. **Third pass**: Polish and cross-reference consistency

Break review into multiple passes if needed.

### Collaborative Review

When gaps require SME input:

1. **Document clearly** in Analysis Notes
2. **Flag specific questions** for domain experts
3. **Suggest interim assumptions** where applicable
4. **Mark sections** needing validation with comments

## Troubleshooting

### Missing functional-description.md

**Problem**: No functional-description.md found in entry point folder

**Solution**:
1. Check for functional-description.in-progress.md
   - If found, this means previous analysis crashed
   - Use it as starting point for review
2. If no description file exists at all:
   - Error to user
   - Instruct to run `/describe-entry-point` first

### Contradictory Information

**Problem**: Code says one thing, description says another

**Solutions**:
1. **Re-read code** to verify actual behavior
2. **Check call tree** for context
3. **Read database-dependencies.json** for DB truth
4. **Correct description** to match code reality
5. **Document uncertainty** if code is ambiguous

### Extensive Rewrites Needed

**Problem**: Description is so poor it requires complete rewrite

**Solutions**:
1. **Assess severity**: Is it faster to rewrite or fix?
2. **If minor issues**: Fix incrementally as planned
3. **If major issues**: Consider flagging for `/describe-entry-point` re-run
4. **Document decision** in review summary

### Missing Code Files

**Problem**: Description references code not in code/ directory

**Solutions**:
1. **Check call-tree.txt**: Should this code be included?
2. **Use symbol-body-extractor**: Extract missing code if relevant
3. **Update description**: Reference available code only
4. **Document gap**: Note missing context in Analysis Notes

## Notes for Command Implementation

### Parameter Parsing

The command accepts a single parameter:

```
path: <entry-point-analysis-folder-path>
```

Same format as `/describe-entry-point`.

### Validation Before Execution

Before starting review, verify:

1. Path exists and is a directory
2. Required file present: **functional-description.md**
3. Supporting files present:
   - metadata.json
   - call-tree.txt
   - code/ directory
4. Optional files:
   - database-dependencies.json
   - database-dependencies/ folder

If functional-description.md missing, provide clear error.

### Backup Strategy

Always create backup before making changes:

```bash
cp functional-description.md functional-description.backup.md
```

Preserve backup even after review completes (for user comparison).

### Edit Approach

**Incremental edits** throughout review:
1. Use Edit tool for targeted fixes
2. Re-read sections after editing to verify
3. Track changes in todo list
4. Don't hold all changes in memory until end

### Context Management

For large documents:
1. Read full document once at start
2. Focus on one section at a time during validation
3. Re-read specific sections when editing
4. Use symbol tools for code verification
5. Summarize findings between phases if context grows

---

**End of Command Specification**
