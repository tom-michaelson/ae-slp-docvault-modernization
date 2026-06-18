class SummarizeApplicationRequest {
    tech_stack string
    directory_descriptions string
    file_descriptions string
}

class FileDescription {
    file string
    content string
}

function SummarizeApplication(request: SummarizeApplicationRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        Your task is to create a high-level summary of an application. You will be given a description of the tech stack and a list of files and directories with brief descriptions of each.

        Your summary should include the business purpose of the application, a summary of the features that it provides, an overview of the architecture and codebase structure, and any other relevant information.

        {{ _.role("user") }}

        <tech_stack>
        {{request.tech_stack}}
        </tech_stack>

        <directory_descriptions>
        {{request.directory_descriptions}}
        </directory_descriptions>

        <file_descriptions>
        {{request.file_descriptions}}
        </file_descriptions>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestSummarizeApplication {
  functions [SummarizeApplication]
  args {
    request {
        tech_stack "Python, Flask, SQLite"
        directory_descriptions [
            "my_directory: contains a file called my_file.cs"
        ]
        file_descriptions [
            "my_file.cs: prints 'Hello, World!'"
        ]
    }
  }
}
