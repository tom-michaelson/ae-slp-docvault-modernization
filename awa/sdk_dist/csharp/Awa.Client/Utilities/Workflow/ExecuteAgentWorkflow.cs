using System;
using System.Threading.Tasks;
using Awa.Client.Constants;
using Awa.Client.Models;
using Temporalio.Workflows;

namespace Awa.Client.Utilities.Workflow
{
    public static partial class WorkflowUtilities
    {
        /// <summary>
        /// Execute an agent with the specified configuration.
        /// </summary>
        /// <param name="agentConfig">The configuration for the agent to execute.</param>
        /// <param name="timeoutSeconds">Optional timeout in seconds for agent execution. If not provided, uses agent_config.timeout_seconds or default.</param>
        /// <param name="name">Optional name for the agent execution, used in workflow ID generation.</param>
        /// <returns>The result of the agent execution.</returns>
        public static async Task<TaskResponseModel?> ExecuteAgentWorkflow(
            AgentConfiguration agentConfig,
            int? timeoutSeconds = null,
            string? name = null)
        {
            if (!agentConfig.TimeoutSeconds.HasValue)
            {
                agentConfig.TimeoutSeconds = timeoutSeconds ?? AwaConstants.AgentTimeoutSeconds;
            }

            var result = await Temporalio.Workflows.Workflow.ExecuteChildWorkflowAsync<TaskResponseModel?>(
                AwaConstants.WorkflowExecuteAgent,
                new object?[] { agentConfig },
                new()
                {
                    TaskQueue = AwaConstants.AwaDefaultTaskQueue,
                    Id = name != null ? $"{name}-{Temporalio.Workflows.Workflow.Info.WorkflowId}" : null
                });

            return result;
        }
    }
}
