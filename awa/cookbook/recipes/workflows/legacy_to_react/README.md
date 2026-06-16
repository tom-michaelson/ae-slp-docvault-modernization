# Legacy to React Workflow

## Overview

The Legacy to React workflow automates the conversion of legacy COBOL applications into modern React applications. It uses AI-powered analysis to extract requirements, create user stories, implement React components, and ensure quality through automated testing and code review.

## Workflow Steps

1. **Read COBOL File** - Loads the legacy COBOL source code
2. **Extract Requirements** - AI analyzes COBOL to extract business logic, data structures, and UI requirements
3. **Create User Story** - Generates comprehensive user story with acceptance criteria
4. **Save to JIRA** - Creates JIRA issue for tracking the conversion work
5. **Create Implementation Plan** - Develops detailed React implementation strategy
6. **Copy Baseline React App** - Sets up the React application structure
7. **Implement React Component** - Agent implements the React components based on requirements
8. **Code Review** - AI reviews the implementation for quality and compliance
9. **Write Unit Tests** - Agent creates comprehensive test suites
10. **Run Unit Tests** - Executes tests and generates coverage reports
11. **Generate Summary Report** - Creates final documentation of the conversion process

## Input Requirements

```python
class LegacyToReactWorkflowInput(BaseModel):
    cobol_file_path: str | Path = "input/legacy_code.cbl"  # Path to COBOL file
    jira_project_key: str  # JIRA project key for story creation
    jira_instance_url: str  # JIRA instance URL
    react_app_path: str | Path = "input/react-baseline-app"  # Baseline React app
```

## Directory Structure

```
legacy_to_react/
├── README.md                    # This file
├── __init__.py
├── legacy_to_react_workflow.py  # Main workflow implementation
├── models/
│   ├── __init__.py
│   └── workflow_input.py        # Input model definition
├── baml_src/                    # BAML AI functions
│   ├── extract_cobol_requirements.baml
│   ├── create_user_story.baml
│   ├── create_implementation_plan.baml
│   ├── perform_code_review.baml
│   └── generate_summary_report.baml
├── agent_prompts/               # Agent task templates
│   ├── implement_react_component.jinja
│   ├── write_unit_tests.jinja
│   └── run_unit_tests.jinja
└── input/                       # Sample input files
    ├── legacy_code.cbl          # Sample COBOL program
    └── react-baseline-app/      # Baseline React application

```

## Sample COBOL Input

The workflow includes a sample COBOL customer management system (`legacy_code.cbl`) that demonstrates:

- File I/O operations
- Data validation
- Screen interactions
- Report generation
- Business logic (high-value customer identification)

## Output Structure

After successful execution, the workflow generates:

```
output/
├── report.md                    # Comprehensive conversion report
├── react-app/                   # Converted React application
│   ├── src/
│   │   ├── components/         # New React components
│   │   └── __tests__/          # Unit tests
│   └── package.json
├── code-review-report.md        # Detailed code review findings
└── test-results.json           # Unit test execution results
```

## Running the Workflow

### Prerequisites

1. Temporal server running
2. JIRA credentials configured
3. Node.js environment for React development

### Example Usage

```python
from temporalio.client import Client
from cookbook.recipes.workflows.legacy_to_react import LegacyToReactWorkflow, LegacyToReactWorkflowInput

async def run_workflow():
    client = await Client.connect("localhost:7233")

    result = await client.execute_workflow(
        LegacyToReactWorkflow.run,
        LegacyToReactWorkflowInput(
            cobol_file_path="input/legacy_code.cbl",
            jira_project_key="PROJ",
            jira_instance_url="https://your-jira.atlassian.net",
            react_app_path="input/react-baseline-app"
        ),
        id="legacy-to-react-conversion-001",
    )

    print(f"Workflow completed: {result}")
```

## Key Features

### AI-Powered Analysis

- Automatic extraction of business requirements from COBOL
- Intelligent user story generation
- Code quality review and recommendations

### Agent-Based Implementation

- Autonomous React component creation
- Automated test generation
- Test execution and reporting

### Quality Assurance

- Comprehensive code review
- Unit test coverage analysis
- Requirements traceability

### Documentation

- Detailed conversion report
- JIRA integration for project tracking
- Code review documentation

## Customization

### Adding New COBOL Patterns

To support additional COBOL patterns, modify the `extract_cobol_requirements.baml` function to recognize new structures.

### React Implementation Strategies

Update `create_implementation_plan.baml` to include specific architectural patterns or libraries your organization prefers.

### Testing Frameworks

The workflow uses Jest and React Testing Library by default. Modify `write_unit_tests.jinja` to use different testing frameworks.

## Troubleshooting

### Common Issues

1. **JIRA Connection Failed**

   - Verify JIRA credentials and URL
   - Check network connectivity
   - Ensure JIRA API access is enabled

2. **React Build Errors**

   - Ensure Node.js and npm are installed
   - Check that all dependencies are properly specified
   - Review agent implementation logs

3. **Test Failures**
   - Check test execution logs in output
   - Review coverage reports for untested code
   - Verify acceptance criteria mapping

## Best Practices

1. **COBOL Preparation**

   - Ensure COBOL code is well-formatted
   - Include comments for complex business logic
   - Provide complete program files

2. **React App Baseline**

   - Use a properly configured TypeScript React app
   - Include necessary dependencies upfront
   - Provide clear project structure

3. **Workflow Monitoring**
   - Monitor Temporal UI for progress
   - Check intermediate outputs
   - Review agent execution logs

## Future Enhancements

- Support for batch COBOL file processing
- Additional legacy languages (FORTRAN, Pascal)
- CI/CD pipeline integration
- Performance comparison metrics
- Multi-framework support (Vue, Angular)
