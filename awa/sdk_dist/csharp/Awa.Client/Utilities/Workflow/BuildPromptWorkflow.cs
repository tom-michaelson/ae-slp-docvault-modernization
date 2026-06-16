using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Build a prompt using a template and variables.
        /// </summary>
        /// <param name="templateInput">InputParams containing template configuration and content.</param>
        /// <param name="variables">Optional dictionary of variables to use in template resolution. Defaults to null.</param>
        /// <param name="inputs">Optional list of InputParams for the prompt building process. Defaults to null.</param>
        /// <param name="outputPath">Optional path where the built prompt should be saved. Defaults to null.</param>
        /// <returns>The built prompt string.</returns>
        public static async Task<string?> BuildPromptWorkflow(
            InputParams templateInput,
            Dictionary<string, object?>? variables = null,
            InputParams[]? inputs = null,
            string? outputPath = null)
        {
            var args = new object?[]
            {
                new
                {
                    template_input = templateInput,
                    variables = variables,
                    inputs = inputs,
                    output_path = outputPath
                }
            };

            return await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<string?>(
                AwaConstants.WorkflowBuildPrompt,
                args,
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue
                });
        }
    }
}
