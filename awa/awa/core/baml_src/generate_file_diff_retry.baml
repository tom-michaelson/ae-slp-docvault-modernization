class GenerateFileDiffRetryRequest {
    file_path string
    file_content string
    natural_language_request string
    invalid_diff string
}

class GenerateFileDiffRetryResult {
    thoughts string
    diff_string string
}

function GenerateFileDiffRetry(request: GenerateFileDiffRetryRequest) -> GenerateFileDiffRetryResult {
  client "openai/gpt-4o"
    prompt #"
        {{ _.role("system") }}

        You are a code assistant specializing in creating detailed and accurate diffs for code files.
        Your task is to modify a file according to a natural_language_request and generate a diff in a specific format.

        IMPORTANT: You attempted to generate a diff previously, but produced an invalid diff. Pay close attention to the issues within your previous diff, and produce a new, valid diff.

        <review_tips>
        - Pay especially close attention to leading spaces on [context_before] and [context_after] lines.
        - Pay especially close attention to leading spaces on lines that begin with "***" -- these lines MUST NOT have preceeding spaces.
        </review_tips

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

        <invalid_diff>
        {{ request.invalid_diff }}
        </invalid_diff>

        # Response
        {{ ctx.output_format }}
    "#
}

test TestGenerateFileDiffRetry {
    functions [GenerateFileDiffRetry]
    args {
        request {
            file_path "awa/sdk/dist/csharp/Utilities/WorkflowUtilities.cs"
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
            invalid_diff #"
*** Begin Patch
*** Update File: awa/sdk/dist/csharp/Utilities/WorkflowUtilities.cs
 namespace Awa.Client.Utilities;

 public static class WorkflowUtilities {
-
+    /// <summary>
+    /// Reads the contents of a file using the AWA read file activity.
+    /// </summary>
+    /// <param name="filePath">The path to the file to read</param>
+    /// <param name="defaultValue">The default value to return if the file cannot be read</param>
+    /// <returns>The file contents as a string, or the default value if specified</returns>
+    public static async Task<string> ReadFileAsync(string filePath, string defaultValue = null)
+    {
+        return await Workflow.ExecuteActivityAsync<string>(
+            AwaConstants.ActivityReadFile,
+            new object[] { filePath, defaultValue },
+            new()
+            {
+                TaskQueue = AwaConstants.AwaDefaultTaskQueue,
+                StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
+            });
+    }

 }
 *** End Patch
            "#
        }
    }
}
