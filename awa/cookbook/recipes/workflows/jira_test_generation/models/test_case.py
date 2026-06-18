from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """Model representing a single test case."""

    test_id: str = Field(
        ...,
        description="Unique identifier for the test case",
    )
    jira_issue: str = Field(
        ...,
        description="JIRA issue key this test case relates to",
    )
    test_name: str = Field(
        ...,
        description="Descriptive name for the test case",
    )
    test_type: str = Field(
        ...,
        description="Type of test: Functional, API, UI, Integration, Security, Performance, etc.",
    )
    priority: str = Field(
        ...,
        description="Priority level: P1, P2, P3",
    )
    preconditions: str = Field(
        default="",
        description="Preconditions that must be met before test execution",
    )
    test_steps: str = Field(
        ...,
        description="Pipe-separated test steps",
    )
    expected_results: str = Field(
        ...,
        description="Pipe-separated expected results",
    )
    test_data: str = Field(
        default="",
        description="Test data in key:value format, pipe-separated",
    )
    tags: str = Field(
        default="",
        description="Comma-separated tags for test categorization",
    )
    automation_status: str = Field(
        default="Ready for Automation",
        description="Automation readiness: 'Ready for Automation', 'Manual Only', 'Needs Review'",
    )


class TestSuite(BaseModel):
    """Collection of test cases for a JIRA issue."""

    jira_issue_key: str = Field(
        ...,
        description="JIRA issue key",
    )
    issue_summary: str = Field(
        ...,
        description="JIRA issue summary",
    )
    test_cases: list[TestCase] = Field(
        default_factory=list,
        description="List of test cases for this issue",
    )
    coverage_summary: str = Field(
        default="",
        description="Summary of test coverage for this issue",
    )
