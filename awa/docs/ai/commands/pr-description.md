# Pull Request Description Generation

## Configuration

```yaml
cursor:
  description: "Generate pull request descriptions using AWA MCP workflow"
  globs:
  alwaysApply: false
  include_in_index: true

copilot:
  output_type: "instructions"
  description: "Pull request description generation using AWA MCP server workflow"
  applyTo: '**/*'
  include_in_index: true

claude:
  command_name: "pr-description"
  description: "Generate PR descriptions using AWA MCP workflow"
  include_in_index: true

opencode:
  command_name: "pr-description"
  description: "Generate PR descriptions using AWA MCP workflow"
  include_in_index: true
```

# Create a Pull Request Description with AWA

When you need to create a pull request description, use the AWA MCP server by running the `pr-description` workflow.

## Tool and Parameters

- **Tool**: `mcp_awa_start_workflow`
- **Workflow**: `pr-description`
- **Task Queue**: Default (`awa_default`)

### Input Parameters

The workflow requires a JSON input with the following keys:

- `branch_name`: The name of your feature or hotfix branch.
- `base_branch`: The target branch for the pull request (e.g., `main` or `develop`).
- `repo_path`: The absolute path to the local repository.

### Example

```json
{
  "branch_name": "hotfix/cognito-fix",
  "base_branch": "main",
  "repo_path": "~/Projects/AWA/agentic-workflow-accelerator"
}
```

### Repository Path Shortcuts

For the `repo_path` parameter, you can use the following shortcut:

- If working in "AWA" (which includes both core and cookbook): `~/Projects/AWA/agentic-workflow-accelerator`

**Important**: Ensure the repository path is correct and exists on your local machine before running the workflow. Note that the cookbook is now part of the main AWA repository under the `cookbook/` directory.

### Missing Parameters

If you are missing any of the required parameters (`branch_name`, `base_branch`, `repo_path`), you will be prompted to provide them.
