# GitHub PR Description Workflow

An advanced Temporal workflow that automatically generates comprehensive pull request descriptions using GitHub APIs, with support for incremental updates and automated pipeline integration.

## Overview

The `github-pr-description` workflow enhances the basic PR Description workflow by integrating directly with GitHub's APIs to provide more sophisticated features like incremental updates, metadata tracking, and seamless CI/CD integration. This workflow is designed for production use in GitHub Actions pipelines and provides intelligent change detection to avoid unnecessary regeneration.

## Key Features

- **GitHub API Integration** - Direct integration with GitHub REST APIs for PR and commit data
- **Incremental Updates** - Smart detection of new commits since last update with automatic timestamp-only updates
- **Metadata Tracking** - Automatic generation of metadata tables with commit SHAs and timestamps
- **CI/CD Ready** - Designed for GitHub Actions automation with Dagger-based pipeline runner
- **Performance Optimized** - Controlled concurrency for file processing and efficient pagination for large PRs

## How It Works

1. **PR Analysis**: Fetches PR details from GitHub API to get branch information
2. **Change Detection**: Determines if full or incremental processing is needed based on existing metadata
3. **Commit Processing**: Retrieves new commits since last update (incremental) or all commits (full)
4. **File Analysis**: Gets changed files using GitHub's PR files API with pagination
5. **AI Summarization**: Uses BAML functions to summarize each file's changes
6. **Description Generation**: Creates comprehensive PR description with metadata table
7. **GitHub Update**: Updates the PR description using GitHub's issue API

## Usage

### Input Parameters

The workflow requires a `GitHubPrDescriptionWorkflowInput` object with:

- `owner`: GitHub repository owner (e.g., "slalombuild")
- `repo`: GitHub repository name (e.g., "agentic-workflow-accelerator-helper")
- `pull_number`: PR number to update (e.g., 42)
- `base_branch`: _(Optional)_ Base branch to compare against (auto-detected if not provided)
- `branch_name`: _(Optional)_ Feature branch name (auto-detected if not provided)

### Output

Returns a markdown-formatted string containing:

- **Summary section**: High-level overview of all changes
- **File-by-File Changes section**: Detailed breakdown of what changed in each file
- **AWA Generation Info table**: Metadata with last processed commit and timestamp

### Command Line Execution

```bash
# Basic usage - let workflow auto-detect branches from PR
uv run -m awa.main run -w "github-pr-description" -i '{
  "owner": "slalombuild",
  "repo": "agentic-workflow-accelerator-helper",
  "pull_number": 42
}'
```

```bash
# Explicit branch specification
uv run -m awa.main run -w "github-pr-description" -i '{
  "owner": "slalombuild",
  "repo": "agentic-workflow-accelerator-helper",
  "pull_number": 42,
  "base_branch": "main",
  "branch_name": "feature/new-functionality"
}'
```

## Example Output

```markdown
## Summary

This PR introduces a new authentication system with JWT token support and enhances the user management interface. The changes include new API endpoints for login/logout, secure password hashing, and improved error handling throughout the authentication flow.

## File-by-File Changes

- `src/auth/jwt.py`: New module implementing JWT token generation and validation with configurable expiration times
- `src/api/auth_routes.py`: Added login and logout endpoints with proper error handling and rate limiting
- `src/models/user.py`: Enhanced User model with password hashing methods and authentication status tracking
- `src/frontend/components/LoginForm.jsx`: New React component for user authentication with form validation
- `tests/test_auth.py`: Comprehensive test suite covering authentication flows and edge cases

---

### 🤖 AWA Generation Info

| Metric                | Value                                                                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------- |
| Last Processed Commit | [`abc1234`](https://github.com/slalombuild/my-repo/commit/abc1234567890abcdef1234567890abcdef123456) |
| Last Updated          | 2024-01-15 14:30:25 UTC                                                                              |
```

## Advanced Features

### Incremental Processing

