"""Workflow test utilities for test case management and discovery.

This module provides utilities for automatically discovering and loading
test cases from individual test case files, supporting the refactored
workflow test structure.
"""

import importlib
import pkgutil
from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from tests.models import WorkflowTestCase


def load_test_cases() -> list[tuple[str, BaseModel, list[str] | None]]:
    """Automatically discover and load all test cases from test case files.

    Discovers all Python modules in tests.workflow.test_cases package and imports
    test cases from them. Supports both single test cases (exported as 'test_case')
    and multiple test cases (exported as 'test_cases' list).

    Returns:
        List of tuples in format: (workflow_name, input_data, custom_text_assertions)

    """
    test_cases = []
    test_cases_package = "tests.workflow.test_cases"

    try:
        # Get the test_cases package
        package = importlib.import_module(test_cases_package)
        package_path = Path(package.__path__[0])

        # Discover all Python modules in the test_cases package
        for module_info in pkgutil.iter_modules([str(package_path)]):
            if module_info.name.endswith("_cases"):  # Only import *_cases.py files
                module_name = f"{test_cases_package}.{module_info.name}"

                try:
                    # Import the module
                    module = importlib.import_module(module_name)

                    # Try to get single test case first
                    if hasattr(module, "test_case"):
                        case = module.test_case
                        if isinstance(case, WorkflowTestCase):
                            # Use Pydantic model attributes directly
                            test_cases.append(
                                (
                                    case.workflow_name,
                                    case.input_data,
                                    case.custom_text_assertions,
                                ),
                            )

                    # Try to get multiple test cases
                    if hasattr(module, "test_cases"):
                        cases = module.test_cases
                        # Use list comprehension and extend for performance
                        test_cases.extend(
                            [
                                (
                                    case.workflow_name,
                                    case.input_data,
                                    case.custom_text_assertions,
                                )
                                for case in cases
                                if isinstance(case, WorkflowTestCase)
                            ],
                        )

                except ImportError as e:
                    logger.warning(f"Could not import test case module {module_name}: {e}")
                    continue
                except (KeyError, AttributeError) as e:
                    logger.warning(f"Invalid test case structure in {module_name}: {e}")
                    continue

    except ImportError as e:
        logger.error(f"Could not import test cases package {test_cases_package}: {e}")
        return []

    return test_cases
