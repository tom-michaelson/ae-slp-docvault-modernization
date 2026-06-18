"""Unit tests for handoff filters functionality."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from awa.sdk.models.openai_agents import OpenAIAgentConfig
from awa.sdk.models.openai_agents.openai_agent_config import HandoffConfig

# Ensure models are rebuilt to handle forward references
HandoffConfig.model_rebuild()
OpenAIAgentConfig.model_rebuild()


class TestHandoffWithFiltersTrue:
    """Test cases for handoff with remove_tools_from_history=True."""

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_remove_tools_true(self, mock_handoff: MagicMock) -> None:
        """Test handoff creation with remove_tools_from_history=True adds input_filter."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        # Setup mock
        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        config = HandoffConfig(
            target_agent="test_agent",
            remove_tools_from_history=True,
        )

        result = HandoffBuilder.build_handoff(config)

        # Verify handoff was created with input_filter when remove_tools is True
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert "agent" in call_kwargs
        assert call_kwargs["agent"] == "test_agent"
        assert "input_filter" in call_kwargs  # Filter should be present
        assert callable(call_kwargs["input_filter"])  # Should be a function

        # Verify handoff object is returned
        assert result == mock_handoff_obj

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_complex_config_and_filters(self, mock_handoff: MagicMock) -> None:
        """Test handoff with full configuration and filters enabled."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        config = HandoffConfig(
            target_agent="complex_agent",
            tool_name_override="complex_handoff",
            tool_description_override="Complex handoff with filtering",
            remove_tools_from_history=True,
        )

        result = HandoffBuilder.build_handoff(config)

        # Check the call was made with expected parameters
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == "complex_agent"
        assert call_kwargs["tool_name_override"] == "complex_handoff"
        assert call_kwargs["tool_description_override"] == "Complex handoff with filtering"
        assert "input_filter" in call_kwargs  # Filter should be present

        # Verify handoff object is returned
        assert result == mock_handoff_obj

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_agent_config_target_and_filters(self, mock_handoff: MagicMock) -> None:
        """Test handoff with OpenAIAgentConfig target and filters enabled."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        target_agent = OpenAIAgentConfig(
            name="target_agent",
            instructions="Target agent instructions",
            input="Target input",
            model="gpt-4",
        )

        config = HandoffConfig(
            target_agent=target_agent,
            remove_tools_from_history=True,
        )

        result = HandoffBuilder.build_handoff(config)

        # Verify handoff was created with OpenAIAgentConfig
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == target_agent
        assert "input_filter" in call_kwargs

        # Verify handoff object is returned
        assert result == mock_handoff_obj


