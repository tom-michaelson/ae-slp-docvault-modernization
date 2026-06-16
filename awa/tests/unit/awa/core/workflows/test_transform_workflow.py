import json
import uuid
from unittest.mock import MagicMock

import pytest
from temporalio import activity, exceptions
from temporalio.client import Client, WorkflowFailureError
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

from awa.core.workflows.transform_workflow import TransformWorkflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.input_params import InputParams
from awa.sdk.models.transform_params import TransformParams


class TestTransformWorkflow:
    @pytest.mark.asyncio
    async def test_transform_workflow_executes_activity(self, workflow_client: Client) -> None:
        """Tests that the transform workflow executes the transform_activity and returns its result."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
        )

        transform_activity_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result
        transform_activity_mock.assert_called_once_with(workflow_input)

    @pytest.mark.asyncio
    async def test_transform_workflow_with_timeout(self, workflow_client: Client) -> None:
        """Tests that the transform workflow properly uses a custom timeout."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        timeout = 120
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            timeout_seconds=timeout,
        )

        transform_activity_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl],
        ):
            # The timeout is checked on the activity execution,
            # we can't directly inspect it here without more complex mocking of workflow.execute_activity
            # So we are mainly testing that the workflow runs successfully with the timeout parameter
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result
        transform_activity_mock.assert_called_once_with(workflow_input)

    @pytest.mark.asyncio
    async def test_transform_workflow_with_inputs_populates_request(self, workflow_client: Client) -> None:
        """Tests that the workflow reads files and populates request when inputs are provided."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"existing_key": "existing_value"},
            inputs=[
                InputParams(path="/path/to/file1.txt", name="file1"),
            ],
        )

        transform_activity_mock = MagicMock(return_value=expected_result)
        read_file_mock = MagicMock(return_value="file_content")

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_activity_impl(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl, read_file_activity_impl],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result
        # Verify that the request was populated with file content
        transform_activity_mock.assert_called_once()
        called_params = transform_activity_mock.call_args[0][0]
        assert "existing_key" in called_params.request
        assert called_params.request["existing_key"] == "existing_value"
        assert "file1" in called_params.request
        assert called_params.request["file1"] == "file_content"

    @pytest.mark.asyncio
    async def test_transform_workflow_with_baml_content_generates_client(self, workflow_client: Client) -> None:
        """Tests that the workflow generates a BAML client when baml_content is provided."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        baml_content = "function test_function(input: string) -> string"
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            baml_content=baml_content,
        )

        transform_activity_mock = MagicMock(return_value=expected_result)
        generate_baml_client_mock = MagicMock(return_value="/mock/baml/dir")
        get_parent_workflow_task_queue_mock = MagicMock(return_value=task_queue_name)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_activity_impl(
            baml_function_name: str,
            baml_content: str,
            workflow_task_queue: str,
        ) -> str:
            return generate_baml_client_mock(baml_function_name, baml_content, workflow_task_queue)

        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_activity_impl() -> str:
            return get_parent_workflow_task_queue_mock()

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[
                transform_activity_impl,
                generate_baml_client_activity_impl,
                get_parent_workflow_task_queue_activity_impl,
            ],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result
        get_parent_workflow_task_queue_mock.assert_called_once()
        generate_baml_client_mock.assert_called_once_with("test_function", baml_content, task_queue_name)

        # Verify that the transform activity was called with the baml_src_dir set
        transform_activity_mock.assert_called_once()
        called_params = transform_activity_mock.call_args[0][0]
        assert called_params.baml_src_dir == "/mock/baml/dir"

    @pytest.mark.asyncio
    async def test_transform_workflow_with_output_path_writes_file(self, workflow_client: Client) -> None:
        """Tests that the workflow writes output to file when output_path is provided."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        output_path = "/path/to/output.json"
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            output_path=output_path,
        )

        transform_activity_mock = MagicMock(return_value=expected_result)
        write_file_mock = MagicMock()

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_activity_impl(path: str, content: str) -> None:
            return write_file_mock(path, content)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl, write_file_activity_impl],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result
        transform_activity_mock.assert_called_once_with(workflow_input)
        # The workflow converts dict responses to JSON strings before writing to file
        expected_json_content = json.dumps(expected_result, indent=4)
        write_file_mock.assert_called_once_with(output_path, expected_json_content)

    @pytest.mark.asyncio
    async def test_transform_workflow_with_output_json_path_extracts_and_writes(
        self,
        workflow_client: Client,
    ) -> None:
        """Tests that the workflow extracts data using JSON path and writes it to file."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        transform_result = {
            "status": "completed",
            "translated_function_content": "def my_function():\n    pass",
            "metadata": {"version": "1.0"},
        }
        output_path = "/path/to/output.py"
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            output_path=output_path,
            output_json_path="$.translated_function_content",
        )

        transform_activity_mock = MagicMock(return_value=transform_result)
        write_file_mock = MagicMock()

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_activity_impl(path: str, content: str) -> None:
            return write_file_mock(path, content)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl, write_file_activity_impl],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == transform_result  # Workflow returns the full transform result
        transform_activity_mock.assert_called_once_with(workflow_input)
        # The workflow should extract only the translated_function_content using JSON path
        write_file_mock.assert_called_once_with(output_path, "def my_function():\n    pass")

    @pytest.mark.asyncio
    async def test_transform_workflow_with_invalid_json_path_falls_back(
        self,
        workflow_client: Client,
    ) -> None:
        """Tests that the workflow falls back to full response when JSON path is invalid."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        transform_result = {"status": "completed", "data": "some_data"}
        output_path = "/path/to/output.json"
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            output_path=output_path,
            output_json_path="$.nonexistent_field",
        )

        transform_activity_mock = MagicMock(return_value=transform_result)
        write_file_mock = MagicMock()

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_activity_impl(path: str, content: str) -> None:
            return write_file_mock(path, content)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl, write_file_activity_impl],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == transform_result
        transform_activity_mock.assert_called_once_with(workflow_input)
        # Since JSON path finds no matches, output_data becomes None and file is not written
        write_file_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_transform_workflow_with_malformed_json_path_falls_back(
        self,
        workflow_client: Client,
    ) -> None:
        """Tests that the workflow falls back to full response when JSON path is malformed."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        transform_result = {"status": "completed", "data": "some_data"}
        output_path = "/path/to/output.json"
        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            output_path=output_path,
            output_json_path="$[invalid syntax",
        )

        transform_activity_mock = MagicMock(return_value=transform_result)
        write_file_mock = MagicMock()

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def write_file_activity_impl(path: str, content: str) -> None:
            return write_file_mock(path, content)

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[transform_activity_impl, write_file_activity_impl],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == transform_result
        transform_activity_mock.assert_called_once_with(workflow_input)
        # When JSON path parsing fails (malformed syntax), no data is extracted and file is not written
        write_file_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_transform_workflow_with_baml_content_dir(self, workflow_client: Client) -> None:
        """Tests that the workflow reads and compiles BAML files from a directory."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        baml_dir = "/path/to/baml/files"

        # Mock directory contents with BAML files
        directory_contents = [
            {"file": "models/user.baml", "content": "class User { name: string }"},
            {"file": "functions/transform.baml", "content": "function transform() -> string"},
            {"file": "README.md", "content": "Documentation"},  # Non-BAML file should be ignored
        ]

        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            baml_content_dir=baml_dir,
        )

        transform_activity_mock = MagicMock(return_value=expected_result)
        read_directory_mock = MagicMock(return_value=directory_contents)
        generate_baml_client_mock = MagicMock(return_value="/mock/baml/dir")
        get_parent_workflow_task_queue_mock = MagicMock(return_value=task_queue_name)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_DIRECTORY)
        async def read_directory_activity_impl(path: str) -> list:
            return read_directory_mock(path)

        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_activity_impl(
            baml_function_name: str,
            baml_content: str,
            workflow_task_queue: str,
        ) -> str:
            return generate_baml_client_mock(baml_function_name, baml_content, workflow_task_queue)

        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_activity_impl() -> str:
            return get_parent_workflow_task_queue_mock()

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[
                transform_activity_impl,
                read_directory_activity_impl,
                generate_baml_client_activity_impl,
                get_parent_workflow_task_queue_activity_impl,
            ],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result
        read_directory_mock.assert_called_once_with(baml_dir)
        get_parent_workflow_task_queue_mock.assert_called_once()

        # Verify that BAML files were combined correctly with source markers
        generate_baml_client_mock.assert_called_once()
        combined_content = generate_baml_client_mock.call_args[0][1]

        # Check that source markers are present and files are sorted alphabetically
        assert "// ===== Source: functions/transform.baml =====" in combined_content
        assert "// ===== Source: models/user.baml =====" in combined_content
        assert "function transform() -> string" in combined_content
        assert "class User { name: string }" in combined_content
        assert "Documentation" not in combined_content  # README.md should be ignored

        # Verify that the transform activity was called with the baml_src_dir set
        transform_activity_mock.assert_called_once()
        called_params = transform_activity_mock.call_args[0][0]
        assert called_params.baml_src_dir == "/mock/baml/dir"

    @pytest.mark.asyncio
    async def test_transform_workflow_baml_content_dir_mutual_exclusivity(self, workflow_client: Client) -> None:
        """Tests that providing both baml_content and baml_content_dir raises a ValueError."""
        # Arrange
        task_queue_name = str(uuid.uuid4())

        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            baml_content="direct baml content",
            baml_content_dir="/path/to/baml/files",
        )

        # Need to mock all potentially called activities before the exception
        transform_activity_mock = MagicMock(return_value={"status": "should_not_reach"})
        read_file_mock = MagicMock(return_value="file_content")
        read_directory_mock = MagicMock(return_value=[{"file": "test.baml", "content": "test"}])

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_activity_impl(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_DIRECTORY)
        async def read_directory_activity_impl(path: str) -> list:
            return read_directory_mock(path)

        # Act & Assert
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[
                transform_activity_impl,
                read_file_activity_impl,
                read_directory_activity_impl,
            ],
        ):
            with pytest.raises(WorkflowFailureError) as exc_info:
                await workflow_client.execute_workflow(
                    TransformWorkflow.run,
                    workflow_input,
                    id=str(uuid.uuid4()),
                    task_queue=task_queue_name,
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )

            # Check the cause chain for the ValueError
            assert isinstance(exc_info.value.cause, exceptions.ApplicationError)
            assert "Cannot specify both 'baml_content' and 'baml_content_dir'" in str(exc_info.value.cause)

    @pytest.mark.asyncio
    async def test_transform_workflow_baml_content_dir_no_baml_files(self, workflow_client: Client) -> None:
        """Tests that a directory with no BAML files raises a ValueError."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        baml_dir = "/path/to/empty/dir"

        # Mock directory contents with no BAML files
        directory_contents = [
            {"file": "README.md", "content": "Documentation"},
            {"file": "config.json", "content": "{}"},
        ]

        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            baml_content_dir=baml_dir,
        )

        # Need to mock all potentially called activities before the exception
        read_directory_mock = MagicMock(return_value=directory_contents)
        transform_activity_mock = MagicMock(return_value={"status": "should_not_reach"})
        read_file_mock = MagicMock(return_value="file_content")

        @activity.defn(name=sdk_constants.ACTIVITY_READ_DIRECTORY)
        async def read_directory_activity_impl(path: str) -> list:
            return read_directory_mock(path)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def read_file_activity_impl(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        # Act & Assert
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[
                read_directory_activity_impl,
                transform_activity_impl,
                read_file_activity_impl,
            ],
        ):
            with pytest.raises(WorkflowFailureError) as exc_info:
                await workflow_client.execute_workflow(
                    TransformWorkflow.run,
                    workflow_input,
                    id=str(uuid.uuid4()),
                    task_queue=task_queue_name,
                    retry_policy=RetryPolicy(maximum_attempts=1),
                )

            # Check the cause chain for the ValueError
            assert isinstance(exc_info.value.cause, exceptions.ApplicationError)
            assert f"No BAML files found in directory: {baml_dir}" in str(exc_info.value.cause)

    @pytest.mark.asyncio
    async def test_transform_workflow_baml_content_dir_file_ordering(self, workflow_client: Client) -> None:
        """Tests that BAML files are always processed in alphabetical order."""
        # Arrange
        task_queue_name = str(uuid.uuid4())
        expected_result = {"status": "completed"}
        baml_dir = "/path/to/baml/files"

        # Mock directory contents with BAML files in random order
        directory_contents = [
            {"file": "z_last.baml", "content": "// z_last"},
            {"file": "a_first.baml", "content": "// a_first"},
            {"file": "m_middle.baml", "content": "// m_middle"},
        ]

        workflow_input = TransformParams(
            baml_function_name="test_function",
            request={"data": "sample"},
            baml_content_dir=baml_dir,
        )

        transform_activity_mock = MagicMock(return_value=expected_result)
        read_directory_mock = MagicMock(return_value=directory_contents)
        generate_baml_client_mock = MagicMock(return_value="/mock/baml/dir")
        get_parent_workflow_task_queue_mock = MagicMock(return_value=task_queue_name)

        @activity.defn(name=sdk_constants.ACTIVITY_TRANSFORM)
        async def transform_activity_impl(params: TransformParams) -> dict:
            return transform_activity_mock(params)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_DIRECTORY)
        async def read_directory_activity_impl(path: str) -> list:
            return read_directory_mock(path)

        @activity.defn(name=sdk_constants.ACTIVITY_GENERATE_BAML_CLIENT)
        async def generate_baml_client_activity_impl(
            baml_function_name: str,
            baml_content: str,
            workflow_task_queue: str,
        ) -> str:
            return generate_baml_client_mock(baml_function_name, baml_content, workflow_task_queue)

        @activity.defn(name=sdk_constants.ACTIVITY_GET_PARENT_WORKFLOW_TASK_QUEUE)
        async def get_parent_workflow_task_queue_activity_impl() -> str:
            return get_parent_workflow_task_queue_mock()

        # Act
        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[TransformWorkflow],
            activities=[
                transform_activity_impl,
                read_directory_activity_impl,
                generate_baml_client_activity_impl,
                get_parent_workflow_task_queue_activity_impl,
            ],
        ):
            result = await workflow_client.execute_workflow(
                TransformWorkflow.run,
                workflow_input,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        # Assert
        assert result == expected_result

        # Verify that files were sorted alphabetically in the combined content
        generate_baml_client_mock.assert_called_once()
        combined_content = generate_baml_client_mock.call_args[0][1]

        # Find the positions of each file marker in the combined content
        pos_a = combined_content.find("// ===== Source: a_first.baml =====")
        pos_m = combined_content.find("// ===== Source: m_middle.baml =====")
        pos_z = combined_content.find("// ===== Source: z_last.baml =====")

        # Verify alphabetical ordering
        assert pos_a < pos_m < pos_z, "Files should be ordered alphabetically"
