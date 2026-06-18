"""Tests to validate project structure and configuration."""

import os
import subprocess
from pathlib import Path

import pytest

from awa.sdk.constants import AWA_DEFAULT_TASK_QUEUE


def test_unit_tests_directory_exists() -> None:
    """Test that the unit tests directory exists."""
    unit_test_dir = Path("tests/unit")
    assert unit_test_dir.exists(), "tests/unit directory should exist"
    assert unit_test_dir.is_dir(), "tests/unit should be a directory"


def test_pytest_ini_configuration() -> None:
    """Test that pytest.ini is configured correctly."""
    pytest_ini = Path("pytest.ini")
    assert pytest_ini.exists(), "pytest.ini should exist"

    content = pytest_ini.read_text()
    assert "testpaths =" in content, "pytest.ini should define testpaths"
    assert "tests" in content, "pytest.ini should point to tests"


def test_makefile_test_target() -> None:
    """Test that Makefile test target is configured correctly."""
    makefile = Path("Makefile") if Path("Makefile").exists() else Path("makefile")
    assert makefile.exists(), "Makefile should exist"

    content = makefile.read_text()
    assert "tests/unit" in content, "Makefile should reference tests/unit"
    assert "uv run -m pytest" in content, "Makefile should use uv run -m pytest"


def test_unit_test_files_exist() -> None:
    """Test that unit test files exist in the correct location."""
    unit_test_dir = Path("tests/unit")
    test_files = list(unit_test_dir.glob("**/test_*.py"))

    assert len(test_files) > 0, "Should have test files in tests/unit"
    assert any(f.name == "test_constants.py" for f in test_files), "Should have test_constants.py"


def test_test_discovery_works() -> None:
    """Test that pytest can discover tests in the unit directory."""
    # This test validates that our configuration works for test discovery

    result = subprocess.run(  # noqa: S603, RUF100
        ["uv", "run", "-m", "pytest", "--collect-only", "-q", "tests/unit/"],  # noqa: S607
        check=False,
        capture_output=True,
        text=True,
        cwd=Path.cwd(),
    )

    assert result.returncode == 0, f"Test discovery failed: {result.stderr}"
    assert "test session starts" in result.stdout or result.stdout.strip() != "", "Should discover tests"


@pytest.mark.skipif(
    os.getenv("CI") is not None,
    reason="Skipping environment validation in CI",
)
def test_project_root_structure() -> None:
    """Test that we're running tests from the correct project root."""
    # Verify we have the expected project structure
    expected_dirs = [
        "cookbook/recipes/workflows",
        "cookbook/recipes/utilities",
        "cookbook/recipes/models",
        "cookbook/recipes/activities",
    ]

    for dir_name in expected_dirs:
        assert Path(dir_name).exists(), f"Project should have {dir_name} directory"
        assert Path(dir_name).is_dir(), f"{dir_name} should be a directory"


def test_imports_work_from_unit_tests() -> None:
    """Test that imports work correctly from the unit test directory."""
    # This validates that our Python path configuration is correct
    try:
        assert AWA_DEFAULT_TASK_QUEUE == "awa_default"
    except ImportError as e:
        pytest.fail(f"Import failed from unit tests: {e}")
