class DescribeCodeFileRequest {
    file_name string
    language string
    file_content string
}

function DescribeCodeFile(request: DescribeCodeFileRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        Your task is to analyze the provided code file and create a detailed technical description that would help developers understand and maintain this code. Your analysis should be thorough and insightful.

        ## Output Format
        Provide your analysis in markdown format with the following sections.

        - IMPORTANT: You may include key code snippets in your output (wherever appropriate), but DO NOT include the entire file content or a majority of the file content.

        ### 1. Overview
        - Provide a high-level summary of the file's purpose and functionality
        - Identify the programming language and any frameworks/libraries used
        - Explain the file's role within the broader application architecture (if apparent)

        ### 2. Code Structure
        - Describe the overall organization and structure of the code
        - Identify key components (classes, functions, modules, etc.)
        - Outline any design patterns or architectural approaches used

        ### 3. Dependencies
        - List external dependencies and imports
        - Explain how they're used within the file
        - Note any version-specific requirements or potential compatibility issues

        ### 4. Key Functionality
        - Explain the primary functions/methods and their purposes
        - Describe important algorithms or business logic
        - Detail data flow and state management

        ### 5. Data Structures
        - Document significant data structures, models, or schemas
        - Explain important variables and their purposes
        - Describe data transformations or processing

        ### 6. Error Handling & Edge Cases
        - Analyze error handling mechanisms
        - Identify potential edge cases and how they're addressed
        - Note any defensive programming techniques

        ### 7. Configuration & Environment
        - Document configuration settings or environment requirements
        - Explain any conditional logic based on environment variables

        ### 8. Security Considerations
        - Identify security measures or sensitive areas in the code
        - Note any potential security concerns

        ### 9. Performance Considerations
        - Highlight performance-critical sections
        - Analyze efficiency of algorithms or operations
        - Note any caching or optimization techniques

        ### 10. Maintenance Notes
        - Identify technical debt or areas that could be improved
        - Note any deprecated approaches or TODOs
        - Suggest potential refactoring opportunities

        ### 11. Summary
        - Provide a concise recap of the file's key points
        - Highlight aspects that require special attention during maintenance

        {{ _.role("user") }}

        <file_name>
        {{ request.file_name }}
        </file_name>

        <language>
        {{ request.language }}
        </language>

        <file_content>
        {{ request.file_content }}
        </file_content>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestDescribeCodeFile {
  functions [DescribeCodeFile]
  args {
    request {
        file_name "my_file.cs"
        language "csharp"
        file_content #"
        public class MyFile {
            public void MyMethod() {
                Console.WriteLine("Hello, World!");
            }
        }
        "#
    }
  }
}
