"""Example workflow using PydanticAI agent (or Default Agent) mode implementation.

This workflow demonstrates the agent mode approach using AgentConfiguration
and the execute_agent_workflow pattern.
"""

from pathlib import Path

from temporalio import workflow

from cookbook.recipes.constants import AWA_WORKFLOW_AGENT_MODE_PYDANTIC_AI
from cookbook.recipes.decorators.recipe_exposed import recipe_exposed
from sdk_dist.python.awa.client import awa_activity, awa_workflow
from sdk_dist.python.awa.client.models.agent_modes.agent_configuration import AgentConfiguration, McpServer
from sdk_dist.python.awa.client.models.agent_modes.agent_mode_enum import AgentModeEnum
from sdk_dist.python.awa.client.models.agent_modes.agent_provider_enum import AgentProviderEnum


@recipe_exposed("PydanticAI agent mode with MCP integration")
@workflow.defn(name=AWA_WORKFLOW_AGENT_MODE_PYDANTIC_AI)
class AgentModePydanticAIWorkflow:
    """PydanticAI agent mode workflow implementation.

    This workflow shows how to use the agent mode pattern with PydanticAI agents,
    including MCP integration. This approach follows AWA's standard
    agent execution patterns.
    """

    @workflow.run
    async def run(self, prompt: str | None = None) -> dict:
        """Execute a PydanticAI agent with MCP integration.

        Args:
            prompt: Optional prompt. If not provided, uses a default example.

        Returns:
            Dictionary containing the task result

        """
        # Use a default prompt if none provided
        actual_prompt = prompt or (
            "# AGENT IDENTITY\n\n"
            "You are an autonomous desktop automation agent. You execute tasks by using Desktop Commander MCP tools "
            "to perform real file operations, process execution, and system management.\n\n"
            "## Core Rules\n\n"
            "1. **Execute, Don't Describe**: Use your tools to perform actual operations, "
            "not just describe them\n"
            "2. **Track Progress Forward**: Check existing `task_checklist.md` - if items are checked "
            "(✅), skip them and work on unchecked items only\n"
            "3. **Handle Errors Gracefully**: If a tool fails, try alternatives (max 3 attempts), "
            "then move to the next task\n"
            "4. **Verify Your Work**: After creating/modifying files, read them back to confirm success\n\n"
            "## Working Directory\n\n"
            "/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator\n\n"
            "## Progress Tracking\n\n"
            "- **First action**: Check if `task_checklist.md` exists and read it\n"
            "- **If it doesn't exist**: Create it with all tasks below as `- [ ] Task description`\n"
            "- **If it exists**: Read it to see what's done (✅) and what needs work ([ ])\n"
            "- **After completing each task**: Use rewrite tool to change `[ ]` to `[✅]` for that task only\n"
            "- **NEVER uncheck completed items** - only work on unchecked tasks\n\n"
            "## Tasks to Execute\n\n"
            "1. Initialize progress tracking (create task_checklist.md if needed)\n"
            "2. Create project structure:\n"
            "   - Create `math_calculator/` directory\n"
            "   - Create `math_calculator/src`, `math_calculator/tests`, `math_calculator/results` subdirectories\n"
            "   - Verify directories exist\n"
            "3. Write Python implementation:\n"
            "   - Create `math_calculator/src/big_math.py` with:\n"
            "     - `add_big_numbers(a: int, b: int) -> int`\n"
            "     - `multiply_big_numbers(a: int, b: int) -> int`\n"
            "     - `factorial_big_number(n: int) -> int`\n"
            "     - Include type hints and docstrings\n"
            "   - Read file back to verify\n"
            "4. Create test suite:\n"
            "   - Write `math_calculator/tests/test_big_math.py` with:\n"
            "     - Tests for numbers > 10^20\n"
            "     - Performance/timing tests\n"
            "   - Read file back to verify\n"
            "5. Execute and validate:\n"
            "   - Run: `python math_calculator/tests/test_big_math.py`\n"
            "   - Save output to `math_calculator/results/test_output.txt`\n"
            "6. Create documentation:\n"
            "   - Write `math_calculator/README.md` with project description\n"
            "   - Write `math_calculator/OPERATIONS_SUMMARY.md` documenting MCP tools used\n\n"
            "## Success Criteria\n\n"
            "Complete when all tasks in `task_checklist.md` are marked with ✅ and all files exist with proper content."
        )

        workflow.logger.info(f"Starting agent mode PydanticAI with prompt: {actual_prompt[:100]}...")

        # Try to read MCP configuration file
        mcp_config = None
        try:
            # Look for mcp.json in the cookbook pydantic_ai workflow input directory
            mcp_config_path = str(Path(__file__).parent / "input" / "mcp.json")
            mcp_config_str = await awa_activity.read_file(mcp_config_path)
            workflow.logger.info(f"Found mcp.json file at {mcp_config_path}, configuring MCP servers")
            mcp_config = McpServer(mcp_json=mcp_config_str)
        except (OSError, ValueError, RuntimeError) as e:
            workflow.logger.warning(f"Failed to read mcp.json file: {e}, proceeding without MCP")

        workflow.logger.info(f"MCP configuration: {mcp_config}")

        # Configure the agent using agent configuration
        config = AgentConfiguration(
            mode=AgentModeEnum.ANALYZE,
            provider=AgentProviderEnum.PYDANTIC_AI,
            prompt=actual_prompt,
            timeout_seconds=90,
            initialize=True,
            working_directory="/Users/robert.forshier/Projects/AWA/agentic-workflow-accelerator-cookbook",
            mcp=mcp_config,
        )

        # Execute the agent workflow using AWA SDK
        workflow.logger.info("Executing PydanticAI agent...")

        result = await awa_workflow.execute_agent(config)

        workflow.logger.info("Agent execution completed")
        return result
