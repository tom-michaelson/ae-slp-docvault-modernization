# Review Technical Plans for Cross-Cutting Concerns

You are a Technical Architect reviewing all technical implementation plans to identify cross-cutting concerns, duplicate functionality, and common patterns that should be extracted into shared components.

## Usage

```
/review-technical-plans
```

No parameters required. This command analyzes all `technical-plan.md` files in `./docs/entry-points/`.

## Purpose

This command performs a comprehensive review across ALL technical plans to identify:

1. **Cross-Cutting Concerns**: Functionality that appears across multiple features and should be implemented as shared infrastructure
2. **Duplicate Functionality**: Similar implementations planned in multiple places that should be consolidated
3. **Common Patterns**: Recurring architectural patterns that should be standardized
4. **Shared Components**: Services, utilities, or models that multiple features depend on

## Output

The command generates a report at `./docs/plan/common.md` documenting all identified commonalities and recommendations for extraction.

## Context Management Strategy

**CRITICAL**: This command analyzes potentially dozens of technical plans, which can quickly overwhelm a single agent's context window. To ensure thorough analysis without context overflow, you MUST use Task subagents strategically throughout the analysis process.

### When to Use Task Subagents

1. **Reading Individual Plans** (Phase 1):
   - Spawn a separate `general-purpose` subagent for each technical plan to extract key information
   - Run multiple subagents in PARALLEL to process plans concurrently
   - Each subagent should return a structured summary (services, repositories, models, patterns, etc.)

2. **Analyzing Pattern Categories** (Phase 2):
   - Spawn separate subagents for each pattern category (services, data access, API contracts, etc.)
   - Each subagent receives the plan summaries and focuses on ONE pattern category
   - Run pattern analysis subagents in PARALLEL

3. **Complex Impact Assessments** (Phase 3):
   - Use subagents for detailed impact analysis of high-frequency patterns
   - Subagents can perform deep dives into specific commonalities

4. **Specialized Research**:
   - When you need to understand a specific technology, pattern, or implementation detail
   - When you need to search for additional context in the codebase

### Parallelization Strategy

**Launch subagents in parallel** by sending a single message with multiple Task tool calls. This dramatically speeds up analysis and prevents context overflow.

### Subagent Prompt Structure

Each subagent should receive:
- **Clear objective**: What specific analysis to perform
- **Input data**: Paths to files or summaries to analyze
- **Output format**: Structured format for returning findings (JSON, markdown sections, etc.)
- **Scope limits**: Stay focused on assigned task only

### Example Workflow

**Step 1**: Discover all plans and launch parallel plan readers:
- Find all `technical-plan.md` files
- Launch N subagents in parallel (one per plan)
- Each returns: services list, repositories list, models list, validation patterns, etc.

**Step 2**: Aggregate plan summaries in main agent context

**Step 3**: Launch parallel pattern analyzers:
- Subagent 1: Analyze service layer patterns across all plans
- Subagent 2: Analyze data access patterns across all plans
- Subagent 3: Analyze API contract patterns across all plans
- Subagent 4: Analyze validation patterns across all plans
- Subagent 5: Analyze error handling patterns across all plans
- (Launch all in single message with multiple Task calls)

**Step 4**: Aggregate pattern analysis results in main agent context

**Step 5**: Main agent synthesizes final report from aggregated data

### Context Budget Management

- **Main Agent**: Orchestrates workflow, aggregates results, generates final report
- **Subagents**: Perform focused analysis tasks, return concise structured summaries
- **Rule**: Never load more than 5-10 full technical plans into main agent context
- **Rule**: Always use subagents for reading individual plans when analyzing 3+ plans

## Analysis Process

### Phase 1: Discovery

1. **Find all technical plans**:
   ```bash
   find ./docs/entry-points -name "technical-plan.md" -type f
   ```

2. **Build analysis inventory**: Create a list of all plans with their paths and feature names

