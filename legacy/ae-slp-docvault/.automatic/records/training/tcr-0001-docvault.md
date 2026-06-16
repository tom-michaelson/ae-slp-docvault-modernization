# Training Coaching Report: [TCR-0001] — Project B — DocVault

**Report ID**: TCR-0001
**Project**: Project B — DocVault
**Student**: tom
**Iteration**: 1
**Date**: 2026-04-22
**Linked Assessment**: `.automatic/records/training/tar-0001-docvault.md`
**Linked Attempt Log**: `.automatic/records/training/tal-0001-docvault.md`
**Previous Assessment**: First iteration

## Gap Analysis by Category *(mandatory)*

### Sloppy Where It Shouldn't Be

**Issues missed / partial in this category**: 3 missed + 1 partial (4 of 10)

**Root cause of gaps**:

- **Dependency health entirely skipped (Issues #9, #10, #11).** The `analyze-repo-hygiene` prompt did not include a dependency-audit step. It produced findings about committed secrets, `.gitignore` patterns, and missing test infrastructure — all structural, file-system-observable issues — but none that required running a package manager command. The three dependency misses (outdated packages, CVEs, deprecated warning) are only discoverable by executing `npm audit` and `npm outdated`. Because the skill never instructs the AI to simulate or interpret the output of these commands, they were structurally unreachable by the pipeline as run.

- **CVE miss is the highest-impact gap.** Issue #10 (High severity, known CVEs) is the most consequential of the three misses. Known CVEs are documented attack vectors requiring zero code reading — `npm audit` surfaces them in seconds. Missing a High-severity security issue while scoring 100% on all architectural issues suggests the analysis workflow was thorough for code-reading tasks but had no Phase 0 dependency-health gate.

- **`DocumentGrid.jsx` god component only partially found (Issue #16).** The `analyze-code-smell` prompt found the utility-function leak from `DocumentGrid.jsx` but did not identify the broader 800-line god-component problem (inline API calls, colocated state management, CSS-in-JS). The root cause: the code smell analyzer found the cross-file import anomaly (a graph-traversal signal) but did not check whether any single component was unusually large. A file-size or line-count check was absent from the prompt's scope.

**Connection to attempt log**: TAL Phase 0 used `analyze-repo-hygiene.prompt.md` ported from ClinicFlow without review. The student noted in the self-assessment: *"Prompts may need to be made more language-agnostic and any specific references to issues from the previous project should be removed."* If the ClinicFlow repo hygiene prompt was tailored to a Python/Django project, it would have no reason to include `npm audit` as a step. This is the direct causal chain: unreviewed prompt → missing dependency-audit step → three misses.

TAL Phase 2 used `analyze-code-smell.prompt.md` in parallel. The student also noted: *"Might benefit from reviewing the analysis artifacts as they were generated rather than deferring all review to after the run."* A mid-run review of `duplicate_utility_directories.md` (which footnoted the `DocumentGrid.jsx` export) would have prompted a follow-up investigation of the file's full scope.

## Prompt Improvement Suggestions *(mandatory)*

### For finding dependency health / security vulnerabilities

These three prompts address all three missed issues (#9, #10, #11) and are the highest-leverage additions for the next iteration. Run these as a dedicated **Phase 0 step before any code analysis**:

```
Audit the dependency health of this project. For each package.json file present:
1. List every direct dependency and its current version vs. the latest available version. Flag any dependency that is 2+ major versions behind or more than 2 years old.
2. Simulate or describe the output of `npm audit`. Identify any packages with known CVEs, their severity (Critical/High/Medium/Low), and which specific vulnerability is present.
3. Identify any packages marked as deprecated in the npm registry. Note whether a replacement package is recommended.
Report results in three sections: Outdated Packages, Known CVEs, Deprecated Packages. For each CVE, state the package name, CVE ID (if known), severity, and recommended remediation.
```

```
Run `npm audit --json` against the backend/ and frontend/ package manifests and interpret the results. List every advisory, its severity, the affected package, and whether a fix is available via `npm audit fix`. Flag any High or Critical advisories for immediate action.
```

### For finding god components / large file code smells

This addresses the partial detection of Issue #16 (`DocumentGrid.jsx`):

```
List every React component file in the frontend/src/components/ directory sorted by line count, largest first. For any component exceeding 300 lines, perform a full audit:
1. Does it contain its own API calls (fetch, axios, useEffect with data fetching)?
2. Does it manage its own state beyond simple UI toggles?
3. Does it include inline styles or CSS-in-JS?
4. Does it export anything other than the default component (utility functions, constants, sub-components)?
5. Is it imported by more than 3 other files?
Report each overloaded responsibility as a separate finding.
```

### For making repo-hygiene prompts project-agnostic

This addresses the root cause of all three missed issues — the ClinicFlow-inherited prompt that lacked npm-specific steps:

```
Perform a full repository hygiene audit for this [Node.js / React] project. Cover ALL of the following:
1. Committed secrets — env files, credentials, tokens in version control
2. .gitignore completeness — are all sensitive file patterns excluded?
3. Dependency health — outdated, vulnerable (CVE), or deprecated packages (run npm audit + npm outdated)
4. Test infrastructure — presence of test files, test runner config, CI pipelines
5. Dead configuration — hardcoded fallback secrets, conflicting port definitions, environment variable fragmentation
6. Documentation accuracy — does the README match the actual running behavior?
Do not stop at structural observation. For (3), actually enumerate package versions and flag vulnerabilities. For (6), compare README claims against code.
```

### For improving mid-run artifact review

This is a workflow suggestion, not a prompt, but it addresses the student's own identified gap:

After each Phase 2 analyzer writes its output, read the generated file and check: *"Does this finding have a footnote or aside that could be a full separate finding on its own?"* If yes, open the referenced file immediately. The `DocumentGrid.jsx` partial was only a footnote in `duplicate_utility_directories.md` — a 30-second scan would have caught it before submission.

## Investigation Strategies *(mandatory)*

- **Make `npm audit` a mandatory Phase 0 gate.** Before any code reading, run (or ask the AI to simulate) `npm audit` and `npm outdated` against every `package.json` in the repo. Known CVEs are High-severity by definition and require no code reading to discover. A 10-second command cannot be blocked by prompt quality. If the environment doesn't support running npm directly, ask the AI to inspect the lockfile (`package-lock.json`) for known-vulnerable version ranges.

- **Add a line-count scan to every code-smell pass.** Ask the AI to list all source files sorted by size before doing qualitative analysis. Files that are outliers (e.g., 3× the median component size) should be explicitly audited for god-component symptoms. This surfaces issues the graph-traversal analysis (import patterns) won't catch.

- **Review prompts before running them on a new project.** The student's self-assessment identified this as a risk. Before executing `analyze-all`, spend 5 minutes reading each prompt file in `.github/prompts/` and checking for: project-specific language, tool names (e.g., Python tools in a Node project), or hardcoded paths. Flag any that need adaptation. This is especially important for Phase 0 prompts like `analyze-repo-hygiene` that define the baseline for all subsequent analysis.

- **Review generated artifacts as they are produced, not after.** Read each output file immediately after it's written. Look for footnotes, asides, and `NOTE:` comments — these often contain follow-up signals that the AI self-identified but didn't elevate to a full finding. The `DocumentGrid.jsx` god-component miss was visible in a footnote; a same-session follow-up prompt would have closed it before submission.

- **Treat the priority matrix as a completeness check.** After the pipeline runs, read `analysis/priority_matrix/*.md` and ask: *"Is there a CVE or security finding listed here?"* If the priority matrix contains no security-category rows, that's a signal that the security/dependency analysis was not run. Use the matrix as a checklist gate before finalizing the submission.

## Next Iteration Focus *(mandatory)*

| Priority | Focus Area | Why | Suggested Approach |
|:--------:|-----------|-----|-------------------|
| 1 | Dependency CVE audit | Missed Issue #10 (High) — known CVEs are the most critical gap; require zero code reading to discover | Add `npm audit` simulation as a mandatory Phase 0 step before any code analysis |
| 2 | Outdated and deprecated packages | Missed Issues #9 (Low) and #11 (Low) — same root cause as #1; captured by the same `npm outdated` command | Include in the Phase 0 dependency health prompt alongside CVE audit |
| 3 | God-component detection | Issue #16 partially found (Medium) — full scope of `DocumentGrid.jsx` missed | Add explicit line-count scan + per-large-file responsibility audit to code-smell pass |

---

## Changelog

| Date | Author | Change |
|------|--------|--------|
| 2026-04-22 | automated | TCR-0001 created — first iteration coaching report for tom's DocVault attempt (TAL-0001 / TAR-0001) |
