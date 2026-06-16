"""Unit tests for requirements data models."""

import pytest
from pydantic import ValidationError

from awa.core.models.hitl import HITLChatMessage
from awa.core.models.requirements import (
    ClarifyingQuestions,
    RequirementsGatheringInput,
    RequirementsGatheringOutput,
    StructuredRequirements,
)


class TestRequirementsGatheringInput:
    """Test RequirementsGatheringInput model validation and behavior."""

    def test_minimal_input(self) -> None:
        """Test creating RequirementsGatheringInput with minimal required fields."""
        input_data = RequirementsGatheringInput(
            initial_description="Build a user management system",
        )

        assert input_data.initial_description == "Build a user management system"
        assert input_data.timeout_seconds == 3600  # Default 1 hour

    def test_full_input(self) -> None:
        """Test creating RequirementsGatheringInput with all fields."""
        input_data = RequirementsGatheringInput(
            initial_description="Build a user management system",
            timeout_seconds=7200,  # 2 hours
        )

        assert input_data.initial_description == "Build a user management system"
        assert input_data.timeout_seconds == 7200

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            RequirementsGatheringInput()  # Missing initial_description

        errors = exc_info.value.errors()
        assert len(errors) == 1
        field_names = {e["loc"][0] for e in errors}
        assert field_names == {"initial_description"}


class TestRequirementsGatheringOutput:
    """Test RequirementsGatheringOutput model validation and behavior."""

    def test_minimal_output(self) -> None:
        """Test creating RequirementsGatheringOutput with defaults."""
        output_data = RequirementsGatheringOutput()

        assert output_data.requirements is None
        assert output_data.user_stories is None
        assert output_data.acceptance_criteria is None
        assert output_data.technical_notes is None
        assert output_data.chat_history == []
        assert output_data.success is False
        assert output_data.error_message is None

    def test_full_output(self) -> None:
        """Test creating RequirementsGatheringOutput with all fields."""
        chat_message = HITLChatMessage(message="Test message")

        output_data = RequirementsGatheringOutput(
            requirements=["User authentication", "Role management"],
            user_stories=["As a user, I can log in"],
            acceptance_criteria=["Login form validates inputs"],
            technical_notes=["Use JWT tokens"],
            chat_history=[chat_message],
            success=True,
            error_message=None,
        )

        assert len(output_data.requirements) == 2
        assert len(output_data.user_stories) == 1
        assert len(output_data.acceptance_criteria) == 1
        assert len(output_data.technical_notes) == 1
        assert len(output_data.chat_history) == 1
        assert output_data.success is True

    def test_error_output(self) -> None:
        """Test creating RequirementsGatheringOutput with error."""
        output_data = RequirementsGatheringOutput(
            success=False,
            error_message="Timeout occurred during requirements gathering",
        )

        assert output_data.success is False
        assert output_data.error_message == "Timeout occurred during requirements gathering"


class TestClarifyingQuestions:
    """Test ClarifyingQuestions model validation and behavior."""

    def test_valid_questions(self) -> None:
        """Test creating ClarifyingQuestions with valid data."""
        questions_data = ClarifyingQuestions(
            questions=[
                "What user roles do you need?",
                "Do you need authentication?",
                "What data should be stored for each user?",
            ],
        )

        assert len(questions_data.questions) == 3
        assert "What user roles do you need?" in questions_data.questions

    def test_empty_questions_list(self) -> None:
        """Test creating ClarifyingQuestions with empty list."""
        questions_data = ClarifyingQuestions(questions=[])

        assert len(questions_data.questions) == 0

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            ClarifyingQuestions()  # Missing questions

        errors = exc_info.value.errors()
        assert len(errors) == 1
        field_names = {e["loc"][0] for e in errors}
        assert field_names == {"questions"}


class TestStructuredRequirements:
    """Test StructuredRequirements model validation and behavior."""

    def test_valid_structured_requirements(self) -> None:
        """Test creating StructuredRequirements with valid data."""
        requirements_data = StructuredRequirements(
            requirements=["User authentication", "Role management"],
            user_stories=["As a user, I can log in", "As an admin, I can manage users"],
            acceptance_criteria=["Login form validates inputs", "Admin can create users"],
            technical_notes=["Use JWT tokens", "Store passwords securely"],
        )

        assert len(requirements_data.requirements) == 2
        assert len(requirements_data.user_stories) == 2
        assert len(requirements_data.acceptance_criteria) == 2
        assert len(requirements_data.technical_notes) == 2

    def test_empty_lists(self) -> None:
        """Test creating StructuredRequirements with empty lists."""
        requirements_data = StructuredRequirements(
            requirements=[],
            user_stories=[],
            acceptance_criteria=[],
            technical_notes=[],
        )

        assert len(requirements_data.requirements) == 0
        assert len(requirements_data.user_stories) == 0
        assert len(requirements_data.acceptance_criteria) == 0
        assert len(requirements_data.technical_notes) == 0

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise validation errors."""
        with pytest.raises(ValidationError) as exc_info:
            StructuredRequirements()  # Missing all required fields

        errors = exc_info.value.errors()
        assert len(errors) == 4
        field_names = {e["loc"][0] for e in errors}
        assert field_names == {"requirements", "user_stories", "acceptance_criteria", "technical_notes"}
