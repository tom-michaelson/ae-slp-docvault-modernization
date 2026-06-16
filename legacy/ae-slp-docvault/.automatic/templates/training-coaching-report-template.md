# Training Coaching Report: [TCR-NNNN] — [Project Name]

<!--
  ============================================================================
  TRAINING COACHING REPORT

  A coaching report analyzes WHY a student missed specific issues and provides
  targeted, actionable guidance on improving their AI-assisted investigation
  approach. It connects the graded assessment (what was missed) to the attempt
  log (what prompts/tools were used) to diagnose gaps and recommend better
  strategies.

  If a previous assessment report exists for the same student and project,
  the coaching report also tracks progress across iterations.

  WHEN TO CREATE:
  - After a training assessment report (TAR) is graded
  - As the third step in the training iteration loop

  INPUTS:
  - Training assessment report (TAR) — the graded results
  - Training attempt log (TAL) — the prompts and tools used
  - Previous TAR (if exists) — for progress comparison

  RELATED TEMPLATES:
  - training-assessment-report-template.md — the graded report this coaching is based on
  - training-attempt-log-template.md — the attempt log this coaching references
  ============================================================================
-->

**Report ID**: TCR-NNNN
**Project**: [e.g., "Project A — ClinicFlow", "Project B — DocVault", "Project C — MetricsAPI"]
**Student**: [name or identifier]
**Iteration**: [e.g., 1, 2, 3]
**Date**: YYYY-MM-DD
**Linked Assessment**: [path to TAR file]
**Linked Attempt Log**: [path to TAL file]
**Previous Assessment**: [path to previous TAR, or "First iteration"]

## Progress Summary *(include if iteration > 1)*

<!--
  ⚠️ INCLUDE if a previous assessment report exists for this student/project.
  Compare the current TAR against the previous TAR to show what changed.
-->

| Metric | Previous | Current | Change |
|--------|:--------:|:-------:|:------:|
| **Detection rate (raw)** | [N%] | [N%] | [+/-N%] |
| **Detection rate (weighted)** | [N%] | [N%] | [+/-N%] |
| **Issues found** | [N] | [N] | [+/-N] |
| **Issues partially found** | [N] | [N] | [+/-N] |
| **Issues missed** | [N] | [N] | [+/-N] |

### What Improved

- [e.g., "Found 3 additional sloppy-category issues that were missed last iteration"]
- [e.g., "Depth improved on 2 issues — moved from Symptom only to Root cause"]

### What Regressed or Stayed the Same

- [e.g., "Still missing all overengineering issues — same blind spot as last iteration"]
- [e.g., "Lost a partial match on the health check issue — may have changed prompts in a way that dropped this"]

## Gap Analysis by Category *(mandatory)*

<!--
  ACTION REQUIRED: For each answer-key category with missed or partial issues,
  analyze WHY the student's approach failed to find them. Reference specific
  prompts from the attempt log where relevant.
-->

### [Category, e.g., "It Runs, But..."]

**Issues missed / partial in this category**: [N of M]

**Root cause of gaps**:

- [e.g., "The student's prompts focused on reading code statically. The data-loss bug on PATCH /appointments only surfaces when you test the endpoint — no prompt asked the AI to trace runtime behavior or test edge cases."]
- [e.g., "The health check issue requires understanding what the /health endpoint actually checks vs. what it should check. The student's initial scan prompt was too broad to catch this nuance."]

**Connection to attempt log**: [e.g., "TAL Phase 1 prompt 'identify any bugs' is too generic to catch subtle runtime issues. Phase 3 verification didn't include endpoint testing."]

### [Next category with gaps, e.g., "Overengineered Where It Shouldn't Be"]

**Issues missed / partial in this category**: [N of M]

**Root cause of gaps**:

- [e.g., "No prompt in the attempt log asked about architecture, abstraction layers, or code complexity. The student's entire approach was bug-focused, not architecture-focused."]
- [e.g., "The PluginSystem issue requires noticing code that exists but is never called — this is a different investigation pattern than looking for broken code."]

