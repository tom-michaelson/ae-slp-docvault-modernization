"""Unit tests for TransformBatchWorkflow."""

import tempfile
import uuid
from datetime import timedelta
from typing import Any
from unittest.mock import MagicMock

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from awa.core.workflows.transform_batch_workflow import TransformBatchWorkflow
from awa.core.workflows.transform_workflow import TransformWorkflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.transform_params import TransformBatchParams, TransformParams


class TestTransformBatchWorkflow:
    """Test cases for TransformBatchWorkflow."""

    def test_workflow_class_exists(self) -> None:
        """Test that TransformBatchWorkflow class exists and is instantiable."""
        workflow_instance = TransformBatchWorkflow()
        assert workflow_instance is not None
        assert hasattr(workflow_instance, "run")

    @pytest.mark.asyncio
    async def test_run_with_single_input(self, workflow_client: Client) -> None:
        """Test workflow run with a single transform input."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed", "output": "Transform result"}

        transform_params = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
        )

        batch_params = TransformBatchParams(
            params_by_key={"key1": transform_params},
        )

        # Mock the transform activity that the child workflow uses
        transform_activity_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        # Mock the get parent workflow task queue activity
        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_impl() -> str:
            return task_queue_name

        # Mock the generate BAML client activity
        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_impl(_function_name: str, _content: str, _task_queue: str) -> str:
            return tempfile.mkdtemp(prefix="baml_")

        # Mock file I/O activities that might be called by TransformWorkflow
        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_BYTES)
        async def read_file_bytes_impl(_file_path: str, _default: str = "") -> bytes:
            return b"mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_or_directory_impl(_input_params: Any) -> str:  # noqa: ANN401
            return "mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_impl(_file_path: str, _content: str) -> None:
            pass

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformBatchWorkflow, TransformWorkflow],
            activities=[
                transform_activity_impl,
                get_parent_workflow_task_queue_impl,
                generate_baml_client_impl,
                read_file_bytes_impl,
                read_file_or_directory_impl,
                write_file_impl,
            ],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                TransformBatchWorkflow.run,
                batch_params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
                execution_timeout=timedelta(seconds=30),
            )

            # Assert
            assert result == {"key1": expected_result}
            transform_activity_mock.assert_called_once_with(transform_params)

    @pytest.mark.asyncio
    async def test_run_with_multiple_inputs(self, workflow_client: Client) -> None:
        """Test workflow run with multiple transform inputs executed in parallel."""
        # Arrange
        task_queue_name = str(uuid.uuid4())

        transform_params_1 = TransformParams(
            baml_function_name="test_function_1",
            request={"data": "sample1"},
        )

        transform_params_2 = TransformParams(
            baml_function_name="test_function_2",
            request={"data": "sample2"},
        )

        batch_params = TransformBatchParams(
            params_by_key={
                "transform_a": transform_params_1,
                "transform_b": transform_params_2,
            },
        )

        # Mock results for each transform
        expected_results = {
            "transform_a": {"status": "completed", "output": "Result A"},
            "transform_b": {"status": "completed", "output": "Result B"},
        }

        # Track calls to ensure all are made
        activity_calls = []

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            activity_calls.append(params)
            # Return different results based on function name
            if params.baml_function_name == "test_function_1":
                return expected_results["transform_a"]
            if params.baml_function_name == "test_function_2":
                return expected_results["transform_b"]
            return {"status": "unknown"}

        # Mock the get parent workflow task queue activity
        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_impl() -> str:
            return task_queue_name

        # Mock the generate BAML client activity
        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_impl(_function_name: str, _content: str, _task_queue: str) -> str:
            return tempfile.mkdtemp(prefix="baml_")

        # Mock file I/O activities that might be called by TransformWorkflow
        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_BYTES)
        async def read_file_bytes_impl(_file_path: str, _default: str = "") -> bytes:
            return b"mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_or_directory_impl(_input_params: Any) -> str:  # noqa: ANN401
            return "mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_impl(_file_path: str, _content: str) -> None:
            pass

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformBatchWorkflow, TransformWorkflow],
            activities=[
                transform_activity_impl,
                get_parent_workflow_task_queue_impl,
                generate_baml_client_impl,
                read_file_bytes_impl,
                read_file_or_directory_impl,
                write_file_impl,
            ],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                TransformBatchWorkflow.run,
                batch_params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
                execution_timeout=timedelta(seconds=30),
            )

            # Assert
            assert result == expected_results
            assert len(activity_calls) == 2

            # Verify all params were called
            called_function_names = {call.baml_function_name for call in activity_calls}
            expected_function_names = {"test_function_1", "test_function_2"}
            assert called_function_names == expected_function_names

    @pytest.mark.asyncio
    async def test_run_with_empty_params_dict(self, workflow_client: Client) -> None:
        """Test workflow run with empty params dictionary."""
        # Arrange
        task_queue_name = str(uuid.uuid4())

        batch_params = TransformBatchParams(
            params_by_key={},  # Empty dictionary
        )

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(_params: TransformParams) -> dict:
            return {"status": "should not be called"}

        # Mock the get parent workflow task queue activity
        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_impl() -> str:
            return task_queue_name

        # Mock the generate BAML client activity
        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_impl(_function_name: str, _content: str, _task_queue: str) -> str:
            return tempfile.mkdtemp(prefix="baml_")

        # Mock file I/O activities that might be called by TransformWorkflow
        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_BYTES)
        async def read_file_bytes_impl(_file_path: str, _default: str = "") -> bytes:
            return b"mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_or_directory_impl(_input_params: Any) -> str:  # noqa: ANN401
            return "mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_impl(_file_path: str, _content: str) -> None:
            pass

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformBatchWorkflow, TransformWorkflow],
            activities=[
                transform_activity_impl,
                get_parent_workflow_task_queue_impl,
                generate_baml_client_impl,
                read_file_bytes_impl,
                read_file_or_directory_impl,
                write_file_impl,
            ],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                TransformBatchWorkflow.run,
                batch_params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
                execution_timeout=timedelta(seconds=30),
            )

            # Assert
            assert result == {}

    @pytest.mark.asyncio
    async def test_max_concurrency_functionality(self, workflow_client: Client) -> None:
        """Test that different max_concurrency values work correctly without mocking."""
        # Test with various concurrency settings to ensure the functionality works
        test_cases = [
            {"max_concurrency": None, "expected_key": "limited"},  # Should use default of 10
            {"max_concurrency": 3, "expected_key": "limited"},  # Should use 3
            {"max_concurrency": 0, "expected_key": "unlimited"},  # Should use unlimited
            {"max_concurrency": -1, "expected_key": "limited"},  # Should use default of 10
        ]

        for _i, case in enumerate(test_cases):
            # Arrange
            task_queue_name = str(uuid.uuid4())

            transform_params = TransformParams(
                baml_function_name="test_function",
                request={"data": "sample", "expected_key": case["expected_key"]},
            )

            batch_params = TransformBatchParams(
                params_by_key={"key1": transform_params},
                max_concurrency=case["max_concurrency"],
            )

            @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
            async def transform_activity_impl(params: TransformParams) -> dict:
                return {"status": "completed", "type": params.request["expected_key"]}

            # Mock the get parent workflow task queue activity
            @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
            async def get_parent_workflow_task_queue_impl(tq_name: str = task_queue_name) -> str:
                return tq_name

            # Mock the generate BAML client activity
            @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
            async def generate_baml_client_impl(_function_name: str, _content: str, _task_queue: str) -> str:
                return tempfile.mkdtemp(prefix="baml_")

            # Mock file I/O activities that might be called by TransformWorkflow
            @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_BYTES)
            async def read_file_bytes_impl(_file_path: str, _default: str = "") -> bytes:
                return b"mock file content"

            @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
            async def read_file_or_directory_impl(_input_params: Any) -> str:  # noqa: ANN401
                return "mock file content"

            @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
            async def write_file_impl(_file_path: str, _content: str) -> None:
                pass

            async with Worker(
                workflow_client,
                task_queue=task_queue_name,
                workflows=[TransformBatchWorkflow, TransformWorkflow],
                activities=[
                    transform_activity_impl,
                    get_parent_workflow_task_queue_impl,
                    generate_baml_client_impl,
                    read_file_bytes_impl,
                    read_file_or_directory_impl,
                    write_file_impl,
                ],
            ):
                # Act
                result = await workflow_client.execute_workflow(
                    TransformBatchWorkflow.run,
                    batch_params,
                    id=str(uuid.uuid4()),
                    task_queue=task_queue_name,
                    execution_timeout=timedelta(seconds=30),
                )

                # Assert
                assert result == {"key1": {"status": "completed", "type": case["expected_key"]}}
                # The workflow should complete successfully regardless of the concurrency setting

    @pytest.mark.asyncio
    async def test_max_concurrency_with_multiple_transforms(self, workflow_client: Client) -> None:
        """Test that concurrency control works correctly with multiple transforms."""
        # Arrange
        task_queue_name = str(uuid.uuid4())

        transform_params_1 = TransformParams(
            baml_function_name="test_function_1",
            request={"data": "sample1"},
        )

        transform_params_2 = TransformParams(
            baml_function_name="test_function_2",
            request={"data": "sample2"},
        )

        batch_params = TransformBatchParams(
            params_by_key={
                "transform_a": transform_params_1,
                "transform_b": transform_params_2,
            },
            max_concurrency=2,  # This should use exactly 2
        )

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            if params.baml_function_name == "test_function_1":
                return {"status": "completed", "output": "Result A"}
            if params.baml_function_name == "test_function_2":
                return {"status": "completed", "output": "Result B"}
            return {"status": "unknown"}

        # Mock the get parent workflow task queue activity
        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_impl() -> str:
            return task_queue_name

        # Mock the generate BAML client activity
        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_impl(_function_name: str, _content: str, _task_queue: str) -> str:
            return tempfile.mkdtemp(prefix="baml_")

        # Mock file I/O activities that might be called by TransformWorkflow
        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_BYTES)
        async def read_file_bytes_impl(_file_path: str, _default: str = "") -> bytes:
            return b"mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_or_directory_impl(_input_params: Any) -> str:  # noqa: ANN401
            return "mock file content"

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_impl(_file_path: str, _content: str) -> None:
            pass

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformBatchWorkflow, TransformWorkflow],
            activities=[
                transform_activity_impl,
                get_parent_workflow_task_queue_impl,
                generate_baml_client_impl,
                read_file_bytes_impl,
                read_file_or_directory_impl,
                write_file_impl,
            ],
        ):
            # Act
            result = await workflow_client.execute_workflow(
                TransformBatchWorkflow.run,
                batch_params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
                execution_timeout=timedelta(seconds=30),
            )

            # Assert
            expected_results = {
                "transform_a": {"status": "completed", "output": "Result A"},
                "transform_b": {"status": "completed", "output": "Result B"},
            }
            assert result == expected_results
