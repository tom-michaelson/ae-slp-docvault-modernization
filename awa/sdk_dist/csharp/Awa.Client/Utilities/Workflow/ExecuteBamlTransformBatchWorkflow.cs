using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;
using Awa.Client.Utilities.Activity;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Execute multiple BAML transformations in batch using a specified function.
        /// </summary>
        /// <param name="bamlRequestsByKey">Dictionary mapping keys to BAML transform params. Each key will have its corresponding request processed.</param>
        /// <param name="bamlPath">Optional path to the BAML file (will be read and added as content to the transform params).</param>
        /// <returns>Dictionary mapping the same keys to their transformation results.</returns>
        public static async Task<Dictionary<string, object?>> ExecuteBamlTransformBatchWorkflow(
            Dictionary<string, TransformParams> bamlRequestsByKey,
            string? bamlPath = null)
        {
            if (bamlRequestsByKey == null || bamlRequestsByKey.Count == 0)
            {
                return new Dictionary<string, object?>();
            }

            if (!string.IsNullOrEmpty(bamlPath))
            {
                var bamlContent = await ActivityUtilities.ReadFileActivity(bamlPath);
                foreach (var transformParams in bamlRequestsByKey.Values)
                {
                    transformParams.BamlContent = bamlContent;
                }
            }

            var bamlFunctionName = bamlRequestsByKey.Values.First().BamlFunctionName;
            return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<Dictionary<string, object?>>(
                AwaConstants.WorkflowTransformBatch,
                new object?[] { new { params_by_key = bamlRequestsByKey, timeout_seconds = AwaConstants.BamlTimeoutSeconds } },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    Id = $"{bamlFunctionName}-{Temporalio.Workflows.Workflow.Info.WorkflowId}"
                });
        }
    }
}
