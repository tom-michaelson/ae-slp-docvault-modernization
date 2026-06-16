class RewriteFileRequest {
    file_content string
    natural_language_request string
}

class RewriteFileResult {
    thoughts string
    complete_new_file_content string @description("The complete version of the new file, with all changes applied")
}

function RewriteFile(request: RewriteFileRequest) -> RewriteFileResult {
  client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}

        You are a code assistant specializing in creating code files.

        Your task is to rewrite a file with new content based on a natural_language_request.

        {{ _.role("user") }}

        <natural_language_request>
        {{ request.natural_language_request }}
        </natural_language_request>

        <original_file_content>
        {{ request.file_content }}
        </original_file_content>

        # Response
        {{ ctx.output_format }}
    "#
}

test TestRewriteFile {
    functions [RewriteFile]
    args {
        request {
            file_content #"
 namespace Awa.Client.Utilities;

 public static class WorkflowUtilities {

 }
"#
            natural_language_request #"Add the following utility function to the file:

/// <summary>
/// Reads the contents of a file using the AWA read file activity.
/// </summary>
/// <param name=\"filePath\">The path to the file to read</param>
/// <param name=\"defaultValue\">The default value to return if the file cannot be read</param>
/// <returns>The file contents as a string, or the default value if specified</returns>
public static async Task<string> ReadFileAsync(string filePath, string defaultValue = null)
{
    return await Workflow.ExecuteActivityAsync<string>(
        AwaConstants.ActivityReadFile,
        new object[] { filePath, defaultValue },
        new()
        {
            TaskQueue = AwaConstants.AwaDefaultTaskQueue,
            StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
        });
}"#
        }
    }
}
