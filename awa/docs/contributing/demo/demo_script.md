# Training Video Demo Template

## Pre-Recording Checklist

- [ ] Script fully written and rehearsed
- [ ] Audio levels tested and optimized
- [ ] All applications/services running smoothly
- [ ] Test scenarios validated and working
- [ ] Desktop cleaned (close unnecessary applications)
- [ ] Notifications disabled
- [ ] Recording software configured
- [ ] Backup examples prepared

## Video Structure Template

### Section 1: Introduction

**[SCREEN: Title slide or clean desktop]**
**[AUDIO: Clear, welcoming tone]**

"Hello, my name is [YOUR NAME], and I'm part of the [TEAM NAME]. Today I'll be demonstrating [FEATURE/TOOL NAME] - [BRIEF DESCRIPTION OF WHAT IT DOES].

This [FEATURE/TOOL] [KEY BENEFIT STATEMENT - how it helps users]."

**Example:**

"Hello, my name is Rob Forshier, and I'm part of the AWA Development Team. Today I'll be demonstrating our PR Description Workflow - an automated tool that generates comprehensive pull request descriptions for your code changes.

This workflow eliminates the manual effort of writing detailed PR descriptions by analyzing your code changes and creating professional summaries automatically."

**Visual Cues:**

- Show title/topic clearly
- Keep intro personal and welcoming
- Focus on the value proposition

---

### Section 2: How It Works Overview

**[SCREEN: Show workflow diagram or documentation]**

"Here's how it works:

**Input Requirements:**

- [INPUT/REQUIREMENT 1] - [BRIEF EXPLANATION]
- [INPUT/REQUIREMENT 2] - [BRIEF EXPLANATION]
- [INPUT/REQUIREMENT 3] - [BRIEF EXPLANATION]

**Process Flow:**

1. [STEP 1 WITH ACTION VERB]
2. [STEP 2 WITH ACTION VERB]
3. [STEP 3 WITH ACTION VERB]
4. [STEP 4 WITH ACTION VERB]
5. [FINAL OUTPUT DESCRIPTION]"

**Example:**
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

---

### Section 3: Usage Options

**[SCREEN: Show different interfaces/methods]**

"This [FEATURE/TOOL] can be [USED/EXECUTED] in [NUMBER] ways:

1. **[METHOD 1]** - [BRIEF DESCRIPTION]
2. **[METHOD 2]** - [BRIEF DESCRIPTION]

Today I'll demonstrate the [CHOSEN METHOD] approach [REASON FOR CHOICE]."

**Example:**
"This workflow can be executed in two ways:

1. **Command Line Interface** - Direct terminal execution
2. **MCP Server Integration** - Seamless IDE integration

Today I'll demonstrate the MCP server approach for IDE integration."

---

### Section 4: Setup & Prerequisites

**[SCREEN: Setup interface/terminal]**

"Before we begin, let me show you the setup:

First, I've already [PREPARATION COMPLETED], which [PURPOSE/FUNCTION].

_[Point to relevant screen elements]_

Important note: [KEY CONFIGURATION/TECHNICAL DETAIL]

Now I need to [FINAL SETUP ACTION]."

**Example:**
"Before we begin, let me show you the setup:

First, I've already started our core service, which handles the workflow execution.

_Point to terminal/service status_

Important note: This demo uses GitHub Copilot API with GPT-4 for all AI summarization requests, ensuring high-quality output.

Now I need to register the workflow since it's located in our recipes folder."

**Visual Cues:**

- Show where to find required items
- Highlight important access points
- Demonstrate any setup steps

---

### Section 5: Step-by-Step Demonstration

**[SCREEN: Application interface]**
**[PACE: Deliberate and clear]**

"Now let's see it in action. I'll [DESCRIBE WHAT YOU'RE ABOUT TO DO].

_[Execute primary action]_

Notice how [EXPLAIN IMMEDIATE FEEDBACK/RESPONSE].

Let's monitor the execution in our [MONITORING TOOL]:

_[Switch to monitoring interface]_

Here we can see:

- [OBSERVATION 1]
- [OBSERVATION 2]
- [OBSERVATION 3]

_[Click/interact with specific element]_

