"""Test cases for CacheUtils class."""

import hashlib
import json

import pytest
from pydantic import BaseModel

from awa.core.utils.cache_utils import CacheUtils

# Constants
SHORT_HASH_LENGTH = 5


class SampleModel(BaseModel):
    """Sample Pydantic model for testing."""

    name: str
    value: int


class SampleClass:
    """Sample regular class for testing."""

    def __init__(self, name: str, value: int) -> None:
        self.name = name
        self.value = value


class TestCacheUtils:
    """Test cases for CacheUtils class."""

    def test_hash_string_normal(self) -> None:
        """Test hashing a normal string."""
        test_string = "test_string"
        expected = hashlib.sha256(test_string.encode()).hexdigest()
        result = CacheUtils._hash_string(test_string)
        assert result == expected

    def test_hash_string_short(self) -> None:
        """Test hashing a string with short option."""
        test_string = "test_string"
        expected = hashlib.sha256(test_string.encode()).hexdigest()[:SHORT_HASH_LENGTH]
        result = CacheUtils._hash_string(test_string, short=True)
        assert result == expected
        assert len(result) == SHORT_HASH_LENGTH

    def test_hash_string_empty(self) -> None:
        """Test hashing an empty string."""
        result = CacheUtils._hash_string("")
        assert result == ""

    def test_hash_string_none(self) -> None:
        """Test hashing None string."""
        result = CacheUtils._hash_string(None)  # type: ignore[arg-type]
        assert result == ""

    def test_hash_dict_normal(self) -> None:
        """Test hashing a normal dictionary."""
        test_dict = {"key": "value", "number": 42}
        json_string = json.dumps(test_dict, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()
        result = CacheUtils._hash_dict(test_dict)
        assert result == expected

    def test_hash_dict_short(self) -> None:
        """Test hashing a dictionary with short option."""
        test_dict = {"key": "value", "number": 42}
        json_string = json.dumps(test_dict, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()[:SHORT_HASH_LENGTH]
        result = CacheUtils._hash_dict(test_dict, short=True)
        assert result == expected
        assert len(result) == SHORT_HASH_LENGTH

    def test_hash_dict_order_independence(self) -> None:
        """Test that dictionary order doesn't affect hash."""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"b": 2, "a": 1}
        result1 = CacheUtils._hash_dict(dict1)
        result2 = CacheUtils._hash_dict(dict2)
        assert result1 == result2

    def test_hash_class_normal(self) -> None:
        """Test hashing a regular class instance."""
        obj = SampleClass("test", 42)
        expected_dict = {"name": "test", "value": 42}
        json_string = json.dumps(expected_dict, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()
        result = CacheUtils._hash_class(obj)
        assert result == expected

    def test_hash_class_short(self) -> None:
        """Test hashing a class instance with short option."""
        obj = SampleClass("test", 42)
        expected_dict = {"name": "test", "value": 42}
        json_string = json.dumps(expected_dict, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()[:SHORT_HASH_LENGTH]
        result = CacheUtils._hash_class(obj, short=True)
        assert result == expected
        assert len(result) == SHORT_HASH_LENGTH

    def test_hash_pydantic_normal(self) -> None:
        """Test hashing a Pydantic model."""
        model = SampleModel(name="test", value=42)
        json_string = model.model_dump_json()
        expected = hashlib.sha256(json_string.encode()).hexdigest()
        result = CacheUtils._hash_pydantic(model)
        assert result == expected

    def test_hash_pydantic_short(self) -> None:
        """Test hashing a Pydantic model with short option."""
        model = SampleModel(name="test", value=42)
        json_string = model.model_dump_json()
        expected = hashlib.sha256(json_string.encode()).hexdigest()[:SHORT_HASH_LENGTH]
        result = CacheUtils._hash_pydantic(model, short=True)
        assert result == expected
        assert len(result) == SHORT_HASH_LENGTH

    def test_get_item_json_string_pydantic(self) -> None:
        """Test getting JSON string for Pydantic model."""
        model = SampleModel(name="test", value=42)
        expected = model.model_dump_json()
        result = CacheUtils._get_item_json_string(model)
        assert result == expected

    def test_get_item_json_string_dict(self) -> None:
        """Test getting JSON string for dictionary."""
        test_dict = {"b": 2, "a": 1}
        expected = json.dumps(test_dict, sort_keys=True)
        result = CacheUtils._get_item_json_string(test_dict)
        assert result == expected

    def test_get_item_json_string_list(self) -> None:
        """Test getting JSON string for list."""
        test_list = [1, 2, 3]
        expected = json.dumps(test_list, sort_keys=True)
        result = CacheUtils._get_item_json_string(test_list)
        assert result == expected

    def test_get_item_json_string_primitive(self) -> None:
        """Test getting JSON string for primitive type."""
        test_string = "test"
        expected = json.dumps(test_string, sort_keys=True)
        result = CacheUtils._get_item_json_string(test_string)
        assert result == expected

    def test_hash_list_normal(self) -> None:
        """Test hashing a normal list."""
        test_list = ["item1", "item2", {"key": "value"}]
        element_json_strings = [CacheUtils._get_item_json_string(i) for i in test_list]
        element_json_strings.sort()
        json_string = json.dumps(element_json_strings, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()
        result = CacheUtils._hash_list(test_list)
        assert result == expected

    def test_hash_list_short(self) -> None:
        """Test hashing a list with short option."""
        test_list = ["item1", "item2"]
        element_json_strings = [CacheUtils._get_item_json_string(i) for i in test_list]
        element_json_strings.sort()
        json_string = json.dumps(element_json_strings, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()[:SHORT_HASH_LENGTH]
        result = CacheUtils._hash_list(test_list, short=True)
        assert result == expected
        assert len(result) == SHORT_HASH_LENGTH

    def test_hash_list_order_independence(self) -> None:
        """Test that list order doesn't affect hash."""
        list1 = ["a", "b", "c"]
        list2 = ["c", "a", "b"]
        result1 = CacheUtils._hash_list(list1)
        result2 = CacheUtils._hash_list(list2)
        assert result1 == result2

    def test_hash_list_with_pydantic_models(self) -> None:
        """Test hashing a list containing Pydantic models."""
        model1 = SampleModel(name="test1", value=1)
        model2 = SampleModel(name="test2", value=2)
        test_list = [model1, model2]

        element_json_strings = [CacheUtils._get_item_json_string(i) for i in test_list]
        element_json_strings.sort()
        json_string = json.dumps(element_json_strings, sort_keys=True)
        expected = hashlib.sha256(json_string.encode()).hexdigest()

        result = CacheUtils._hash_list(test_list)
        assert result == expected

    def test_hash_main_function_string(self) -> None:
        """Test main hash function with string input."""
        test_string = "test"
        expected = CacheUtils._hash_string(test_string)
        result = CacheUtils.hash(test_string)
        assert result == expected

    def test_hash_main_function_dict(self) -> None:
        """Test main hash function with dict input."""
        test_dict = {"key": "value"}
        expected = CacheUtils._hash_dict(test_dict)
        result = CacheUtils.hash(test_dict)
        assert result == expected

    def test_hash_main_function_list(self) -> None:
        """Test main hash function with list input."""
        test_list = ["item1", "item2"]
        expected = CacheUtils._hash_list(test_list)
        result = CacheUtils.hash(test_list)
        assert result == expected

    def test_hash_main_function_pydantic(self) -> None:
        """Test main hash function with Pydantic model input."""
        model = SampleModel(name="test", value=42)
        expected = CacheUtils._hash_pydantic(model)
        result = CacheUtils.hash(model)
        assert result == expected

    def test_hash_main_function_class(self) -> None:
        """Test main hash function with regular class input."""
        obj = SampleClass("test", 42)
        expected = CacheUtils._hash_class(obj)
        result = CacheUtils.hash(obj)
        assert result == expected

    def test_hash_main_function_short(self) -> None:
        """Test main hash function with short option."""
        test_string = "test"
        expected = CacheUtils._hash_string(test_string, short=True)
        result = CacheUtils.hash(test_string, short=True)
        assert result == expected
        assert len(result) == SHORT_HASH_LENGTH

    def test_hash_main_function_empty_value(self) -> None:
        """Test main hash function with empty/falsy input."""
        result = CacheUtils.hash("")
        assert result == ""

        result = CacheUtils.hash(None)
        assert result == ""

        result = CacheUtils.hash([])
        assert result == ""

    def test_hash_main_function_unsupported_type(self) -> None:
        """Test main hash function with unsupported type."""

        # Create an object that can't be JSON serialized and isn't a supported type
        class UnsupportedType:
            def __init__(self) -> None:
                self.circular_ref = self  # Create circular reference to make JSON serialization fail

        unsupported = UnsupportedType()

        # This should fail during JSON serialization in _hash_class method
        with pytest.raises((ValueError, TypeError)):
            CacheUtils.hash(unsupported)
