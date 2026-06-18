"""Unit tests for the run CLI command."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer.testing

from awa.core.cli.commands.run import _run, app


class TestRunCommand:
    """Test cases for run CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = typer.testing.CliRunner()

    @patch("awa.core.cli.commands.run.asyncio.run")
    @patch("awa.core.cli.commands.run.init_logging")
    def test_run_command_no_params(
        self,
        mock_init_logging: MagicMock,
        mock_asyncio_run: MagicMock,
    ) -> None:
        """Test run command with no parameters."""
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        result = self.runner.invoke(app, [])

        assert result.exit_code == 0
        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()

    @patch("awa.core.cli.commands.run.asyncio.run")
    @patch("awa.core.cli.commands.run.init_logging")
    def test_run_command_with_workflow(
        self,
        mock_init_logging: MagicMock,
        mock_asyncio_run: MagicMock,
    ) -> None:
        """Test run command with workflow parameter."""
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        result = self.runner.invoke(app, ["--workflow", "test_workflow"])

        assert result.exit_code == 0
        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()

    @patch("awa.core.cli.commands.run.asyncio.run")
    @patch("awa.core.cli.commands.run.init_logging")
    def test_run_command_with_workflow_and_input(
        self,
        mock_init_logging: MagicMock,
        mock_asyncio_run: MagicMock,
    ) -> None:
        """Test run command with workflow and input parameters."""
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        result = self.runner.invoke(
            app,
            [
                "--workflow",
                "test_workflow",
                "--input",
                "test_input",
                "--task-queue",
                "test_queue",
            ],
        )

        assert result.exit_code == 0
        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()

    @patch("awa.core.cli.commands.run.asyncio.run")
    @patch("awa.core.cli.commands.run.init_logging")
    def test_run_command_short_flags(
        self,
        mock_init_logging: MagicMock,
        mock_asyncio_run: MagicMock,
    ) -> None:
        """Test run command with short flags."""
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        result = self.runner.invoke(
            app,
            [
                "-w",
                "test_workflow",
                "-i",
                "test_input",
                "-q",
                "test_queue",
            ],
        )

        assert result.exit_code == 0
        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()

    def test_run_command_help(self) -> None:
        """Test the run command help output."""
        # Act
        result = self.runner.invoke(app, ["--help"])

        # Assert
        assert result.exit_code == 0
        assert "Run the AWA Engine, API, and UI" in result.stdout
        assert "--workflow" in result.stdout
        assert "--input" in result.stdout
        assert "--task-queue" in result.stdout


