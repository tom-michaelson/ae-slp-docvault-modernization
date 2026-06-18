using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Recursively list all directories under the source directory.
        /// </summary>
        /// <param name="sourceDir">The root directory to search from.</param>
        /// <returns>A list of directory paths as strings.</returns>
        public static async Task<string[]?> ListAllDirectoriesRecursiveActivity(string sourceDir)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string[]?>(
                AwaConstants.ActivityListAllDirectoriesRecursive,
                new object?[] { sourceDir },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds * 10)
                });
        }
    }
}
