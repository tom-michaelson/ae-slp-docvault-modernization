"""Factory for creating handoff objects for OpenAI agents from AWA configuration.

This module provides utilities to transform AWA's HandoffConfig models into
handoff objects that can be consumed by the OpenAI Agents SDK, supporting
tool customizations, filtering, and conditional enablement.
"""

import dataclasses
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Union

from agents import Agent, handoff
from agents.handoffs import HandoffInputData
from pydantic import create_model

from awa.sdk.models.openai_agents.openai_agent_config import HandoffConfig

if TYPE_CHECKING:
    from awa.sdk.models.openai_agents.openai_agent_config import OpenAIAgentConfig


class HandoffBuilder:
    """Factory for creating handoff objects from AWA configuration.

    This factory handles the conversion of AWA's HandoffConfig models
    to handoff objects compatible with the OpenAI Agents SDK, supporting
    customizations, filtering, and conditional enablement.
    """

    @staticmethod
    def build_handoff(
        config: HandoffConfig,
        target_agent_instance: Agent | str | None = None,
    ) -> Any:  # noqa: ANN401
        """Create handoff objects from HandoffConfig.

        Args:
            config: AWA handoff configuration model
            target_agent_instance: Optional Agent instance or agent name to override config

        Returns:
            Handoff object compatible with OpenAI Agents SDK

        Raises:
            ValueError: If the configuration is invalid or disabled

        """
        if not config.is_enabled:
            msg = f"Handoff configuration for target '{config.target_agent}' is disabled"
            raise ValueError(msg)

        # Determine the target agent
        target = target_agent_instance if target_agent_instance is not None else config.target_agent

        # Build the handoff parameters
        handoff_params = HandoffBuilder._build_handoff_params(config, target)

        # Apply input filter if remove_tools_from_history is enabled
        if config.remove_tools_from_history:
            handoff_params["input_filter"] = HandoffBuilder._create_remove_tools_filter()

        # Create the handoff object
        handoff_obj = handoff(**handoff_params)

        return handoff_obj

    @staticmethod
    def _build_handoff_params(
        config: HandoffConfig,
        target: Union[Agent, str, "OpenAIAgentConfig"],
    ) -> dict[str, Any]:
        """Build parameters for handoff function.

        Args:
            config: HandoffConfig containing customization settings
            target: Target agent for the handoff

        Returns:
            Dictionary of parameters for handoff function

        """
        params = {"agent": target}

        # Apply tool name override
        if config.tool_name_override:
            params["tool_name_override"] = config.tool_name_override

        # Apply tool description override
        if config.tool_description_override:
            params["tool_description_override"] = config.tool_description_override

        # Handle input_type if specified
        if config.input_type:
            # Create Python type from JSON schema
            input_type = HandoffBuilder._create_type_from_schema(config.input_type)
            params["input_type"] = input_type

            # Create no-op on_handoff callback when using input_type
            params["on_handoff"] = HandoffBuilder._create_noop_on_handoff()

        return params

    @staticmethod
    def _create_remove_tools_filter() -> Callable[[HandoffInputData], HandoffInputData]:
        """Create a filter function that removes tool-related messages from conversation history.

        Returns:
            Filter function that takes HandoffInputData and returns filtered HandoffInputData

        """

        def remove_tools_filter(data: HandoffInputData) -> HandoffInputData:
            """Filter out tool-related messages from the conversation history.

            This removes tool call and tool result messages to create a cleaner
            conversation history for the next agent.

            Args:
                data: HandoffInputData containing conversation history

            Returns:
                HandoffInputData with tool messages filtered out

            """
            # Filter tool-related items from new_items
            filtered_new_items = []
            for item in data.new_items:
                # Check if this is a tool-related item
                # This is a simplified filter - in practice you might want to be more specific
                # about which tool messages to filter based on the item type/content
                item_type = type(item).__name__

                # Skip items that appear to be tool calls or tool responses
                # This is a basic implementation - you may need to adjust based on actual item types
                if "tool" not in item_type.lower() and "function" not in item_type.lower():
                    filtered_new_items.append(item)

            # Return a new HandoffInputData with filtered items
            return dataclasses.replace(data, new_items=tuple(filtered_new_items))

        return remove_tools_filter

    @staticmethod
    def _create_type_from_schema(schema: dict[str, Any]) -> type:
        """Create a Pydantic model from a JSON schema.

        Args:
            schema: JSON schema dictionary containing type definitions

        Returns:
            Pydantic model class that can be used as input_type

        Raises:
            ValueError: If the schema is invalid or cannot be converted

        """
        try:
            # Handle the case where schema has properties (object type)
            if "properties" in schema:
                properties = schema["properties"]
                field_definitions = {}

                for field_name, field_def in properties.items():
                    # Get required fields from schema
                    required_fields = schema.get("required", [])
                    is_required = field_name in required_fields

                    # Map JSON schema types to Python types
                    field_type = HandoffBuilder._json_schema_type_to_python_type(field_def)

                    # Create field definition tuple (type, default_value)
                    if is_required:
                        field_definitions[field_name] = (field_type, ...)
                    else:
                        field_definitions[field_name] = (field_type, None)

                # Create dynamic Pydantic model
                return create_model("HandoffInputType", **field_definitions)

            # Handle simple types (string, int, etc.)
            if "type" in schema:
                python_type = HandoffBuilder._json_schema_type_to_python_type(schema)
                return create_model("HandoffInputType", value=(python_type, ...))

            # Default to a simple string model if schema structure is unclear
            return create_model("HandoffInputType", value=(str, ...))

        except Exception as e:
            msg = f"Failed to create type from schema: {e}"
            raise ValueError(msg) from e

    @staticmethod
    def _json_schema_type_to_python_type(field_def: dict[str, Any]) -> type:
        """Convert JSON schema type definition to Python type.

        Args:
            field_def: JSON schema field definition

        Returns:
            Corresponding Python type

        """
        json_type = field_def.get("type", "string")

        type_mapping = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        return type_mapping.get(json_type, str)

    @staticmethod
    def _create_noop_on_handoff() -> Callable:
        """Create a no-op callback that satisfies the SDK requirement.

        Returns:
            A callable that does nothing but satisfies the on_handoff parameter requirement

        """

        def noop_callback(*args: Any, **kwargs: Any) -> None:  # noqa: ANN401
            """No-op callback function that does nothing."""

        return noop_callback

    @staticmethod
    def build_multiple_handoffs(
        configs: list[HandoffConfig],
        target_agent_instances: dict[str, Agent | str] | None = None,
    ) -> list[Any]:
        """Create multiple handoff objects from a list of configurations.

        Args:
            configs: List of AWA handoff configuration models
            target_agent_instances: Optional mapping of target names to agent instances

        Returns:
            List of handoff objects compatible with OpenAI Agents SDK

        Raises:
            ValueError: If any configuration is invalid

        """
        if not configs:
            return []

        handoffs = []
        target_mapping = target_agent_instances or {}

        for idx, config in enumerate(configs):
            try:
                # Skip disabled configurations
                if not config.is_enabled:
                    continue

                # Get target agent instance if available
                target_key = str(config.target_agent)
                target_instance = target_mapping.get(target_key)

                handoff_obj = HandoffBuilder.build_handoff(config, target_instance)
                handoffs.append(handoff_obj)

            except ValueError as e:
                msg = f"Error building handoff at index {idx}: {e}"
                raise ValueError(msg) from e

        return handoffs

    @staticmethod
    def validate_handoff_config(config: HandoffConfig) -> list[str]:
        """Validate a handoff configuration and return any validation errors.

        Args:
            config: HandoffConfig to validate

        Returns:
            List of validation error messages (empty if valid)

        """
        errors = []

        # Check if target agent is specified
        if not config.target_agent:
            errors.append("Handoff configuration requires a target_agent")

        # Validate input_type schema if provided
        if config.input_type:
            try:
                # Basic JSON schema validation
                if not isinstance(config.input_type, dict):
                    errors.append("input_type must be a valid JSON schema dictionary")
                # Check for basic schema structure
                elif "properties" in config.input_type:
                    properties = config.input_type["properties"]
                    if not isinstance(properties, dict):
                        errors.append("input_type properties must be a dictionary")
                    else:
                        # Validate each property has a type
                        for prop_name, prop_def in properties.items():
                            if not isinstance(prop_def, dict) or "type" not in prop_def:
                                errors.append(f"Property '{prop_name}' must have a type definition")
                            else:
                                # Validate the type is supported
                                prop_type = prop_def.get("type")
                                supported_types = {"string", "integer", "number", "boolean", "array", "object"}
                                if prop_type not in supported_types:
                                    errors.append(
                                        f"Property '{prop_name}' has unsupported type '{prop_type}'. "
                                        f"Supported types: {', '.join(supported_types)}",
                                    )

                # Test schema-to-type conversion
                try:
                    HandoffBuilder._create_type_from_schema(config.input_type)
                except ValueError as e:
                    errors.append(f"Failed to create type from input_type schema: {e}")

            except (TypeError, AttributeError):
                errors.append("input_type must be a valid JSON schema")

        return errors
