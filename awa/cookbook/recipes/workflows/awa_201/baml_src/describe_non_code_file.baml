class DescribeNonCodeFileRequest {
    file_name string
    file_category string
    file_content string
}

function DescribeNonCodeFile(request: DescribeNonCodeFileRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        Your task is to analyze the provided non-code file and create a detailed technical description that would help developers understand and maintain this file. Your analysis should be thorough and insightful.

        ## Output Format
        Provide your analysis in markdown format with the following sections:

        ### 1. Overview
        - Provide a high-level summary of the file's purpose and role
        - Identify the file type/format and its general category
        - Explain how this file contributes to the overall project

        ### 2. File Type & Format
        - Describe the file format specifications
        - Note any formatting conventions or standards followed
        - Identify any validation requirements for this file type

        ### 3. Content Structure
        - Outline the organization and structure of the file
        - Identify major sections or components
        - Explain the hierarchical structure (if applicable)

        ### 4. Key Components
        - Document the most important elements in the file
        - Explain critical settings, configurations, or content
        - Highlight any required or essential fields/sections

        ### 5. Data Elements
        - Identify significant data fields or configuration parameters
        - Explain the purpose and impact of important values
        - Document any default values and their significance

        ### 6. Dependencies & References
        - List any references to other files or resources
        - Explain relationships with other system components
        - Note any external resources referenced by this file

        ### 7. Usage Context
        - Describe where and how this file is used in the application
        - Explain which components or processes consume this file
        - Detail the impact of changes to this file on the system

        ### 8. Configuration Impact
        - Explain how configurations in this file affect application behavior
        - Document any environment-specific settings
        - Note how different values might change system functionality

        ### 9. Validation & Constraints
        - Identify any validation rules that apply to this file
        - Note constraints on values or structure
        - Explain error scenarios that might occur with invalid content

        ### 10. Security Considerations
        - Identify any sensitive information contained in the file
        - Note access control requirements or concerns
        - Highlight security implications of this file's contents

        ### 11. Maintenance Notes
        - Identify areas that require careful maintenance
        - Note any versioning considerations
        - Suggest best practices for modifying this file

        ### 12. Summary
        - Provide a concise recap of the file's importance and role
        - Highlight key points developers should know about this file
        - Offer recommendations for effective management of this file

        {{ _.role("user") }}

        <file_name>
        {{ request.file_name }}
        </file_name>

        <file_type>
        {{ request.file_category }}
        </file_type>

        <file_content>
        {{ request.file_content }}
        </file_content>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestDescribeNonCodeFile {
  functions [DescribeNonCodeFile]
  args {
    request {
        file_name "README.md"
        file_category "DOCUMENTATION"
        file_content #"
            # README.md

            This is a README file.
        "#
    }
  }
}
