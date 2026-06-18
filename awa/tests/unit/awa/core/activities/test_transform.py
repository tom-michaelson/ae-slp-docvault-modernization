from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from temporalio.testing import ActivityEnvironment

from awa.core.activities.transform import TransformActivity
from awa.sdk.models.transform_params import TransformParams


class SampleResponse(BaseModel):
    message: str
    success: bool


class TestTransformActivity:
    @pytest.fixture
    def mock_temporal_client(self) -> MagicMock:
        """Create a mock temporal client for testing."""
        return MagicMock()

    @pytest.fixture
    def transform_activity_instance(self, mock_temporal_client: MagicMock) -> TransformActivity:
        """Create a TransformActivity instance with mocked client."""
        return TransformActivity(mock_temporal_client)

    @pytest.mark.asyncio
    async def test_transform_activity_success_with_pydantic_response(
        self,
        activity_env: ActivityEnvironment,
        transform_activity_instance: TransformActivity,
    ) -> None:
        # Arrange
        params = TransformParams(
            model_name="test_model",
            baml_function_name="test_function",
            baml_content="test content",
            request={"input": "test"},
            baml_src_dir="/mock/baml/dir",  # BAML client directory is provided by workflow
        )
        expected_response = SampleResponse(message="test response", success=True)

        with (
            patch("awa.core.activities.transform.ConfigLoader.get_config") as mock_config_loader,
            patch("awa.core.activities.transform.LlmInvoker") as mock_llm_invoker,
            patch(
                "awa.core.activities.transform.TemporalUtils.get_top_level_workflow_info_from_activity",
            ) as mock_get_info,
        ):
            # Arrange
            mock_config = MagicMock()
            mock_config.llm.default_model = "default_model"
            mock_config_loader.return_value = mock_config

            # Mock workflow info
            mock_workflow_info = MagicMock()
            mock_workflow_info.workflow_type = "test_workflow_type"
            mock_workflow_info.workflow_id = "test_workflow_id"
            mock_get_info.return_value = mock_workflow_info

            mock_invoker_instance = AsyncMock()
            mock_invoker_instance.execute_transform.return_value = expected_response
            mock_llm_invoker.return_value = mock_invoker_instance

            # Act
            result = await activity_env.run(transform_activity_instance.transform_activity, params)

            # Assert
            assert result == expected_response.model_dump()
            mock_llm_invoker.assert_called_once_with(config=mock_config, baml_src_dir="/mock/baml/dir", logger=ANY)
            mock_invoker_instance.execute_transform.assert_called_once_with(
                top_level_workflow_type="test_workflow_type",
                top_level_workflow_id="test_workflow_id",
                activity_info=activity_env.info,
                model_name="test_model",
                baml_function_name=params.baml_function_name,
                request=params.request,
                images=None,
            )

    @pytest.mark.asyncio
    async def test_transform_activity_success_with_dict_response(
        self,
        activity_env: ActivityEnvironment,
        transform_activity_instance: TransformActivity,
    ) -> None:
        # Arrange
        params = TransformParams(
            model_name="test_model",
            baml_function_name="test_function",
            baml_content="test content",
            request={"input": "test"},
            baml_src_dir="/mock/baml/dir",  # BAML client directory is provided by workflow
        )
        expected_response = {"message": "test response", "success": True}

        with (
            patch("awa.core.activities.transform.ConfigLoader.get_config") as mock_config_loader,
            patch("awa.core.activities.transform.LlmInvoker") as mock_llm_invoker,
            patch(
                "awa.core.activities.transform.TemporalUtils.get_top_level_workflow_info_from_activity",
            ) as mock_get_info,
        ):
            # Arrange
            mock_config = MagicMock()
            mock_config.llm.default_model = "default_model"
            mock_config_loader.return_value = mock_config

            # Mock workflow info
            mock_workflow_info = MagicMock()
            mock_workflow_info.workflow_type = "test_workflow_type"
            mock_workflow_info.workflow_id = "test_workflow_id"
            mock_get_info.return_value = mock_workflow_info

            mock_invoker_instance = AsyncMock()
            mock_invoker_instance.execute_transform.return_value = expected_response
            mock_llm_invoker.return_value = mock_invoker_instance

            # Act
            result = await activity_env.run(transform_activity_instance.transform_activity, params)

            # Assert
            assert result == expected_response
            mock_llm_invoker.assert_called_once_with(config=mock_config, baml_src_dir="/mock/baml/dir", logger=ANY)
            mock_invoker_instance.execute_transform.assert_called_once_with(
                top_level_workflow_type="test_workflow_type",
                top_level_workflow_id="test_workflow_id",
                activity_info=activity_env.info,
                model_name="test_model",
                baml_function_name=params.baml_function_name,
                request=params.request,
                images=None,
            )

    @pytest.mark.asyncio
    async def test_transform_activity_uses_default_model_when_none_provided(
        self,
        activity_env: ActivityEnvironment,
        transform_activity_instance: TransformActivity,
    ) -> None:
        # Arrange
        params = TransformParams(
            model_name=None,  # No model specified
            baml_function_name="test_function",
            baml_content="test content",
            request={"input": "test"},
            baml_src_dir="/mock/baml/dir",  # BAML client directory is provided by workflow
        )

        with (
            patch("awa.core.activities.transform.ConfigLoader.get_config") as mock_config_loader,
            patch("awa.core.activities.transform.LlmInvoker") as mock_llm_invoker,
            patch(
                "awa.core.activities.transform.TemporalUtils.get_top_level_workflow_info_from_activity",
            ) as mock_get_info,
        ):
            # Arrange
            mock_config = MagicMock()
            mock_config.llm.default_model = "default_model"
            mock_config_loader.return_value = mock_config

            # Mock workflow info
            mock_workflow_info = MagicMock()
            mock_workflow_info.workflow_type = "test_workflow_type"
            mock_workflow_info.workflow_id = "test_workflow_id"
            mock_get_info.return_value = mock_workflow_info

            mock_invoker_instance = AsyncMock()
            mock_invoker_instance.execute_transform.return_value = {"success": True}
            mock_llm_invoker.return_value = mock_invoker_instance

            # Act
            await activity_env.run(transform_activity_instance.transform_activity, params)

            # Assert
            mock_invoker_instance.execute_transform.assert_called_once_with(
                top_level_workflow_type="test_workflow_type",
                top_level_workflow_id="test_workflow_id",
                activity_info=activity_env.info,
                model_name="default_model",  # Should use default model
                baml_function_name=params.baml_function_name,
                request=params.request,
                images=None,
            )

    @pytest.mark.asyncio
    async def test_transform_activity_without_baml_content(
        self,
        activity_env: ActivityEnvironment,
        transform_activity_instance: TransformActivity,
    ) -> None:
        # Arrange
        params = TransformParams(
            model_name="test_model",
            baml_function_name="test_function",
            baml_content=None,  # No BAML content
            request={"input": "test"},
            baml_src_dir=None,  # No BAML source directory when no content
        )

        with (
            patch("awa.core.activities.transform.ConfigLoader.get_config") as mock_config_loader,
            patch("awa.core.activities.transform.LlmInvoker") as mock_llm_invoker,
            patch(
                "awa.core.activities.transform.TemporalUtils.get_top_level_workflow_info_from_activity",
            ) as mock_get_info,
        ):
            # Arrange
            mock_config = MagicMock()
            mock_config.llm.default_model = "default_model"
            mock_config_loader.return_value = mock_config

            # Mock workflow info
            mock_workflow_info = MagicMock()
            mock_workflow_info.workflow_type = "test_workflow_type"
            mock_workflow_info.workflow_id = "test_workflow_id"
            mock_get_info.return_value = mock_workflow_info

            mock_invoker_instance = AsyncMock()
            mock_invoker_instance.execute_transform.return_value = {"success": True}
            mock_llm_invoker.return_value = mock_invoker_instance

            # Act
            result = await activity_env.run(transform_activity_instance.transform_activity, params)

            # Assert
            assert result == {"success": True}
            mock_llm_invoker.assert_called_once_with(config=mock_config, baml_src_dir=None, logger=ANY)
            mock_invoker_instance.execute_transform.assert_called_once_with(
                top_level_workflow_type="test_workflow_type",
                top_level_workflow_id="test_workflow_id",
                activity_info=activity_env.info,
                model_name="test_model",
                baml_function_name=params.baml_function_name,
                request=params.request,
                images=None,
            )

    @pytest.mark.asyncio
    async def test_transform_activity_handles_llm_invoker_exception(
        self,
        activity_env: ActivityEnvironment,
        transform_activity_instance: TransformActivity,
    ) -> None:
        # Arrange
        params = TransformParams(
            model_name="test_model",
            baml_function_name="test_function",
            baml_content="test content",
            request={"input": "test"},
            baml_src_dir="/mock/baml/dir",
        )

        with (
            patch("awa.core.activities.transform.ConfigLoader.get_config") as mock_config_loader,
            patch("awa.core.activities.transform.LlmInvoker") as mock_llm_invoker,
            patch(
                "awa.core.activities.transform.TemporalUtils.get_top_level_workflow_info_from_activity",
            ) as mock_get_info,
        ):
            # Arrange
            mock_config = MagicMock()
            mock_config.llm.default_model = "default_model"
            mock_config_loader.return_value = mock_config

            # Mock workflow info
            mock_workflow_info = MagicMock()
            mock_workflow_info.workflow_type = "test_workflow_type"
            mock_workflow_info.workflow_id = "test_workflow_id"
            mock_get_info.return_value = mock_workflow_info

            mock_invoker_instance = AsyncMock()
            mock_invoker_instance.execute_transform.side_effect = Exception("LLM error")
            mock_llm_invoker.return_value = mock_invoker_instance

            # Act & Assert
            with pytest.raises(Exception, match="LLM error"):
                await activity_env.run(transform_activity_instance.transform_activity, params)

    @pytest.mark.asyncio
    async def test_transform_activity_with_string_response(
        self,
        activity_env: ActivityEnvironment,
        transform_activity_instance: TransformActivity,
    ) -> None:
        # Arrange
        params = TransformParams(
            model_name="test_model",
            baml_function_name="test_function",
            baml_content="test content",
            request={"input": "test"},
            baml_src_dir="/mock/baml/dir",
        )
        expected_response = "Simple string response"

        with (
            patch("awa.core.activities.transform.ConfigLoader.get_config") as mock_config_loader,
            patch("awa.core.activities.transform.LlmInvoker") as mock_llm_invoker,
            patch(
                "awa.core.activities.transform.TemporalUtils.get_top_level_workflow_info_from_activity",
            ) as mock_get_info,
        ):
            # Arrange
            mock_config = MagicMock()
            mock_config.llm.default_model = "default_model"
            mock_config_loader.return_value = mock_config

            # Mock workflow info
            mock_workflow_info = MagicMock()
            mock_workflow_info.workflow_type = "test_workflow_type"
            mock_workflow_info.workflow_id = "test_workflow_id"
            mock_get_info.return_value = mock_workflow_info

            mock_invoker_instance = AsyncMock()
            mock_invoker_instance.execute_transform.return_value = expected_response
            mock_llm_invoker.return_value = mock_invoker_instance

            # Act
            result = await activity_env.run(transform_activity_instance.transform_activity, params)

            # Assert
            assert result == expected_response
            mock_llm_invoker.assert_called_once_with(config=mock_config, baml_src_dir="/mock/baml/dir", logger=ANY)
            mock_invoker_instance.execute_transform.assert_called_once_with(
                top_level_workflow_type="test_workflow_type",
                top_level_workflow_id="test_workflow_id",
                activity_info=activity_env.info,
                model_name="test_model",
                baml_function_name=params.baml_function_name,
                request=params.request,
                images=None,
            )
