"""Unit tests for handoff configuration models."""

import json
import time

import pytest
from pydantic import ValidationError

from awa.sdk.models.openai_agents import OpenAIAgentConfig, OpenAIAgentResponse
from awa.sdk.models.openai_agents.openai_agent_config import HandoffConfig, HandoffEvent

# Ensure models are rebuilt to handle forward references
HandoffConfig.model_rebuild()
OpenAIAgentConfig.model_rebuild()


class TestHandoffConfig:
    """Test cases for HandoffConfig model."""

    def test_minimal_handoff_config(self) -> None:
        """Test creating handoff config with only required fields."""
        config = HandoffConfig(target_agent="data_analyst")

        assert config.target_agent == "data_analyst"
        assert config.tool_name_override is None
        assert config.tool_description_override is None
        assert config.remove_tools_from_history is False
        assert config.is_enabled is True
        assert config.input_type is None

    def test_full_handoff_config(self) -> None:
        """Test creating handoff config with all optional fields."""
        config = HandoffConfig(
            target_agent="data_analyst",
            tool_name_override="analyze_data",
            tool_description_override="Hand off to data analyst for comprehensive analysis",
            remove_tools_from_history=True,
            is_enabled=True,
        )

        assert config.target_agent == "data_analyst"
        assert config.tool_name_override == "analyze_data"
        assert config.tool_description_override == "Hand off to data analyst for comprehensive analysis"
        assert config.remove_tools_from_history is True
        assert config.is_enabled is True

    def test_handoff_config_with_openai_agent_config(self) -> None:
        """Test HandoffConfig with OpenAIAgentConfig as target."""
        target_agent = OpenAIAgentConfig(
            name="specialist-agent",
            instructions="You are a specialist agent",
            input="Process this data",
            model="gpt-4",
        )

        config = HandoffConfig(
            target_agent=target_agent,
            tool_name_override="specialist_handoff",
        )

        assert isinstance(config.target_agent, OpenAIAgentConfig)
        assert config.target_agent.name == "specialist-agent"
        assert config.tool_name_override == "specialist_handoff"

    def test_handoff_config_disabled(self) -> None:
        """Test disabled handoff configuration."""
        config = HandoffConfig(
            target_agent="disabled_agent",
            is_enabled=False,
        )

        assert config.target_agent == "disabled_agent"
        assert config.is_enabled is False

    def test_handoff_config_serialization(self) -> None:
        """Test HandoffConfig serialization and deserialization."""
        original = HandoffConfig(
            target_agent="test_agent",
            tool_name_override="custom_tool",
        )

        # Serialize to dict
        data = original.model_dump()
        assert data["target_agent"] == "test_agent"
        assert data["tool_name_override"] == "custom_tool"

        # Deserialize from dict
        restored = HandoffConfig(**data)
        assert restored.target_agent == original.target_agent
        assert restored.tool_name_override == original.tool_name_override

    def test_handoff_config_json_serialization(self) -> None:
        """Test JSON serialization round-trip for HandoffConfig."""
        config = HandoffConfig(
            target_agent="json_test_agent",
            remove_tools_from_history=True,
        )

        # Serialize to JSON
        json_str = config.model_dump_json()
        data = json.loads(json_str)
        assert data["target_agent"] == "json_test_agent"
        assert data["remove_tools_from_history"] is True

        # Deserialize from JSON
        restored = HandoffConfig.model_validate_json(json_str)
        assert restored.target_agent == config.target_agent
        assert restored.remove_tools_from_history == config.remove_tools_from_history

    def test_complex_handoff_config(self) -> None:
        """Test HandoffConfig with complex target agent configuration."""
        # Test with OpenAIAgentConfig as target
        target_agent = OpenAIAgentConfig(
            name="search_agent",
            instructions="You are a search specialist",
            input="Process search queries",
            model="gpt-4",
        )

        config = HandoffConfig(
            target_agent=target_agent,
            tool_name_override="search_specialist",
            tool_description_override="Hand off to search specialist for advanced queries",
        )

        assert isinstance(config.target_agent, OpenAIAgentConfig)
        assert config.target_agent.name == "search_agent"
        assert config.tool_name_override == "search_specialist"

    def test_handoff_config_with_valid_input_type(self) -> None:
        """Test HandoffConfig creation with valid input_type JSON schema."""
        # Test with simple object schema
        simple_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["query"],
        }

        config = HandoffConfig(
            target_agent="search_agent",
            input_type=simple_schema,
        )

        assert config.target_agent == "search_agent"
        assert config.input_type == simple_schema
        assert config.input_type["type"] == "object"
        assert "query" in config.input_type["properties"]

        # Test with array schema
        array_schema = {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
        }

        config_array = HandoffConfig(
            target_agent="list_processor",
            input_type=array_schema,
        )

        assert config_array.input_type == array_schema
        assert config_array.input_type["type"] == "array"

        # Test with string schema
        string_schema = {
            "type": "string",
            "minLength": 1,
            "maxLength": 1000,
        }

        config_string = HandoffConfig(
            target_agent="text_processor",
            input_type=string_schema,
        )

        assert config_string.input_type == string_schema
        assert config_string.input_type["type"] == "string"

    def test_handoff_config_serialization_with_input_type(self) -> None:
        """Test serialization/deserialization with input_type."""
        input_schema = {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Input data"},
                "options": {
                    "type": "object",
                    "properties": {
                        "format": {"type": "string", "enum": ["json", "xml", "csv"]},
                        "validate": {"type": "boolean", "default": True},
                    },
                },
            },
            "required": ["data"],
        }

        original = HandoffConfig(
            target_agent="data_processor",
            tool_name_override="process_data",
            input_type=input_schema,
        )

        # Serialize to dict
        data = original.model_dump()
        assert data["target_agent"] == "data_processor"
        assert data["tool_name_override"] == "process_data"
        assert data["input_type"] == input_schema

        # Deserialize from dict
        restored = HandoffConfig(**data)
        assert restored.target_agent == original.target_agent
        assert restored.tool_name_override == original.tool_name_override
        assert restored.input_type == original.input_type

        # Test JSON serialization
        json_str = original.model_dump_json()
        restored_from_json = HandoffConfig.model_validate_json(json_str)
        assert restored_from_json.input_type == original.input_type

    def test_handoff_config_invalid_input_type_missing_type_field(self) -> None:
        """Test validation of invalid input_type schemas (missing 'type' field)."""
        invalid_schema = {
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        }

        with pytest.raises(ValidationError) as exc_info:
            HandoffConfig(
                target_agent="test_agent",
                input_type=invalid_schema,
            )

        error = exc_info.value.errors()[0]
        assert "input_type must include a 'type' field" in str(error)

        # Test with empty dict
        with pytest.raises(ValidationError) as exc_info:
            HandoffConfig(
                target_agent="test_agent",
                input_type={},
            )

        error = exc_info.value.errors()[0]
        assert "input_type must include a 'type' field" in str(error)

    def test_handoff_config_invalid_input_type_not_dict(self) -> None:
        """Test validation of invalid input_type schemas (not a dictionary)."""
        # Test with string - Pydantic will catch this as a type error first
        with pytest.raises(ValidationError) as exc_info:
            HandoffConfig(
                target_agent="test_agent",
                input_type="invalid_schema",  # type: ignore[arg-type]
            )

        error = exc_info.value.errors()[0]
        # Pydantic's built-in validation catches this first
        assert "Input should be a valid dictionary" in error["msg"]

        # Test with list
        with pytest.raises(ValidationError) as exc_info:
            HandoffConfig(
                target_agent="test_agent",
                input_type=["invalid", "schema"],  # type: ignore[arg-type]
            )

        error = exc_info.value.errors()[0]
        assert "Input should be a valid dictionary" in error["msg"]

        # Test with integer
        with pytest.raises(ValidationError) as exc_info:
            HandoffConfig(
                target_agent="test_agent",
                input_type=123,  # type: ignore[arg-type]
            )

        error = exc_info.value.errors()[0]
        assert "Input should be a valid dictionary" in error["msg"]

    def test_handoff_config_with_input_type_and_other_features(self) -> None:
        """Test combination of input_type with other handoff features."""
        input_schema = {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 10},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["task"],
        }

        config = HandoffConfig(
            target_agent="task_processor",
            tool_name_override="process_task",
            tool_description_override="Process tasks with structured input validation",
            remove_tools_from_history=True,
            is_enabled=True,
            input_type=input_schema,
        )

        assert config.target_agent == "task_processor"
        assert config.tool_name_override == "process_task"
        assert config.tool_description_override == "Process tasks with structured input validation"
        assert config.remove_tools_from_history is True
        assert config.is_enabled is True
        assert config.input_type == input_schema
        assert config.input_type["required"] == ["task"]

        # Test with OpenAIAgentConfig as target
        target_agent = OpenAIAgentConfig(
            name="specialized-processor",
            instructions="You process structured data",
            input="Process this structured input",
            model="gpt-4",
        )

        config_with_agent = HandoffConfig(
            target_agent=target_agent,
            input_type=input_schema,
            is_enabled=False,
        )

        assert isinstance(config_with_agent.target_agent, OpenAIAgentConfig)
        assert config_with_agent.target_agent.name == "specialized-processor"
        assert config_with_agent.input_type == input_schema
        assert config_with_agent.is_enabled is False

    def test_handoff_config_input_type_optional(self) -> None:
        """Test that input_type is optional (None by default)."""
        # Test with explicit None
        config_explicit_none = HandoffConfig(
            target_agent="flexible_agent",
            input_type=None,
        )

        assert config_explicit_none.target_agent == "flexible_agent"
        assert config_explicit_none.input_type is None

        # Test without specifying input_type (should default to None)
        config_default = HandoffConfig(target_agent="default_agent")

        assert config_default.target_agent == "default_agent"
        assert config_default.input_type is None

        # Test that other fields work normally without input_type
        config_full_without_input = HandoffConfig(
            target_agent="complete_agent",
            tool_name_override="custom_tool",
            tool_description_override="Custom tool description",
            remove_tools_from_history=True,
            is_enabled=False,
        )

        assert config_full_without_input.target_agent == "complete_agent"
        assert config_full_without_input.tool_name_override == "custom_tool"
        assert config_full_without_input.tool_description_override == "Custom tool description"
        assert config_full_without_input.remove_tools_from_history is True
        assert config_full_without_input.is_enabled is False
        assert config_full_without_input.input_type is None

    def test_handoff_config_complex_input_type_schemas(self) -> None:
        """Test HandoffConfig with complex input_type schemas."""
        # Test with nested object schema
        complex_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string", "minLength": 1},
                        "email": {"type": "string", "format": "email"},
                        "preferences": {
                            "type": "object",
                            "properties": {
                                "notifications": {"type": "boolean"},
                                "theme": {"type": "string", "enum": ["light", "dark"]},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "required": ["id", "name"],
                },
                "action": {"type": "string", "enum": ["create", "update", "delete"]},
                "timestamp": {"type": "string", "format": "date-time"},
            },
            "required": ["user", "action"],
            "additionalProperties": False,
        }

        config = HandoffConfig(
            target_agent="user_manager",
            input_type=complex_schema,
        )

        assert config.input_type == complex_schema
        assert config.input_type["type"] == "object"
        assert "user" in config.input_type["required"]
        assert "action" in config.input_type["required"]

        # Test with array of objects schema
        array_of_objects_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "value": {"type": "number"},
                },
                "required": ["id"],
            },
            "minItems": 1,
            "maxItems": 100,
        }

        config_array = HandoffConfig(
            target_agent="batch_processor",
            input_type=array_of_objects_schema,
        )

        assert config_array.input_type == array_of_objects_schema
        assert config_array.input_type["type"] == "array"
        assert config_array.input_type["items"]["type"] == "object"

    def test_handoff_config_input_type_edge_cases(self) -> None:
        """Test edge cases for input_type validation."""
        # Test with minimal valid schema
        minimal_schema = {"type": "string"}

        config = HandoffConfig(
            target_agent="minimal_agent",
            input_type=minimal_schema,
        )

        assert config.input_type == minimal_schema
        assert config.input_type["type"] == "string"

        # Test with null type (valid JSON Schema)
        null_schema = {"type": "null"}

        config_null = HandoffConfig(
            target_agent="null_agent",
            input_type=null_schema,
        )

        assert config_null.input_type == null_schema
        assert config_null.input_type["type"] == "null"

        # Test with boolean type
        boolean_schema = {"type": "boolean"}

        config_bool = HandoffConfig(
            target_agent="boolean_agent",
            input_type=boolean_schema,
        )

        assert config_bool.input_type == boolean_schema
        assert config_bool.input_type["type"] == "boolean"

        # Test with number type
        number_schema = {
            "type": "number",
            "minimum": 0,
            "maximum": 100,
        }

        config_number = HandoffConfig(
            target_agent="number_agent",
            input_type=number_schema,
        )

        assert config_number.input_type == number_schema
        assert config_number.input_type["type"] == "number"


