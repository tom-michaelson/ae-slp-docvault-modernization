import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow

from awa.core import constants
from awa.core.utils.concurrency_utils import ConcurrencyUtils
from awa.sdk import constants as sdk_constants
from awa.sdk.models.transform_params import TransformBatchParams, TransformParams


# TODO RH: Need to control level of parallelism here
@workflow.defn(name=sdk_constants.WORKFLOW_TRANSFORM_BATCH)
class TransformBatchWorkflow:
    @workflow.run
    async def run(self, workflow_input: TransformBatchParams) -> dict[str, Any]:
        """Execute transform workflows for multiple inputs in parallel.

        Note: This executes child transform workflows for each input in parallel. In the future,
        having a workflow here will allow us to provide more functionality by default (e.g. response streaming).

        Args:
            workflow_input: A dictionary mapping keys to TransformParams for each transform operation.

        Returns:
            A dictionary mapping the original input keys to their respective transform results.

        """
        # Collect unique BAML functions that need client generation
        unique_baml_functions: dict[tuple[str, str], tuple[str, str]] = {}
        for transform_params in workflow_input.params_by_key.values():
            if transform_params.baml_content is not None:
                # Use baml_function_name and baml_content as the unique key
                key = (transform_params.baml_function_name, transform_params.baml_content)
                unique_baml_functions[key] = (transform_params.baml_function_name, transform_params.baml_content)

        # Generate BAML clients for all unique functions in parallel
        baml_client_mapping: dict[tuple[str, str], str] = {}
        if unique_baml_functions:
            workflow_task_queue = await workflow.execute_local_activity(
                activity=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE,
                start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS),
            )

            # Create tasks for generating all unique BAML clients
            baml_generation_tasks = []
            baml_function_keys = []

            for baml_function_name, baml_content in unique_baml_functions.values():
                task = workflow.execute_local_activity(
                    activity=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT,
                    args=[baml_function_name, baml_content, workflow_task_queue],
                    start_to_close_timeout=timedelta(seconds=constants.DEFAULT_ACTIVITY_TIMEOUT_SECONDS * 5),
                )
                baml_generation_tasks.append(task)
                baml_function_keys.append((baml_function_name, baml_content))

            # Execute all BAML client generations in parallel
            baml_src_dirs = await asyncio.gather(*baml_generation_tasks)

            # Create mapping from function key to generated source directory
            baml_client_mapping = dict(zip(baml_function_keys, baml_src_dirs, strict=False))

        # Update transform params with generated BAML source directories
        for transform_params in workflow_input.params_by_key.values():
            if transform_params.baml_content is not None:
                key = (transform_params.baml_function_name, transform_params.baml_content)
                if key in baml_client_mapping:
                    transform_params.baml_src_dir = baml_client_mapping[key]

        use_controlled_concurrency = True
        max_concurrency: int = constants.DEFAULT_TRANSFORM_BATCH_MAX_CONCURRENCY
        if workflow_input.max_concurrency == 0:
            # 0 means unlimited concurrency
            max_concurrency = None
            use_controlled_concurrency = False
        elif workflow_input.max_concurrency is not None and workflow_input.max_concurrency > 0:
            max_concurrency = int(workflow_input.max_concurrency)
            use_controlled_concurrency = True
        # If max_concurrency is negative or None, use default value

        # Create coroutine functions for child workflows and collect keys
        async def create_child_workflow_coroutine(key: str, transform_params: TransformParams) -> Any:  # noqa: ANN401
            return await workflow.execute_child_workflow(
                sdk_constants.WORKFLOW_TRANSFORM,
                transform_params,
                id=f"{transform_params.baml_function_name}-{key}-{workflow.info().workflow_id}",
            )

        # Create list of coroutine functions and keys
        coroutine_funcs = []
        keys = []
        for key, transform_params in workflow_input.params_by_key.items():
            coroutine_funcs.append(lambda k=key, tp=transform_params: create_child_workflow_coroutine(k, tp))
            keys.append(key)

        # Execute child workflows with controlled concurrency or unlimited concurrency
        if use_controlled_concurrency:
            # Use controlled concurrency
            results = await ConcurrencyUtils.run_with_controlled_concurrency(
                coroutine_funcs=coroutine_funcs,
                max_concurrency=max_concurrency,
            )
        else:
            # Use original unlimited concurrency approach
            results = await asyncio.gather(*[coro_func() for coro_func in coroutine_funcs])

        # Return results in dict format with original keys
        return dict(zip(keys, results, strict=False))
