import pytest
from pydantic import ValidationError

from awa.sdk.models.jira_issue_request import JiraIssueRequest


class TestJiraIssueRequest:
    """Test cases for JiraIssueRequest Pydantic model."""

    def test_model_initialization_with_required_fields(self) -> None:
        """Test that the model can be initialized with only required fields."""
        # Arrange & Act
        request = JiraIssueRequest(project_id="TEST-123")

        # Assert
        assert request.project_id == "TEST-123"
        assert request.key is None
        assert request.summary is None
        assert request.description is None
        assert request.issue_type is None
        assert request.parent is None
        assert request.tags is None
        assert request.comments is None

    def test_model_initialization_with_all_fields(self) -> None:
        """Test that the model can be initialized with all fields."""
        # Arrange
        test_data = {
            "project_id": "TEST-123",
            "key": "TEST-456",
            "summary": "Test issue summary",
            "description": "Test issue description",
            "issue_type": "Bug",
            "parent": "TEST-100",
            "tags": ["urgent", "backend"],
            "comments": ["Initial comment", "Follow-up comment"],
        }

        # Act
        request = JiraIssueRequest(**test_data)

        # Assert
        assert request.project_id == "TEST-123"
        assert request.key == "TEST-456"
        assert request.summary == "Test issue summary"
        assert request.description == "Test issue description"
        assert request.issue_type == "Bug"
        assert request.parent == "TEST-100"
        assert request.tags == ["urgent", "backend"]
        assert request.comments == ["Initial comment", "Follow-up comment"]

    def test_model_initialization_with_partial_fields(self) -> None:
        """Test that the model can be initialized with partial fields."""
        # Arrange & Act
        request = JiraIssueRequest(project_id="TEST-123", summary="Test summary", issue_type="Story")

        # Assert
        assert request.project_id == "TEST-123"
        assert request.key is None
        assert request.summary == "Test summary"
        assert request.description is None
        assert request.issue_type == "Story"
        assert request.parent is None
        assert request.tags is None
        assert request.comments is None

    def test_model_field_validation_project_id_required(self) -> None:
        """Test that project_id field is required."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest()

        # Verify the error is about the missing project_id field
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("project_id",)

    def test_model_field_validation_project_id_type(self) -> None:
        """Test that project_id field must be a string."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("project_id",)

    def test_model_field_validation_key_type(self) -> None:
        """Test that key field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", key=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("key", "str")

    def test_model_field_validation_summary_type(self) -> None:
        """Test that summary field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", summary=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("summary", "str")

    def test_model_field_validation_description_type(self) -> None:
        """Test that description field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", description=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("description", "str")

    def test_model_field_validation_issue_type_type(self) -> None:
        """Test that issue_type field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", issue_type=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("issue_type", "str")

    def test_model_field_validation_parent_type(self) -> None:
        """Test that parent field must be a string or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", parent=123)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("parent", "str")

    def test_model_field_validation_tags_type(self) -> None:
        """Test that tags field must be a list of strings or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", tags="invalid")

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "list_type"
        assert errors[0]["loc"] == ("tags", "list[str]")

    def test_model_field_validation_tags_element_type(self) -> None:
        """Test that tags field elements must be strings."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", tags=["valid", 123])

        # Verify the error is about the wrong type in list element
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("tags", "list[str]", 1)

    def test_model_field_validation_comments_type(self) -> None:
        """Test that comments field must be a list of strings or None."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", comments="invalid")

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "list_type"
        assert errors[0]["loc"] == ("comments", "list[str]")

    def test_model_field_validation_comments_element_type(self) -> None:
        """Test that comments field elements must be strings."""
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest(project_id="TEST-123", comments=["valid", 123])

        # Verify the error is about the wrong type in list element
        errors = exc_info.value.errors()
        assert len(errors) == 2
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("comments", "list[str]", 1)

    def test_model_default_values(self) -> None:
        """Test that default values are correctly set."""
        # Arrange & Act
        request = JiraIssueRequest(project_id="TEST-123")

        # Assert
        assert request.key is None
        assert request.summary is None
        assert request.description is None
        assert request.issue_type is None
        assert request.parent is None
        assert request.tags is None
        assert request.comments is None

    def test_model_empty_lists(self) -> None:
        """Test that empty lists are accepted for tags and comments."""
        # Arrange & Act
        request = JiraIssueRequest(project_id="TEST-123", tags=[], comments=[])

        # Assert
        assert request.tags == []
        assert request.comments == []

    def test_model_serialization_model_dump(self) -> None:
        """Test that the model can be serialized using model_dump()."""
        # Arrange
        test_data = {
            "project_id": "TEST-123",
            "key": "TEST-456",
            "summary": "Test summary",
            "description": "Test description",
            "issue_type": "Bug",
            "parent": "TEST-100",
            "tags": ["urgent", "backend"],
            "comments": ["Initial comment"],
        }
        request = JiraIssueRequest(**test_data)

        # Act
        serialized = request.model_dump()

        # Assert
        assert isinstance(serialized, dict)
        assert serialized == test_data

    def test_model_serialization_model_dump_with_none_values(self) -> None:
        """Test that model_dump() includes None values by default."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123")

        # Act
        serialized = request.model_dump()

        # Assert
        expected = {
            "project_id": "TEST-123",
            "key": None,
            "summary": None,
            "description": None,
            "issue_type": None,
            "parent": None,
            "tags": None,
            "comments": None,
        }
        assert serialized == expected

    def test_model_serialization_model_dump_exclude_none(self) -> None:
        """Test that model_dump() can exclude None values."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123", summary="Test")

        # Act
        serialized = request.model_dump(exclude_none=True)

        # Assert
        expected = {"project_id": "TEST-123", "summary": "Test"}
        assert serialized == expected

    def test_model_deserialization_model_validate(self) -> None:
        """Test that the model can be deserialized using model_validate()."""
        # Arrange
        test_data = {
            "project_id": "TEST-123",
            "key": "TEST-456",
            "summary": "Test summary",
            "description": "Test description",
            "issue_type": "Bug",
            "parent": "TEST-100",
            "tags": ["urgent", "backend"],
            "comments": ["Initial comment"],
        }

        # Act
        request = JiraIssueRequest.model_validate(test_data)

        # Assert
        assert request.project_id == "TEST-123"
        assert request.key == "TEST-456"
        assert request.summary == "Test summary"
        assert request.description == "Test description"
        assert request.issue_type == "Bug"
        assert request.parent == "TEST-100"
        assert request.tags == ["urgent", "backend"]
        assert request.comments == ["Initial comment"]

    def test_model_deserialization_model_validate_minimal(self) -> None:
        """Test that model_validate() works with minimal data."""
        # Arrange
        test_data = {"project_id": "TEST-123"}

        # Act
        request = JiraIssueRequest.model_validate(test_data)

        # Assert
        assert request.project_id == "TEST-123"
        assert request.key is None
        assert request.summary is None
        assert request.description is None
        assert request.issue_type is None
        assert request.parent is None
        assert request.tags is None
        assert request.comments is None

    def test_model_deserialization_model_validate_invalid_data(self) -> None:
        """Test that model_validate() raises ValidationError for invalid data."""
        # Arrange
        invalid_data = {"project_id": 123}  # Invalid type

        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            JiraIssueRequest.model_validate(invalid_data)

        # Verify the error is about the wrong type
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "string_type"
        assert errors[0]["loc"] == ("project_id",)

    def test_model_json_serialization(self) -> None:
        """Test that the model can be serialized to JSON."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123", summary="Test summary", tags=["urgent"])

        # Act
        json_str = request.model_dump_json()

        # Assert
        assert isinstance(json_str, str)
        assert "TEST-123" in json_str
        assert "Test summary" in json_str
        assert "urgent" in json_str

    def test_model_equality(self) -> None:
        """Test that two models with same data are equal."""
        # Arrange
        request1 = JiraIssueRequest(project_id="TEST-123", summary="Test summary", tags=["urgent"])
        request2 = JiraIssueRequest(project_id="TEST-123", summary="Test summary", tags=["urgent"])

        # Act & Assert
        assert request1 == request2

    def test_model_inequality(self) -> None:
        """Test that two models with different data are not equal."""
        # Arrange
        request1 = JiraIssueRequest(project_id="TEST-123")
        request2 = JiraIssueRequest(project_id="TEST-456")

        # Act & Assert
        assert request1 != request2

    def test_model_hash(self) -> None:
        """Test that the model is not hashable by default."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123")

        # Act & Assert
        # Pydantic models are not hashable by default
        with pytest.raises(TypeError, match="unhashable type"):
            hash(request)

    def test_model_repr(self) -> None:
        """Test that the model has a useful string representation."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123", summary="Test summary")

        # Act
        repr_str = repr(request)

        # Assert
        assert "JiraIssueRequest" in repr_str
        assert "TEST-123" in repr_str
        assert "Test summary" in repr_str

    def test_model_fields_are_accessible(self) -> None:
        """Test that all model fields are accessible as attributes."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123")

        # Act & Assert
        # All fields should be accessible
        assert hasattr(request, "project_id")
        assert hasattr(request, "key")
        assert hasattr(request, "summary")
        assert hasattr(request, "description")
        assert hasattr(request, "issue_type")
        assert hasattr(request, "parent")
        assert hasattr(request, "tags")
        assert hasattr(request, "comments")

    def test_model_field_assignment(self) -> None:
        """Test that model fields can be assigned new values."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123")

        # Act
        request.summary = "New summary"
        request.tags = ["new", "tag"]

        # Assert
        assert request.summary == "New summary"
        assert request.tags == ["new", "tag"]

    def test_model_field_assignment_validation(self) -> None:
        """Test that field assignment allows any value (validation happens at model creation)."""
        # Arrange
        request = JiraIssueRequest(project_id="TEST-123")

        # Act
        # Pydantic allows direct field assignment without validation
        request.project_id = 123  # This is allowed
        request.summary = 456  # This is allowed

        # Assert
        assert request.project_id == 123
        assert request.summary == 456

    def test_model_with_complex_data(self) -> None:
        """Test model with complex real-world data."""
        # Arrange
        complex_data = {
            "project_id": "PROJ-2023",
            "key": "PROJ-2023-1234",
            "summary": "Critical bug in user authentication system",
            "description": (
                "Users are unable to log in due to session timeout issues.\n\n"
                "Steps to reproduce:\n1. Navigate to login page\n2. Enter valid credentials\n"
                "3. Submit form\n4. Observe session timeout error"
            ),
            "issue_type": "Bug",
            "parent": "PROJ-2023-1000",
            "tags": ["critical", "authentication", "p0", "security"],
            "comments": [
                "Issue reported by multiple users",
                "Affecting 30% of login attempts",
                "Engineering team assigned",
                "Fix deployed to staging environment",
            ],
        }

        # Act
        request = JiraIssueRequest(**complex_data)

        # Assert
        assert request.project_id == "PROJ-2023"
        assert request.key == "PROJ-2023-1234"
        assert "Critical bug" in request.summary
        assert "session timeout" in request.description
        assert request.issue_type == "Bug"
        assert request.parent == "PROJ-2023-1000"
        assert "critical" in request.tags
        assert "security" in request.tags
        assert len(request.comments) == 4
        assert "multiple users" in request.comments[0]