3. **Read all technical plans using parallel subagents**:
   - **DO NOT** read plans directly into main agent context
   - **Launch parallel subagents**: Create one `general-purpose` subagent per technical plan
   - **Launch in batches** if there are many plans (e.g., 10-20 subagents per batch)
   - Each subagent should:
     - Read its assigned `technical-plan.md` file
     - Extract structured information in this format:
       ```json
       {
         "plan_path": "path/to/technical-plan.md",
         "feature_name": "...",
         "feature_type": "api-endpoint|ui-feature",
         "services": [{"name": "...", "purpose": "...", "methods": ["..."]}],
         "repositories": [{"name": "...", "tables": ["..."], "operations": ["..."]}],
         "models": [{"name": "...", "type": "entity|dto|request|response", "key_fields": ["..."]}],
         "validation_patterns": ["..."],
         "error_handling": ["..."],
         "security_patterns": ["..."],
         "utilities": [{"name": "...", "purpose": "..."}],
         "external_dependencies": ["..."]
       }
       ```
     - Return ONLY the structured summary (not the full plan text)

4. **Aggregate plan summaries**: Collect all subagent results into a master list

### Phase 2: Pattern Recognition

**Use parallel subagents** to analyze different pattern categories concurrently. Launch multiple `general-purpose` subagents in a single message, each focused on one pattern category.

Each pattern analysis subagent receives:
- The aggregated plan summaries from Phase 1
- Instructions to analyze ONE specific pattern category
- Template for returning structured findings

**Launch these subagents in parallel**:
1. Service Layer Patterns Analysis Subagent
2. Data Access Patterns Analysis Subagent
3. API Contract Patterns Analysis Subagent
4. Validation & Business Rules Analysis Subagent
5. Security Patterns Analysis Subagent
6. Error Handling Patterns Analysis Subagent
7. Utility Functions Analysis Subagent
8. Domain Entity Patterns Analysis Subagent

Analyze all plans to identify the following categories of commonality:

---

#### 2.1 Service Layer Patterns

**Look for**:
- Services with similar names or purposes across plans
- Methods that perform the same operations in different contexts
- Common business logic patterns (validation, calculation, transformation)
- Shared dependencies between services

**Common patterns to identify**:
- User/session management services
- Audit logging services
- Permission checking services
- Data transformation services
- External system integration services
- Notification services
- Caching services

---

#### 2.2 Data Access Patterns

**Look for**:
- Repositories accessing the same tables
- Similar query patterns across repositories
- Common CRUD operations
- Shared filtering, sorting, paging logic
- Audit trail patterns

**Common patterns to identify**:
- Generic repository base patterns
- Query builder abstractions
- Soft delete handling
- Audit field management (created_by, modified_by, etc.)
- Effective date range filtering
- Pagination and sorting utilities

---

#### 2.3 API Contract Patterns

**Look for**:
- Similar request/response model structures
- Common fields appearing in multiple DTOs
- Shared error response formats
- Standard pagination response structures
- Common validation patterns

**Common patterns to identify**:
- Base request/response classes
- Pagination wrapper models
- Standard error response structure
- Audit field DTOs (id, createdBy, createdDate, etc.)
- Common field types (money, dates, identifiers)

---

#### 2.4 Validation and Business Rules

**Look for**:
- Validation logic that appears in multiple plans
- Common business rule patterns
- Shared constraints and checks

**Common patterns to identify**:
- Date range validation
- Required field validation
- Cross-field validation patterns
- Permission validation
- Status transition validation
- Business entity existence checks

---

#### 2.5 Security Patterns

**Look for**:
- Authorization patterns repeated across features
- Common permission checking approaches
- Data access control patterns

**Common patterns to identify**:
- Permission guard implementations
- Row-level security filters
- Audit logging for sensitive operations
- Sensitive data masking

---

#### 2.6 Error Handling Patterns

**Look for**:
- Similar exception types across plans
- Common error codes and messages
- Standard error mapping approaches

**Common patterns to identify**:
- Base exception hierarchy
- Standard error code constants
- Error message templates
- HTTP status mapping conventions

---

#### 2.7 Utility Functions

**Look for**:
- Common data transformations
- String/date/number formatting
- Type conversions
- Collection operations

**Common patterns to identify**:
- Date formatting utilities
- String manipulation utilities
- Type conversion utilities
- Collection transformation utilities
- Null/empty checking utilities

---

#### 2.8 Domain Entity Patterns

**Look for**:
- Entities with similar structures
- Common relationships patterns
- Shared field types

