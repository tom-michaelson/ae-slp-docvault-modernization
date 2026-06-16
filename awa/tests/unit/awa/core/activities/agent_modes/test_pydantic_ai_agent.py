import json
from unittest.mock import AsyncMock, Mock, patch

import pytest

from awa.core.activities.agent_modes.pydantic_ai_agent import PydanticAIAgent
from awa.sdk.models.agent_modes.agent_configuration import McpTool


class TestPydanticAIAgent:
    """Test suite for PydanticAIAgent."""

    @pytest.mark.asyncio
    async def test_initialization(self) -> None:
        """Test PydanticAI agent initialization."""
        agent = PydanticAIAgent()

        result = await agent.initialize("test_agent", session_id="test_session")

        assert result.status is True
        assert "initialized successfully" in result.result
        assert result.session_id == "test_session"

    @pytest.mark.asyncio
    async def test_supports_mcp(self) -> None:
        """Test that PydanticAI agent supports MCP."""
        agent = PydanticAIAgent()
        assert agent.supports_mcp() is True

    @pytest.mark.asyncio
    async def test_execute_prompt_with_json_config(self) -> None:
        """Test executing a prompt with JSON configuration."""
        agent = PydanticAIAgent()

        # Mock the TemporalAgent and its run method
        mock_result = AsyncMock()
        mock_result.output = "Test response from PydanticAI"
        mock_result.usage = None  # Avoid serialization issues

        with (
            patch("awa.core.activities.agent_modes.pydantic_ai_agent.Agent") as mock_agent_class,
            patch("awa.core.activities.agent_modes.pydantic_ai_agent.TemporalAgent") as mock_temporal_class,
            patch(
                "awa.core.activities.agent_modes.pydantic_ai_agent.PydanticAIAgent._get_pydantic_ai_model_string",
            ) as mock_config,
        ):
            mock_config.return_value = "openai:gpt-4"  # Mock the config to return the expected model
            mock_temporal_instance = AsyncMock()
            mock_temporal_instance.run.return_value = mock_result
            mock_temporal_class.return_value = mock_temporal_instance

            # Create JSON configuration
            config = {
                "agent_name": "test_agent",
                "instructions": "You are a test assistant.",
                "model": {
                    "provider": "openai",
                    "model": "gpt-4",
                },
                "prompt": "What is 2+2?",
            }

            result = await agent.execute_prompt(
                json.dumps(config),
                session_id="test_session",
            )

            assert result.status is True
            assert result.session_id == "test_session"
            assert result.content == "Test response from PydanticAI"

            # Verify the agent was created with correct parameters
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args.kwargs
            assert call_kwargs["model"] == "openai:gpt-4"
            assert call_kwargs["instructions"] == "You are a test assistant."
            assert call_kwargs["name"] == "test_agent"

            # Verify the temporal agent run was called
            mock_temporal_instance.run.assert_called_once_with("What is 2+2?")

    @pytest.mark.asyncio
    async def test_execute_prompt_with_plain_text(self) -> None:
        """Test executing a plain text prompt with default configuration."""
        agent = PydanticAIAgent()

        mock_result = AsyncMock()
        mock_result.output = "Default response"
        mock_result.usage = None  # Avoid serialization issues

        with (
            patch("awa.core.activities.agent_modes.pydantic_ai_agent.Agent") as mock_agent_class,
            patch("awa.core.activities.agent_modes.pydantic_ai_agent.TemporalAgent") as mock_temporal_class,
            patch(
                "awa.core.activities.agent_modes.pydantic_ai_agent.PydanticAIAgent._get_pydantic_ai_model_string",
            ) as mock_config,
        ):
            mock_config.return_value = "openai:gpt-4"  # Mock the config to return the expected model
            mock_temporal_instance = AsyncMock()
            mock_temporal_instance.run.return_value = mock_result
            mock_temporal_class.return_value = mock_temporal_instance

            result = await agent.execute_prompt("Simple prompt", session_id="test_session")

            assert result.status is True
            assert result.content == "Default response"

            # Verify default configuration was used
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args.kwargs
            assert call_kwargs["model"] == "openai:gpt-4"
            assert call_kwargs["instructions"] == "You are a helpful assistant."
            assert call_kwargs["name"] == "default_agent"

    @pytest.mark.asyncio
    async def test_execute_prompt_with_different_providers(self) -> None:
        """Test executing prompts with different model providers."""
        agent = PydanticAIAgent()

        providers_tests = [
            ("anthropic", "claude-3-sonnet", "anthropic:claude-3-sonnet"),
            ("google", "gemini-pro", "google:gemini-pro"),
            ("azure-openai", "gpt-4", "azure-openai:gpt-4"),
            ("custom", "custom-model", "custom:custom-model"),
        ]

        for provider, model, expected_model_str in providers_tests:
            with (
                patch("awa.core.activities.agent_modes.pydantic_ai_agent.Agent") as mock_agent_class,
                patch("awa.core.activities.agent_modes.pydantic_ai_agent.TemporalAgent") as mock_temporal_class,
            ):
                # Set up the TemporalAgent mock
                mock_result = AsyncMock()
                mock_result.output = "Test response"
                mock_temporal_instance = AsyncMock()
                mock_temporal_instance.run.return_value = mock_result
                mock_temporal_class.return_value = mock_temporal_instance
                # The test expects the model string conversion to happen from the JSON config
                # So we don't need to mock _get_pydantic_ai_model_string here
                config = {
                    "agent_name": "test_agent",
                    "instructions": "Test instructions",
                    "model": {
                        "provider": provider,
                        "model": model,
                    },
                    "prompt": "Test prompt",
                }

                await agent.execute_prompt(json.dumps(config))

                mock_agent_class.assert_called_once()
                call_kwargs = mock_agent_class.call_args.kwargs
                assert call_kwargs["model"] == expected_model_str

    @pytest.mark.asyncio
    async def test_execute_prompt_error_handling(self) -> None:
        """Test error handling during prompt execution."""
        agent = PydanticAIAgent()

        with patch("awa.core.activities.agent_modes.pydantic_ai_agent.Agent") as mock_agent_class:
            mock_agent_class.side_effect = RuntimeError("Test error")

            result = await agent.execute_prompt("Test prompt", session_id="test_session")

            assert result.status is False
            assert result.session_id == "test_session"

            result_data = json.loads(result.result)
            assert "error" in result_data
            assert "Test error" in result_data["error"]
            assert result_data["error_type"] == "RuntimeError"

    @pytest.mark.asyncio
    async def test_configure_mcp(self) -> None:
        """Test MCP configuration."""
        agent = PydanticAIAgent()

        mcp_json = json.dumps(
            {
                "mcpServers": {
                    "test_server": {
                        "command": "test_command",
                    },
                },
            },
        )

        mcp_tools = [
            McpTool(server="test_server", tools=["tool1", "tool2"]),
        ]

        # Mock the MCP client and its tools
        with patch("awa.core.activities.agent_modes.pydantic_ai_agent.Client") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock the tools that would be returned
            mock_tool1 = Mock()
            mock_tool1.name = "tool1"
            mock_tool1.description = "Test tool 1"

            mock_tool2 = Mock()
            mock_tool2.name = "tool2"
            mock_tool2.description = "Test tool 2"

            mock_client.list_tools.return_value = [mock_tool1, mock_tool2]

            result = await agent.configure_mcp(".", mcp_json, mcp_tools)

            assert result is not None
            assert len(result) == 2
            assert "test_server__tool1" in result
            assert "test_server__tool2" in result

    @pytest.mark.asyncio
    async def test_execute_command_file(self) -> None:
        """Test executing a command file."""
        agent = PydanticAIAgent()

        # Mock Path.read_text() since we use pathlib now
        with patch("pathlib.Path.read_text") as mock_read_text:
            mock_read_text.return_value = "File content prompt"

            with patch.object(agent, "execute_prompt") as mock_execute_prompt:
                mock_execute_prompt.return_value = AsyncMock(status=True, result="Success")

                await agent.execute_command("test_file.txt", "/test/dir", session_id="test")

                mock_read_text.assert_called_once()
                mock_execute_prompt.assert_called_once_with(
                    "File content prompt",
                    "/test/dir",
                    None,
                    "test",
                )

    @pytest.mark.asyncio
    async def test_cleanup(self) -> None:
        """Test agent cleanup."""
        agent = PydanticAIAgent()
        # Should not raise any exceptions
        await agent.cleanup("test_session")

    @pytest.mark.asyncio
    async def test_get_log_files(self) -> None:
        """Test getting log files."""
        agent = PydanticAIAgent()
        # Should not raise any exceptions
        await agent.get_log_files("/test/dir", "test_session")
