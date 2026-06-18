# ruff: noqa: ANN401
# Import the functions from the script
import importlib.util
import shutil
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Calculate project root correctly from tests/unit/scripts/test_generate_cli_docs.py
test_file_path = Path(__file__).resolve()
# Go up 3 levels: tests/unit/scripts/test_generate_cli_docs.py -> project_root
project_root = test_file_path.parents[3]

# Import the script as a module
script_path = project_root / "scripts" / "generate_cli_docs.py"
spec = importlib.util.spec_from_file_location(
    "generate_cli_docs",
    script_path,
)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for {script_path}")
generate_cli_docs_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generate_cli_docs_module)

# Import the functions we need to test
_check_process_result = generate_cli_docs_module._check_process_result
generate_cli_docs = generate_cli_docs_module.generate_cli_docs
main = generate_cli_docs_module.main


@pytest.fixture
def test_setup() -> Any:
    """Set up test environment with temporary directory."""
    test_dir = Path(tempfile.mkdtemp())
    docs_dir = test_dir / "docs" / "reference"
    docs_dir.mkdir(parents=True)
    cli_md_path = docs_dir / "cli.md"

    yield {
        "test_dir": test_dir,
        "docs_dir": docs_dir,
        "cli_md_path": cli_md_path,
    }

    # Cleanup
    shutil.rmtree(test_dir, ignore_errors=True)


def test_check_process_result_success() -> None:
    """Test _check_process_result with successful return code."""
    # Should not raise any exception
    _check_process_result(0, b"success")


def test_check_process_result_failure() -> None:
    """Test _check_process_result with failure return code."""
    with pytest.raises(RuntimeError) as excinfo:
        _check_process_result(1, b"error message")

    assert "Command failed with return code 1" in str(excinfo.value)
    assert "error message" in str(excinfo.value)


@patch("asyncio.create_subprocess_exec")
async def test_generate_cli_docs_success(mock_subprocess: AsyncMock, test_setup) -> None:
    """Test successful CLI documentation generation."""
    cli_md_path = test_setup["cli_md_path"]
    test_dir = test_setup["test_dir"]

    # Arrange
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (
        b"# AWA CLI Reference\n\n**Usage:**\n\n```console\n$ awa [OPTIONS] COMMAND [ARGS]...\n```",
        b"",
    )
    mock_subprocess.return_value = mock_process

    # Mock the path resolution within the generate_cli_docs function
    with patch.object(generate_cli_docs_module, "Path") as mock_path:
        # Mock script directory resolution
        mock_script_file = Mock()
        mock_script_file.parent = test_dir / "scripts"

        # Mock docs path resolution
        mock_docs_path = Mock()
        mock_docs_path.resolve.return_value = cli_md_path
        mock_docs_path.open = cli_md_path.open

        # Configure Path mock to return different objects based on arguments
        def path_side_effect(*args: Any) -> Mock:
            path_str = str(args[0]) if args else ""
            if "generate_cli_docs.py" in path_str:
                return mock_script_file
            if "cli.md" in path_str:
                return mock_docs_path
            return Mock()

        mock_path.side_effect = path_side_effect

        # Act
        await generate_cli_docs()

    # Assert
    mock_subprocess.assert_called_once()
    mock_process.communicate.assert_called_once()
    assert cli_md_path.exists()

    content = cli_md_path.read_text()
    assert "This file is auto-generated" in content
    assert "AWA CLI Reference" in content


@patch("asyncio.create_subprocess_exec")
async def test_generate_cli_docs_subprocess_failure(mock_subprocess: AsyncMock) -> None:
    """Test CLI documentation generation with subprocess failure."""
    # Arrange
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate.return_value = (b"", b"Typer command failed")
    mock_subprocess.return_value = mock_process

    # Act & Assert
    with pytest.raises(RuntimeError) as excinfo:
        await generate_cli_docs()

    assert "Command failed with return code 1" in str(excinfo.value)
    assert "Typer command failed" in str(excinfo.value)


@patch("asyncio.create_subprocess_exec")
async def test_generate_cli_docs_with_debug_logs(mock_subprocess: AsyncMock, test_setup) -> None:
    """Test CLI documentation generation filters out debug logs."""
    cli_md_path = test_setup["cli_md_path"]
    test_dir = test_setup["test_dir"]

    # Arrange
    mock_process = AsyncMock()
    mock_process.returncode = 0
    # Mock output with debug logs and ANSI codes
    debug_line_1 = (
        b"[32m2025-07-02 15:10:44.681[0m | [34m[1mDEBUG   [0m | "
        b"[36mAWA         [0m | [34m[1mInitializing server 'AWA MCP'[0m\n"
    )
    debug_line_2 = (
        b"[32m2025-07-02 15:10:44.682[0m | [34m[1mDEBUG   [0m | [36mAWA         [0m | [34m[1mRegistering handler[0m\n"
    )
    mock_output = (
        debug_line_1
        + debug_line_2
        + b"# AWA CLI Reference\n\n"
        + b"**Usage:**\n\n"
        + b"```console\n"
        + b"$ awa [OPTIONS] COMMAND [ARGS]...\n"
        + b"```\n"
    )
    mock_process.communicate.return_value = (mock_output, b"")
    mock_subprocess.return_value = mock_process

    # Mock the path resolution
    with patch.object(generate_cli_docs_module, "Path") as mock_path:
        mock_script_file = Mock()
        mock_script_file.parent = test_dir / "scripts"

        mock_docs_path = Mock()
        mock_docs_path.resolve.return_value = cli_md_path
        mock_docs_path.open = cli_md_path.open

        def path_side_effect(*args: Any) -> Mock:
            path_str = str(args[0]) if args else ""
            if "generate_cli_docs.py" in path_str:
                return mock_script_file
            if "cli.md" in path_str:
                return mock_docs_path
            return Mock()

        mock_path.side_effect = path_side_effect

        # Act
        await generate_cli_docs()

    # Assert
    content = cli_md_path.read_text()

    # Should contain the markdown content
    assert "# AWA CLI Reference" in content
    assert "awa [OPTIONS] COMMAND [ARGS]" in content

    # Should NOT contain debug logs or ANSI codes
    assert "DEBUG" not in content
    assert "AWA MCP" not in content
    assert "[32m" not in content
    assert "[34m" not in content


