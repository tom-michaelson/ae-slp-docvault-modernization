from pydantic import BaseModel, Field, PrivateAttr, model_validator


class JiraToTestCasesInput(BaseModel):
    """Input model for JIRA to Test Cases workflow."""

    project_id: str = Field(
        ...,
        description="JIRA project ID (e.g., 'AWA', 'PROJ')",
    )
    key: str = Field(
        ...,
        description=(
            "Comma-separated JIRA issue keys. "
            "Examples: Single issue: AWA-191 | Multiple issues: AWA-191,AWA-192,AWA-193"
        ),
    )
    # Internal field - completely hidden from schema
    _issue_keys: list[str] = PrivateAttr(default_factory=list)
    exclude_edge_cases: bool = Field(
        default=False,
        description="Exclude edge case test scenarios - CHECK TO EXCLUDE",
    )
    exclude_negative_tests: bool = Field(
        default=False,
        description="Exclude negative test scenarios - CHECK TO EXCLUDE",
    )
    exclude_security_tests: bool = Field(
        default=False,
        description="Exclude security test scenarios - CHECK TO EXCLUDE",
    )
    # Test Case Priority Filters - check boxes to EXCLUDE priorities
    exclude_priority_p1: bool = Field(
        default=False,
        description="Exclude P1 (Critical) priority test cases - CHECK TO EXCLUDE",
    )
    exclude_priority_p2: bool = Field(
        default=False,
        description="Exclude P2 (High) priority test cases - CHECK TO EXCLUDE",
    )
    exclude_priority_p3: bool = Field(
        default=False,
        description="Exclude P3 (Medium) priority test cases - CHECK TO EXCLUDE",
    )
    csv_format: str = Field(
        default="standard",
        json_schema_extra={"default": "standard"},
        description="CSV format type: 'standard', 'ado', or 'testrail' (default: 'standard')",
    )
    max_issues: int = Field(
        default=50,
        json_schema_extra={"default": 50},
        description="Maximum number of issues to process (default: 50, max: 100)",
        ge=1,
        le=100,
    )

    @property
    def issue_keys(self) -> list[str]:
        """Get the processed issue keys list."""
        return self._issue_keys

    @property
    def include_edge_cases(self) -> bool:
        """Get whether edge cases should be included."""
        return not self.exclude_edge_cases

    @property
    def include_negative_tests(self) -> bool:
        """Get whether negative tests should be included."""
        return not self.exclude_negative_tests

    @property
    def include_security_tests(self) -> bool:
        """Get whether security tests should be included."""
        return not self.exclude_security_tests

    @property
    def test_case_priority(self) -> list[str]:
        """Get the list of selected priority levels."""
        priorities = []
        if not self.exclude_priority_p1:
            priorities.append("P1")
        if not self.exclude_priority_p2:
            priorities.append("P2")
        if not self.exclude_priority_p3:
            priorities.append("P3")
        return priorities

    @model_validator(mode="after")
    def process_issue_keys(self) -> "JiraToTestCasesInput":
        """Process issue keys from the 'key' field (comma-separated string)."""
        # Split by comma and clean each key
        keys_from_string = [k.strip() for k in self.key.split(",") if k.strip()]

        if not keys_from_string:
            raise ValueError("At least one valid issue key must be provided")

        # Clean and deduplicate issue keys
        seen = set()
        unique_keys = []
        for original_key in keys_from_string:
            cleaned_key = original_key.strip().upper()  # Normalize to uppercase
            if cleaned_key and cleaned_key not in seen:
                seen.add(cleaned_key)
                unique_keys.append(cleaned_key)

        if not unique_keys:
            raise ValueError("At least one valid issue key must be provided")

        self._issue_keys = unique_keys
        return self
