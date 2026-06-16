#!/usr/bin/env python3
"""Pre-commit hook script to enforce SDK utils naming convention.

This script ensures that:
1. All utility functions in awa/sdk/utils/activity/ have an "_activity" suffix
2. All utility functions in awa/sdk/utils/workflow/ have a "_workflow" suffix
3. All file names match their corresponding function names
4. Functions without suffixes are allowed only if they are not async utility functions
"""

import re
import sys
from pathlib import Path


def check_activity_functions(file_path: Path) -> list[str]:
    """Check that activity utility functions have _activity suffix."""
    errors = []

    if not file_path.exists():
        return errors

    content = file_path.read_text()

    # Find all async function definitions
    async_functions = re.findall(r"^async def (\w+)\(", content, re.MULTILINE)

    # Check that async functions have _activity suffix
    for func_name in async_functions:
        if not func_name.endswith("_activity"):
            errors.append(f"{file_path}: Function '{func_name}' should have '_activity' suffix")  # noqa: PERF401

    # Check that filename matches function name (for single-function files)
    if len(async_functions) == 1:
        func_name = async_functions[0]
        expected_filename = f"{func_name}.py"
        if file_path.name != expected_filename:
            errors.append(f"{file_path}: Filename should be '{expected_filename}' to match function '{func_name}'")

    return errors


def check_workflow_functions(file_path: Path) -> list[str]:
    """Check that workflow utility functions have _workflow suffix."""
    errors = []

    if not file_path.exists():
        return errors

    content = file_path.read_text()

    # Find all async function definitions
    async_functions = re.findall(r"^async def (\w+)\(", content, re.MULTILINE)

    # Check that async functions have _workflow suffix
    for func_name in async_functions:
        if not func_name.endswith("_workflow"):
            errors.append(f"{file_path}: Function '{func_name}' should have '_workflow' suffix")  # noqa: PERF401

    # Check that filename matches function name (for single-function files)
    if len(async_functions) == 1:
        func_name = async_functions[0]
        expected_filename = f"{func_name}.py"
        if file_path.name != expected_filename:
            errors.append(f"{file_path}: Filename should be '{expected_filename}' to match function '{func_name}'")

    return errors


def check_sdk_utils_naming() -> tuple[bool, list[str]]:
    """Check SDK utils naming convention across all relevant files."""
    errors = []

    # Find project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Check activity utils
    activity_utils_dir = project_root / "awa" / "sdk" / "utils" / "activity"
    if activity_utils_dir.exists():
        for py_file in activity_utils_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                errors.extend(check_activity_functions(py_file))

    # Check workflow utils
    workflow_utils_dir = project_root / "awa" / "sdk" / "utils" / "workflow"
    if workflow_utils_dir.exists():
        for py_file in workflow_utils_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                errors.extend(check_workflow_functions(py_file))

    return len(errors) == 0, errors


def main() -> int:
    """Serve as the main entry point for the pre-commit hook."""
    success, errors = check_sdk_utils_naming()

    if not success:
        print("❌ SDK Utils Naming Convention Violations:")
        for error in errors:
            print(f"  {error}")
        print()
        print("📋 Naming Convention Rules:")
        print("  • Activity utility functions must end with '_activity'")
        print("  • Workflow utility functions must end with '_workflow'")
        print("  • File names must match their function names")
        print("  • Example: async def read_file_activity() → read_file_activity.py")
        print("  • Example: async def execute_agent_workflow() → execute_agent_workflow.py")
        return 1

    print("✅ SDK Utils naming convention check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