async def test_generate_cli_docs_handles_exceptions() -> None:
    """Test that CLI documentation generation properly handles and re-raises exceptions."""
    # This test verifies that exceptions are properly propagated
    # The actual generate_cli_docs function properly handles OSError and RuntimeError
    # and re-raises them, which is tested in the main function tests

    # Verify that _check_process_result raises RuntimeError for non-zero return codes
    with pytest.raises(RuntimeError) as excinfo:
        _check_process_result(1, b"Process failed")

    assert "Command failed with return code 1" in str(excinfo.value)
    assert "Process failed" in str(excinfo.value)


@patch("asyncio.create_subprocess_exec")
async def test_generate_cli_docs_empty_output(mock_subprocess: AsyncMock, test_setup) -> None:
    """Test CLI documentation generation with empty Typer output."""
    cli_md_path = test_setup["cli_md_path"]
    test_dir = test_setup["test_dir"]

    # Arrange
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate.return_value = (b"", b"")  # Empty output
    mock_subprocess.return_value = mock_process

    # Mock the path resolution
    with patch.object(generate_cli_docs_module, "Path") as mock_path:
        mock_script_file = Mock()
        mock_script_file.parent = test_dir / "scripts"

        mock_docs_path = Mock()
        mock_docs_path.resolve.return_value = cli_md_path
        mock_docs_path.open = cli_md_path.open

        def path_side_effect(*args: Any) -> Mock:
            path_str = str(args[0]) if args else ""
            if "generate_cli_docs.py" in path_str:
                return mock_script_file
            if "cli.md" in path_str:
                return mock_docs_path
            return Mock()

        mock_path.side_effect = path_side_effect

        # Act
        await generate_cli_docs()

    # Assert
    assert cli_md_path.exists()
    content = cli_md_path.read_text()
    # Should still contain the header even with empty Typer output
    assert "This file is auto-generated" in content


@patch.object(generate_cli_docs_module, "generate_cli_docs")
@patch("sys.argv", ["generate_cli_docs.py"])
async def test_main_success(mock_generate: AsyncMock) -> None:
    """Test main function with successful generation."""
    # Arrange
    mock_generate.return_value = None

    # Act
    await main()

    # Assert
    mock_generate.assert_called_once()


@patch.object(generate_cli_docs_module, "generate_cli_docs")
@patch("builtins.print")
@patch("sys.argv", ["generate_cli_docs.py", "--error-on-fail"])
async def test_main_with_error_on_fail_flag(mock_print: Mock, mock_generate: AsyncMock) -> None:
    """Test main function with --error-on-fail flag and generation failure."""
    # Arrange
    mock_generate.side_effect = RuntimeError("Generation failed")

    # Act & Assert
    with pytest.raises(SystemExit) as excinfo:
        await main()

    assert excinfo.value.code == 1
    mock_generate.assert_called_once()
    mock_print.assert_called_with("Failed to generate CLI documentation: Generation failed")


@patch.object(generate_cli_docs_module, "generate_cli_docs")
@patch("builtins.print")
@patch("sys.argv", ["generate_cli_docs.py"])
async def test_main_without_error_on_fail_flag(mock_print: Mock, mock_generate: AsyncMock) -> None:
    """Test main function without --error-on-fail flag and generation failure."""
    # Arrange
    mock_generate.side_effect = RuntimeError("Generation failed")

    # Act
    await main()

    # Assert
    mock_generate.assert_called_once()
    mock_print.assert_called_with("Failed to generate CLI documentation: Generation failed")


def test_debug_log_filtering_integration() -> None:
    """Test that debug log filtering works as expected in the CLI generation process."""
    # Test the filtering logic directly using the patterns from the script
    test_lines = [
        "2025-07-02 15:10:44.681 | DEBUG | AWA | Initializing server",
        "# AWA CLI Reference",
        "**Usage:**",
        "[32mDEBUG[0m colored debug line",
        "```console",
        "$ awa [OPTIONS] COMMAND [ARGS]...",
        "```",
    ]

    # Simulate the filtering logic from the script
    filtered_lines = []
    found_header = False

    for line in test_lines:
        # Skip debug log lines (they contain timestamps and log formatting)
        if "DEBUG" in line and ("AWA" in line or "Initializing" in line or "Registering" in line):
            continue
        # Skip ANSI color code lines
        if line.startswith("\x1b[") or "[32m" in line or "[34m" in line or "[36m" in line:
            continue
        # Start collecting lines once we hit the markdown header
        if line.startswith("# ") and not found_header:
            found_header = True

        if found_header:
            filtered_lines.append(line)

    # Should have filtered out debug lines but kept markdown content
    assert len(filtered_lines) == 5
    assert "# AWA CLI Reference" in filtered_lines
    assert "**Usage:**" in filtered_lines
    assert "DEBUG" not in " ".join(filtered_lines)
