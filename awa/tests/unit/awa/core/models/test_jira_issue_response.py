import pytest
from pydantic import ValidationError

from awa.sdk.models.jira_issue_response import JiraIssueResponse


class TestJiraIssueResponse:
    """Test cases for JiraIssueResponse Pydantic model."""

    def test_model_initialization_with_no_fields(self) -> None:
        """Test that the model can be initialized with no fields (all optional)."""
        # Arrange & Act
        response = JiraIssueResponse()

        # Assert
        assert response.key is None
        assert response.summary is None
        assert response.description is None
        assert response.issue_type is None

    def test_model_initialization_with_all_fields(self) -> None:
        """Test that the model can be initialized with all fields."""
        # Arrange
        test_data = {
            "key": "TEST-456",
            "summary": "Test issue summary",
            "description": "Test issue description",
            "issue_type": "Bug",
        }

        # Act
        response = JiraIssueResponse(**test_data)

        # Assert
        assert response.key == "TEST-456"
        assert response.summary == "Test issue summary"
        assert response.description == "Test issue description"
        assert response.issue_type == "Bug"

    def test_model_initialization_with_partial_fields(self) -> None:
        """Test that the model can be initialized with partial fields."""
        # Arrange & Act
        response = JiraIssueResponse(key="TEST-123", summary="Test summary")

        # Assert
        assert response.key == "TEST-123"
        assert response.summary == "Test summary"
        assert response.description is None
        assert response.issue_type is None

    def test_model_field_validation_key_type(self) -> None:
        """Test that key field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueResponse(key=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("key", "str")

    def test_model_field_validation_summary_type(self) -> None:
        """Test that summary field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueResponse(summary=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("summary", "str")

    def test_model_field_validation_description_type(self) -> None:
        """Test that description field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueResponse(description=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("description", "str")

    def test_model_field_validation_issue_type_type(self) -> None:
        """Test that issue_type field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueResponse(issue_type=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("issue_type", "str")

    def test_model_default_values(self) -> None:
        """Test that default values are correctly set."""
        # Arrange & Act
        response = JiraIssueResponse()

        # Assert
        assert response.key is None
        assert response.summary is None
        assert response.description is None
        assert response.issue_type is None

    def test_model_field_validation_multiple_invalid_types(self) -> None:
        """Test that multiple field validation errors are caught."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueResponse(key=123, summary=456, description=789, issue_type=999)

        # Verify all errors are reported
        errors = exc_info.value.errors()
        assert len(errors) == 8

        # Check that all fields have type errors
        error_fields = {error["loc"][0] for error in errors}
        assert error_fields == {"key", "summary", "description", "issue_type"}

        # Check that all errors are string_type errors
        for error in errors:
            assert error["type"] == "string_type" or error["type"] == "none_required"

    def test_model_serialization_model_dump(self) -> None:
        """Test that the model can be serialized using model_dump()."""
        # Arrange
        test_data = {
            "key": "TEST-456",
            "summary": "Test summary",
            "description": "Test description",
            "issue_type": "Bug",
        }
        response = JiraIssueResponse(**test_data)

        # Act
        serialized = response.model_dump()

        # Assert
        assert isinstance(serialized, dict)
        assert serialized == test_data

    def test_model_serialization_model_dump_with_none_values(self) -> None:
        """Test that model_dump() includes None values by default."""
        # Arrange
        response = JiraIssueResponse(key="TEST-123")

        # Act
        serialized = response.model_dump()

        # Assert
        expected = {"key": "TEST-123", "summary": None, "description": None, "issue_type": None}
        assert serialized == expected

    def test_model_serialization_model_dump_exclude_none(self) -> None:
        """Test that model_dump() can exclude None values."""
        # Arrange
        response = JiraIssueResponse(key="TEST-123", summary="Test")

        # Act
        serialized = response.model_dump(exclude_none=True)

        # Assert
        expected = {"key": "TEST-123", "summary": "Test"}
        assert serialized == expected

    def test_model_serialization_model_dump_empty_model(self) -> None:
        """Test that model_dump() works with empty model."""
        # Arrange
        response = JiraIssueResponse()

        # Act
        serialized = response.model_dump()

        # Assert
        expected = {"key": None, "summary": None, "description": None, "issue_type": None}
        assert serialized == expected

    def test_model_serialization_model_dump_exclude_none_empty_model(self) -> None:
        """Test that model_dump(exclude_none=True) works with empty model."""
        # Arrange
        response = JiraIssueResponse()

        # Act
        serialized = response.model_dump(exclude_none=True)

        # Assert
        assert serialized == {}

    def test_model_deserialization_model_validate(self) -> None:
        """Test that the model can be deserialized using model_validate()."""
        # Arrange
        test_data = {
            "key": "TEST-456",
            "summary": "Test summary",
            "description": "Test description",
            "issue_type": "Bug",
        }

        # Act
        response = JiraIssueResponse.model_validate(test_data)

        # Assert
        assert response.key == "TEST-456"
        assert response.summary == "Test summary"
        assert response.description == "Test description"
        assert response.issue_type == "Bug"

    def test_model_deserialization_model_validate_empty_dict(self) -> None:
        """Test that model_validate() works with empty dictionary."""
        # Arrange
        test_data = {}

        # Act
        response = JiraIssueResponse.model_validate(test_data)

        # Assert
        assert response.key is None
        assert response.summary is None
        assert response.description is None
        assert response.issue_type is None

    def test_model_deserialization_model_validate_partial_data(self) -> None:
        """Test that model_validate() works with partial data."""
        # Arrange
        test_data = {"key": "TEST-123", "issue_type": "Story"}

        # Act
        response = JiraIssueResponse.model_validate(test_data)

        # Assert
        assert response.key == "TEST-123"
        assert response.summary is None
        assert response.description is None
        assert response.issue_type == "Story"

    def test_model_deserialization_model_validate_invalid_data(self) -> None:
        """Test that model_validate() raises ValidationError for invalid data."""
        # Arrange
        invalid_data = {"key": 123}  # Invalid type

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueResponse.model_validate(invalid_data)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("key", "str")

    def test_model_json_serialization(self) -> None:
        """Test that the model can be serialized to JSON."""
        # Arrange
        response = JiraIssueResponse(key="TEST-123", summary="Test summary", issue_type="Bug")

        # Act
        json_str = response.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "TEST-123" in json_str
        assert "Test summary" in json_str
        assert "Bug" in json_str

    def test_model_json_serialization_empty_model(self) -> None:
        """Test that empty model can be serialized to JSON."""
        # Arrange
        response = JiraIssueResponse()

        # Act
        json_str = response.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "null" in json_str  # JSON representation of None

    def test_model_json_serialization_exclude_none(self) -> None:
        """Test that JSON serialization can exclude None values."""
        # Arrange
        response = JiraIssueResponse(key="TEST-123")

        # Act
        json_str = response.model_dump_json(exclude_none=True)

        # Assert
        assert isinstance(json_str, str)
        assert "TEST-123" in json_str
        assert "null" not in json_str

    def test_model_equality(self) -> None:
        """Test that two models with same data are equal."""
        # Arrange
        response1 = JiraIssueResponse(key="TEST-123", summary="Test summary", issue_type="Bug")
        response2 = JiraIssueResponse(key="TEST-123", summary="Test summary", issue_type="Bug")

        # Act & Assert
        assert response1 == response2

    def test_model_equality_empty_models(self) -> None:
        """Test that two empty models are equal."""
        # Arrange
        response1 = JiraIssueResponse()
        response2 = JiraIssueResponse()

        # Act & Assert
        assert response1 == response2

    def test_model_inequality(self) -> None:
        """Test that two models with different data are not equal."""
        # Arrange
        response1 = JiraIssueResponse(key="TEST-123")
        response2 = JiraIssueResponse(key="TEST-456")

        # Act & Assert
        assert response1 != response2

    def test_model_inequality_none_vs_value(self) -> None:
        """Test that model with None value is not equal to model with actual value."""
        # Arrange
        response1 = JiraIssueResponse()
        response2 = JiraIssueResponse(key="TEST-123")

        # Act & Assert
        assert response1 != response2

    def test_model_hash(self) -> None:
        """Test that the model is not hashable by default."""
        # Arrange
        response = JiraIssueResponse(key="TEST-123")

        # Act & Assert
        # Pydantic models are not hashable by default
        with pytest.raises(TypeError, match="unhashable type"):
            hash(response)

    def test_model_hash_empty_models(self) -> None:
        """Test that empty models are not hashable."""
        # Arrange
        response1 = JiraIssueResponse()
        response2 = JiraIssueResponse()

        # Act & Assert
        # Pydantic models are not hashable by default
        with pytest.raises(TypeError, match="unhashable type"):
            hash(response1)
        with pytest.raises(TypeError, match="unhashable type"):
            hash(response2)

    def test_model_repr(self) -> None:
        """Test that the model has a useful string representation."""
        # Arrange
        response = JiraIssueResponse(key="TEST-123", summary="Test summary")

        # Act
        repr_str = repr(response)

        # Assert
        assert "JiraIssueResponse" in repr_str
        assert "TEST-123" in repr_str
        assert "Test summary" in repr_str

    def test_model_repr_empty_model(self) -> None:
        """Test that empty model has a useful string representation."""
        # Arrange
        response = JiraIssueResponse()

        # Act
        repr_str = repr(response)

        # Assert
        assert "JiraIssueResponse" in repr_str

    def test_model_fields_are_accessible(self) -> None:
        """Test that all model fields are accessible as attributes."""
        # Arrange
        response = JiraIssueResponse()

        # Act & Assert
        # All fields should be accessible
        assert hasattr(response, "key")
        assert hasattr(response, "summary")
        assert hasattr(response, "description")
        assert hasattr(response, "issue_type")

    def test_model_field_assignment(self) -> None:
        """Test that model fields can be assigned new values."""
        # Arrange
        response = JiraIssueResponse()

        # Act
        response.key = "NEW-123"
        response.summary = "New summary"
        response.description = "New description"
        response.issue_type = "Story"

        # Assert
        assert response.key == "NEW-123"
        assert response.summary == "New summary"
        assert response.description == "New description"
        assert response.issue_type == "Story"

    def test_model_field_assignment_validation(self) -> None:
        """Test that field assignment allows any value (validation happens at model creation)."""
        # Arrange
        response = JiraIssueResponse()

        # Act
        # Pydantic allows direct field assignment without validation
        response.key = 123  # This is allowed
        response.summary = 456  # This is allowed
        response.description = 789  # This is allowed
        response.issue_type = 999  # This is allowed

        # Assert
        assert response.key == 123
        assert response.summary == 456
        assert response.description == 789
        assert response.issue_type == 999

    def test_model_field_assignment_none_values(self) -> None:
        """Test that fields can be assigned None values."""
        # Arrange
        response = JiraIssueResponse(
            key="TEST-123",
            summary="Test summary",
            description="Test description",
            issue_type="Bug",
        )

        # Act
        response.key = None
        response.summary = None
        response.description = None
        response.issue_type = None

        # Assert
        assert response.key is None
        assert response.summary is None
        assert response.description is None
        assert response.issue_type is None

    def test_model_with_complex_data(self) -> None:
        """Test model with complex real-world data."""
        # Arrange
        complex_data = {
            "key": "PROJ-2023-1234",
            "summary": "Critical bug in user authentication system causing login failures",
            "description": (
                "Users are unable to log in due to session timeout issues.\n\n"
                "Root cause analysis:\n- Session cookies are being invalidated prematurely\n"
                "- Authentication service is not properly handling token refresh\n"
                "- Database connection pooling issues during peak hours\n\n"
                "Impact:\n- Affecting 30% of login attempts\n"
                "- User satisfaction dropping\n- Revenue impact due to cart abandonment\n\n"
                "Resolution:\n- Updated session management configuration\n"
                "- Fixed token refresh logic\n- Optimized database connection pool"
            ),
            "issue_type": "Bug",
        }

        # Act
        response = JiraIssueResponse(**complex_data)

        # Assert
        assert response.key == "PROJ-2023-1234"
        assert "Critical bug" in response.summary
        assert "authentication system" in response.summary
        assert "session timeout" in response.description
        assert "Root cause analysis" in response.description
        assert "Resolution" in response.description
        assert response.issue_type == "Bug"

    def test_model_with_empty_strings(self) -> None:
        """Test model with empty string values."""
        # Arrange
        response = JiraIssueResponse(key="", summary="", description="", issue_type="")

        # Act & Assert
        assert response.key == ""
        assert response.summary == ""
        assert response.description == ""
        assert response.issue_type == ""

    def test_model_with_whitespace_strings(self) -> None:
        """Test model with whitespace-only string values."""
        # Arrange
        response = JiraIssueResponse(key="   ", summary="\t\n", description="  \t  ", issue_type="\n\n")

        # Act & Assert
        assert response.key == "   "
        assert response.summary == "\t\n"
        assert response.description == "  \t  "
        assert response.issue_type == "\n\n"

    def test_model_with_unicode_strings(self) -> None:
        """Test model with unicode string values."""
        # Arrange
        response = JiraIssueResponse(
            key="TEST-123-🚀",
            summary="Test with émojis and spéciał characters",
            description="Description with 中文 and العربية text",
            issue_type="Büg",
        )

        # Act & Assert
        assert response.key == "TEST-123-🚀"
        assert response.summary == "Test with émojis and spéciał characters"
        assert response.description == "Description with 中文 and العربية text"
        assert response.issue_type == "Büg"

    def test_model_copy(self) -> None:
        """Test that the model can be copied."""
        # Arrange
        original = JiraIssueResponse(key="TEST-123", summary="Original summary", issue_type="Bug")

        # Act
        copied = original.model_copy()

        # Assert
        assert copied == original
        assert copied is not original  # Different objects
        assert copied.key == original.key
        assert copied.summary == original.summary
        assert copied.issue_type == original.issue_type

    def test_model_copy_with_updates(self) -> None:
        """Test that the model can be copied with updates."""
        # Arrange
        original = JiraIssueResponse(key="TEST-123", summary="Original summary", issue_type="Bug")

        # Act
        updated = original.model_copy(update={"summary": "Updated summary"})

        # Assert
        assert updated.key == original.key
        assert updated.summary == "Updated summary"
        assert updated.issue_type == original.issue_type
        assert original.summary == "Original summary"  # Original unchanged
