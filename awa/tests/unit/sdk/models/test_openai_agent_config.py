"""Unit tests for OpenAI Agent configuration models."""

import json
from typing import Any
from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from awa.sdk.models.openai_agents import AgentToolConfig, OpenAIAgentConfig, OpenAIAgentResponse, ResponseFormat


class TestOpenAIAgentConfig:
    """Test cases for OpenAIAgentConfig model."""

    def test_minimal_config(self) -> None:
        """Test creating config with only required fields."""
        config = OpenAIAgentConfig(
            name="test-agent",
            instructions="You are a helpful assistant",
            input="Test input",
            model="gpt-4",
        )

        assert config.name == "test-agent"
        assert config.instructions == "You are a helpful assistant"
        assert config.model == "gpt-4"
        assert config.response_format == ResponseFormat.TEXT  # default
        assert config.response_schema is None
        assert config.mcp_servers is None
        assert config.workflow_id is None
        assert config.metadata is None

    def test_full_config(self) -> None:
        """Test creating config with all optional fields."""
        mcp_servers = ["server1", "server2"]
        metadata = {"user_id": "123", "session_id": "abc"}

        config = OpenAIAgentConfig(
            name="advanced-agent",
            instructions="Complex instructions",
            input="Advanced input",
            model="gpt-4-turbo",
            mcp_servers=mcp_servers,
            response_format=ResponseFormat.TEXT,
            workflow_id="workflow-123",
            metadata=metadata,
        )

        assert config.name == "advanced-agent"
        assert len(config.mcp_servers) == 2
        assert config.mcp_servers == ["server1", "server2"]
        assert config.workflow_id == "workflow-123"
        assert config.metadata == metadata

    def test_json_schema_response_format(self) -> None:
        """Test JSON schema response format configuration."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name"],
        }

        config = OpenAIAgentConfig(
            name="json-agent",
            instructions="Return structured data",
            input="JSON input",
            model="gpt-4",
            response_format=ResponseFormat.JSON_SCHEMA,
            response_schema=schema,
        )

        assert config.response_format == ResponseFormat.JSON_SCHEMA
        assert config.response_schema == schema

    def test_response_schema_validator_with_text_format(self) -> None:
        """Test that response_schema raises error when response_format is not JSON_SCHEMA."""
        schema = {"type": "object"}

        with pytest.raises(ValidationError) as exc_info:
            OpenAIAgentConfig(
                name="invalid-agent",
                instructions="Test",
                input="Test input",
                model="gpt-4",
                response_format=ResponseFormat.TEXT,
                response_schema=schema,
            )

        error = exc_info.value.errors()[0]
        assert "response_schema can only be set when response_format is JSON_SCHEMA" in str(error)

    def test_serialization_deserialization(self) -> None:
        """Test model serialization and deserialization."""
        original = OpenAIAgentConfig(
            name="serialize-test",
            instructions="Test serialization",
            input="Test input",
            model="gpt-4",
            metadata={"key": "value"},
        )

        # Serialize to dict
        data = original.model_dump()
        assert data["name"] == "serialize-test"

        # Deserialize from dict
        restored = OpenAIAgentConfig(**data)
        assert restored.name == original.name
        assert restored.metadata == original.metadata

    def test_json_serialization(self) -> None:
        """Test JSON serialization round-trip."""
        config = OpenAIAgentConfig(
            name="json-test",
            instructions="JSON test",
            input="Test input",
            model="gpt-4",
        )

        # Serialize to JSON
        json_str = config.model_dump_json()
        data = json.loads(json_str)
        assert data["name"] == "json-test"

        # Deserialize from JSON
        restored = OpenAIAgentConfig.model_validate_json(json_str)
        assert restored.name == config.name


class TestOpenAIAgentResponse:
    """Test cases for OpenAIAgentResponse model."""

    def test_successful_response(self) -> None:
        """Test creating a successful response."""
        response = OpenAIAgentResponse(
            content="Hello, world!",
            execution_id="exec-123",
            agent_name="test-agent",
            model_used="gpt-4",
            execution_time_seconds=1.5,
            metadata={"session": "test"},
        )

        assert response.content == "Hello, world!"
        assert response.execution_id == "exec-123"
        assert response.execution_time_seconds == 1.5
        assert response.error is None
        assert response.error_type is None

    def test_error_response(self) -> None:
        """Test creating an error response."""
        response = OpenAIAgentResponse(
            content="",  # Empty content on error
            execution_id="exec-456",
            agent_name="failed-agent",
            model_used="gpt-4",
            execution_time_seconds=0.5,
            error="Connection timeout",
            error_type="TimeoutError",
        )

        assert response.content == ""
        assert response.error == "Connection timeout"
        assert response.error_type == "TimeoutError"

    def test_minimal_response(self) -> None:
        """Test creating response with only required fields."""
        response = OpenAIAgentResponse(
            content="Minimal response",
            execution_id="exec-789",
            agent_name="minimal",
            model_used="gpt-3.5",
            execution_time_seconds=0.8,
        )

        assert response.content == "Minimal response"
        assert response.error is None
        assert response.metadata is None

    def test_response_serialization(self) -> None:
        """Test response model serialization."""
        response = OpenAIAgentResponse(
            content="Test content",
            execution_id="test-id",
            agent_name="test",
            model_used="gpt-4",
            execution_time_seconds=2.0,
        )

        # Serialize to dict
        data = response.model_dump()
        assert data["content"] == "Test content"

        # Deserialize from dict
        restored = OpenAIAgentResponse(**data)
        assert restored.content == response.content


class TestMCPServerConfiguration:
    """Test cases for MCP server configuration in OpenAI agent."""

    def test_mcp_servers_string_list(self) -> None:
        """Test OpenAIAgentConfig with string list of MCP server names."""
        mcp_servers = ["server1", "server2", "server3"]

        config = OpenAIAgentConfig(
            name="multi-mcp",
            instructions="Test multiple MCP servers",
            input="MCP input",
            model="gpt-4",
            mcp_servers=mcp_servers,
        )

        assert len(config.mcp_servers) == 3
        assert config.mcp_servers == ["server1", "server2", "server3"]
        assert all(isinstance(server, str) for server in config.mcp_servers)

    def test_empty_mcp_servers_list(self) -> None:
        """Test OpenAIAgentConfig with empty MCP servers list."""
        config = OpenAIAgentConfig(
            name="empty-mcp",
            instructions="Test empty MCP servers",
            input="Empty MCP input",
            model="gpt-4",
            mcp_servers=[],
        )

        assert config.mcp_servers == []

    def test_single_mcp_server(self) -> None:
        """Test OpenAIAgentConfig with single MCP server."""
        config = OpenAIAgentConfig(
            name="single-mcp",
            instructions="Test single MCP server",
            input="Single MCP input",
            model="gpt-4",
            mcp_servers=["my-server"],
        )

        assert len(config.mcp_servers) == 1
        assert config.mcp_servers[0] == "my-server"

    def test_mcp_servers_serialization(self) -> None:
        """Test serialization of MCP servers as string list."""
        config = OpenAIAgentConfig(
            name="serialize-mcp",
            instructions="Test MCP servers serialization",
            input="Serialize MCP input",
            model="gpt-4",
            mcp_servers=["server1", "server2"],
        )

        # Serialize to dict
        data = config.model_dump()
        assert data["mcp_servers"] == ["server1", "server2"]
        assert isinstance(data["mcp_servers"], list)
        assert all(isinstance(server, str) for server in data["mcp_servers"])

        # Deserialize from dict
        restored = OpenAIAgentConfig(**data)
        assert restored.mcp_servers == config.mcp_servers


class TestDefaultValues:
    """Test default values and optional fields."""

    def test_config_defaults(self) -> None:
        """Test all default values in OpenAIAgentConfig."""
        config = OpenAIAgentConfig(
            name="defaults-test",
            instructions="Test defaults",
            input="Test defaults input",
            model="gpt-4",
        )

        # Check all defaults
        assert config.mcp_servers is None
        assert config.response_format == ResponseFormat.TEXT
        assert config.response_schema is None
        assert config.workflow_id is None
        assert config.metadata is None

    def test_response_defaults(self) -> None:
        """Test optional fields in OpenAIAgentResponse."""
        response = OpenAIAgentResponse(
            content="Test",
            execution_id="id",
            agent_name="agent",
            model_used="model",
            execution_time_seconds=1.0,
        )

        # Check all optional fields are None
        assert response.error is None
        assert response.error_type is None
        assert response.metadata is None


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_strings(self) -> None:
        """Test that empty strings are rejected for required fields."""
        with pytest.raises(ValidationError):
            OpenAIAgentConfig(
                name="",  # Empty name should fail
                instructions="test",
                input="Empty test input",
                model="gpt-4",
            )

    def test_null_required_fields(self) -> None:
        """Test that None is rejected for required fields."""
        with pytest.raises(ValidationError):
            OpenAIAgentConfig(
                name=None,  # type: ignore[arg-type]
                instructions="test",
                input="Null test input",
                model="gpt-4",
            )

    def test_complex_metadata(self) -> None:
        """Test complex nested metadata."""
        metadata: dict[str, Any] = {
            "user": {
                "id": "123",
                "preferences": {"theme": "dark", "language": "en"},
            },
            "context": {
                "source": "api",
                "version": "1.2.3",
                "tags": ["important", "urgent"],
            },
        }

        config = OpenAIAgentConfig(
            name="complex",
            instructions="test",
            input="Complex input",
            model="gpt-4",
            metadata=metadata,
        )

        assert config.metadata["user"]["preferences"]["theme"] == "dark"
        assert "urgent" in config.metadata["context"]["tags"]

    def test_mcp_servers_validation(self) -> None:
        """Test validation that MCP servers must be strings."""
        # Valid string list should work
        config = OpenAIAgentConfig(
            name="valid-mcp",
            instructions="test",
            input="Valid MCP input",
            model="gpt-4",
            mcp_servers=["server1", "server2"],
        )
        assert config.mcp_servers == ["server1", "server2"]

        # Test with non-string items should fail during validation
        with pytest.raises(ValidationError):
            OpenAIAgentConfig(
                name="invalid-mcp",
                instructions="test",
                input="Invalid MCP input",
                model="gpt-4",
                mcp_servers=[123, "server2"],  # type: ignore[list-item]
            )

        with pytest.raises(ValidationError):
            OpenAIAgentConfig(
                name="invalid-mcp-2",
                instructions="test",
                input="Invalid MCP input 2",
                model="gpt-4",
                mcp_servers=[{"server": "config"}],  # type: ignore[list-item]
            )

    def test_large_response_schema(self) -> None:
        """Test handling of large/complex JSON schemas."""
        schema = {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "attributes": {
                                "type": "object",
                                "additionalProperties": {"type": "string"},
                            },
                        },
                    },
                },
                "metadata": {"type": "object"},
            },
        }

        config = OpenAIAgentConfig(
            name="schema-test",
            instructions="test",
            input="Schema test input",
            model="gpt-4",
            response_format=ResponseFormat.JSON_SCHEMA,
            response_schema=schema,
        )

        assert config.response_schema == schema


class TestAgentToolConfig:
    """Test cases for AgentToolConfig model."""

    def test_create_with_openai_agent_config_minimal(self) -> None:
        """Test creating AgentToolConfig with minimal OpenAIAgentConfig as target_agent."""
        target_agent = OpenAIAgentConfig(
            name="test-agent",
            instructions="You are a helpful assistant",
            input="Test input",
            model="gpt-4",
        )

        config = AgentToolConfig(target_agent=target_agent)

        assert config.target_agent == target_agent
        assert config.tool_name_override is None
        assert config.tool_description_override is None
        assert config.is_enabled is True  # default value

    def test_create_with_all_fields(self) -> None:
        """Test creating AgentToolConfig with all fields specified."""
        target_agent = OpenAIAgentConfig(
            name="data-analyzer",
            instructions="Analyze data and provide insights",
            input="Please analyze this data",
            model="gpt-4-turbo",
        )

        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="custom_analyzer",
            tool_description_override="Custom data analysis tool with advanced capabilities",
            is_enabled=False,
        )

        assert config.target_agent == target_agent
        assert config.tool_name_override == "custom_analyzer"
        assert config.tool_description_override == "Custom data analysis tool with advanced capabilities"
        assert config.is_enabled is False

    def test_is_enabled_default_value(self) -> None:
        """Test that is_enabled defaults to True."""
        target_agent = OpenAIAgentConfig(
            name="test-agent",
            instructions="Test instructions",
            input="Test input",
            model="gpt-4",
        )

        config = AgentToolConfig(target_agent=target_agent)

        assert config.is_enabled is True

    def test_tool_overrides_can_be_none(self) -> None:
        """Test that tool_name_override and tool_description_override can be None."""
        target_agent = OpenAIAgentConfig(
            name="test-agent",
            instructions="Test instructions",
            input="Test input",
            model="gpt-4",
        )

        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override=None,
            tool_description_override=None,
        )

        assert config.tool_name_override is None
        assert config.tool_description_override is None

    def test_missing_required_field_target_agent(self) -> None:
        """Test that ValidationError is raised when target_agent is missing."""
        with pytest.raises(ValidationError) as exc_info:
            AgentToolConfig()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert "target_agent" in str(errors[0])

    def test_serialization_to_dict(self) -> None:
        """Test serialization of AgentToolConfig to dict."""
        target_agent = OpenAIAgentConfig(
            name="serialize-test",
            instructions="Test serialization",
            input="Test input",
            model="gpt-4",
        )

        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="custom_tool",
            tool_description_override="Custom description",
            is_enabled=False,
        )

        data = config.model_dump()

        assert isinstance(data, dict)
        assert "target_agent" in data
        assert data["tool_name_override"] == "custom_tool"
        assert data["tool_description_override"] == "Custom description"
        assert data["is_enabled"] is False

        # Verify target_agent is serialized as a dict
        assert isinstance(data["target_agent"], dict)
        assert data["target_agent"]["name"] == "serialize-test"

    def test_serialization_to_json(self) -> None:
        """Test JSON serialization of AgentToolConfig."""
        target_agent = OpenAIAgentConfig(
            name="json-test",
            instructions="JSON test",
            input="Test input",
            model="gpt-4",
        )

        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="json_tool",
            is_enabled=True,
        )

        json_str = config.model_dump_json()
        data = json.loads(json_str)

        assert isinstance(data, dict)
        assert data["tool_name_override"] == "json_tool"
        assert data["is_enabled"] is True
        assert data["target_agent"]["name"] == "json-test"

    def test_deserialization_from_dict(self) -> None:
        """Test deserialization of AgentToolConfig from dict."""
        # First create and serialize a config
        original_target = OpenAIAgentConfig(
            name="deserialize-test",
            instructions="Test deserialization",
            input="Test input",
            model="gpt-4",
        )

        original_config = AgentToolConfig(
            target_agent=original_target,
            tool_name_override="deserialize_tool",
            tool_description_override="Deserialize description",
            is_enabled=False,
        )

        data = original_config.model_dump()

        # Now deserialize from the dict
        restored_config = AgentToolConfig(**data)

        assert restored_config.tool_name_override == "deserialize_tool"
        assert restored_config.tool_description_override == "Deserialize description"
        assert restored_config.is_enabled is False
        assert isinstance(restored_config.target_agent, OpenAIAgentConfig)
        assert restored_config.target_agent.name == "deserialize-test"

    def test_deserialization_from_json(self) -> None:
        """Test deserialization of AgentToolConfig from JSON."""
        target_agent = OpenAIAgentConfig(
            name="json-deserialize",
            instructions="JSON deserialize test",
            input="Test input",
            model="gpt-4-turbo",
        )

        original_config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="json_deserialize_tool",
        )

        json_str = original_config.model_dump_json()

        # Deserialize from JSON
        restored_config = AgentToolConfig.model_validate_json(json_str)

        assert restored_config.tool_name_override == "json_deserialize_tool"
        assert restored_config.tool_description_override is None
        assert restored_config.is_enabled is True  # default value
        # Note: JSON deserialization returns OpenAIAgentConfig instance due to model_rebuild()
        assert isinstance(restored_config.target_agent, OpenAIAgentConfig)
        assert restored_config.target_agent.name == "json-deserialize"

    def test_field_validation_string_types(self) -> None:
        """Test validation of string fields."""
        target_agent = OpenAIAgentConfig(
            name="validation-test",
            instructions="Test validation",
            input="Test input",
            model="gpt-4",
        )

        # Test with valid string overrides
        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="valid_name",
            tool_description_override="Valid description",
        )

        assert config.tool_name_override == "valid_name"
        assert config.tool_description_override == "Valid description"

        # Test with empty strings (should be allowed)
        config_empty = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="",
            tool_description_override="",
        )

        assert config_empty.tool_name_override == ""
        assert config_empty.tool_description_override == ""

    def test_boolean_field_validation(self) -> None:
        """Test validation of boolean is_enabled field."""
        target_agent = OpenAIAgentConfig(
            name="bool-test",
            instructions="Boolean test",
            input="Test input",
            model="gpt-4",
        )

        # Test explicit True
        config_true = AgentToolConfig(target_agent=target_agent, is_enabled=True)
        assert config_true.is_enabled is True

        # Test explicit False
        config_false = AgentToolConfig(target_agent=target_agent, is_enabled=False)
        assert config_false.is_enabled is False

        # Test that Pydantic coerces string values to boolean (this is expected behavior)
        config_string = AgentToolConfig(target_agent=target_agent, is_enabled="true")  # type: ignore[arg-type]
        assert config_string.is_enabled is True

        config_string_false = AgentToolConfig(target_agent=target_agent, is_enabled="false")  # type: ignore[arg-type]
        assert config_string_false.is_enabled is False

        # Test that Pydantic coerces numeric values to boolean (this is expected behavior)
        config_numeric = AgentToolConfig(target_agent=target_agent, is_enabled=1)  # type: ignore[arg-type]
        assert config_numeric.is_enabled is True

        config_numeric_zero = AgentToolConfig(target_agent=target_agent, is_enabled=0)  # type: ignore[arg-type]
        assert config_numeric_zero.is_enabled is False

    def test_complex_agent_configuration(self) -> None:
        """Test AgentToolConfig with complex OpenAIAgentConfig."""
        target_agent = OpenAIAgentConfig(
            name="complex-agent",
            instructions="Complex agent with metadata",
            input="Complex input",
            model="gpt-4-turbo",
            mcp_servers=["server1", "server2"],
            response_format=ResponseFormat.JSON_SCHEMA,
            response_schema={"type": "object", "properties": {"result": {"type": "string"}}},
            workflow_id="workflow-123",
            metadata={"environment": "production", "version": "1.0.0"},
        )

        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override="complex_tool",
            tool_description_override="A complex tool with advanced configuration",
        )

        assert config.target_agent.name == "complex-agent"
        assert config.target_agent.mcp_servers == ["server1", "server2"]
        assert config.target_agent.response_format == ResponseFormat.JSON_SCHEMA
        assert config.target_agent.metadata["environment"] == "production"
        assert config.tool_name_override == "complex_tool"

    def test_model_config_allows_openai_agent_config_instances(self) -> None:
        """Test that the model correctly accepts OpenAIAgentConfig instances with arbitrary_types_allowed."""
        # Create a valid OpenAIAgentConfig instance
        valid_agent = OpenAIAgentConfig(
            name="valid-agent",
            instructions="Test instructions",
            input="Test input",
            model="gpt-4",
        )

        # This should work with arbitrary_types_allowed
        config = AgentToolConfig(target_agent=valid_agent)
        assert config.target_agent == valid_agent
        assert config.target_agent.name == "valid-agent"

        # Test that non-OpenAIAgentConfig objects fail validation
        mock_agent = Mock()
        mock_agent.name = "mock-agent"

        with pytest.raises(ValidationError) as exc_info:
            AgentToolConfig(target_agent=mock_agent)

        # Verify the error is about type validation
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "model_type"

    def test_edge_case_none_overrides_explicit(self) -> None:
        """Test explicitly setting overrides to None."""
        target_agent = OpenAIAgentConfig(
            name="none-test",
            instructions="None test",
            input="Test input",
            model="gpt-4",
        )

        config = AgentToolConfig(
            target_agent=target_agent,
            tool_name_override=None,
            tool_description_override=None,
            is_enabled=True,
        )

        assert config.tool_name_override is None
        assert config.tool_description_override is None
        assert config.is_enabled is True