class TestRunAsyncFunction:
    """Test cases for the _run async function."""

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_with_workflow_success(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function with successful workflow execution."""
        # Arrange
        workflow_name = "test_workflow"
        workflow_input = '{"test": "data"}'
        task_queue = "test_queue"
        expected_output = {"result": "success"}

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager.execute_workflow.return_value = expected_output
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result = await _run(workflow_name, workflow_input, task_queue)

        # Assert
        assert result == expected_output
        mock_service_manager.execute_workflow.assert_called_once_with(
            workflow_name,
            workflow_input,
            task_queue,
        )
        mock_logger.info.assert_any_call("Executing workflow...")
        mock_logger.info.assert_any_call(f"Workflow output: {expected_output}")
        mock_logger.info.assert_any_call("Workflow execution complete.")
        mock_logger.info.assert_any_call("Exited.")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_with_workflow_minimal_params(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function with workflow but minimal parameters."""
        # Arrange
        workflow_name = "test_workflow"
        expected_output = {"result": "success"}

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager.execute_workflow.return_value = expected_output
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result = await _run(workflow_name)

        # Assert
        assert result == expected_output
        mock_service_manager.execute_workflow.assert_called_once_with(
            workflow_name,
            None,
            None,
        )
        mock_logger.info.assert_any_call("Executing workflow...")
        mock_logger.info.assert_any_call(f"Workflow output: {expected_output}")
        mock_logger.info.assert_any_call("Workflow execution complete.")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_without_workflow(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function without workflow (should show error)."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result = await _run()

        # Assert
        assert result is None
        mock_service_manager.execute_workflow.assert_not_called()
        mock_logger.error.assert_called_once_with(
            "No workflow specified. Use the `-w` flag to specify a workflow to run.",
        )
        mock_logger.info.assert_any_call("Exited.")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_with_empty_workflow(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function with empty string workflow."""
        # Arrange
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result = await _run("")

        # Assert
        assert result is None
        mock_service_manager.execute_workflow.assert_not_called()
        mock_logger.error.assert_called_once_with(
            "No workflow specified. Use the `-w` flag to specify a workflow to run.",
        )

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_with_none_workflow_result(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function when workflow execution returns None."""
        # Arrange
        workflow_name = "test_workflow"

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager.execute_workflow.return_value = None
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result = await _run(workflow_name)

        # Assert
        assert result is None
        mock_service_manager.execute_workflow.assert_called_once_with(
            workflow_name,
            None,
            None,
        )
        mock_logger.info.assert_any_call("Executing workflow...")
        mock_logger.info.assert_any_call("Workflow output: None")
        mock_logger.info.assert_any_call("Workflow execution complete.")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_workflow_execution_exception(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function when workflow execution raises an exception."""
        # Arrange
        workflow_name = "test_workflow"
        test_exception = Exception("Workflow execution failed")

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager.execute_workflow.side_effect = test_exception
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act & Assert
        with pytest.raises(Exception, match="Workflow execution failed"):
            await _run(workflow_name)

        mock_service_manager.execute_workflow.assert_called_once_with(
            workflow_name,
            None,
            None,
        )
        mock_logger.info.assert_any_call("Executing workflow...")

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    async def test_run_async_service_manager_creation_exception(
        self,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function when ServiceManager creation fails."""
        # Arrange
        workflow_name = "test_workflow"
        test_exception = Exception("ServiceManager creation failed")

        mock_service_manager_class.create = AsyncMock(side_effect=test_exception)

        # Act & Assert
        with pytest.raises(Exception, match="ServiceManager creation failed"):
            await _run(workflow_name)

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    @patch("awa.core.cli.commands.run.cli_constants")
    async def test_run_async_logs_intro_message(
        self,
        mock_cli_constants: MagicMock,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function logs the intro message."""
        # Arrange
        expected_intro = "Test Intro Message"
        mock_cli_constants.INTRO = expected_intro

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        await _run()

        # Assert
        mock_logger.info.assert_any_call(expected_intro)

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_with_complex_workflow_input(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function with complex JSON workflow input."""
        # Arrange
        workflow_name = "test_workflow"
        complex_input = '{"users": [{"name": "John", "age": 30}], "metadata": {"version": 1}}'
        expected_output = {"processed": True}

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager.execute_workflow.return_value = expected_output
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result = await _run(workflow_name, complex_input)

        # Assert
        assert result == expected_output
        mock_service_manager.execute_workflow.assert_called_once_with(
            workflow_name,
            complex_input,
            None,
        )

    @pytest.mark.asyncio
    @patch("awa.core.cli.commands.run.ServiceManager")
    @patch("awa.core.cli.commands.run.get_logger")
    async def test_run_async_return_type_annotation(
        self,
        mock_get_logger: MagicMock,
        mock_service_manager_class: MagicMock,
    ) -> None:
        """Test _run async function return type is correctly typed as Any."""
        # Arrange
        workflow_name = "test_workflow"
        expected_output: Any = {"result": "success", "data": [1, 2, 3]}

        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_service_manager = AsyncMock()
        mock_service_manager.execute_workflow.return_value = expected_output
        mock_service_manager_class.create = AsyncMock(return_value=mock_service_manager)

        # Act
        result: Any = await _run(workflow_name)

        # Assert
        assert result == expected_output
        assert isinstance(result, dict)


class TestRunCommandIntegration:
    """Integration-style tests for the run command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = typer.testing.CliRunner()

    @patch("awa.core.cli.commands.run.init_logging")
    @patch("awa.core.cli.commands.run.asyncio.run")
    def test_run_command_integration_with_workflow(
        self,
        mock_asyncio_run: MagicMock,
        mock_init_logging: MagicMock,
    ) -> None:
        """Test run command integration - ensures asyncio.run gets correct arguments."""
        # Arrange
        mock_init_logging.return_value = None

        # Capture the coroutine passed to asyncio.run
        captured_coroutine = None

        def capture_asyncio_run_call(coro: object) -> None:
            nonlocal captured_coroutine
            captured_coroutine = coro
            coro.close()

        mock_asyncio_run.side_effect = capture_asyncio_run_call

        # Act
        result = self.runner.invoke(app, ["--workflow", "test_workflow", "--input", "test_input"])

        # Assert
        assert result.exit_code == 0
        assert captured_coroutine is not None
        # Check that the captured coroutine is from the _run function
        assert captured_coroutine.cr_code.co_name == "_run"
        mock_init_logging.assert_called_once_with()
        mock_asyncio_run.assert_called_once()
