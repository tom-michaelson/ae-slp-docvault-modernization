using System;
using System.IO;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;
using Awa.Client.Utilities.Activity;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Execute a BAML transformation using a specified function.
        /// </summary>
        /// <param name="transformParams">Parameters for the BAML transformation</param>
        /// <param name="bamlPath">Optional path to the BAML file (will be read and added as content to the transform params)</param>
        /// <param name="additionalWorkflowIdPart">Optional additional part to include in the workflow ID</param>
        /// <returns>The result of the BAML transformation</returns>
        public static async Task<object?> ExecuteBamlTransformWorkflow(
            TransformParams transformParams,
            string? bamlPath = null,
            string? additionalWorkflowIdPart = null)
        {
            if (!string.IsNullOrEmpty(bamlPath))
            {
                var bamlContent = await ActivityUtilities.ReadFileActivity(bamlPath);
                transformParams.BamlContent = bamlContent;
            }

            var additionalWorkflowIdPartFormatted = !string.IsNullOrEmpty(additionalWorkflowIdPart)
                ? $"-{additionalWorkflowIdPart}"
                : "";

            var transformResult = await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<object?>(
                AwaConstants.WorkflowTransform,
                new object?[] { transformParams },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    Id = $"{transformParams.BamlFunctionName}{additionalWorkflowIdPartFormatted}-{Temporalio.Workflows.Workflow.Info.WorkflowId}"
                });

            return transformResult;
        }
    }
}
