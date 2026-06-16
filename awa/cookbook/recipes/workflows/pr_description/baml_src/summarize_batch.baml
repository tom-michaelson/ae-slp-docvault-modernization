class SummarizeBatchRequest {
    summaries string[]
}

function SummarizeBatch(request: SummarizeBatchRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}
        You are an expert at summarizing technical information. You will be given a list of summaries, each detailing changes to a specific file. Your task is to synthesize these individual summaries into a single, coherent summary that encapsulates the overall changes for this batch of files.

        {{ _.role("user") }}

        <summaries>
        {% for summary in request.summaries %}
        - {{ summary }}
        {% endfor %}
        </summaries>

        # Response

        Provide a concise summary of the combined changes described in the list above.

        {{ ctx.output_format }}
    "#
}

test TestSummarizeBatch {
  functions [SummarizeBatch]
  args {
    request {
        summaries [
            "src/components/Button.js: Adds a new Button component with updated styling, including a new CSS class.",
            "src/styles/main.css: Trivial formatting changes.",
            "src/api/user.js: Adds a new endpoint for fetching user data.",
            "src/utils/helpers.js: Adds a new helper function for formatting dates.",
            "src/tests/Button.test.js: Adds a new test for the Button component."
        ]
    }
  }
}
