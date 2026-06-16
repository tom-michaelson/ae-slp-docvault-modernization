# Training Assessment Report: [TAR-NNNN] — [Project Name]

<!--
  ============================================================================
  TRAINING ASSESSMENT REPORT

  A training assessment report evaluates how thoroughly a student (or team)
  identified known issues in a purposefully broken codebase during an
  AI-accelerated engineering training exercise.

  The report compares student-submitted findings against the canonical
  answer key (the broken-project-*.md file) to determine which issues
  were found, partially found, or missed, and catalogs additional findings
  beyond the answer key.

  WHEN TO CREATE:
  - After students complete a broken-project assessment exercise
  - When grading AI-assisted codebase analysis submissions

  INPUTS:
  - broken-project-*.md — the canonical answer key listing all planted issues
  - One or more student-authored markdown files documenting their findings

  SEVERITY MULTIPLIERS:
  - Critical = 4 (security vulnerabilities, data loss, data corruption)
  - High     = 3 (functional bugs, broken workflows, missing safeguards)
  - Medium   = 2 (architectural bloat, overengineering, misused patterns)
  - Low      = 1 (documentation drift, cosmetic issues, stale TODOs)
  ============================================================================
-->

**Report ID**: TAR-NNNN
**Project**: [e.g., "Project A — ClinicFlow", "Project B — DocVault", "Project C — MetricsAPI"]
**Answer Key**: [path to broken-project-*.md file]
**Student Submissions**: [list of student markdown file paths]
**Date Assessed**: YYYY-MM-DD
**Status**: [Complete | Needs Review]

## Score Summary *(mandatory)*

| Metric | Value |
|--------|:-----:|
| **Total known issues** | [N] |
| **Issues found** | [N] |
| **Issues partially found** | [N] |
| **Issues missed** | [N] |
| **Additional findings (beyond answer key)** | [N] |
| **Detection rate (raw)** | [N%] |
| **Detection rate (weighted by severity)** | [N%] |

<!--
  Detection rate (raw)      = (found + 0.5 × partial) / total × 100
  Detection rate (weighted) = sum(found_weight + 0.5 × partial_weight) / sum(all_weights) × 100
  where weight = severity multiplier (Critical=4, High=3, Medium=2, Low=1)
-->

## Issue Detection Matrix *(mandatory)*

<!--
  ACTION REQUIRED: For every issue listed in the answer key, determine
  whether the student's submission(s) identified it. Map each answer-key
  issue to the corresponding student finding (if any).

  Categories come directly from the answer key's section headings
  (e.g., "It Runs, But…", "Overengineered Where It Shouldn't Be",
  "Sloppy Where It Shouldn't Be").

  If a single answer-key bullet contains multiple discrete issues,
  decompose it into separate rows — each independently identifiable
  problem gets its own row.

  Status values:
  - ✅ Found   — student identified the issue and understood the root cause
  - 🔶 Partial — student noticed the symptom but missed the root cause
  - ❌ Missed  — no corresponding finding in any student submission

  Depth values:
  - Root cause + fix — student identified root cause and suggested correct fix
  - Root cause       — student identified root cause without a fix
  - Symptom only     — student described the symptom but not the underlying cause
  - —                — not applicable (missed issues)
-->

### [Category from answer key, e.g., "It Runs, But…"]

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 1 | [e.g., High] | [e.g., "Health endpoint returns 200 even when DB is down"] | [✅ / 🔶 / ❌] | [e.g., Root cause] | [e.g., "student-report.md § Health Check Analysis" or "—"] | [e.g., "Correctly identified Express-only check"] |
| 2 | [Severity] | [Issue description] | [Status] | [Depth] | [Reference or "—"] | [Notes] |

### [Next category, e.g., "Overengineered Where It Shouldn't Be"]

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 1 | [Severity] | [Issue description] | [Status] | [Depth] | [Reference or "—"] | [Notes] |

### [Next category, e.g., "Sloppy Where It Shouldn't Be"]

| # | Severity | Known Issue (from answer key) | Status | Depth | Student Reference | Notes |
|---|:--------:|-------------------------------|:------:|-------|-------------------|-------|
| 1 | [Severity] | [Issue description] | [Status] | [Depth] | [Reference or "—"] | [Notes] |

## Coverage by Category *(mandatory)*

<!--
  ACTION REQUIRED: Summarize detection rates per answer-key category.
-->

| Category | Total Issues | Found | Partial | Missed | Detection Rate (raw) | Detection Rate (weighted) |
|----------|:-----------:|:-----:|:-------:|:------:|:--------------------:|:-------------------------:|
| [e.g., "It Runs, But…"] | [N] | [N] | [N] | [N] | [N%] | [N%] |
| [e.g., "Overengineered Where It Shouldn't Be"] | [N] | [N] | [N] | [N] | [N%] | [N%] |
| [e.g., "Sloppy Where It Shouldn't Be"] | [N] | [N] | [N] | [N] | [N%] | [N%] |
| **Total** | **[N]** | **[N]** | **[N]** | **[N]** | **[N%]** | **[N%]** |

## Additional Findings *(include if student reported findings beyond the answer key)*

<!--
  ⚠️ INCLUDE if the student reported findings that do not correspond to
  any known issue in the answer key. The answer key is not exhaustive —
  these codebases contain more problems than are explicitly listed.
  Classify each finding by type:

  - Legitimate issue — a real problem the answer key didn't enumerate
  - Cosmetic / opinion — a style preference or subjective observation, not a defect
  - Misidentification — student was incorrect about the issue
-->

| # | Student-Reported Finding | Source in Submission | Classification |
|---|-------------------------|---------------------|----------------|
| 1 | [e.g., "Variable naming is inconsistent across modules"] | [e.g., "student-report.md § Code Quality"] | [Legitimate issue / Cosmetic / opinion / Misidentification] |

## Missed Issues Detail *(mandatory)*

<!--
  ACTION REQUIRED: For each issue the student missed, provide the
  answer-key description so instructors can use this for targeted feedback.
-->

| # | Category | Severity | Known Issue | Why It Matters |
|---|----------|:--------:|-------------|---------------|
| 1 | [e.g., "Sloppy"] | [e.g., Critical] | [e.g., "Raw SQL with string interpolation — SQL injection vector"] | [e.g., "Security vulnerability — critical miss"] |
| 2 | [Category] | [Severity] | [Issue] | [Impact] |

## Qualitative Assessment *(mandatory)*

<!--
  ACTION REQUIRED: Provide a narrative summary of the student's analysis
  quality. Consider: depth of investigation, accuracy of root-cause
  analysis, quality of evidence cited, and whether the student went
  beyond surface-level symptoms to identify underlying causes.
-->

### Strengths

- [e.g., "Thorough investigation of the auth flow — correctly traced the JWT/session conflict"]
- [e.g., "Good use of tooling to identify dependency vulnerabilities"]

### Areas for Improvement

- [e.g., "Missed all overengineering issues — focus was entirely on bugs, not architecture"]
- [e.g., "Findings lacked specificity — described symptoms but not root causes"]

### Overall Assessment

[Narrative summary: 2–4 sentences evaluating the student's performance, noting patterns in what was found vs. missed and recommendations for skill development.]

<!-- AGENT: Insert changelog from .automatic/templates/partials/changelog.md -->
