using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Awa.Client.Constants;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Apply a diff to a single file based on a natural language prompt.
        /// </summary>
        /// <param name="filePath">The path to the file to modify.</param>
        /// <param name="prompt">The natural language request describing the changes to make.</param>
        public static async Task ApplySingleFileDiffWorkflow(string filePath, string prompt)
        {
            var args = new Dictionary<string, object?>
            {
                ["file_path"] = filePath,
                ["natural_language_request"] = prompt
            };

            await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync(
                AwaConstants.WorkflowApplySingleFileDiff,
                new object?[] { args },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue
                });
        }
    }
}
