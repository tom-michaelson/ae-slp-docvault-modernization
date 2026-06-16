# JIRA Test Generation Workflow

An automated Temporal workflow that generates comprehensive test cases from JIRA issues, producing test documentation in CSV and Markdown formats to accelerate test planning and execution.

## Overview

The `jira-to-test-cases` workflow fetches JIRA issues based on custom queries and leverages AI to generate detailed test cases including functional, edge case, negative, and security tests. It supports multiple CSV output formats for integration with various test management tools.

## How It Works

1. **JIRA Query Execution**: Fetches issues from JIRA based on JQL query, project key, or sprint ID
2. **Issue Analysis**: Processes each JIRA issue's summary and description
3. **AI Test Generation**: Uses BAML-powered LLM to generate comprehensive test cases
4. **Format Conversion**: Outputs test cases in specified CSV format (Standard, Azure DevOps, or TestRail)
5. **Documentation Creation**: Generates markdown summary reports alongside test cases

## Key Features

- **Flexible JIRA Queries**: Support for JQL, project keys, and sprint IDs
- **Multiple Test Types**: Generates functional, API, UI, integration, security, performance, negative, and edge case tests
- **Configurable Coverage**: Options to include/exclude edge cases, negative tests, and security tests
- **Priority Management**: Configurable test case priorities (P1, P2, P3)
- **Multi-Format Export**: Support for Standard, Azure DevOps, and TestRail CSV formats
- **Automation Status**: Classifies tests as "Ready for Automation", "Manual Only", or "Needs Review"
- **Comprehensive Reports**: Generates both CSV test cases and markdown summary documentation

## Usage

### Input Parameters

| Parameter                | Description                                  | Required | Default                  |
| ------------------------ | -------------------------------------------- | -------- | ------------------------ |
| `jira_query`             | JQL query to fetch JIRA issues               | No       | -                        |
| `project_key`            | JIRA project key                             | No       | -                        |
| `sprint_id`              | JIRA sprint ID                               | No       | -                        |
| `issue_types`            | Types of issues to include                   | Yes      | ["Story", "Bug", "Task"] |
| `max_issues`             | Maximum number of issues to process          | Yes      | 50                       |
| `include_edge_cases`     | Generate edge case tests                     | Yes      | true                     |
| `include_negative_tests` | Generate negative tests                      | Yes      | true                     |
| `include_security_tests` | Generate security tests                      | Yes      | true                     |
| `test_case_priority`     | Priority levels for test cases               | Yes      | ["P1", "P2", "P3"]       |
| `csv_format`             | Output format: "standard", "ado", "testrail" | Yes      | "standard"               |

### Output

The workflow generates the following files in `./output/jira-to-test-cases/<issue-key>/`:

- `test_cases.csv` - Test cases in the specified CSV format
- `test_cases.md` - Test cases in Markdown format for documentation
- `test_generation_summary.md` - Summary report with statistics and insights

## CSV Formats

### Standard Format

```csv
Test ID,JIRA Issue,Test Name,Test Type,Priority,Preconditions,Test Steps,Expected Results,Test Data,Tags,Automation Status
```

### Azure DevOps Format

```csv
Work Item Type,Title,Test Type,Priority,Steps,Expected Result,Tags,Automation Status,Associated Work Item
```

### TestRail Format

```csv
Title,Section,Type,Priority,Preconditions,Steps,Expected Result,References
```

## Test Types Generated

- **Functional** - Core functionality tests validating main features
- **API** - API endpoint tests for backend services
- **UI** - User interface tests for frontend interactions
- **Integration** - System integration tests between components
- **Security** - Security validation tests for vulnerabilities
- **Performance** - Performance and load tests for scalability
- **Negative** - Error handling and invalid input tests
- **Edge Case** - Boundary condition and limit tests

## Command Line Execution

```bash
# Generate test cases from a JIRA sprint
uv run -m awa.main run -w jira-to-test-cases \
  -i '{"jira_query":"project = PROJ AND sprint in openSprints()","include_security_tests":true}'

# Generate test cases for specific issue types with Azure DevOps format
uv run -m awa.main run -w jira-to-test-cases \
  -i '{"project_key":"MYPROJ","issue_types":["Story","Bug"],"csv_format":"ado","max_issues":25}'
```

## Configuration

### Prerequisites

1. **JIRA Configuration**: Set up JIRA connection in main AWA repository's `config.yaml`
2. **JIRA API Token**: Configure as environment variable
3. **AWA Core Services**: Ensure AWA core services are running

### JIRA Configuration Example

In the main AWA repository's `config.yaml`:

```yaml
jira:
  url: https://your-instance.atlassian.net
  username: your-email@example.com
  api_token: ${JIRA_API_TOKEN}
```

## Troubleshooting

### JIRA Connection Issues

- Verify JIRA configuration in main AWA `config.yaml`
- Check JIRA API token is set as environment variable
- Ensure JIRA user has appropriate permissions to read issues

### Test Generation Issues

- Ensure JIRA issues have sufficient detail in descriptions
- Verify LLM API keys are configured in main AWA
- Review BAML function logs for generation errors
- Check that issue types match those in your JIRA instance

### CSV Parsing Issues

- Ensure CSV format parameter matches expected values
- Check for special characters in test data that may need escaping
- Verify output directory permissions

## Related Workflows

- [Test Doctor Workflow](../test-doctor/test-doctor-workflow.md) - Generates unit tests for code changes
- [PR Description Workflow](../pr-description/PRDescriptionWorkflow.md) - Generates pull request descriptions from git changes