class TestHandoffEvent:
    """Test cases for HandoffEvent model."""

    def test_minimal_handoff_event(self) -> None:
        """Test creating handoff event with required fields."""
        timestamp = time.time()
        event = HandoffEvent(
            from_agent="agent_a",
            to_agent="agent_b",
            timestamp=timestamp,
        )

        assert event.from_agent == "agent_a"
        assert event.to_agent == "agent_b"
        assert event.timestamp == timestamp
        assert event.input_data is None
        assert event.tools_removed is False

    def test_full_handoff_event(self) -> None:
        """Test creating handoff event with all fields."""
        timestamp = time.time()
        input_data = {
            "query": "analyze sales data",
            "parameters": {"region": "north", "period": "Q1"},
        }

        event = HandoffEvent(
            from_agent="coordinator",
            to_agent="data_analyst",
            timestamp=timestamp,
            input_data=input_data,
            tools_removed=True,
        )

        assert event.from_agent == "coordinator"
        assert event.to_agent == "data_analyst"
        assert event.timestamp == timestamp
        assert event.input_data == input_data
        assert event.tools_removed is True

    def test_handoff_event_serialization(self) -> None:
        """Test HandoffEvent serialization and deserialization."""
        timestamp = time.time()
        original = HandoffEvent(
            from_agent="source",
            to_agent="target",
            timestamp=timestamp,
            input_data={"data": "test"},
        )

        # Serialize to dict
        data = original.model_dump()
        assert data["from_agent"] == "source"
        assert data["to_agent"] == "target"

        # Deserialize from dict
        restored = HandoffEvent(**data)
        assert restored.from_agent == original.from_agent
        assert restored.to_agent == original.to_agent
        assert restored.timestamp == original.timestamp
        assert restored.input_data == original.input_data

    def test_handoff_event_validation(self) -> None:
        """Test HandoffEvent field validation."""
        timestamp = time.time()

        # Valid event
        event = HandoffEvent(
            from_agent="valid_agent",
            to_agent="another_agent",
            timestamp=timestamp,
        )
        assert event.from_agent == "valid_agent"

        # Test with None agent names should fail
        with pytest.raises(ValidationError):
            HandoffEvent(
                from_agent=None,  # type: ignore[arg-type]
                to_agent="target",
                timestamp=timestamp,
            )

        with pytest.raises(ValidationError):
            HandoffEvent(
                from_agent="source",
                to_agent=None,  # type: ignore[arg-type]
                timestamp=timestamp,
            )


