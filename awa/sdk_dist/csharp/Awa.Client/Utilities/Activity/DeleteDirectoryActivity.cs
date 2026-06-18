using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Delete a directory and all its contents.
        /// </summary>
        /// <param name="dirPath">The directory path to delete.</param>
        public static async Task DeleteDirectoryActivity(string dirPath)
        {
            await Temporalio.Workflows.Workflow.ExecuteActivityAsync(
                AwaConstants.ActivityDeleteDirectory,
                new object?[] { dirPath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds * 10)
                });
        }
    }
}
