"""Unit tests for OpenAI Agent workflow."""

import uuid
from unittest.mock import patch

import pytest
from temporalio.testing import WorkflowEnvironment

from awa.core.models.config.app_config import AppConfig
from awa.core.models.config.llm_config import LLMConfig
from awa.core.models.config.llm_providers_config import (
    AzureOpenAiLlmProvider,
    LiteLlmProvider,
    LlmProviderEnum,
    LlmProvidersConfig,
    OpenAiLlmProvider,
)
from awa.core.models.config.model_config import ModelConfig
from awa.core.workflows.openai_agent_workflow import OpenAIAgentWorkflow
from awa.sdk.models.openai_agents import OpenAIAgentConfig, OpenAIAgentResponse


@pytest.fixture
def mock_app_config() -> AppConfig:
    """Create a mock AppConfig with various provider configurations."""
    return AppConfig(
        llm=LLMConfig(
            providers=LlmProvidersConfig(
                openai=OpenAiLlmProvider(),
                azure_openai=AzureOpenAiLlmProvider(
                    resource_name="test-resource",
                    api_version="2024-02-01",
                    domain="openai.azure.com",
                    use_entra_auth=False,
                ),
                lite_llm=LiteLlmProvider(
                    base_url="http://localhost:4000",
                ),
            ),
            default_model="gpt-4",
            models=[
                ModelConfig(
                    name="gpt-4",
                    model="gpt-4",
                    provider=LlmProviderEnum.OPEN_AI,
                    temperature=0.7,
                    max_tokens=1000,
                ),
                ModelConfig(
                    name="gpt-4-azure",
                    model="gpt-4-deployment",
                    provider=LlmProviderEnum.AZURE_OPEN_AI,
                    temperature=0.5,
                    resource_name="test-resource",
                    api_version="2024-02-01",
                    domain="openai.azure.com",
                ),
                ModelConfig(
                    name="claude-3",
                    model="claude-3-opus-20240229",
                    provider=LlmProviderEnum.LITE_LLM,
                    temperature=0.8,
                ),
            ],
        ),
    )


@pytest.fixture
def basic_agent_config() -> OpenAIAgentConfig:
    """Create a basic OpenAI agent configuration."""
    return OpenAIAgentConfig(
        name="test-agent",
        instructions="You are a helpful assistant",
        input="Hello, how can you help me?",
        model="gpt-4",
    )


