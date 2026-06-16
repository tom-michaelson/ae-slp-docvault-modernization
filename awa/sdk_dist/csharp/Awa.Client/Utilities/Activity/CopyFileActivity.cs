using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Copy a file from source to destination.
        /// </summary>
        /// <param name="sourcePath">The source file path.</param>
        /// <param name="destinationPath">The destination file path.</param>
        public static async Task CopyFileActivity(string sourcePath, string destinationPath)
        {
            await Temporalio.Workflows.Workflow.ExecuteActivityAsync(
                AwaConstants.ActivityCopyFile,
                new object?[] { sourcePath, destinationPath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
