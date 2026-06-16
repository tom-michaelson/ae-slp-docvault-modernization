import gradio as gr
from multi_agent_orchestrator.agents import AgentCallbacks, BedrockLLMAgent, BedrockLLMAgentOptions
from multi_agent_orchestrator.orchestrator import MultiAgentOrchestrator
from multi_agent_orchestrator.types import ConversationMessage
from singleton_decorator import singleton
from tools import filesystem_tool_backup, weather_tool


class BedrockLLMAgentCallbacks(AgentCallbacks):
    def on_llm_new_token(self, token: str) -> None:
        # handle response streaming here
        print(token, end="", flush=True)


@singleton(thread_lock=True)
class UIClient:
    _instance = None

    def __init__(self) -> None:
        self.orchestrator = MultiAgentOrchestrator()
        self.register_agents()

    def draw_ui(self):
        """Main entrypoint"""
        gr.ChatInterface(self.chat_responder).launch()

    async def chat_responder(self, question, history):
        """Example Question:
        I am interested in the origin of the spice Melange which enables the spacing guild to traverse the cosmos.  Can you provide any details?
        What is the weather like today in Atlanta, GA?
        How does blockchain work?
        """
        response = await self.orchestrator.route_request(question, "user123", "session456")
        print("\n** HISTORY ** \n")
        print(history)
        # Handle non-streaming response (AgentProcessingResult)
        print("\n** RESPONSE ** \n")
        print(f"> Agent ID: {response.metadata.agent_id}")
        print(f"> Agent Name: {response.metadata.agent_name}")
        print(f"> User Input: {response.metadata.user_input}")
        print(f"> User ID: {response.metadata.user_id}")
        print(f"> Session ID: {response.metadata.session_id}")
        print(f"> Additional Parameters: {response.metadata.additional_params}")
        print(f"\n> Response: {response.output.content}")
        if isinstance(response.output, ConversationMessage):
            return response.output.content[0].get("text")
        return "Error processing response"

    def register_agents(self):
        tech_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="Tech Agent",
                streaming=False,
                description="Specializes in technology areas including software development, hardware, AI, \
            cybersecurity, blockchain, cloud computing, emerging tech innovations, and pricing/costs \
            related to technology products and services.",
                model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                callbacks=BedrockLLMAgentCallbacks(),
            ),
        )
        self.orchestrator.add_agent(tech_agent)

        scifi_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="Science Fiction Agent",
                streaming=False,
                description="Specializes in encyclopedic knowledge of science fiction novels.  Excellent at \
                recognizing genre tropes and identifying award winning novels, particularly the Hugo Award \
                and Nebula award.",
                model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                callbacks=BedrockLLMAgentCallbacks(),
            ),
        )
        self.orchestrator.add_agent(scifi_agent)

        weather_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="Weather Agent",
                streaming=False,
                description="Specialized agent for giving weather condition from a city.",
                tool_config={
                    "tool": weather_tool.weather_tool_description,
                    "toolMaxRecursions": 5,
                    "useToolHandler": weather_tool.weather_tool_handler,
                },
            ),
        )
        weather_agent.set_system_prompt(weather_tool.weather_tool_prompt)
        self.orchestrator.add_agent(weather_agent)

        file_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="FileSystem Agent",
                streaming=False,
                description="Specialized agent for retrieving contents of files used in other tasks.",
                tool_config={
                    "tool": filesystem_tool_backup.file_listing_tool_description,
                    "toolMaxRecursion": 5,
                    "useToolHandler": filesystem_tool_backup.file_listing_tool_handler,
                },
            ),
        )
        file_agent.set_system_prompt(filesystem_tool_backup.file_listing_tool_prompt)
        self.orchestrator.add_agent(file_agent)


if __name__ == "__main__":
    client = UIClient()
    client.draw_ui()
