class GenerateSummaryReportRequest {
    cobol_file string
    requirements string
    user_story string
    jira_url string
    code_review string
}

class SummaryReport {
    report string
}

function GenerateSummaryReport(request: GenerateSummaryReportRequest) -> SummaryReport {
    client "openai/gpt-4o"
    prompt #"
        You are a technical documentation expert. Generate a comprehensive summary report of the legacy to React conversion workflow.

        <workflow_data>

        <cobol_file>
        {{request.cobol_file}}
        </cobol_file>

        <requirements>
        {{request.requirements}}
        </requirements>

        <user_story>
        {{request.user_story}}
        </user_story>

        <jira_url>
        {{request.jira_url}}
        </jira_url>

        <code_review>
        {{request.code_review}}
        </code_review>
        </workflow_data>

        Generate a professional markdown report that includes:

        # Legacy to React Conversion Report

        ## Executive Summary
        - Brief overview of the conversion process
        - Key outcomes and success metrics

        ## Original COBOL Analysis
        - File analyzed: {{request.cobol_file}}
        - Summary of functionality
        - Key business logic identified

        ## Requirements Extraction
        - Business logic requirements
        - Data structure requirements
        - Validation rules
        - UI requirements
        - Integration points

        ## User Story Created
        - JIRA Issue: {{request.jira_url}}
        - Story details and acceptance criteria

        ## Code Review Results
        - Compliance score: X/100
        - Key findings
        - Strengths identified
        - Issues to address

        ## Recommendations and Next Steps
        - Immediate actions required
        - Future enhancements
        - Maintenance considerations

        ## Conclusion
        - Overall success assessment
        - Value delivered

        Make the report professional, clear, and actionable. Include specific details from the workflow execution.

        ## Response format
        {{ ctx.output_format}}
    "#
}

test GenerateSummaryReportTest {
    functions [GenerateSummaryReport]
    args {
        request {
            cobol_file "customer_report.cbl"
            requirements {
                business_logic ["Display high value customers"]
                data_structures ["Customer record"]
                validations ["Balance > 1000"]
                user_interface_requirements ["Display customer list"]
                integration_points ["File I/O"]
                summary "Customer report program"
            }
            user_story {
                title "High Value Customer Report"
                description "As a user, I want to see high value customers"
                acceptance_criteria ["Show customers with balance > $1000"]
                technical_notes "Uses customer file"
                implementation_considerations ["React hooks"]
            }
            jira_url "https://jira.example.com/browse/PROJ-123"
            implementation_result "Successfully created CustomerReport component"
            code_review {
                overall_assessment "Good implementation"
                compliance_score 85
                issues []
                suggestions ["Add error handling"]
                strengths ["Clean code"]
                requirements_coverage {
                    covered_requirements ["Display logic", "Filtering"]
                    missing_requirements ["File I/O"]
                    partially_covered []
                }
                report "Code review passed"
            }
            test_results "All tests passed. Coverage: 92%"
        }
    }
}
