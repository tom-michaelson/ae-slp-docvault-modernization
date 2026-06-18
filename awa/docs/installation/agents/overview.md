# Agents

AWA integrates with several off-the-shelf, third-party agents to provide specialized code generation and modification capabilities. These agents are typically run as command-line tools (bash commands) invoked by AWA during workflow execution.

**Integration with these agents is optional**. You only need to install and configure an agent if you plan to utilize its specific capabilities within your AWA workflows. Utilizing these agents requires using the [`Activity - Agent`](/reference/activity/agent-execute.md) within your workflow and selecting one of these installed agents as the provider.

## Supported Agents

<!--@include: ./parts/agent_list.md-->

Each agent has its own installation and configuration process. Please refer to the specific documentation page for the agent you wish to use.
