using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Check if a path is a directory.
        /// </summary>
        /// <param name="dirPath">The directory path to check.</param>
        /// <returns>True if the path is a directory, False otherwise.</returns>
        public static async Task<bool> IsDirectoryActivity(string dirPath)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<bool>(
                AwaConstants.ActivityIsDirectory,
                new object?[] { dirPath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
