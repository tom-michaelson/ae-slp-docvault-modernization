class GenerateTestCasesRequest {
    issue JiraIssueForTesting
    include_edge_cases bool
    include_negative_tests bool
    include_security_tests bool
    test_priorities string[]
    business_context string? @description("Additional business context or domain information")
    related_systems string[]? @description("Related systems, APIs, or components affected")
    dependencies string[]? @description("External dependencies that may need mocking or setup")
}

class JiraIssueForTesting {
    key string
    summary string
    description string?
    issue_type string
    priority string
    acceptance_criteria string[]? @description("Specific acceptance criteria or success conditions")
    components string[]? @description("JIRA components or system areas affected")
    labels string[]? @description("JIRA labels for categorization")
    story_points int? @description("Story points indicating complexity")
    epic_link string? @description("Epic or parent issue this belongs to")
}

class TestCaseData {
    name string @description("Descriptive test case name")
    category string @description("Test category: Functional, Integration, UI, API, Database, Security, Performance, Usability")
    type string @description("Test type: Positive, Negative, Boundary, Error Handling")
    priority string @description("Priority level: P1, P2, or P3")
    requirement_traceability string[] @description("Which acceptance criteria or requirements this test verifies")
    preconditions string[] @description("Setup requirements before test execution")
    test_steps string[] @description("Step-by-step test procedure")
    expected_results string[] @description("Expected outcomes for each step")
    test_data TestDataSet? @description("Structured test data for this test case")
    tags string[] @description("Tags for test categorization")
    automation_status string @description("Ready for Automation, Manual Only, or Needs Review")
    risk_level string @description("Low, Medium, High - based on business impact")
    test_environment string @description("Environment requirements: Unit, Integration, System, UAT")
}

class TestDataSet {
    input_data string @description("Input data in key:value format, derived from story requirements")
    expected_outputs string? @description("Expected output data if applicable")
    boundary_values string[]? @description("Boundary values specific to story constraints")
    invalid_inputs string[]? @description("Invalid inputs that should trigger specific error responses")
}

class TestCoverageAnalysis {
    requirements_covered string[] @description("List of requirements/acceptance criteria covered by generated tests")
    requirements_not_covered string[]? @description("Any requirements that may need additional test coverage")
    test_categories_included string[] @description("Categories of tests generated")
    risk_areas_addressed string[] @description("Business risk areas addressed by the test suite")
    recommended_additional_tests string[]? @description("Suggestions for additional tests if gaps identified")
}

class TestCasesResponse {
    test_cases TestCaseData[]
    coverage_analysis TestCoverageAnalysis @description("Analysis of test coverage completeness")
    total_test_count int @description("Total number of test cases generated")
    test_execution_estimate string @description("Estimated time for manual test execution")
}