**Common patterns to identify**:
- Base entity classes with common fields
- Audit mixin (created/modified timestamps)
- Soft delete patterns
- Effective date patterns
- Status/state patterns

---

#### Pattern Analysis Subagent Output Format

Each pattern analysis subagent should return findings in this structure:

**IMPORTANT**: Subagents should provide a suggested descriptive name for each pattern. The main agent will assign sequential unique keys (001, 002, 003, etc.) during report synthesis to ensure uniqueness across all pattern categories.

```json
{
  "pattern_category": "Service Layer|Data Access|API Contract|Validation|Security|Error Handling|Utilities|Domain Entity",
  "patterns_found": [
    {
      "suggested_key_name": "descriptive-kebab-case-name",
      "pattern_name": "...",
      "pattern_type": "...",
      "description": "...",
      "occurrences": [
        {
          "plan_path": "...",
          "feature_name": "...",
          "implementation_details": "...",
          "code_examples": ["..."]
        }
      ],
      "frequency": "count of plans using this pattern",
      "complexity": "Low|Medium|High",
      "risk_of_divergence": "Low|Medium|High",
      "extraction_effort": "Low|Medium|High",
      "priority": "Critical|High|Medium|Low",
      "recommended_extraction": {
        "component_type": "Service|Repository|Util|Model|etc.",
        "suggested_name": "...",
        "interface_sketch": "...",
        "benefits": ["..."],
        "implementation_notes": ["..."]
      }
    }
  ]
}
```

---

### Phase 3: Impact Assessment

**Note**: Most impact assessment data should already be provided by pattern analysis subagents in Phase 2. If additional deep-dive analysis is needed for high-frequency patterns, launch focused subagents for those specific assessments.

For each identified commonality, assess (or aggregate from subagent findings):

1. **Frequency**: How many plans include this pattern?
2. **Complexity**: How complex is the duplicated functionality?
3. **Risk of Divergence**: If not extracted, how likely will implementations drift?
4. **Extraction Effort**: How difficult to extract into shared component?
5. **Priority**: Recommended extraction priority (Critical/High/Medium/Low)

### Phase 4: Generate Report

**Main agent responsibility**: Synthesize all subagent findings into the final comprehensive report.

**Inputs**:
- Aggregated plan summaries from Phase 1 subagents
- Pattern analysis findings from Phase 2 subagents
- Any additional impact assessments from Phase 3

**Process**:
1. Consolidate all pattern findings across categories
2. **Assign unique keys**: Generate sequential keys (001, 002, 003, etc.) for ALL identified patterns/components across all categories. Keys must be:
   - Sequential and unique across the entire report
   - Descriptive using kebab-case (e.g., `001-user-session-management`, `002-audit-logging-service`)
   - Consistently applied to every common component/pattern
   - **Key assignment order**: Assign keys in priority order (Critical → High → Medium → Low) so that most important components get lower numbers
   - Use the `suggested_key_name` from subagent output, prepend with sequential number
3. Identify Critical vs High vs Medium vs Low priority extractions
4. Group related patterns and components
5. Generate recommendations with code examples
6. Create implementation roadmap
7. Document risks and mitigations

Create `./docs/plan/common.md` with the following structure:

