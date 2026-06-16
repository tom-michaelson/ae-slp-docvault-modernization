using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Get information about a single directory including its immediate files and subdirectories.
        /// </summary>
        /// <param name="directoryPath">The path to the directory to analyze.</param>
        /// <returns>
        /// A FolderInfo object containing:
        /// - path: The directory path
        /// - files: List of file names (not full paths)
        /// - subdirectories: List of subdirectory names (not full paths)
        /// </returns>
        /// <remarks>
        /// This function examines a single directory and returns information about its
        /// immediate contents without recursing into subdirectories. It provides lists
        /// of file names and subdirectory names found directly in the specified directory.
        /// </remarks>
        public static async Task<FolderInfo?> GetDirectoryInfoActivity(string directoryPath)
        {
            var rawResult = await Temporalio.Workflows.Workflow.ExecuteActivityAsync<object?>(
                AwaConstants.ActivityGetDirectoryInfo,
                new object?[] { directoryPath },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });

            if (rawResult == null)
            {
                return null;
            }

            // Convert the raw result to FolderInfo
            return FolderInfo.FromJson(rawResult.ToString());
        }
    }
}
