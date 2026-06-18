# PR Description Workflow Demo Script

## Opening (30 seconds)
"Hello, my name is [USER], and I'm part of the AWA Development Team. Today I'll be demonstrating our PR Description Workflow - an automated tool that generates comprehensive pull request descriptions for your code changes.

This workflow eliminates the manual effort of writing detailed PR descriptions by analyzing your code changes and creating professional summaries automatically."

## Workflow Overview (45 seconds)
"Here's how it works:

**Input Requirements:**
- Branch name (containing your changes - must be pushed to remote)
- Repository path (absolute path required)
- Base branch for comparison (typically 'main' or 'develop')

**Process Flow:**
1. Performs a git diff between your branch and the base branch
2. Analyzes each changed file individually using AI summarization
3. Groups file summaries into batch summaries (optimized for large PRs to avoid context window limits)
4. Generates a comprehensive overall summary
5. Outputs a structured PR description with both high-level overview and file-by-file breakdown"

## Execution Methods (20 seconds)
"This workflow can be executed in two ways:
1. **Command Line Interface** - Direct terminal execution
2. **MCP Server Integration** - Seamless IDE integration

Today I'll demonstrate the MCP server approach for IDE integration."

## Demo Setup (30 seconds)
"Before we begin, let me show you the setup:

First, I've already started our core service, which handles the workflow execution.

*[Point to terminal/service status]*

Important note: This demo uses GitHub Copilot API with GPT-4 for all AI summarization requests, ensuring high-quality output.

Now I need to register the workflow since it's located in our recipes folder."

*[Demonstrate registration process]*

## Live Demonstration (60 seconds)
"Now let's see it in action. I'll ask my AI agent to generate a PR description using our current branch.

*[Type/execute command]*

Notice how the model understands the request context - I've created a rule that helps it identify when someone wants a PR description and what parameters are needed.

Let's monitor the execution in our Temporal UI:

*[Switch to Temporal UI]*

Here we can see:
- The workflow has initiated
- Individual file summarizations are running in parallel
- Each summarization shows the actual diff content being analyzed

*[Click on a specific summarization to show diff content]*

As you can see, it's processing the actual git diff for each file. Now the batch summarization phase is beginning...

*[Return to main interface]*

Perfect! The workflow has completed. Here's our generated PR description:
- **Top section**: Overall summary of all changes
- **Below**: File-by-file breakdown with specific change descriptions"

## Closing (15 seconds)
"This PR Description Workflow streamlines your development process by automatically creating professional, comprehensive pull request descriptions. It scales from small changes to large feature branches, ensuring consistent documentation quality across your team.

Thank you for watching this demonstration of the PR Description Workflow."

---

## Preparation Tips:
- Have all services running before starting
- Test the workflow once before recording
- Keep the Temporal UI open in a separate tab
- Ensure your example branch has meaningful changes to showcase
