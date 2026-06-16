import pytest
from pydantic import BaseModel

from tests.workflow.utils.temporal_utils import execute_workflow
from tests.workflow.utils.workflow_utils import load_test_cases


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "workflow_name,input_data,custom_text_assertions",  # noqa: PT006
    load_test_cases(),
)
@pytest.mark.timeout(90)  # Applied to all test cases, will be overridden by individual timeout logic
async def test_workflow_execution(
    workflow_name: str,
    input_data: BaseModel,  # Pre-instantiated Pydantic model
    custom_text_assertions: list[str] | None,
) -> None:
    """Parametrized test for workflow execution with configurable assertions."""
    # Execute workflow - input_data is already a Pydantic instance
    result = await execute_workflow(workflow_name, input_data)

    # Basic assertion - result should not be None
    assert result is not None, "Workflow should return a result"

    # Custom text assertions if provided
    if custom_text_assertions:
        for assertion_text in custom_text_assertions:
            assert assertion_text in result, f"Result should contain '{assertion_text}'"


# Commented out - excluded from parametrization due to skip requirement
# @pytest.mark.asyncio
# @pytest.mark.skip(reason="Isolated agent workflow requires agent configuration and credentials")
# async def test_isolated_agent_workflow_analyze_mode() -> None:
#     """Test the isolated agent workflow in ANALYZE mode."""
#     input_data = IsolatedAgentParams(
#         source_directory="tests/workflow/test-data",
#         source_branch="main",
#         agent_config=AgentConfiguration(
#             mode=AgentModeEnum.ANALYZE,
#             provider=AgentProviderEnum.CLAUDE,
#             prompt="List the files in this directory and provide a brief summary",
#             timeout_seconds=300,
#         ),
#         agent_execution_timeout_minutes=5,
#         output_directory="analysis-output",
#     )
#
#     result = await execute_workflow("awa-isolated-agent", input_data)
#     assert result is not None, "Workflow should return a result"