class TestHandoffWithFiltersFalse:
    """Test cases for handoff with remove_tools_from_history=False."""

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_remove_tools_false(self, mock_handoff: MagicMock) -> None:
        """Test handoff creation with remove_tools_from_history=False doesn't add filter."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        config = HandoffConfig(
            target_agent="test_agent",
            remove_tools_from_history=False,
        )

        result = HandoffBuilder.build_handoff(config)

        # Verify handoff was created WITHOUT input_filter
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == "test_agent"
        assert "input_filter" not in call_kwargs  # Filter should NOT be present

        # Verify handoff object is returned
        assert result == mock_handoff_obj

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_default_filter_setting(self, mock_handoff: MagicMock) -> None:
        """Test handoff with default remove_tools_from_history (should be False)."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        config = HandoffConfig(target_agent="default_agent")

        result = HandoffBuilder.build_handoff(config)

        # Default should be False, so no filter
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert "input_filter" not in call_kwargs

        assert result == mock_handoff_obj

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_complex_config_no_filters(self, mock_handoff: MagicMock) -> None:
        """Test complex handoff configuration without filters."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        config = HandoffConfig(
            target_agent="complex_agent",
            tool_name_override="complex_tool",
            tool_description_override="Complex description",
            remove_tools_from_history=False,
        )

        result = HandoffBuilder.build_handoff(config)

        # Verify all parameters except filter
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == "complex_agent"
        assert call_kwargs["tool_name_override"] == "complex_tool"
        assert call_kwargs["tool_description_override"] == "Complex description"
        assert "input_filter" not in call_kwargs

        assert result == mock_handoff_obj


class TestFilterApplicationScenarios:
    """Test various scenarios of filter application."""

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_multiple_handoffs_with_mixed_filter_settings(self, mock_handoff: MagicMock) -> None:
        """Test creating multiple handoffs with different filter settings."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        # Create handoffs with different settings
        configs = [
            HandoffConfig(target_agent="agent1", remove_tools_from_history=True),
            HandoffConfig(target_agent="agent2", remove_tools_from_history=False),
            HandoffConfig(target_agent="agent3"),  # Default (False)
        ]

        for config in configs:
            HandoffBuilder.build_handoff(config)

        # Verify each call
        assert mock_handoff.call_count == 3
        calls = mock_handoff.call_args_list

        # First call should have filter
        assert "input_filter" in calls[0].kwargs

        # Second and third calls should not have filter
        assert "input_filter" not in calls[1].kwargs
        assert "input_filter" not in calls[2].kwargs

    def test_handoff_with_disabled_config_skips_filters(self) -> None:
        """Test that disabled handoff configurations raise error."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        config = HandoffConfig(
            target_agent="disabled_agent",
            remove_tools_from_history=True,
            is_enabled=False,
        )

        with pytest.raises(ValueError, match="disabled"):
            HandoffBuilder.build_handoff(config)

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_filter_application_with_custom_target_agent(self, mock_handoff: MagicMock) -> None:
        """Test filter application when using custom target agent instance."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        config = HandoffConfig(
            target_agent="config_agent",
            remove_tools_from_history=True,
        )

        # Override with custom target
        custom_target = Mock(spec=["name"])
        custom_target.name = "custom_agent"

        HandoffBuilder.build_handoff(config, target_agent_instance=custom_target)

        # Should use custom target but still apply filter
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == custom_target
        assert "input_filter" in call_kwargs

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_filter_error_handling(self, mock_handoff: MagicMock) -> None:
        """Test that errors in handoff creation are properly propagated."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.side_effect = RuntimeError("Handoff creation failed")

        config = HandoffConfig(
            target_agent="error_agent",
            remove_tools_from_history=True,
        )

        with pytest.raises(RuntimeError, match="Handoff creation failed"):
            HandoffBuilder.build_handoff(config)


class TestHandoffConfigSerializationWithFilters:
    """Test serialization of HandoffConfig with filter settings."""

    def test_complex_handoff_config_serialization_with_filters(self) -> None:
        """Test serialization of complex HandoffConfig with all fields and filters."""
        config = HandoffConfig(
            target_agent="complex_filter_agent",
            tool_name_override="complex_filtered_handoff",
            tool_description_override="Complex handoff with comprehensive filtering",
            remove_tools_from_history=True,
            is_enabled=True,
        )

        # Test serialization
        data = config.model_dump()

        assert data["remove_tools_from_history"] is True

        # Test JSON round-trip with complex data
        json_str = config.model_dump_json()
        restored = HandoffConfig.model_validate_json(json_str)

        assert restored.remove_tools_from_history is True
        assert restored.tool_name_override == "complex_filtered_handoff"

    def test_handoff_config_with_agent_target_serialization(self) -> None:
        """Test serialization when target_agent is an OpenAIAgentConfig instance."""
        target_agent = OpenAIAgentConfig(
            name="serialized_agent",
            instructions="Agent for serialization testing",
            input="Test input",
            model="gpt-4",
        )

        config = HandoffConfig(
            target_agent=target_agent,
            remove_tools_from_history=True,
        )

        # Test serialization
        data = config.model_dump()

        assert data["remove_tools_from_history"] is True
        assert isinstance(data["target_agent"], dict)
        assert data["target_agent"]["name"] == "serialized_agent"

        # Test deserialization
        restored = HandoffConfig(**data)

        assert restored.remove_tools_from_history is True
        assert isinstance(restored.target_agent, OpenAIAgentConfig)
        assert restored.target_agent.name == "serialized_agent"


class TestHandoffConfigValidationWithFilters:
    """Test validation scenarios specific to filter configurations."""

    def test_valid_filter_configurations(self) -> None:
        """Test that various filter configurations are valid."""
        # True setting
        config_true = HandoffConfig(
            target_agent="test_agent",
            remove_tools_from_history=True,
        )
        assert config_true.remove_tools_from_history is True

        # False setting
        config_false = HandoffConfig(
            target_agent="test_agent",
            remove_tools_from_history=False,
        )
        assert config_false.remove_tools_from_history is False

        # Default setting (should be False)
        config_default = HandoffConfig(target_agent="test_agent")
        assert config_default.remove_tools_from_history is False

    def test_filter_setting_with_complex_configurations(self) -> None:
        """Test filter setting in combination with complex configurations."""
        # Test with all possible field combinations
        config = HandoffConfig(
            target_agent="complex_agent",
            tool_name_override="complex_tool",
            tool_description_override="Complex description",
            remove_tools_from_history=True,
            is_enabled=True,
        )

        # All fields should be valid and preserved
        assert config.remove_tools_from_history is True
        assert config.tool_name_override == "complex_tool"
        assert config.is_enabled is True

    def test_invalid_filter_type_validation(self) -> None:
        """Test validation when invalid types are provided for remove_tools_from_history."""
        # Test with invalid type (should be coerced or fail validation)
        with pytest.raises(ValidationError):
            HandoffConfig(
                target_agent="test_agent",
                remove_tools_from_history="invalid",  # type: ignore[arg-type]
            )

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_filter_config_validation_by_handoff_builder(self, mock_handoff: MagicMock) -> None:
        """Test that HandoffBuilder properly validates filter configurations."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        # Valid configuration with filters
        valid_config = HandoffConfig(
            target_agent="valid_agent",
            remove_tools_from_history=True,
        )

        result = HandoffBuilder.build_handoff(valid_config)
        assert result is not None

        # Check filter was applied
        call_kwargs = mock_handoff.call_args.kwargs
        assert "input_filter" in call_kwargs

    def test_serialization_of_default_filter_value(self) -> None:
        """Test that default filter value is properly serialized."""
        config = HandoffConfig(target_agent="test_agent")

        data = config.model_dump()
        assert data["remove_tools_from_history"] is False

        # Test deserialization preserves default
        restored = HandoffConfig(**data)
        assert restored.remove_tools_from_history is False


