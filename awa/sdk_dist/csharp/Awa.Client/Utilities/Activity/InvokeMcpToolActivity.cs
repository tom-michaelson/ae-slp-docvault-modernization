using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Temporalio.Common;

namespace Awa.Client.Utilities.Activity
{
    public static partial class ActivityUtilities
    {
        /// <summary>
        /// Invoke a Model Context Protocol (MCP) tool.
        /// </summary>
        /// <param name="mcpConfig">Configuration dictionary for the MCP server.</param>
        /// <param name="toolName">Name of the MCP tool to invoke.</param>
        /// <param name="parameters">Parameters to pass to the MCP tool.</param>
        /// <param name="timeoutSeconds">Optional timeout in seconds for the tool invocation. Defaults to agent timeout if not specified.</param>
        /// <param name="retryPolicy">Optional Temporal retry policy for handling failures. Defaults to null.</param>
        /// <returns>The result returned by the MCP tool.</returns>
        public static async Task<object?> InvokeMcpToolActivity(
            Dictionary<string, object?> mcpConfig,
            string toolName,
            Dictionary<string, object?> parameters,
            int? timeoutSeconds = null,
            RetryPolicy? retryPolicy = null)
        {
            return await Temporalio.Workflows.Workflow.ExecuteActivityAsync<object?>(
                AwaConstants.ActivityInvokeMcpTool,
                new object?[] { mcpConfig, toolName, parameters },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    StartToCloseTimeout = TimeSpan.FromSeconds(timeoutSeconds ?? AwaConstants.AgentTimeoutSeconds),
                    RetryPolicy = retryPolicy
                });
        }
    }
}