**Connection to attempt log**: [e.g., "All three investigation phases focused on 'bugs' and 'issues' — the word 'architecture' or 'overengineering' never appeared in any prompt."]

### [Next category with gaps, e.g., "Sloppy Where It Shouldn't Be"]

**Issues missed / partial in this category**: [N of M]

**Root cause of gaps**:

- [e.g., "The student found some sloppy issues (missing tests, stale docs) but missed the SQL injection vector. Security-specific prompting was absent from the attempt log."]

**Connection to attempt log**: [e.g., "No prompt specifically asked about security vulnerabilities, input validation, or injection risks."]

## Prompt Improvement Suggestions *(mandatory)*

<!--
  ACTION REQUIRED: Provide specific, actionable prompt recommendations
  the student can use in their next iteration. Organize by the type of
  gap they address.
-->

### For finding runtime / behavioral issues

- [e.g., "Ask the AI: 'Trace the full request lifecycle for each CRUD endpoint. For each one, what happens with edge-case inputs like empty strings, null values, or missing fields?'"]
- [e.g., "Ask the AI: 'Run the test suite and analyze which tests are skipped, failing, or testing the wrong thing. What should each test actually verify?'"]

### For finding overengineering / architectural issues

- [e.g., "Ask the AI: 'Trace a single request from HTTP handler to database and back. Count every layer of indirection. Which layers add value and which are unnecessary?'"]
- [e.g., "Ask the AI: 'Find all classes, interfaces, and abstractions in this project. Which ones are used by only one consumer? Which have zero consumers?'"]

### For finding security / data integrity issues

- [e.g., "Ask the AI: 'Audit this codebase for SQL injection, XSS, CSRF, and other OWASP Top 10 vulnerabilities. Show me the exact lines of code.'"]
- [e.g., "Ask the AI: 'Find every place where user input flows into a database query, file operation, or shell command without sanitization.'"]

### For finding configuration / infrastructure issues

- [e.g., "Ask the AI: 'Review all configuration files (.env, docker-compose, config.*) for hardcoded values, inconsistencies, or references to paths/systems that don't exist.'"]
- [e.g., "Ask the AI: 'Compare the README and API documentation against the actual codebase. What's out of date?'"]

## Investigation Strategies *(mandatory)*

<!--
  ACTION REQUIRED: Recommend broader investigation techniques beyond
  specific prompts. These are approaches the student should adopt.
-->

- [e.g., "**Run the app**: Many issues only surface at runtime. Start the application, test each endpoint, and observe the actual behavior vs. documented behavior."]
- [e.g., "**Use multiple prompt angles**: Don't rely on a single 'find all issues' prompt. Make separate passes for bugs, architecture, security, documentation, and configuration."]
- [e.g., "**Ask 'why does this exist?'**: For every abstraction, class, or configuration layer, ask the AI why it exists and whether it's justified. This catches overengineering."]
- [e.g., "**Compare against best practices**: Ask the AI to compare the codebase against its framework's conventions and best practices. This surfaces sloppy patterns."]
- [e.g., "**Read error handling paths**: Ask the AI to trace what happens when things fail — database down, invalid input, missing config. Many bugs hide in error handling."]

## Next Iteration Focus *(mandatory)*

<!--
  ACTION REQUIRED: Prioritize what the student should target in their
  next attempt, ordered by highest-severity misses first.
-->

| Priority | Focus Area | Why | Suggested Approach |
|:--------:|-----------|-----|-------------------|
| 1 | [e.g., "Security vulnerabilities"] | [e.g., "Missed a Critical-severity SQL injection — highest-impact gap"] | [e.g., "Dedicated security audit pass with OWASP-focused prompts"] |
| 2 | [e.g., "Overengineering patterns"] | [e.g., "Missed entire category — 0% detection rate on Medium-severity issues"] | [e.g., "Architecture trace prompts + 'why does this exist' questioning"] |
| 3 | [e.g., "Runtime behavior testing"] | [e.g., "2 High-severity issues only discoverable by running the app"] | [e.g., "Start the app, test each endpoint, observe vs. document"] |

<!-- AGENT: Insert changelog from .automatic/templates/partials/changelog.md -->