class TestTypedHandoffIntegration:
    """Integration tests for typed handoffs with HandoffBuilder."""

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_builder_with_input_type(self, mock_handoff: MagicMock) -> None:
        """Test handoff creation with input_type specified."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff_obj = Mock()
        mock_handoff.return_value = mock_handoff_obj

        # Simple string type schema
        input_schema = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            "required": ["query"],
        }

        config = HandoffConfig(
            target_agent="typed_agent",
            input_type=input_schema,
        )

        result = HandoffBuilder.build_handoff(config)

        # Verify handoff was created with input_type and on_handoff
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == "typed_agent"
        assert "input_type" in call_kwargs
        assert "on_handoff" in call_kwargs
        assert callable(call_kwargs["on_handoff"])

        # Verify the input_type is a Pydantic model
        input_type = call_kwargs["input_type"]
        assert hasattr(input_type, "model_fields")  # Pydantic v2 model characteristic

        # Verify handoff object is returned
        assert result == mock_handoff_obj

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_builder_input_type_conversion(self, mock_handoff: MagicMock) -> None:
        """Test that input_type is correctly converted from JSON schema to Python types."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        # Complex schema with different types
        input_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "height": {"type": "number"},
                "is_active": {"type": "boolean"},
                "tags": {"type": "array"},
                "metadata": {"type": "object"},
            },
            "required": ["name", "age"],
        }

        config = HandoffConfig(
            target_agent="conversion_agent",
            input_type=input_schema,
        )

        HandoffBuilder.build_handoff(config)

        # Check that schema was properly converted
        call_kwargs = mock_handoff.call_args.kwargs
        input_type = call_kwargs["input_type"]

        # Verify it's a Pydantic model that can be instantiated
        assert hasattr(input_type, "model_fields")

        # Test that the model can be created with valid data
        try:
            instance = input_type(name="test", age=25)
            assert instance.name == "test"
            assert instance.age == 25
        except (TypeError, ValueError, ValidationError) as e:
            pytest.fail(f"Failed to create instance of converted type: {e}")

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_builder_input_type_with_filter(self, mock_handoff: MagicMock) -> None:
        """Test combination of input_type with input_filter functionality."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        input_schema = {
            "type": "object",
            "properties": {
                "data": {"type": "string"},
            },
            "required": ["data"],
        }

        config = HandoffConfig(
            target_agent="filtered_typed_agent",
            input_type=input_schema,
            remove_tools_from_history=True,  # Enable filtering
        )

        HandoffBuilder.build_handoff(config)

        # Verify both input_type and input_filter are present
        call_kwargs = mock_handoff.call_args.kwargs
        assert "input_type" in call_kwargs
        assert "input_filter" in call_kwargs
        assert "on_handoff" in call_kwargs
        assert callable(call_kwargs["input_filter"])
        assert callable(call_kwargs["on_handoff"])

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_multiple_handoffs_different_input_types(self, mock_handoff: MagicMock) -> None:
        """Test multiple handoffs with different input_types."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        # Create different schemas
        schema1 = {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

        schema2 = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"},
                "active": {"type": "boolean"},
            },
            "required": ["count"],
        }

        configs = [
            HandoffConfig(target_agent="agent1", input_type=schema1),
            HandoffConfig(target_agent="agent2", input_type=schema2),
            HandoffConfig(target_agent="agent3"),  # No input_type
        ]

        results = HandoffBuilder.build_multiple_handoffs(configs)

        assert len(results) == 3
        assert mock_handoff.call_count == 3

        calls = mock_handoff.call_args_list

        # First call should have input_type and on_handoff
        assert "input_type" in calls[0].kwargs
        assert "on_handoff" in calls[0].kwargs

        # Second call should have input_type and on_handoff
        assert "input_type" in calls[1].kwargs
        assert "on_handoff" in calls[1].kwargs

        # Third call should not have input_type or on_handoff
        assert "input_type" not in calls[2].kwargs
        assert "on_handoff" not in calls[2].kwargs

    def test_handoff_builder_invalid_input_type_schema(self) -> None:
        """Test error handling when schema cannot be converted."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        # Test the type conversion directly since config validation prevents invalid schemas
        # This schema has invalid property definition format
        invalid_schema = {
            "type": "object",
            "properties": {"field": "not_a_dict"},  # Properties should be dicts
        }

        with pytest.raises(ValueError, match="Failed to create type from schema"):
            HandoffBuilder._create_type_from_schema(invalid_schema)

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_builder_simple_type_schema(self, mock_handoff: MagicMock) -> None:
        """Test handling of simple type schemas (non-object)."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        # Simple string type
        simple_schema = {"type": "string"}

        config = HandoffConfig(
            target_agent="simple_agent",
            input_type=simple_schema,
        )

        HandoffBuilder.build_handoff(config)

        call_kwargs = mock_handoff.call_args.kwargs
        assert "input_type" in call_kwargs
        assert "on_handoff" in call_kwargs

        # Verify the converted type works
        input_type = call_kwargs["input_type"]
        try:
            instance = input_type(value="test string")
            assert instance.value == "test string"
        except (TypeError, ValueError, ValidationError) as e:
            pytest.fail(f"Failed to create instance of simple type: {e}")

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_handoff_with_complex_config_and_input_type(self, mock_handoff: MagicMock) -> None:
        """Test handoff with full configuration including input_type."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        input_schema = {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                "urgent": {"type": "boolean", "default": False},
            },
            "required": ["task", "priority"],
        }

        config = HandoffConfig(
            target_agent="full_config_agent",
            tool_name_override="complex_typed_handoff",
            tool_description_override="Complex handoff with type validation",
            remove_tools_from_history=True,
            input_type=input_schema,
            is_enabled=True,
        )

        result = HandoffBuilder.build_handoff(config)

        # Check all parameters are present
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == "full_config_agent"
        assert call_kwargs["tool_name_override"] == "complex_typed_handoff"
        assert call_kwargs["tool_description_override"] == "Complex handoff with type validation"
        assert "input_filter" in call_kwargs  # From remove_tools_from_history
        assert "input_type" in call_kwargs  # From input_type
        assert "on_handoff" in call_kwargs  # From input_type

        assert result is not None

    def test_input_type_validation_in_config(self) -> None:
        """Test that HandoffConfig properly validates input_type schemas."""
        # Valid schema
        valid_schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }

        config = HandoffConfig(
            target_agent="valid_agent",
            input_type=valid_schema,
        )
        assert config.input_type == valid_schema

        # Invalid schema - missing type
        with pytest.raises(ValidationError, match="input_type must include a 'type' field"):
            HandoffConfig(
                target_agent="invalid_agent",
                input_type={"properties": {"name": {"type": "string"}}},
            )

        # Invalid schema - not a dict
        with pytest.raises(ValidationError, match="Input should be a valid dictionary"):
            HandoffConfig(
                target_agent="invalid_agent",
                input_type="not_a_dict",  # type: ignore[arg-type]
            )

    def test_handoff_config_validation_method(self) -> None:
        """Test the validate_handoff_config method with input_type schemas."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        # Valid configuration
        valid_config = HandoffConfig(
            target_agent="test_agent",
            input_type={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        )

        errors = HandoffBuilder.validate_handoff_config(valid_config)
        assert errors == []

        # Invalid schema with unsupported type
        invalid_config = HandoffConfig(
            target_agent="test_agent",
            input_type={
                "type": "object",
                "properties": {"custom": {"type": "unsupported_type"}},
            },
        )

        errors = HandoffBuilder.validate_handoff_config(invalid_config)
        assert len(errors) > 0
        assert any("unsupported type" in error.lower() for error in errors)

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_noop_on_handoff_callback(self, mock_handoff: MagicMock) -> None:
        """Test that the noop on_handoff callback is properly created."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        config = HandoffConfig(
            target_agent="callback_agent",
            input_type={"type": "string"},
        )

        HandoffBuilder.build_handoff(config)

        call_kwargs = mock_handoff.call_args.kwargs
        on_handoff = call_kwargs["on_handoff"]

        # Test that the callback can be called without errors
        try:
            on_handoff()  # No args
            on_handoff("arg1", "arg2")  # With args
            on_handoff(key="value")  # With kwargs
            on_handoff("arg", key="value")  # With both
        except (TypeError, ValueError, RuntimeError) as e:
            pytest.fail(f"Noop callback should not raise errors: {e}")

    @patch("awa.core.utils.openai_agents_handoff_builder.handoff")
    def test_input_type_with_agent_config_target(self, mock_handoff: MagicMock) -> None:
        """Test input_type functionality with OpenAIAgentConfig as target."""
        from awa.core.utils.openai_agents_handoff_builder import HandoffBuilder

        mock_handoff.return_value = Mock()

        target_agent = OpenAIAgentConfig(
            name="typed_target_agent",
            instructions="Target agent with type validation",
            input="Typed input",
            model="gpt-4",
        )

        input_schema = {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        }

        config = HandoffConfig(
            target_agent=target_agent,
            input_type=input_schema,
        )

        result = HandoffBuilder.build_handoff(config)

        # Verify handoff was created with OpenAIAgentConfig and input_type
        mock_handoff.assert_called_once()
        call_kwargs = mock_handoff.call_args.kwargs
        assert call_kwargs["agent"] == target_agent
        assert "input_type" in call_kwargs
        assert "on_handoff" in call_kwargs

        assert result is not None
