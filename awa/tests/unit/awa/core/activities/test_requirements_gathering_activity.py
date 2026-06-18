"""Unit tests for requirements gathering activities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from awa.core.activities.requirements_gathering_activity import (
    analyze_requirements,
    generate_clarifying_questions,
    generate_contextual_follow_up,
)
from awa.core.models.requirements import ClarifyingQuestions, StructuredRequirements


class TestGenerateClarifyingQuestions:
    """Test cases for generate_clarifying_questions activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.requirements_gathering_activity.LlmInvoker")
    @patch("awa.core.activities.requirements_gathering_activity.ConfigLoader")
    async def test_generate_clarifying_questions_success(
        self,
        mock_config_loader: MagicMock,
        mock_llm_invoker_class: MagicMock,
    ) -> None:
        """Test successful generation of clarifying questions."""
        # Arrange
        initial_description = "I need a user management system"
        mock_config = MagicMock()
        mock_config.llm.default_model = "gpt-4"
        mock_config_loader.get_config.return_value = mock_config

        mock_llm_invoker = AsyncMock()
        expected_questions = ClarifyingQuestions(
            questions=[
                "What user roles do you need?",
                "Do you need authentication?",
                "What user information should be stored?",
            ],
        )
        mock_llm_invoker.execute_transform.return_value = expected_questions
        mock_llm_invoker_class.return_value = mock_llm_invoker

        # Act
        result = await generate_clarifying_questions(initial_description)

        # Assert
        assert result == expected_questions
        mock_llm_invoker_class.assert_called_once()
        call_args = mock_llm_invoker_class.call_args
        assert call_args[1]["config"] == mock_config
        # Check that baml_src_dir ends with the correct path components
        assert call_args[1]["baml_src_dir"].name == "baml_src"
        assert call_args[1]["baml_src_dir"].parent.name == "core"
        mock_llm_invoker.execute_transform.assert_called_once_with(
            model_name="gpt-4",
            baml_function_name="GenerateClarifyingQuestions",
            request=initial_description,
        )

    @pytest.mark.asyncio
    @patch("awa.core.activities.requirements_gathering_activity.LlmInvoker")
    @patch("awa.core.activities.requirements_gathering_activity.ConfigLoader")
    async def test_generate_clarifying_questions_llm_error(
        self,
        mock_config_loader: MagicMock,
        mock_llm_invoker_class: MagicMock,
    ) -> None:
        """Test handling of LLM errors in generate_clarifying_questions."""
        # Arrange
        initial_description = "I need a user management system"
        mock_config = MagicMock()
        mock_config.llm.default_model = "gpt-4"
        mock_config_loader.get_config.return_value = mock_config

        mock_llm_invoker = AsyncMock()
        mock_llm_invoker.execute_transform.side_effect = Exception("LLM API error")
        mock_llm_invoker_class.return_value = mock_llm_invoker

        # Act & Assert
        with pytest.raises(Exception, match="LLM API error"):
            await generate_clarifying_questions(initial_description)


class TestGenerateContextualFollowUp:
    """Test cases for generate_contextual_follow_up activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.requirements_gathering_activity.LlmInvoker")
    @patch("awa.core.activities.requirements_gathering_activity.ConfigLoader")
    async def test_generate_contextual_follow_up_success(
        self,
        mock_config_loader: MagicMock,
        mock_llm_invoker_class: MagicMock,
    ) -> None:
        """Test successful generation of contextual follow-up questions."""
        # Arrange
        context = {
            "original_request": "User management system",
            "conversation_history": [
                {"user": "I need user roles", "assistant": "What roles do you need?"},
            ],
            "latest_user_response": "Admin and regular user roles",
        }
        mock_config = MagicMock()
        mock_config.llm.default_model = "gpt-4"
        mock_config_loader.get_config.return_value = mock_config

        mock_llm_invoker = AsyncMock()
        expected_questions = ClarifyingQuestions(
            questions=[
                "What permissions should admin users have?",
                "Should regular users be able to edit profiles?",
            ],
        )
        mock_llm_invoker.execute_transform.return_value = expected_questions
        mock_llm_invoker_class.return_value = mock_llm_invoker

        # Act
        result = await generate_contextual_follow_up(context)

        # Assert
        assert result == expected_questions
        mock_llm_invoker.execute_transform.assert_called_once_with(
            model_name="gpt-4",
            baml_function_name="GenerateContextualFollowUpQuestions",
            request=context,
        )


class TestAnalyzeRequirements:
    """Test cases for analyze_requirements activity."""

    @pytest.mark.asyncio
    @patch("awa.core.activities.requirements_gathering_activity.LlmInvoker")
    @patch("awa.core.activities.requirements_gathering_activity.ConfigLoader")
    async def test_analyze_requirements_success(
        self,
        mock_config_loader: MagicMock,
        mock_llm_invoker_class: MagicMock,
    ) -> None:
        """Test successful requirements analysis."""
        # Arrange
        conversation_text = (
            "User: I need a user management system\n"
            "Assistant: What user roles do you need?\n"
            "User: Admin and regular users\n"
            "Assistant: What should admins be able to do?\n"
            "User: Manage all users, create/delete accounts"
        )
        mock_config = MagicMock()
        mock_config.llm.default_model = "gpt-4"
        mock_config_loader.get_config.return_value = mock_config

        mock_llm_invoker = AsyncMock()
        expected_requirements = StructuredRequirements(
            requirements=[
                "User authentication system",
                "Role-based access control",
                "User account management",
            ],
            user_stories=[
                "As a user, I can log in",
                "As an admin, I can manage all users",
            ],
            acceptance_criteria=[
                "System must be secure",
                "Support multiple concurrent users",
            ],
            technical_notes=[
                "Use JWT tokens",
                "Must integrate with existing system",
            ],
        )
        mock_llm_invoker.execute_transform.return_value = expected_requirements
        mock_llm_invoker_class.return_value = mock_llm_invoker

        # Act
        result = await analyze_requirements(conversation_text)

        # Assert
        assert result == expected_requirements
        mock_llm_invoker.execute_transform.assert_called_once_with(
            model_name="gpt-4",
            baml_function_name="AnalyzeRequirements",
            request=conversation_text,
        )