The workflow automatically detects when a PR description has been previously generated and intelligently processes only new changes:

- **First Run**: Processes all commits and files in the PR
- **Subsequent Runs**: Only processes commits added since last update
- **No Changes**: Updates only the timestamp when no new commits are found

### MCP Server Integration

The workflow can be executed through MCP servers for integration with AI development tools:

```json
{
  "workflow": "github-pr-description",
  "workflow_input": {
    "owner": "slalombuild",
    "repo": "my-project",
    "pull_number": 123
  }
}
```

## Pipeline Integration

This workflow is designed to work seamlessly with GitHub Actions pipelines. See the following guides for implementation:

- [**GitHub Actions Integration**](./github-actions-integration.md) - Complete setup guide for GitHub Actions
- [**Pipeline Runner**](./pipeline-runner.md) - Dagger-based pipeline implementation details

## Configuration Requirements

### Environment Variables

- `GH_PERSONAL_ACCESS_TOKEN`: GitHub personal access token with repo permissions
- `OPENAI_API_KEY`: OpenAI API key for AI summarization (or other supported LLM providers)
- `AWS_ACCESS_KEY_ID`: AWS access key for CodeArtifact authentication (CI/CD environments)
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for CodeArtifact authentication (CI/CD environments)
- `AWS_SESSION_TOKEN`: AWS session token for CodeArtifact authentication (CI/CD environments)
- `AWS_DEFAULT_REGION`: AWS region for CodeArtifact domain (default: us-east-1)

### GitHub Token Permissions

The GitHub token requires the following permissions:

- `repo` - Full repository access
- `pull_requests:write` - Update PR descriptions
- `contents:read` - Read repository contents

### AWS CodeArtifact Requirements

The workflow requires access to AWS CodeArtifact for private SDK packages:

**Local Development:**

- AWS CLI configured with profile `slalom-codeartifact`
- Profile must have CodeArtifact permissions for domain `your-domain` in account `YOUR_CODEARTIFACT_ACCOUNT_ID`

**CI/CD Environments:**

- GitHub Actions OIDC integration with AWS IAM role
- Role must have permissions to access CodeArtifact or assume cross-account roles
- Required IAM policies: `AWSCodeArtifactReadOnlyAccess` or custom CodeArtifact permissions

## Comparison with Basic PR Description Workflow

| Feature              | Basic PR Description   | GitHub PR Description        |
| -------------------- | ---------------------- | ---------------------------- |
| **Data Source**      | Local git commands     | GitHub MCP Server            |
| **Updates**          | Full regeneration      | Full or Incremental updates  |
| **Metadata**         | None                   | Commit tracking & timestamps |
| **Pipeline Ready**   | Manual execution       | GitHub Actions integrated    |
| **Branch Detection** | Manual specification   | Auto-detection from PR       |
| **Performance**      | Good for small changes | Optimized for large PRs      |

## Troubleshooting

### Common Issues

**Authentication Errors**

- Verify `GH_PERSONAL_ACCESS_TOKEN` is set correctly
- Ensure token has required repository permissions

**CodeArtifact Access Issues**

- **Local Development**: Ensure AWS profile `slalom-codeartifact` is configured and has access to domain `slalom-all`
- **CI/CD**: Verify OIDC integration is set up correctly and role has CodeArtifact permissions
- Check AWS region configuration (domain must be in `us-east-1`)
- Verify cross-account permissions if using role assumption

**Rate Limiting**

- The workflow includes automatic retry policies
- Large PRs may take longer due to GitHub API rate limits

**Empty Descriptions**

- Check that the PR has actual file changes
- Verify the base and head branches are correctly specified

**Pipeline Failures**

- Check CodeArtifact authentication in pipeline logs
- Verify all required environment variables are set
- Review AWA services startup logs for dependency issues

**Incremental Updates Not Working**

- Ensure previous runs completed successfully and generated metadata
- Check that the metadata table format is preserved in the PR description
