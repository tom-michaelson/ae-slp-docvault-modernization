"""Test cases for resolve_config_variables activity."""

import json
import os

import pytest

from awa.core.activities.resolve_config_variables import resolve_config_variables_activity


class TestResolveConfigVariablesActivity:
    """Test cases for resolve_config_variables_activity."""

    @pytest.mark.asyncio
    async def test_resolve_string_with_env_vars(self) -> None:
        """Test resolving environment variables in a string."""
        # Set up test environment variable
        os.environ["TEST_VAR"] = "test_value"

        try:
            input_str = "prefix_${TEST_VAR}_suffix"
            input_json = json.dumps(input_str)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps("prefix_test_value_suffix")
            assert result == expected_json
        finally:
            # Clean up
            del os.environ["TEST_VAR"]

    @pytest.mark.asyncio
    async def test_resolve_dict_with_env_vars(self) -> None:
        """Test resolving environment variables in a nested dictionary."""
        os.environ["TEST_HOST"] = "localhost"
        os.environ["TEST_PORT"] = "8080"

        try:
            input_dict = {
                "host": "${TEST_HOST}",
                "port": "${TEST_PORT}",
                "nested": {
                    "url": "http://${TEST_HOST}:${TEST_PORT}/api",
                },
            }
            input_json = json.dumps(input_dict)

            result = await resolve_config_variables_activity(input_json)

            expected = {
                "host": "localhost",
                "port": "8080",
                "nested": {
                    "url": "http://localhost:8080/api",
                },
            }
            expected_json = json.dumps(expected)
            assert result == expected_json
        finally:
            del os.environ["TEST_HOST"]
            del os.environ["TEST_PORT"]

    @pytest.mark.asyncio
    async def test_resolve_list_with_env_vars(self) -> None:
        """Test resolving environment variables in a list."""
        os.environ["TEST_ITEM"] = "resolved_item"

        try:
            input_list = ["static_item", "${TEST_ITEM}", ["nested_${TEST_ITEM}"]]
            input_json = json.dumps(input_list)
            result = await resolve_config_variables_activity(input_json)

            expected = ["static_item", "resolved_item", ["nested_resolved_item"]]
            expected_json = json.dumps(expected)
            assert result == expected_json
        finally:
            del os.environ["TEST_ITEM"]

    @pytest.mark.asyncio
    async def test_resolve_missing_env_var_raises_error(self) -> None:
        """Test that missing environment variables raise appropriate errors."""
        input_str = "prefix_${MISSING_VAR}_suffix"
        input_json = json.dumps(input_str)

        with pytest.raises(ValueError, match="Required environment variables not set: MISSING_VAR"):
            await resolve_config_variables_activity(input_json)

    @pytest.mark.asyncio
    async def test_resolve_multiple_missing_env_vars(self) -> None:
        """Test error message for multiple missing environment variables."""
        input_str = "${MISSING_VAR1}_${MISSING_VAR2}"
        input_json = json.dumps(input_str)

        with pytest.raises(ValueError, match="Required environment variables not set: MISSING_VAR1, MISSING_VAR2"):
            await resolve_config_variables_activity(input_json)

    @pytest.mark.asyncio
    async def test_resolve_non_string_types_unchanged(self) -> None:
        """Test that non-string types are returned unchanged."""
        test_cases = [
            123,
            45.67,
            True,
            False,
            None,
        ]

        for test_input in test_cases:
            input_json = json.dumps(test_input)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps(test_input)
            assert result == expected_json

    @pytest.mark.asyncio
    async def test_resolve_mixed_complex_structure(self) -> None:
        """Test resolving environment variables in a complex mixed structure."""
        os.environ["DB_HOST"] = "prod-db"
        os.environ["DB_PORT"] = "5432"
        os.environ["API_KEY"] = "secret123"

        try:
            input_data = {
                "database": {
                    "host": "${DB_HOST}",
                    "port": "${DB_PORT}",
                    "config": {
                        "timeout": 30,
                        "ssl": True,
                        "connection_string": "postgresql://${DB_HOST}:${DB_PORT}/mydb",
                    },
                },
                "api": {
                    "key": "${API_KEY}",
                    "endpoints": [
                        "https://${DB_HOST}/api/v1",
                        "https://${DB_HOST}/api/v2",
                    ],
                },
                "static_config": {
                    "debug": False,
                    "max_retries": 3,
                },
            }
            input_json = json.dumps(input_data)

            result = await resolve_config_variables_activity(input_json)

            expected = {
                "database": {
                    "host": "prod-db",
                    "port": "5432",
                    "config": {
                        "timeout": 30,
                        "ssl": True,
                        "connection_string": "postgresql://prod-db:5432/mydb",
                    },
                },
                "api": {
                    "key": "secret123",
                    "endpoints": [
                        "https://prod-db/api/v1",
                        "https://prod-db/api/v2",
                    ],
                },
                "static_config": {
                    "debug": False,
                    "max_retries": 3,
                },
            }
            expected_json = json.dumps(expected)
            assert result == expected_json
        finally:
            del os.environ["DB_HOST"]
            del os.environ["DB_PORT"]
            del os.environ["API_KEY"]

    @pytest.mark.asyncio
    async def test_resolve_empty_structures(self) -> None:
        """Test resolving environment variables in empty structures."""
        test_cases = [
            {},
            [],
            "",
        ]

        for test_input in test_cases:
            input_json = json.dumps(test_input)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps(test_input)
            assert result == expected_json

    @pytest.mark.asyncio
    async def test_resolve_dollar_var_pattern(self) -> None:
        """Test resolving both ${VAR} and $VAR patterns."""
        os.environ["SIMPLE_VAR"] = "simple_value"

        try:
            # $VAR works when followed by space or end of string
            input_str = "prefix $SIMPLE_VAR end"
            input_json = json.dumps(input_str)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps("prefix simple_value end")
            assert result == expected_json

            # For variables followed by underscore, need braces
            input_str2 = "prefix_${SIMPLE_VAR}_suffix"
            input_json2 = json.dumps(input_str2)
            result2 = await resolve_config_variables_activity(input_json2)
            expected_json2 = json.dumps("prefix_simple_value_suffix")
            assert result2 == expected_json2
        finally:
            del os.environ["SIMPLE_VAR"]

    @pytest.mark.asyncio
    async def test_resolve_mixed_var_patterns(self) -> None:
        """Test resolving mixed ${VAR} and $VAR patterns in the same string."""
        os.environ["VAR1"] = "value1"
        os.environ["VAR2"] = "value2"

        try:
            # Use ${VAR} for unambiguous variable names
            input_str = "${VAR1}_and_${VAR2}_mixed"
            input_json = json.dumps(input_str)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps("value1_and_value2_mixed")
            assert result == expected_json

            # $VAR works when followed by space
            input_str2 = "$VAR1 and ${VAR2} mixed"
            input_json2 = json.dumps(input_str2)
            result2 = await resolve_config_variables_activity(input_json2)
            expected_json2 = json.dumps("value1 and value2 mixed")
            assert result2 == expected_json2
        finally:
            del os.environ["VAR1"]
            del os.environ["VAR2"]

    @pytest.mark.asyncio
    async def test_resolve_var_with_underscores_and_numbers(self) -> None:
        """Test resolving variable names containing underscores and numbers."""
        os.environ["VAR_WITH_UNDERSCORE"] = "underscore_value"
        os.environ["VAR123"] = "numeric_value"
        os.environ["_LEADING_UNDERSCORE"] = "leading_value"

        try:
            input_dict = {
                "underscore": "${VAR_WITH_UNDERSCORE}",
                "numeric": "${VAR123}",
                "leading": "${_LEADING_UNDERSCORE}",
            }
            input_json = json.dumps(input_dict)
            result = await resolve_config_variables_activity(input_json)

            expected = {
                "underscore": "underscore_value",
                "numeric": "numeric_value",
                "leading": "leading_value",
            }
            expected_json = json.dumps(expected)
            assert result == expected_json
        finally:
            del os.environ["VAR_WITH_UNDERSCORE"]
            del os.environ["VAR123"]
            del os.environ["_LEADING_UNDERSCORE"]

    @pytest.mark.asyncio
    async def test_resolve_var_edge_cases(self) -> None:
        """Test edge cases in variable resolution."""
        os.environ["EDGE_VAR"] = "edge_value"

        try:
            # Test various edge case patterns
            test_cases = [
                "${",  # Incomplete pattern
                "${}",  # Empty braces
                "${EDGE_VAR",  # Missing closing brace
                "EDGE_VAR}",  # Missing opening pattern
                "${123VAR}",  # Invalid variable name (starts with number)
                "${VAR-WITH-DASH}",  # Invalid character in variable name
            ]

            for test_input in test_cases:
                input_json = json.dumps(test_input)
                result = await resolve_config_variables_activity(input_json)
                # These should either remain unchanged or be handled by os.expandvars
                assert isinstance(json.loads(result), str)

            # Test valid pattern
            valid_input = "prefix_${EDGE_VAR}_suffix"
            valid_json = json.dumps(valid_input)
            result = await resolve_config_variables_activity(valid_json)
            expected_json = json.dumps("prefix_edge_value_suffix")
            assert result == expected_json

        finally:
            del os.environ["EDGE_VAR"]

    @pytest.mark.asyncio
    async def test_resolve_deeply_nested_structure(self) -> None:
        """Test resolving environment variables in deeply nested structures."""
        os.environ["DEEP_VAR"] = "deep_value"

        try:
            input_data = {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": {
                                    "value": "${DEEP_VAR}",
                                    "list": [
                                        {
                                            "nested_value": "prefix_${DEEP_VAR}_suffix",
                                        },
                                    ],
                                },
                            },
                        },
                    },
                },
            }
            input_json = json.dumps(input_data)

            result = await resolve_config_variables_activity(input_json)

            expected = {
                "level1": {
                    "level2": {
                        "level3": {
                            "level4": {
                                "level5": {
                                    "value": "deep_value",
                                    "list": [
                                        {
                                            "nested_value": "prefix_deep_value_suffix",
                                        },
                                    ],
                                },
                            },
                        },
                    },
                },
            }
            expected_json = json.dumps(expected)
            assert result == expected_json
        finally:
            del os.environ["DEEP_VAR"]

    @pytest.mark.asyncio
    async def test_resolve_no_expansion_needed(self) -> None:
        """Test structures that require no environment variable expansion."""
        test_cases = [
            "simple string without variables",
            {"key": "value", "number": 42},
            ["item1", "item2", {"nested": "value"}],
            "",
            0,
            False,
            None,
        ]

        for test_input in test_cases:
            input_json = json.dumps(test_input)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps(test_input)
            assert result == expected_json

    @pytest.mark.asyncio
    async def test_resolve_partial_expansion_with_missing_var(self) -> None:
        """Test partial expansion when some variables are missing."""
        os.environ["AVAILABLE_VAR"] = "available"

        try:
            input_str = "${AVAILABLE_VAR} and ${MISSING_VAR}"
            input_json = json.dumps(input_str)

            with pytest.raises(ValueError, match="Required environment variables not set: MISSING_VAR"):
                await resolve_config_variables_activity(input_json)
        finally:
            del os.environ["AVAILABLE_VAR"]

    @pytest.mark.asyncio
    async def test_resolve_with_special_characters_in_values(self) -> None:
        """Test resolving variables that contain special characters."""
        os.environ["SPECIAL_VAR"] = "value with spaces & symbols!@#$%^&*()[]{}|\\:;\"'<>?,./"

        try:
            input_str = "Before ${SPECIAL_VAR} After"
            input_json = json.dumps(input_str)
            result = await resolve_config_variables_activity(input_json)
            expected_json = json.dumps("Before value with spaces & symbols!@#$%^&*()[]{}|\\:;\"'<>?,./ After")
            assert result == expected_json
        finally:
            del os.environ["SPECIAL_VAR"]

    @pytest.mark.asyncio
    async def test_resolve_invalid_json_input(self) -> None:
        """Test that invalid JSON input raises appropriate error."""
        invalid_json = "{ invalid json structure"

        with pytest.raises(ValueError, match="Invalid JSON configuration"):
            await resolve_config_variables_activity(invalid_json)