```markdown
# Common Components and Cross-Cutting Concerns

> **Generated**: [date]
> **Plans Analyzed**: [count]
> **Last Updated**: [date]

## Executive Summary

[2-3 paragraphs summarizing the key findings, total number of cross-cutting concerns identified, and overall recommendations for extraction strategy]

**Key System**: Each identified common component/pattern is assigned a unique key (format: `NNN-descriptive-name`) for tracking and reference purposes throughout the report and in subsequent planning documents.

## Analysis Scope

### Plans Analyzed

| # | Plan Path | Feature Name | Type |
|---|-----------|--------------|------|
| 1 | [path] | [name] | [api-endpoints/ui-features] |

## Critical Extractions

These components appear in multiple plans and MUST be extracted before implementation to avoid duplication.

**Note**: Each component is assigned a unique key (format: `NNN-descriptive-name`) for tracking and reference purposes.

### [Component Name]

**Key**: `NNN-descriptive-kebab-case-name`

**Type**: [Service/Utility/Model/Repository/etc.]

**Appears In**:
- [Plan 1 path] - [How it's used]
- [Plan 2 path] - [How it's used]
- [Plan N path] - [How it's used]

**Current Implementations**:
[Summary of how each plan proposes to implement this]

**Recommended Extraction**:

```typescript
// Suggested shared implementation structure
[Interface or class definition]
```

**Benefits**:
- [Benefit 1]
- [Benefit 2]

**Implementation Notes**:
- [Note 1]
- [Note 2]

---

[Repeat for each critical extraction]

## High Priority Extractions

These components appear frequently and should be extracted early in implementation.

### [Component Name]

**Key**: `NNN-descriptive-kebab-case-name`

[Same structure as Critical Extractions]

---

## Medium Priority Extractions

These components have moderate duplication and should be extracted as time permits.

### [Component Name]

**Key**: `NNN-descriptive-kebab-case-name`

[Same structure as Critical Extractions]

---

## Low Priority Extractions

These patterns have minor duplication but could benefit from standardization.

### [Pattern Name]

**Key**: `NNN-descriptive-kebab-case-name`

**Type**: [Pattern type]

**Appears In**: [count] plans

**Description**: [Brief description of the pattern]

**Recommendation**: [How to standardize]

---

## Common Patterns Catalog

### Service Layer Patterns

| Key | Pattern | Description | Occurrences | Recommendation |
|-----|---------|-------------|-------------|----------------|
| `NNN-xxx` | [Pattern] | [Description] | [N plans] | [Extract/Standardize/Document] |

### Data Access Patterns

| Key | Pattern | Description | Occurrences | Recommendation |
|-----|---------|-------------|-------------|----------------|
| `NNN-xxx` | [Pattern] | [Description] | [N plans] | [Extract/Standardize/Document] |

### API Contract Patterns

| Key | Pattern | Description | Occurrences | Recommendation |
|-----|---------|-------------|-------------|----------------|
| `NNN-xxx` | [Pattern] | [Description] | [N plans] | [Extract/Standardize/Document] |

### Validation Patterns

| Key | Pattern | Description | Occurrences | Recommendation |
|-----|---------|-------------|-------------|----------------|
| `NNN-xxx` | [Pattern] | [Description] | [N plans] | [Extract/Standardize/Document] |

### Error Handling Patterns

| Key | Pattern | Description | Occurrences | Recommendation |
|-----|---------|-------------|-------------|----------------|
| `NNN-xxx` | [Pattern] | [Description] | [N plans] | [Extract/Standardize/Document] |

### Domain Entity Patterns

| Key | Pattern | Description | Occurrences | Recommendation |
|-----|---------|-------------|-------------|----------------|
| `NNN-xxx` | [Pattern] | [Description] | [N plans] | [Extract/Standardize/Document] |

## Shared Infrastructure Recommendations

### Recommended Shared Libraries

| Library | Purpose | Component Keys | Priority |
|---------|---------|----------------|----------|
| [Name] | [Purpose] | [e.g., 001, 005, 012] | [Critical/High/Medium] |

**Note**: Component Keys column references the unique keys assigned to each common component in this report.

### Suggested Package Structure

```
shared/
├── common/
│   ├── models/          # Shared DTOs and entities
│   ├── services/        # Shared services
│   ├── repositories/    # Base repositories
│   ├── utils/           # Utility functions
│   ├── validators/      # Common validators
│   └── exceptions/      # Exception hierarchy
├── security/
│   ├── guards/          # Permission guards
│   └── filters/         # Data access filters
└── infrastructure/
    ├── audit/           # Audit logging
    ├── cache/           # Caching utilities
    └── config/          # Configuration
