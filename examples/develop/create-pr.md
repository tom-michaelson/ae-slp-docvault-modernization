# Create Pull Request

Create a Pull Request for the current or specified branch using Azure DevOps, with intelligent PR title and description generation based on branch changes.

## What This Does

This command automates the PR creation workflow by:
- **Committing ALL outstanding changes** (staged AND unstaged) in the current branch
- **Pushing the branch to remote** so changes are available in Azure DevOps
- Gathering context about branch changes (commits, modified files, git status)
- Analyzing the nature and scope of changes (documentation, code, tests, etc.)
- Generating an appropriate PR title and description based on project patterns
- Invoking the ado-operator subagent to create the PR in Azure DevOps
- Returning ONLY the PR URL (no markdown formatting, no explanation)

## Usage

```
/create-pr source: [source-branch] target: [target-branch]
```

**Parameters**:
- `source` (required): The source branch containing changes to be merged (typically your feature branch)
- `target` (required): The target branch to merge into (typically `main` or `dev`)

**Examples**:
```
/create-pr source: feature/company-maintenance target: main
```

```
/create-pr source: dev/ai-workflow target: dev
```

```
/create-pr source: bugfix/null-pointer target: main
```

## How It Works

When you run this command, I will:

### Phase 0: Prepare Branch for PR

**IMPORTANT**: This phase ensures ALL local changes are committed and pushed before creating the PR.

1. **Stage all outstanding changes**:
   - Run `git add -A` to stage ALL changes (modified, deleted, and untracked files)
   - This ensures nothing is left behind, even files not yet staged

2. **Commit all staged changes**:
   - Check if there are staged changes to commit (using `git diff --cached --quiet`)
   - If changes exist, generate an appropriate commit message based on:
     - The nature of the changes (docs, code, tests, config)
     - The branch name context
     - Modified file patterns
   - Execute: `git commit -m "[generated message]"`
   - Commit message format:
     - For docs: "Add/Update [domain] documentation"
     - For code: "Implement [feature] changes"
     - For mixed: "Update [feature] with implementation and documentation"
     - For fixes: "Fix [description] in [component]"
     - Always append: `🤖 Generated with Claude Code`

3. **Push all commits to remote**:
   - Push the current branch to origin: `git push -u origin [current-branch]`
   - This ensures all local commits (including the one just created) are available on the remote
   - If push fails due to upstream changes, attempt `git pull --rebase` first, then push again

### Phase 1: Gather Branch Context

1. **Verify git state and parameters**:
   - Validate that source branch exists (it was just pushed in Phase 0)
   - Validate that target branch exists
   - Confirm repository is clean (should be clean after Phase 0)
   - Ensure source and target branches are different

2. **Collect change information**:
   - Get list of commits on source branch that are not in target branch
   - Use: `git log [target-branch]..[source-branch]`
   - Get summary of changed files between target and source
   - Use: `git diff --name-status [target-branch]...[source-branch]`
   - Analyze file patterns to determine change type:
     - Documentation changes (`docs/**`)
     - Implementation code (`passage-api/**`, `passage-ui/**`)
     - Configuration changes
     - Test changes
     - Infrastructure/tooling changes

3. **Extract commit context**:
   - Read commit messages to understand intent
   - Identify patterns:
     - Feature implementation
     - Bug fixes
     - Documentation updates
     - Refactoring
     - Technical plan creation
     - Functional analysis

### Phase 2: Generate PR Metadata

4. **Determine PR title**:
   - For feature branches: Extract feature name from branch or commits
   - For documentation: "Add [domain] functional analysis" or "Add [feature] technical plan"
   - For implementation: "Implement [feature-name]"
   - For fixes: "Fix [issue-description]"
   - Format: Concise, descriptive, follows project conventions

5. **Generate PR description**:
   - **Summary section**: 2-3 sentences describing what changed and why
   - **Changes section**: Bullet points of key modifications
   - **Documentation references**: Links to related docs if applicable
   - **Testing notes**: What testing was performed
   - **Context section**: Any relevant background or dependencies
   - Include standard footer:
     ```markdown
     🤖 Generated with [Claude Code](https://claude.com/claude-code)
     ```

### Phase 3: Create PR Using ADO Operator

6. **Invoke ado-operator subagent**:
   - Use the Task tool with `subagent_type: "ado-operator"`
   - Provide comprehensive context:
     - Source branch name
     - Target branch name (typically `main`)
     - Generated PR title
     - Generated PR description
     - Repository name (`passage-modernization`)
     - Any work item IDs if mentioned in commits

