"""Unit tests for the workflows CLI command."""

import json
from unittest.mock import MagicMock, patch

import pytest
import typer.testing

from awa.core.cli.commands.workflows import _list_workflows, app
from awa.core.utils.workflow_metadata import ParameterInfo, WorkflowMetadata


class TestWorkflowsCommand:
    """Test cases for workflows CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = typer.testing.CliRunner()

    def test_list_workflows_command_help(self) -> None:
        """Test the list workflows command help output."""
        result = self.runner.invoke(app, ["list", "--help"])

        assert result.exit_code == 0
        assert "List all available workflows" in result.stdout
        assert "--json" in result.stdout

    def test_workflows_command_help(self) -> None:
        """Test the main workflows command help output."""
        result = self.runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "workflows" in result.stdout


class TestListWorkflowsAsyncFunction:
    """Test cases for the _list_workflows async function."""

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_success_table_format(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test successful workflow listing in table format."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_metadata = [
            WorkflowMetadata(
                name="TestWorkflow1",
                class_name="TestWorkflow1",
                module="test.module1",
                parameters=["param1", "param2"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                    ParameterInfo(name="param2", type_str="int"),
                ],
            ),
            WorkflowMetadata(
                name="TestWorkflow2",
                class_name="TestWorkflow2",
                module="test.module2",
                parameters=[],
                parameter_info=[],
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Act
        await _list_workflows(json_output=False)

        # Assert
        mock_get_metadata.assert_called_once()
        mock_logger.info.assert_called_once_with("Found 2 workflows")
        mock_console.print.assert_called()

        # Check that print was called with a table (Rich Table object)
        print_calls = mock_console.print.call_args_list
        assert len(print_calls) == 1
        printed_arg = print_calls[0][0][0]
        assert hasattr(printed_arg, "add_row")  # Rich Table has add_row method

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_success_json_format(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test successful workflow listing in JSON format."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_metadata = [
            WorkflowMetadata(
                name="TestWorkflow1",
                class_name="TestWorkflow1",
                module="test.module1",
                parameters=["param1", "param2"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                    ParameterInfo(name="param2", type_str="int"),
                ],
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Act
        await _list_workflows(json_output=True)

        # Assert
        mock_get_metadata.assert_called_once()
        mock_logger.info.assert_called_once_with("Found 1 workflows")
        mock_console.print.assert_called_once()

        # Check that JSON was printed
        printed_json = mock_console.print.call_args[0][0]
        parsed_json = json.loads(printed_json)
        assert "workflows" in parsed_json
        assert len(parsed_json["workflows"]) == 1
        assert parsed_json["workflows"][0]["name"] == "TestWorkflow1"
        assert parsed_json["workflows"][0]["module"] == "test.module1"
        assert parsed_json["workflows"][0]["parameters"] == {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_empty_list_table_format(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test workflow listing with empty results in table format."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_get_metadata.return_value = []
        mock_format_metadata.return_value = {}

        # Act
        await _list_workflows(json_output=False)

        # Assert
        mock_get_metadata.assert_called_once()
        mock_logger.info.assert_called_once_with("Found 0 workflows")
        mock_console.print.assert_called_once_with("No workflows found.")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_empty_list_json_format(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test workflow listing with empty results in JSON format."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_get_metadata.return_value = []
        mock_format_metadata.return_value = {}

        # Act
        await _list_workflows(json_output=True)

        # Assert
        mock_get_metadata.assert_called_once()
        mock_logger.info.assert_called_once_with("Found 0 workflows")
        mock_console.print.assert_called_once()

        # Check that empty JSON was printed
        printed_json = mock_console.print.call_args[0][0]
        parsed_json = json.loads(printed_json)
        assert "workflows" in parsed_json
        assert len(parsed_json["workflows"]) == 0

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_no_parameters(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test workflow listing with workflows that have no parameters."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_metadata = [
            WorkflowMetadata(
                name="NoParamWorkflow",
                class_name="NoParamWorkflow",
                module="test.module",
                parameters=[],
                parameter_info=[],
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Act
        await _list_workflows(json_output=False)

        # Assert
        mock_get_metadata.assert_called_once()
        mock_logger.info.assert_called_once_with("Found 1 workflows")
        mock_console.print.assert_called()

        # Check that "None" is displayed for empty parameters
        print_calls = mock_console.print.call_args_list
        assert len(print_calls) == 1

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_discovery_failure(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test handling of workflow discovery failures."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_get_metadata.side_effect = Exception("Discovery failed")
        mock_format_metadata.return_value = {}

        # Act & Assert
        with pytest.raises(typer.Exit) as exc_info:
            await _list_workflows(json_output=False)

        assert exc_info.value.exit_code == 1
        mock_get_metadata.assert_called_once()
        mock_logger.exception.assert_called_once_with("Failed to list workflows")
        mock_console.print.assert_called_once()

        # Check that error message was printed
        error_message = mock_console.print.call_args[0][0]
        assert "[red]Error: Failed to list workflows: Discovery failed[/red]" in error_message

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_runtime_error(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test handling of runtime errors during workflow listing."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_get_metadata.side_effect = RuntimeError("Runtime error occurred")
        mock_format_metadata.return_value = {}

        # Act & Assert
        with pytest.raises(typer.Exit) as exc_info:
            await _list_workflows(json_output=False)

        assert exc_info.value.exit_code == 1
        mock_get_metadata.assert_called_once()
        mock_logger.exception.assert_called_once_with("Failed to list workflows")
        mock_console.print.assert_called_once()

        # Check that error message was printed
        error_message = mock_console.print.call_args[0][0]
        assert "[red]Error: Failed to list workflows: Runtime error occurred[/red]" in error_message

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_complex_parameters(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test workflow listing with complex parameter names."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_metadata = [
            WorkflowMetadata(
                name="ComplexWorkflow",
                class_name="ComplexWorkflow",
                module="complex.module",
                parameters=["request_data", "config_settings", "user_context"],
                parameter_info=[
                    ParameterInfo(name="request_data", type_str="RequestData"),
                    ParameterInfo(name="config_settings", type_str="ConfigSettings"),
                    ParameterInfo(name="user_context", type_str="UserContext"),
                ],
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Act
        await _list_workflows(json_output=True)

        # Assert
        mock_get_metadata.assert_called_once()
        mock_logger.info.assert_called_once_with("Found 1 workflows")
        mock_console.print.assert_called_once()

        # Check that JSON contains complex parameters
        printed_json = mock_console.print.call_args[0][0]
        parsed_json = json.loads(printed_json)
        workflow = parsed_json["workflows"][0]
        assert "type" in workflow["parameters"]

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_json_format_structure(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that JSON output has the correct structure."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_metadata = [
            WorkflowMetadata(
                name="TestWorkflow",
                class_name="TestWorkflow",
                module="test.module",
                parameters=["param1"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                ],
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Act
        await _list_workflows(json_output=True)

        # Assert
        printed_json = mock_console.print.call_args[0][0]
        parsed_json = json.loads(printed_json)

        # Check root structure
        assert "workflows" in parsed_json
        assert isinstance(parsed_json["workflows"], list)

        # Check workflow structure
        workflow = parsed_json["workflows"][0]
        assert "name" in workflow
        assert "module" in workflow
        assert "parameters" in workflow
        assert isinstance(workflow["parameters"], dict)

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.workflows.get_workflow_metadata")
    @patch("awa.core.cli.commands.workflows.format_workflow_parameters")
    @patch("awa.core.cli.commands.workflows.get_logger")
    @patch("awa.core.cli.commands.workflows.console")
    async def test_list_workflows_json_indentation(
        self,
        mock_console: MagicMock,
        mock_get_logger: MagicMock,
        mock_format_metadata: MagicMock,
        mock_get_metadata: MagicMock,
    ) -> None:
        """Test that JSON output is properly indented."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_metadata = [
            WorkflowMetadata(
                name="TestWorkflow",
                class_name="TestWorkflow",
                module="test.module",
                parameters=["param1"],
                parameter_info=[
                    ParameterInfo(name="param1", type_str="str"),
                ],
            ),
        ]
        mock_get_metadata.return_value = mock_metadata
        mock_formatted_metadata = {
            "type": "object",
            "properties": {
                "template": {
                    "title": "Template",
                    "type": "string",
                },
            },
        }
        mock_format_metadata.return_value = mock_formatted_metadata

        # Act
        await _list_workflows(json_output=True)

        # Assert
        printed_json = mock_console.print.call_args[0][0]

        # Check that JSON is indented (contains newlines and spaces)
        assert "\n" in printed_json
        assert "  " in printed_json  # 2-space indentation

        # Verify it's valid JSON
        parsed_json = json.loads(printed_json)
        assert isinstance(parsed_json, dict)
