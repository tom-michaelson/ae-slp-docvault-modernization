class SummarizeCodeWithAdditionalInstructionsRequest {
    code_file_name string
    code_file string
    additional_instructions string?
}

function SummarizeCodeWithAdditionalInstructions(request: SummarizeCodeWithAdditionalInstructionsRequest) -> string {
  client "openai/gpt-4.1"
    prompt #"
        Summarize the provided code file.

        <code_file name="{{ request.code_file_name }}">
        {{ request.code_file }}
        </code_file>

        {% if request.additional_instructions %}
        <additional_instructions>
        {{ request.additional_instructions }}
        </additional_instructions>
        {% endif %}

        ## Response Format
        Respond with well-formatted markdown.
    "#
}


test SummarizeCodeWithAdditionalInstructionsTest {
    functions [SummarizeCodeWithAdditionalInstructions]
    args {
        request {
            code_file_name "test.py"
            code_file #"
            print("Hello, World!")
            "#
            additional_instructions "Talk like a pirate."
        }
    }
}