7. **ado-operator execution**:
   - The ado-operator will use Azure CLI (`az repos pr create`)
   - It will handle authentication and API communication
   - It will set appropriate PR metadata (reviewers, policies, etc.)
   - It will return the PR URL

8. **Return PR URL only**:
   - Output ONLY the PR URL
   - No markdown formatting (no backticks, no brackets, no labels)
   - No explanatory text before or after
   - Just the raw URL: `https://dev.azure.com/...`

## Branch Naming Convention Patterns

This command recognizes common branch naming patterns to generate better PR titles:

| Pattern | Example | Generated Title |
|---------|---------|----------------|
| `feature/*` | `feature/company-maintenance` | "Add Company Maintenance feature" |
| `bugfix/*` or `fix/*` | `bugfix/null-pointer-error` | "Fix null pointer error" |
| `docs/*` | `docs/company-functional-analysis` | "Add Company functional analysis documentation" |
| `refactor/*` | `refactor/service-layer` | "Refactor service layer" |
| `test/*` | `test/add-integration-tests` | "Add integration tests" |
| `dev/*` | `dev/ai-workflow` | Title derived from commits |

## Change Type Detection

The command intelligently detects the type of changes based on modified files:

| File Pattern | Change Type | Description Impact |
|--------------|-------------|-------------------|
| `docs/entry-points/**/*.md` | Documentation | Emphasizes analysis/planning work |
| `docs/plan/**` | Planning | Highlights implementation planning |
| `passage-api/**/*.ts` | Backend Code | Notes API/backend implementation |
| `passage-ui/**/*.tsx` | Frontend Code | Notes UI component development |
| `**/test/**` or `**/*.spec.ts` | Tests | Emphasizes test coverage additions |
| `*.md` (root or .claude) | Documentation | Configuration or project docs |
| `package.json`, `*.config.*` | Configuration | Infrastructure changes |

## PR Description Template

The generated PR description follows this structure:

```markdown
## Summary

[2-3 sentences describing what changed and why, derived from commits and file analysis]

## Changes

- [Key change 1 - derived from commit messages]
- [Key change 2 - derived from file analysis]
- [Key change 3 - patterns detected]

## Documentation

[If docs/ changes exist, list them with references]

## Technical Context

[If technical plans exist, reference them]

## Testing

[If test files changed, describe test additions/changes]

## Related Work Items

[If work item IDs found in commits, reference them]

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## Project-Specific Conventions

For the Northwest Passage modernization project:

### Documentation PRs

When the branch primarily contains documentation changes:
- Title format: "Add [domain] [analysis-type] documentation"
- Description emphasizes:
  - What domain/feature was analyzed
  - What documentation was created (functional specs, technical plans, etc.)
  - References to entry point directories
  - Any discovered insights or patterns

**Example**:
```markdown
Title: Add Company domain functional analysis

Description:
## Summary

This PR adds comprehensive functional analysis for the Company domain, including
15 entry points covering company maintenance, contacts, addresses, and reporting.

## Changes

- Functional specifications for 15 company-related entry points
- Technical plans for API endpoints and UI features
- Call tree analysis for backend services
- Database dependency mapping

## Documentation Structure

- `docs/entry-points/ui-features/2105-infrastructure-company-company-maintenance/`
- `docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany/`
- Additional entry points under `docs/entry-points/**`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Implementation PRs

When the branch contains implementation code:
- Title format: "Implement [feature-name]"
- Description emphasizes:
  - What feature was implemented
  - Backend and/or frontend components added
  - Test coverage added
  - Migration scripts if database changes

**Example**:
```markdown
Title: Implement Company Maintenance API endpoints

Description:
## Summary

Implements core Company Maintenance API endpoints including GET, POST, PUT, and
DELETE operations with full test coverage.

## Changes

- CompanyController with 4 REST endpoints
- CompanyService with business logic
- CompanyRepository with TypeORM integration
- Company entity mapping to COMPANY table
- 45 unit tests and 12 integration tests
- Database migration for new indexes

## Testing

- Unit test coverage: 92%
- Integration tests for all endpoints
- E2E tests for critical workflows

## Related Documentation

- Technical plan: `docs/entry-points/api-endpoints/2984-spring-companymaintenanceservice-getcompany/technical-plan.md`
- Functional spec: Same directory

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

### Planning PRs

When the branch contains meta-plans or planning documentation:
- Title format: "Add [domain] implementation plan"
- Description emphasizes:
  - Scope of planning work
  - Number of features/entry points planned
  - Dependencies identified
  - Sequencing recommendations

## Context to Provide to ado-operator

When invoking the ado-operator subagent, provide this context:

```markdown
Task: Create a Pull Request from source branch to target branch

