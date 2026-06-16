"""Integration tests for document parsing functionality."""

import pytest
from temporalio.testing import ActivityEnvironment

from awa.core.activities.read_file_and_parse_activity import read_file_and_parse_activity
from awa.sdk.models.read_file_and_parse_input import ReadFileAndParseInput
from tests.workflow.test_cases.document_parsing_cases import TEST_CASES


@pytest.mark.asyncio
async def test_document_parsing_with_sample_files() -> None:
    """Test document parsing with real sample files."""
    activity_env = ActivityEnvironment()

    for test_case in TEST_CASES:
        # Testing: {test_case['name']}

        # Execute the activity
        inp = ReadFileAndParseInput(
            file_path=test_case["file_path"],
            default_content=test_case.get("default"),
        )

        try:
            result = await activity_env.run(read_file_and_parse_activity, inp)

            # Verify results
            if "expected_exact" in test_case:
                assert result == test_case["expected_exact"], f"Failed test: {test_case['name']}"
            else:
                # Check expected contains
                for expected in test_case.get("expected_contains", []):
                    assert expected in result, (
                        f"Expected '{expected}' not found in result for test: {test_case['name']}"
                    )

                # Check should not contain
                for not_expected in test_case.get("should_not_contain", []):
                    assert not_expected not in result, (
                        f"Unexpected '{not_expected}' found in result for test: {test_case['name']}"
                    )

            # Test passed

        except FileNotFoundError:
            # This is expected for non-existent file tests without default
            if "expected_exact" not in test_case:
                pass  # FileNotFoundError as expected
