class SummarizeCodeRequest {
    code_file_name string
    code_file string
}

function SummarizeCode(request: SummarizeCodeRequest) -> string {
  client "openai/gpt-4.1"
    prompt #"
        Summarize the provided code file.

        <code_file name="{{ request.code_file_name }}">
        {{ request.code_file }}
        </code_file>

        ## Response Format
        Respond with well-formatted markdown.
    "#
}


test SummarizeCodeTest {
    functions [SummarizeCode]
    args {
        request {
            code_file_name "test.py"
            code_file #"
            print("Hello, World!")
            "#
        }
    }
}
