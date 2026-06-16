class ExtractTechnicalRequirementsRequest {
    code_file_name string
    code_file string
    the_code_summary string
}

function ExtractTechnicalRequirements(request: ExtractTechnicalRequirementsRequest) -> string {
  client "openai/gpt-4.1"
    prompt #"
        Extract detailed technical requirements from the given code file summary and content.

        <code_file_summary>
        {{request.the_code_summary}}
        </code_file_summary>

        <code_file_content>
        {{request.code_file}}
        </code_file_content>

        ## Response Format
        Respond with well-formatted markdown.
    "#
}


test ExtractTechnicalRequirementsTest {
    functions [ExtractTechnicalRequirements]
    args {
        request {
            code_file_name "test.py"
            code_file #"
            print("Hello, World!")
            "#
            the_code_summary "The code file prints 'Hello, World!'."
        }
    }
}
