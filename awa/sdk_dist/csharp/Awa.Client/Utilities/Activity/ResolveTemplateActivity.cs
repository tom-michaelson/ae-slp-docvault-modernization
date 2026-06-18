using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Resolve a template string by substituting variables.
        /// </summary>
        /// <param name="templateStr">The template string containing variable placeholders.</param>
        /// <param name="variables">Optional dictionary of variables to substitute in the template. Defaults to null.</param>
        /// <returns>The resolved template string with variables substituted.</returns>
        public static async Task<string?> ResolveTemplateActivity(
            string templateStr,
            Dictionary<string, object?>? variables = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<string?>(
                AwaConstants.ActivityResolveTemplate,
                new object?[] { templateStr, variables },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(AwaConstants.FileIoTimeoutSeconds)
                });
        }
    }
}