function GenerateTestCases(request: GenerateTestCasesRequest) -> TestCasesResponse {
    client "anthropic/claude-3-5-sonnet-latest"

    prompt #"
        You are an expert QA engineer generating comprehensive test cases for a JIRA issue.

        JIRA Issue Details:
        - Key: {{request.issue.key}}
        - Summary: {{request.issue.summary}}
        - Description: {{request.issue.description}}
        - Type: {{request.issue.issue_type}}
        - Priority: {{request.issue.priority}}
        {% if request.issue.acceptance_criteria %}
        - Acceptance Criteria: {{request.issue.acceptance_criteria}}
        {% endif %}
        {% if request.issue.components %}
        - Components: {{request.issue.components}}
        {% endif %}
        {% if request.issue.labels %}
        - Labels: {{request.issue.labels}}
        {% endif %}
        {% if request.issue.story_points %}
        - Story Points: {{request.issue.story_points}}
        {% endif %}
        {% if request.issue.epic_link %}
        - Epic: {{request.issue.epic_link}}
        {% endif %}

        Test Generation Requirements:
        - Include Edge Cases: {{request.include_edge_cases}}
        - Include Negative Tests: {{request.include_negative_tests}}
        - Include Security Tests: {{request.include_security_tests}}
        - Priority Levels to Use: {{request.test_priorities}}

        {% if request.business_context %}
        Business Context: {{request.business_context}}
        {% endif %}
        {% if request.related_systems %}
        Related Systems: {{request.related_systems}}
        {% endif %}
        {% if request.dependencies %}
        Dependencies: {{request.dependencies}}
        {% endif %}

        STEP 1: REQUIREMENTS ANALYSIS
        Analyze the issue to understand:
        - Functional requirements: What specific features/behaviors are being implemented?
        - Acceptance criteria: What are the explicit success conditions?
        - Business rules: What constraints, validations, or logic must be enforced?
        - User personas: What roles will interact with this functionality?
        - System boundaries: What components, APIs, or integrations are involved?
        - Data entities: What objects, fields, or data structures are mentioned?
        - Risk areas: What could go wrong and what's the business impact?

        STEP 2: TEST STRATEGY PLANNING
        Based on the issue type and components, determine:
        - Primary test categories needed (UI, API, integration, database, etc.)
        - Test environment requirements (test data, system state, permissions)
        - Risk areas requiring additional coverage
        - Dependencies that need mocking or stubbing
        - Appropriate test levels (unit, integration, system, acceptance)

        STEP 3: DYNAMIC TEST DATA PLANNING
        Based on your analysis, identify:
        - What data fields are actually needed to test this functionality?
        - What realistic values would exercise the described requirements?
        - What edge cases are relevant to the specific constraints mentioned?
        - What business-appropriate data would a real user provide?
        - What boundary conditions exist based on the actual requirements?

        STEP 4: GENERATE TEST CASES WITH TRACEABILITY
        Generate comprehensive test cases that:
        1. Map explicitly to acceptance criteria or functional requirements
        2. Cover all functional requirements from the issue description
        3. Include positive/happy path scenarios
        4. Add negative test cases if requested (invalid inputs, error conditions)
        5. Include edge cases if requested (boundary values, special characters, limits)
        6. Add security test cases if requested (injection, XSS, authentication)
        7. Ensure each test case is atomic and independent
        8. Provide clear, actionable test steps
        9. Include story-specific, realistic test data examples

        For each test case, ensure:
        - Name clearly describes what is being tested
        - Category reflects the test level (Functional, Integration, UI, API, Database, Security, Performance, Usability)
        - Type indicates test nature (Positive, Negative, Boundary, Error Handling)
        - Priority reflects business importance (P1=Critical, P2=Important, P3=Nice to have)
        - Requirement traceability explicitly maps to acceptance criteria
        - Risk level indicates business impact if this test fails
        - Test environment specifies where this test should run
        - Preconditions list any setup required
        - Test steps are numbered and clear
        - Expected results match each test step
        - Test data provides structured, story-specific examples
        - Tags help with test organization (e.g., smoke, regression, feature name)
        - Automation status: "Ready for Automation" for UI/API tests, "Manual Only" for visual/UX tests

        For test data generation:
        - EXTRACT specific data fields mentioned or implied in the story description
        - DERIVE field names from the actual terminology used in the requirements
        - GENERATE realistic values that reflect the business domain and use cases described
        - INCORPORATE any constraints, formats, or validation rules mentioned in the story
        - CREATE values that would realistically be used by actual users in this context
        - For boundary tests: use the specific limits or constraints mentioned in the story
        - For negative tests: violate the specific rules or requirements described
        - STRUCTURE test data as input_data, expected_outputs, boundary_values, and invalid_inputs
        - NEVER use generic templates - always derive from the actual story content

        Examples of dynamic analysis:
        - Story mentions "product SKU must be unique" → generate realistic SKUs like "LAPTOP-2024-001"
        - Story describes "user profile with department" → use actual department names like "Engineering", "Sales"
        - Story involves "order processing" → generate order numbers, amounts, dates relevant to that domain
        - Story mentions "email validation" → create various email formats to test validation rules

        STEP 5: COVERAGE ANALYSIS
        Provide comprehensive coverage analysis including:
        - Which requirements/acceptance criteria are covered by the generated tests
        - Any requirements that may need additional test coverage
        - Test categories included in the generated suite
        - Business risk areas addressed by the test suite
        - Recommendations for additional tests if gaps are identified
        - Estimated manual execution time for the test suite

        Generate test cases covering different aspects of the requirement, ensuring comprehensive coverage of all acceptance criteria.

        {{ctx.output_format}}
    "#
}

test GenerateTestCasesTest {
    functions [GenerateTestCases]
    args {
        request {
            issue {
                key "PROJ-123"
                summary "Add user login functionality with email and password"
                description "As a user, I want to log in using my email and password so that I can access my account. The system should validate credentials and show appropriate error messages for invalid inputs."
                issue_type "Story"
                priority "High"
                acceptance_criteria [
                    "User can successfully log in with valid email and password",
                    "System displays error message for invalid email format",
                    "System displays error message for incorrect password",
                    "User account is locked after 3 failed attempts",
                    "System redirects to dashboard after successful login"
                ]
                components ["Authentication", "User Management"]
                labels ["login", "security", "frontend"]
                story_points 5
                epic_link "EPIC-001: User Authentication System"
            }
            include_edge_cases true
            include_negative_tests true
            include_security_tests true
            test_priorities ["P1", "P2", "P3"]
            business_context "E-commerce platform with strict security requirements"
            related_systems ["User Database", "Session Management", "Audit Logging"]
            dependencies ["User Registration System", "Password Encryption Service"]
        }
    }
}
