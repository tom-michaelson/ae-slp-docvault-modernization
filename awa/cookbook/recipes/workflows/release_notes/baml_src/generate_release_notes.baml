class GenerateReleaseNotesRequest {
    summaries_by_file map<string, string>
    commit_logs string
}

function GenerateReleaseNotes(request: GenerateReleaseNotesRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}
        You are an expert technical writer, skilled at creating clear and comprehensive release notes from technical summaries and commit logs.

        You will be provided with:
        1. `commit_logs`: A list of commit messages associated with the PR.
        2. `summaries_by_file`: A collection of summaries detailing changes for each file in the PR.

        Your task is to generate ONLY the high-level summary paragraph based on the provided information. Do not include any other sections, headers, or markdown formatting. The output should be a single, concise paragraph.

        {{ _.role("user") }}

        <commit_logs>
        {{request.commit_logs}}
        </commit_logs>

        <summaries_by_file>
        {% for file in request.summaries_by_file %}
        - `{{ file }}`: {{ request.summaries_by_file[file] }}
        {% endfor %}
        </summaries_by_file>

        Your response MUST be only the raw text for the summary paragraph. Do not wrap it in JSON, markdown headers, or any other special formatting.

        # Response

        {{ ctx.output_format }}
    "#
}

test TestGeneratePrDescription {
  functions [GenerateReleaseNotes]
  args {
    request {
        commit_logs #"
        - feat: Add new button component
        - style: Update button styling
        "#
        summaries_by_file {
            "src/components/Button.js" "Adds a new Button component with updated styling, including a new CSS class."
            "src/styles/main.css" "Trivial formatting changes."
        }
    }
  }
}
