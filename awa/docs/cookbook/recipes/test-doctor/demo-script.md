# Test Doctor Workflow Demo Script

## Demo-Specific Setup & Pre-Recording Checklist

### Repository Preparation

1. **Feature Branch**: Create a branch with new code files that lack corresponding tests
2. **Testing Guidelines**: Prepare a testing guidelines file with project-specific standards
3. **File Types**: Ensure sample files use supported extensions (py, ts, cs)
4. **Clean State**: Start with no existing test files for the demo files

### Expected Outcomes

- Multiple test files generated simultaneously
- Clear demonstration of parent-child workflow orchestration
- Visual proof of two-stage pipeline (generation + linting)
- Executable tests that pass validation

### Pre-Recording Checklist

- [ ] Script fully written and rehearsed
- [ ] Audio levels tested and optimized
- [ ] All applications/services running smoothly
- [ ] Notifications disabled
- [ ] Recording software configured
- [ ] Backup examples prepared
- [ ] AWA core service running

## Video Structure Template

### Section 1: Introduction

**[SCREEN: Title slide or clean desktop]**
**[AUDIO: Clear, welcoming tone]**

"Hello, my name is [YOUR NAME], and I'm part of the AWA Development Team. Today I'll be demonstrating our Test Doctor Workflow – an intelligent Temporal workflow that automatically generates comprehensive unit tests for changed files in a pull request, and immediately applies linting and code quality fixes to those tests.

- Focus on the value proposition of automated test generation

---

### Section 2: How It Works & Usage

**[SCREEN: Show workflow diagram, then command and parameters]**

"Let's walk through how the Test Doctor Workflow operates and how you can use it:

**Input Requirements:**

| Parameter                 | Description                                |
| ------------------------- | ------------------------------------------ |
| `branch_name`             | Name of your feature branch                |
| `base_branch`             | Branch to compare against (main/develop)   |
| `repo_path`               | Absolute path to your repository           |
| `working_directory`       | Directory (relative to repo) to run in     |
| `testing_guidelines_path` | Path to your testing guidelines file       |
| `file_extensions`         | File types to process (e.g., py, ts, cs)   |
| `tests_directory`         | Where to output generated tests (relative) |

**Process Flow:**

1. Performs git analysis between your branch and the base branch
2. Filters files based on specified extensions and excludes existing test files
3. Orchestrates child workflows for each file with controlled concurrency
4. Each child workflow implements a two-stage pipeline:
   - Test Generation Agent: AI-powered creation of comprehensive unit tests
   - Test Linting Agent: Code quality validation using ruff linter
5. Outputs fully formatted, validated unit tests following your project guidelines

---

### Section 4: Setup & Prerequisites

**[SCREEN: Setup interface/terminal]**

"Before we begin, let me show you the setup:

First, I've already started our AWA core service, which handles the workflow execution and Temporal orchestration.

_Point to terminal/service status_

Before we kick off the workflow execution, let's establish a baseline for our code quality and test coverage. I'll run the following commands to show the current state:

```bash
make test-coverage
make lint
# Show all file names changed in this branch compared to the remote base branch:
git diff --name-only main | grep '\.py$'
```

This will:

- Show the current test coverage
- Run linting to display any existing issues
- List all files changed in this branch (file names only)

Important note: This demo uses a test branch specifically prepared to showcase different scenarios:

- One file has broken unit tests that will need to be fixed and covered comprehensively
- One file does not have any tests at all and will require full test generation
- One file already has good code coverage, so when the agent runs, it should detect this and skip generating new tests for that file

We also have testing guidelines configured to ensure the generated tests follow our project standards.

---

### Section 5: Step-by-Step Demonstration

**[SCREEN: Application interface]**
**[PACE: Deliberate and clear]**

Now let's see it in action. I'm going to execute our bash command to run the Test Doctor workflow and generate unit tests for all changed Python files in our feature branch.

Here is the command I'll use for this demo:

```bash
uv run -m awa.main run -w test-doctor -i '{
  "branch_name": "demo/test-doctor",
  "base_branch": "main",
  "repo_path": "/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator-cookbook",
  "working_directory": "recipes",
  "testing_guidelines_path": "recipes/workflows/test_doctor/input/testing_guidelines.md",
  "file_extensions": "py",
  "tests_directory": "recipes/tests"
}'
```

_Execute command through MCP interface_

Let's monitor the execution in our Temporal UI:

_Switch to Temporal UI_

Here we can see:

- The parent test-doctor workflow has initiated
- Multiple child Test and Lint Pipeline workflows are spawning for each file
- Each child workflow shows the two-stage process: test generation and linting
- The workflows are running in parallel with controlled concurrency

_Click on a specific child workflow to show detailed execution_

As you can see, each file is being processed through the two-agent approach. The test generation agent is creating comprehensive unit tests with timeout decorators, and then the linting agent applies code quality standards.

_Return to main interface_

---

### Section 6: Key Points & Benefits

**[SCREEN: Summary slide or highlight key interface elements]**

"Let me highlight the key benefits:

- **Intelligent Analysis**: Automatically identifies which files need testing based on git changes
- **Parallel Processing**: Generates tests for multiple files simultaneously with controlled concurrency
- **Two-Stage Pipeline**: Separates test generation from code quality validation for better reliability
- **AI-Powered**: Creates comprehensive unit tests that understand source code functionality
- **Quality Assured**: Applies linting and formatting standards automatically
- **Guideline Compliance**: Uses your custom testing guidelines to ensure project standards

This workflow transforms the tedious task of writing unit tests into an automated, intelligent process that maintains high code quality standards while saving significant development time."

---

### Section 7: Let It Run

**[SCREEN: Temporal UI running, muted audio]**

"Now that the workflow is running, this process may take a little while depending on the number of files and the complexity of the code. During this time, I'll mute myself and let the workflow complete. I'll keep refreshing the Temporal UI to monitor progress."

Once the workflow finishes, I'll show the UI to confirm that all tasks have completed successfully.

// --- Break for demo running (this section will be cut in post-production) ---

---

### Section 8: Wrap-up

**[SCREEN: Summary or clean desktop]**

Perfect! The workflow has completed. Here's what was generated:

- **Test Files**: Individual test files created for each source file
- **Quality Assured**: All tests pass ruff linting standards
- **Executable**: Generated tests include proper imports and can be run immediately
- **Guidelines Compliant**: Tests follow our project-specific testing guidelines

I'll re-run the following commands to show the updated state:

```bash
make test-coverage
make lint
git status
```

This will demonstrate the improved test coverage and code quality after the workflow has finished. I'll discuss how the test coverage has changed and whether there are any remaining linting errors.

The Test Doctor Workflow revolutionizes how we approach test coverage by automatically generating comprehensive, high-quality unit tests for changed files. It combines intelligent git analysis, AI-powered test generation, and automated code quality validation to ensure your projects maintain excellent test coverage without manual effort.

Thank you for watching this demonstration of the Test Doctor Workflow."

## Post-Production Checklist

Next, go through the post demo recording workflow for steps on editing, hosting, and publishing your demo video.
