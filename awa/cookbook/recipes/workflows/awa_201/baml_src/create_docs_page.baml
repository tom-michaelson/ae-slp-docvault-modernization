class CreateDocsPageRequest {
    tech_stack string
    title string
    summary string
    linked_documentation_pages string[]
    relevant_source_file_descriptions map<string,string>
}

function CreateDocsPage(request: CreateDocsPageRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        You are tasked with creating a detailed technical documentation page for a software application. Your audience is the technical development team responsible for maintaining the application.

        {{ _.role("user") }}

        # Input

        <tech_stack>
        {{request.tech_stack}}
        </tech_stack>

        <page_title>
        {{request.title}}
        </page_title>

        <page_summary>
        {{request.summary}}
        </page_summary>

        <linked_documentation_pages>
        {% for page in request.linked_documentation_pages %}
        <page>
        {{page}}
        </page>
        {% endfor %}
        </linked_documentation_pages>

        <relevant_source_file_descriptions>
        {{request.relevant_source_file_descriptions}}
        </relevant_source_file_descriptions>

        # Output Requirements
        Create a comprehensive Markdown documentation page that:

        1. Uses the page title as the main (H1) heading
        2. Implements all the suggested sections from the summary as H2 headings
        3. Elaborates each section with detailed technical content derived from the source files
        4. References linked documentation pages where appropriate using Markdown links
        5. Includes relevant code snippets from the source files with proper syntax highlighting
        6. Explains implementation details, design patterns, and technical decisions
        7. Addresses potential issues, edge cases, or gotchas developers might encounter
        8. Uses technical terminology appropriate for experienced developers

        # Style Guidelines
        - Write with technical precision and depth
        - Include explanatory comments alongside code samples
        - Use tables, bulleted lists, and other formatting to organize complex information
        - Provide specific, concrete examples rather than general statements
        - Include context and rationale for technical decisions where appropriate
        - Use consistent terminology throughout the document
        - Format code snippets with appropriate language identifiers (e.g., ```csharp)
        - Create a logical flow from basic concepts to more advanced topics

        Remember that the documentation should be comprehensive enough that a developer unfamiliar with this specific codebase but knowledgeable about the technology stack can understand how to work with and maintain the code.

        # Response

        {{ ctx.output_format }}
    "#
}

test TestCreateDocsPage {
  functions [CreateDocsPage]
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