Branch Information:
- Source branch: [source-branch-name]
- Target branch: [target-branch-name]
- Repository: passage-modernization

PR Metadata:
Title: [generated title]

Description:
[generated description following template above]

Commits (for reference):
[commit 1]: [message]
[commit 2]: [message]
...

Changed Files Summary:
- Documentation: [count] files
- Backend Code: [count] files
- Frontend Code: [count] files
- Tests: [count] files
- Configuration: [count] files

Work Items:
[list of any work item IDs found in commit messages]

Additional Notes:
[any special considerations, such as database migrations, breaking changes, etc.]

Please use the Azure CLI to create this PR with:
- **DO NOT use --auto-complete** - PRs must remain open for human review
- squash merge enabled
- delete source branch after merge
- appropriate reviewers if project defaults exist
```

## Important Guidelines

### Before Creating PR

**PRE-FLIGHT CHECKS** (performed BEFORE Phase 0):
- [ ] Verify we are on the correct source branch
- [ ] Verify target branch exists
- [ ] Ensure source and target branches are different

**PHASE 0 ACTIONS** (commit and push):
- [ ] Stage ALL changes with `git add -A`
- [ ] Commit if there are staged changes (generate appropriate message)
- [ ] Push to remote with `git push -u origin [branch]`
- [ ] Verify push succeeded

**POST-PHASE-0 CHECKS**:
- [ ] Verify source branch is now pushed to remote
- [ ] Verify there are commits between target and source branches
- [ ] Check if PR already exists for this source→target combination

### During PR Creation

**CONTEXT GATHERING**:
- Use `git log` to get commit history
- Use `git diff --name-status` to get changed files
- Parse commit messages for work item IDs (e.g., "#1234", "AB#1234")
- Analyze file paths to determine change types
- Read commit messages to understand intent

### After PR Creation

**POST-CREATION OUTPUT**:
- Output ONLY the PR URL
- No markdown formatting
- No explanatory text
- No suggestions or next steps
- Format: Just the URL itself

## Error Handling

### Commit Failed

**Problem**: Unable to commit staged changes during Phase 0

**Action**:
```
Failed to commit changes.

Error: [git error message]
```

Common causes and recovery:
1. **No changes to commit**: This is not an error - proceed to push existing commits
2. **Pre-commit hook failed**: Report hook failure and ask user to fix or skip hooks
3. **Git configuration issue**: Check git user.name and user.email are configured

### Push Failed

**Problem**: Unable to push branch to remote (after Phase 0 auto-push attempt)

**Action**:
```
Failed to push branch [branch-name] to remote.

Error: [git error message]

Attempting recovery...
```

Recovery steps:
1. If remote has new commits: `git pull --rebase origin [branch-name]` then retry push
2. If conflicts exist: Report conflicts and ask user to resolve manually
3. If permission denied: Report authentication/permission issue (see Authentication Issues below)

### No Commits

**Problem**: Source branch has no commits different from target

**Action**:
```
The source branch [source-branch] has no commits that differ from [target-branch].
Cannot create a PR without changes.

Branches are identical:
- Source: [source-branch]
- Target: [target-branch]

Please make and commit changes to [source-branch] before creating a PR.
```

### PR Already Exists

**Problem**: A PR already exists for this source→target combination

**Action**:
```
A Pull Request already exists for [source-branch] → [target-branch]:
PR #[number]: [title]
URL: [pr-url]

Would you like me to:
1. Update the existing PR description
2. View the existing PR details
3. Cancel

Please specify (1/2/3):
```

### Authentication Issues

**Problem**: Azure CLI authentication failed

**Action**:
```
Azure DevOps authentication failed.

Please authenticate using:
  az login
  az devops login

Then run this command again.
```

### Permission Issues

**Problem**: User lacks permissions to create PR

**Action**:
```
You do not have permission to create Pull Requests in the passage-modernization repository.

Please contact your repository administrator to request:
- Contributor access to the repository
- Permission to create Pull Requests

