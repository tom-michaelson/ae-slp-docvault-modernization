from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from awa.core.cli.commands.docs import app, docs, docs_async


class TestDocsCommand:
    """Test cases for docs CLI command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_docs_command_exists(self) -> None:
        """Test that the docs command app exists."""
        assert app is not None

    def test_docs_function_exists(self) -> None:
        """Test that docs functions exist."""
        assert docs is not None
        assert docs_async is not None

    @patch("awa.core.cli.commands.docs.asyncio.run")
    @patch("awa.core.cli.commands.docs.init_logging")
    def test_docs_calls_asyncio_run(self, mock_init_logging: MagicMock, mock_asyncio_run: MagicMock) -> None:
        """Test that docs function calls asyncio.run wrapper."""
        # Arrange
        mock_init_logging.return_value = None

        def close_coroutine(coro: object) -> None:
            coro.close()

        mock_asyncio_run.side_effect = close_coroutine

        # Act
        docs()

        # Assert
        mock_init_logging.assert_called_once()
        mock_asyncio_run.assert_called_once()

    def test_docs_help(self) -> None:
        """Test docs command help."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "docs" in result.stdout.lower()

    @patch("awa.core.cli.commands.docs.CommandUtils.run_command_async")
    async def test_docs_async_function(self, mock_run_command: MagicMock) -> None:
        """Test the docs_async function."""
        # Arrange
        mock_run_command.return_value = None

        # Act
        await docs_async()

        # Assert
        mock_run_command.assert_called_once_with(command="pnpm run docs:dev")
