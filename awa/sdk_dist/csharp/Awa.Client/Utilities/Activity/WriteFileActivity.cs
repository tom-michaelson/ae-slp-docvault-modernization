using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Write content to a file.
        /// </summary>
        /// <param name="filePath">The path where the file should be written.</param>
        /// <param name="content">The string content to write to the file.</param>
        public static async Task WriteFileActivity(string filePath, string content)
        {
            await Temporalio.Workflows.Workflow.ExecuteActivityAsync(
                AwaConstants.ActivityWriteFile,
                new object?[] { filePath, content },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
