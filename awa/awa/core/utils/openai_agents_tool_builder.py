"""Factory for creating agent tools from AWA configuration."""

from agents import Agent, Tool

from awa.sdk.models.openai_agents import AgentToolConfig, OpenAIAgentConfig


class AgentToolBuilder:
    """Factory for creating agent tools from AWA configuration."""

    @staticmethod
    def build_agent_tool(
        config: AgentToolConfig | OpenAIAgentConfig,
        target_agent_instance: Agent,
    ) -> Tool:
        """Create an agent tool from configuration.

        Args:
            config: AgentToolConfig or OpenAIAgentConfig
            target_agent_instance: The Agent instance to expose as a tool

        Returns:
            Tool object that wraps the agent

        """
        if isinstance(config, OpenAIAgentConfig):
            # Simple agent reference - use defaults
            tool_name = config.name
            tool_description = f"Use {config.name} agent for specialized tasks"
        else:
            # AgentToolConfig with potential overrides
            tool_name = config.tool_name_override or target_agent_instance.name
            tool_description = config.tool_description_override or f"Use {target_agent_instance.name} agent"

        return target_agent_instance.as_tool(
            tool_name=tool_name,
            tool_description=tool_description,
        )