```

## Implementation Roadmap

### Phase 1: Foundation (Before Feature Implementation)

- [ ] [Component 1] - [Reason for priority]
- [ ] [Component 2] - [Reason for priority]

### Phase 2: Core Services (During Early Implementation)

- [ ] [Component 3] - [Reason]
- [ ] [Component 4] - [Reason]

### Phase 3: Optimization (During Later Implementation)

- [ ] [Component 5] - [Reason]
- [ ] [Component 6] - [Reason]

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk if not extracted] | [Impact description] | [How to mitigate] |

## Appendix

### Component Key Index

Quick reference of all assigned keys:

| Key | Component Name | Category | Priority | Location in Report |
|-----|----------------|----------|----------|-------------------|
| `001-xxx` | [Name] | [Service/Data/API/etc.] | [Critical/High/Med/Low] | [Section] |
| `002-xxx` | [Name] | [Service/Data/API/etc.] | [Critical/High/Med/Low] | [Section] |

### Detailed Pattern Analysis

[Additional detailed analysis for complex patterns]

### Cross-Reference Matrix

[Matrix showing which plans use which common components, referenced by key]

Example:
| Plan | Component Keys Used |
|------|-------------------|
| api-endpoints/tariff-rates/get | 001, 003, 007, 015 |
| api-endpoints/users/create | 001, 002, 008, 012 |

---

*Report generated by Legacy Analyzer Agent*
```

## Execution Instructions

### Overview

This is a **multi-phase workflow** that leverages parallel Task subagents to analyze technical plans without overwhelming the main agent's context.

### Detailed Steps

#### Step 1: Discover Technical Plans

Use Glob or Bash to find all `technical-plan.md` files:
```bash
find ./docs/entry-points -name "technical-plan.md" -type f
```

Create an inventory list with paths.

#### Step 2: Launch Parallel Plan Reader Subagents

- **Critical**: Do NOT read plans into main agent context
- For each technical plan, launch a `general-purpose` Task subagent
- **Launch in parallel**: Send single message with multiple Task tool calls
- Each subagent prompt should:
  ```
  Read and extract structured information from the technical plan at [PATH].

  Return a JSON summary with:
  - plan_path
  - feature_name
  - feature_type (api-endpoint or ui-feature)
  - services: array of {name, purpose, methods}
  - repositories: array of {name, tables, operations}
  - models: array of {name, type, key_fields}
  - validation_patterns: array of patterns
  - error_handling: array of patterns
  - security_patterns: array of patterns
  - utilities: array of {name, purpose}
  - external_dependencies: array

  Be concise. Return ONLY the structured JSON, not the full plan text.
  ```

#### Step 3: Aggregate Plan Summaries

Collect all subagent JSON responses into a master list in main agent context. This compressed format keeps context usage low.

#### Step 4: Launch Parallel Pattern Analyzer Subagents

Launch 8 `general-purpose` Task subagents **in parallel** (single message, multiple Task calls):

1. **Service Layer Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Service patterns, common methods, business logic patterns
   - Returns: JSON with patterns found (see Phase 2 output format)

2. **Data Access Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Repository patterns, query patterns, CRUD operations
   - Returns: JSON with patterns found

3. **API Contract Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Request/response models, DTOs, common fields
   - Returns: JSON with patterns found

4. **Validation Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Validation logic, business rules, constraints
   - Returns: JSON with patterns found

5. **Security Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Authorization, permission checks, data access control
   - Returns: JSON with patterns found

6. **Error Handling Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Exception types, error codes, error mapping
   - Returns: JSON with patterns found

7. **Utility Functions Analyzer**
   - Receives: All plan summaries
   - Analyzes: Common transformations, formatting, conversions
   - Returns: JSON with patterns found

8. **Domain Entity Patterns Analyzer**
   - Receives: All plan summaries
   - Analyzes: Entity structures, relationships, common fields
   - Returns: JSON with patterns found

#### Step 5: Aggregate Pattern Analysis Results

Collect all pattern analyzer JSON responses in main agent context.

#### Step 6: Synthesize Final Report

Main agent uses aggregated findings to generate `./docs/plan/common.md`:
- **Assign unique keys**: Generate sequential keys starting from 001 for ALL patterns/components
  - Format: `NNN-descriptive-kebab-case-name` (e.g., `001-user-session-service`, `002-audit-logger`, `003-permission-checker`)
  - Keys must be unique across entire report
  - Keys should be descriptive and concise
  - **Assignment process**:
    1. Collect all patterns from all subagent outputs
    2. Group by priority (Critical/High/Medium/Low)
    3. Assign sequential keys starting from 001, processing in priority order
    4. Use `suggested_key_name` from subagent output, prepend with number
