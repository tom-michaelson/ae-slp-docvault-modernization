"""OpenAI Agents Demo Workflow - Demonstrates OpenAI Agent agents-as-tools functionality for creating haikus."""

from temporalio import workflow

from cookbook.recipes.constants import AWA_WORKFLOW_OPENAI_AGENTS_SDK_DEMO
from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_workflow
from sdk_dist.python.awa.client.models import AgentToolConfig, HandoffConfig, OpenAIAgentConfig

from .models.openai_agents_sdk_demo_input import OpenAIAgentsSdkDemoInput


@recipe_exposed("Demonstrates OpenAI Agent SDK with agents-as-tools")
@workflow.defn(name=AWA_WORKFLOW_OPENAI_AGENTS_SDK_DEMO)
class OpenAIAgentsSdkDemoWorkflow:
    """A demo workflow that uses the OpenAI Agent SDK workflow with agents-as-tools.

    This workflow demonstrates how to use agents as tools within an orchestrator:
    1. Orchestrator agent manages the overall flow
    2. Jira Operator agent (as tool) fetches Jira issue details
    3. Haiku Author agent (as tool) creates the haiku
    """

    @workflow.run
    async def run(self, workflow_input: OpenAIAgentsSdkDemoInput) -> str:
        """Execute the haiku creation workflow with agents-as-tools.

        Args:
            workflow_input: A OpenAIAgentsDemoInput model containing the topic for the haiku

        Returns:
            A haiku poem as a string

        """
        workflow.logger.info(f"Creating a haiku about: {workflow_input.topic}")

        model = "openai/gpt-4.1"
        # model="bedrock/arn:aws:bedrock:us-east-1:577638363028:inference-profile/us.anthropic.claude-sonnet-4-20250514-v1:0" # noqa: E501

        # Define the Jira Operator agent (no handoffs needed)
        jira_operator = OpenAIAgentConfig(
            name="JiraOperator",
            instructions="""You are a Jira issue operator. Your role is to:
            1. Fetch details from the provided Jira issue ID
            2. Extract and summarize the key information (title, description, status, priority)
            3. Return a concise summary for the haiku author

            Use the Atlassian MCP server to fetch issue details.
            Return the summary in a format useful for poetry creation.""",
            input="Fetch Jira issue details",
            model=model,
            mcp_servers=["atlassian"],
        )

        # Define the Haiku Author agent (no handoffs needed)
        haiku_author = OpenAIAgentConfig(
            name="HaikuAuthor",
            instructions="""You are a masterful haiku poet. Your role is to:
            1. Receive information about a topic (possibly Jira issue details)
            2. Create a beautiful haiku that captures the essence of the topic

            Remember, a haiku has three lines:
            - First line: 5 syllables
            - Second line: 7 syllables
            - Third line: 5 syllables

            Respond with ONLY the haiku, nothing else.""",
            input="Create haiku from provided information",
            model=model,
        )

        # Define the Finisher agent (no handoffs needed)
        finisher = OpenAIAgentConfig(
            name="Finisher",
            instructions="""You are a final formatter agent. Your role is to:
            1. Receive structured input containing a haiku and optional Jira issue key
            2. Format the haiku into ASCII art format with a border and simple graphical header
            3. If a Jira issue key is provided, include it in the header
            4. Return the formatted haiku

            You will receive input as a JSON object with:
            - haiku_content: The haiku poem text to format
            - jira_issue_key: The original Jira issue key (if applicable)

            Respond with ONLY the formatted haiku, nothing else.""",
            input="Format haiku from provided information",
            model=model,
        )

        # Define the Orchestrator agent with agents-as-tools
        orchestrator = OpenAIAgentConfig(
            name="Orchestrator",
            instructions=f"""You are the orchestrator for creating a haiku about: {workflow_input.topic}

            Your workflow:
            1. If the topic looks like a Jira issue ID (e.g., ABC-123), use the fetch_jira_details tool to fetch details
            2. Once you have the topic information, use the create_haiku tool to create a haiku
            3. Hand off to the Finisher agent with structured input containing the haiku and Jira key (if applicable)

            You have access to two specialized agent tools:
            - fetch_jira_details: Fetches Jira issue details
            - create_haiku: Creates beautiful haikus

            When handing off to the Finisher, provide a JSON object with:
            - haiku_content: The haiku poem text
            - jira_issue_key: The original Jira issue key (if the topic was a Jira ID)

            Coordinate between these tools to produce the best result.""",
            input=workflow_input.topic,
            model=model,
            agent_tools=[
                AgentToolConfig(
                    target_agent=jira_operator,
                    tool_name_override="fetch_jira_details",
                    tool_description_override="Fetch details from a Jira issue ID",
                ),
                AgentToolConfig(
                    target_agent=haiku_author,
                    tool_name_override="create_haiku",
                    tool_description_override="Create a haiku from the provided information",
                ),
            ],
            handoffs=[
                HandoffConfig(
                    target_agent=finisher,
                    input_type={
                        "type": "object",
                        "properties": {
                            "haiku_content": {
                                "type": "string",
                                "description": "The haiku poem text to format",
                            },
                            "jira_issue_key": {
                                "type": "string",
                                "description": "The original Jira issue key if the haiku was created from a Jira issue",
                            },
                        },
                        "required": ["haiku_content"],
                    },
                ),
            ],
        )

        # Execute the OpenAI Agent workflow with the orchestrator
        result = await awa_workflow.openai_agent(orchestrator)

        # Handle the result
        if isinstance(result, dict):
            # Check for errors
            if result.get("error", None) is not None:
                workflow.logger.error(f"Agent execution failed: {result['error']}")
                raise RuntimeError(f"Failed to create haiku: {result['error']}")

            workflow.logger.info(f"Haiku created successfully in {result.get('execution_time_seconds', 0):.2f} seconds")
            workflow.logger.info(f"Model used: {result.get('model_used', 'unknown')}")

            # Log agent tool usage events if present
            agent_tool_events = result.get("agent_tool_events", [])
            if agent_tool_events:
                workflow.logger.info(f"Agent tools used: {len(agent_tool_events)}")
                for event in agent_tool_events:
                    workflow.logger.info(
                        f"  - Tool: {event.get('tool_name', 'Unknown')} -> "
                        f"Agent: {event.get('target_agent', 'Unknown')}",
                    )

            return result.get("content", "")

        # Handle as an object
        if result.error:
            workflow.logger.error(f"Agent execution failed: {result.error}")
            raise RuntimeError(f"Failed to create haiku: {result.error}")

        workflow.logger.info(f"Haiku created successfully in {result.execution_time_seconds:.2f} seconds")
        workflow.logger.info(f"Model used: {result.model_used}")

        # Log agent tool events if present
        if hasattr(result, "agent_tool_events") and result.agent_tool_events:
            workflow.logger.info(f"Agent tools used: {len(result.agent_tool_events)}")
            for event in result.agent_tool_events:
                workflow.logger.info(f"  - Tool: {event.tool_name} -> Agent: {event.target_agent}")
        else:
            workflow.logger.info("No agent tool events recorded in result")

        return result.content