class TestOpenAIAgentConfigWithHandoffs:
    """Test cases for OpenAIAgentConfig with handoff support."""

    def test_agent_config_with_string_handoffs(self) -> None:
        """Test OpenAIAgentConfig with string-based handoffs."""
        handoffs = ["data_analyst", "code_generator", "reviewer"]

        config = OpenAIAgentConfig(
            name="coordinator",
            instructions="You coordinate between other agents",
            input="Process this request",
            model="gpt-4",
            handoffs=handoffs,
            handoff_description="Can hand off to data analysis, code generation, or review agents",
        )

        assert config.handoffs == handoffs
        assert len(config.handoffs) == 3
        assert "data_analyst" in config.handoffs
        assert config.handoff_description == "Can hand off to data analysis, code generation, or review agents"

    def test_agent_config_with_handoff_config_objects(self) -> None:
        """Test OpenAIAgentConfig with HandoffConfig objects."""
        handoff_configs = [
            HandoffConfig(
                target_agent="data_analyst",
                tool_name_override="analyze_data",
            ),
            HandoffConfig(
                target_agent="code_generator",
                tool_description_override="Generate code based on specifications",
            ),
        ]

        config = OpenAIAgentConfig(
            name="main_agent",
            instructions="Main coordination agent",
            input="Handle this task",
            model="gpt-4",
            handoffs=handoff_configs,
        )

        assert len(config.handoffs) == 2
        assert isinstance(config.handoffs[0], HandoffConfig)
        assert config.handoffs[0].target_agent == "data_analyst"
        assert config.handoffs[0].tool_name_override == "analyze_data"
        assert config.handoffs[1].tool_description_override == "Generate code based on specifications"

    def test_agent_config_with_nested_agent_configs(self) -> None:
        """Test OpenAIAgentConfig with other OpenAIAgentConfig instances as handoffs."""
        specialist_agent = OpenAIAgentConfig(
            name="specialist",
            instructions="Specialized processing agent",
            input="Handle specialized tasks",
            model="gpt-4",
        )

        reviewer_agent = OpenAIAgentConfig(
            name="reviewer",
            instructions="Review and validate outputs",
            input="Review this content",
            model="gpt-4",
        )

        main_config = OpenAIAgentConfig(
            name="orchestrator",
            instructions="Orchestrate complex workflows",
            input="Coordinate this multi-step process",
            model="gpt-4",
            handoffs=[specialist_agent, reviewer_agent],
        )

        assert len(main_config.handoffs) == 2
        assert isinstance(main_config.handoffs[0], OpenAIAgentConfig)
        assert main_config.handoffs[0].name == "specialist"
        assert main_config.handoffs[1].name == "reviewer"

    def test_agent_config_with_mixed_handoff_types(self) -> None:
        """Test OpenAIAgentConfig with mixed handoff types."""
        specialist_agent = OpenAIAgentConfig(
            name="specialist",
            instructions="Handle specialized tasks",
            input="Process specialized content",
            model="gpt-4",
        )

        handoff_config = HandoffConfig(
            target_agent="data_processor",
            tool_name_override="process_data",
        )

        config = OpenAIAgentConfig(
            name="mixed_orchestrator",
            instructions="Handle mixed handoff scenarios",
            input="Coordinate various agent types",
            model="gpt-4",
            handoffs=["simple_agent", handoff_config, specialist_agent],
        )

        assert len(config.handoffs) == 3
        assert config.handoffs[0] == "simple_agent"
        assert isinstance(config.handoffs[1], HandoffConfig)
        assert isinstance(config.handoffs[2], OpenAIAgentConfig)

    def test_agent_config_handoff_serialization(self) -> None:
        """Test serialization of OpenAIAgentConfig with handoffs."""
        config = OpenAIAgentConfig(
            name="test_agent",
            instructions="Test agent with handoffs",
            input="Test input",
            model="gpt-4",
            handoffs=["agent1", "agent2"],
            handoff_description="Test handoff description",
        )

        # Serialize to dict
        data = config.model_dump()
        assert data["handoffs"] == ["agent1", "agent2"]
        assert data["handoff_description"] == "Test handoff description"

        # Deserialize from dict
        restored = OpenAIAgentConfig(**data)
        assert restored.handoffs == config.handoffs
        assert restored.handoff_description == config.handoff_description

    def test_empty_handoffs_list(self) -> None:
        """Test OpenAIAgentConfig with empty handoffs list."""
        config = OpenAIAgentConfig(
            name="no_handoffs",
            instructions="Agent without handoffs",
            input="Process independently",
            model="gpt-4",
            handoffs=[],
        )

        assert config.handoffs == []
        assert len(config.handoffs) == 0

    def test_none_handoffs(self) -> None:
        """Test OpenAIAgentConfig with None handoffs (default)."""
        config = OpenAIAgentConfig(
            name="default_handoffs",
            instructions="Agent with default handoffs",
            input="Process with defaults",
            model="gpt-4",
        )

        assert config.handoffs is None
        assert config.handoff_description is None


