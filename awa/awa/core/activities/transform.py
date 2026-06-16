from typing import Any

from pydantic import BaseModel
from temporalio import activity
from temporalio.client import Client

from awa.core.utils.config_loader import ConfigLoader
from awa.core.utils.llm_invoker import LlmInvoker
from awa.core.utils.temporal_utils import TemporalUtils
from awa.sdk import constants as sdk_constants
from awa.sdk.models.transform_params import TransformParams


class TransformActivity:
    def __init__(self, temporal_client: Client) -> None:
        """Initialize the TransformActivity with a Temporal client.

        Args:
            temporal_client: The Temporal client instance used for workflow operations
                and task queue management during BAML transformations.

        """
        self._temporal_client = temporal_client

    @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
    async def transform_activity(
        self,
        params: TransformParams,
    ) -> Any:  # noqa: ANN401
        """Transform activity.

        Execute a BAML-defined transformation using an LLM.

        This activity invokes a specified BAML function to perform a transformation on the
        input data. It can operate with pre-existing BAML functions or generate a BAML client
        dynamically if `baml_content` is provided in the parameters. The transformation is
        executed using the configured LLM.

        Args:
            params: An object containing the transformation parameters, including the
                request data, BAML function name, and optional BAML content and model name.

        Returns:
            A dictionary containing the transformation result from the LLM.

        """
        app_config = ConfigLoader.get_config()
        model_name = params.model_name or app_config.llm.default_model

        try:
            top_level_workflow_info = await TemporalUtils.get_top_level_workflow_info_from_activity(
                self._temporal_client,
            )
            llm_invoker = LlmInvoker(config=app_config, baml_src_dir=params.baml_src_dir, logger=activity.logger)
            response: BaseModel | dict[str, Any] | str = await llm_invoker.execute_transform(
                top_level_workflow_type=top_level_workflow_info.workflow_type,
                top_level_workflow_id=top_level_workflow_info.workflow_id,
                activity_info=activity.info(),
                model_name=model_name,
                baml_function_name=params.baml_function_name,
                request=params.request,
                images=params.images,
            )
        except Exception as e:
            activity.logger.error(f"Failed to execute BAML function: {e}")
            raise

        if isinstance(response, BaseModel):
            return response.model_dump()
        return response
