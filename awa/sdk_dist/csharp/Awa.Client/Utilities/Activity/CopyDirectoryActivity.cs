using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Copy a directory and its contents to a destination.
        /// </summary>
        /// <param name="sourcePath">The path to the source directory to copy.</param>
        /// <param name="destinationPath">The path where the directory should be copied.</param>
        /// <param name="ignoreFilePath">Optional path to an ignore file (like .gitignore) to exclude files. Defaults to null.</param>
        /// <returns>A list of the files that were copied.</returns>
        public static async Task<List<string>?> CopyDirectoryActivity(
            string sourcePath,
            string destinationPath,
            string? ignoreFilePath = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<List<string>?>(
                AwaConstants.ActivityCopyDirectory,
                new object?[] { sourcePath, destinationPath, ignoreFilePath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds * 20)
                });
        }
    }
}
