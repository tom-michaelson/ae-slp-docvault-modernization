class GenerateFileDiffRequest {
    file_path string
    file_content string
    natural_language_request string
}

class GenerateFileDiffResult {
    diff_string string
}

template_string DiffInstructions() #"
Create a diff using this specific V4A format:

```
*** Begin Patch
*** Update File: [path/to/file]
 [context_before]
-[old_code]
+[new_code]
 [context_after]
*** End Patch
```

Or for adding a new file:

```
*** Begin Patch
*** Add File: [path/to/file]
+ [line 1 of new file]
+ [line 2 of new file]
+ [...]
*** End Patch
```

Or for deleting a file:

```
*** Begin Patch
*** Delete File: [path/to/file]
*** End Patch
```

### Context Guidelines
- Show 3 lines of code immediately above and below each change
- If a change is within 3 lines of a previous change, do NOT duplicate context
- If 3 lines is insufficient to identify the snippet, use `@@ class ClassName` or `@@ method methodName` to indicate scope
- IMPORTANT: [context_before] and [context_after] MUST include a blank space at the beginning of each line (instead of a "+" or "-").
- IMPORTANT: DO NOT include a leading blank space on any "***" lines.
- Multiple `@@` statements can be used for nested context, e.g.:
    ```
    @@ class BaseClass
    @@   def method():
    ```

"#

function GenerateFileDiff(request: GenerateFileDiffRequest) -> GenerateFileDiffResult {
  client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}
        You are a code assistant specializing in creating detailed and accurate diffs for code files.
        Your task is to modify a file according to a natural language request and generate a diff in a specific format.

        <instructions_for_generating_diff>
        {{ DiffInstructions() }}
        </instructions_for_generating_diff>

        {{ _.role("user") }}

        <natural_language_request>
        {{ request.natural_language_request }}
        </natural_language_request>

        <file_path>
        {{ request.file_path }}
        </file_path>

        <original_file_content>
        {{ request.file_content }}
        </original_file_content>

        ## Response Format
        {{ ctx.output_format }}
    "#
}

test TestGenerateFileDiff {
    functions [GenerateFileDiff]
    args {
        request {
            file_path "example.py"
            file_content "def hello():\n    print(\"Hello, world!\")\n\ndef main():\n    hello()\n\nif __name__ == \"__main__\":\n    main()\n"
            natural_language_request "Add a new function called goodbye that prints 'Goodbye, world!' and call it from main."
        }
    }
}
