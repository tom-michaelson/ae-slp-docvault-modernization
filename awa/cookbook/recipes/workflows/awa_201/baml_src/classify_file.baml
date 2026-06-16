class ClassifyFileRequest {
    file_name string
    file_content string
}

enum FileCategory {
    APP_CODE @description("Source code files that are part of the application's core logic or UI. This could include frontend or backend logic, views, styles, scripts, etc. UI views should fit this category.")
    CONFIGURATION @description("Files that configure the application, build process, or deployment (e.g., .yaml, .ini, Dockerfile).")
    DEPENDENCY_MANIFEST @description("Files that declare project dependencies or manage package information (e.g., package.json, pyproject.toml, pom.xml).")
    DOCUMENTATION @description("Files containing documentation for the project or code (e.g., README.md, .rst files, Javadoc).")
    OTHER @description("Files that do not fit into any of the other predefined categories.")
}

class ClassifyFileResult {
    file_category FileCategory @description("The category of the file.")
    language string @description("The programming language of the file. All lowercase. Avoid special characters (e.g. use 'csharp' instead of 'c#').")
    dependency_manager string? @description("The dependency manager used, if applicable (e.g., npm, pip). Omit this field if not applicable or unknown.")
}

function ClassifyFile(request: ClassifyFileRequest) -> ClassifyFileResult {
    client "openai/gpt-4.1"
    prompt #"
        {{ _.role("system")}}

        Your task is to classify a file from an application.

        You must determine the following aspects of the file:
        - What category of file is it?
        - What language is it (primarily)?
        - If it is a dependency manifest file, what is the primary dependency manager (e.g. npm, pip, etc.)?

        IMPORTANT: Read the file content carefully to make the best determination.

        {{ _.role("user") }}

        <file_name>
        {{request.file_name}}
        </file_name>

        <file_content description="The first 5,000 characters of the file content">
        {{request.file_content}}
        </file_content>

        # Response

        {{ ctx.output_format }}
    "#
}

test TestClassifyFile {
  functions [ClassifyFile]
  args {
    request {
        file_name "my_file.cs"
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
