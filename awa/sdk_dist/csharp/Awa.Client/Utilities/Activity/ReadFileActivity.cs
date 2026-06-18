using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Read the contents of a file as a string.
        /// </summary>
        /// <param name="filePath">The path to the file to read.</param>
        /// <param name="defaultValue">The default value to return if the file cannot be read. Defaults to null.</param>
        /// <returns>The contents of the file as a string, or the default value if specified.</returns>
        public static async Task<string?> ReadFileActivity(string filePath, string? defaultValue = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
                AwaConstants.ActivityReadFile,
                new object?[] { filePath, defaultValue },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
