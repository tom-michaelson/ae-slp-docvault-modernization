# Agent Streaming

Watch your AI agents work in real-time. Agent streaming lets you see what your agents are doing as they execute tasks, providing live updates, progress tracking, and detailed insights into agent behavior.

## What is Agent Streaming?

When you run workflows that use AI agents, agent streaming shows you:

- **Live progress updates** - See what the agent is doing right now
- **Step-by-step execution** - Watch each action the agent takes
- **Real-time output** - View agent responses as they're generated
- **Multiple agent tracking** - Monitor several agents working simultaneously

Think of it like watching a progress bar, but instead of just seeing a percentage, you see exactly what's happening at each step.

## Which Workflows Support Streaming?

Agent streaming is available for workflows that execute AI agents, including:

- **Agent Execution** (`awa-execute-agent`) - Direct agent task execution
- **Test Doctor** - Automated test fixing
- **Test and Lint Pipeline** - Code quality improvements
- Custom workflows built with agent streaming support

:::tip
Not sure if a workflow supports streaming? Look for the **Agents** tab when viewing the workflow run details.
:::

## Viewing Agent Streams

### Step 1: Start a Workflow

Execute a workflow that supports agent streaming. The workflow will automatically create streaming sessions when agents are involved.

### Step 2: Navigate to Run Details

1. Go to the **Workflows** page in the AWA UI
2. Find your workflow run in the list
3. Click the workflow ID to open the run details page

### Step 3: Open the Agents Tab

On the run details page, click the **Agents** tab. This tab appears automatically for workflows that support streaming.

You'll see:

- **Active sessions** - Currently running agents
- **Completed sessions** - Finished agent executions
- **Parent session** - The consolidated view of all agent activity

<img src="/images/agent-tab-navigation.png" alt="Navigating to Agent Streaming" />

### Step 4: Select a Stream to View

Choose which stream you want to watch:

#### Parent Stream (Recommended for Overview)

- Shows all agent activity in one place
- Best for understanding the big picture
- See how multiple agents coordinate
- Track overall workflow progress

#### Individual Agent Streams (Best for Debugging)

- Focus on one specific agent
- See detailed step-by-step execution
- Review agent-specific outputs
- Diagnose issues with a particular agent

## Understanding Stream Events

<img src="/images/agent-execution-output.png" alt="Viewing Agent Execution Stream" />

As you watch the stream, you'll see different types of events:

### 💬 Messages

General updates and information from the agent

```
Starting code analysis...
Found 3 files to process
```

### 📊 Progress Updates

Visual progress bars showing completion status

```
Processing files (3/10 - 30%)
```

### ▶️ Step Started

Agent beginning a new action

```
▶️ Analyzing test_example.py
```

### ✅ Step Completed

Agent finished an action successfully

```
✅ Fixed 2 linting issues in test_example.py
```

### ❌ Step Error

Something went wrong during execution

```
❌ Failed to parse config.json: Invalid JSON
```

### 📄 File Events

File operations performed by the agent

```
File completed: src/main.py - Added type hints
```

### 🤖 Agent Actions

Specific agent operations and tool usage

```
Agent claude: Running tests on modified files
```

## Real-Time Features

### Live Updates

Streams update automatically as agents work - no need to refresh the page. New messages appear instantly.

### Auto-Scroll

The stream automatically scrolls to show the latest activity. You can pause auto-scroll by scrolling up to review earlier events.

### Status Indicators

- **🟢 Running** - Agent is currently active
- **✅ Completed** - Agent finished successfully
- **❌ Failed** - Agent encountered an error
- **⏸️ Waiting** - Agent is idle or waiting

### Timestamps

Every event shows when it occurred, helping you understand timing and sequence.

## Common Use Cases

### Monitoring Long-Running Tasks

For workflows that take several minutes, streaming lets you:

- Confirm the agent is making progress
- See which step is taking the longest
- Catch issues early instead of waiting for completion

### Debugging Agent Behavior

When something goes wrong, streams help you:

- See exactly where the agent failed
- Review the sequence of actions leading to the error
- Understand what the agent was trying to do

### Understanding Multi-Agent Workflows

For complex workflows with multiple agents:

- See how agents hand off work to each other
- Track which agent is responsible for what
- Understand the coordination between agents

### Providing User Feedback

If you're building applications for end users:

- Show real-time progress updates
- Build trust by demonstrating what's happening
- Provide transparency in AI operations

## Tips for Best Experience

### Use Parent Stream for Overview

Start with the parent stream to see all activity. Switch to individual agent streams only when you need detailed debugging.

### Watch for Error Patterns

If you see repeated errors, the agent might need different instructions or configuration.

### Monitor Performance

Notice which steps take the longest - this can help optimize your workflows.

### Save Important Outputs

Stream data is temporary. If you see important information, note it down or ensure it's captured in the workflow output.

## Troubleshooting

### I don't see the Agents tab

- The workflow may not support agent streaming
- The workflow might not have executed any agents yet
- Try refreshing the page after the workflow has started

### Stream isn't updating

- Check your internet connection
- Ensure WebSockets aren't blocked by your network
- Try refreshing the browser page
- Check if the workflow is still running

### Missing messages or gaps in the stream

- Network interruptions can cause missed messages
- The workflow run history shows the complete execution record
- Stream is for real-time monitoring, not permanent storage

### Can't see specific agent details

- Make sure you've selected the correct agent session
- The parent stream may aggregate details differently
- Some agent-specific data only appears in individual agent streams

## Developer Resources

For technical details on implementing agent streaming in your own workflows, see the [Agent Streaming Development Guide](/development/agent-streaming.md).

## Related Features

- [Agents](/usage/features/agents.md) - Learn about AI agent capabilities
- [Workflow Registration](/usage/features/workflow-registration.md) - Create custom workflows
