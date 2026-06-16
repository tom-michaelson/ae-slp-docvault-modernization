class DescribeFileShortRequest {
    file_name string
    file_description string
}

function DescribeFileShort(request: DescribeFileShortRequest) -> string {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        Describe the provided file in 1-2 sentences.

        {{ _.role("user") }}

        <file_name>
        {{ request.file_name }}
        </file_name>

        <file_description>
        {{ request.file_description }}
        </file_description>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestDescribeFileShort {
  functions [DescribeFileShort]
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