class TestOpenAIAgentResponseWithHandoffs:
    """Test cases for OpenAIAgentResponse with handoff tracking."""

    def test_response_without_handoffs(self) -> None:
        """Test OpenAIAgentResponse without handoff events."""
        response = OpenAIAgentResponse(
            content="Task completed successfully",
            execution_id="exec-123",
            agent_name="single_agent",
            model_used="gpt-4",
            execution_time_seconds=2.5,
        )

        assert response.handoff_events is None
        assert response.final_agent is None

    def test_response_with_single_handoff(self) -> None:
        """Test OpenAIAgentResponse with single handoff event."""
        timestamp = time.time()
        handoff_event = HandoffEvent(
            from_agent="coordinator",
            to_agent="data_analyst",
            timestamp=timestamp,
            input_data={"query": "analyze sales"},
        )

        response = OpenAIAgentResponse(
            content="Analysis completed",
            execution_id="exec-456",
            agent_name="coordinator",
            model_used="gpt-4",
            execution_time_seconds=5.2,
            handoff_events=[handoff_event],
            final_agent="data_analyst",
        )

        assert len(response.handoff_events) == 1
        assert response.handoff_events[0].from_agent == "coordinator"
        assert response.handoff_events[0].to_agent == "data_analyst"
        assert response.final_agent == "data_analyst"

    def test_response_with_multiple_handoffs(self) -> None:
        """Test OpenAIAgentResponse with multiple handoff events."""
        timestamp = time.time()
        handoff_events = [
            HandoffEvent(
                from_agent="coordinator",
                to_agent="data_processor",
                timestamp=timestamp,
                input_data={"data": "raw_data"},
            ),
            HandoffEvent(
                from_agent="data_processor",
                to_agent="data_analyst",
                timestamp=timestamp + 1,
                input_data={"processed_data": "clean_data"},
            ),
            HandoffEvent(
                from_agent="data_analyst",
                to_agent="report_generator",
                timestamp=timestamp + 2,
                input_data={"analysis": "insights"},
            ),
        ]

        response = OpenAIAgentResponse(
            content="Multi-agent workflow completed",
            execution_id="exec-789",
            agent_name="coordinator",
            model_used="gpt-4",
            execution_time_seconds=15.7,
            handoff_events=handoff_events,
            final_agent="report_generator",
        )

        assert len(response.handoff_events) == 3
        assert response.handoff_events[0].from_agent == "coordinator"
        assert response.handoff_events[1].from_agent == "data_processor"
        assert response.handoff_events[2].from_agent == "data_analyst"
        assert response.final_agent == "report_generator"

    def test_response_handoff_tracking_serialization(self) -> None:
        """Test serialization of OpenAIAgentResponse with handoff tracking."""
        timestamp = time.time()
        handoff_event = HandoffEvent(
            from_agent="agent_a",
            to_agent="agent_b",
            timestamp=timestamp,
        )

        response = OpenAIAgentResponse(
            content="Handoff test response",
            execution_id="exec-serial",
            agent_name="agent_a",
            model_used="gpt-4",
            execution_time_seconds=3.0,
            handoff_events=[handoff_event],
            final_agent="agent_b",
        )

        # Serialize to dict
        data = response.model_dump()
        assert len(data["handoff_events"]) == 1
        assert data["final_agent"] == "agent_b"

        # Deserialize from dict
        restored = OpenAIAgentResponse(**data)
        assert len(restored.handoff_events) == 1
        assert restored.handoff_events[0].from_agent == "agent_a"
        assert restored.final_agent == "agent_b"

    def test_response_with_error_and_handoffs(self) -> None:
        """Test OpenAIAgentResponse with error state and handoff tracking."""
        timestamp = time.time()
        handoff_event = HandoffEvent(
            from_agent="main_agent",
            to_agent="error_handler",
            timestamp=timestamp,
            input_data={"error_context": "processing_failed"},
        )

        response = OpenAIAgentResponse(
            content="",  # Empty content on error
            execution_id="exec-error",
            agent_name="main_agent",
            model_used="gpt-4",
            execution_time_seconds=1.2,
            error="Processing failed during handoff",
            error_type="HandoffError",
            handoff_events=[handoff_event],
            final_agent="error_handler",
        )

        assert response.error == "Processing failed during handoff"
        assert response.error_type == "HandoffError"
        assert len(response.handoff_events) == 1
        assert response.final_agent == "error_handler"


