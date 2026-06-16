# Training Attempt Log: [TAL-NNNN] — [Project Name]

<!--
  ============================================================================
  TRAINING ATTEMPT LOG

  An attempt log captures what AI tools, prompts, and investigation strategies
  a student used during a single attempt at analyzing a broken codebase. This
  record enables the coaching command to give prompt-specific feedback and
  allows students to track how their approach evolves across iterations.

  IMPORTANT: Fill this out BEFORE grading. The self-assessment section is
  most valuable when written before the student sees their score.

  WHEN TO CREATE:
  - Before each grading attempt on a broken project
  - Each iteration through the training loop produces one attempt log

  RELATED TEMPLATES:
  - training-assessment-report-template.md — the graded report for this attempt
  - training-coaching-report-template.md — coaching based on this attempt
  ============================================================================
-->

**Attempt ID**: TAL-NNNN
**Project**: [e.g., "Project A — ClinicFlow", "Project B — DocVault", "Project C — MetricsAPI"]
**Student**: [name or identifier]
**Iteration**: [e.g., 1, 2, 3 — which attempt at this project]
**Date**: YYYY-MM-DD
**Findings File**: [path to the student's findings markdown]
**Previous Attempt**: [path to previous TAL for this project, or "First attempt"]

## Tools Used *(mandatory)*

<!--
  ACTION REQUIRED: List every AI tool and model used during this attempt.
-->

| Tool | Model / Version | How Used |
|------|----------------|----------|
| [e.g., "Cursor"] | [e.g., "Claude Sonnet 4"] | [e.g., "Primary analysis tool — used Agent mode for codebase exploration"] |
| [e.g., "ChatGPT"] | [e.g., "GPT-4o"] | [e.g., "Pasted code snippets for second-opinion analysis"] |
| [e.g., "Terminal"] | [e.g., "N/A"] | [e.g., "Ran the app locally, tested endpoints with curl"] |

## Investigation Approach *(mandatory)*

<!--
  ACTION REQUIRED: Document your approach in each phase. Include actual
  prompts (or close paraphrases) so the coaching report can give
  prompt-specific feedback.
-->

### Phase 1: Initial Scan

**Goal**: [e.g., "Get a high-level understanding of the codebase and identify obvious issues"]

**Prompts / actions used**:

1. [e.g., "Explore this codebase and identify any bugs, code smells, or architectural issues"]
2. [e.g., "Review the project structure and dependency configuration"]
3. [Additional prompts or manual actions]

**Time spent**: [e.g., "~15 minutes"]

### Phase 2: Deep Dive

**Goal**: [e.g., "Investigate specific areas flagged in the initial scan"]

**Prompts / actions used**:

1. [e.g., "Trace the request flow for POST /appointments and identify any data handling issues"]
2. [e.g., "Review the database schema and migration files for inconsistencies"]
3. [Additional prompts or manual actions]

**Time spent**: [e.g., "~30 minutes"]

### Phase 3: Verification

**Goal**: [e.g., "Confirm suspected issues and look for anything missed"]

**Prompts / actions used**:

1. [e.g., "Run npm audit and summarize the results"]
2. [e.g., "Are there any security vulnerabilities in this codebase?"]
3. [Additional prompts or manual actions]

**Time spent**: [e.g., "~10 minutes"]

## Self-Assessment *(mandatory — complete BEFORE grading)*

<!--
  ACTION REQUIRED: Honest reflection on this attempt. This is most
  valuable when written before seeing the graded results.
-->

### What went well

- [e.g., "Found the SQL injection issue quickly by asking the AI to look for security vulnerabilities"]
- [e.g., "Running the app locally helped me discover the data loss bug through testing"]

### What I'd change next time

- [e.g., "Didn't spend enough time on architecture — focused too heavily on bugs"]
- [e.g., "Should have asked the AI to compare against framework best practices"]

### Confidence level

[e.g., "Medium — I feel good about the bugs I found but suspect I missed some architectural issues. Estimated 60–70% coverage."]

## Notes *(optional)*

[Any additional context, observations about tool behavior, or lessons learned during this attempt.]

<!-- AGENT: Insert changelog from .automatic/templates/partials/changelog.md -->