Repository: passage-modernization
Organization: [org-name]
```

## Examples

### Example 1: Documentation PR

**Scenario**: User has been working on functional analysis for the Company domain

**Command**:
```
/create-pr source: dev/company-analysis target: main
```

**Process**:
1. **Phase 0**: Stage all changes (`git add -A`), commit with message "Add Company domain documentation 🤖 Generated with Claude Code", push to origin
2. Uses source branch: `dev/company-analysis`, target: `main`
3. Finds 25 new markdown files in `docs/entry-points/` (diff between main and dev/company-analysis)
4. Analyzes commits between main and dev/company-analysis
5. Generates title: "Add Company domain functional analysis"
6. Generates description with summary, file list, and context
7. Invokes ado-operator with context (source: dev/company-analysis, target: main)
8. Returns: `https://dev.azure.com/williams-alm/northwest-passage/_git/passage-modernization/pullrequest/123`

### Example 2: Implementation PR

**Scenario**: User has implemented a feature with backend and frontend code

**Command**:
```
/create-pr source: feature/company-api target: main
```

**Process**:
1. **Phase 0**: Stage all changes (`git add -A`), commit with message "Implement Company API changes 🤖 Generated with Claude Code", push to origin
2. Uses source: `feature/company-api`, target: `main`
3. Compares branches to find 15 TypeScript files in `passage-api/`, 8 test files
4. Analyzes commits between main and feature/company-api
5. Generates title: "Implement Company Maintenance API"
6. Generates description with code changes, test coverage
7. Invokes ado-operator with both source and target branches
8. Returns: `https://dev.azure.com/williams-alm/northwest-passage/_git/passage-modernization/pullrequest/124`

### Example 3: Multi-type PR

**Scenario**: User has both documentation and implementation changes

**Command**:
```
/create-pr source: feature/company-with-docs target: main
```

**Process**:
1. **Phase 0**: Stage all changes (`git add -A`), commit with message "Update Company feature with implementation and documentation 🤖 Generated with Claude Code", push to origin
2. Compares source and target, detects mixed changes: docs/ and passage-api/
3. Generates balanced title: "Implement Company feature with documentation"
4. Description sections for both documentation and code
5. Highlights both aspects in summary
6. Invokes ado-operator with source→target branches
7. Returns: `https://dev.azure.com/williams-alm/northwest-passage/_git/passage-modernization/pullrequest/125`

### Example 4: PR to Development Branch

**Scenario**: User wants to merge a feature branch to the development branch

**Command**:
```
/create-pr source: feature/new-ui-component target: dev
```

**Process**:
1. **Phase 0**: Stage all changes (`git add -A`), commit if needed, push to origin
2. Uses source: `feature/new-ui-component`, target: `dev`
3. Compares against dev branch (not main)
4. Generates title based on changes between dev and feature branch
5. Creates PR targeting dev branch
6. Returns: `https://dev.azure.com/williams-alm/northwest-passage/_git/passage-modernization/pullrequest/126`

## Advanced Usage

### Custom PR Title

If the generated title is not appropriate, you can guide me:

```
User: /create-pr source: dev/company target: main
Assistant: https://dev.azure.com/williams-alm/northwest-passage/_git/passage-modernization/pullrequest/123
User: Actually, change the title to "Company Domain: Complete functional specification"
Assistant: [updates PR and returns new URL]
https://dev.azure.com/williams-alm/northwest-passage/_git/passage-modernization/pullrequest/123
```

### Adding Reviewers

After PR creation, you can add reviewers:

```
User: Add Sarah and Mike as reviewers
Assistant: [invokes ado-operator to update PR reviewers]
```

### Linking Work Items

```
User: Link this PR to work item 1234
Assistant: [invokes ado-operator to link work item]
```

## Success Criteria

The command successfully completes when:

- [ ] All outstanding changes (staged and unstaged) are committed
- [ ] Branch is pushed to remote (all commits available in ADO)
- [ ] PR is created in Azure DevOps
- [ ] PR has appropriate title reflecting changes
- [ ] PR description provides clear context and summary
- [ ] ONLY the PR URL is returned (no other text)
- [ ] URL has no markdown formatting (no backticks, no labels)
- [ ] PR is in the correct state (draft/active as appropriate)
- [ ] Source and target branches are correct

## Related Commands

- `/create-command` - Create new slash commands
- `/review-pr` - Review and comment on existing PRs (future)
- `/update-pr` - Update existing PR metadata (future)

---

**Note**: This command delegates PR creation to the ado-operator subagent, which has deep expertise in Azure DevOps operations and the Azure CLI. The ado-operator handles authentication, API communication, error handling, and all ADO-specific concerns.
