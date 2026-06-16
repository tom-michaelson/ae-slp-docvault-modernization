using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Read the contents of a file as bytes.
        /// </summary>
        /// <param name="filePath">The path to the file to read.</param>
        /// <param name="defaultValue">The default value to return if the file cannot be read. Defaults to null.</param>
        /// <returns>The contents of the file as bytes, or the default value if specified.</returns>
        public static async Task<byte[]?> ReadFileBytesActivity(string filePath, byte[]? defaultValue = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<byte[]?>(
                AwaConstants.ActivityReadFileBytes,
                new object?[] { filePath, defaultValue },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