As you can see, [EXPLAIN WHAT'S VISIBLE]. Now [DESCRIBE NEXT PHASE]...

_[Return to main interface]_

Perfect! [DESCRIBE COMPLETION]. Here's our [FINAL OUTPUT]:

- **[OUTPUT SECTION 1]**: [DESCRIPTION]
- **[OUTPUT SECTION 2]**: [DESCRIPTION]"

**Example:**
"Now let's see it in action. I'll ask my AI agent to generate a PR description using our current branch.

_Type/execute command_

Notice how the model understands the request context - I've created a rule that helps it identify when someone wants a PR description and what parameters are needed.

Let's monitor the execution in our Temporal UI:

_Switch to Temporal UI_

Here we can see:

- The workflow has initiated
- Individual file summarizations are running in parallel
- Each summarization shows the actual diff content being analyzed

_Click on a specific summarization to show diff content_

As you can see, it's processing the actual git diff for each file. Now the batch summarization phase is beginning...

_Return to main interface_

Perfect! The workflow has completed. Here's our generated PR description:

- **Top section**: Overall summary of all changes
- **Below**: File-by-file breakdown with specific change descriptions"

**Visual Cues:**

- Use cursor highlights/circles for key clicks
- Zoom in on small interface elements
- Pause after each major action
- Show both process and results clearly

---

### Section 6: Key Points & Benefits

**[SCREEN: Summary slide or highlight key interface elements]**

"Let me highlight the key benefits:

- **[BENEFIT 1]**: [EXPLANATION]
- **[BENEFIT 2]**: [EXPLANATION]
- **[BENEFIT 3]**: [EXPLANATION]

This [FEATURE/TOOL] [OVERALL VALUE STATEMENT]."

**Example:**
"Let me highlight the key benefits:

- **Automation**: Eliminates manual PR description writing
- **Consistency**: Ensures professional documentation quality
- **Scalability**: Works for both small changes and large feature branches

This workflow streamlines your development process while maintaining high documentation standards."

---

### Section 7: Wrap-up

**[SCREEN: Summary or clean desktop]**

"This [FEATURE/TOOL NAME] [CORE VALUE STATEMENT]. It [KEY BENEFITS], ensuring [QUALITY OUTCOME].

Thank you for watching this demonstration of [FEATURE/TOOL NAME]."

**Example:**
"This PR Description Workflow streamlines your development process by automatically creating professional, comprehensive pull request descriptions. It scales from small changes to large feature branches, ensuring consistent documentation quality across your team.

Thank you for watching this demonstration of the PR Description Workflow."

## Template Variables

### Basic Information

| Variable                  | Your Value                                                            |
| ------------------------- | --------------------------------------------------------------------- |
| `[YOUR NAME]`             | Rob Forshier                                                          |
| `[TEAM NAME]`             | AWA Development Team                                                  |
| `[FEATURE/TOOL NAME]`     | PR Description Workflow                                               |
| `[BRIEF DESCRIPTION]`     | automated tool that generates comprehensive pull request descriptions |
| `[KEY BENEFIT STATEMENT]` | eliminates the manual effort of writing detailed PR descriptions      |

### Technical Details

| Variable                    | Your Value                                     |
| --------------------------- | ---------------------------------------------- |
| `[INPUT/REQUIREMENT 1/2/3]` | Branch name, Repository path, Base branch      |
| `[STEP 1-5]`                | Process flow steps                             |
| `[METHOD 1/2]`              | Command Line Interface, MCP Server Integration |
| `[MONITORING TOOL]`         | Temporal UI                                    |
| `[FINAL OUTPUT]`            | Generated PR description                       |

## Recording Best Practices

### Audio Guidelines

- **Microphone**: Use external mic, not computer built-in
- **Environment**: Record in quiet space, avoid echo
- **Pace**: Speak 20% slower than normal conversation
- **Tone**: Professional but friendly, conversational
- **Pauses**: Allow natural pauses between major steps

### Visual Guidelines

- **Cursor Movement**: Slow and deliberate
- **Highlighting**: Use cursor highlights, zoom, or annotations
- **Text Size**: Ensure all text is readable at training platform resolution
- **Screen Real Estate**: Keep important actions in center 2/3 of screen
- **Transitions**: Smooth movements between interface sections

### Content Guidelines

- **One Concept Per Video**: Focus on single workflow/feature
- **Show, Don't Just Tell**: Demonstrate every step visually
- **Realistic Examples**: Use data/scenarios learners will recognize
- **Error Handling**: Show what success looks like vs. common errors
- **Accessibility**: Describe what you're clicking for screen readers
