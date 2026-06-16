using System;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Clone a Git repository to a destination path.
        /// </summary>
        /// <param name="gitUrl">The Git repository URL to clone</param>
        /// <param name="destinationPath">Optional destination path. If not provided, uses a temp directory</param>
        /// <param name="branch">Optional branch to checkout</param>
        /// <returns>The path to the cloned repository</returns>
        public static async Task<string?> GitCloneActivity(
            string gitUrl,
            string? destinationPath = null,
            string? branch = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
                AwaConstants.ActivityGitClone,
                new object?[] { gitUrl, destinationPath, branch },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.GitTimeoutSeconds)
                });
        }
    }
}