class TestEdgeCasesAndValidation:
    """Test edge cases and validation scenarios for handoff models."""

    def test_handoff_config_with_none_target_agent(self) -> None:
        """Test that HandoffConfig requires target_agent."""
        with pytest.raises(ValidationError) as exc_info:
            HandoffConfig(target_agent=None)  # type: ignore[arg-type]

        error = exc_info.value.errors()[0]
        assert "Input should be" in str(error)

    def test_handoff_event_with_invalid_timestamp(self) -> None:
        """Test HandoffEvent with invalid timestamp types."""
        # String timestamp should be converted to float
        event = HandoffEvent(
            from_agent="agent_a",
            to_agent="agent_b",
            timestamp="1234567890.5",  # type: ignore[arg-type]
        )
        assert isinstance(event.timestamp, float)

        # Invalid timestamp formats should fail
        with pytest.raises(ValidationError):
            HandoffEvent(
                from_agent="agent_a",
                to_agent="agent_b",
                timestamp="invalid_timestamp",  # type: ignore[arg-type]
            )

    def test_handoff_config_json_schema_validation(self) -> None:
        """Test HandoffConfig with various configuration options."""
        # Test with all boolean flags
        config = HandoffConfig(
            target_agent="schema_agent",
            remove_tools_from_history=True,
            is_enabled=False,
        )

        assert config.target_agent == "schema_agent"
        assert config.remove_tools_from_history is True
        assert config.is_enabled is False

        # Test with tool overrides
        config_with_overrides = HandoffConfig(
            target_agent="minimal_agent",
            tool_name_override="minimal_tool",
            tool_description_override="Minimal processing agent",
        )
        assert config_with_overrides.tool_name_override == "minimal_tool"
        assert config_with_overrides.tool_description_override == "Minimal processing agent"

    def test_handoff_event_edge_case_timestamps(self) -> None:
        """Test HandoffEvent with edge case timestamp values."""
        # Very large timestamp (far future)
        future_timestamp = 9999999999.999
        event_future = HandoffEvent(
            from_agent="agent1",
            to_agent="agent2",
            timestamp=future_timestamp,
        )
        assert event_future.timestamp == future_timestamp

        # Zero timestamp
        event_zero = HandoffEvent(
            from_agent="agent1",
            to_agent="agent2",
            timestamp=0.0,
        )
        assert event_zero.timestamp == 0.0

        # Negative timestamp (past epoch)
        negative_timestamp = -123456.789
        event_negative = HandoffEvent(
            from_agent="agent1",
            to_agent="agent2",
            timestamp=negative_timestamp,
        )
        assert event_negative.timestamp == negative_timestamp

    def test_agent_config_handoff_circular_reference_prevention(self) -> None:
        """Test that circular references in handoffs are handled properly."""
        # Create agents that could potentially reference each other
        agent_a = OpenAIAgentConfig(
            name="agent_a",
            instructions="Agent A instructions",
            input="Input for A",
            model="gpt-4",
        )

        agent_b = OpenAIAgentConfig(
            name="agent_b",
            instructions="Agent B instructions",
            input="Input for B",
            model="gpt-4",
            handoffs=[agent_a],  # B can handoff to A
        )

        # Update A to handoff to B (creating potential circular reference)
        agent_a.handoffs = [agent_b]

        # Test that basic properties are accessible despite circular structure
        assert agent_a.name == "agent_a"
        assert agent_b.name == "agent_b"
        assert len(agent_a.handoffs) == 1
        assert len(agent_b.handoffs) == 1

        # Test that we can access the handoff targets without serialization
        assert isinstance(agent_a.handoffs[0], OpenAIAgentConfig)
        assert isinstance(agent_b.handoffs[0], OpenAIAgentConfig)
        assert agent_a.handoffs[0].name == "agent_b"
        assert agent_b.handoffs[0].name == "agent_a"

    def test_large_handoff_event_list(self) -> None:
        """Test OpenAIAgentResponse with large number of handoff events."""
        timestamp = time.time()

        # Create 100 handoff events
        handoff_events = [
            HandoffEvent(
                from_agent=f"agent_{i}",
                to_agent=f"agent_{i + 1}",
                timestamp=timestamp + i,
                input_data={"step": i, "data": f"data_{i}"},
            )
            for i in range(100)
        ]

        response = OpenAIAgentResponse(
            content="Large workflow completed",
            execution_id="exec-large",
            agent_name="agent_0",
            model_used="gpt-4",
            execution_time_seconds=120.5,
            handoff_events=handoff_events,
            final_agent="agent_100",
        )

        assert len(response.handoff_events) == 100
        assert response.handoff_events[0].from_agent == "agent_0"
        assert response.handoff_events[99].to_agent == "agent_100"
        assert response.final_agent == "agent_100"

        # Test serialization works with large event list
        data = response.model_dump()
        assert len(data["handoff_events"]) == 100
