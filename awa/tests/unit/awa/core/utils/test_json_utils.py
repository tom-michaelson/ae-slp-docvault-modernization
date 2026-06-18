import json

import pytest

from awa.core.utils.json_utils import JsonUtils


class TestJsonUtils:
    """Test cases for JsonUtils class."""

    def test_parse_json_valid_json_string(self) -> None:
        """Test parsing a valid JSON string."""
        json_str = '{"key": "value", "number": 42, "array": [1, 2, 3]}'
        expected = {"key": "value", "number": 42, "array": [1, 2, 3]}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_empty_object(self) -> None:
        """Test parsing an empty JSON object."""
        json_str = "{}"
        expected = {}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_complex_nested_structure(self) -> None:
        """Test parsing a complex nested JSON structure."""
        json_str = '{"user": {"name": "John", "age": 30}, "items": ["apple", "banana"], "active": true}'
        expected = {
            "user": {"name": "John", "age": 30},
            "items": ["apple", "banana"],
            "active": True,
        }

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_with_single_quotes_fallback(self) -> None:
        """Test parsing a string with single quotes using ast.literal_eval fallback."""
        json_str = "{'key': 'value', 'number': 42, 'array': [1, 2, 3]}"
        expected = {"key": "value", "number": 42, "array": [1, 2, 3]}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_mixed_quotes_fallback(self) -> None:
        """Test parsing a string with mixed quotes using ast.literal_eval fallback."""
        json_str = "{'outer': \"inner\", 'number': 123}"
        expected = {"outer": "inner", "number": 123}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_single_quotes_empty_object(self) -> None:
        """Test parsing an empty object with single quotes."""
        json_str = "{}"
        expected = {}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_invalid_json_no_single_quotes_raises_error(self) -> None:
        """Test that invalid JSON without single quotes raises JSONDecodeError."""
        json_str = '{"key": "value", "invalid": }'

        with pytest.raises(json.JSONDecodeError):
            JsonUtils.parse_json(json_str)

    def test_parse_json_invalid_json_with_single_quotes_raises_error(self) -> None:
        """Test that invalid JSON with single quotes that can't be parsed raises an error."""
        json_str = "{'key': 'value', 'invalid': }"

        with pytest.raises((ValueError, SyntaxError)):
            JsonUtils.parse_json(json_str)

    def test_parse_json_malformed_with_single_quotes(self) -> None:
        """Test that malformed strings with single quotes raise appropriate errors."""
        json_str = "{'key': 'value', 'unclosed': 'string"

        with pytest.raises((ValueError, SyntaxError)):
            JsonUtils.parse_json(json_str)

    def test_parse_json_non_dict_structure_with_single_quotes(self) -> None:
        """Test parsing non-dict structures with single quotes."""
        # This should work as ast.literal_eval can handle lists too
        json_str = "['item1', 'item2', 3]"
        expected = ["item1", "item2", 3]

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_boolean_and_none_values(self) -> None:
        """Test parsing JSON with boolean and None values."""
        json_str = '{"active": true, "inactive": false, "empty": null}'
        expected = {"active": True, "inactive": False, "empty": None}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_single_quotes_boolean_and_none(self) -> None:
        """Test parsing single quote string with boolean and None values."""
        json_str = "{'active': True, 'inactive': False, 'empty': None}"
        expected = {"active": True, "inactive": False, "empty": None}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_numeric_values(self) -> None:
        """Test parsing JSON with various numeric values."""
        json_str = '{"int": 42, "float": 3.14, "negative": -10, "zero": 0}'
        expected = {"int": 42, "float": 3.14, "negative": -10, "zero": 0}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_empty_string_raises_error(self) -> None:
        """Test that empty string raises JSONDecodeError."""
        json_str = ""

        with pytest.raises(json.JSONDecodeError):
            JsonUtils.parse_json(json_str)

    def test_parse_json_whitespace_only_raises_error(self) -> None:
        """Test that whitespace-only string raises JSONDecodeError."""
        json_str = "   \n\t  "

        with pytest.raises(json.JSONDecodeError):
            JsonUtils.parse_json(json_str)

    def test_parse_json_unicode_characters(self) -> None:
        """Test parsing JSON with unicode characters."""
        json_str = '{"name": "José", "emoji": "🎉", "chinese": "你好"}'
        expected = {"name": "José", "emoji": "🎉", "chinese": "你好"}

        result = JsonUtils.parse_json(json_str)

        assert result == expected

    def test_parse_json_escape_sequences(self) -> None:
        """Test parsing JSON with escape sequences."""
        json_str = '{"newline": "line1\\nline2", "tab": "col1\\tcol2", "quote": "He said \\"hello\\""}'
        expected = {"newline": "line1\nline2", "tab": "col1\tcol2", "quote": 'He said "hello"'}

        result = JsonUtils.parse_json(json_str)

        assert result == expected
