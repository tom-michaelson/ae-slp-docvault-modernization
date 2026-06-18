using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Run a command and return the result.
        /// </summary>
        /// <param name="commandInput">The command input containing command and working directory.</param>
        /// <returns>CommandResult with success status and output.</returns>
        public static async Task<CommandResult?> RunCommandActivity(CommandInput commandInput)
        {
            var result = await Temporalio.Workflows.Workflow.ExecuteActivityAsync<CommandResult?>(
                AwaConstants.ActivityRunCommand,
                new object?[] { commandInput },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(300) // 5 minutes for commands
                });

            return result;
        }
    }
}