- Consolidate patterns by priority (Critical/High/Medium/Low)
- Group related components
- Generate code examples for recommended extractions
- Create implementation roadmap
- Document risks and mitigations
- **Ensure keys are prominently displayed** in all sections and tables

#### Step 7: Create Directory and Write Report

- Ensure `./docs/plan/` directory exists
- Write comprehensive report to `./docs/plan/common.md`

### Context Management Rules

- **Main agent context**: Contains only plan summaries (JSON) + pattern analysis results (JSON) + final report
- **Main agent NEVER**: Loads full technical plan markdown files
- **Subagents**: Perform all detailed reading and analysis
- **Parallelization**: Always launch multiple subagents in single message when possible

## Pattern Detection Heuristics

### Same-Name Detection
- Services/repositories/models with identical or very similar names
- Methods with the same signatures across different services

### Similar-Purpose Detection
- Components that serve the same business function
- Methods that perform equivalent operations on different data

### Structural Similarity Detection
- DTOs/entities with overlapping field sets
- Similar validation rule patterns
- Common error handling structures

### Dependency Analysis
- Services that multiple features depend on
- Repositories that multiple services reference
- Utilities imported across multiple plans

## Subagent Best Practices

### Parallel Execution Example

**Correct** - Launch multiple subagents in a single message:
```
I'm launching 15 plan reader subagents in parallel to analyze all technical plans...

[Single message with 15 Task tool calls]
```

**Incorrect** - Launching subagents sequentially:
```
I'm launching a subagent to read plan 1...
[Wait for response]
I'm launching a subagent to read plan 2...
[Wait for response]
...
```

### Subagent Prompt Guidelines

Each subagent prompt should include:

1. **Clear Task**: "Read and extract structured information from [FILE]"
2. **Specific Output Format**: "Return JSON with these fields: ..."
3. **Scope Limitation**: "Return ONLY the summary, not full content"
4. **Success Criteria**: "Be concise and focus on patterns, services, repositories, models"

### Batching Strategy

If there are 50+ technical plans:
- **Batch 1**: Launch 20 plan readers in parallel
- Wait for results, aggregate
- **Batch 2**: Launch next 20 in parallel
- Repeat until all plans are processed

This prevents overwhelming the system while still maximizing parallelization.

### Error Handling

If a subagent fails or returns incomplete data:
- Note which plan failed
- Retry with a more specific prompt
- If persistent failure, read that plan directly (exception to the rule)

### Avoiding Context Bloat

**Good**: Subagent returns compact JSON summary (1-2 KB per plan)
**Bad**: Subagent returns full plan markdown (20-50 KB per plan)

With 50 plans:
- Good approach: ~100 KB total context
- Bad approach: ~2500 KB total context (exceeds limits)

## Quality Criteria

The report should:

- [ ] **Assign unique keys to ALL common components/patterns**: Every pattern must have a unique key in format `NNN-descriptive-name`
  - [ ] Keys are sequential (001, 002, 003, etc.)
  - [ ] Keys use kebab-case
  - [ ] Keys are clearly displayed in each section (Critical, High, Medium, Low priority)
  - [ ] Keys are included in all catalog tables
- [ ] Include ALL technical plans in the analysis scope
- [ ] Use Task subagents appropriately:
  - [ ] Parallel plan reader subagents for Phase 1
  - [ ] Parallel pattern analyzer subagents for Phase 2
  - [ ] Main agent context contains only compressed summaries
  - [ ] No full technical plan markdown loaded into main agent
- [ ] Identify at least the following pattern categories:
  - Service layer patterns
  - Data access patterns
  - API contract patterns
  - Validation patterns
  - Error handling patterns
  - Domain entity patterns
- [ ] Provide concrete extraction recommendations with code examples
- [ ] Prioritize extractions by impact and frequency
- [ ] Include implementation roadmap
- [ ] Document risks of not extracting common components

## Use Cases

### Pre-Implementation Review
Run this command before beginning implementation to identify what shared infrastructure needs to be built first.

### Progress Check
Run periodically during planning to identify new commonalities as more plans are created.

### Technical Debt Prevention
Use findings to prevent duplicate implementations and ensure consistency across features.

---

**End of Command Specification**