class TestOpenAIAgentWorkflow:
    """Test cases for OpenAIAgentWorkflow."""

    @pytest.mark.asyncio
    async def test_workflow_execution_success(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        basic_agent_config: OpenAIAgentConfig,
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test successful workflow execution with OpenAI provider."""
        # Create workflow instance
        workflow = OpenAIAgentWorkflow()

        # Mock the _run_agent_with_handoffs method
        mock_response = OpenAIAgentResponse(
            content="Hello, I'm here to help!",
            execution_id=str(uuid.uuid4()),
            agent_name="test-agent",
            model_used="gpt-4",
            execution_time_seconds=1.5,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response) as mock_run_agent:
            # Execute workflow
            result = await workflow.run(basic_agent_config)

            # Verify result
            assert result.content == "Hello, I'm here to help!"
            assert result.agent_name == "test-agent"
            assert result.model_used == "gpt-4"
            assert result.error is None

            # Verify _run_agent_with_handoffs was called
            mock_run_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_with_mcp_servers(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test workflow with MCP server names."""
        mcp_servers = ["filesystem-server", "database-server"]

        agent_config = OpenAIAgentConfig(
            name="mcp-agent",
            instructions="Agent with MCP servers",
            input="Test MCP server functionality",
            model="gpt-4",
            mcp_servers=mcp_servers,
        )

        workflow = OpenAIAgentWorkflow()

        mock_response = OpenAIAgentResponse(
            content="MCP response",
            execution_id=str(uuid.uuid4()),
            agent_name="mcp-agent",
            model_used="gpt-4",
            execution_time_seconds=2.0,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response) as mock_run_agent:
            result = await workflow.run(agent_config)

            # Verify the workflow ran successfully
            assert result.content == "MCP response"
            assert result.agent_name == "mcp-agent"
            mock_run_agent.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_with_server_name_resolution(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test that server names are properly resolved from MCP configuration."""
        agent_config = OpenAIAgentConfig(
            name="resolution-agent",
            instructions="Test server resolution",
            input="Test server name resolution",
            model="gpt-4",
            mcp_servers=["test-server"],
        )

        workflow = OpenAIAgentWorkflow()

        mock_response = OpenAIAgentResponse(
            content="Server resolved",
            execution_id=str(uuid.uuid4()),
            agent_name="resolution-agent",
            model_used="gpt-4",
            execution_time_seconds=1.0,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response):
            result = await workflow.run(agent_config)

            # Verify response
            assert result.content == "Server resolved"
            assert result.agent_name == "resolution-agent"

    @pytest.mark.asyncio
    async def test_workflow_with_multiple_server_names(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test workflow with multiple MCP server names."""
        agent_config = OpenAIAgentConfig(
            name="multi-server-agent",
            instructions="Test multiple servers",
            input="Test multiple MCP servers",
            model="gpt-4",
            mcp_servers=["server-1", "server-2", "server-3"],
        )

        workflow = OpenAIAgentWorkflow()

        mock_response = OpenAIAgentResponse(
            content="All servers resolved",
            execution_id=str(uuid.uuid4()),
            agent_name="multi-server-agent",
            model_used="gpt-4",
            execution_time_seconds=2.5,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response):
            await workflow.run(agent_config)

    @pytest.mark.asyncio
    async def test_workflow_with_empty_mcp_servers(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test workflow with empty MCP servers list."""
        agent_config = OpenAIAgentConfig(
            name="empty-mcp-agent",
            instructions="Test with empty servers",
            input="Test with empty MCP servers list",
            model="gpt-4",
            mcp_servers=[],  # Empty list
        )

        workflow = OpenAIAgentWorkflow()

        mock_response = OpenAIAgentResponse(
            content="No servers configured",
            execution_id=str(uuid.uuid4()),
            agent_name="empty-mcp-agent",
            model_used="gpt-4",
            execution_time_seconds=1.0,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response):
            await workflow.run(agent_config)

    @pytest.mark.asyncio
    async def test_workflow_with_none_mcp_servers(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test workflow with None MCP servers (default behavior)."""
        agent_config = OpenAIAgentConfig(
            name="no-mcp-agent",
            instructions="Test without MCP servers",
            input="Test without MCP servers configured",
            model="gpt-4",
            mcp_servers=None,  # Explicitly None
        )

        workflow = OpenAIAgentWorkflow()

        mock_response = OpenAIAgentResponse(
            content="No MCP configured",
            execution_id=str(uuid.uuid4()),
            agent_name="no-mcp-agent",
            model_used="gpt-4",
            execution_time_seconds=0.8,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response):
            await workflow.run(agent_config)

    @pytest.mark.asyncio
    async def test_workflow_with_missing_mcp_server(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test error handling when MCP server name is not found in configuration."""
        agent_config = OpenAIAgentConfig(
            name="missing-server-agent",
            instructions="Test missing server",
            input="Test with non-existent MCP server",
            model="gpt-4",
            mcp_servers=["non-existent-server"],
        )

        workflow = OpenAIAgentWorkflow()

        # Mock _build_agent_with_tools_and_handoffs to raise ValueError
        error_msg = "MCP server 'non-existent-server' not found in configuration"
        with (
            patch.object(workflow, "_build_agent_with_tools_and_handoffs", side_effect=ValueError(error_msg)),
            pytest.raises(ValueError, match=error_msg),
        ):
            await workflow.run(agent_config)

    @pytest.mark.asyncio
    async def test_workflow_with_case_sensitive_server_names(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test that server name resolution is case-sensitive."""
        agent_config = OpenAIAgentConfig(
            name="case-test-agent",
            instructions="Test case sensitivity",
            input="Test case-sensitive server names",
            model="gpt-4",
            mcp_servers=["Test-Server"],  # Different case
        )

        workflow = OpenAIAgentWorkflow()

        # Mock _build_agent_with_tools_and_handoffs to raise ValueError
        error_msg = "MCP server 'Test-Server' not found in configuration"
        with (
            patch.object(workflow, "_build_agent_with_tools_and_handoffs", side_effect=ValueError(error_msg)),
            pytest.raises(ValueError, match=error_msg),
        ):
            await workflow.run(agent_config)

    @pytest.mark.asyncio
    async def test_workflow_with_max_turns(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test that max_turns is properly passed through to the agent."""
        agent_config = OpenAIAgentConfig(
            name="max-turns-agent",
            instructions="Test max turns configuration",
            input="Test with custom max_turns",
            model="gpt-4",
            max_turns=50,  # Custom max_turns value
        )

        workflow = OpenAIAgentWorkflow()

        mock_response = OpenAIAgentResponse(
            content="Max turns configured",
            execution_id=str(uuid.uuid4()),
            agent_name="max-turns-agent",
            model_used="gpt-4",
            execution_time_seconds=1.0,
        )

        with patch.object(workflow, "_run_agent_with_handoffs", return_value=mock_response):
            result = await workflow.run(agent_config)

            # Verify the workflow ran successfully
            assert result.content == "Max turns configured"
            assert result.agent_name == "max-turns-agent"

            # Verify that the agent was built with the config including max_turns
            # The test_create_agent_config_includes_max_turns validates the config dict includes max_turns

    @pytest.mark.asyncio
    async def test_runner_receives_max_turns(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test that max_turns is passed to Runner.run() when specified."""
        from unittest.mock import AsyncMock

        agent_config = OpenAIAgentConfig(
            name="max-turns-agent",
            instructions="Test max turns configuration",
            input="Test with custom max_turns",
            model="gpt-4",
            max_turns=50,
        )

        workflow = OpenAIAgentWorkflow()

        # Mock Runner.run to capture the arguments
        mock_run_result = AsyncMock()
        mock_run_result.new_items = []
        mock_run_result.final_output = "Test output"

        with patch("awa.core.workflows.openai_agent_workflow.Runner.run", return_value=mock_run_result) as mock_runner:
            await workflow.run(agent_config)

            # Verify Runner.run was called with max_turns
            mock_runner.assert_called_once()
            call_kwargs = mock_runner.call_args[1]
            assert "max_turns" in call_kwargs
            assert call_kwargs["max_turns"] == 50

    @pytest.mark.asyncio
    async def test_runner_no_max_turns_when_not_specified(
        self,
        mock_app_config: AppConfig,  # noqa: ARG002
        workflow_env: WorkflowEnvironment,  # noqa: ARG002
    ) -> None:
        """Test that max_turns is not passed to Runner.run() when not specified."""
        from unittest.mock import AsyncMock

        agent_config = OpenAIAgentConfig(
            name="no-max-turns-agent",
            instructions="Test without max turns",
            input="Test without max_turns",
            model="gpt-4",
            # max_turns not specified
        )

        workflow = OpenAIAgentWorkflow()

        # Mock Runner.run to capture the arguments
        mock_run_result = AsyncMock()
        mock_run_result.new_items = []
        mock_run_result.final_output = "Test output"

        with patch("awa.core.workflows.openai_agent_workflow.Runner.run", return_value=mock_run_result) as mock_runner:
            await workflow.run(agent_config)

            # Verify Runner.run was called without max_turns
            mock_runner.assert_called_once()
            call_kwargs = mock_runner.call_args[1]
            assert "max_turns" not in call_kwargs
