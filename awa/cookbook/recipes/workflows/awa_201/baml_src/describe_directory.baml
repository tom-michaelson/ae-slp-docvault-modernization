class DescribeDirectoryRequest {
    directory_name string
    files string[]
    sub_directories string[]
}

function DescribeDirectory(request: DescribeDirectoryRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        Describe the directory based on the description of the files and sub-directories it contains. Describe the directory in 1-2 sentences.


        {{ _.role("user") }}

        <directory_name>
        {{request.directory_name}}
        </directory_name>

        <files>
        {{request.files}}
        </files>

        <sub_directories>
        {{request.sub_directories}}
        </sub_directories>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestDescribeDirectory {
  functions [DescribeDirectory]
  args {
    request {
        files [
            "my_file.cs: prints 'Hello, World!'"
        ]
        sub_directories [
            "my_sub_directory_1: contains a CLI entry point executable"
            "my_sub_directory_2: empty"
        ]
    }
  }
}
