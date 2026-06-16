class SummarizeDiffRequest {
    file_path string
    diff_content string
}

function SummarizeDiff(request: SummarizeDiffRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}
        You are an expert at reviewing code changes and writing concise, easy-to-understand summaries.
        Your task is to summarize the code changes from a git diff for a single file.
        **YOUR RESPONSE MUST BE A SINGLE, TERSE SENTENCE, UNDER 150 CHARACTERS.**
        This is a strict requirement. Do not write more than 150 characters.

        Your summary should focus on the "what" and "why" of the changes.
        If the changes are trivial (e.g., formatting, comments), state that clearly.
        For new files, just state that the file was added and its high-level purpose.

        Good summary: "Adds new documentation for BAML best practices."
        Bad summary: "A new file, b/.cursor/rules/baml-best-practices.mdc, was added to provide best practice guidelines for writing BAML..."

        You will be provided with:
        1. `file_path`: The path to the file that was changed.
        2. `diff_content`: The git diff output for the file.

        {{ _.role("user") }}

        <file_path>
        {{request.file_path}}
        </file_path>

        <diff_content>
        {{request.diff_content}}
        </diff_content>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestSummarizeDiff {
  functions [SummarizeDiff]
  args {
    request {
        file_path "src/components/Button.js"
        diff_content #"
        diff --git a/src/components/Button.js b/src/components/Button.js
        index 1234567..abcdefg 100644
        --- a/src/components/Button.js
        +++ b/src/components/Button.js
        @@ -1,5 +1,6 @@
         import React from 'react';

         const Button = ({ children, onClick }) => (
        -  <button onClick={onClick}>{children}</button>
        +  <button className="btn" onClick={onClick} type="button">
        +    {children}
        +  </button>
         );

         export default Button;
        "#
    }
  }
}
