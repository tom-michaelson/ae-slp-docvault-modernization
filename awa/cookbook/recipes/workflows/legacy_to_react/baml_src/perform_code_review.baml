class PerformCodeReviewRequest {
    react_code string
    requirements string
    user_story string
}

class CodeReviewReportForCodeReview {
    overall_assessment string
    compliance_score int @check(valid_score, {{0 <= this <= 100}})
    issues CodeIssue[]
    suggestions string[]
    strengths string[]
    requirements_coverage RequirementsCoverageForCodeReview
    report string
}

class CodeIssue {
    severity string @check(valid_severity, {{this in ["critical", "major", "minor", "suggestion"]}})
    category string
    description string
    file_path string
    line_number int?
    suggested_fix string?
}

class RequirementsCoverageForCodeReview {
    covered_requirements string[]
    missing_requirements string[]
    partially_covered string[]
}

function PerformCodeReview(request: PerformCodeReviewRequest) -> CodeReviewReportForCodeReview {
    client "openai/gpt-4o"
    prompt #"
        You are an expert React code reviewer. Review the implemented React code against the requirements and user story.

        <react_code>
        {{request.react_code}}
        </react_code>

        <requirements>
        {{request.requirements}}
        </requirements>

        <user_story>
        {{request.user_story}}
        </user_story>

        Perform a comprehensive code review that includes:

        1. **Overall Assessment**: Summary of code quality and requirements compliance

        2. **Compliance Score**: 0-100 score for how well the code meets requirements

        3. **Issues**: Identify any problems categorized as:
           - Critical: Must fix before deployment
           - Major: Should fix for maintainability
           - Minor: Nice to fix
           - Suggestion: Improvement recommendations

        4. **Suggestions**: General improvement recommendations

        5. **Strengths**: What was done well

        6. **Requirements Coverage**:
           - Which requirements are fully covered
           - Which are missing
           - Which are partially implemented

        7. **Report**: Generate a markdown formatted code review report

        Focus on:
        - React best practices and patterns
        - TypeScript usage (if applicable)
        - Performance considerations
        - Accessibility
        - Security
        - Code maintainability
        - Test coverage potential

        ## Response format
        {{ ctx.output_format}}
    "#
}

test PerformCodeReviewTest {
    functions [PerformCodeReview]
    args {
        request {
            react_code [{
                path "src/components/CustomerReport.tsx"
                content #"
                import React from 'react';

                const CustomerReport = () => {
                    const customers = [
                        { id: 1, name: 'John Doe', balance: 1500 },
                        { id: 2, name: 'Jane Smith', balance: 800 }
                    ];

                    return (
                        <div>
                            <h1>Customer Report</h1>
                            {customers.filter(c => c.balance > 1000).map(customer => (
                                <div key={customer.id}>
                                    {customer.name} - High Value Customer
                                </div>
                            ))}
                        </div>
                    );
                };

                export default CustomerReport;
                "#
            }]
            requirements {
                business_logic ["Display high value customers", "Read customer records sequentially"]
                data_structures ["Customer record with ID, Name, and Balance fields"]
                validations ["Balance threshold check > 1000"]
                user_interface_requirements ["Display customer names with high value indicator"]
                integration_points ["Read from customer file"]
                summary "Customer report program that identifies high value customers"
            }
            user_story {
                title "High Value Customer Report Display"
                description "As a business analyst, I want to view a report of high value customers"
                acceptance_criteria ["Display customers with balance > $1000"]
                technical_notes "Customer data structure"
                implementation_considerations ["Use React hooks"]
            }
        }
    }
}
