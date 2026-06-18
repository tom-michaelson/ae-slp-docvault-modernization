using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// List the contents of a directory.
        /// </summary>
        /// <param name="dirPath">The path to the directory to list.</param>
        /// <param name="ignoreFilePath">Optional path to an ignore file (like .gitignore) to exclude files. Defaults to null.</param>
        /// <returns>A list of file and directory names in the specified directory.</returns>
        public static async Task<string[]?> ListDirectoryActivity(string dirPath, string? ignoreFilePath = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string[]?>(
                AwaConstants.ActivityListDirectory,
                new object?[] { dirPath, ignoreFilePath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
