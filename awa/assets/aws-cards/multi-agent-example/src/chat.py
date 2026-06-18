"""Testing out the AWS multi-agent orchestrator library"""

import os
import shutil

import boto3
import gradio as gr
from botocore.config import Config
from multi_agent_orchestrator.agents import AgentCallbacks, BedrockLLMAgent, BedrockLLMAgentOptions
from multi_agent_orchestrator.orchestrator import MultiAgentOrchestrator
from multi_agent_orchestrator.types import ConversationMessage
from tools import filesystem_tool


class BedrockLLMAgentCallbacks(AgentCallbacks):
    """Generic agent callback"""

    def on_llm_new_token(self, token: str) -> None:
        # handle response streaming here
        print(token, end="", flush=True)


class UIClient:
    """Generic wrapper class for gradio UI"""

    def __init__(self) -> None:
        self.orchestrator = MultiAgentOrchestrator()
        self.register_agents()

    def draw_ui(self):
        """Main entrypoint"""
        gr.ChatInterface(self.chat_responder).launch()

    async def chat_responder(self, question, history):
        """Example Question:
        As a Cobol Developer, which files do I have access to?
        See script.txt in the project root for a scenario
        """
        response = await self.orchestrator.route_request(question, "shankinson", "session001")
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
        """Register all of the agents in this workflow with mutli-agent-orchestrator"""
        # Pulling in some of the schema / future state context from TaskStream
        future_implementation_notes = """
        # Project Definition
        This project aims to deliver a user-centric frontend application that allows for quick and accurate calculations of deferred interest, helping users understand potential charges and manage their finances effectively.

        #Project Vision
        Develop an intuitive, responsive single-page application using React and TypeScript that empowers users to accurately calculate deferred interest and explore various financial scenarios, enhancing financial transparency and user decision-making.

        # Non-Functional Requirements

        ## Peformance
        - Calculations must be nearly immediate and logic must execute locally.
        - The platform must enable realtime calculations with no external integrations.

        ## Maintainability
        - The solution should be designed to be portable and self-contained in a single page.
        - Industry-standard coding practices should be followed.
        - Comprehensive documentation should be provided within source code for all requirements

        # Technology Stack
        - Framework: React
        - Language: TypeScript
        - State Management: React Hooks
        - Styling: MUI Material UI
        - Routing: Next.js App Router
        - Package Manager: npm
        - Form Management: MUI Material UI
        - HTTP Client: Next.js
        """

        # Claude likes to think about it -- give more time than the boto3 default 60s
        session = boto3.Session()
        config = Config(read_timeout=300)
        longer_client = session.client("bedrock-runtime", config=config)

        cobol_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="Cobol Developer Agent",
                streaming=False,
                description="Specializes in maintaining and interpreting legacy COBOL code, ensuring that business logic and \
                functionality are preserved for modernization projects.  Capable of extracting business logic and technical \
                specifications from COBOL Code, analyzing COBOL code structure, incorporating documentation, describing \
                legacy user interfaces in detail, and generating Markdown documentation.",
                model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                inference_config={"maxTokens": 8192, "temperature": 0.0},
                tool_config={
                    "tool": filesystem_tool.filesystem_tools_description,
                    "toolMaxRecursion": 5,
                    "useToolHandler": filesystem_tool.file_tools_handler,
                },
                callbacks=BedrockLLMAgentCallbacks(),
                client=longer_client,
            ),
        )
        cobol_agent.set_system_prompt(
            filesystem_tool.filesystem_tools_prompt,
            {
                "ROLE": "COBOL Developer",
                "ROLE_INPUT_FOLDER": "./work/01_COBOL_DEVELOPER",
                "ROLE_OUTPUT_FOLDER": "./work/02_SOLUTION_ARCHITECT",
            },
        )
        self.orchestrator.add_agent(cobol_agent)

        solution_architect_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="Solution Architect Agent",
                streaming=False,
                description=f"Responsible for describing system architecture, ensuring business goals are satisfied with technical \
                requirements.  Skilled with system definition, technical specifications, solution approach, and code examples.\
                    Skilled at translating legacy requirements into modern architecture.  Any solution should be designed with \
                    the following additional details in mind:\n\n {future_implementation_notes}",
                model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                inference_config={"maxTokens": 8192, "temperature": 0.0},
                tool_config={
                    "tool": filesystem_tool.filesystem_tools_description,
                    "toolMaxRecursion": 5,
                    "useToolHandler": filesystem_tool.file_tools_handler,
                },
                callbacks=BedrockLLMAgentCallbacks(),
                client=longer_client,
            ),
        )
        solution_architect_agent.set_system_prompt(
            filesystem_tool.filesystem_tools_prompt,
            {
                "ROLE": "Solution Architect",
                "ROLE_INPUT_FOLDER": "./work/02_SOLUTION_ARCHITECT",
                "ROLE_OUTPUT_FOLDER": "./work/03_FRONTEND_ENGINEER",
            },
        )
        self.orchestrator.add_agent(solution_architect_agent)

        frontend_agent = BedrockLLMAgent(
            BedrockLLMAgentOptions(
                name="Frontend Developer",
                streaming=False,
                description=f"Responsible for the client-side development, interfaces, and user interaction aspects of the application. \
                    Skilled at implementing UI using standard HTML/CSS/JavaScript.  Any solution should be implemented with \
                    the following additional details in mind:\n\n {future_implementation_notes}",
                model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
                inference_config={"maxTokens": 8192, "temperature": 0.0},
                tool_config={
                    "tool": filesystem_tool.filesystem_tools_description,
                    "toolMaxRecursion": 5,
                    "useToolHandler": filesystem_tool.file_tools_handler,
                },
                callbacks=BedrockLLMAgentCallbacks(),
                client=longer_client,
            ),
        )
        frontend_agent.set_system_prompt(
            filesystem_tool.filesystem_tools_prompt,
            {
                "ROLE": "Frontend Developer",
                "ROLE_INPUT_FOLDER": "./work/03_FRONTEND_ENGINEER",
                "ROLE_OUTPUT_FOLDER": "./work/04_OUTPUT",
            },
        )
        self.orchestrator.add_agent(frontend_agent)


