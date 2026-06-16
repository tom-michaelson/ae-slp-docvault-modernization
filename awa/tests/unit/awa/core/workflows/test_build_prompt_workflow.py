"""Unit tests for BuildPromptWorkflow."""

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from temporalio import activity
from temporalio.client import Client
from temporalio.worker import Worker

from awa.core.workflows.build_prompt_workflow import BuildPromptWorkflow
from awa.sdk import constants as sdk_constants
from awa.sdk.models.build_prompt_params import BuildPromptParams
from awa.sdk.models.input_params import InputParams


class TestBuildPromptWorkflow:
    """Test cases for BuildPromptWorkflow."""

    def test_workflow_class_exists(self) -> None:
        """Test that BuildPromptWorkflow class exists and is instantiable."""
        workflow = BuildPromptWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "run")

    @pytest.mark.asyncio
    async def test_run_with_direct_template_no_variables(self, workflow_client: Client) -> None:
        """Test workflow run with direct template and no variables."""
        task_queue_name = str(uuid.uuid4())
        template = "Hello World"
        expected_result = "Hello World"
        params = BuildPromptParams(template=template)

        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        resolve_template_mock.assert_called_once_with(template, {})

    @pytest.mark.asyncio
    async def test_run_with_direct_template_and_variables(self, workflow_client: Client) -> None:
        """Test workflow run with direct template and variables."""
        task_queue_name = str(uuid.uuid4())
        template = "Hello {{name}}"
        variables = {"name": "World"}
        expected_result = "Hello World"
        params = BuildPromptParams(template=template, variables=variables)

        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        resolve_template_mock.assert_called_once_with(template, variables)

    @pytest.mark.asyncio
    async def test_run_with_template_from_file(self, workflow_client: Client) -> None:
        """Test workflow run with template loaded from file."""
        task_queue_name = str(uuid.uuid4())
        template_content = "Hello {{name}}"
        template_input = InputParams(path="/path/to/template.txt", name="template")
        variables = {"name": "World"}
        expected_result = "Hello World"
        params = BuildPromptParams(template_input=template_input, variables=variables)

        read_file_mock = MagicMock(return_value=template_content)
        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        read_file_mock.assert_called_once_with(template_input)
        resolve_template_mock.assert_called_once_with(template_content, variables)

    @pytest.mark.asyncio
    async def test_run_with_output_file_writing(self, workflow_client: Client) -> None:
        """Test workflow run with output file writing."""
        task_queue_name = str(uuid.uuid4())
        template = "Hello World"
        output_path = "/path/to/output.txt"
        expected_result = "Hello World"
        params = BuildPromptParams(template=template, output_path=output_path)

        resolve_template_mock = MagicMock(return_value=expected_result)
        write_file_mock = MagicMock()

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def mock_write_file(path: str, content: str) -> None:
            write_file_mock(path, content)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_resolve_template, mock_write_file],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        resolve_template_mock.assert_called_once_with(template, {})
        write_file_mock.assert_called_once_with(output_path, expected_result)

    @pytest.mark.asyncio
    async def test_run_with_inputs_single_file(self, workflow_client: Client) -> None:
        """Test workflow run with single input file."""
        task_queue_name = str(uuid.uuid4())
        template = "Template: {{content}}"
        input_file = InputParams(path="/path/to/input.txt", name="content")
        input_content = "File content here"
        expected_result = "Template: File content here"
        params = BuildPromptParams(template=template, inputs=[input_file])

        read_file_mock = MagicMock(return_value=input_content)
        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        read_file_mock.assert_called_once_with(input_file)
        resolve_template_mock.assert_called_once_with(template, {"content": input_content})

    @pytest.mark.asyncio
    async def test_run_with_inputs_multiple_files(self, workflow_client: Client) -> None:
        """Test workflow run with multiple input files."""
        task_queue_name = str(uuid.uuid4())
        template = "File1: {{file1}}, File2: {{file2}}"
        input_file1 = InputParams(path="/path/to/file1.txt", name="file1")
        input_file2 = InputParams(path="/path/to/file2.txt", name="file2")
        file1_content = "Content of file 1"
        file2_content = "Content of file 2"
        expected_result = "File1: Content of file 1, File2: Content of file 2"
        params = BuildPromptParams(template=template, inputs=[input_file1, input_file2])

        read_file_calls = []

        def read_file_side_effect(input_params: InputParams) -> str:
            read_file_calls.append(input_params)
            if input_params.path == "/path/to/file1.txt":
                return file1_content
            if input_params.path == "/path/to/file2.txt":
                return file2_content
            raise ValueError(f"Unexpected file path: {input_params.path}")

        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_side_effect(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        assert len(read_file_calls) == 2
        expected_variables = {"file1": file1_content, "file2": file2_content}
        resolve_template_mock.assert_called_once_with(template, expected_variables)

    @pytest.mark.asyncio
    async def test_run_with_inputs_and_existing_variables(self, workflow_client: Client) -> None:
        """Test workflow run with input files and existing variables."""
        task_queue_name = str(uuid.uuid4())
        template = "Var: {{var}}, File: {{file_content}}"
        existing_variables = {"var": "existing_value"}
        input_file = InputParams(path="/path/to/file.txt", name="file_content")
        file_content = "File content"
        expected_result = "Var: existing_value, File: File content"
        params = BuildPromptParams(template=template, variables=existing_variables, inputs=[input_file])

        read_file_mock = MagicMock(return_value=file_content)
        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        expected_variables = {"var": "existing_value", "file_content": file_content}
        resolve_template_mock.assert_called_once_with(template, expected_variables)

    @pytest.mark.asyncio
    async def test_run_with_inputs_no_name_uses_default_naming(self, workflow_client: Client) -> None:
        """Test workflow run with input files that have no name specified."""
        task_queue_name = str(uuid.uuid4())
        template = "File: {{None}}"
        input_file = InputParams(path="/path/to/file.txt")  # No name specified
        file_content = "File content"
        expected_result = "File: File content"
        params = BuildPromptParams(template=template, inputs=[input_file])

        read_file_mock = MagicMock(return_value=file_content)
        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_mock(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        # The key should be None when no name is specified (but it gets serialized as "None" string)
        expected_variables = {"None": file_content}
        resolve_template_mock.assert_called_once_with(template, expected_variables)

    @pytest.mark.asyncio
    async def test_run_with_template_from_file_and_inputs(self, workflow_client: Client) -> None:
        """Test workflow run with template from file and additional input files."""
        task_queue_name = str(uuid.uuid4())
        template_content = "Template: {{content}}"
        template_input = InputParams(path="/path/to/template.txt", name="template")
        input_file = InputParams(path="/path/to/input.txt", name="content")
        input_content = "Input file content"
        expected_result = "Template: Input file content"
        params = BuildPromptParams(template_input=template_input, inputs=[input_file])

        read_file_calls = []

        def read_file_side_effect(input_params: InputParams) -> str:
            read_file_calls.append(input_params)
            if input_params.path == "/path/to/template.txt":
                return template_content
            if input_params.path == "/path/to/input.txt":
                return input_content
            raise ValueError(f"Unexpected file path: {input_params.path}")

        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_side_effect(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        assert len(read_file_calls) == 2
        expected_variables = {"content": input_content}
        resolve_template_mock.assert_called_once_with(template_content, expected_variables)

    @pytest.mark.asyncio
    async def test_run_with_empty_inputs_list(self, workflow_client: Client) -> None:
        """Test workflow run with empty inputs list."""
        task_queue_name = str(uuid.uuid4())
        template = "Hello World"
        expected_result = "Hello World"
        params = BuildPromptParams(template=template, inputs=[])  # Empty list

        resolve_template_mock = MagicMock(return_value=expected_result)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_resolve_template],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        resolve_template_mock.assert_called_once_with(template, {})

    @pytest.mark.asyncio
    async def test_run_with_complete_workflow_all_features(self, workflow_client: Client) -> None:
        """Test workflow run with all features: template from file, variables, inputs, and output."""
        task_queue_name = str(uuid.uuid4())
        template_content = "{{greeting}} {{name}}, here is the file content: {{file_content}}"
        template_input = InputParams(path="/path/to/template.txt", name="template")
        existing_variables = {"greeting": "Hello", "name": "World"}
        input_file = InputParams(path="/path/to/input.txt", name="file_content")
        input_content = "Important data"
        output_path = "/path/to/output.txt"
        expected_result = "Hello World, here is the file content: Important data"
        params = BuildPromptParams(
            template_input=template_input,
            variables=existing_variables,
            inputs=[input_file],
            output_path=output_path,
        )

        read_file_calls = []

        def read_file_side_effect(input_params: InputParams) -> str:
            read_file_calls.append(input_params)
            if input_params.path == "/path/to/template.txt":
                return template_content
            if input_params.path == "/path/to/input.txt":
                return input_content
            raise ValueError(f"Unexpected file path: {input_params.path}")

        resolve_template_mock = MagicMock(return_value=expected_result)
        write_file_mock = MagicMock()

        @activity.defn(name=sdk_constants.ACTIVITY_READ_FILE_OR_DIRECTORY)
        async def mock_read_file(input_params: InputParams) -> str:
            return read_file_side_effect(input_params)

        @activity.defn(name=sdk_constants.ACTIVITY_RESOLVE_TEMPLATE)
        async def mock_resolve_template(template_str: str, vars_dict: dict[str, Any]) -> str:
            return resolve_template_mock(template_str, vars_dict)

        @activity.defn(name=sdk_constants.ACTIVITY_WRITE_FILE)
        async def mock_write_file(path: str, content: str) -> None:
            write_file_mock(path, content)

        async with Worker(
            workflow_client,
            task_queue=task_queue_name,
            workflows=[BuildPromptWorkflow],
            activities=[mock_read_file, mock_resolve_template, mock_write_file],
        ):
            result = await workflow_client.execute_workflow(
                BuildPromptWorkflow.run,
                params,
                id=str(uuid.uuid4()),
                task_queue=task_queue_name,
            )

        assert result == expected_result
        assert len(read_file_calls) == 2
        expected_variables = {"greeting": "Hello", "name": "World", "file_content": input_content}
        resolve_template_mock.assert_called_once_with(template_content, expected_variables)
        write_file_mock.assert_called_once_with(output_path, expected_result)