def clean_work_directory(work_dir="./work"):
    """Clean work directory while preserving:
    1. All files in the root of the work directory
    2. All folders in the root of the work directory
    But delete all nested content within any subdirectories.

    Args:
        work_dir (str): Path to work directory

    """
    try:
        # Ensure work directory exists
        if not os.path.exists(work_dir):
            print(f"Work directory {work_dir} does not exist")
            return

        # Track what's being deleted and preserved
        deleted_items = []
        preserved_root_items = []
        errors = []

        # Handle items in work directory root
        for item in os.listdir(work_dir):
            full_path = os.path.join(work_dir, item)

            # Preserve root items but clean subdirectories
            if os.path.isdir(full_path):
                preserved_root_items.append(full_path)

                # Delete all contents within the directory
                for sub_item in os.listdir(full_path):
                    sub_path = os.path.join(full_path, sub_item)
                    try:
                        if os.path.isfile(sub_path):
                            os.remove(sub_path)
                        else:
                            shutil.rmtree(sub_path)
                        deleted_items.append(sub_path)
                    except Exception as e:
                        errors.append(f"Error deleting {sub_path}: {e!s}")
            else:
                # Preserve files in root
                preserved_root_items.append(full_path)

        # Print summary
        print("\nWork Folder Cleanup Summary:")
        print("---------------")
        print(f"Items deleted: {len(deleted_items)}")
        for item in deleted_items:
            print(f"  - Deleted: {item}")

        print(f"\nRoot items preserved: {len(preserved_root_items)}")
        for item in preserved_root_items:
            print(f"  - Preserved: {item}")

        # Stage files for the R4 demo example
        print("\nRoot items staged: 3")
        print("  - Staged: Q_Explain.txt")
        shutil.copy("./work/Q_Explain.txt", "./work/01_COBOL_DEVELOPER/Q_Explain.txt")
        print("  - Staged: SourceCode.txt")
        shutil.copy("./work/SourceCode.txt", "./work/01_COBOL_DEVELOPER/SourceCode.txt")
        print("  - Staged: page.tsx")
        shutil.copy("./work/page.tsx", "./work/03_FRONTEND_ENGINEER/page.tsx")

        if errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")

    except Exception as e:
        print(f"An error occurred: {e!s}")


if __name__ == "__main__":
    clean_work_directory()

    client = UIClient()
    client.draw_ui()
